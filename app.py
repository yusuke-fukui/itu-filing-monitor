#!/usr/bin/env python3
"""
ITU Filing Tool - Streamlit Web App
survey.py と brific_downloader.py を統合したWebツール

起動方法:
  streamlit run app.py
"""

import io
import sys
import time
import zipfile
from pathlib import Path

import requests
import streamlit as st

# パス設定
ROOT = Path(__file__).parent
sys.path.insert(0, str(ROOT / "src"))

from survey import (
    build_excel,
    fetch_all,
    load_config,
    make_session,
)
from brific_downloader import (
    find_zip_url,
    fetch_year_page,
    guess_years,
    list_year,
    make_session as brific_session,
    resolve_zip_url,
)

# ── ページ設定 ────────────────────────────────────────────────
st.set_page_config(
    page_title="ITU Filing Tool",
    page_icon="🛰",
    layout="wide",
)

# ── ログイン認証 ──────────────────────────────────────────────
def check_login():
    if st.session_state.get("authenticated"):
        return True
    st.title("🛰 ITU Filing Tool")
    st.subheader("🔐 ログイン")
    with st.form("login_form"):
        username = st.text_input("ユーザーID")
        password = st.text_input("パスワード", type="password")
        submitted = st.form_submit_button("ログイン")
        if submitted:
            if username == "kddi" and password == "since2026":
                st.session_state["authenticated"] = True
                st.rerun()
            else:
                st.error("IDまたはパスワードが正しくありません")
    return False

if not check_login():
    st.stop()

# ── サイドバー：Cookie設定 ───────────────────────────────────
with st.sidebar:
    st.title("🛰 ITU Filing Tool")
    st.divider()
    # Streamlit Secrets から自動読み込み
    cookie = st.secrets.get("SPACEEXPLORER_COOKIE", "") if hasattr(st, "secrets") else ""
    if cookie:
        st.caption("✅ SpaceExplorer 認証済み")
    else:
        cookie = st.text_area(
            "🔑 SpaceExplorer Cookie",
            placeholder="BIGipServer...=...; TScb...=...;",
            height=120,
            help="ブラウザのDevTools → Network → Cookie の値を貼り付け",
        )
    st.divider()
    if st.button("ログアウト"):
        st.session_state["authenticated"] = False
        st.rerun()
    st.caption("v1.0 | [GitHub](https://github.com/yusuke-fukui/itu-filing-monitor)")

# ── タブ ─────────────────────────────────────────────────────
tab1, tab2 = st.tabs(["📋 Filing Search", "📦 BRIFIC Download"])


