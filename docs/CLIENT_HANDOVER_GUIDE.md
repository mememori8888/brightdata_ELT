# クライアント向け運用開始・移管ガイド

更新日: 2026-08-26

この文書は、所有権移転後の新オーナーを`jmh8128494-cloud`として記載しています。

## 1. 移管後の構成

| 用途 | 移管後のリポジトリ・URL | 公開範囲 |
|---|---|---|
| コード・Actions・WebApp | `jmh8128494-cloud/brightdata_ELT` | Public推奨（Privateも選択可） |
| 設定・入力・結果CSV | `jmh8128494-cloud/googlemap` | Private |
| 公開WebApp | `https://jmh8128494-cloud.github.io/brightdata_ELT/webapp/` | Public |

`brightdata_ELT`のコード内にあるowner・repository参照は、この移管先へ変更済みです。同期後から所有権移転完了までの間は、WebAppのIssue作成先とActionsのデータ取得先が移管後URLを向くため、実行しないでください。

### Publicを推奨する理由

Publicの標準GitHub-hosted runnerはActions実行分数が無料です。Privateでも1ジョブの上限は原則6時間で変わりませんが、プラン別の月間分数を消費します。

歯科医院のDataset逐次レビュー全件処理は、過去に約2日半かかりました。単一runnerが60時間連続稼働した場合の単純換算は約3,600 runner分です。実際の請求対象分数は、各jobの実行時間とmatrix並列数をActionsの`Usage`で確認します。また、PrivateリポジトリからGitHub Pagesを公開するには対応プランが必要です。

詳細とPrivate化の判断条件は[`GITHUB_ACTIONS_RUNTIME_AND_VISIBILITY.md`](GITHUB_ACTIONS_RUNTIME_AND_VISIBILITY.md)を確認してください。

## 2. 所有権移転の順番

参照切れを最小限にするため、次の順番で手作業を行います。

1. `googlemap`を`jmh8128494-cloud`へTransfer ownershipする
2. 新オーナーがTransferを承認し、Privateのままであることを確認する
3. `brightdata_ELT`を`jmh8128494-cloud`へTransfer ownershipする
4. 新オーナーがTransferを承認し、事前に決めた公開範囲であることを確認する
5. 両リポジトリの既定ブランチが`main`であることを確認する
6. 新オーナーのSecretsとPagesを設定してから受入テストを行う

旧オーナーの認証情報は、新オーナー側の受入テストが成功するまで失効させません。

### `already has a repository in the ... network`で移管できない場合

`jmh8128494-cloud already has a repository in the 旧オーナー/googlemap network`は、共同編集者（Collaborator）であることが原因ではありません。移管先アカウントが、`googlemap`と同じforkネットワークに属するリポジトリをすでに所有していることを示します。forkは名前を変更しても同じネットワークに残るため、renameだけでは解消しません。

