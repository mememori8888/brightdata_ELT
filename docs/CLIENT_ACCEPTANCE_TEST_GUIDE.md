# クライアント向け WebApp受入テスト手順書

更新日: 2026-08-25

この手順書は、WebAppからGitHub Actionsを起動し、結果CSVがプライベートデータリポジトリへ保存されることをお客様側で確認するためのものです。

## 1. 現在のテスト対象

現在、受入テストを行うのは次の2つです。

| 順番 | WebAppの表示名 | Issueコマンド | API |
|---|---|---|---|
| 1 | 施設・レビュー取得 (Google Places API) | `/run-facility-places` | Google Places API (New) |
| 2 | レビュー取得・新仕様逐次実行 | `/run-reviews-sequential` | Bright Data Dataset / Web Scraper API |

次の3つはBright DataのSERP APIを必要とします。直近の確認ではSERPゾーンを利用できなかったため、初回受入テストでは選択・実行しません。将来ゾーンが再開した場合は別途テストします。

- レビュー取得 (Reviews): `/run-reviews`
- 施設データ取得 (Facility): `/run-facility`
- レビュー取得・30日関連度ランク付き: `/run-reviews-relevance`

将来SERP APIが再開できる可能性があるため、WebAppにはこの3項目も残しています。

## 2. 事前準備

- GitHubへログインしている
- コードリポジトリとプライベートデータリポジトリを閲覧できる
- コードリポジトリのActionsを閲覧できる
- コードリポジトリのSecretsに`PRIVATE_REPO_PAT`、`BRIGHTDATA_API_TOKEN`、`GOOGLE_MAPS_API_KEY`が登録されている
- プライベートデータリポジトリに次のテスト入力がある
  - `settings/address_test.csv`
  - `settings/exclude_gids.csv`
  - `results/care_roujin-home_test.csv`

API費用と同時pushの競合を避けるため、ワークフローは1件ずつ実行します。前のActionsが終了してから次を開始してください。

## 3. 共通の実行方法

1. 公開WebAppを開く
   - 移管後の環境: `https://jmh8128494-cloud.github.io/brightdata_ELT/webapp/`
2. 「実行するワークフロー」を選択する
3. この手順書に記載したテスト値を設定する
4. 「GitHubでIssueを作成」を押す
5. Issue本文の入力・出力ファイル、件数、日数を確認する
6. GitHubの「Create」を押す
7. オーナーまたは許可ユーザーが作成したIssueは自動実行される
8. それ以外のユーザーが作成した場合は、オーナーまたは許可ユーザーがIssueへ`/承認`とコメントする
9. Issue内の「Actionsログ」リンクから完了を待つ
10. Issueの完了コメント、Actionsの結果、出力CSVを確認する

出力ファイル名には実行日を付け、本番ファイルを上書きしないでください。以下では日付を`YYYYMMDD`と表記します。

## 4. テスト1: Google Places API版

### WebAppの入力値

1. 「施設・レビュー取得 (Google Places API)」を選択する
2. プリセット「老人ホーム（テスト）」を選択する
3. 次を確認する

| 項目 | 値 |
|---|---|
| 設定ファイル | `settings/care_roujin-home_test.json` |
| 住所CSV | `settings/address_test.csv` |
| 除外GID | `settings/exclude_gids.csv` |
| 検索キーワード | 老人ホーム用キーワードが自動入力されている |

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
- `googlemap/results/`に指定した4ファイルがある
- レビューCSVと増分レビューCSVのヘッダーが「レビューCSVの共通15列」と一致する
- APIから対象データが返った場合はデータ行が1件以上ある
- 文字化け・列ずれがない

Google Places APIはオーナー返信を返しません。そのため`オーナー返信`、別処理用の関連度3列、`レビュー要約`は空欄が正常です。列自体がない場合は不合格です。

## 5. テスト2: Bright Data Dataset逐次レビュー取得

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
| dataset_id | WebAppの初期値 |
| skip_column | `web` |
| レポート生成 | 無効 |
| report_days | `30` |

