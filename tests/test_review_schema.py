import csv
import importlib
import tempfile
import unittest
from pathlib import Path
from unittest import mock

import pandas as pd

import main
import get_reviews_from_dental_new as dataset_reviews
from review_schema import PLACES_REVIEW_SORT_LABEL, REVIEW_FIELDNAMES


class ReviewSchemaTests(unittest.TestCase):
    def test_dataset_and_postprocessing_use_the_canonical_schema(self):
        self.assertIs(dataset_reviews.REVIEW_FIELDNAMES, REVIEW_FIELDNAMES)
        repository_root = Path(__file__).resolve().parents[1]
        for relative_path in (
            "scripts/merge_review_batches.py",
            "scripts/enrich_review_relevance_ranks.py",
            "scripts/enrich_review_relevance_ranks_state.py",
        ):
            source = (repository_root / relative_path).read_text(encoding="utf-8")
            self.assertIn("FIELDNAMES = REVIEW_FIELDNAMES", source)

    def test_places_review_uses_the_canonical_columns(self):
        row = main.build_places_review_row(
            {
                "name": "places/place-1/reviews/review-1",
                "rating": 1,
                "publishTime": "2026-08-23T22:08:22.777Z",
                "text": {"text": "レビュー本文"},
                "authorAttribution": {"displayName": "さかなちゃん"},
            },
            assigned_review_id=101,
            facility_id=117,
            facility_gid="ChIJ-test",
            display_order=1,
        )

        self.assertEqual(list(row), REVIEW_FIELDNAMES)
        self.assertEqual(row["オーナー返信"], "")
        self.assertEqual(row["レビュー表示順位"], 1)
        self.assertEqual(row["レビュー取得ソート"], PLACES_REVIEW_SORT_LABEL)
        self.assertEqual(row["レビュー日時"], "2026-08-23T22:08:22.777Z")
        self.assertEqual(row["レビューGID"], "review-1")

    def test_old_places_csv_is_expanded_and_reordered(self):
        old = pd.DataFrame(
            [{"レビューID": 1, "施設ID": 117, "レビュー本文": "本文", "レビューGID": "gid-1"}]
        )

        normalized = main.normalize_review_dataframe(old)

        self.assertEqual(list(normalized.columns), REVIEW_FIELDNAMES)
        self.assertEqual(normalized.loc[0, "レビュー本文"], "本文")
        self.assertEqual(normalized.loc[0, "オーナー返信"], "")
        self.assertEqual(normalized.loc[0, "関連度取得日時"], "")

    def test_places_pipeline_writes_the_canonical_csv(self):
        api_response = mock.Mock()
        api_response.raise_for_status.return_value = None
        api_response.json.return_value = {
            "places": [
                {
                    "id": "ChIJ-test",
                    "displayName": {"text": "テスト施設"},
                    "formattedAddress": "日本、東京都千代田区1-1",
                    "reviews": [
                        {
                            "name": "places/place-1/reviews/review-1",
                            "rating": 4,
                            "publishTime": "2026-08-23T22:08:22.777Z",
                            "text": {"text": "レビュー本文"},
                            "authorAttribution": {"displayName": "利用者"},
                        }
                    ],
                }
            ]
        }

        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            address_file = root / "address.csv"
            address_file.write_text("東京都千代田区\n", encoding="utf-8")
            facility_file = root / "facility.csv"
            review_file = root / "review.csv"
            update_facility_file = root / "facility_increment.csv"
            update_review_file = root / "review_increment.csv"

            with (
                mock.patch.object(main.requests, "post", return_value=api_response),
                mock.patch.object(main.time, "sleep"),
            ):
                main.update_mini(
                    base_query="老人ホーム",
                    api_key="test-key",
                    file_path=str(address_file),
                    facility_file=str(facility_file),
                    review_file=str(review_file),
                    update_facility_path=str(update_facility_file),
                    update_review_path=str(update_review_file),
                    exclude_gids_path=None,
                    results_dir=str(root),
                )

            for output in (review_file, update_review_file):
                with output.open("r", encoding="utf-8", newline="") as stream:
                    reader = csv.DictReader(stream)
                    rows = list(reader)
                self.assertEqual(reader.fieldnames, REVIEW_FIELDNAMES)
                self.assertEqual(rows[0]["オーナー返信"], "")
                self.assertEqual(rows[0]["レビュー取得ソート"], PLACES_REVIEW_SORT_LABEL)
                self.assertEqual(rows[0]["レビュー日時"], "2026-08-23T22:08:22.777Z")

    def test_serp_writer_uses_the_same_columns(self):
        with mock.patch("builtins.print"):
            serp = importlib.import_module("reviews_BrightData_50")

        review = {
            "assigned_review_id": 101,
            "facility_id": "117",
            "facility_gid": "ChIJ-test",
            "rating": 1,
            "reviewer_name": "さかなちゃん",
            "timestamp": "2026-08-23T22:08:22.777Z",
            "text": "レビュー本文",
            "response_of_owner": "オーナー返信本文",
            "review_display_order": 1,
            "review_sort": "qualityScore",
            "review_gid": "review-1",
        }

        with tempfile.TemporaryDirectory() as temp_dir:
            output = Path(temp_dir) / "reviews.csv"
            serp.save_reviews_to_csv(output, [review])
            with output.open("r", encoding="utf-8", newline="") as stream:
                reader = csv.DictReader(stream)
                rows = list(reader)

        self.assertEqual(reader.fieldnames, REVIEW_FIELDNAMES)
        self.assertEqual(rows[0]["オーナー返信"], "オーナー返信本文")
        self.assertEqual(rows[0]["関連度ランク"], "")
        self.assertEqual(rows[0]["関連度取得ソート"], "")
        self.assertEqual(rows[0]["関連度取得日時"], "")
        self.assertEqual(rows[0]["レビュー取得ソート"], "関連度順（SERP API）")


if __name__ == "__main__":
    unittest.main()
