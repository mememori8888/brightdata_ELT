# n8n・Googleログイン状態 操作ガイド

更新日: 2026-08-25

この経路は、Google Mapsの画面からレビューの関連度順位を取得するローカル補助処理です。WebAppの5処理とは別で、Windows PC上のn8nから手動実行します。

## 1. 構成

```text
n8n画面
  → n8n/run_local_relevance.ps1
  → scripts/enrich_review_relevance_ranks_state.py
  → googlemap/results/*.csv
```

Google Chromeのプロファイルフォルダーをコードへ固定しません。専用Chromiumで一度手動ログインし、Playwrightの`storage_state` JSONを再利用します。このJSONにはCookieなどの認証情報が含まれるため、Gitへ追加したり他人へ渡したりしないでください。

## 2. 前提

- Windows PowerShell
- Python 3.11以降
- Node.jsと`npx`
- コードリポジトリ`brightdata_ELT`
- Privateデータリポジトリ`googlemap`（`results/`を含む）

2つのリポジトリはどこへcloneしても構いません。以下では実際の絶対パスへ読み替えます。

## 3. 初回セットアップとGoogleログイン

コードリポジトリで次を実行します。

```powershell
Set-Location C:\path\to\brightdata_ELT
powershell.exe -ExecutionPolicy Bypass -File .\n8n\setup_google_login.ps1
```

スクリプトはPython依存パッケージとPlaywright Chromiumを準備し、Chromiumを開きます。

1. 使用するGoogleアカウントでログインする
2. Google Mapsが表示できることを確認する
3. PowerShellへ戻ってEnterを押す

ログイン状態は既定で`n8n/.secrets/google-maps-storage-state.json`へ保存されます。この場所は`.gitignore`対象です。

ログイン期限切れやアカウント変更時は、同じコマンドをもう一度実行して更新します。

## 4. n8nの起動

`-DataRoot`には`googlemap`の絶対パスを指定します。

```powershell
Set-Location C:\path\to\brightdata_ELT
powershell.exe -ExecutionPolicy Bypass -File .\n8n\start_n8n_windows.ps1 `
  -DataRoot C:\path\to\googlemap
```

起動後に`http://localhost:5678`を開きます。初回はn8nのローカル管理ユーザーを作成します。

## 5. ワークフローの取り込み

n8n画面で`Import from file`を選び、コードリポジトリ内の次のファイルを取り込みます。

```text
n8n/google_reviews_local_relevance_workflow.json
```

ワークフロー内のパスは、起動スクリプトが設定した環境変数から自動的に組み立てます。開発者個人のドライブ名やユーザー名を直す必要はありません。

既定の入出力:

| 用途 | `googlemap`からの相対パス |
|---|---|
| レビュー入力・更新先 | `results/dental_reviews.csv` |
| 施設入力 | `results/dental_new.csv` |
| 新規レビュー候補 | `results/increments/*.csv` |
| 実行サマリー | `results/relevance_rank_summary_local.csv` |
| 順位詳細 | `results/relevance_rank_detail_local.csv` |
| 未一致レビュー | `results/relevance_rank_unmatched_reviews_local.csv` |

別ファイルを使う場合は、n8nの`Edit run settings`ノードで変更します。

## 6. 10件テスト

取り込み直後の初期値は小規模テストです。

- `rank_limit`: `10`
- `start`: `1`
- `limit`: `10`
- `allow_failures`: `true`

`Execute workflow`を押し、完了後に次を確認します。

- `dental_reviews.csv`の15列が保たれている
- `関連度ランク`、`関連度取得ソート`、`関連度取得日時`が対象レビューへ入った
- summary、detail、unmatchedの各CSVが作成された
- 既存のレビュー本文、レビューGID、施設IDが変更されていない

## 7. 途中再開と本番件数

`Edit run settings`で次を変更します。

- `start`: 再開する施設位置（1始まり）
- `limit`: 処理する施設数。`0`は開始位置以降の全件
- `allow_failures`: 一部施設の失敗を記録して続ける場合は`true`

最初は10件、次に100件で確認してから増やします。長時間実行中はPCをスリープさせないでください。

## 8. GitHub Actionsで同じログイン状態を使う場合

`.github/workflows/relevance_ranks_playwright_state.yml`は同じ`storage_state`方式です。Actionsで使う場合だけ、JSONをBase64化して`GOOGLE_MAPS_STORAGE_STATE_B64` Secretへ登録します。

GitHub CLIを使う例:

```powershell
$statePath = '.\n8n\.secrets\google-maps-storage-state.json'
$stateBytes = [IO.File]::ReadAllBytes((Resolve-Path -LiteralPath $statePath))
$stateB64 = [Convert]::ToBase64String($stateBytes)
gh secret set GOOGLE_MAPS_STORAGE_STATE_B64 --repo jmh8128494-cloud/brightdata_ELT --body $stateB64
Remove-Variable stateB64, stateBytes
```

Secretの値をIssue、ログ、チャットへ貼らないでください。ログイン状態を作り直した場合はSecretも更新します。

## 9. 注意点

- Google Mapsの画面構造変更やログイン確認により失敗することがあります。summaryとdebug出力で対象施設を確認します。
- n8nはWindowsローカルで起動します。Docker版n8nからホスト側のファイルやブラウザーを操作する構成にはしていません。
- 同じレビューCSVを複数処理から同時更新しないでください。
- この経路はSERP APIの復旧手段ではありません。SERP API再開時の確認は`SERP_API_REACTIVATION_GUIDE.md`に従います。
