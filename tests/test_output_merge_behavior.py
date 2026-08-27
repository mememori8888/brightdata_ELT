import csv
import importlib
import tempfile
import unittest
from pathlib import Path
from unittest import mock

import get_reviews_from_dental_new as dataset_reviews
from review_schema import REVIEW_FIELDNAMES
from scripts.merge_review_batches import merge_batches


class OutputMergeBehaviorTests(unittest.TestCase):
    def write_reviews(self, path, rows):
        with Path(path).open("w", encoding="utf-8-sig", newline="") as stream:
            writer = csv.DictWriter(stream, fieldnames=REVIEW_FIELDNAMES)
            writer.writeheader()
            writer.writerows(rows)

    def test_new_output_assigns_review_ids_from_one(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            output = root / "new_reviews.csv"
            self.write_reviews(
                root / "batch_1.csv",
                [
                    {"レビューID": "501", "施設ID": "101", "レビューGID": "gid-1"},
                    {"レビューID": "502", "施設ID": "101", "レビューGID": "gid-2"},
                ],
            )

            rows, new_rows = merge_batches(output, str(root / "batch_*.csv"))

        self.assertEqual([row["レビューID"] for row in rows], ["1", "2"])
        self.assertEqual([row["レビューID"] for row in new_rows], ["1", "2"])

    def test_existing_output_keeps_ids_and_adds_only_unique_review_gid(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            output = root / "existing_reviews.csv"
            self.write_reviews(
                output,
                [{"レビューID": "7", "施設ID": "101", "レビュー本文": "既存", "レビューGID": "gid-1"}],
            )
            self.write_reviews(
                root / "batch_1.csv",
                [
                    {"レビューID": "501", "施設ID": "101", "レビュー本文": "更新", "レビューGID": "gid-1"},
                    {"レビューID": "502", "施設ID": "102", "レビュー本文": "新規", "レビューGID": "gid-2"},
                ],
            )

            rows, new_rows = merge_batches(output, str(root / "batch_*.csv"))

        self.assertEqual([row["レビューID"] for row in rows], ["7", "8"])
        self.assertEqual([row["レビューGID"] for row in rows], ["gid-1", "gid-2"])
        self.assertEqual(rows[0]["レビュー本文"], "更新")
        self.assertEqual([row["レビューGID"] for row in new_rows], ["gid-2"])

    def test_merge_keeps_successful_and_partial_artifacts_when_another_batch_is_missing(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            output = root / "reviews.csv"
            self.write_reviews(
                root / "reviews_batch_1.csv",
                [{"施設ID": "101", "レビューGID": "success-gid"}],
            )
            # batch 2 failed before producing a CSV; batch 3 produced a partial checkpoint.
            self.write_reviews(
                root / "reviews_batch_3.csv",
                [{"施設ID": "103", "レビューGID": "partial-gid"}],
            )

            rows, new_rows = merge_batches(output, str(root / "reviews_batch_*.csv"))

        self.assertEqual([row["レビューGID"] for row in rows], ["success-gid", "partial-gid"])
        self.assertEqual([row["レビューID"] for row in rows], ["1", "2"])
        self.assertEqual(len(new_rows), 2)

    def test_dataset_and_serp_new_files_start_before_review_id_one(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            with mock.patch.object(dataset_reviews, "OUTPUT_CSV", root / "dataset.csv"):
                _, _, dataset_max_id = dataset_reviews.load_existing_reviews()

            with mock.patch("builtins.print"):
                serp_reviews = importlib.import_module("reviews_BrightData_50")
                _, _, serp_max_id = serp_reviews.load_existing_reviews(root / "serp.csv")

        self.assertEqual(dataset_max_id, 0)
        self.assertEqual(serp_max_id, 0)


if __name__ == "__main__":
    unittest.main()
