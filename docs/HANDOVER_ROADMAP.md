# 引き渡しロードマップ

更新日: 2026-08-22

## 目的

受領者が、開発者の環境や認証情報に依存せず、システムの設定・実行・結果確認・障害対応・軽微な修正を自分で行える状態にする。

移行後の対象となる処理経路:

```text
Webapp → GitHub Issue → GitHub Actions → Bright Data API
                                      ↓
                              results/
                                      ↓
                              Issueへ完了通知
```

## 現状判定

| 項目 | 現状 | 判定 |
|---|---|---|
| Pythonコード・GitHub Actions | リポジトリに存在 | 要実行確認 |
| WebappからIssueを作成 | 実装あり | 要受入テスト |
| コード・設定・データの分離 | `demo`と`googlemap`に分散 | 1つの非公開リポジトリへ統合 |
| Bright Data接続 | 過去に成功記録あり | 受領者アカウントで再確認 |
| 最新のレビュー処理 | 2026-08-11に一部チャンク失敗 | 原因確認または既知問題として合意 |
| 依存スクリプト | 未配置の記録あり | 本番対象を確定し、修正または除外 |
| 新仕様Web Scraper API | ラッパーと実行ファイルあり | 非対話実行を検証 |
| 運用手順・障害対応 | 資料が分散 | 本書と手順書に集約 |

## 2026-08-22時点の進捗

### 完了

- 引き渡し作業を`handover-roadmap`ブランチへ分離した
- `reviews_brightData_new_version.py`の重複実装を整理した
- レビュー・施設ラッパーについて、データルートが見つからない場合にコードリポジトリへ書き込まず、エラー終了するよう変更した
- 無効な`PRIVATE_DATA_ROOT`で両ラッパーが終了コード1になることを確認した
- 対象ラッパーと`run_reviews_local_interactive.py`のPython構文を確認した
- 現行Actionsでは、施設処理は施設ラッパー、レビュー処理は`run_reviews_local_interactive.py`直接呼び出しであることを確認した

### この環境では未実施

- GitHub Secretsの存在・値の検証
- `googlemap`への読み書き権限の検証
- Bright Data APIへの接続と課金が発生する実データ処理
- GitHub Actionsの実行、再実行、結果コミットの確認
- 受領者アカウントによるWebappからのIssue作成

上記は、GitHub権限、受領者のSecrets、Bright Dataアカウント、テスト用データが必要であり、ローカルのコード検証だけでは完了扱いにしない。

## 統合先リポジトリ（確定）

- 移行先: `mememori8888/brightdata_ELT`
- このCodespacesの既定トークンは`demo`専用スコープのため、`brightdata_ELT`へは直接アクセスできないことを確認済み
- アクセスには、`Contents: Read and write`権限を持つ Personal Access Token（Fine-grained）が必要
- 2026-08-22: チャット上にPATが誤って貼り付けられた。当該トークンは漏えい扱いとし、GitHub側で失効(Revoke)済みであることを前提とする。以後、トークンはターミナルにのみ入力する運用に変更
- 現時点で`gh auth status`はCodespaces既定の`GITHUB_TOKEN`のままであり、`brightdata_ELT`への認証はまだ完了していない

## オーナー移行スコープ（2026-08-23確定）

- 移行対象: `googlemap`（プライベートデータ）と`brightdata_ELT`（統合先）の2リポジトリ
- `demo`はオーナー移行の対象外。現行オーナーのまま残す
- 移行先: 同一アカウント内の権限付与ではなく、**別GitHubアカウントへの所有権移転**（GitHub の Transfer ownership機能）
- 実際の「Transfer ownership」操作自体は、ユーザーが手作業でGitHub画面から行う
- こちら（エージェント）が担当するのは、**その手前の段階**まで
  - バックアップの取得と確認
  - `brightdata_ELT`への統合作業の完了
  - 移行後に必要な設定（Secrets再発行など）の明文化
  - 移行前チェックリストの整備

### 手動オーナー移行 前段階チェックリスト

