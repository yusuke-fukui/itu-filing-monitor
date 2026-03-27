# 📖 使い方ガイド

このページでは、ITU衛星ファイリングの **Appendix 4データをPDFで確認する方法** を説明します。

---

## 🔧 必要なソフトウェア

| ソフトウェア | 用途 | 入手先 |
|---|---|---|
| **BR Space Software (SAM/BRSIS)** | データ閲覧・PDF出力 | [ITU公式](https://www.itu.int/en/ITU-R/software/Pages/space-network-software.aspx) |

---

## Step 1：mdbファイルをダウンロードする

**「📦 BRIFIC mdb ダウンローダー」** タブを使ってダウンロードします。

1. 上部の **「📦 BRIFIC mdb ダウンローダー」** タブをクリック
2. 「IFIC番号（スペース区切りで複数可）」に対象の **BR IFIC No.** を入力（例: `3067`）
   - BR IFIC No. は「📋 衛星ファイリング検索」の結果テーブルの **BR IFIC No.** 列で確認できます
3. **「ダウンロード後にzipを解凍してフォルダに保存」** にチェックが入っていることを確認（デフォルトON）
4. **「📦 ダウンロード」** をクリック
5. 処理完了後、**「💾 ificXXXX.mdb (mdb)」** ボタンをクリックしてmdbを保存

> **💡 IFIC番号と発行年の目安**
> | IFIC番号 | 発行年 |
> |---|---|
> | 3080〜 | 2026年〜 |
> | 3050〜3079 | 2025年 |
> | 3020〜3049 | 2024年 |
> | 2987〜3019 | 2023年 |

---

## Step 1.5：古いmdbはv10にコンバートする（必要な場合のみ）

> **このステップが必要なケース**
> ダウンロードしたmdbが **v7 / v8 / v9 / v9.1 形式**の場合（古いIFIC号のmdb）。
> 2025年以降のIFIC号（3050〜）のmdbは最初からv10形式のため不要。

SAMの **「SRS convert」** タスクを使って、古い形式のmdbをv10に変換する。

### 手順

1. **SAM** を起動
2. 右側パネルを下にスクロールして **「SRS convert」** を選択
3. 下部「Selected database」で **「Microsoft Access」** を選択
4. **「Browse」** をクリック → 変換したい古いmdb（例：`ific2764.mdb`）を選択
5. **「Start」** をクリック → BRSIS-SRSConvert が起動
6. 変換先ファイル名を指定して実行 → `ificXXXX_v10.mdb` が生成される
7. 生成されたv10のmdbを使って Step 2 へ進む

> **バージョンの見分け方**
> ファイル名に `_v10` が付いていればv10形式。付いていない場合はコンバートが必要な可能性がある。
> SAMのタスク説明に「Convert an SNS formatted database from v7/v8/v9/v9.1 to v10」と記載されている。

---

## Step 2：SAMを起動してmdbを読み込む

1. **SAM**（Space Application Manager）を起動
2. 右側のタスク一覧から **「Publication」** を選択
3. 下部「Selected database」で **「Microsoft Access」** を選択
4. **「Browse」** をクリック → ダウンロードした `ificXXXX_v10.mdb` を選択
5. 画面下部に `Selected database: ificXXXX_v10.mdb` と表示されることを確認
6. **「Start」** をクリック → **BRSIS - Publication** が起動

---

## Step 3：ファイリングを検索する

1. **BRSIS - Publication** 画面が開く
2. 「Notice Id.」右の **虫眼鏡アイコン** をクリック → **Notice Finder** が開く
3. **「Type of Notice」** からカテゴリを選択：

   | 選択肢 | 対応する手続き |
   |---|---|
   | Advance Publication | API（事前通知） |
   | Coordination | CR（調整要求） |
   | Notification | 登録通知（最も一般的） |

4. ラジオボタンをクリックするとリストにファイリングが表示される
5. **Adm列のフィルター**（🔤アイコン）で `CHN` などと入力して絞り込む
6. 対象ネットワークをダブルクリック → Publication画面に戻る

---

## Step 4：PDFとして出力する

1. 右側の **「Print Selection」** エリアを確認
2. 必要に応じてオプションを設定：
   - **Show GIMS graphics**：アンテナパターン・サービスエリア図も含める場合はチェック
   - その他はデフォルトのままでOK
3. 画面を下にスクロール → **「Print」** ボタンをクリック
4. 印刷ダイアログで **PDFプリンタ**（例：「Microsoft Print to PDF」）を選択
5. 保存先とファイル名を指定して保存

---

## ⚠️ 注意事項

- **`ificXXXX.mdb` はその号に掲載されたファイリングのみ収録**されています
  - 特定のファイリングを探すには、そのファイリングが掲載された号のBR IFIC番号（このアプリの `BR IFIC No.` 列）を確認してください
- **全登録済みファイリングを横断検索したい場合は `srsXXXX.mdb`** が必要ですが、こちらはBRIFIC DVD/ISOにのみ収録されており、SNS Onlineからは入手できません
- mdbから出力したPDFは**参考資料扱い**です。規制上の公式参照文書はBRIFICに収録されたPDF形式のPart / Special Sectionです

---

## 🔗 関連リンク

- [SNS Online（mdb無料ダウンロード）](https://www.itu.int/sns/wic/demowic.html)
- [BR Space Software ダウンロード](https://www.itu.int/en/ITU-R/software/Pages/space-network-software.aspx)
- [BR IFIC データベース説明](https://www.itu.int/en/ITU-R/space/Pages/brificDatabase.aspx)
- [ITU Space Explorer（オンライン検索）](https://www.itu.int/itu-r/space/apps/public/spaceexplorer/query-builder)
