# n8n・Googleレビュー補助処理 操作ガイド

更新日: 2026-08-25

n8nは次の2機能だけに使用します。

1. Googleログイン状態（以下「Googleプロファイル」）を半手動で作成・更新する
2. Google Maps画面からレビューの関連度順位を抽出する

どちらも**Codexを開いた状態で、Codexの案内と確認を受けながら実行することが条件**です。お客様がn8nだけを単独操作する運用は対象外です。

WebAppの日常操作、既存／新規出力、ID採番については[`USER_OPERATION_MANUAL.md`](USER_OPERATION_MANUAL.md)を先に確認してください。

## 1. 構成

```text
01 Google profile - Semi-automatic setup
  → Chromiumを開く
  → 利用者がGoogleへ手動ログイン
  → storage_state JSONを自動保存

02 Google Reviews - Data extraction
  → 入力・件数をCodexが確認
  → Google Mapsから関連度順位を抽出
  → googlemap/results/*.csvを更新
```

Google Chrome本体のプロファイルフォルダーはコピーしません。Playwrightの`storage_state` JSONにログイン状態を保存します。このファイルにはCookieなどの認証情報が含まれるため、Secretと同じ扱いにします。

## 2. 前提

- Windows PowerShell
- Python 3.11以降
- Node.jsと`npx`
- Codexデスクトップアプリ
- コードリポジトリ`brightdata_ELT`
- Privateデータリポジトリ`googlemap`（`results/`を含む）

2つのリポジトリは任意の場所へcloneできます。固定ドライブ名や固定ユーザー名は使いません。

## 3. n8nを起動する

Codexに「n8nのGoogleプロファイル作成を案内して」と依頼し、コードリポジトリとデータリポジトリの場所を確認してから実行します。

```powershell
Set-Location C:\path\to\brightdata_ELT
powershell.exe -ExecutionPolicy Bypass -File .\n8n\start_n8n_windows.ps1 `
  -DataRoot C:\path\to\googlemap
```

`http://localhost:5678`を開きます。Googleプロファイルがまだなくてもn8nは起動できます。

## 4. 2つのワークフローを取り込む

n8nの`Import from file`から次の順に取り込みます。

1. `n8n/google_profile_semiautomatic_workflow.json`
2. `n8n/google_reviews_local_relevance_workflow.json`

ワークフロー内のパスは起動スクリプトが設定した環境変数から取得します。取り込み後に個人PCのパスへ書き換える必要はありません。

## 5. 機能1: Googleプロファイルの半手動作成

1. Codexにプロファイル作成を開始すると伝える
2. `01 Google profile - Semi-automatic setup (Codex assisted)`を開く
3. `Edit profile settings`で`codex_assisted`を`true`にする
4. `wait_seconds`を確認する。既定は300秒
5. `Execute workflow`を押す
6. 開いたChromiumで利用するGoogleアカウントへ手動ログインする
7. Google Mapsが表示できることを確認し、ブラウザーを開いたまま待つ
8. 指定時間後にn8nがログイン状態を保存する
9. Codexに完了ログとファイル作成を確認してもらう

保存先は既定で`n8n/.secrets/google-maps-storage-state.json`です。`.gitignore`対象のためGitへは入りません。

ログインできていない場合は保存処理がエラーになります。パスワード、Cookie、storage_stateの内容をCodex、Issue、チャットへ貼らないでください。

ログイン期限切れやアカウント変更時は同じ手順で作り直します。

## 6. 機能2: データ抽出

実行前にCodexへ次を確認してもらいます。

- 入力レビューCSVと施設CSVが存在する
- 出力先が意図したファイルである
- 同じCSVを別の処理が更新中ではない
- 最初は`limit=10`である
- 既存CSVを上書きする場合は復旧元がある

確認後、`02 Google Reviews - Data extraction (Codex assisted)`を開きます。

1. `Edit run settings`で`codex_assisted`を`true`にする
2. 入出力ファイルを確認する
3. `rank_limit=10`、`start=1`、`limit=10`でテストする
4. `Execute workflow`を押す
5. Codexに実行ログと出力CSVを確認してもらう

既定の入出力:

| 用途 | `googlemap`からの相対パス |
|---|---|
| レビュー入力・更新先 | `results/dental_reviews.csv` |
| 施設入力 | `results/dental_new.csv` |
| 新規レビュー候補 | `results/increments/*.csv` |
| 実行サマリー | `results/relevance_rank_summary_local.csv` |
| 順位詳細 | `results/relevance_rank_detail_local.csv` |
| 未一致レビュー | `results/relevance_rank_unmatched_reviews_local.csv` |

## 7. 10件テストの合格条件

- レビューCSVの共通15列が保たれている
- `関連度ランク`、`関連度取得ソート`、`関連度取得日時`が対象レビューへ入った
- summary、detail、unmatchedの各CSVが作成された
- レビュー本文、レビューGID、施設IDが意図せず変更されていない
- エラー施設がある場合、Codexがsummaryとdebug出力を確認した

10件の次は100件で確認し、その後に件数を増やします。長時間実行中はPCをスリープさせません。

## 8. 途中再開

- `start`: 再開する施設位置（1始まり）
- `limit`: 処理施設数。`0`は開始位置以降の全件
- `allow_failures`: 一部施設の失敗を記録して続ける場合は`true`

途中再開時も、Codexが前回summaryと開始位置を照合してから`codex_assisted=true`へ変更します。

## 9. GitHub Actionsで同じログイン状態を使う場合

`.github/workflows/relevance_ranks_playwright_state.yml`も同じ`storage_state`方式です。Actionsで使う場合だけ、JSONをBase64化して`GOOGLE_MAPS_STORAGE_STATE_B64` Secretへ登録します。

```powershell
$statePath = '.\n8n\.secrets\google-maps-storage-state.json'
$stateBytes = [IO.File]::ReadAllBytes((Resolve-Path -LiteralPath $statePath))
$stateB64 = [Convert]::ToBase64String($stateBytes)
gh secret set GOOGLE_MAPS_STORAGE_STATE_B64 --repo jmh8128494-cloud/brightdata_ELT --body $stateB64
Remove-Variable stateB64, stateBytes
```

## 10. 注意点

- `codex_assisted`は、Codexが入力、件数、復旧方法を確認済みであることの確認欄です。確認前に`true`へしません。
- Google Mapsの画面構造変更やログイン確認で失敗する場合があります。
- n8nはWindowsローカルで起動します。Docker版n8nは対象外です。
- この経路はSERP APIの復旧手段ではありません。
- Secrets、Google認証情報、Private CSVの内容を公開ログへ出力しません。
