# Issueオーケストレーション仕様

更新日: 2026-08-25

## 概要

`.github/workflows/issue-ops-universal.yml`は、WebAppが作成したIssueを検証し、権限とコマンドに応じて再利用ワークフローへ処理を振り分けます。

```text
WebApp → Issue opened → parse-and-route → validate-request
                                      ↓
                              対象ワークフロー
                                      ↓
                        report-completion → Issue close
```

## 対応コマンドと現在の運用状態

| コマンド | 内部workflow値 | 呼出先 | 状態 |
|---|---|---|---|
| `/run-facility-places` | `facility_places` | `main_places_api.yml` | 使用する |
| `/run-reviews-sequential` | `reviews_sequential` | `reviews_local_interactive_sequential.yml` | 使用する |
| `/run-reviews` | `reviews` | `brightdata_reviews.yml` | SERPゾーン再開待ち |
| `/run-facility` | `facility` | `brightdata_facility.yml`相当処理 | SERPゾーン再開待ち |
| `/run-reviews-relevance` | `reviews_recent_relevance` | `reviews_recent_with_relevance.yml` | SERPゾーン再開待ち |

将来のSERP API再開に備え、ルーティング定義とWebAppの選択肢は残しています。現在の受入テストではSERP依存の3処理を選択しません。

## 起動と権限

起動イベント:

- `issues: opened`
- `issue_comment: created`

自動実行対象:

- リポジトリオーナー
- `.github/workflows/issue-ops-universal.yml`の`AUTO_RUN_USERS`
- 現在の許可リスト: `jmh8128494-cloud,asahi26366`

対象外ユーザーのIssueは見積もりプレビューで停止します。オーナーまたは許可ユーザーによる`/承認`コメントで実行できます。対象外ユーザー自身の`/承認`では実行されません。

## 実行シーケンス

1. Issue本文からコマンドとJSONブロックを抽出する
2. 作成者または承認者の権限を判定する
3. `validate-request`で必須キー、パス、Privateリポジトリ上の入力ファイルを検証する
4. 対象ワークフローだけを実行する
5. 成功時は出力リンクをコメントしてIssueを閉じる
6. 失敗・キャンセル時はActionsログのリンクをコメントする

選択していないジョブが`skipped`になるのは正常です。

## データの読書き

- コード: 合意した公開範囲のコードリポジトリ（Public推奨、Privateも選択可）
- 設定・入力・結果: `jmh8128494-cloud/googlemap`
- 認証: `PRIVATE_REPO_PAT`
- 主な結果: `googlemap/results/*.csv`

全workflowのcheckout先と完了コメント内のPrivateリポジトリURLは、移管先の`jmh8128494-cloud/googlemap`へ変更済みです。

## 入力検証

現在は次を実行前に検証します。

- Issue JSONの構文
- workflowごとの必須パラメータ
- 許可された`settings/*.json`、`settings/*.csv`、`results/*.csv`形式のパス
- `..`や想定外ディレクトリを含むパスの拒否
- Privateリポジトリ内の設定・入力ファイルの存在
- 対象ラッパースクリプトの存在

## 障害時の確認順

1. `parse-and-route`: コマンド、JSON、権限
2. `validate-request`: 必須値、パス、入力ファイル
3. 対象ジョブ: API認証、API応答、スナップショット
4. 保存ステップ: PAT、Privateリポジトリ権限、push競合
5. `report-completion`: Issueへの書込み権限

同じIssueを重複承認したり、複数のデータ更新処理を同時実行したりしないでください。
