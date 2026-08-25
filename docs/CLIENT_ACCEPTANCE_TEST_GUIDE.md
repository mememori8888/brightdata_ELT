# クライアント向け WebApp受入テスト手順書

この手順書は、引き継ぎ後のクライアント担当者が、WebAppからGitHub Actionsを起動し、結果CSVがプライベートデータリポジトリへ保存されることを確認するためのものです。

## 1. テスト対象

現在の受入テスト対象は次の3つです。

| 順番 | WebAppの表示名 | Issueコマンド | 状態 |
|---|---|---|---|
| 1 | 施設・レビュー取得 (Google Places API) | `/run-facility-places` | テスト対象 |
| 2 | レビュー取得 (Reviews) | `/run-reviews` | テスト対象 |
| 3 | レビュー取得・新仕様逐次実行 | `/run-reviews-sequential` | テスト対象 |

次の2つはBright DataのSERP APIを必要とします。現在はSERP APIを利用できないため、選択・実行しないでください。

- 施設データ取得 (Facility)
- レビュー取得・30日関連度ランク付き

施設を取得するときは「施設・レビュー取得 (Google Places API)」を使用します。

## 2. 事前準備

テスト担当者は、開始前に次を確認してください。

- GitHubへログインしている
- コードリポジトリとプライベートデータリポジトリを閲覧できる
- コードリポジトリのActionsを閲覧できる
- `PRIVATE_REPO_PAT`、`BRIGHTDATA_API_TOKEN`、`GOOGLE_MAPS_API_KEY`がActions Secretsへ登録されている
- プライベートデータリポジトリに次のテスト入力がある
  - `settings/address_test.csv`
  - `settings/exclude_gids.csv`
  - `results/fid_test.csv`
  - `results/care_roujin-home_test.csv`

API費用とプライベートデータリポジトリへの同時push競合を抑えるため、ワークフローは必ず1件ずつ実行してください。前のActionsが終了してから次を開始します。

## 3. 共通の実行方法

1. 公開WebAppを開く
   - 現行環境: `https://mememori8888.github.io/demo/webapp/`
   - 引き継ぎ後: `https://<GitHubアカウント>.github.io/<コードリポジトリ>/webapp/`
2. 「実行するワークフロー」を選択する
3. この手順書に記載されたテスト用の値を入力する
4. 「GitHubでIssueを作成」を押す
5. 表示されたIssue本文で、入力ファイル、出力ファイル、件数、日数を確認する
6. GitHubの「Create」を押してIssueを作成する
7. 実行権限のあるユーザーが作成した場合は自動実行される
8. 自動実行されない場合は、リポジトリオーナーがIssueへ `/承認` とコメントする
9. Issue内の「Actionsログ」リンクを開き、完了まで待つ
10. 完了後、Issueの完了コメント、Actionsの結果、出力CSVを確認する

出力ファイル名には実行日を付け、既存の本番ファイルを上書きしないでください。この文書では日付を`YYYYMMDD`と表記します。

## 4. テスト1: Google Places API版の施設・レビュー取得

### WebAppの入力値

1. 「施設・レビュー取得 (Google Places API)」を選択する
2. プリセットから「老人ホーム（テスト）」を選択する
3. 次の値が入っていることを確認する

| 項目 | 値 |
|---|---|
| 設定ファイル | `settings/care_roujin-home_test.json` |
| 住所CSV | `settings/address_test.csv` |
| 除外GID | `settings/exclude_gids.csv` |
| 検索キーワード | プリセットで自動入力された老人ホーム用キーワード |

4. 4つの出力欄で「新規ファイルを作成」を選び、次を入力する

| 項目 | テスト用ファイル名 |
|---|---|
| 施設出力CSV | `client_acceptance_places_facility_YYYYMMDD.csv` |
| レビュー出力CSV | `client_acceptance_places_review_YYYYMMDD.csv` |
| 増分施設出力CSV | `client_acceptance_places_facility_increment_YYYYMMDD.csv` |
| 増分レビュー出力CSV | `client_acceptance_places_review_increment_YYYYMMDD.csv` |

### 合格条件

- Actionsの`run-facility-places`が成功する
- Issueへ「ジョブ完了」がコメントされ、自動クローズされる
- プライベートデータリポジトリの`results/`に指定した4ファイルがある
- 施設CSVとレビューCSVにヘッダーがある
- APIから対象データが返った場合は、データ行が1件以上ある

件数はGoogle側の検索結果によって変動します。固定件数との一致ではなく、Actions成功、ファイル保存、CSV形式を合格判定の中心にします。

## 5. テスト2: 通常レビュー取得

### WebAppの入力値

1. 「レビュー取得 (Reviews)」を選択する
2. 次を入力する

| 項目 | 値 |
|---|---|
| 設定ファイル | `settings/settings.json` |
| FIDファイル | `results/fid_test.csv` |
| 開始行 | `1` |
| 処理件数 | `1` |
| 並列数 | `1` |
| レビュー出力CSV | 新規作成 `client_acceptance_reviews_YYYYMMDD.csv` |

### 合格条件

- Actionsの`run-reviews`が成功する
- Issueへ「ジョブ完了」がコメントされ、自動クローズされる
- `results/client_acceptance_reviews_YYYYMMDD.csv`が保存される
- CSVにレビュー用ヘッダーがある

