import unittest
from pathlib import Path


REPOSITORY_ROOT = Path(__file__).resolve().parents[1]


class UserOperationManualTests(unittest.TestCase):
    def test_manual_documents_existing_and_new_output_behavior(self):
        manual = (REPOSITORY_ROOT / "docs/USER_OPERATION_MANUAL.md").read_text(encoding="utf-8")

        self.assertIn("既存ファイルを選んだ場合", manual)
        self.assertIn("新規ファイルを選んだ場合", manual)
        self.assertIn("`施設GID`", manual)
        self.assertIn("`レビューGID`", manual)
        self.assertIn("新規レビューCSV: `レビューID`を`1`から", manual)
        self.assertIn("新規施設CSV: `施設ID`を`101`から", manual)
        self.assertIn("同じ出力CSVへ複数Actionsを同時実行しない", manual)
        self.assertIn("増分施設・増分レビューファイル名は設定プリセットごとに固定", manual)

    def test_manual_is_linked_from_docs_root_readme_and_webapp(self):
        docs_readme = (REPOSITORY_ROOT / "docs/README.md").read_text(encoding="utf-8")
        root_readme = (REPOSITORY_ROOT / "README.md").read_text(encoding="utf-8")
        html = (REPOSITORY_ROOT / "docs/webapp/index.html").read_text(encoding="utf-8")

        self.assertIn("USER_OPERATION_MANUAL.md", docs_readme)
        self.assertIn("docs/USER_OPERATION_MANUAL.md", root_readme)
        self.assertIn("../USER_OPERATION_MANUAL.html", html)
        self.assertIn("新規作成では施設IDは101、レビューIDは1から採番", html)


if __name__ == "__main__":
    unittest.main()
