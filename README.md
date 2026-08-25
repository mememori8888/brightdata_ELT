# Google Maps 施設・レビューデータ取得

WebAppからGitHub Issueを作成し、GitHub Actions経由で施設・レビューCSVをPrivateデータリポジトリへ保存するシステムです。

移管後の運用リポジトリは`jmh8128494-cloud/brightdata_ELT`、公開WebAppは`https://jmh8128494-cloud.github.io/brightdata_ELT/webapp/`です。

## 現在使用するワークフロー

| WebApp表示 | コマンド | データソース |
|---|---|---|
| 施設・レビュー取得 (Google Places API) | `/run-facility-places` | Google Places API (New) |
| レビュー取得・新仕様逐次実行 | `/run-reviews-sequential` | Bright Data Dataset / Web Scraper API |

Bright DataのSERP APIは現在利用できないため、`/run-reviews`、`/run-facility`、`/run-reviews-relevance`は運用対象外です。

Google Places APIはオーナー返信を提供しません。返信が必要なレビュー取得にはDataset逐次版を使用します。すべてのレビューCSVは[`review_schema.py`](review_schema.py)の共通15列で出力します。

## リポジトリ構成

- このリポジトリ: Pythonコード、GitHub Actions、WebApp、ドキュメント
- `jmh8128494-cloud/googlemap`（Private）: 設定、入力CSV、結果CSV

主なファイル:

- `main.py`: Google Places API版
- `get_reviews_from_dental_new.py`: Bright Data Datasetレビュー取得
- `reviews_BrightData_50.py`: SERPレビュー取得（現在利用不可、互換性維持）
- `.github/workflows/issue-ops-universal.yml`: Issueの検証・権限判定・処理分岐
- `docs/webapp/`: GitHub Pages用WebApp
- `docs/CLIENT_ACCEPTANCE_TEST_GUIDE.md`: お客様側の受入テスト
- `docs/CLIENT_HANDOVER_GUIDE.md`: 運用開始・移管手順

## ローカルテスト

```powershell
$env:PYTHONIOENCODING='utf-8'
python -m unittest discover -s tests -v
```

実APIを呼ぶ受入テストは、API費用とPrivateデータ更新を伴います。クライアント向け手順書に従い、1処理ずつ小規模に実行してください。