1. `jmh8128494-cloud`でGitHubへログインし、[所有リポジトリ一覧](https://github.com/jmh8128494-cloud?tab=repositories)を開く
2. `Private`を含めて、`forked from 旧オーナー/googlemap`と表示されるリポジトリを探す
3. forkに独自のcommitやbranchがある場合は、必要な変更を移管元の`googlemap`へ取り込むか、ローカルへ退避する
4. 退避結果を確認後、`jmh8128494-cloud`が所有する対象forkの`Settings` → `General` → `Danger Zone`から削除する
5. 数分待ってから、移管元の`googlemap`でTransfer ownershipを再実行する
6. `jmh8128494-cloud`へ届く確認メールから24時間以内に承認する

削除してよいのは`jmh8128494-cloud`側のforkです。移管元の`googlemap`を削除してはいけません。削除前にリポジトリURL、必要なbranch、未反映commitを記録します。Private forkはGitHub画面の`Leave fork network`対象外なので、forkを残す必要がある場合や対象を特定できない場合は、削除せず[GitHub Support](https://support.github.com/)へforkの切り離しを依頼します。詳細は[GitHubのリポジトリ移管条件](https://docs.github.com/en/repositories/creating-and-managing-repositories/transferring-a-repository)と[fork切り離し手順](https://docs.github.com/en/pull-requests/how-tos/work-with-forks/detaching-a-fork)を参照してください。

既存のローカルcloneを継続使用する場合は、Transfer後にremote URLを更新します。

```powershell
git remote set-url origin https://github.com/jmh8128494-cloud/brightdata_ELT.git
git remote -v
```

## 3. コードへ反映済みの移管先設定

次はすでに`jmh8128494-cloud`向けへ変更済みです。

| 対象 | 設定値 |
|---|---|
| `docs/webapp/app.js` | `GITHUB_OWNER = 'jmh8128494-cloud'` |
| `docs/webapp/app.js` | `GITHUB_REPO = 'brightdata_ELT'` |
| `docs/webapp/app.js` | `DATA_REPO = 'googlemap'` |
| `.github/workflows/*.yml` | `repository: jmh8128494-cloud/googlemap` |
| `issue-ops-universal.yml`の完了リンク | `https://github.com/jmh8128494-cloud/googlemap` |
| PythonのGitHub ownerフォールバック | `jmh8128494-cloud` |
| WebAppキャッシュ識別子 | `app.js?v=20260825-user-manual` |

移管前の固定値が現行ファイルに残っていないことを確認するコマンド:

```powershell
$oldOwner = 'mememori' + '8888'
$oldCodeRepo = 'de' + 'mo'
rg -n "$oldOwner|GITHUB_REPO = '$oldCodeRepo'|repository: $oldOwner" `
  docs/webapp .github/workflows README.md `
  docs/CLIENT_ACCEPTANCE_TEST_GUIDE.md `
  docs/CLIENT_HANDOVER_GUIDE.md `
  docs/issueオーケストレーション.md `
  reviews_BrightData_50.py facility_BrightData_20.py
```

この確認は結果0件が正常です。

## 4. 必要なSecrets

`jmh8128494-cloud/brightdata_ELT`の`Settings` → `Secrets and variables` → `Actions`で登録します。

| Secret | 用途 | 必須条件 |
|---|---|---|
| `PRIVATE_REPO_PAT` | `jmh8128494-cloud/googlemap`のcheckout・push | 常に必須 |
| `GOOGLE_MAPS_API_KEY` | Google Places API版 | Places版で必須 |
| `BRIGHTDATA_API_TOKEN` | Dataset逐次レビュー | 逐次版で必須 |
| `BRIGHTDATA_ZONE_NAME` | SERP APIのゾーン | SERP再開時に必須 |
| `GOOGLE_MAPS_STORAGE_STATE_B64` | Playwright関連度取得のGoogleログイン状態 | 手動のstate workflow使用時のみ |
| `GEMINI_API_KEY` | AI要約 | 現在無効、不要 |

移管前に同名Secretがダミー値で用意されている場合も、そのままでは実行できません。移管完了後、新オーナーが各Secretを開いて`Update secret`から実値へ置き換えます。GitHubでは保存済みのSecret値を再表示できません。

### `PRIVATE_REPO_PAT`の発行手順

`PRIVATE_REPO_PAT`は、`googlemap`の移管が完了してから新オーナー自身がFine-grained personal access tokenとして発行します。移管前の`jmh8128494-cloud`はCollaboratorなので、移管前に作成したFine-grained tokenではこの用途を満たせません。

1. `jmh8128494-cloud`でGitHubへログインする
2. 右上のプロフィール画像 → `Settings` → `Developer settings`を開く
3. `Personal access tokens` → `Fine-grained tokens` → `Generate new token`を開く
4. `Token name`へ`brightdata-elt-googlemap`など用途が分かる名前を入力する
5. `Expiration`へ運用上の有効期限を設定する。期限なしにはせず、更新予定日を管理する
6. `Resource owner`で`jmh8128494-cloud`を選ぶ
7. `Repository access`で`Only select repositories`を選び、`googlemap`だけを指定する
8. `Repository permissions`の`Contents`を`Read and write`へ変更する
9. ほかの権限は追加せず、`Generate token`を押す
10. 表示されたtokenを一度だけコピーする。ページを離れると再表示できない

GitHub公式の[Fine-grained token作成画面](https://github.com/settings/personal-access-tokens/new)と[Personal access token管理手順](https://docs.github.com/en/authentication/keeping-your-account-and-data-secure/managing-your-personal-access-tokens)も参照してください。

### `PRIVATE_REPO_PAT`をActions Secretへ登録する手順

1. `jmh8128494-cloud/brightdata_ELT`の`Settings` → `Secrets and variables` → `Actions`を開く
2. `PRIVATE_REPO_PAT`がダミー値で存在する場合は、その名前を開いて`Update secret`を選ぶ。存在しない場合は`New repository secret`を選ぶ
3. `Name`を`PRIVATE_REPO_PAT`、`Secret`を直前にコピーしたtokenとして保存する
4. token値をIssue、文書、チャット、画面キャプチャ、Actionsログへ貼らない
5. 有効期限前に新しいtokenを発行し、同じSecretを更新してから古いtokenを失効する

このtokenの役割は、Public側の`brightdata_ELT` ActionsからPrivate側の`googlemap`をcheckoutし、結果CSVをpushすることだけです。権限は`googlemap`一つと`Contents: Read and write`に限定します。

`GITHUB_TOKEN`はActionsが自動発行するため登録不要です。

### Actions・Issues権限との違い

ActionsとIssuesの機能は必要ですが、`PRIVATE_REPO_PAT`へ`Actions`や`Issues`の権限を追加する必要はありません。認証の役割を次のように分けています。

| 認証 | 対象リポジトリ | 必要な権限 | 用途 |
|---|---|---|---|
| `PRIVATE_REPO_PAT` | `jmh8128494-cloud/googlemap` | `Contents: Read and write` | Private入力のcheckout、結果CSVのpush |
| Actionsが自動発行する`GITHUB_TOKEN` | `jmh8128494-cloud/brightdata_ELT` | workflow記載の`issues: write`、`actions: read`、`contents: write` | Issueへのコメント・クローズ、Actions情報の参照、コードリポジトリ内の処理 |

`GITHUB_TOKEN`の権限は`.github/workflows/issue-ops-universal.yml`冒頭の`permissions`で宣言済みです。利用者がtokenを発行してSecretへ登録する必要はありません。`PRIVATE_REPO_PAT`へ余分な`Actions`・`Issues`権限を付けてもIssue処理には使われず、漏えい時の影響範囲だけが広がります。

### リポジトリ設定も確認する

- `brightdata_ELT`の`Settings` → `General` → `Features`でIssuesが有効になっている
- `brightdata_ELT`の`Settings` → `Actions` → `General`でGitHub Actionsが有効になっている
- 組織・リポジトリポリシーがworkflowの`contents: write`と`issues: write`を禁止していない
- `googlemap/main`のbranch ruleがPATによる結果CSVのpushを拒否しない
- `googlemap`をPublicへ変更していない

## 5. 移管前後のリポジトリ設定チェックリスト

2026-08-26の監査時点では、両リポジトリともPrivateで、Issues・Actions・公開GitHub Pages・Private fork許可が有効です。`googlemap`には移管を妨げる同一ネットワークのforkが1件あります。

| 設定 | `brightdata_ELT`の現在値 | `googlemap`の現在値 | 移管後の方針 |
|---|---|---|---|
| 公開範囲 | Private | Private | `brightdata_ELT`はPublicかPrivateかを決定、`googlemap`はPrivateを維持 |
| 既定ブランチ | `main` | `main` | 両方とも`main`を維持 |
| Issues | 有効 | 有効 | `brightdata_ELT`は有効、データ保管専用の`googlemap`は無効化を推奨 |
| Actions | 有効、すべてのActionを許可 | 有効、workflowなし | `brightdata_ELT`は有効、`googlemap`は無効化を推奨 |
| GitHub Pages | `main`の`/docs`を公開 | `main`の`/docs`を公開 | `brightdata_ELT`は移管後に再設定、`googlemap`は無効化 |
| Private fork | 許可 | 許可、同一ネットワークにforkが1件 | `googlemap`は既存fork解消後に`Allow forking`を無効化 |
| ruleset・branch protection | なし | なし | 直接pushを維持する場合は現状のまま。追加する場合はActions・PATのpushを許可 |
| Secrets | 移管用の名前をダミー登録済み | 旧API Secretが残存 | `brightdata_ELT`を実値へ更新後、`googlemap`の不要Secretを削除・失効 |
| branch | `main` | `main`、`master`、`copilot/*` | `googlemap`は必要な変更を確認し、不要branchを退避後に削除 |
| collaborator | 旧オーナーのみ | 新オーナー候補と運用ユーザーを含む | 受入完了後に旧オーナー・運用ユーザーの継続権限を決定 |
| Webhook・Deploy key | なし | なし | 追加対応なし |

### 移管前

1. `jmh8128494-cloud`側の`googlemap` forkに独自変更がないか確認し、必要なcommit・branchを退避する
2. forkを削除またはGitHub Supportで切り離し、`googlemap`のTransferを可能にする
3. `brightdata_ELT`をPublicで運用するかPrivateで運用するか決定する
4. Privateを選ぶ場合は、`jmh8128494-cloud`のプランでPrivate Pagesが利用できるか、Actionsの月間分数と予算を確認する
5. `asahi26366`を移管後も自動実行ユーザー・`googlemap`共同編集者として残すか決定する

### 移管直後

1. `googlemap`がPrivate、両リポジトリの既定ブランチが`main`であることを確認する
2. 新オーナー自身が`PRIVATE_REPO_PAT`を発行し、`brightdata_ELT`のダミーSecretを実値へ更新する
3. `GOOGLE_MAPS_API_KEY`と`BRIGHTDATA_API_TOKEN`を新オーナー管理の実値へ更新する
4. `brightdata_ELT`のIssuesとActionsを有効にし、`main`の`/docs`からPagesを再設定する
5. Pagesの新URLを開き、WebAppが`jmh8128494-cloud/brightdata_ELT`へIssueを作成することを確認する
6. `WebApp用ファイル一覧・住所CSV検証` workflowを1回実行し、移管後の`googlemap`からファイル一覧を再生成する
7. WebAppの設定・住所・入力・出力プルダウンへ移管後のファイルが表示されることを確認する

### 受入成功後の整理

1. `googlemap`のGitHub Pages、Issues、Actions、`Allow forking`を無効化する
2. `brightdata_ELT`で実値Secretが動作することを確認後、`googlemap`に残る不要な`BRIGHTDATA_API_TOKEN`と`GEMINI_API_KEY`を削除し、旧tokenを失効する
3. `googlemap`の`master`・`copilot/*` branchに必要な変更がないことを確認し、不要なら削除する
4. 移管により共同編集者となった旧オーナーの権限を残すか削除するか決定する
5. `asahi26366`を残さない場合は、`googlemap`の共同編集権限と`AUTO_RUN_USERS`の両方から削除する
6. `brightdata_ELT`のActions許可範囲をGitHub提供Actionとリポジトリ内の再利用workflowへ限定するか検討する

branch protectionを追加すると、`googlemap`への結果CSV pushと`brightdata_ELT`への`files.json`更新が失敗する可能性があります。`Require a pull request`などを有効にする場合は、GitHub Actionsと`PRIVATE_REPO_PAT`の実行主体へ明示的なbypassを設定してから受入テストを行います。

## 6. 実行権限

自動実行できるのは次のユーザーです。

- リポジトリオーナー`jmh8128494-cloud`
- `.github/workflows/issue-ops-universal.yml`の`AUTO_RUN_USERS`に登録されたユーザー
- 現在の許可リスト: `jmh8128494-cloud,asahi26366`

移管後は`jmh8128494-cloud`がオーナー判定でも許可されるため、許可リスト内の同名指定は重複しますが動作上の問題はありません。`asahi26366`を今後も自動実行ユーザーにするかは、運用開始前に確認してください。

それ以外のユーザーのIssueはプレビューで停止し、オーナーまたは許可ユーザーによる`/承認`コメントで実行されます。

## 7. GitHub Pages

`brightdata_ELT`をPrivateにする場合は、GitHub Pro、Team、Enterprise等のPrivate Pages対応プランであることを先に確認します。リポジトリがPrivateでも、通常のPagesサイト自体は公開されます。

1. `jmh8128494-cloud/brightdata_ELT`の`Settings` → `Pages`を開く
2. Sourceで`Deploy from a branch`を選ぶ
3. Branchを`main`、Folderを`/docs`にする
4. Pagesのbuildとdeployが成功するまで待つ
5. `https://jmh8128494-cloud.github.io/brightdata_ELT/webapp/`を開く
6. WebAppから作成されるIssue URLが`jmh8128494-cloud/brightdata_ELT`であることを確認する

WebAppに古いJavaScriptが残る場合は、スーパーリロードまたはブラウザキャッシュ削除を行います。

## 8. 現在のワークフロー

### WebAppの役割

WebAppはAPIをブラウザ内で直接実行したり、CSVの中身を編集したりする画面ではありません。設定プリセットから検索条件と入出力ファイルを選び、その内容をGitHub Issueへ渡してActionsを実行する画面です。

- 設定プリセット: 業種ごとの検索キーワード、住所CSV、除外GID、入出力先の既定値をまとめて設定
- 住所CSV: 検索する地域を指定。内容を変えると検索地域、リクエスト数、時間、API費用が変わる
- 検索キーワード: 検索する施設の種類と除外語を指定
- 入出力ファイル: 読み込む施設データと、結果を保存するCSVを指定
- Issue作成: 選択内容を検証可能な実行依頼へ変換

施設検索では、住所CSVの各行と検索キーワードを結合します。例えば`北海道,札幌市`と`歯科医院`を選ぶと、`北海道 札幌市 歯科医院`として検索します。検索キーワードは`settings/*.json`の`query`へ主業種を1つ記入し、住所は含めません。キーワードの良い例・避ける例、住所CSVの作成方法、検索範囲と費用の関係、不正テンプレートのエラー例は[`ADDRESS_CSV_GUIDE.md`](ADDRESS_CSV_GUIDE.md)を参照してください。

既存出力を選ぶと、施設GID・レビューGIDで照合して重複を除き、新規分を既存IDの続きで追加します。新規出力ではレビューIDを1、施設IDを101から採番します。日常操作、主出力と増分出力の違い、同時実行の禁止事項は[`USER_OPERATION_MANUAL.md`](USER_OPERATION_MANUAL.md)を正本とします。

| WebAppグループ | WebApp表示 | Issueコマンド | データソース | 初回受入 |
|---|---|---|---|---|
| 現在の運用 | 施設・レビュー取得 (Google Places API) | `/run-facility-places` | Google Places API (New) | 実施する |
| 現在の運用 | レビュー取得・新仕様逐次実行 | `/run-reviews-sequential` | Bright Data Dataset / Web Scraper API | 実施する |
| SERP API再開後 | レビュー取得 (Reviews) | `/run-reviews` | Bright Data SERP API | ゾーン再開後に実施 |
| SERP API再開後 | 施設データ取得 (Facility) | `/run-facility` | Bright Data SERP API | ゾーン再開後に実施 |
| SERP API再開後 | 30日関連度ランク付き | `/run-reviews-relevance` | Dataset + SERP API | ゾーン再開後に実施 |

SERP依存の3処理は将来の再開に備えてWebAppとActionsへ残しています。SERPゾーンの利用可否をBright Data側で確認できるまでは、初回受入テストでは選択しません。

Google Places APIはレビューのオーナー返信を返しません。返信が必要な場合はDataset逐次版を使用します。

Bright Dataの同時処理数は最大20です。Dataset逐次版のWebAppは「Bright Data同時処理数」を20件、GitHub Actionsの並列ジョブ数を1に固定しています。Issue・workflow・Pythonでは`api_batch_size × max_parallel_jobs`が20を超える設定を拒否します。SERP APIの並列数（レビュー10、施設10、関連度3）は別設定で、既存の安全な既定値を維持します。

## 9. 受入テスト

詳細は[`CLIENT_ACCEPTANCE_TEST_GUIDE.md`](CLIENT_ACCEPTANCE_TEST_GUIDE.md)に従います。

初回は次の2処理を1件ずつ実行します。

1. Google Places API版を`settings/address_test.csv`で実行する
2. Dataset逐次レビューを`results/care_roujin-home_test.csv`、`days_back=30`で実行する
3. Actions成功、Issue完了、`jmh8128494-cloud/googlemap`へのCSV保存を確認する
4. レビューCSVが次の共通15列であることを確認する

```text
レビューID,施設ID,施設GID,レビュワー評価,レビュワー名,レビュー日時,レビュー本文,オーナー返信,レビュー表示順位,レビュー取得ソート,関連度ランク,関連度取得ソート,関連度取得日時,レビュー要約,レビューGID
```

Places版の`オーナー返信`、関連度3列、`レビュー要約`が空欄なのは正常です。列が欠落している場合は異常です。

## 10. n8n・Googleログイン状態（任意）

ローカルn8nは、Googleプロファイルの半手動作成とGoogle Maps関連度順位の抽出に使用します。どちらもCodexの使用が条件です。詳細は[`n8n_google_reviews_ops.md`](n8n_google_reviews_ops.md)を使用します。Googleログイン状態はSecret相当として扱い、リポジトリへ保存しません。

## 11. 障害時の確認

| 症状 | 確認 |
|---|---|
| WebAppが旧リポジトリを開く | Pagesのdeploy、`app.js`の定数、ブラウザキャッシュ |
| Actionsが起動しない | Issue作成者または承認者が許可対象か |
| Private checkout/push失敗 | PATの対象が`jmh8128494-cloud/googlemap`か、ContentsがRead and writeか |
| Google Places 401/403 | `GOOGLE_MAPS_API_KEY`とPlaces API有効化 |
| Bright Data 401/403 | `BRIGHTDATA_API_TOKEN` |
| `zone "..." not found` | `BRIGHTDATA_ZONE_NAME`とSERPゾーンの契約・有効状態 |
| Datasetで正常な0件 | `days_back`を30へ広げ、対象期間を確認 |
| DatasetでActionsエラー | スナップショットまたはダウンロード失敗ログ |
| レビューCSVの列が不足 | 15列統一後の`main`か確認 |
| 住所CSVがWebAppに表示されない | `ADDRESS_CSV_GUIDE.md`のテンプレート条件を確認し、「WebApp用ファイル一覧・住所CSV検証」を実行 |
| `住所CSVのヘッダーが不正です` | 1行目を`都道府県,市区町村,町域`形式に修正 |
| `都道府県が不正です` | 1列目を`北海道`・`東京都`など正式名称に修正 |
| `住所CSVはUTF-8で保存してください` | Excel等でCSV UTF-8として保存し直す |
| 新規レビューCSVのIDが1から始まらない | 同名ファイルがすでに存在し、既存ファイルとして更新されていないか確認 |
| 既存CSVでGID重複が増えた | GIDの空欄・変更、同一出力への同時実行、古いコード版を確認 |

Issue URL、Actions URL、失敗ステップ、エラー文を記録し、Secretsの値は共有しません。

## 12. 移管完了条件

- `jmh8128494-cloud`が両リポジトリのオーナーになっている
- `googlemap`はPrivateで、`brightdata_ELT`は合意した公開範囲である
- 両リポジトリの既定ブランチが`main`である
- 新オーナー自身のPAT・APIキーへ置き換わっている
- 現行ファイルから旧owner/repositoryの固定参照がなくなっている
- GitHub Pagesが新URLで公開されている
- 初回受入対象2処理が成功し、共通15列を確認済みである
- 受入成功後、旧オーナーのPAT・APIキーを失効している

## 13. 運用開始前に決めること

- `brightdata_ELT`をPublicのままにするか、対応プランとActions budgetを用意してPrivateにするか
- Privateにする場合の月間Actions budgetと、budget到達時に停止するか課金継続するか
- 同時処理上限20で10件、100件、1バッチを測定し、全件の所要時間を更新する
- n8nを操作する担当者がCodexを利用できるか
- Googleプロファイル用アカウントの管理者、2段階認証、更新担当者
- Googleログイン状態とGitHub Secretsの更新期限・失効手順
- Public ActionsログへPrivateデータやAPI応答全文が出ていないか定期確認する担当者
