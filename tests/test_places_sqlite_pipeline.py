import csv
import json
import os
import tempfile
import unittest
from pathlib import Path
from unittest import mock

import main
from places_csv_store import PlacesCsvStore
from review_schema import REVIEW_FIELDNAMES


FACILITY_FIELDS = [
    "施設ID", "施設名", "電話番号", "郵便番号", "都道府県", "市区町村", "住所",
    "web", "GoogleMap", "ランク", "カテゴリ", "緯度", "経度", "施設GID", "営業ステータス",
]


def write_rows(path, fieldnames, rows):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def read_rows(path):
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        return list(csv.DictReader(handle))


class PlacesCsvStoreScaleTests(unittest.TestCase):
    def test_streams_more_than_25000_rows_and_allocates_from_true_max_id(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            facility = root / "facility.csv"
            review = root / "review.csv"
            update_facility = root / "facility_increment.csv"
            update_review = root / "review_increment.csv"
            database = root / "progress" / "places.sqlite3"

            facility_fields = [*FACILITY_FIELDS, "担当メモ"]
            facility_rows = []
            review_rows = []
            for index in range(25_005):
                facility_rows.append({
                    "施設ID": 90_000 if index == 12_345 else index + 101,
                    "施設名": f"施設{index}",
                    "施設GID": "" if index == 25_004 else f"facility-{index}",
                    "担当メモ": "保持する列" if index == 0 else "",
                })
                review_rows.append({
                    "レビューID": 80_000 if index == 12_345 else index + 1,
                    "施設ID": index + 101,
                    "施設GID": f"facility-{index}",
                    "レビューGID": "" if index == 25_004 else f"review-{index}",
                })
            write_rows(facility, facility_fields, facility_rows)
            write_rows(review, REVIEW_FIELDNAMES, review_rows)

            store = PlacesCsvStore(
                database, facility, review, FACILITY_FIELDS, REVIEW_FIELDNAMES
            )
            try:
                with self.assertRaisesRegex(ValueError, "施設GIDが空"):
                    store.add_facility({"施設GID": "", "施設名": "採番しない"})
                self.assertEqual(store.add_review({"レビューGID": ""}), (None, False))
                facility_id, created = store.add_facility({"施設GID": "facility-new", "施設名": "新規"})
                same_id, duplicate_created = store.add_facility({"施設GID": "facility-new", "施設名": "重複"})
                review_id, review_created = store.add_review({
                    "レビューGID": "review-new",
                    "施設GID": "facility-new",
                    "施設ID": facility_id,
                })
                store.export(facility, review, update_facility, update_review)
            finally:
                store.close()

            self.assertTrue(created)
            self.assertFalse(duplicate_created)
            self.assertEqual(same_id, facility_id)
            self.assertEqual(facility_id, 90_001)
            self.assertTrue(review_created)
            self.assertEqual(review_id, 80_001)

            exported_facilities = read_rows(facility)
            exported_reviews = read_rows(review)
            self.assertEqual(len(exported_facilities), 25_006)
            self.assertEqual(len(exported_reviews), 25_006)
            self.assertEqual(exported_facilities[0]["担当メモ"], "保持する列")
            self.assertTrue(any(not row["施設GID"] for row in exported_facilities))
            self.assertEqual(len(read_rows(update_facility)), 1)
            self.assertEqual(len(read_rows(update_review)), 1)

    def test_atomic_csv_writer_keeps_previous_file_when_stream_fails(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            path = Path(temp_dir) / "output.csv"
            path.write_text("original\n", encoding="utf-8")

            def broken_rows():
                yield {"column": "first"}
                raise RuntimeError("simulated failure")

            with self.assertRaisesRegex(RuntimeError, "simulated failure"):
                PlacesCsvStore._atomic_write_csv(path, ["column"], broken_rows())

            self.assertEqual(path.read_text(encoding="utf-8"), "original\n")


class PlacesAddressResumeTests(unittest.TestCase):
    def make_files(self, root):
        address = root / "settings" / "address.csv"
        address.parent.mkdir()
        address.write_text("都道府県,市区町村\n東京都,千代田区\n大阪府,大阪市\n", encoding="utf-8")
        facility = root / "results" / "facility.csv"
        review = root / "results" / "review.csv"
        update_facility = root / "results" / "facility_increment.csv"
        update_review = root / "results" / "review_increment.csv"
        write_rows(facility, FACILITY_FIELDS, [
            {"施設ID": 500, "施設名": "既存A", "施設GID": "existing-a"},
            {"施設ID": 105, "施設名": "既存B", "施設GID": "existing-b"},
        ])
        write_rows(review, REVIEW_FIELDNAMES, [])
        return address, facility, review, update_facility, update_review

    @staticmethod
    def response(*places):
        response = mock.Mock()
        response.raise_for_status.return_value = None
        response.json.return_value = {"places": list(places)}
        return response

    @staticmethod
    def place(gid, name):
        return {
            "id": gid,
            "displayName": {"text": name},
            "formattedAddress": "日本、東京都千代田区1-1",
            "reviews": [],
        }

    def run_update(self, files):
        address, facility, review, update_facility, update_review = files
        return main.update_mini(
            base_query="歯科医院",
            api_key="test-key",
            file_path=str(address),
            facility_file=str(facility),
            review_file=str(review),
            update_facility_path=str(update_facility),
            update_review_path=str(update_review),
            exclude_gids_path=None,
            results_dir=str(facility.parent),
        )

    def test_soft_limit_resumes_and_same_run_gid_uses_one_id(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            files = self.make_files(Path(temp_dir))
            first = self.response(self.place("new-a", "新規A"))
            with (
                mock.patch.object(main.requests, "post", return_value=first),
                mock.patch.object(main.time, "sleep"),
                mock.patch.object(main.time, "monotonic", side_effect=[0, 0, 61]),
                mock.patch.dict(os.environ, {"PLACES_SOFT_LIMIT_MINUTES": "1"}),
            ):
                self.run_update(files)

            status_path = files[1].parent / "places_run_status.json"
            partial = json.loads(status_path.read_text(encoding="utf-8"))
            self.assertEqual(partial["status"], "partial")
            self.assertEqual(partial["next_address_index"], 1)

            second = self.response(self.place("new-a", "重複A"), self.place("new-b", "新規B"))
            with (
                mock.patch.object(main.requests, "post", return_value=second) as post,
                mock.patch.object(main.time, "sleep"),
                mock.patch.object(main.time, "monotonic", return_value=0),
                mock.patch.dict(os.environ, {"PLACES_SOFT_LIMIT_MINUTES": "240"}),
            ):
                self.run_update(files)

            facilities = read_rows(files[1])
            gids = [row["施設GID"] for row in facilities]
            ids = {row["施設GID"]: row["施設ID"] for row in facilities}
            self.assertEqual(post.call_count, 1)
            self.assertEqual(gids.count("new-a"), 1)
            self.assertEqual(gids.count("new-b"), 1)
            self.assertEqual(ids["new-a"], "501")
            self.assertEqual(ids["new-b"], "502")
            self.assertEqual(len(read_rows(files[3])), 2)
            self.assertEqual(read_rows(files[4]), [])
            self.assertEqual(json.loads(status_path.read_text(encoding="utf-8"))["status"], "success")

    def test_api_failure_exports_only_committed_addresses_and_can_resume(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            files = self.make_files(Path(temp_dir))
            success = self.response(self.place("new-a", "新規A"))
            with (
                mock.patch.object(
                    main.requests,
                    "post",
                    side_effect=[success, *[main.requests.exceptions.ConnectionError("offline") for _ in range(5)]],
                ),
                mock.patch.object(main.time, "sleep"),
                mock.patch.object(main.time, "monotonic", return_value=0),
            ):
                with self.assertRaisesRegex(Exception, "Max retries exceeded"):
                    self.run_update(files)

            facilities = read_rows(files[1])
            self.assertEqual([row["施設GID"] for row in facilities].count("new-a"), 1)
            self.assertEqual(len(facilities), 3)
            status = json.loads((files[1].parent / "places_run_status.json").read_text(encoding="utf-8"))
            self.assertEqual(status["status"], "failed")
            self.assertEqual(status["next_address_index"], 1)


if __name__ == "__main__":
    unittest.main()
