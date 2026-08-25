from pathlib import Path
import re
import unittest


REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
TARGET_OWNER = "jmh8128494-cloud"
TARGET_CODE_REPOSITORY = "brightdata_ELT"
TARGET_DATA_REPOSITORY = f"{TARGET_OWNER}/googlemap"


class TransferConfigurationTests(unittest.TestCase):
    def test_webapp_targets_the_transferred_code_and_data_repositories(self):
        app = (REPOSITORY_ROOT / "docs/webapp/app.js").read_text(encoding="utf-8")
        html = (REPOSITORY_ROOT / "docs/webapp/index.html").read_text(encoding="utf-8")

        self.assertIn(f"const GITHUB_OWNER = '{TARGET_OWNER}';", app)
        self.assertIn(f"const GITHUB_REPO = '{TARGET_CODE_REPOSITORY}';", app)
        self.assertIn("const DATA_REPO = 'googlemap';", app)
        self.assertIn("app.js?v=20260825-address-validation", html)

    def test_every_googlemap_checkout_targets_the_new_owner(self):
        checkout_references = []
        for workflow_path in (REPOSITORY_ROOT / ".github/workflows").glob("*.yml"):
            workflow = workflow_path.read_text(encoding="utf-8")
            checkout_references.extend(
                (workflow_path.name, repository)
                for repository in re.findall(r"repository:\s*([^\s]+/googlemap)", workflow)
            )

        self.assertTrue(checkout_references)
        for workflow_name, repository in checkout_references:
            with self.subTest(workflow=workflow_name):
                self.assertEqual(repository, TARGET_DATA_REPOSITORY)

    def test_completion_link_and_python_fallbacks_target_the_new_owner(self):
        orchestrator = (
            REPOSITORY_ROOT / ".github/workflows/issue-ops-universal.yml"
        ).read_text(encoding="utf-8")
        self.assertIn(f"https://github.com/{TARGET_DATA_REPOSITORY}", orchestrator)
        self.assertIn('[[ ",$AUTO_RUN_USERS," == *",$COMMENT_USER,"* ]]', orchestrator)

        for relative_path in ("reviews_BrightData_50.py",):
            source = (REPOSITORY_ROOT / relative_path).read_text(encoding="utf-8")
            self.assertIn(f"'GITHUB_REPOSITORY_OWNER', '{TARGET_OWNER}'", source)

    def test_current_client_docs_use_the_transfer_target(self):
        for relative_path in (
            "README.md",
            "docs/CLIENT_ACCEPTANCE_TEST_GUIDE.md",
            "docs/CLIENT_HANDOVER_GUIDE.md",
            "docs/issueオーケストレーション.md",
        ):
            document = (REPOSITORY_ROOT / relative_path).read_text(encoding="utf-8")
            self.assertNotIn("mememori" + "8888", document)
            self.assertIn(TARGET_OWNER, document)


if __name__ == "__main__":
    unittest.main()
