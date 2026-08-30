from pathlib import Path
import unittest


REPOSITORY_ROOT = Path(__file__).resolve().parents[1]


class ApiServiceCostGuideTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.guide = (
            REPOSITORY_ROOT / "docs/API_SERVICE_COST_GUIDE.md"
        ).read_text(encoding="utf-8")

    def test_requested_service_links_are_documented(self):
        self.assertIn("https://get.brightdata.com/g0nvj7i1g1ho", self.guide)
        self.assertIn("mapsplatform.google.com/pricing/", self.guide)
        self.assertIn("#subscribe-to-save", self.guide)

    def test_current_places_sku_is_not_described_as_subscription_included(self):
        self.assertIn("Text Search Enterprise + Atmosphere", self.guide)
        self.assertIn("サブスク加入後も従量課金になる可能性", self.guide)
        self.assertIn("places.reviews", self.guide)

    def test_brightdata_comparison_keeps_units_distinct(self):
        self.assertIn("US$1.5／1,000成功records", self.guide)
        self.assertIn("単純な`1,000対1,000`比較はできません", self.guide)
        self.assertIn("オーナー返信", self.guide)
        self.assertIn("1施設につき最大5件", self.guide)
        self.assertIn("`days_back`へ過去何日分かを指定", self.guide)
        self.assertIn("期間内の全レビューが常に返ることを保証するものではありません", self.guide)

    def test_cost_guide_is_linked_from_operator_documents(self):
        for relative_path in (
            "README.md",
            "docs/README.md",
            "docs/CLIENT_HANDOVER_GUIDE.md",
            "docs/USER_OPERATION_MANUAL.md",
        ):
            document = (REPOSITORY_ROOT / relative_path).read_text(encoding="utf-8")
            with self.subTest(document=relative_path):
                self.assertIn("API_SERVICE_COST_GUIDE.md", document)


if __name__ == "__main__":
    unittest.main()
