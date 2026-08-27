# プログラム・workflow仕様書（正本）

更新日: 2026-08-27

この文書は、PythonプログラムとGitHub Actions workflowの入力、出力、照合、分割、タイムアウト、失敗時の成果物、再開方法を定義する技術仕様の正本です。日常操作は[`USER_OPERATION_MANUAL.md`](USER_OPERATION_MANUAL.md)、初回テストは[`CLIENT_ACCEPTANCE_TEST_GUIDE.md`](CLIENT_ACCEPTANCE_TEST_GUIDE.md)を参照してください。

## 1. システム全体

```text
WebApp → GitHub Issue → issue-ops-universal.yml → 対象workflow
                                              ├─ 公開コードリポジトリ
                                              ├─ 外部API
                                              └─ Privateデータリポジトリ googlemap
```

- コード、WebApp、workflowは`jmh8128494-cloud/brightdata_ELT`に置く。
- 設定、住所CSV、既存CSV、出力CSVはPrivateの`jmh8128494-cloud/googlemap`に置く。
- 認証情報はGitHub Actions Secretsから環境変数で渡し、コード、Issue、状態JSON、Artifactへ書かない。
- 施設の照合キーは`施設GID`、レビューの照合キーは`レビューGID`とする。
- レビューCSVは[`review_schema.py`](../review_schema.py)の共通15列を使用する。
- 同じ出力CSVを更新するActionsは同時に実行しない。

## 2. 共通のID・出力仕様

| 条件 | 施設ID | レビューID | 動作 |
|---|---:|---:|---|
| 新しい出力CSV | 101から | 1から | 独立したデータとして採番 |
| 既存出力CSV | CSV全行の最大ID+1 | CSV全行の最大ID+1 | 行順や末尾IDに依存しない |
| 既存GID | 既存IDを維持 | 既存IDを維持 | 重複追加しない |
| 新規データのGIDが空 | 採番しない | 採番しない | 警告を残してスキップ |
| 既存CSVのGIDが空 | 既存行を保持 | 既存行を保持 | 自動削除しない |

主出力は既存行と新規行を含み、増分出力はその実行条件で新規追加された行だけを含みます。既存施設の値は上書きせず、新規施設・新規レビューだけを追加します。

## 3. Pythonプログラム

| ファイル | 用途・入力 | 出力・外部接続 | 分割・照合・復旧 |
|---|---|---|---|
| `main.py` | Google Places API (New)で、住所CSV各行と`query`を結合して施設・Placesレビューを検索 | 施設主／増分CSV、レビュー主／増分CSV、`results/places_run_status.json`、進捗JSON。Google Places APIへ接続 | 既存CSVは10,000行単位でSQLiteへ読み込み、GID索引で照合。住所単位でcommit。240分で部分完了し、同じ条件なら自動再開 |
| `places_csv_store.py` | `main.py`のディスク上照合・採番・CSVトランザクション | `results/progress/places_*.sqlite3`と原子的に置換するCSV | 全件DataFrame結合を行わない。SQLiteのGID一意索引と`MAX(ID)`を使用。CSV書出しも10,000行単位 |
| `address_csv_validator.py` | UTF-8住所CSVのヘッダー、都道府県、空行、数式、終了行を検証 | 検証済み検索文字列の配列。外部接続なし | 不正テンプレートはAPI実行前に停止 |
| `review_schema.py` | レビュー共通15列と取得ソート表示名を定義 | 他プログラムが参照する定数 | 列順の唯一の定義元 |
| `get_reviews_from_dental_new.py` | 施設CSVのGoogle Maps URLをBright Data Datasetへ渡し、期間内レビューを取得 | レビュー主／増分／期間内CSV、`RUN_STATUS_FILE`。Bright Data Dataset APIへ接続 | APIチャンク20件固定。各チャンク後にCSVと状態を保存。ready後の空配列は成功。trigger、snapshot、download失敗は別のエラー種別 |
| `run_reviews_local_interactive.py` | Dataset取得の対話／非対話ラッパー。入力、出力、行範囲、日数等を環境変数へ変換 | `get_reviews_from_dental_new.py`を起動、ログを`results/logs/`へ保存 | APIバッチ20固定、バッチモードは最大500行。ローカルでも同じ制約を拒否 |
| `facility_BrightData_20.py` | Bright Data SERP経由で住所ごとの施設を取得 | 施設主／増分、FID、重複分析、`serp_facility_run_status.json`。Bright Data `/request`へ接続 | 住所ごとにCSVと進捗を保存。最大worker 20、既定10。最大worker件のグループ処理。240分で部分完了し同じ条件なら再開 |
| `faiility_brightdata_new_version.py` | SERP施設取得のデータルート検出ラッパー | `PRIVATE_DATA_ROOT`配下で`facility_BrightData_20.py`を起動 | データルート不明時は公開コード側へ書かず停止 |
| `reviews_BrightData_50.py` | SERP APIでレビューを取得する待機機能 | 共通15列レビューCSV。Bright Data SERPへ接続 | SERP再開待ち。workerは1～20で検証し、再開時は小規模テスト必須 |
| `reviews_brightData_new_version.py` | SERPレビュー取得のラッパー | Privateデータルートで`reviews_BrightData_50.py`を起動 | データルート・設定・入力を検証してから実行 |
| `scripts/merge_review_batches.py` | 成功したDatasetバッチCSVを既存出力と統合 | 主出力、増分出力、任意の全地域出力、行数をworkflow outputへ出力 | `レビューGID`で重複排除。既存IDを維持し、新規IDを最大値の続きから採番。空施設行の除外設定あり |
| `scripts/enrich_review_relevance_ranks.py` | SERPを使って既存レビューへ関連度順位を付加 | 更新レビューCSV、サマリー、詳細、未照合CSV | SERP再開待ち。施設単位で処理し、失敗を診断用CSVへ分離 |
| `scripts/enrich_review_relevance_ranks_state.py` | PlaywrightとGoogleログイン状態で関連度順位を付加 | 上記と同種のCSV、デバッグ資料 | Codex併用の半手動運用。storage stateはSecretとして扱う |
| `scripts/diagnose_places_api_review_fields.py` | Placesレビューの返却フィールド確認 | 診断ログ。Google Places APIへ接続 | 本番更新をしない診断用。実行にはAPI費用が発生し得る |
| `scripts/diagnose_serp_reviews_api.py` | SERPレビューの応答形式確認 | 診断ログ。Bright Dataへ接続 | SERP再開時のsmoke test専用 |
| `update_file_list.py` | Private側の設定・CSVからWebApp選択肢を生成 | `docs/webapp/files.json`と必要なworkflow選択肢 | 住所CSVはvalidatorを通過したものだけを候補にする |