- [x] `googlemap`のミラーバックアップ（`git clone --mirror`）を取得する — 完了(2026-08-23、`/workspaces/backups/googlemap.git`、270MB、ブランチ: main/master/copilot/collect-user-reviews/copilot/explore-agent-capabilities)
- [x] `brightdata_ELT`のミラーバックアップ（`git clone --mirror`）を取得する — 完了(2026-08-23、`/workspaces/backups/brightdata_ELT.git`、132KB、`main`ブランチのみ、内容は`README.md`のみで未統合の空リポジトリと確認)
- [x] `settings/`・`results/`の内容を最新版でバックアップする — 完了(2026-08-23、`googlemap`ミラーから`git archive`で展開、`/workspaces/backups/googlemap_worktree/`、settings 7.6M・results 195M)
- [x] `brightdata_ELT`へコード・Actions・Webappの統合を完了させる — 完了(2026-08-23、`handover-roadmap`ブランチの内容をそのまま`brightdata_ELT`の`main`へforce push。コミット`fb720e0`まで反映。`private-data`/`googlemap`連携ロジックは変更せず維持。push時にPATへ`Workflows: Read and write`権限の追加が必要だった)
- [x] ~~`demo`の各ワークフローが`googlemap`ではなく`brightdata_ELT`単体で完結するよう修正する（別リポジトリ依存を解消）~~ → **対象外(2026-08-23、ユーザー指示)**: `private-data`経由の`googlemap`連携ロジックは、他コードへの影響が読み切れないため変更しない。二重リポジトリ構成はそのまま維持する
- [ ] 移行後に新オーナー側で再発行が必要なSecretsを一覧化する（`BRIGHTDATA_API_TOKEN`、`BRIGHTDATA_ZONE_NAME`、`PRIVATE_REPO_PAT`、必要なら`GEMINI_API_KEY`）
- [ ] 旧オーナー（開発者）側のPAT・APIキーを、移行後に失効させる手順を明記する
- [ ] 上記すべて完了後にのみ、ユーザーが手作業で「Transfer ownership」を実行する

現時点でこのCodespacesの認証は`brightdata_ELT`へのアクセスが未確立のため、上記チェックリストのうち、ミラーバックアップと統合作業はまだ着手できない。次の1項目は、PATによる認証確立である。

### 認証作業ログ（2026-08-23）

- `gh auth login`をCodespaces既定`GITHUB_TOKEN`と競合させず実行するため、`unset GITHUB_TOKEN`が必要だった
- 新規PATでの認証後、`gh auth switch`でアクティブアカウントを切り替え、`brightdata_ELT`へのアクセスを確認した（Private、pushedAt 2026-08-22T13:02:59Z）
- `googlemap`は同じPATでアクセス不可。原因切り分け中に、チャットへ誤って貼られた旧PATが未失効のまま残っていたことが判明
- 旧PATは失効(Delete)済みであることを確認した
- 直後、`gh auth login`のトークン検証時に`API rate limit exceeded for user ID 42532462`が3回連続発生。REST API(`/user`)側の二次的なレート制限とみられ、`gh auth login`の再試行は行わない方針に切り替えた
- 代替として、`git ls-remote`にトークンをURL埋め込みで渡す方式（Git Smart HTTPプロトコル、REST APIとは別の窓口）で`googlemap`への到達性を確認し、成功した（ブランチ・PR参照が取得できた）
- `gh`コマンドでの操作は当面レート制限の影響を受ける可能性があるため、バックアップ等はまず`git`直接操作で進める

## 移行方針

引き渡し先は、コード・GitHub Actions・Webapp・設定・入力データ・結果データをまとめた1つのプライベートリポジトリとする。現在の`demo`と`googlemap`をそのまま運用させるのではなく、統合後のリポジトリを受領者の管理下に置く。

統合先リポジトリ: `mememori8888/brightdata_ELT`（作成済み、2026-08-22）

- 現在のCodespaces（`demo`用の一時トークン）からはアクセス不可を確認済み。プッシュ・Secrets設定・Actions確認は、受領者またはオーナー自身のGitHubログインで行う必要がある。

### 統合後の構成

```text
brightdata_ELT/
├── .github/workflows/
├── .github/scripts/
├── docs/webapp/
├── settings/
├── results/
├── scripts/
├── *.py
├── requirements.txt
└── README.md
```

### 統合で削除・簡略化する処理

- `googlemap`へのcheckout
- `private-data/`へのコピー
- `private-data/`からの結果書き戻し
- `PRIVATE_REPO_PAT`
- 2リポジトリ間の同期処理
- `PRIVATE_DATA_ROOT`の自動検出

### 統合時に手作業で必要な項目

- ~~新しいプライベートリポジトリの作成~~ → 完了（`mememori8888/brightdata_ELT`）
- `googlemap/settings/`と`googlemap/results/`の内容確認・移行
- GitHub IssuesとActionsの有効化
- GitHub Actionsの権限設定
- `BRIGHTDATA_API_TOKEN`と`BRIGHTDATA_ZONE_NAME`の登録
- 必要な場合の`GEMINI_API_KEY`登録
- 受領者への管理者権限付与
- Webappの公開方法決定
- APIキーや個人情報がGit履歴・Issue・ログに残っていないかの確認

