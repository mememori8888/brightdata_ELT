# SERP API 再開ガイド

更新日: 2026-08-25

SERP依存の3処理は将来の再開に備えてコード、Actions、WebAppへ残しています。WebAppでは「SERP API再開後」グループに分け、削除も無効化もしていません。

## 対象処理

| WebApp表示 | コマンド | 主なworkflow |
|---|---|---|
| レビュー取得 (Reviews) | `/run-reviews` | `brightdata_reviews.yml` |
| 施設データ取得 (Facility) | `/run-facility` | `brightdata_facility.yml` |
| レビュー取得・30日関連度ランク付き | `/run-reviews-relevance` | `reviews_recent_with_relevance.yml` |

## 再開前の確認

1. Bright DataへGoogle Mapsの対象エンドポイントが契約中の製品とゾーンで提供されているか確認する
2. 新しいゾーン名を`BRIGHTDATA_ZONE_NAME` Secretへ登録する
3. `BRIGHTDATA_API_TOKEN`が有効であることを確認する
4. `.github/workflows/serp_reviews_smoke.yml`を最小件数で手動実行する
5. HTTP応答だけでなく、レビュー本文または施設配列が入っていることを確認する

旧ゾーン名`serp_api2`がコードの既定値に残っていても、現在有効であるとは判断しません。契約画面またはBright Dataサポートの回答を正とします。

## 過去に確認した症状

- `google.com/reviews?fid=...&brd_json=1`がHTTP 200でも空オブジェクトを返す
- Maps place URLでは施設基本情報とレビュー件数だけが返り、レビュー本文配列がない
- raw HTML取得が無効化メッセージを返す
- ゾーン無効時に502または`zone not found`となる

上記の場合、成功扱いで本番件数を流しません。リクエスト形式、対象製品、ゾーンの有効状態をBright Dataへ確認します。

## 再開テスト

1. smoke workflowで1施設だけ確認する
2. WebAppのSERP対象処理をテスト入力・新規出力ファイル名で実行する
3. Actionsが成功し、Privateデータリポジトリへ結果が保存されたことを確認する
4. レビュー出力の場合は`review_schema.py`の共通15列と一致することを確認する
5. 新規レビュー出力のレビューIDが1から始まることを確認する
6. 既存出力ではレビューGIDの重複が除かれ、既存IDの続きで新規分だけ追加されることを確認する
7. 空本文、重複レビューGID、既存CSVの欠落がないことを確認する
8. 10件、100件の順に増やしてから通常件数へ戻す

再開確認が終わるまでは、現在の運用グループにあるGoogle Places API版とDataset逐次版を使用します。
