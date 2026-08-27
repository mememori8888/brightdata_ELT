# GitHub Actions・公開範囲・実行時間

更新日: 2026-08-27

## 結論

コードリポジトリをPublicにする主な理由は、標準GitHub-hosted runnerのActions実行分数がPublicリポジトリでは無料になるためです。Publicにしても1ジョブの標準上限が6時間より長くなるわけではありません。

Privateへ変更することもできますが、月間Actions分数、超過料金、GitHub Pagesを利用できるプランかを事前に確認します。設定、入力、結果を保存する`jmh8128494-cloud/googlemap`はPrivateを維持します。

## PublicとPrivateの違い

| 項目 | Publicコードリポジトリ | Privateコードリポジトリ |
|---|---|---|
| 標準GitHub-hosted runner | 無料 | プランの月間分数を消費し、超過分は課金対象 |
| 1ジョブの標準上限 | 原則6時間 | 原則6時間 |
| GitHub Pages | GitHub Freeでも利用可能 | Pro、Team、Enterprise等の対応プランが必要 |
| ソースコード・Actionsログ | 公開 | 許可ユーザーのみ |

公式情報:

- [GitHub Actions billing](https://docs.github.com/en/billing/concepts/product-billing/github-actions)
- [Workflow syntax: timeout-minutes](https://docs.github.com/en/actions/reference/workflows-and-actions/workflow-syntax#jobsjob_idtimeout-minutes)
- [GitHub-hosted runners](https://docs.github.com/en/actions/reference/runners/github-hosted-runners)
- [GitHub Pages site creation](https://docs.github.com/en/pages/getting-started-with-github-pages/creating-a-github-pages-site)

## demoの長時間実行実績

確認対象は、demoリポジトリのDataset逐次レビュー全件runです。

| 項目 | 確認値 |
|---|---:|
| 経過時間 | 約60時間22分（約2日半） |
| matrixバッチ | 134バッチ（22～155） |
| 成功 | 94バッチ |
| 失敗 | 40バッチ |
| 6時間timeout | 0バッチ |
| マージ行数 | 66,358件 |
| 新規追加 | 34,227件 |
| Privateリポジトリ保存 | 成功 |

このrunは「全バッチ成功」ではありません。94バッチの成功成果をマージしてPrivateリポジトリへ保存できた部分完了です。Actions全体は40バッチの失敗によりfailureでした。

実行時の主設定は`rows_per_batch=500`、`api_batch_size=20`、`max_parallel_jobs=3`、`max_wait_minutes=90`でした。現在はBright Data全体上限20を守るため、`api_batch_size=20`、`max_parallel_jobs=1`へ固定しており、過去の60同時処理設定は復元しません。そのため現在設定の全件経過時間は、この過去実績より長くなる可能性があります。

## Privateにした場合の分数

約60時間22分は壁時計時間です。請求対象分数は、matrixの各job、セットアップ、マージ、再実行を合計するため、単純に60時間22分とはなりません。対象runの`Actions` → `Usage`で確認してください。

Privateへ変更する場合は、10件、100件、1バッチの順で現在設定を実測し、次を記録して月間利用量と予算を見積もります。

- 1 APIチャンクの平均時間と最大時間
- 500行バッチの平均時間と最大時間
- 予定バッチ数
- setup、Artifact、mergeの追加時間
- 失敗範囲の手動再実行分

## 6時間上限への対応

1つのjobを約2日半動かす設計ではありません。施設CSVを最大500行のmatrixバッチへ分け、次の明示上限を設定しています。

- stepを持つ全job: 最大300分
- Dataset API、Places API、SERP API、Playwrightの長時間step: 最大270分
- merge・復旧: 30～180分
- 検証・ルーティング・ファイル一覧: 30～60分

270分でAPI stepを止め、job上限までの残り30分で状態JSON、途中CSV、ログをArtifactとPrivateリポジトリへ保存します。逐次レビューは各APIチャンク後、施設取得は住所ごとにチェックポイントを更新します。

結果は次の3状態で扱います。

- `success`: 全対象が成功。Datasetの正常なレビュー0件も含む。
- `partial`: 成功成果があり、別のバッチ・住所が失敗またはソフト上限へ到達。
- `failed`: 成功成果がない、または入力・認証・API trigger等で開始できない。

逐次レビューの部分完了では成功バッチを必ずマージし、Issueへ失敗バッチ番号、開始行、終了行、完了チャンク数を表示します。自動再試行は行わず、該当範囲だけを手動再実行します。Google Places／SERP施設の部分完了は、同じ住所CSV・検索条件・出力先で再実行すると未処理住所から再開します。

詳しい上限と成果物は[`PROGRAM_AND_WORKFLOW_REFERENCE.md`](PROGRAM_AND_WORKFLOW_REFERENCE.md)を参照してください。

## 推奨判断

Publicのままが向く条件:

- コード自体を公開して問題がない
- 標準runner利用料金を抑えたい
- GitHub FreeでPagesを公開したい
- Secrets、設定、入力、結果をPrivateリポジトリへ分離できている

Privateが向く条件:

- ソースコードとActionsログの非公開を優先する
- 対応プランとActions超過料金を許容できる
- 月間budgetと利用停止条件を設定できる
- Private Pagesの利用条件を確認済み

Public運用でも、認証情報、Private CSVの内容、API応答全文をActionsログへ出さないことが必須です。
