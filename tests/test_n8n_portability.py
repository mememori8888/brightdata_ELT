import json
from pathlib import Path
import unittest


REPOSITORY_ROOT = Path(__file__).resolve().parents[1]


class N8nPortabilityTests(unittest.TestCase):
    def test_workflow_uses_runtime_roots_and_storage_state(self):
        workflow_path = REPOSITORY_ROOT / "n8n/google_reviews_local_relevance_workflow.json"
        workflow_text = workflow_path.read_text(encoding="utf-8")
        json.loads(workflow_text)

        self.assertIn("BRIGHTDATA_ELT_DATA_ROOT", workflow_text)
        self.assertIn("BRIGHTDATA_ELT_ROOT", workflow_text)
        self.assertIn("GOOGLE_MAPS_STORAGE_STATE", workflow_text)
        self.assertIn("-StorageState", workflow_text)
        self.assertNotIn("profile_dir", workflow_text)
        self.assertNotIn("D:\\\\python", workflow_text)
        self.assertNotIn("C:\\\\Users", workflow_text)

    def test_windows_scripts_do_not_fix_a_developer_path(self):
        for relative_path in (
            "n8n/start_n8n_windows.ps1",
            "n8n/setup_google_login.ps1",
            "n8n/run_local_relevance.ps1",
        ):
            source = (REPOSITORY_ROOT / relative_path).read_text(encoding="utf-8")
            with self.subTest(script=relative_path):
                self.assertNotIn("D:\\python", source)
                self.assertNotIn("C:\\Users\\user", source)

    def test_authentication_state_is_ignored(self):
        root_ignore = (REPOSITORY_ROOT / ".gitignore").read_text(encoding="utf-8")
        n8n_ignore = (REPOSITORY_ROOT / "n8n/.gitignore").read_text(encoding="utf-8")
        self.assertIn("google-maps-storage-state.json", root_ignore)
        self.assertIn(".secrets/", n8n_ignore)

    def test_superseded_files_are_removed(self):
        for relative_path in (
            ".github/workflows/dental_new_reviews_sequential.yml",
            "facility_BrightData_20_update.py",
            "facility_BrightData_heatmap.py",
            "scripts/enrich_review_relevance_ranks_local.py",
            "docs/HANDOVER_ROADMAP.md",
        ):
            with self.subTest(path=relative_path):
                self.assertFalse((REPOSITORY_ROOT / relative_path).exists())


if __name__ == "__main__":
    unittest.main()
