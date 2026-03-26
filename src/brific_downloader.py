#!/usr/bin/env python3
"""
brific_downloader.py
ITU-R SNS Online から BRIFIC mdb (zip) を IFIC番号を指定してダウンロードするツール。

使い方:
  python3 src/brific_downloader.py 3067
  python3 src/brific_downloader.py 3067 3066 3065
  python3 src/brific_downloader.py --extract 3067
  python3 src/brific_downloader.py --outdir ~/Downloads/brific 3067
  python3 src/brific_downloader.py --list 2026
"""

import argparse
import sys
import time
import zipfile
from pathlib import Path

import requests
from bs4 import BeautifulSoup

# ── 定数 ─────────────────────────────────────────────────────
BASE_WIC   = "https://www.itu.int/sns/wic"
DEMO_URL   = f"{BASE_WIC}/demowic{{yy}}.html"
USER_AGENT = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"

# IFIC番号 → 発行年の対応テーブル（おおよその目安）
IFIC_YEAR_TABLE = [
    (1,    2463, 1984, 2001),
    (2464, 2529, 2002, 2004),
    (2530, 2629, 2005, 2008),
    (2630, 2729, 2009, 2012),
    (2730, 2829, 2013, 2016),
    (2830, 2929, 2017, 2020),
    (2930, 2986, 2021, 2022),
    (2987, 3019, 2023, 2023),
    (3020, 3049, 2024, 2024),
    (3050, 3079, 2025, 2025),
    (3080, 9999, 2026, 2026),
]


def guess_years(ific_no: int) -> list[int]:
    """IFIC番号から発行年の候補を返す（前後1年も含む）"""
    for lo, hi, y_start, y_end in IFIC_YEAR_TABLE:
        if lo <= ific_no <= hi:
            years = list(range(max(1984, y_start - 1), y_end + 2))
            return years
    return [2026, 2025]


def make_session() -> requests.Session:
    s = requests.Session()
    s.headers.update({"User-Agent": USER_AGENT})
    return s


def fetch_year_page(session: requests.Session, year: int) -> tuple[BeautifulSoup, str] | tuple[None, None]:
    """指定年の demowic{YY}.html を取得してパース。(soup, url) を返す"""
    yy = str(year)[2:]  # 下2桁
    url = DEMO_URL.format(yy=yy)
    try:
        r = session.get(url, timeout=30)
        if r.status_code == 404:
            return None, None
        r.raise_for_status()
        return BeautifulSoup(r.text, "html.parser"), url
    except requests.RequestException:
        return None, None


def find_zip_url(soup: BeautifulSoup, ific_no: int, page_url: str) -> str | None:
    """ページ内テーブルから指定IFIC番号のzipURLを探す"""
    from urllib.parse import urljoin
    for a in soup.find_all("a", href=True):
        href = a["href"]
        if f"ific{ific_no}.zip" in href:
            return urljoin(page_url, href)
    return None


def resolve_zip_url(session: requests.Session, ific_no: int) -> str | None:
    """IFIC番号 → zip URL を解決する"""
    candidate_years = guess_years(ific_no)
    print(f"  候補年: {candidate_years}")

    for year in candidate_years:
        print(f"  {year}年ページを確認中...", end=" ", flush=True)
        soup, page_url = fetch_year_page(session, year)
        if soup is None:
            print("取得失敗")
            continue
        url = find_zip_url(soup, ific_no, page_url)
        if url:
            print(f"✓ 発見")
            return url
        print("なし")
    return None


def download_zip(session: requests.Session, url: str, dest: Path) -> bool:
    """zipをダウンロードしてdestに保存。進捗をパーセント表示"""
    print(f"  ダウンロード中: {url}")
    try:
        r = session.get(url, stream=True, timeout=120)
        r.raise_for_status()
        total = int(r.headers.get("Content-Length", 0))
        downloaded = 0
        dest.parent.mkdir(parents=True, exist_ok=True)
        with open(dest, "wb") as f:
            for chunk in r.iter_content(chunk_size=8192):
                if chunk:
                    f.write(chunk)
                    downloaded += len(chunk)
                    if total:
                        pct = downloaded / total * 100
                        print(f"\r  {pct:.1f}% ({downloaded:,} / {total:,} bytes)", end="", flush=True)
        print()
        print(f"  保存完了: {dest}")
        return True
    except requests.RequestException as e:
        print(f"\n  ダウンロード失敗: {e}")
        return False


