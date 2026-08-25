import json
import os
import tempfile
import unittest
from pathlib import Path
from unittest import mock

import main


class RunFromConfigFileOverrideTests(unittest.TestCase):
    def test_selected_files_override_config_paths(self):
        task = {
            "task_name": "test",
            "query": "歯科医院",
            "address_csv_path": "settings/default_address.csv",
            "facility_file": "results/default_facility.csv",
            "review_file": "results/default_review.csv",
            "update_facility_path": "results/default_facility_increment.csv",
            "update_review_path": "results/default_review_increment.csv",
        }
        overrides = {
            "query": "老人ホーム",
            "includedType": "dental_clinic",
            "address_csv_path": "settings/selected_address.csv",
            "facility_file": "results/selected_facility.csv",
            "review_file": "results/selected_review.csv",
            "update_facility_path": "results/selected_facility_increment.csv",
            "update_review_path": "results/selected_review_increment.csv",
            "exclude_gids_path": "settings/selected_exclude_gids.csv",
        }

        with tempfile.TemporaryDirectory() as temp_dir:
            config_path = Path(temp_dir) / "settings.json"
            config_path.write_text(json.dumps([task]), encoding="utf-8")

            with (
                mock.patch.dict(os.environ, {"GOOGLE_MAPS_API_KEY": "test-key"}),
                mock.patch.object(main.time, "sleep"),
                mock.patch.object(main, "update_mini", return_value=0) as update_mini,
            ):
                main.run_from_config(str(config_path), overrides)

        kwargs = update_mini.call_args.kwargs
        self.assertEqual(kwargs["base_query"], "老人ホーム")
        self.assertEqual(kwargs["included_type"], "dental_clinic")
        self.assertEqual(kwargs["file_path"], "settings/selected_address.csv")
        self.assertEqual(kwargs["facility_file"], "results/selected_facility.csv")
        self.assertEqual(kwargs["review_file"], "results/selected_review.csv")
        self.assertEqual(kwargs["update_facility_path"], "results/selected_facility_increment.csv")
        self.assertEqual(kwargs["update_review_path"], "results/selected_review_increment.csv")
        self.assertEqual(kwargs["exclude_gids_path"], "settings/selected_exclude_gids.csv")

    def test_blank_overrides_keep_config_paths(self):
        task = {
            "query": "歯科医院",
            "address_csv_path": "address.csv",
            "facility_file": "facility.csv",
            "review_file": "review.csv",
            "update_facility_path": "facility_increment.csv",
            "update_review_path": "review_increment.csv",
        }

        with tempfile.TemporaryDirectory() as temp_dir:
            config_path = Path(temp_dir) / "settings.json"
            config_path.write_text(json.dumps([task]), encoding="utf-8")

            with (
                mock.patch.dict(os.environ, {"GOOGLE_MAPS_API_KEY": "test-key"}),
                mock.patch.object(main.time, "sleep"),
                mock.patch.object(main, "update_mini", return_value=0) as update_mini,
            ):
                main.run_from_config(str(config_path), {"facility_file": ""})

        kwargs = update_mini.call_args.kwargs
        self.assertEqual(kwargs["file_path"], os.path.join("settings", "address.csv"))
        self.assertEqual(kwargs["facility_file"], os.path.join("results", "facility.csv"))

    def test_override_rejects_path_outside_expected_directory(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            config_path = Path(temp_dir) / "settings.json"
            config_path.write_text("[]", encoding="utf-8")

            with (
                mock.patch.dict(os.environ, {"GOOGLE_MAPS_API_KEY": "test-key"}),
                self.assertRaisesRegex(ValueError, "Expected results/\\*\\.csv"),
            ):
                main.run_from_config(
                    str(config_path),
                    {"facility_file": "../outside.csv"},
                )


if __name__ == "__main__":
    unittest.main()