# ════════════════════════════════════════════════════════════
# Tab 1: Filing Search
# ════════════════════════════════════════════════════════════
with tab1:
    st.header("衛星ファイリング検索")

    col1, col2 = st.columns(2)

    with col1:
        st.subheader("対象国 (ADM)")
        adm_input = st.text_input(
            "ITUコード（カンマ区切りで複数可）",
            placeholder="例: CHN  または  J, CHN, USA",
            help="日本=J, 中国=CHN, 米国=USA, 英国=G など。空欄で全国対象。",
        )

        st.subheader("軌道種別")
        col_geo, col_ngso = st.columns(2)
        with col_geo:
            use_geo = st.checkbox("GSO（静止軌道）", value=True)
        with col_ngso:
            use_ngso = st.checkbox("NGSO（非静止軌道）", value=True)

        st.subheader("軌道位置フィルタ（GSO・任意）")
        col_lon1, col_lon2 = st.columns(2)
        with col_lon1:
            lon_from = st.number_input("東経（開始）°", value=None, placeholder="例: 100", format="%g")
        with col_lon2:
            lon_to = st.number_input("東経（終了）°", value=None, placeholder="例: 150", format="%g")

    with col2:
        st.subheader("周波数フィルタ（任意）")
        col_f1, col_f2 = st.columns(2)
        with col_f1:
            freq_min = st.number_input("最小周波数 (MHz)", value=None, placeholder="例: 10700", format="%g")
        with col_f2:
            freq_max = st.number_input("最大周波数 (MHz)", value=None, placeholder="例: 12750", format="%g")

        st.subheader("手続き種別")
        col_p1, col_p2, col_p3 = st.columns(3)
        with col_p1:
            use_api  = st.checkbox("API", value=True)
        with col_p2:
            use_coord = st.checkbox("CR", value=True)
        with col_p3:
            use_notif = st.checkbox("Notification", value=True)

        st.subheader("BR IFIC対象")
        latest_brific = st.radio(
            "表示範囲",
            ["最新のみ（Latest BR IFIC）", "全BR IFIC（変遷シートあり）"],
            index=0,
        )

        take = st.slider("1回の取得件数（take）", 100, 1000, 500, 100)

    label = st.text_input("ラベル（Excel ファイル名に使用）", value="survey")
    filter_words = st.text_input(
        "衛星名フィルタ（任意・スペース区切り）",
        placeholder="例: ACONNECT CHINASAT",
    )

    st.divider()
    run_btn = st.button("🔍 検索実行", type="primary", use_container_width=True)

    if run_btn:
        if not cookie:
            st.warning("⚠️ Cookie が未設定です。認証なしで試みます。")

        # config 組み立て
        adm_list = [a.strip() for a in adm_input.replace("、", ",").split(",") if a.strip()]
        cfg = {
            "adm":           adm_list,
            "orbit":         {"geo": use_geo, "ngso": use_ngso},
            "lon_from":      lon_from,
            "lon_to":        lon_to,
            "freq_min":      freq_min,
            "freq_max":      freq_max,
            "proc":          {"api": use_api, "coord": use_coord, "notification": use_notif},
            "latest_brific": latest_brific.startswith("最新"),
            "take":          take,
            "label":         label,
            "cookie":        cookie,
            "_config_path":  "（Web UI）",
        }

        session = make_session(cookie)

        with st.spinner("ITU SpaceExplorer からデータ取得中..."):
            try:
                rows = fetch_all(session, cfg)
            except requests.HTTPError as e:
                st.error(f"API取得失敗: {e}")
                rows = []

        if not rows:
            st.warning("取得結果が0件でした。設定や認証を確認してください。")
        else:
            # フィルタ適用
            if filter_words.strip():
                keywords = filter_words.strip().split()
                rows = [r for r in rows if any(
                    k.upper() in (r.get("sat_name") or "").upper() for k in keywords
                )]
                st.info(f"フィルタ適用後: {len(rows)} 件")

            st.success(f"✅ {len(rows)} 件取得しました")

            # 結果テーブル表示
            import pandas as pd
            from survey import parse_lon, proc_label, pdf_url, parse_freq
            display_data = []
            for r in rows:
                display_data.append({
                    "ADM":       r.get("adm", ""),
                    "衛星名":    (r.get("sat_name") or "").strip(),
                    "軌道位置":  parse_lon(r.get("long_nom")),
                    "手続き":    proc_label(r),
                    "受理日":    r.get("d_rcv", ""),
                    "BR IFIC":   r.get("wic_no"),
                    "掲載日":    r.get("d_wic", ""),
                    "保護期限":  r.get("d_prot_eff_max", ""),
                    "BIU期限":   r.get("d_inuse_max", ""),
                    "登録期限":  r.get("d_reg_limit_max", ""),
                })
            df = pd.DataFrame(display_data)
            st.dataframe(df, use_container_width=True, height=400)

            # Excel 生成 & ダウンロード
            from datetime import date
            today = date.today().strftime("%Y%m%d")
            output_filename = f"survey_{label}_{today}.xlsx"
            tmp_path = ROOT / "results" / output_filename
            tmp_path.parent.mkdir(exist_ok=True)

            with st.spinner("Excel 生成中..."):
                build_excel(rows, cfg, str(tmp_path))

            with open(tmp_path, "rb") as f:
                st.download_button(
                    label="📥 Excel ダウンロード",
                    data=f.read(),
                    file_name=output_filename,
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                    use_container_width=True,
                )


