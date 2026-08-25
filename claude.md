# 開発時の前提

フェイルセーフかつ誤操作しにくい設計を優先し、既存の外部動作を保護してから変更する。

## 実行経路

```text
WebApp → GitHub Issue → GitHub Actions → API処理 → googlemap/results/
```

中心となるオーケストレーターは`.github/workflows/issue-ops-universal.yml`。

## 主な処理

- `main.py`: Google Places APIによる施設・基本レビュー取得
- `run_reviews_local_interactive.py` → `get_reviews_from_dental_new.py`: Bright Data Datasetによる逐次レビュー取得
- `facility_BrightData_20.py`: Bright Data SERP施設取得。SERPゾーン再開後に使用
- `reviews_BrightData_50.py`: Bright Data SERPレビュー取得。SERPゾーン再開後に使用
- `faiility_brightdata_new_version.py`: Bright Data施設取得ラッパー
- `reviews_brightData_new_version.py`: Bright Dataレビュー取得ラッパー

絶対パスや特定開発環境のワークスペース名をコードへ固定しない。運用・受入条件は`docs/CLIENT_HANDOVER_GUIDE.md`と`docs/CLIENT_ACCEPTANCE_TEST_GUIDE.md`を正本とする。
