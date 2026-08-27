import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import Mock, patch

import requests

import get_reviews_from_dental_new as reviews


TEST_ENTRY = {
    "url": "https://www.google.com/maps/place/test",
    "facility_id": "101",
    "gid": "test-gid",
}


class ReviewEmptyBatchTests(unittest.TestCase):
    def run_main_with_batch_result(self, batch_result=None, batch_error=None):
        client = Mock()
        if batch_error is not None:
            client.process_batch.side_effect = batch_error
        else:
            client.process_batch.return_value = batch_result

        with (
            patch.object(reviews, "load_dental_csv", return_value=[TEST_ENTRY]),
            patch.object(reviews, "load_existing_reviews", return_value=([], set(), 100)),
            patch.object(reviews, "BrightDataWebScraperReviews", return_value=client),
            patch.object(reviews, "ALLOW_PARTIAL_FAILURE", False),
            patch.object(reviews, "BATCH_SIZE", 20),
        ):
            reviews.main()

    def test_successful_empty_snapshot_is_not_a_failed_batch(self):
        with self.assertLogs(level="INFO") as captured:
            self.run_main_with_batch_result([])

        self.assertIn("期間内レビュー0件（正常終了）", "\n".join(captured.output))

    def test_real_batch_error_still_fails_the_run(self):
        with self.assertRaisesRegex(RuntimeError, "APIチャンクが 1 件失敗"):
            self.run_main_with_batch_error(RuntimeError("download failed"))

    def test_ready_snapshot_with_no_reviews_returns_an_empty_success(self):
        client = reviews.BrightDataWebScraperReviews("test-token", "test-dataset")

        with (
            patch.object(client, "trigger_snapshot", return_value="snapshot-1"),
            patch.object(client, "wait_for_snapshot", return_value=True),
            patch.object(client, "get_snapshot_data", return_value=[]),
        ):
            self.assertEqual(client.process_batch([{"url": TEST_ENTRY["url"]}]), [])

    def test_failed_snapshot_raises_instead_of_looking_empty(self):
        client = reviews.BrightDataWebScraperReviews("test-token", "test-dataset")

        with (
            patch.object(client, "trigger_snapshot", return_value="snapshot-1"),
            patch.object(client, "wait_for_snapshot", return_value=False),
        ):
            with self.assertRaisesRegex(RuntimeError, "Snapshot processing failed"):
                client.process_batch([{"url": TEST_ENTRY["url"]}])

    def test_trigger_http_400_is_classified_as_a_real_failure(self):
        client = reviews.BrightDataWebScraperReviews("test-token", "test-dataset")
        response = requests.Response()
        response.status_code = 400
        error = requests.exceptions.HTTPError("bad request", response=response)

        with patch.object(client, "trigger_snapshot", side_effect=error):
            with self.assertRaises(reviews.SnapshotTriggerError):
                client.process_batch([{"url": TEST_ENTRY["url"]}])

    def test_snapshot_download_failure_has_a_separate_error_type(self):
        client = reviews.BrightDataWebScraperReviews("test-token", "test-dataset")
        with (
            patch.object(client, "trigger_snapshot", return_value="snapshot-1"),
            patch.object(client, "wait_for_snapshot", return_value=True),
            patch.object(client, "get_snapshot_data", side_effect=RuntimeError("download failed")),
        ):
            with self.assertRaises(reviews.SnapshotDownloadError):
                client.process_batch([{"url": TEST_ENTRY["url"]}])

    def test_status_json_keeps_the_specific_api_error_type(self):
        client = Mock()
        client.process_batch.side_effect = reviews.SnapshotTriggerError("HTTP 400")
        with tempfile.TemporaryDirectory() as temp_dir:
            status_file = Path(temp_dir) / "status.json"
            with (
                patch.object(reviews, "load_dental_csv", return_value=[TEST_ENTRY]),
                patch.object(reviews, "load_existing_reviews", return_value=([], set(), 100)),
                patch.object(reviews, "BrightDataWebScraperReviews", return_value=client),
                patch.object(reviews, "ALLOW_PARTIAL_FAILURE", False),
                patch.object(reviews, "BATCH_SIZE", 20),
                patch.object(reviews, "RUN_STATUS_FILE", str(status_file)),
            ):
                with self.assertRaisesRegex(RuntimeError, "APIチャンクが 1 件失敗"):
                    reviews.main()

            status = json.loads(status_file.read_text(encoding="utf-8"))
            self.assertEqual(status["status"], "partial")
            self.assertEqual(status["error_type"], "SnapshotTriggerError")

    def run_main_with_batch_error(self, error):
        self.run_main_with_batch_result(batch_error=error)


if __name__ == "__main__":
    unittest.main()
