import json
import tempfile
import unittest
from pathlib import Path

from update_file_list import extract_places_profiles


class ExtractPlacesProfilesTests(unittest.TestCase):
    def test_extracts_safe_webapp_fields_and_normalizes_paths(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            settings_dir = Path(temp_dir)
            config = [{
                "task_name": "search-test",
                "zone_name": "secret-zone-is-not-public",
                "query": "歯科医院",
                "includedType": "dental_clinic",
                "address_csv_path": "address_test.csv",
                "facility_file": "results/dental_test",
                "review_file": "dental_test_review.csv",
                "update_facility_path": "add_dental_test.csv",
                "update_review_path": "add_dental_test_review.csv",
                "exclude_gids_path": "exclude_gids.csv",
            }]
            (settings_dir / "places_test.json").write_text(
                json.dumps(config, ensure_ascii=False), encoding="utf-8"
            )

            profiles = extract_places_profiles(str(settings_dir))

        self.assertEqual(len(profiles), 1)
        profile = profiles[0]
        self.assertEqual(profile["label"], "歯科医院（テスト）")
        self.assertEqual(profile["facility_file"], "results/dental_test.csv")
        self.assertEqual(profile["address_csv"], "settings/address_test.csv")
        self.assertEqual(profile["exclude_gids_file"], "settings/exclude_gids.csv")
        self.assertNotIn("zone_name", profile)


if __name__ == "__main__":
    unittest.main()
