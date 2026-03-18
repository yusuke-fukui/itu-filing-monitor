# itu-filing-monitor

ITU SpaceExplorer API を監視し、新規衛星ファイリングをメールで通知する Python スクリプト。  
GitHub Actions で週2回自動実行。

## 監視対象

| 管理機関 | 対象 |
|---|---|
| JPN | 日本のファイリング全件 |

通知対象の手続き種別：`API/A`, `API/B`, `CR/C`〜`CR/F`, `AR11/A`〜`AR11/D`

## セットアップ

### 1. リポジトリのクローン

```bash
git clone https://github.com/yusuke-fukui/itu-filing-monitor.git
cd itu-filing-monitor
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### 2. config.yaml の作成

```bash
cp config.template.yaml config.yaml
```

`config.yaml` を編集して以下を設定：

- `cookie`: ブラウザで SpaceExplorer を開き、DevTools → Network → `satellites?adm=...` → Cookie ヘッダーをコピー
- `gmail_user`: 送信元 Gmail アドレス
- `gmail_app_password`: Google アカウント → セキュリティ → アプリパスワード（16文字）
- `notify_email`: 通知先メールアドレス

### 3. ローカル実行

```bash
# テスト実行（メール送信なし）
python3 src/monitor.py --dry-run

# 本番実行
python3 src/monitor.py

# HTMLプレビュー確認
python3 src/monitor.py --debug
open data/email_preview.html

# 強制実行（前回と件数変化なくても実行）
python3 src/monitor.py --force --dry-run
```

## GitHub Actions の設定

### Secrets の登録

[Settings → Secrets and variables → Actions](https://github.com/yusuke-fukui/itu-filing-monitor/settings/secrets/actions) に以下を登録：

| Secret名 | 内容 |
|---|---|
| `SPACEEXPLORER_COOKIE` | ブラウザからコピーした Cookie 文字列 |
| `GMAIL_USER` | yusuke.fukui@gmail.com |
| `GMAIL_APP_PASSWORD` | Gmail アプリパスワード（16文字・スペースなし） |
| `NOTIFY_EMAIL` | KDDI メールアドレス |

### 実行スケジュール

毎週火・金曜日 UTC 22:00（日本時間翌朝7:00）に自動実行。  
ITU SpaceExplorer の隔週更新タイミングに合わせて週2回。

## Cookie の更新方法

Cookie の有効期限が切れた場合：

1. ブラウザで [SpaceExplorer](https://www.itu.int/itu-r/space/apps/public/spaceexplorer/networks-explorer) を開く
2. DevTools → Network → Fetch/XHR → `satellites?adm=...` をクリック
3. Headers → Cookie の値をコピー
4. GitHub Secrets の `SPACEEXPLORER_COOKIE` を更新

## ディレクトリ構造

```
itu-filing-monitor/
├── src/
│   └── monitor.py          # メインスクリプト
├── data/
│   └── state.json          # 前回取得時のファイリング記録
├── logs/
│   └── monitor.log
├── .github/
│   └── workflows/
│       └── monitor.yml
├── config.template.yaml
├── config.yaml             # ローカル用（git管理外）
├── requirements.txt
└── .gitignore
```

## state.json の構造

```json
{
  "JPN": {
    "total": 42,
    "sat_names": ["JCSAT-1", "JCSAT-2", ...]
  }
}
```

初回実行時は空の状態から全件を「新規」として検出・通知します。  
通知後に state.json が更新され、次回以降は差分のみ通知されます。
