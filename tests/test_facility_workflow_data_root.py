from pathlib import Path
import unittest


REPOSITORY_ROOT = Path(__file__).resolve().parents[1]


class FacilityWorkflowDataRootTests(unittest.TestCase):
    def test_facility_workflows_pass_workspace_as_private_data_root(self):
        workflow_paths = [
            REPOSITORY_ROOT / ".github/workflows/issue-ops-universal.yml",
            REPOSITORY_ROOT / ".github/workflows/brightdata_facility.yml",
        ]

        for workflow_path in workflow_paths:
            with self.subTest(workflow=workflow_path.name):
                workflow = workflow_path.read_text(encoding="utf-8")
                run_step = workflow.split("- name: Run facility scraper", maxsplit=1)[1]
                run_step = run_step.split("- name:", maxsplit=1)[0]

                self.assertIn(
                    "PRIVATE_DATA_ROOT: ${{ github.workspace }}",
                    run_step,
                )
                self.assertIn("python faiility_brightdata_new_version.py", run_step)

    def test_issue_orchestrator_validates_the_facility_wrapper(self):
        workflow_path = REPOSITORY_ROOT / ".github/workflows/issue-ops-universal.yml"
        workflow = workflow_path.read_text(encoding="utf-8")

        self.assertIn('"faiility_brightdata_new_version.py"', workflow)

    def test_places_workflows_validate_address_templates_before_api_calls(self):
        places_workflow = (
            REPOSITORY_ROOT / ".github/workflows/main_places_api.yml"
        ).read_text(encoding="utf-8")
        issue_workflow = (
            REPOSITORY_ROOT / ".github/workflows/issue-ops-universal.yml"
        ).read_text(encoding="utf-8")

        self.assertIn("python address_csv_validator.py", places_workflow)
        self.assertIn("load_address_queries(data_path(address_csv))", issue_workflow)
        self.assertIn('"address_csv_validator.py"', issue_workflow)


if __name__ == "__main__":
    unittest.main()
