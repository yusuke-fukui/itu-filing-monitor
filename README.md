# itu-filing-monitor

ITU SpaceExplorer API から衛星ファイリングの状態を一括取得し、Excel に出力するツール。  
contributions-monitor の横展開として開発。

## できること

- 複数国のファイリングを一括取得（SpaceExplorer の手動操作が不要）
- 周波数帯・軌道位置でのフィルタリング
- 衛星名での部分一致検索（`--filter` オプション）
- GSO / NGSO シート分けで Excel 出力
- 調査条件・実行日時を先頭シートに自動記録
- 手続き変遷シートの生成（`latest_brific: false` のとき）

## セットアップ
```bash
git clone https://github.com/yusuke-fukui/itu-filing-monitor.git
cd itu-filing-monitor
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
cp config.template.yaml config.yaml
```

## 実行方法
```bash
source venv/bin/activate

# 基本実行
python3 src/survey.py --config survey_configs/jpn_all.yaml

# 衛星名でフィルタ（複数キーワード可）
python3 src/survey.py --config survey_configs/usa_all.yaml --filter DBSD Terrestar
```

## ITU国コードの注意点

| 国 | ITUコード |
|---|---|
| 日本 | J |
| 英国 | G |
| ドイツ | D |
| フランス | F |
| 中国 | CHN |
| 米国 | USA |