この手作業は、現在のワークスペースから完了させることはできない。GitHub管理画面、`googlemap`の実データ、受領者アカウントが必要である。

## 第2項目: 統合対象の棚卸し

### このリポジトリから移行するもの

- `.github/workflows/`: GitHub Actions定義
- `.github/scripts/`: Actionsから呼び出す設定更新処理
- `docs/webapp/`: Issue作成用Webapp
- `scripts/`: API診断、レビュー統合、関連度処理
- Pythonエントリーポイント一式
- `requirements.txt`
- README、運用資料、変更履歴
- `n8n/`: n8nを本番対象とする場合のみ移行

### `googlemap`から手作業で移行するもの

- `settings/`内の設定JSON
- `results/`内の入力CSV
- 過去の結果CSVと必要な増分データ
- バックアップ対象と保持期間

### 移行前に確認するもの

- `settings/`と`results/`に個人情報・不要な秘密情報がないか
- Git履歴、Issue、ActionsログにAPIキーが残っていないか
- 入力CSVのファイル名と、Actionsのデフォルト値が一致しているか
- `n8n/`を現行運用するか
- 旧スクリプトと新仕様スクリプトのどちらを本番入口にするか

### 現時点の判定

このワークスペースでは、コード側の移行対象は確認できた。`googlemap`の実データ、履歴、個人情報の有無は確認できないため、データ移行と秘密情報監査は手作業項目として残す。

## Phase 0: 契約・対象範囲の確定

### 作業

- 引き渡すリポジトリを確定する: `demo`、`googlemap`
- 本番対象の処理を確定する
  - SERP APIによる施設取得
  - SERP APIによるレビュー取得
  - Web Scraper APIによるレビュー取得
  - 関連度処理・ヒートマップ処理
- 対象外の処理を明記する
  - 廃止予定のn8nワークフロー
  - 無効化されているGemini関連機能
  - 未使用の旧スクリプト
- 納品物、外部サービス料金、保守・追加修正の範囲を文書化する
- 未解決事項を「納品前に解消する項目」と「既知の制限」に分類する

### 完了条件

- 受領者が、何が納品対象で、何が対象外かを文書で確認できる
- 未解決事項に担当者と対応期限がある
- 外部API利用料と開発費の負担者が明記されている

## Phase 1: アカウント・権限の移管

### 作業

- `demo`の管理者または必要な書き込み権限を受領者へ付与する
- `googlemap`の読み書き権限を受領者へ付与する
- GitHub Actionsの実行・再実行・ログ閲覧権限を確認する
- Bright Dataの契約主体と支払方法を受領者側へ切り替える
- 受領者自身のBright Data APIトークンとゾーンを作成する
- 必要な場合、Gemini APIの契約とキーを受領者側で用意する
- 既存の開発者用PAT/APIキーは引き渡し後に失効させる

### GitHub Secrets

受領者のリポジトリに、平文で共有せず再発行した値を登録する。

- `BRIGHTDATA_API_TOKEN`
- `BRIGHTDATA_ZONE_NAME`
- `PRIVATE_REPO_PAT`
- 必要な場合は `GEMINI_API_KEY`

### 完了条件

- 受領者のアカウントだけで `googlemap`を読み書きできる
- Secretsの値を表示せず、存在確認と接続テストができる
- 開発者の認証情報を無効化しても処理が継続できる

## Phase 2: ソースコードと実行経路の確定

### 確認対象

- `facility_BrightData_20.py`
- `reviews_BrightData_50.py`
- `faiility_brightdata_new_version.py`
- `reviews_brightData_new_version.py`
- `run_reviews_local_interactive.py`
- `get_reviews_from_dental_new.py`
- `.github/workflows/issue-ops-universal.yml`
- 各処理用の再利用可能ワークフロー
- `requirements.txt`

### 作業

- 各コマンドが、どのPythonエントリーポイントを呼ぶかを一覧化する
- 対話型実行とGitHub Actions用の非対話実行を分離・確認する
- 入力CSV、設定JSON、出力CSVの場所と必須列を明記する
- `apply_custom_settings.py`、`search_optimizer.py`の参照を確認する
  - 本番に必要なら実装・配置する
  - 不要ならワークフローと文書から参照を削除する
- 新仕様Web Scraper APIのパラメータ引き渡しを実データで確認する
- n8nが本番対象か廃止対象かを決定し、不要なら明記する

### 完了条件

- 各処理について、入力・実行コマンド・出力・依存サービスが1枚の表で分かる
- 未配置ファイルを参照したままの本番経路がない
- GitHub Actionsから対話入力を要求されない
- 受領者がローカルで最小処理を再現できる

