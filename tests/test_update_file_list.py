import json
import tempfile
import unittest
from pathlib import Path

from update_file_list import classify_settings_file, extract_places_profiles


class ExtractPlacesProfilesTests(unittest.TestCase):
    def test_extracts_safe_webapp_fields_and_normalizes_paths(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            settings_dir = Path(temp_dir)
            (settings_dir / "address_test.csv").write_text(
                "都道府県,市区町村\n北海道,札幌市\n",
                encoding="utf-8",
            )
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

    def test_invalid_address_template_is_not_exposed_to_webapp(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            settings_dir = Path(temp_dir)
            invalid_address = settings_dir / "address_bad.csv"
            invalid_address.write_text(
                "施設名,電話番号\nテスト施設,000-0000\n",
                encoding="utf-8",
            )
            (settings_dir / "settings.json").write_text(
                json.dumps([{
                    "task_name": "invalid",
                    "query": "歯科医院",
                    "address_csv_path": "address_bad.csv",
                }], ensure_ascii=False),
                encoding="utf-8",
            )

            entry = classify_settings_file(
                invalid_address.name,
                str(invalid_address),
            )
            profiles = extract_places_profiles(str(settings_dir))

        self.assertNotIn("address_input", entry["purposes"])
        self.assertEqual(entry["validation_status"], "invalid_address_template")
        self.assertEqual(profiles, [])


if __name__ == "__main__":
    unittest.main()
