import json
import tempfile
import unittest
from pathlib import Path

from address_csv_validator import (
    AddressCsvValidationError,
    load_address_queries,
    validate_config_addresses,
)


class AddressCsvValidatorTests(unittest.TestCase):
    def write_csv(self, root, content, name="address.csv"):
        path = Path(root) / name
        path.write_text(content, encoding="utf-8")
        return path

    def test_loads_legacy_template_and_stops_at_end_marker(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            path = self.write_csv(
                temp_dir,
                "a,b,c\n北海道,札幌市,中央区\n東京都,新宿区\nend,end\n大阪府,大阪市\n",
            )

            queries = load_address_queries(path)

        self.assertEqual(queries, ["北海道 札幌市 中央区", "東京都 新宿区"])

    def test_loads_descriptive_japanese_template(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            path = self.write_csv(
                temp_dir,
                "都道府県,市区町村,町域\n兵庫県,西宮市,西宮北口\n",
            )

            self.assertEqual(load_address_queries(path), ["兵庫県 西宮市 西宮北口"])

    def test_rejects_missing_or_wrong_header(self):
        for content in (
            "北海道,札幌市\n",
            "施設名,電話番号\nテスト施設,000-0000\n",
        ):
            with self.subTest(content=content), tempfile.TemporaryDirectory() as temp_dir:
                path = self.write_csv(temp_dir, content)
                with self.assertRaisesRegex(AddressCsvValidationError, "ヘッダーが不正"):
                    load_address_queries(path)

    def test_rejects_invalid_prefecture_and_formula(self):
        cases = (
            ("都道府県,市区町村\n札幌,札幌市\n", "都道府県が不正"),
            ("都道府県,市区町村\n=北海道,札幌市\n", "数式または不正"),
        )
        for content, message in cases:
            with self.subTest(message=message), tempfile.TemporaryDirectory() as temp_dir:
                path = self.write_csv(temp_dir, content)
                with self.assertRaisesRegex(AddressCsvValidationError, message):
                    load_address_queries(path)

    def test_rejects_non_utf8_and_header_only_files(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            encoded = root / "encoded.csv"
            encoded.write_bytes("都道府県,市区町村\n北海道,札幌市\n".encode("cp932"))
            with self.assertRaisesRegex(AddressCsvValidationError, "UTF-8"):
                load_address_queries(encoded)

            empty = self.write_csv(root, "都道府県,市区町村\n", "empty.csv")
            with self.assertRaisesRegex(AddressCsvValidationError, "1行以上"):
                load_address_queries(empty)

    def test_config_validation_uses_override_or_config_address(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            settings = root / "settings"
            settings.mkdir()
            self.write_csv(settings, "a,b\n北海道,札幌市\n", "default.csv")
            self.write_csv(settings, "a,b\n東京都,新宿区\n", "selected.csv")
            config = settings / "settings.json"
            config.write_text(
                json.dumps([{"address_csv_path": "default.csv"}]),
                encoding="utf-8",
            )

            defaults = validate_config_addresses(config)
            selected = validate_config_addresses(config, "settings/selected.csv")

        self.assertEqual(defaults[0][1], 1)
        self.assertEqual(selected[0][1], 1)
        self.assertEqual(selected[0][0].name, "selected.csv")


if __name__ == "__main__":
    unittest.main()
