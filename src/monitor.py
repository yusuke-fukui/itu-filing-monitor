#!/usr/bin/env python3
"""
itu-filing-monitor
ITU SpaceExplorer API を監視し、新規衛星ファイリングをメールで通知する。
"""

import argparse
import json
import logging
import os
import smtplib
import sys
from datetime import date
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from pathlib import Path

import requests
import yaml

# ── パス設定 ──────────────────────────────────────────────
ROOT = Path(__file__).parent.parent
DATA_DIR = ROOT / "data"
LOG_DIR = ROOT / "logs"
STATE_FILE = DATA_DIR / "state.json"
PREVIEW_FILE = DATA_DIR / "email_preview.html"
CONFIG_FILE = ROOT / "config.yaml"

DATA_DIR.mkdir(exist_ok=True)
LOG_DIR.mkdir(exist_ok=True)

# ── ロガー ────────────────────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(message)s",
    handlers=[
        logging.FileHandler(LOG_DIR / "monitor.log"),
        logging.StreamHandler(sys.stdout),
    ],
)
log = logging.getLogger(__name__)

# ── API 定数 ──────────────────────────────────────────────
BASE_URL = "https://www.itu.int/itu-r/space/apps/ep/spaceexplorer/v1/sns/dictionaries"

# 監視対象の管理機関コード
MONITOR_ADMS = ["JPN"]

# 監視対象 special_section コード（新着として通知するもの）
WATCH_SECTIONS = {"API/A", "API/B", "API/C", "CR/C", "CR/D", "CR/E", "CR/F",
                  "AR11/A", "AR11/B", "AR11/C", "AR11/D", "AR14/C", "AR14/D"}


# ── 設定読み込み ───────────────────────────────────────────
def load_config() -> dict:
    """config.yaml またはEnvironment Variables から設定を読み込む。"""
    cfg = {}

    # まず config.yaml を試みる（ローカル開発用）
    if CONFIG_FILE.exists():
        with open(CONFIG_FILE) as f:
            cfg = yaml.safe_load(f) or {}

    # 環境変数で上書き（GitHub Actions 用）
    cfg.setdefault("cookie", os.environ.get("SPACEEXPLORER_COOKIE", ""))
    cfg.setdefault("gmail_user", os.environ.get("GMAIL_USER", ""))
    cfg.setdefault("gmail_app_password", os.environ.get("GMAIL_APP_PASSWORD", ""))
    cfg.setdefault("notify_email", os.environ.get("NOTIFY_EMAIL", ""))

    return cfg


# ── state.json ────────────────────────────────────────────
def load_state() -> dict:
    if STATE_FILE.exists():
        return json.loads(STATE_FILE.read_text())
    return {}


def save_state(state: dict) -> None:
    STATE_FILE.write_text(json.dumps(state, ensure_ascii=False, indent=2))
    log.info("state.json を更新しました")


# ── API クライアント ───────────────────────────────────────
def make_session(cookie: str) -> requests.Session:
    session = requests.Session()
    session.headers.update({
        "Accept": "*/*",
        "Accept-Language": "ja,en-US;q=0.9,en;q=0.8",
        "Cache-Control": "no-cache",
        "Connection": "keep-alive",
        "Referer": "https://www.itu.int/itu-r/space/apps/public/spaceexplorer/networks-explorer",
        "Sec-Fetch-Dest": "empty",
        "Sec-Fetch-Mode": "cors",
        "Sec-Fetch-Site": "same-origin",
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36",
    })
    if cookie:
        session.headers["Cookie"] = cookie
    return session


def get_counts(session: requests.Session, adm: str) -> dict:
    """counts エンドポイントを取得（軽量チェック用）。"""
    url = f"{BASE_URL}/counts"
    r = session.get(url, params={"adm": adm}, timeout=30)
    r.raise_for_status()
    return r.json()


def get_satellites(session: requests.Session, adm: str) -> list[dict]:
    """satellites エンドポイントを取得（差分検出用）。"""
    url = f"{BASE_URL}/satellites"
    r = session.get(url, params={"adm": adm}, timeout=30)
    r.raise_for_status()
    return r.json().get("satellites", [])


# ── 差分検出 ──────────────────────────────────────────────
def detect_new_filings(satellites: list[dict], prev_names: set[str]) -> list[dict]:
    """前回状態と比較して新規ファイリングを返す。"""
    new = []
    for sat in satellites:
        name = sat["sat_name"].strip()
        if name not in prev_names:
            new.append(sat)
    return new