## Phase 3: フェイルセーフと障害対応の確認

### 作業

次の異常系をテストし、停止位置と案内を確認する。

- 不正なJSON
- 必須パラメータ不足
- 存在しないCSV
- `googlemap`へのアクセス権不足
- Bright Dataの401/403
- Bright Dataの429または5xx
- APIタイムアウト
- バッチ数がGitHub Actionsの上限を超える場合
- 同一Issueの重複承認・重複実行

### 完了条件

- 不正入力がAPI実行前に停止する
- IssueまたはActionsログに原因と次の対応が表示される
- 途中失敗時に、重複処理や既存結果の破壊を避けて再実行できる
- 失敗したバッチ番号、入力、出力、ログの場所を特定できる

## Phase 4: 受入テスト

受領者のGitHub・Bright Data・Secretsを使用し、開発者の認証情報を使わずに実施する。

### Test A: Webapp

- Webappを開く
- 処理方式とパラメータを選択する
- Issue本文のプレビューを確認する
- GitHub Issueを作成する

期待結果: Issueが正しいコマンドとJSONを含んで作成される。

### Test B: Issueルーター

- Issue作成を検知する
- `parse-and-route`が起動する
- `validate-request`が入力と権限を検証する
- 必要な処理ワークフローへ分岐する

期待結果: 不正入力は処理前に停止し、正常入力は対象ワークフローへ進む。

### Test C: 小規模データ処理

- テスト用CSV 10件程度を用意する
- レビュー取得を実行する
- `googlemap/results/`に結果を保存する
- 結果がコミットされることを確認する
- Issueに完了コメントが投稿されることを確認する

### Test D: エラー処理

- 不存在ファイルを指定する
- API認証を一時的に失敗させる
- 不正なJSONを指定する
- 小さなバッチで1チャンクを失敗させる

期待結果: 原因がログとIssueコメントから追跡でき、再実行手順が明確である。

### Test E: 受領者による単独再実行

開発者が操作を代行せず、受領者だけで次を行う。

- Secrets確認
- Issue作成
- Actionsログ確認
- 失敗時の再実行
- 結果CSVの確認
- GitHub上での軽微な設定変更

### 完了条件

- Test AからEが記録付きで成功する
- 失敗したテストは、未解決事項として担当者と期限を持つ
- 受領者が自力で一連の処理を完了できる

## Phase 5: ドキュメントと最終引き渡し

### 引き渡す資料

- システム構成図
- リポジトリ一覧と権限一覧
- Secrets名一覧（値は記載しない）
- Bright DataのDataset ID、ゾーン名、料金の確認方法
- 入力CSVの仕様
- 出力CSVの仕様
- Webapp操作手順
- Issueコマンド一覧
- GitHub Actionsの確認・再実行手順
- エラーコード別の対応表
- バックアップ・復旧手順
- 変更履歴と既知の制限
- 受入テスト結果

### 完了条件

- 手順書だけで受領者が初回セットアップできる
- 秘密情報を除き、運用に必要な情報が欠落していない
- 受領者が質問なしで最小処理を実行できる
- 最終版のリポジトリコミット、設定、テスト結果が記録されている

## 優先順位

### P0: 引き渡し前に必須

- `demo`と`googlemap`の権限確認
- Secretsの再設定
- Bright Dataアカウントと利用料負担の確定
- 本番対象ワークフローの確定
- 未配置スクリプトの解消または対象外化
- 10件程度の小規模受入テスト
- 受領者単独での再実行確認

### P1: 本番運用前に必須

- 最新の一部チャンク失敗の原因確認
- 非対話実行の確認
- APIエラー、タイムアウト、再実行手順の整備
- 結果のバックアップと復旧手順
- ドキュメントと現行コードの同期

### P2: 運用改善

- 自動リトライと部分再開
- 利用量・費用の監視
- Slack等への失敗通知
- 自動テストの追加
- n8nなど旧経路の整理

## 最終受領判定

次の条件をすべて満たした場合に、運用可能な状態での引き渡し完了とする。

- 受領者のアカウントで設定できる
- 受領者のSecretsでAPI接続できる
- WebappからIssueを作成できる
- GitHub Actionsが正常に分岐・実行される
- 結果が`googlemap/results/`に保存される
- 失敗時の原因と復旧手順が確認できる
- 受領者が単独で再実行できる
- 未解決事項、対象外機能、外部料金の負担者が文書化されている
- 受入テスト結果と最終コミットが記録されている

この条件を満たさない項目は、「引き渡し済み」ではなく「未完了」または「既知の制限」として明示する。
