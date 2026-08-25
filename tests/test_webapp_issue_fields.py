from pathlib import Path
import unittest


REPOSITORY_ROOT = Path(__file__).resolve().parents[1]


class WebAppIssueFieldTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = (REPOSITORY_ROOT / "docs/webapp/app.js").read_text(encoding="utf-8")
        cls.html = (REPOSITORY_ROOT / "docs/webapp/index.html").read_text(encoding="utf-8")

    def test_places_included_type_is_not_exposed_by_webapp(self):
        self.assertNotIn("places_included_type", self.html)
        self.assertNotIn("places_included_type", self.app)
        self.assertNotIn("data.included_type", self.app)

    def test_generated_issue_does_not_request_admin_approval(self):
        self.assertNotIn("**管理者へ**", self.app)
        self.assertNotIn("入力して承認してください", self.app)

    def test_serp_workflows_remain_available_for_future_reactivation(self):
        self.assertIn(
            "const ALLOWED_WEBAPP_WORKFLOWS = ['reviews', 'reviews_sequential', 'reviews_recent_relevance', 'facility', 'facility_places'];",
            self.app,
        )
        for workflow in ("reviews", "reviews_recent_relevance", "facility"):
            self.assertIn(f'<option value="{workflow}">', self.html)
        self.assertIn('<optgroup label="現在の運用">', self.html)
        self.assertIn('<optgroup label="SERP API再開後">', self.html)
        self.assertNotIn("SERP API利用不可", self.html)


if __name__ == "__main__":
    unittest.main()