# ── メール送信 ────────────────────────────────────────────
def build_email_html(new_filings: dict[str, list[dict]], counts_summary: dict) -> str:
    today = date.today().isoformat()
    total_new = sum(len(v) for v in new_filings.values())

    rows = ""
    for adm, filings in new_filings.items():
        for f in filings:
            geo_label = "GSO" if f["geo"] else "NGSO"
            rows += f"<tr><td>{adm}</td><td>{f['sat_name'].strip()}</td><td>{geo_label}</td></tr>\n"

    counts_rows = ""
    for adm, c in counts_summary.items():
        np = c.get("nonPlan", {})
        counts_rows += (
            f"<tr><td>{adm}</td>"
            f"<td>{np.get('advancePublications', '-')}</td>"
            f"<td>{np.get('coordination', '-')}</td>"
            f"<td>{np.get('notification', '-')}</td>"
            f"<td>{c.get('current', '-')}</td></tr>\n"
        )

    return f"""<!DOCTYPE html>
<html lang="ja">
<head><meta charset="UTF-8">
<style>
  body {{ font-family: Arial, sans-serif; font-size: 14px; color: #333; }}
  h2 {{ color: #1a5276; }}
  table {{ border-collapse: collapse; width: 100%; margin-bottom: 20px; }}
  th {{ background: #1a5276; color: #fff; padding: 8px 12px; text-align: left; }}
  td {{ border: 1px solid #ddd; padding: 7px 12px; }}
  tr:nth-child(even) {{ background: #f4f6f7; }}
  .badge {{ display: inline-block; background: #e74c3c; color: #fff;
            border-radius: 4px; padding: 2px 8px; font-size: 12px; }}
</style>
</head>
<body>
<h2>🛰 ITU Filing Monitor — 新規ファイリング通知</h2>
<p>実行日: {today} &nbsp;<span class="badge">新規 {total_new} 件</span></p>

<h3>新規検出ファイリング</h3>
<table>
  <tr><th>ADM</th><th>Satellite Name</th><th>軌道</th></tr>
  {rows}
</table>

<h3>件数サマリ（現在）</h3>
<table>
  <tr><th>ADM</th><th>API</th><th>CR</th><th>Notification</th><th>合計</th></tr>
  {counts_rows}
</table>

<p style="color:#888;font-size:12px;">
  Source: <a href="https://www.itu.int/itu-r/space/apps/public/spaceexplorer/networks-explorer">ITU SpaceExplorer</a>
</p>
</body>
</html>"""


def send_email(html: str, cfg: dict, dry_run: bool) -> None:
    subject = f"[ITU Filing] 新規ファイリング {date.today().isoformat()}"
    msg = MIMEMultipart("alternative")
    msg["Subject"] = subject
    msg["From"] = cfg["gmail_user"]
    msg["To"] = cfg["notify_email"]
    msg.attach(MIMEText(html, "html"))

    if dry_run:
        log.info(f"[dry-run] メール送信をスキップ: {subject}")
        PREVIEW_FILE.write_text(html)
        log.info(f"プレビューを保存しました: {PREVIEW_FILE}")
        return

    with smtplib.SMTP_SSL("smtp.gmail.com", 465) as smtp:
        smtp.login(cfg["gmail_user"], cfg["gmail_app_password"])
        smtp.sendmail(cfg["gmail_user"], cfg["notify_email"], msg.as_string())
    log.info(f"メール送信完了: {subject}")


# ── メイン ────────────────────────────────────────────────
def main() -> None:
    parser = argparse.ArgumentParser(description="ITU Filing Monitor")
    parser.add_argument("--dry-run", action="store_true", help="メール送信なし（テスト用）")
    parser.add_argument("--debug", action="store_true", help="HTMLプレビューを保存して終了")
    parser.add_argument("--force", action="store_true", help="変化なしでも強制実行")
    args = parser.parse_args()

    cfg = load_config()
    if not cfg.get("cookie"):
        log.warning("SPACEEXPLORER_COOKIE が未設定です。認証なしで試みます。")

    session = make_session(cfg.get("cookie", ""))
    state = load_state()
    new_state = {}
    all_new_filings: dict[str, list[dict]] = {}
    counts_summary: dict[str, dict] = {}

    for adm in MONITOR_ADMS:
        log.info(f"--- {adm} を確認中 ---")

        # Step 1: counts で件数チェック（軽量）
        try:
            counts_data = get_counts(session, adm)
        except Exception as e:
            log.error(f"counts 取得失敗 ({adm}): {e}")
            continue

        counts = counts_data.get("counts", {})
        current_total = counts.get("current", 0)
        np_counts = counts.get("regProcess", {}).get("nonPlan", {})
        counts_summary[adm] = {
            "current": current_total,
            "nonPlan": np_counts,
        }

        prev_total = state.get(adm, {}).get("total", -1)
        log.info(f"{adm}: 現在 {current_total} 件（前回 {prev_total} 件）")

        if current_total == prev_total and not args.force:
            log.info(f"{adm}: 変化なし → スキップ")
            new_state[adm] = state.get(adm, {})
            continue

        # Step 2: 変化あり → satellites で差分特定
        try:
            satellites = get_satellites(session, adm)
        except Exception as e:
            log.error(f"satellites 取得失敗 ({adm}): {e}")
            continue

        prev_names = set(state.get(adm, {}).get("sat_names", []))
        new_filings = detect_new_filings(satellites, prev_names)

        if new_filings:
            log.info(f"🆕 {adm}: 新規 {len(new_filings)} 件検出")
            for f in new_filings:
                geo = "GSO" if f["geo"] else "NGSO"
                log.info(f"  New ({geo}): {f['sat_name'].strip()}")
            all_new_filings[adm] = new_filings
        else:
            log.info(f"{adm}: 件数変化あるが sat_name に差異なし（修正・削除の可能性）")

        new_state[adm] = {
            "total": current_total,
            "sat_names": [s["sat_name"].strip() for s in satellites],
        }

    # 通知
    if all_new_filings:
        html = build_email_html(all_new_filings, counts_summary)

        if args.debug:
            PREVIEW_FILE.write_text(html)
            log.info(f"プレビュー保存: {PREVIEW_FILE}")
        else:
            send_email(html, cfg, dry_run=args.dry_run)
    else:
        log.info("新規ファイリングなし → メール送信なし")

    # state 更新（新規取得があった adm のみ上書き）
    merged_state = {**state, **new_state}
    save_state(merged_state)
    log.info("Done.")


if __name__ == "__main__":
    main()
