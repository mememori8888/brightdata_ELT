import csv
import logging
import os
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest
from unittest.mock import Mock, patch

import facility_BrightData_20 as facility


class FacilityApiFailureTests(unittest.TestCase):
    def run_scraper(self, response):
        with TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory)
            settings_dir = root / "settings"
            results_dir = root / "results"
            settings_dir.mkdir()
            results_dir.mkdir()

            address_file = settings_dir / "address.csv"
            with address_file.open("w", newline="", encoding="utf-8") as stream:
                writer = csv.writer(stream)
                writer.writerow(["prefecture", "city"])
                writer.writerow(["北海道", "札幌市"])

            try:
                with (
                    patch.object(facility.requests, "post", return_value=response),
                    patch.object(facility.time, "sleep", return_value=None),
                    patch.dict(
                        os.environ,
                        {"MAX_WORKERS": "1", "MAX_REQUESTS": "1"},
                        clear=False,
                    ),
                ):
                    return facility.update_mini(
                        base_query="歯科医院",
                        api_token="test-token",
                        zone_name="missing-zone",
                        file_path=str(address_file),
                        facility_file=str(results_dir / "facility.csv"),
                        update_facility_path=str(results_dir / "facility_increment.csv"),
                        exclude_gids_path=None,
                        results_dir=str(results_dir),
                        fid_file_path=str(results_dir / "facility_fid.csv"),
                    )
            finally:
                for handler in logging.root.handlers[:]:
                    handler.close()
                    logging.root.removeHandler(handler)

    def test_all_failed_requests_raise_an_error(self):
        response = Mock(status_code=400, text='zone "missing-zone" not found')

        with self.assertRaisesRegex(RuntimeError, "全リクエストが失敗"):
            self.run_scraper(response)

    def test_successful_empty_response_is_not_an_api_failure(self):
        response = Mock(status_code=200, text="")

        self.assertEqual(self.run_scraper(response), 1)


if __name__ == "__main__":
    unittest.main()