指定したFIDに対象レビューがない場合、データ行が0件でも異常とは限りません。ActionsログにAPIエラーがなく、CSVが正常保存されていることを確認してください。

## 6. テスト3: 逐次レビュー取得

このテストは実データ取得まで確認しやすいよう、直近30日を指定します。

### WebAppの入力値

1. 「レビュー取得・新仕様逐次実行」を選択する
2. 次を入力する

| 項目 | 値 |
|---|---|
| 入力CSV | `results/care_roujin-home_test.csv` |
| 出力CSV | 新規作成 `client_acceptance_reviews_sequential_YYYYMMDD.csv` |
| days_back | `30` |
| start_from_batch | `1` |
| rows_per_batch | `20` |
| max_parallel_jobs | `1` |
| batch_wait | `1` |
| api_batch_size | `20` |
| max_wait_minutes | `10` |
| dataset_id | WebAppの初期値を使用 |
| skip_column | `web` |
| レポート生成 | 無効 |
| report_days | `30` |

### 合格条件

- `prepare`、`run-batches`、`merge-results`がすべて成功する
- Issueへ「ジョブ完了」がコメントされ、自動クローズされる
- `results/client_acceptance_reviews_sequential_YYYYMMDD.csv`が保存される
- CSVにレビュー用ヘッダーがある
- Bright Dataが期間内レビューを返した場合はデータ行が1件以上ある

Bright Dataのスナップショット完成待ちがあるため、数分かかります。今回の開発側テストでは全体で約8分でした。

## 7. Actionsと出力の確認方法

### Actions

GitHubのコードリポジトリで「Actions」→「オーケストレーション」→対象runを開きます。

合格時は、次が緑色になります。

- `parse-and-route`
- `validate-request`
- 選択したワークフローのジョブ
- `report-completion`

選択していないワークフローが`skipped`になるのは正常です。

### 出力CSV

プライベートデータリポジトリの`results/`を開き、指定したファイル名を検索します。

確認項目:

- ファイル名が指定どおりである
- 更新時刻が今回のテスト時刻である
- CSVの1行目にヘッダーがある
- 文字化けや列ずれがない
- 既存の本番CSVを上書きしていない

## 8. 結果の記録

クライアント担当者は、各テストについて次を記録してください。

| 項目 | 記録内容 |
|---|---|
| 実行日時 | 例: 2026-08-25 15:00 JST |
| 担当者 | GitHubユーザー名 |
| ワークフロー | WebAppで選択した名前 |
| Issue URL | 作成されたIssue |
| Actions URL | 実行run |
| Actions結果 | success / failure / cancelled |
| 出力ファイル | `results/...csv` |
| データ行数 | ヘッダーを除く行数 |
| 備考 | エラー、0件理由、再実行内容など |

3つのテスト結果をこの表でまとめ、開発担当者へ共有してください。Secretsの値、APIトークン、PATは記録・共有しないでください。

## 9. 今回の開発側テスト実績

2026年8月25日に、同じWebApp経路で次を確認しました。件数は参考値であり、クライアント側の固定合格件数ではありません。

| テスト | Issue | Actions | 結果 |
|---|---|---|---|
| Google Places API版 | [#23](https://github.com/mememori8888/demo/issues/23) | [run 32811243800](https://github.com/mememori8888/demo/actions/runs/32811243800) | 成功。施設20件、レビュー80件 |
| 通常レビュー | [#25](https://github.com/mememori8888/demo/issues/25) | [run 32812585775](https://github.com/mememori8888/demo/actions/runs/32812585775) | 成功。対象FIDのレビューは0件 |
| 逐次レビュー・30日 | [#27](https://github.com/mememori8888/demo/issues/27) | [run 32813489837](https://github.com/mememori8888/demo/actions/runs/32813489837) | 成功。レビュー5件 |
| Bright Data施設取得 | [#29](https://github.com/mememori8888/demo/issues/29) | [run 32815199054](https://github.com/mememori8888/demo/actions/runs/32815199054) | `PRIVATE_DATA_ROOT`修正を確認。SERPゾーン利用不可のためデータ0件 |
| 関連度付きレビュー | [#28](https://github.com/mememori8888/demo/issues/28) | [run 32814133948](https://github.com/mememori8888/demo/actions/runs/32814133948) | SERP API利用不可の連絡を受けキャンセル |

## 10. よくあるエラー

| 症状 | 対応 |
|---|---|
| Issueを作成してもActionsが動かない | オーナーまたは許可ユーザーが`/承認`とコメントする |
| `private-data`のcheckoutで失敗 | `PRIVATE_REPO_PAT`の対象リポジトリとContents権限を確認する |
| `PRIVATE_DATA_ROOT`エラー | コードリポジトリが修正コミット`fb9eae6`以降か確認する |
| Bright Dataで401/403 | `BRIGHTDATA_API_TOKEN`の有効性を確認する |
| `zone "serp_api2" not found` | SERP API対象の機能を実行している。Google Places API版または通常レビューへ切り替える |
| 逐次レビューが1日指定で0件になる | `days_back`を`30`にして再テストする |
| CSVが0件 | ActionsログでAPI成功かAPI失敗かを確認する。正常な検索0件と通信失敗を区別する |
| 結果が保存されない | `Save results to private repository`または`merge-results`のログを確認する |

同じ失敗を条件変更なしで繰り返さないでください。Issue URL、Actions URL、失敗したステップ、エラーメッセージを開発担当者へ共有してから再実行します。
