from pathlib import Path
import unittest


REPOSITORY_ROOT = Path(__file__).resolve().parents[1]


class BrightDataConcurrencyTests(unittest.TestCase):
    def test_dataset_workflows_default_to_twenty_by_one(self):
        for relative_path in (
            ".github/workflows/reviews_local_interactive_sequential.yml",
            ".github/workflows/reviews_recent_with_relevance.yml",
        ):
            source = (REPOSITORY_ROOT / relative_path).read_text(encoding="utf-8")
            with self.subTest(workflow=relative_path):
                self.assertGreaterEqual(source.count("default: '20'"), 2)
                self.assertGreaterEqual(source.count("default: '1'"), 2)
                self.assertIn("api_batch_size * max_parallel_jobs > 20", source)

    def test_webapp_defaults_and_validates_the_global_limit(self):
        html = (REPOSITORY_ROOT / "docs/webapp/index.html").read_text(encoding="utf-8")
        app = (REPOSITORY_ROOT / "docs/webapp/app.js").read_text(encoding="utf-8")

        self.assertIn('id="sequential_api_batch_size" value="20"', html)
        self.assertIn('id="sequential_max_parallel_jobs" value="1"', html)
        self.assertNotIn("sequential_api_batch_size: '50'", app)
        self.assertIn("apiBatchSize * sequentialMaxParallel > 20", app)

    def test_orchestrator_and_python_entrypoints_enforce_twenty(self):
        orchestrator = (REPOSITORY_ROOT / ".github/workflows/issue-ops-universal.yml").read_text(encoding="utf-8")
        dataset = (REPOSITORY_ROOT / "get_reviews_from_dental_new.py").read_text(encoding="utf-8")
        wrapper = (REPOSITORY_ROOT / "run_reviews_local_interactive.py").read_text(encoding="utf-8")
        serp_reviews = (REPOSITORY_ROOT / "reviews_BrightData_50.py").read_text(encoding="utf-8")
        serp_facility = (REPOSITORY_ROOT / "facility_BrightData_20.py").read_text(encoding="utf-8")

        self.assertIn("api_batch_value * max_parallel_value > 20", orchestrator)
        self.assertIn("BRIGHTDATA_CONCURRENCY_LIMIT = 20", dataset)
        self.assertIn("--batch-size は1〜20", wrapper)
        self.assertIn("BRIGHTDATA_CONCURRENCY_LIMIT = 20", serp_reviews)
        self.assertIn("MAX_WORKERS <= 20", serp_facility)


if __name__ == "__main__":
    unittest.main()