def extract_zip(zip_path: Path) -> list[Path]:
    """zipを解凍してmdbファイルのパスリストを返す"""
    out_dir = zip_path.parent / zip_path.stem
    out_dir.mkdir(exist_ok=True)
    with zipfile.ZipFile(zip_path) as zf:
        zf.extractall(out_dir)
        names = zf.namelist()
    mdb_files = [out_dir / n for n in names if n.lower().endswith(".mdb")]
    print(f"  解凍先: {out_dir}")
    for m in mdb_files:
        print(f"  .mdb: {m}")
    return mdb_files


def list_year(session: requests.Session, year: int):
    """指定年の全IFIC番号とzipURLを一覧表示"""
    print(f"=== {year}年 BRIFIC一覧 ===")
    soup, page_url = fetch_year_page(session, year)
    if soup is None:
        print(f"  {year}年のページが取得できませんでした。")
        return

    from urllib.parse import urljoin
    found = 0
    for a in soup.find_all("a", href=True):
        href = a["href"]
        if ".zip" in href and "ific" in href.lower():
            full_url = urljoin(page_url, href)
            # IFIC番号を抽出
            import re
            m = re.search(r"ific(\d+)\.zip", href, re.IGNORECASE)
            ific = m.group(1) if m else "?"
            print(f"  IFIC {ific:>5}: {full_url}")
            found += 1
    if found == 0:
        print("  （該当なし）")


def process_ific(session: requests.Session, ific_no: int, outdir: Path, do_extract: bool) -> bool:
    """1件のIFIC番号を処理して結果を返す"""
    print("=" * 50)
    print(f"IFIC {ific_no} を処理中...")

    dest = outdir / f"ific{ific_no}.zip"
    if dest.exists():
        print(f"  スキップ（既存）: {dest}")
        if do_extract:
            extract_zip(dest)
        return True

    url = resolve_zip_url(session, ific_no)
    if url is None:
        print(f"  ✗ zipURLが見つかりませんでした（IFIC {ific_no}）")
        return False

    print(f"  URL: {url}")
    ok = download_zip(session, url, dest)
    if ok and do_extract:
        extract_zip(dest)
    return ok


def main():
    parser = argparse.ArgumentParser(
        description="ITU-R BRIFIC mdb (zip) ダウンローダー",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    parser.add_argument("ific_numbers", nargs="*", type=int, metavar="IFIC",
                        help="ダウンロードするIFIC番号（複数可）")
    parser.add_argument("--list", type=int, metavar="YEAR",
                        help="指定年のIFIC一覧を表示")
    parser.add_argument("--no-extract", action="store_true",
                        help="解凍せずzipのまま保存する（デフォルトは自動解凍）")
    parser.add_argument("--outdir", type=Path, default=Path(__file__).parent.parent / "mdb",
                        help="保存先ディレクトリ（デフォルト: <project>/mdb）")
    args = parser.parse_args()

    if not args.list and not args.ific_numbers:
        parser.print_help()
        sys.exit(1)

    session = make_session()

    if args.list:
        list_year(session, args.list)
        return

    results = {}
    for i, ific_no in enumerate(args.ific_numbers):
        if i > 0:
            time.sleep(1)  # サーバー負荷軽減
        ok = process_ific(session, ific_no, args.outdir, not args.no_extract)
        results[ific_no] = ok

    print()
    print("=" * 50)
    print("処理結果:")
    for ific_no, ok in results.items():
        dest = args.outdir / f"ific{ific_no}.zip"
        if ok:
            print(f"  IFIC {ific_no}: ✓ {dest}")
        else:
            print(f"  IFIC {ific_no}: ✗ 失敗")


if __name__ == "__main__":
    main()
