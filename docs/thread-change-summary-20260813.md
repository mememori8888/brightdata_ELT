# このスレッドの変更記録

更新日: 2026-08-13

## 目的

このスレッドで確認・変更した内容を、後から見直しても経緯と現在の状態が分かるように記録する。

## 1. GitHub Actions の実行結果確認

最新の `オーケストレーション` 実行を確認した。

- 実行ID: `31649554338`
- 実行名: `[Reviews Sequential Job] 2026-08-11`
- 起動イベント: `issue_comment`
- 結果: `failure`
- 失敗ジョブ: `run-reviews-sequential / run-batches (2, 501, 1000)`
- 原因: 10個のAPIチャンクのうち1個が失敗し、`get_reviews_from_dental_new.py` が `RuntimeError: APIチャンクが 1 件失敗しました` で終了した。
- 取得済みデータ: 第2バッチでは687件の新規レビューが出力され、各バッチのActionsアーティファクトは保存されていた。

## 2. Dataset API のレビュー取得ソート表示

### 背景

Dataset APIの入力では `sort` を明示的に指定していないが、内部値として `qualityScore` が出力CSVの `レビュー取得ソート` 列に残っていた。Dataset APIが関連度順であると断定できないため、利用者に誤解を与える表示だった。

### 変更内容

対象ファイル:

- `get_reviews_from_dental_new.py`
- `reviews_BrightData_50.py`

`qualityScore`、空値、Dataset ID由来の既定値を、CSV出力時に次の表示へ変換する処理を追加した。

```text
新着順（Dataset ID）
```

既存の列名 `レビュー取得ソート` は変更していない。後日、関連度順の取得処理へ切り替える場合も、列スキーマを維持したまま値だけを変更できるようにしている。

### 既存CSVへの反映

ローカルの `add_marriage_review_2026-8-11.csv` について、`レビュー取得ソート` 列の `qualityScore` を全2,165行で `新着順（Dataset ID）` に置き換えた。

- ヘッダー: 変更なし
- 行数: 2,165行
- `qualityScore` 残存: 0件
- 行順および他列: 変更なし

このCSVはユーザーが手動で `mememori8888/googlemap` の `results` フォルダへpushした。

## 3. `/承認` フローの方針

承認フロー自体を全面廃止する方針は採用していない。Issue作成者によって承認要否を分ける方針に変更した。

### 現在の実装

対象ファイル:

- `.github/workflows/issue-ops-universal.yml`

Issue作成イベントでは、次のユーザーだけ `/承認` 不要で実行する。

- リポジトリオーナー。`author_association == OWNER` で判定
- `jmh8128494-cloud`
- `asahi26366`

上記以外のユーザーがIssueを作成した場合は、従来どおりプレビューを表示し、承認が必要な状態にする。

`/承認` コメントによる実行も、次のユーザーだけを許可する。

- リポジトリオーナー
- `jmh8128494-cloud`
- `asahi26366`

`CONTRIBUTOR` という関連付け全体を許可する実装は採用していない。GitHubの `CONTRIBUTOR` は書き込み権限を必ずしも意味せず、ユーザー名で2名に固定する方が要件に合い、安全である。

### セキュリティ上の注意

このワークフローは `contents: write`、`issues: write`、`actions: read` の権限を持ち、さらにプライベートリポジトリのデータとAPIシークレットを利用する。そのため、公開リポジトリでIssue作成者を広く自動実行対象にするのは危険である。

現在は、指定ユーザーとオーナー以外にはプレビュー・承認を要求する設計としている。ただし、Issue本文のパラメータ検証、同一Issueの重複実行防止、許可リストの一元管理は今後の改善候補である。

## 4. GitHubリポジトリへの反映状況

作業対象ワークスペースは `mememori8888/demo` である。

`mememori8888/googlemap` への直接pushを試したが、Codespacesの認証が `GITHUB_TOKEN` であり、次のエラーになった。

```text
403 Write access to repository not granted
```

その後、ユーザーがローカルターミナルからCSVを手動でpushした。ワークフロー変更については、この記録作成時点ではローカルの `demo` ワークスペースに未pushの差分として残っている。

## 5. 検証済み事項

- `issue-ops-universal.yml` のYAML構文: `YAML OK`
- Issue作成者の判定: `OWNER`、指定2名は `should_run=true`、その他は `preview`
- `/承認` 投稿者の判定: オーナーまたは指定2名のみ `should_run=true`
- Dataset API由来の `qualityScore` のCSV表示: `新着順（Dataset ID）`
- 既存CSVの `qualityScore` 残存: 0件

## 6. 起動経路ごとの適用範囲と今後の確認事項

Issue起点の全ワークフローについて、限定ユーザーが作成したIssueでは `/承認` を不要にした。ユーザー限定判定は共通ルーターの `issue-ops-universal.yml` に集約している。

ただし、各ワークフローの起動経路は分けて管理する必要がある。

- Issueから呼び出される再利用ワークフロー
- `workflow_dispatch` による手動実行
- `workflow_call` による呼び出し
- `push` などの自動実行

特に `workflow_dispatch` はGitHub UIのアクセス権で制御されるため、YAML内の `if` だけで完全なユーザー制限を実現できるとは限らない。公開リポジトリで厳密に制限するなら、GitHubのリポジトリ権限、Environment protection rules、またはサーバー側の許可リストも併用する必要がある。

## 7. Issue起点の全ワークフローへの承認省略

Issueイベントを直接受け取るワークフローは `issue-ops-universal.yml` だけであり、レビュー取得・施設取得などの個別ワークフローは、この共通ルーターから `workflow_call` で起動される。そのため、個別ワークフローへ重複したユーザー判定を追加せず、共通ルーターの入口で全処理に同じ制御を適用した。

### 固定許可リスト

`issue-ops-universal.yml` の `AUTO_RUN_USERS` に次のユーザーを定義している。

- リポジトリオーナー。`author_association == OWNER` で判定
- `jmh8128494-cloud`
- `asahi26366`

この3者がIssueを作成した場合、Issue本文のコマンドに該当する全ワークフローで `/承認` を要求せず、`should_run=true` として検証・実行へ進む。その他のIssue作成者は従来どおりプレビュー後に `/承認` が必要である。

`workflow_dispatch` の手動実行や、外部から直接呼び出す `workflow_call` はIssue作成イベントを持たないため、このIssue作成者ルールの対象外である。これらを同じユーザーに限定する場合は、GitHubリポジトリ権限やEnvironment保護ルールを併用する必要がある。
