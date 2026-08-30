# APIサービス契約・料金比較

更新日: 2026-08-31

この文書は、本システムが使用するGoogle Maps PlatformとBright Dataの契約入口、課金単位、選定上の注意をまとめた正本です。料金、無料枠、対象SKUは変更されるため、契約前と本番全件実行前にリンク先の最新表示とCloud Console／Bright Data Control Panelの契約内容を確認してください。記載額は米ドル、税・為替換算前です。

## 1. 契約・料金ページ

- [Bright Dataの申込・アカウント作成](https://get.brightdata.com/g0nvj7i1g1ho)
- [Bright Data Web Scraper API料金](https://brightdata.com/pricing/web-scraper)
- [Bright Data SERP API料金](https://brightdata.com/pricing/serp)
- [Google Maps Platformのサブスクリプション／従量課金](https://mapsplatform.google.com/pricing/?utm_source=gnp&utm_medium=email&utm_campaign=FY25-Q3-global-Maps-website-of-GNP-New-Customer-Onboarding-Journey&utm_content=pricing_variant2#subscribe-to-save)
- [Google Maps Platformサブスクリプション対象SKU](https://developers.google.com/maps/billing-and-pricing/subscriptions)
- [Google Maps Platform Places APIのSKU別料金](https://developers.google.com/maps/billing-and-pricing/pricing)
- [Google Places APIのレビュー返却仕様](https://developers.google.com/maps/documentation/places/web-service/reference/rest/v1/places)

申込リンクを開いた後も、契約主体、請求先、月間上限、解約条件、利用する製品名を管理者が確認します。API token、API key、請求情報はIssueやリポジトリへ記載しません。

## 2. Google Maps Platformサブスクリプション

2026-08-31時点で公式料金ページに表示されるプランです。

| プラン | 月額 | 月間合算call | 主な対象 |
|---|---:|---:|---|
| Starter | US$100 | 50,000 | Dynamic Maps、Geocoding等の基本機能 |
| Essentials | US$275 | 100,000 | Maps、Routes、Places等の一般的な機能。Place Details Essentials等 |
| Pro | US$1,200 | 250,000 | Pro対象機能。Places API Text Search Pro等 |

上限超過分とプラン対象外SKUは従量課金です。Googleは上限到達時にAPIを自動停止せず、超過分を従量課金すると説明しています。Cloud Consoleで予算アラート、quota、利用量を別途設定してください。

### 現在のGoogle Places処理に関する重要事項

`main.py`はPlaces API (New)のText Searchを使用し、`places.reviews`、評価、電話番号、Webサイト、営業時間などをFieldMaskへ含めています。`reviews`は「Places API Text Search Enterprise + Atmosphere」を発生させるフィールドです。

2026-08-31時点のサブスクリプション対象SKU一覧には「Text Search Pro」はありますが、「Text Search Enterprise + Atmosphere」は掲載されていません。そのため、現在のコードはStarter／Essentials／Proの定額callへ含まれず、サブスク加入後も従量課金になる可能性があります。契約前にGoogle Cloudの請求SKUとサブスクリプション対象を確認してください。

従量課金表ではText Search Enterprise + Atmosphereは、月間無料枠1,000リクエスト、その後100,000リクエストまでUS$40／1,000リクエストと表示されています。大量実行前に少数住所でBilling reportの実SKUと金額を確認します。

## 3. Bright Dataの料金

2026-08-31時点の公式料金ページに表示される代表値です。

| 製品 | 無料枠 | Pay as you go | 月額プラン例 | 本システムでの用途 |
|---|---:|---:|---:|---|
| Web Scraper API / Google Maps Reviews | 月5,000 records | US$1.5／1,000成功records | US$499で384,000 records、追加US$1.3／1,000 | Dataset逐次レビュー、レビュー本文・オーナー返信 |
| SERP API | 月5,000 requests | US$1.5／1,000成功requests | US$499で380,000 requests、追加US$1.3／1,000 | SERP施設・SERPレビュー・関連度。現在はゾーン再開待ち |

Bright Dataは成功したrecordまたはrequest単位です。Web Scraper APIの1 recordは通常1件の取得レコードであり、Google Places APIの1 requestとは同じ単位ではありません。契約画面に表示されるDataset固有の料金がこの表と異なる場合は、契約画面を優先します。

## 4. Google PlacesとBright Dataの料金比較

| 比較点 | Google Places API (New) | Bright Data Web Scraper / SERP |
|---|---|---|
| 課金単位 | API request。FieldMaskの最も高いSKUで決定 | 成功recordまたは成功request |
| 表示単価の例 | 現行FieldMaskはText Search Enterprise + Atmosphere。無料枠後US$40／1,000 requests | Pay as you goはUS$1.5／1,000成功recordsまたはrequests |
| 施設検索 | 公式Placesデータ。1 requestで複数施設を返す | SERP／Maps Scraperの成功request・record単位 |
| レビュー | 1施設につき最大5件。関連度順で返り、期間指定や全件取得はできない。オーナー返信は現在の出力で取得できない | `days_back`へ過去何日分かを指定し、その期間内レビューを取得。多数レビューとオーナー返信の取得に使用 |
| 定額プラン | Starter、Essentials、Pro。ただし現行Enterprise + Atmosphere SKUは対象外の可能性 | US$499等の月額枠。製品ごとに契約・請求単位を確認 |
| 現在の採用方針 | 施設検索と少数のPlacesレビュー | Dataset逐次レビュー。SERP系はゾーン再開後 |

単価だけを見るとBright Dataが安く見えますが、Googleの1 requestは複数施設を返し、Bright Dataはreview等の1 recordごとに課金されるため、単純な`1,000対1,000`比較はできません。取得件数、必要列、レビュー数、オーナー返信の要否で比較します。

Google Places APIの`reviews[]`は、公式仕様上1施設につき最大5件です。Google側で返却対象が選ばれるため、「過去30日」「前回取得後の全レビュー」のような期間指定には使いません。一方、Bright Data Dataset逐次レビューはWebAppの`days_back`で`1`、`30`などを指定し、実行日時から過去○日以内のレビューを取得します。対象期間内にレビューが多数あれば5件を超えて取得でき、オーナー返信も取得対象です。Google Maps側の表示状態やDataset応答によって、指定期間内の全レビューが常に返ることを保証するものではありません。

参考として無料枠を除外した単価の単純計算では、Googleの現行SKU 10,000 requestsはUS$400、Bright Data Pay as you go 10,000成功records／requestsはUS$15です。これは同じ件数の施設・レビューを取得できるという意味ではありません。

## 5. 本番前の選定手順

1. Google Placesを住所1～3件で実行し、Cloud Billing reportに出たSKUとrequest数を記録する。
2. Bright Data Datasetを20URL以下、`days_back=30`等の小規模条件で実行し、成功review recordsと実請求額を記録する。
3. `1施設あたりの取得レビュー数`、オーナー返信、欠損列を比較する。
4. 月間住所数、Google request数、Bright Data record数を見積もる。
5. 無料枠、サブスク対象外料金、月額枠超過料金を含めた月額を比較する。
6. Google Cloud budget alertsとBright Data monthly spend limitを設定してから全件実行する。

現在の運用では、Google Placesを施設検索、Bright Data Datasetを詳細レビューとオーナー返信に使い分けます。Googleのサブスクリプションへ加入する場合は、現在のEnterprise + Atmosphere呼び出しを含むか確認できるまで、削減額へ算入しません。
