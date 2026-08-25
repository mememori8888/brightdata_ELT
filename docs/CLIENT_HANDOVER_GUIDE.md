# brightdata_ELT 運用開始ガイド（新オーナー向け）

このドキュメントは、`brightdata_ELT`（コード・Actions・Webapp）と`googlemap`（データ）を引き継いだ方が、ご自身のアカウントでシステムを動かせるようにするための手順書です。

## このシステムの全体像

```text
Webapp（Issue作成画面）
      ↓
GitHub Issue（brightdata_ELT）
      ↓
GitHub Actions（brightdata_ELT）
      ↓ 設定・入力データを取得／結果を保存
googlemap（Private・データ専用）
      ↓
Bright Data API（施設・レビュー取得）
      ↓
結果CSV（googlemap/results/）
      ↓
Issueへ完了コメント
```

- `brightdata_ELT`: コード・GitHub Actions・Webapp（Public）
- `googlemap`: 設定ファイル・入力CSV・結果データ（Private）

この2つのリポジトリは両方とも必要です。`brightdata_ELT`だけでは動作しません。

---

## Step 1: リポジトリの所有権を確認する

1. GitHubから届く「Repository transfer」の通知メールを確認し、承認する
2. 以下の2つが、ご自身のGitHubアカウントの所有物になっていることを確認する
   - `https://github.com/<あなたのアカウント>/brightdata_ELT`
   - `https://github.com/<あなたのアカウント>/googlemap`

以降の手順は、すべて**ご自身のアカウントで**行ってください。

---

## Step 2: 必要なアカウント・契約を用意する

- Bright Dataのアカウント（[公式サイト](https://get.brightdata.com/mam10)）
  - 施設取得・レビュー取得に使う「SERP API」「Web Scraper API」を利用できる契約が必要です
  - 利用料金はBright Data側との契約に基づき発生します。開発費とは別に、ご自身の名義・支払い方法で契約してください

---

## Step 3: `brightdata_ELT`にGitHub Secretsを登録する

`brightdata_ELT`の以下のページを開いてください。

```text
https://github.com/<あなたのアカウント>/brightdata_ELT/settings/secrets/actions
```

「New repository secret」から、以下を登録してください。

| Secret名 | 値の取得方法 | 必須 |
|---|---|---|
| `PRIVATE_REPO_PAT` | ご自身のGitHubアカウントで発行するPersonal Access Token。Repository accessに`googlemap`を含め、`Contents: Read and write`権限を付与する | 必須 |
| `BRIGHTDATA_API_TOKEN` | Bright Dataのダッシュボードで発行するAPIトークン | 必須 |
| `BRIGHTDATA_ZONE_NAME` | Bright Data側で有効化したSERP APIのゾーン名（例: `serp_api2`） | 必須 |
| `GOOGLE_MAPS_API_KEY` | Google CloudでPlaces APIを有効化したAPIキー。Google Places API版を実行する場合のみ使用 | Google Places API版で必須 |
| `GEMINI_API_KEY` | Gemini APIを使う場合のみ発行（現状コード側で無効化されているため未設定でも動作します） | 任意 |

`GITHUB_TOKEN`は登録不要です（GitHub Actionsが自動的に発行します）。

### `PRIVATE_REPO_PAT`発行時の注意

1. https://github.com/settings/personal-access-tokens を開く
2. Repository access に `brightdata_ELT` と `googlemap` の両方を選択
3. Permissions で `Contents: Read and write` を選択
4. `.github/workflows/`を更新する予定がある場合は `Workflows: Read and write` も選択

Playwrightを使った関連度取得機能は現在使用しないため、`GOOGLE_MAPS_STORAGE_STATE_B64`・`GOOGLE_MAPS_STORAGE_STATE_JSON`の登録は不要です。

---

## Step 4: 実行権限を持つユーザーを確認する

このシステムは、誰でもIssueを作れますが、実行できるのは限定されたユーザーだけです。

- リポジトリオーナー
- 許可リストに登録された特定ユーザー（現在: `jmh8128494-cloud`、`asahi26366`）

上記以外のユーザーがIssueを作成した場合は、見積もりが表示されるだけで、実行はされません。実行するには、オーナーまたは許可ユーザーが`/承認`とコメントする必要があります。

許可リストを変更したい場合は、`.github/workflows/issue-ops-universal.yml`内の`AUTO_RUN_USERS`を編集してください。

---

## Step 5: 小規模テストを実行する

1. `docs/webapp/index.html`をブラウザで開く
2. 少人数分（10件程度）のテスト用CSVで、レビュー取得または施設取得を選択する
   - Google Places API版では、まず「設定プリセット」から通常用またはテスト用を選択する
   - プリセットから検索キーワード、カテゴリ、住所CSV、除外GID、各出力CSVが自動設定されるため、必要な項目だけ変更する
   - 最初の小規模テストでは「テスト」と表示されるプリセットと `settings/address_test.csv` を使用する
3. 「GitHubでIssueを作成」からIssueを作成する
4. `brightdata_ELT`の「Actions」タブで、ワークフローが起動し、正常に完了するか確認する
5. `googlemap/results/`に、結果のCSVが保存されているか確認する
6. Issueに完了コメントが投稿され、Issueが自動クローズされるか確認する

---

## 2種類の取得方法の使い分け

このシステムには、施設・レビューを取得する方法が2種類あります。データソースが異なるため、取得できる項目にも違いがあります。

| 取得方法 | Issueコマンド | 必要なSecret | オーナー返信 |
|---|---|---|---|
| Bright Data（Web Scraper API / SERP API） | `/run-reviews`系 | `BRIGHTDATA_API_TOKEN` 等 | 取得できる |
| Google Places API（公式API） | `/run-facility-places` | `GOOGLE_MAPS_API_KEY` | **取得できない**（Google公式APIの仕様上の制限） |

オーナー返信の情報が必要な場合は、必ずBright Data経由（`/run-reviews`系）を使用してください。Google Places API経由で取得したレビューは、`オーナー返信`列が常に空欄になります。これはシステムの不具合ではなく、Google Places APIが公式にオーナー返信を提供していないためです。

---

## うまくいかない場合の確認ポイント

| 症状 | 確認すること |
|---|---|
| Actionsがそもそも起動しない | Issue作成者・コメント投稿者が、Step 4の許可対象になっているか |
| `private-data`のcheckoutで失敗する | `PRIVATE_REPO_PAT`が正しく設定されているか、`googlemap`への書き込み権限があるか |
| Bright Data呼び出しで401/403エラー | `BRIGHTDATA_API_TOKEN`が正しいか、有効期限切れでないか |
| SERP APIで502エラー | Bright Data側で該当ゾーンが有効化されているか |
| 結果が`googlemap`に反映されない | Actionsのログで「Save results to private repository」ステップのエラーを確認 |

---

## 困ったときは

- Actionsの実行ログ（各ステップの出力）を確認してください
- 個々のPythonスクリプトも、`BRIGHTDATA_API_TOKEN`等の環境変数を設定すればローカルでも実行できます
- 本ドキュメントに記載のない詳細な移行経緯は、開発者側の`docs/HANDOVER_ROADMAP.md`（社内向け）を参照してください
