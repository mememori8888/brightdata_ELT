# クライアント向け運用開始・移管ガイド

更新日: 2026-08-25

## 1. 現在の正本

2026年8月25日時点で、最新のコード、WebApp、受入テスト実績が揃っている環境は次の2リポジトリです。

- コード・Actions・WebApp: `mememori8888/demo`（Public）
- 設定・入力・結果CSV: `mememori8888/googlemap`（Private）
- 公開WebApp: `https://mememori8888.github.io/demo/webapp/`

`brightdata_ELT`は2026年8月23日時点のコードで止まっており、現在の`demo`の修正とPages設定は反映されていません。移管先を`brightdata_ELT`にする場合は、所有権移転前に`demo/main`の最新版を同期し、GitHub Pagesを`main`ブランチの`/docs`から公開してください。

今回のレビュー15列修正前は、`demo`と`brightdata_ELT`のどちらの`main.py`も旧9列でした。以前15列へ揃っていたのはBright Data Dataset版だけです。

## 2. システム構成

```text
WebApp
  ↓ Issue作成
コードリポジトリのIssue / GitHub Actions
  ↓ 入力取得・結果保存
googlemap（Private）
  ↓
Google Places API または Bright Data Dataset API
  ↓
googlemap/results/*.csv + Issue完了コメント
```

コードリポジトリだけでは動作しません。Privateデータリポジトリへの読書き権限が必要です。

## 3. 現在使用する処理

| 状態 | WebApp表示 | Issueコマンド | データソース |
|---|---|---|---|
| 使用する | 施設・レビュー取得 (Google Places API) | `/run-facility-places` | Google Places API (New) |
| 使用する | レビュー取得・新仕様逐次実行 | `/run-reviews-sequential` | Bright Data Dataset / Web Scraper API |
| 使用しない | レビュー取得 (Reviews) | `/run-reviews` | Bright Data SERP API |
| 使用しない | 施設データ取得 (Facility) | `/run-facility` | Bright Data SERP API |
| 使用しない | 30日関連度ランク付き | `/run-reviews-relevance` | Dataset + Bright Data SERP API |

Bright DataからSERP APIを利用できないとの連絡がありますが、将来の再開に備えて下3つもWebAppに残しています。現在の受入テストでは選択しません。

Google Places APIはレビューのオーナー返信を返しません。返信が必要な場合は`/run-reviews-sequential`を使用します。

## 4. 所有権移転前の必須修正

現在はリポジトリ名がコード内に固定されています。所有権移転またはリポジトリ名変更後に、次を新しい値へ変更してください。

1. `docs/webapp/app.js`冒頭
   - `GITHUB_OWNER`
   - `GITHUB_REPO`
   - `DATA_REPO`
2. `.github/workflows/*.yml`
   - `repository: mememori8888/googlemap`
3. `.github/workflows/issue-ops-universal.yml`
   - 完了コメント用の`https://github.com/mememori8888/googlemap`
4. 本書と受入手順書の公開URL

確認コマンド:

```powershell
rg -n "mememori8888|demo|googlemap" docs/webapp .github/workflows docs
```

変更後はWebAppのキャッシュ対策として`docs/webapp/index.html`末尾の`app.js?v=...`も更新します。

## 5. 必要なアカウントとSecrets

コードリポジトリの`Settings` → `Secrets and variables` → `Actions`で登録します。

| Secret | 用途 | 必須条件 |
|---|---|---|
| `PRIVATE_REPO_PAT` | Privateデータリポジトリのcheckout・push | 常に必須 |
| `GOOGLE_MAPS_API_KEY` | Google Places API版 | Places版で必須 |
| `BRIGHTDATA_API_TOKEN` | Dataset逐次レビュー | 逐次版で必須 |
| `BRIGHTDATA_ZONE_NAME` | SERP API | 現在は不要 |
| `GEMINI_API_KEY` | AI要約 | 現在無効、不要 |

`PRIVATE_REPO_PAT`はFine-grained tokenを使用し、PrivateデータリポジトリをRepository accessへ含め、`Contents: Read and write`を付与します。`GITHUB_TOKEN`はActionsが自動発行するため登録不要です。

