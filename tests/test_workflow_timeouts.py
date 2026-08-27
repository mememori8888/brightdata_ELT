from pathlib import Path
import unittest

import yaml


REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
WORKFLOW_ROOT = REPOSITORY_ROOT / ".github" / "workflows"


class WorkflowTimeoutTests(unittest.TestCase):
    def test_every_job_with_steps_has_an_explicit_five_hour_or_lower_limit(self):
        inspected = 0
        for workflow_path in sorted(WORKFLOW_ROOT.glob("*.yml")):
            workflow = yaml.safe_load(workflow_path.read_text(encoding="utf-8")) or {}
            for job_name, job in (workflow.get("jobs") or {}).items():
                if not isinstance(job, dict) or "steps" not in job:
                    continue
                inspected += 1
                with self.subTest(workflow=workflow_path.name, job=job_name):
                    self.assertIn("timeout-minutes", job)
                    self.assertLessEqual(int(job["timeout-minutes"]), 300)
        self.assertGreater(inspected, 0)

    def test_all_step_timeouts_are_270_minutes_or_lower(self):
        inspected = 0
        for workflow_path in sorted(WORKFLOW_ROOT.glob("*.yml")):
            workflow = yaml.safe_load(workflow_path.read_text(encoding="utf-8")) or {}
            for job in (workflow.get("jobs") or {}).values():
                if not isinstance(job, dict):
                    continue
                for step in job.get("steps") or []:
                    if isinstance(step, dict) and "timeout-minutes" in step:
                        inspected += 1
                        with self.subTest(workflow=workflow_path.name, step=step.get("name")):
                            self.assertLessEqual(int(step["timeout-minutes"]), 270)
        self.assertGreaterEqual(inspected, 5)

    def test_long_running_workflows_preserve_status_and_artifacts(self):
        sequential = (WORKFLOW_ROOT / "reviews_local_interactive_sequential.yml").read_text(encoding="utf-8")
        places = (WORKFLOW_ROOT / "main_places_api.yml").read_text(encoding="utf-8")
        serp_facility = (WORKFLOW_ROOT / "brightdata_facility.yml").read_text(encoding="utf-8")
        serp_reviews = (WORKFLOW_ROOT / "brightdata_reviews.yml").read_text(encoding="utf-8")
        recent_relevance = (WORKFLOW_ROOT / "reviews_recent_with_relevance.yml").read_text(encoding="utf-8")
        playwright = (WORKFLOW_ROOT / "relevance_ranks_playwright_state.yml").read_text(encoding="utf-8")

        self.assertIn("results/status/status_batch_", sequential)
        self.assertIn("if: always()", sequential)
        self.assertIn("completion_state", sequential)
        self.assertIn("failed_batches", sequential)
        self.assertIn("results/places_run_status.json", places)
        self.assertIn("completion_state", places)
        self.assertIn("results/serp_facility_run_status.json", serp_facility)
        self.assertIn("completion_state", serp_facility)
        self.assertIn("results/status/serp_reviews_", serp_reviews)
        self.assertIn("completion_state", serp_reviews)
        self.assertIn("results/status/status_batch_", recent_relevance)
        self.assertIn("completion_state", recent_relevance)
        self.assertIn("results/status/relevance_state_", playwright)
        self.assertIn("completion_state", playwright)


if __name__ == "__main__":
    unittest.main()
