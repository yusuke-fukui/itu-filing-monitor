# Claude Codeへの指示：Streamlitアプリに「使い方」タブを追加する
#
# 以下の内容を既存の streamlit_app.py（またはメインファイル）に組み込んでください。
# 既存のタブ構造に応じて適宜調整してください。
#
# ─────────────────────────────────────────
# 【実装パターン】
#
# 既存コードにタブがある場合（例：tab1, tab2 が既に存在する場合）：
#
#   tab1, tab2, tab_guide = st.tabs(["既存タブ1", "既存タブ2", "使い方"])
#   with tab_guide:
#       show_usage_guide()
#
# ─────────────────────────────────────────

import streamlit as st
from pathlib import Path


def show_usage_guide():
    """使い方ガイドページを表示する"""
    
    # Markdownファイルを読み込んで表示
    guide_path = Path(__file__).parent / "pages" / "usage_guide.md"
    if guide_path.exists():
        content = guide_path.read_text(encoding="utf-8")
        st.markdown(content)
    else:
        # ファイルがない場合はインラインで表示
        _show_inline_guide()


def _show_inline_guide():
    """インライン版の使い方ガイド（usage_guide.mdが見つからない場合のフォールバック）"""
    
    st.title("使い方ガイド")
    st.markdown("このページでは、ITU衛星ファイリングの **Appendix 4データをPDFで確認する方法** を説明します。")
    
    st.divider()
    
    # 必要なソフトウェア
    st.header("必要なソフトウェア")
    st.markdown("""
| ソフトウェア | 用途 | 入手先 |
|---|---|---|
| **BR Space Software (SAM/BRSIS)** | データ閲覧・PDF出力 | [ITU公式](https://www.itu.int/en/ITU-R/software/Pages/space-network-software.aspx) |
| **brific_downloader.py** | mdbの自動ダウンロード | このリポジトリの `tools/` フォルダ |
""")
    
    st.divider()
    
    # Step 1
    st.header("Step 1：mdbファイルをダウンロードする")

    st.markdown("このWebアプリの **「BRIFIC mdb ダウンローダー」** タブからダウンロードできます。")
    st.markdown("""
1. 上部の **「BRIFIC mdb ダウンローダー」** タブをクリック
2. 対象のファイリングの **BR IFIC No.**（例: `3067`）を入力
3. **「ダウンロード後にzipを解凍してフォルダに保存」** にチェックが入っていることを確認（デフォルトON）
4. **「ダウンロード」** をクリック
5. zip と解凍済みmdbのダウンロードボタンが表示されるので、mdbをクリックして保存
""")
    st.info("BR IFIC No. は「衛星ファイリング検索」タブの結果テーブルの **BR IFIC No.** 列で確認できます。")
    st.success("mdbは自動解凍されます。`ificXXXX/` フォルダ内の `.mdb` ファイルをSAMで開いてください。")
    
    with st.expander("IFIC番号と発行年の目安"):
        st.markdown("""
| IFIC番号 | 発行年 |
|---|---|
| 3080〜 | 2026年〜 |
| 3050〜3079 | 2025年 |
| 3020〜3049 | 2024年 |
| 2987〜3019 | 2023年 |
""")
    
    st.divider()

    # Step 1.5
    st.header("Step 1.5：古いmdbはv10にコンバートする（必要な場合のみ）")
    st.info("""
**このステップが必要なケース**
ダウンロードしたmdbが **v7 / v8 / v9 / v9.1 形式** の場合（古いIFIC号のmdb）。
2025年以降のIFIC号（3050〜）のmdbは最初からv10形式のため不要。
""")
    st.markdown("""
SAMの **「SRS convert」** タスクを使って、古い形式のmdbをv10に変換する。

1. **SAM** を起動
2. 右側パネルを下にスクロールして **「SRS convert」** を選択
3. 下部「Selected database」で **「Microsoft Access」** を選択
4. **「Browse」** をクリック → 変換したい古いmdb（例：`ific2764.mdb`）を選択
5. **「Start」** をクリック → BRSIS-SRSConvert が起動
6. 変換先ファイル名を指定して実行 → `ificXXXX_v10.mdb` が生成される
7. 生成されたv10のmdbを使って Step 2 へ進む
""")
    with st.expander("バージョンの見分け方"):
        st.markdown("""
- ファイル名に `_v10` が付いていれば **v10形式**（コンバート不要）
- 付いていない場合はコンバートが必要な可能性がある
- SAMのタスク説明：「Convert an SNS formatted database from v7/v8/v9/v9.1 to v10」
""")

    st.divider()

    # Step 2
    st.header("Step 2：SAMを起動してmdbを読み込む")
    st.markdown("""
1. **SAM**（Space Application Manager）を起動
2. 右側のタスク一覧から **「Publication」** を選択
3. 下部「Selected database」で **「Microsoft Access」** を選択
4. **「Browse」** をクリック → ダウンロードした `ificXXXX_v10.mdb` を選択
5. 画面下部に `Selected database: ificXXXX_v10.mdb` と表示されることを確認
6. **「Start」** をクリック → **BRSIS - Publication** が起動
""")

    st.divider()
    
    # Step 3
    st.header("Step 3：ファイリングを検索する")
    st.markdown("""
1. **BRSIS - Publication** 画面が開く
2. 「Notice Id.」右の **虫眼鏡アイコン** をクリック → **Notice Finder** が開く
3. **「Type of Notice」** からカテゴリを選択：
""")
    st.markdown("""
| 選択肢 | 対応する手続き |
|---|---|
| Advance Publication | API（事前通知） |
| Coordination | CR（調整要求） |
| Notification | 登録通知（最も一般的） |
""")
    st.markdown("""
4. ラジオボタンをクリックするとリストにファイリングが表示される
5. **Adm列のフィルター**（フィルターアイコン）で `CHN` などと入力して絞り込む
6. 対象ネットワークをダブルクリック → Publication画面に戻る
""")

    st.divider()
    
    # Step 4
    st.header("Step 4：PDFとして出力する")
    st.markdown("""
1. 右側の **「Print Selection」** エリアを確認
2. 必要に応じてオプションを設定：
   - **Show GIMS graphics**：アンテナパターン・サービスエリア図も含める場合はチェック
   - その他はデフォルトのままでOK
3. 画面を下にスクロール → **「Print」** ボタンをクリック
4. 印刷ダイアログで **PDFプリンタ**（例：「Microsoft Print to PDF」）を選択
5. 保存先とファイル名を指定して保存
""")

    st.divider()
    
    # 注意事項
    st.header("注意事項")
    st.warning("""
- **`ificXXXX.mdb` はその号に掲載されたファイリングのみ収録**されています。特定のファイリングを探すには、上の表の `BR IFIC No.` 列を確認してください。
- **全登録済みファイリングを横断検索したい場合は `srsXXXX.mdb`** が必要ですが、こちらはBRIFIC DVD/ISOにのみ収録されており、SNS Onlineからは入手できません。
- mdbから出力したPDFは**参考資料扱い**です。規制上の公式参照文書はBRIFICに収録されたPDF形式のPart / Special Sectionです。
""")
    
    # 関連リンク
    st.header("関連リンク")
    st.markdown("""
- [SNS Online（mdb無料ダウンロード）](https://www.itu.int/sns/wic/demowic.html)
- [BR Space Software ダウンロード](https://www.itu.int/en/ITU-R/software/Pages/space-network-software.aspx)
- [BR IFIC データベース説明](https://www.itu.int/en/ITU-R/space/Pages/brificDatabase.aspx)
- [ITU Space Explorer（オンライン検索）](https://www.itu.int/itu-r/space/apps/public/spaceexplorer/query-builder)
""")


# ─────────────────────────────────────────
# 【Claude Codeへの実装指示】
#
# 1. このファイル（usage_guide_tab.py）を streamlit_app.py と同じディレクトリに配置
# 2. pages/usage_guide.md を配置（同梱のMarkdownファイル）
# 3. streamlit_app.py の先頭に以下を追加：
#
#    from usage_guide_tab import show_usage_guide
#
# 4. 既存のタブ定義を以下のように拡張する：
#
#    【変更前の例】
#    tab1, tab2 = st.tabs(["ファイリング検索", "サマリ"])
#
#    【変更後】
#    tab1, tab2, tab_guide = st.tabs(["ファイリング検索", "サマリ", "使い方"])
#    with tab_guide:
#        show_usage_guide()
#
# 5. 既存タブの中身（with tab1: ... / with tab2: ...）はそのまま維持する
# ─────────────────────────────────────────