## 4. Google PlacesのSQLite照合

`main.py`は既存施設・レビューCSVをpandasへ全件結合しません。`places_csv_store.py`が次の順序で処理します。

1. 既存施設CSVとレビューCSVを10,000行ずつSQLiteへ取り込む。
2. `施設GID`と`レビューGID`へ一意索引を作る。GID空欄の既存行は別キーで保持する。
3. CSV全行で確認した最大IDの続きから採番する。
4. 新規施設をレビュー有無に関係なく直ちに索引へ登録する。
5. 同じ実行中に別住所で同じGIDを再発見した場合は、同じ施設IDを使用して重複追加しない。
6. 住所1件が成功した時点でSQLiteをcommitし、進捗JSONを原子的に更新する。
7. チェックポイントまたは完了時、主出力と増分出力を10,000行ずつ一時CSVへ書き、`os.replace`で置換する。

出力中に例外が起きた場合、一時CSVを削除して既存CSVを残します。進捗キーは住所CSVの内容、検索キーワード、`includedType`、4つの出力先から生成します。どれかが変わると別実行として最初から検索します。全住所完了後に同じ条件で再度実行する場合も、新しい更新処理として最初から検索します。

## 5. Dataset逐次レビューの固定制約

| 設定 | 既定・許容値 | 理由 |
|---|---|---|
| `rows_per_batch` | 既定500、1～500 | 1つのActionsバッチを5時間以内へ収める |
| `api_batch_size` | 20固定 | Bright Dataへ一度に渡す施設数 |
| `max_parallel_jobs` | 1固定 | 全ジョブ合計の同時処理数を20以下にする |
| `max_wait_minutes` | 既定90 | Dataset snapshotの待機上限 |
| matrix job数 | 最大256 | GitHub Actionsのmatrix上限 |

WebApp、Issue検証、workflow planner、CLI、Pythonの各層で制約を検証します。`api_batch_size × max_parallel_jobs > 20`も拒否します。過去の`20件×3ジョブ=60件`設定には戻しません。

1つのmatrix jobは最大500施設を20件ずつ、最大25 APIチャンクとして順に処理します。チャンク成功ごとに途中CSVと状態JSONを更新します。270分のステップ上限に達した場合も、その前に保存されたチャンクはArtifactへ残ります。自動再試行はせず、失敗バッチ範囲だけを利用者が再実行します。

状態の判定:

- `success`: 全対象チャンクが成功。ready後の正常な空配列も「期間内レビュー0件」として成功。
- `partial`: 1件以上のチャンクまたはバッチが成功し、別のチャンクまたはバッチが失敗。
- `failed`: 成功バッチがない、入力・認証・trigger等で処理できない。

