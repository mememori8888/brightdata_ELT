# クライアント向け運用開始・移管ガイド

更新日: 2026-08-25

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
| WebAppキャッシュ識別子 | `app.js?v=20260825-concurrency-20` |

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

`PRIVATE_REPO_PAT`は新オーナー自身がFine-grained tokenとして発行します。

- Repository access: `jmh8128494-cloud/googlemap`
- Repository permissions: `Contents: Read and write`
- 有効期限: 運用ルールに合わせて設定し、期限前に更新する
- 値を文書、Issue、Actionsログへ貼らない

`GITHUB_TOKEN`はActionsが自動発行するため登録不要です。

### リポジトリ設定も確認する

- `brightdata_ELT`でIssuesが有効になっている
- `brightdata_ELT`でGitHub Actionsが有効になっている
- 組織・リポジトリポリシーがworkflowの`contents: write`と`issues: write`を禁止していない
- `googlemap/main`のbranch ruleがPATによる結果CSVのpushを拒否しない
- `googlemap`をPublicへ変更していない

## 5. 実行権限

自動実行できるのは次のユーザーです。

- リポジトリオーナー`jmh8128494-cloud`
- `.github/workflows/issue-ops-universal.yml`の`AUTO_RUN_USERS`に登録されたユーザー
- 現在の許可リスト: `jmh8128494-cloud,asahi26366`

移管後は`jmh8128494-cloud`がオーナー判定でも許可されるため、許可リスト内の同名指定は重複しますが動作上の問題はありません。`asahi26366`を今後も自動実行ユーザーにするかは、運用開始前に確認してください。

それ以外のユーザーのIssueはプレビューで停止し、オーナーまたは許可ユーザーによる`/承認`コメントで実行されます。

## 6. GitHub Pages

`brightdata_ELT`をPrivateにする場合は、GitHub Pro、Team、Enterprise等のPrivate Pages対応プランであることを先に確認します。リポジトリがPrivateでも、通常のPagesサイト自体は公開されます。

1. `jmh8128494-cloud/brightdata_ELT`の`Settings` → `Pages`を開く
2. Sourceで`Deploy from a branch`を選ぶ
3. Branchを`main`、Folderを`/docs`にする
4. Pagesのbuildとdeployが成功するまで待つ
5. `https://jmh8128494-cloud.github.io/brightdata_ELT/webapp/`を開く
6. WebAppから作成されるIssue URLが`jmh8128494-cloud/brightdata_ELT`であることを確認する

WebAppに古いJavaScriptが残る場合は、スーパーリロードまたはブラウザキャッシュ削除を行います。

## 7. 現在のワークフロー

| WebAppグループ | WebApp表示 | Issueコマンド | データソース | 初回受入 |
|---|---|---|---|---|
| 現在の運用 | 施設・レビュー取得 (Google Places API) | `/run-facility-places` | Google Places API (New) | 実施する |
| 現在の運用 | レビュー取得・新仕様逐次実行 | `/run-reviews-sequential` | Bright Data Dataset / Web Scraper API | 実施する |
| SERP API再開後 | レビュー取得 (Reviews) | `/run-reviews` | Bright Data SERP API | ゾーン再開後に実施 |
| SERP API再開後 | 施設データ取得 (Facility) | `/run-facility` | Bright Data SERP API | ゾーン再開後に実施 |
| SERP API再開後 | 30日関連度ランク付き | `/run-reviews-relevance` | Dataset + SERP API | ゾーン再開後に実施 |

SERP依存の3処理は将来の再開に備えてWebAppとActionsへ残しています。SERPゾーンの利用可否をBright Data側で確認できるまでは、初回受入テストでは選択しません。

Google Places APIはレビューのオーナー返信を返しません。返信が必要な場合はDataset逐次版を使用します。

Bright Dataの同時処理数は最大20です。Dataset逐次版は既定値を`api_batch_size=20`、`max_parallel_jobs=1`とし、2値の積が20を超える設定を拒否します。

## 8. 受入テスト

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

## 9. n8n・Googleログイン状態（任意）

ローカルn8nは、Googleプロファイルの半手動作成とGoogle Maps関連度順位の抽出に使用します。どちらもCodexの使用が条件です。詳細は[`n8n_google_reviews_ops.md`](n8n_google_reviews_ops.md)を使用します。Googleログイン状態はSecret相当として扱い、リポジトリへ保存しません。

## 10. 障害時の確認

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

Issue URL、Actions URL、失敗ステップ、エラー文を記録し、Secretsの値は共有しません。

## 11. 移管完了条件

- `jmh8128494-cloud`が両リポジトリのオーナーになっている
- `googlemap`はPrivateで、`brightdata_ELT`は合意した公開範囲である
- 両リポジトリの既定ブランチが`main`である
- 新オーナー自身のPAT・APIキーへ置き換わっている
- 現行ファイルから旧owner/repositoryの固定参照がなくなっている
- GitHub Pagesが新URLで公開されている
- 初回受入対象2処理が成功し、共通15列を確認済みである
- 受入成功後、旧オーナーのPAT・APIキーを失効している

## 12. 運用開始前に決めること

- `brightdata_ELT`をPublicのままにするか、対応プランとActions budgetを用意してPrivateにするか
- Privateにする場合の月間Actions budgetと、budget到達時に停止するか課金継続するか
- 同時処理上限20で10件、100件、1バッチを測定し、全件の所要時間を更新する
- n8nを操作する担当者がCodexを利用できるか
- Googleプロファイル用アカウントの管理者、2段階認証、更新担当者
- Googleログイン状態とGitHub Secretsの更新期限・失効手順
- Public ActionsログへPrivateデータやAPI応答全文が出ていないか定期確認する担当者