## 6. 実行できる限定ユーザー

許可ユーザーは次のファイルで指定されています。

- `.github/workflows/issue-ops-universal.yml`の環境変数`AUTO_RUN_USERS`
- 現在値: `jmh8128494-cloud,asahi26366`

自動実行できるのはリポジトリオーナーとこの許可リストです。それ以外のユーザーのIssueはプレビューで停止し、オーナーまたは許可ユーザーが`/承認`とコメントすると実行されます。許可リスト変更後は、対象外ユーザーで自動実行されないことも確認してください。

## 7. GitHub Pagesの設定

1. コードリポジトリの`Settings` → `Pages`を開く
2. `Deploy from a branch`を選択する
3. Branchを`main`、Folderを`/docs`にする
4. 公開URL`https://<owner>.github.io/<repo>/webapp/`を開く
5. 5処理が表示され、受入テストではGoogle Places API版とDataset逐次版を選択できることを確認する

Pagesは反映まで数分かかる場合があります。古い表示が残る場合はスーパーリロードを行います。

## 8. 小規模受入テスト

詳細は[`CLIENT_ACCEPTANCE_TEST_GUIDE.md`](CLIENT_ACCEPTANCE_TEST_GUIDE.md)に従います。

1. Google Places API版を`settings/address_test.csv`で実行する
2. Dataset逐次レビューを`results/care_roujin-home_test.csv`、`days_back=30`で実行する
3. どちらもActions成功、Issue完了、PrivateリポジトリへのCSV保存を確認する
4. レビューCSVが次の共通15列であることを確認する

```text
レビューID,施設ID,施設GID,レビュワー評価,レビュワー名,レビュー日時,レビュー本文,オーナー返信,レビュー表示順位,レビュー取得ソート,関連度ランク,関連度取得ソート,関連度取得日時,レビュー要約,レビューGID
```

Places版の`オーナー返信`と関連度3列が空欄なのはAPI仕様上正常です。列が欠落している場合は異常です。

## 9. 取得方法の違い

| 項目 | Google Places API | Bright Data Dataset逐次 |
|---|---|---|
| 主用途 | 施設と基本レビューをまとめて取得 | 既存施設のレビューを取得 |
| オーナー返信 | 取得不可、空欄 | 取得元にあれば保存 |
| 返却レビュー数 | Places APIの仕様に依存 | Datasetと期間指定に依存 |
| レビュー取得ソート | 関連度順 | 新着順（Dataset ID） |
| APIキー | `GOOGLE_MAPS_API_KEY` | `BRIGHTDATA_API_TOKEN` |

## 10. 障害時の確認

| 症状 | 確認 |
|---|---|
| Actionsが起動しない | Issue作成者または承認者が許可対象か |
| Private checkout/push失敗 | `PRIVATE_REPO_PAT`の対象と権限 |
| Google Places 401/403 | `GOOGLE_MAPS_API_KEY`とPlaces API有効化 |
| Bright Data 401/403 | `BRIGHTDATA_API_TOKEN` |
| `zone "..." not found` | SERP対象機能を選んでいないか |
| Datasetで正常な0件 | `days_back`を30へ広げ、対象期間を確認 |
| DatasetでActionsエラー | スナップショットまたはダウンロード失敗ログを確認 |
| Placesで返信が空欄 | 正常。APIが返信を提供しない |
| レビューCSVの列が不足 | コードリポジトリを15列対応後の版へ更新 |

Actions URL、Issue URL、失敗ステップ、エラー文を記録し、秘密情報は共有しないでください。

## 11. 移管完了条件

- 新オーナーの2リポジトリで所有権または必要権限が確認できる
- 新オーナー自身のPAT・APIキーへ置き換わっている
- 固定されたowner/repository名を移管先へ変更済み
- GitHub Pagesが新しいURLで公開されている
- 2つの受入テストが成功し、共通15列を確認済み
- 確認後、旧オーナーのPAT・APIキーを失効している