`error_type`には`SnapshotTriggerError`、`SnapshotProcessingError`、`SnapshotDownloadError`、ステップtimeout等の分類だけを保存し、API応答本文やtokenは保存しません。

## 6. GitHub Actions workflow

| workflow | 用途 | job上限 | 長時間step | 失敗時・再開 |
|---|---|---:|---:|---|
| `issue-ops-universal.yml` | Issue解析、権限判定、入力検証、対象処理への分岐、結果通知 | 解析30分、検証60分、SERP施設300分、通知30分 | SERP施設270分 | 部分完了をIssueへ通知。逐次レビューは失敗バッチ範囲を表示 |
| `main_places_api.yml` | Google Places施設・レビュー取得 | 300分 | 270分 | results全体と進捗をArtifact／Privateへ保存。partialは同条件で自動再開 |
| `reviews_local_interactive_sequential.yml` | Dataset逐次レビューのmatrix実行とマージ | prepare 30分、各batch 300分、merge 60分 | API batch 270分 | status、途中CSV、ログを常時Artifact化。成功バッチを必ずマージ |
| `reviews_recent_with_relevance.yml` | Dataset取得後にSERP関連度を付加 | prepare 30分、各batch 300分、merge 180分 | Dataset batch 270分 | Dataset成功分をArtifact化。SERP再開待ち |
| `brightdata_facility.yml` | SERP施設取得 | 300分 | 270分 | 住所進捗と途中CSVを保存し、partialは同条件で再開。SERP再開待ち |
| `brightdata_reviews.yml` | SERPレビュー取得 | 300分 | 270分 | 常時Artifactを保存。SERP再開待ち |
| `relevance_ranks_playwright_state.yml` | storage stateを使った関連度抽出 | 300分 | 270分 | 出力・デバッグ資料を保存。Codex併用 |
| `generate-file-list.yml` | WebAppファイル一覧と住所CSV検証 | 30分 | なし | 不正住所CSVは候補へ出さず、検証エラーを表示 |
| `recover-run-artifacts.yml` | 過去runのArtifactをPrivateへ復旧 | 30分 | なし | 対象run・Artifactを指定して手動復旧 |
| `serp_reviews_smoke.yml` | SERPレビュー1件診断 | 15分 | なし | SERP再開時だけ実行 |

stepを持つ全jobは明示的に300分以下です。API取得・Playwrightの長時間stepは270分以下で、保存・通知のためにjob上限まで30分の余裕を持たせます。再利用workflowを呼ぶjobには`timeout-minutes`を指定できないため、呼び出し先の実行jobで上限を持ちます。

## 7. 成果物と再開

### Google Places／SERP施設

- 状態JSONの`status`、`completed_address_rows`、`next_address_index`、`error_type`を確認する。
- `partial`なら住所CSV、検索キーワード、出力先を変えずに再実行する。
- 条件を変えると新しい進捗キーになるため、最初から実行される。
- 進捗JSONやSQLiteだけを手作業で編集しない。

### Dataset逐次レビュー

- `results/status/status_batch_<番号>.json`で開始行、終了行、完了APIチャンク数、総チャンク数、エラー種別を確認する。
- mergeは成功Artifactを統合し、`results/status/reviews_sequential_<run_id>.json`へ全体状態を保存する。
- Issueの部分完了コメントに表示された失敗バッチ番号を`start_from_batch`へ指定する。
- 複数の離れたバッチが失敗した場合は、`max_batches`を使い、連続範囲ごとに別実行する。
- 自動再試行は行わない。同じ本番出力を使う別runが動いていないことを確認する。

## 8. 現在運用と待機機能

| 区分 | 機能 |
|---|---|
| 現在運用 | Google Places API施設・レビュー、Bright Data Dataset逐次レビュー |
| SERP再開待ち | SERP施設、SERPレビュー、Dataset＋SERP関連度 |
| Codex併用 | Playwright／n8nでGoogleログイン状態を半手動作成し関連度を抽出 |

SERP機能は削除せずWebAppにも残します。再開時は[`SERP_API_REACTIVATION_GUIDE.md`](SERP_API_REACTIVATION_GUIDE.md)に従い、1件、新規テスト出力、10件、100件の順で確認します。

## 9. 変更時の確認

```powershell
$env:PYTHONIOENCODING='utf-8'
python -m unittest discover -s tests -v
```

実APIを使うActionsは自動テストに含めません。API費用とPrivateデータ更新を伴うため、受入手順に従って小規模に1処理ずつ実行します。
