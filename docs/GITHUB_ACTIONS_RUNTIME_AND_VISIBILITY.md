# GitHub Actions・公開範囲・実行時間

更新日: 2026-08-25

## 結論

コードリポジトリをPublicにしている主な理由は、標準GitHub-hosted runnerのActions実行分数がPublicリポジトリでは無料になるためです。Publicにしても1ジョブの実行時間上限が長くなるわけではありません。

Privateへ変更することも可能ですが、月間のActions分数、超過料金、GitHub Pagesを使えるプランかを先に確認します。設定・入力・結果を保存する`googlemap`は引き続きPrivateにします。

## PublicとPrivateの違い

| 項目 | Publicコードリポジトリ | Privateコードリポジトリ |
|---|---|---|
| 標準GitHub-hosted runner | 無料 | プランの月間分数を消費し、超過分は課金対象 |
| 1ジョブの標準上限 | 原則6時間 | 原則6時間 |
| GitHub Pages | GitHub Freeでも利用可能 | Pro、Team、Enterprise等の対応プランが必要 |
| ソースコード | 誰でも閲覧可能 | 許可ユーザーのみ |
| Actionsログ | 公開 | 許可ユーザーのみ |

公式情報:

- [GitHub Actions billing](https://docs.github.com/en/billing/concepts/product-billing/github-actions)
- [Workflow syntax: timeout-minutes](https://docs.github.com/en/actions/reference/workflows-and-actions/workflow-syntax#jobsjob_idtimeout-minutes)
- [GitHub-hosted runners](https://docs.github.com/en/actions/reference/runners/github-hosted-runners)
- [GitHub Pages site creation](https://docs.github.com/en/pages/getting-started-with-github-pages/creating-a-github-pages-site)

## Privateにした場合の分数

GitHub公式の月間無料枠は、GitHub Freeが2,000分、GitHub Proが3,000分、GitHub Teamが3,000分です。枠を超えた分は支払方法とbudget設定に従って課金または停止します。

歯科医院のDataset逐次レビュー取得では、過去の全件処理に約2日半かかりました。これはおよそ60時間で、1台のrunnerが連続実行したと仮定する単純換算は約3,600 runner分です。実際の請求対象分数は、runnerが動いていない待ち時間を除き、matrixの並列ジョブ、セットアップ、再実行をjobごとに加算するため、対象runの`Usage`で確認します。

Privateへ変更しても処理内容が同じなら、経過時間の計画値はまず約2日半以上とします。ただし、Bright Dataの同時処理上限を20へ下げた後は以前より長くなる可能性があるため、10件、100件、1バッチの実測から全体時間を再計算します。

正確な分数は対象runの`Actions` → `Usage`で確認します。

## 6時間上限への対応

現在の大量処理は1つのジョブを2日半動かしていません。施設CSVを複数バッチへ分け、各ジョブを5時間以内にし、途中成果をArtifactへ保存して最後にマージします。

- 各GitHub-hosted job: 5時間以内
- 全バッチの完了: 約2日半の実績あり
- 失敗時: 成功バッチを残し、開始バッチを指定して再開

Public／Privateのどちらでも、この分割・途中保存・再開設計は必要です。

## 推奨判断

次の条件ならPublicのままを推奨します。

- コード自体を公開して問題がない
- 長時間の標準runner利用料金を抑えたい
- GitHub FreeでPagesを公開したい
- Secrets、設定、入力、結果をPrivateリポジトリへ分離できている

次の条件ならPrivateを検討します。

- ソースコードやActionsログの非公開を優先する
- Pro、Team等の必要プランとActions超過料金を許容できる
- 月間budgetと利用停止条件を設定できる
- Privateリポジトリ由来のPages公開条件を確認済み

Publicで運用する場合も、Actionsログへ施設データ、認証情報、API応答全文を出さないことが必須です。