### 合格条件

- `prepare`、`run-batches`、`merge-results`がすべて成功する
- Issueへ「ジョブ完了」がコメントされ、自動クローズされる
- `googlemap/results/client_acceptance_reviews_sequential_YYYYMMDD.csv`が保存される
- ヘッダーが「レビューCSVの共通15列」と一致する
- Bright Dataが期間内レビューを返した場合はデータ行が1件以上ある
- 取得元にオーナー返信があるレビューでは、`オーナー返信`へ値が保存される

スナップショット完成待ちのため、数分かかることがあります。期間内レビューが本当に0件の場合は成功扱いです。通信失敗やスナップショット失敗はActionsがエラーになります。

## 6. レビューCSVの共通15列

すべてのレビュー取得処理は次の順番で出力します。

```text
レビューID,施設ID,施設GID,レビュワー評価,レビュワー名,レビュー日時,レビュー本文,オーナー返信,レビュー表示順位,レビュー取得ソート,関連度ランク,関連度取得ソート,関連度取得日時,レビュー要約,レビューGID
```

| 列 | Google Places API | Dataset逐次取得 |
|---|---|---|
| オーナー返信 | API仕様により空欄 | 取得元に存在すれば保存 |
| レビュー表示順位 | Places API返却順 | Dataset返却順 |
| レビュー取得ソート | `関連度順（Google Places API）` | `新着順（Dataset ID）` |
| 関連度ランク・取得ソート・取得日時 | 空欄 | 通常の逐次取得では空欄 |
| レビュー要約 | 空欄 | 現在は空欄 |

既存の旧9列・旧12列CSVをPlaces API処理で更新した場合も、不足列を空欄で補ってこの15列へ統一されます。

## 7. Actionsと出力の確認

GitHubのコードリポジトリで「Actions」→「オーケストレーション」→対象runを開きます。合格時は`parse-and-route`、`validate-request`、選択した処理、`report-completion`が緑色です。選択していない処理が`skipped`になるのは正常です。

CSVでは次を確認します。

- ファイル名と更新時刻が今回の実行と一致する
- 1行目のヘッダーが共通15列と完全一致する
- データ行の各値が隣の列へずれていない
- 本番CSVを上書きしていない

## 8. 結果の記録

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
| 15列確認 | OK / NG |
| 備考 | エラー、0件理由、再実行内容など |

2つのテスト結果を共有してください。Secrets、APIトークン、PATの値は記録しません。

## 9. 開発側の確認実績

2026年8月25日に、移管元環境のWebApp経路で次を確認しています。

| 対象 | 移管元での結果 |
|---|---|
| Google Places API版 | 施設20件、レビュー80件を保存 |
| Dataset逐次レビュー | レビュー5件を保存 |

15列統一後は、ローカルの自動テストでGoogle Places、Dataset、SERPの列定義とCSV出力を確認しています。修正後の実API Actions再実行は行っていないため、移管後に本書の2テストを実施してください。SERPは実API通信ではなくCSV出力単体テストのみです。

## 10. よくあるエラー

| 症状 | 対応 |
|---|---|
| Issueを作成してもActionsが動かない | オーナーまたは許可ユーザーが`/承認`とコメントする |
| `private-data`のcheckoutで失敗 | `PRIVATE_REPO_PAT`の対象リポジトリと`Contents: Read and write`を確認する |
| Bright Dataで401/403 | `BRIGHTDATA_API_TOKEN`を確認する |
| `zone "..." not found` | SERP API対象機能を実行している。利用可能な2機能へ切り替える |
| 逐次レビューが1日指定で0件 | `days_back`を`30`にしてテストする |
| CSVが0件 | API成功の0件か通信失敗かをActionsログで区別する |
| 列が9列または12列のまま | コードリポジトリが15列統一対応後の版か確認する |
| 結果が保存されない | `Save results to private repository`または`merge-results`を確認する |

同じ条件で失敗を繰り返さず、Issue URL、Actions URL、失敗ステップ、エラーメッセージを開発担当者へ共有してください。
