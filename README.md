# Google Maps 施設・レビューデータ取得

WebAppからGitHub Issueを作成し、GitHub Actions経由で施設・レビューCSVをPrivateデータリポジトリへ保存するシステムです。

移管後の運用リポジトリは`jmh8128494-cloud/brightdata_ELT`、公開WebAppは`https://jmh8128494-cloud.github.io/brightdata_ELT/webapp/`です。

## WebAppのワークフロー

| WebAppグループ | WebApp表示 | コマンド | データソース |
|---|---|---|---|
| 現在の運用 | 施設・レビュー取得 (Google Places API) | `/run-facility-places` | Google Places API (New) |
| 現在の運用 | レビュー取得・新仕様逐次実行 | `/run-reviews-sequential` | Bright Data Dataset / Web Scraper API |
| SERP API再開後 | レビュー取得 (Reviews) | `/run-reviews` | Bright Data SERP API |
| SERP API再開後 | 施設データ取得 (Facility) | `/run-facility` | Bright Data SERP API |
| SERP API再開後 | レビュー取得・30日関連度ランク付き | `/run-reviews-relevance` | Dataset + SERP API |

SERP依存の3処理は、将来再開できるようコードと選択肢を保持しています。再開時は[`docs/SERP_API_REACTIVATION_GUIDE.md`](docs/SERP_API_REACTIVATION_GUIDE.md)に従って小規模確認を行います。

Google Places APIはオーナー返信を提供しません。返信が必要なレビュー取得にはDataset逐次版を使用します。すべてのレビューCSVは[`review_schema.py`](review_schema.py)の共通15列で出力します。

## リポジトリ構成

- このリポジトリ: Pythonコード、GitHub Actions、WebApp、ドキュメント
- `jmh8128494-cloud/googlemap`（Private）: 設定、入力CSV、結果CSV

主なファイル:

- `main.py`: Google Places API版
- `get_reviews_from_dental_new.py`: Bright Data Datasetレビュー取得
- `reviews_BrightData_50.py`: SERPレビュー取得（SERP再開用に保持）
- `.github/workflows/issue-ops-universal.yml`: Issueの検証・権限判定・処理分岐
- `docs/webapp/`: GitHub Pages用WebApp
- `docs/USER_OPERATION_MANUAL.md`: 日常操作、入出力、重複排除、ID採番の利用者向け正本
- `docs/CLIENT_ACCEPTANCE_TEST_GUIDE.md`: お客様側の受入テスト
- `docs/CLIENT_HANDOVER_GUIDE.md`: 運用開始・移管手順
- `docs/ADDRESS_CSV_GUIDE.md`: 住所CSV・検索キーワード・不正テンプレートの説明
- `docs/n8n_google_reviews_ops.md`: n8nとGoogleログイン状態のローカル操作
- `docs/GITHUB_ACTIONS_RUNTIME_AND_VISIBILITY.md`: Public／Privateと長時間処理の判断資料

Bright Dataへ同時に渡す処理数は全経路で最大20です。Dataset逐次版のWebAppは「Bright Data同時処理数」を20件、GitHub Actionsの並列ジョブ数を1に固定して表示を簡素化しています。Issue・workflow・Pythonでは引き続き`api_batch_size × max_parallel_jobs <= 20`を検証します。

## ローカルテスト

```powershell
$env:PYTHONIOENCODING='utf-8'
python -m unittest discover -s tests -v
```

実APIを呼ぶ受入テストは、API費用とPrivateデータ更新を伴います。クライアント向け手順書に従い、1処理ずつ小規模に実行してください。