# ════════════════════════════════════════════════════════════
# Tab 2: BRIFIC Download
# ════════════════════════════════════════════════════════════
with tab2:
    st.header("BRIFIC mdb ダウンローダー")
    st.caption("ITU SNS Online から BRIFIC mdb (zip) をダウンロードします。認証不要。")

    col_a, col_b = st.columns([2, 1])

    with col_a:
        st.subheader("IFIC番号指定ダウンロード")
        ific_input = st.text_input(
            "IFIC番号（スペース区切りで複数可）",
            placeholder="例: 3067  または  3067 3066 3065",
        )
        do_extract = st.checkbox("ダウンロード後にzipを解凍する", value=False)
        dl_btn = st.button("📦 ダウンロード", type="primary")

    with col_b:
        st.subheader("年別一覧表示")
        list_year_input = st.number_input("年", value=2026, min_value=1998, max_value=2030, step=1)
        list_btn = st.button("📋 一覧表示")

    st.divider()

    # 年別一覧
    if list_btn:
        session_b = brific_session()
        soup, page_url = fetch_year_page(session_b, int(list_year_input))
        if soup is None:
            st.error(f"{int(list_year_input)}年のページが取得できませんでした。")
        else:
            from urllib.parse import urljoin
            import re
            items = []
            for a in soup.find_all("a", href=True):
                href = a["href"]
                if ".zip" in href and "ific" in href.lower():
                    full_url = urljoin(page_url, href)
                    m = re.search(r"ific(\d+)\.zip", href, re.IGNORECASE)
                    ific = int(m.group(1)) if m else 0
                    items.append({"IFIC番号": ific, "ZIP URL": full_url})
            if items:
                import pandas as pd
                df_list = pd.DataFrame(items).sort_values("IFIC番号", ascending=False)
                st.dataframe(df_list, use_container_width=True)
                st.info(f"{len(items)} 件")
            else:
                st.warning("該当なし")

    # ダウンロード
    if dl_btn:
        if not ific_input.strip():
            st.warning("IFIC番号を入力してください。")
        else:
            ific_numbers = [int(x) for x in ific_input.strip().split() if x.isdigit()]
            session_b = brific_session()
            results = {}

            progress = st.progress(0, text="処理中...")
            log_area = st.empty()
            logs = []

            for i, ific_no in enumerate(ific_numbers):
                if i > 0:
                    time.sleep(1)
                logs.append(f"**IFIC {ific_no}** を処理中...")
                log_area.markdown("\n\n".join(logs))

                url = resolve_zip_url(session_b, ific_no)
                if url is None:
                    logs.append(f"  ✗ IFIC {ific_no}: zipURLが見つかりません")
                    results[ific_no] = None
                else:
                    logs.append(f"  URL: `{url}`")
                    log_area.markdown("\n\n".join(logs))
                    try:
                        r = session_b.get(url, timeout=120)
                        r.raise_for_status()
                        zip_bytes = r.content
                        results[ific_no] = (f"ific{ific_no}.zip", zip_bytes)
                        logs.append(f"  ✅ IFIC {ific_no}: {len(zip_bytes):,} bytes")
                    except Exception as e:
                        logs.append(f"  ✗ IFIC {ific_no}: ダウンロード失敗 ({e})")
                        results[ific_no] = None

                log_area.markdown("\n\n".join(logs))
                progress.progress((i + 1) / len(ific_numbers), text=f"{i+1}/{len(ific_numbers)} 完了")

            progress.empty()

            # ダウンロードボタン表示
            st.divider()
            for ific_no, result in results.items():
                if result is None:
                    st.error(f"IFIC {ific_no}: 失敗")
                else:
                    fname, data = result
                    col_dl1, col_dl2 = st.columns([3, 1])
                    with col_dl1:
                        st.success(f"IFIC {ific_no}: {len(data):,} bytes")
                    with col_dl2:
                        st.download_button(
                            label=f"💾 {fname}",
                            data=data,
                            file_name=fname,
                            mime="application/zip",
                            key=f"dl_{ific_no}",
                        )

                    if do_extract:
                        with zipfile.ZipFile(io.BytesIO(data)) as zf:
                            mdb_names = [n for n in zf.namelist() if n.lower().endswith(".mdb")]
                            for mdb_name in mdb_names:
                                mdb_data = zf.read(mdb_name)
                                st.download_button(
                                    label=f"💾 {mdb_name} (mdb)",
                                    data=mdb_data,
                                    file_name=mdb_name,
                                    mime="application/octet-stream",
                                    key=f"mdb_{ific_no}_{mdb_name}",
                                )
