from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from oss_readiness.checks import analyze_repository


class ReadinessChecksTest(unittest.TestCase):
    def test_minimal_repo_reports_missing_docs(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            (root / "README.md").write_text("# Demo\n\nUsage: run it.\n", encoding="utf-8")

            report = analyze_repository(root)

        self.assertLess(report.score, 60)
        self.assertTrue(any(check.id == "license" and check.status == "fail" for check in report.checks))
        self.assertTrue(any(check.id == "readme" for check in report.checks))

    def test_ready_repo_scores_high(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            write_ready_repo(root)

            report = analyze_repository(root)

        self.assertGreaterEqual(report.score, 80)
        self.assertLessEqual(report.failed, 2)

    def test_unknown_license_does_not_receive_full_credit(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            (root / "README.md").write_text("# Demo\n\nInstall and usage.\n", encoding="utf-8")
            (root / "LICENSE").write_text("All rights reserved.\n", encoding="utf-8")

            report = analyze_repository(root)

        license_check = next(check for check in report.checks if check.id == "license")
        self.assertEqual(license_check.status, "partial")
        self.assertLess(license_check.points, license_check.max_points)

    def test_empty_tests_directory_does_not_receive_full_credit(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            (root / "README.md").write_text("# Demo\n\nInstall and usage.\n", encoding="utf-8")
            (root / "tests").mkdir()

            report = analyze_repository(root)

        tests_check = next(check for check in report.checks if check.id == "tests")
        self.assertEqual(tests_check.status, "partial")
        self.assertLess(tests_check.points, tests_check.max_points)


def write_ready_repo(root: Path) -> None:
    (root / "README.md").write_text(
        """# Ready Repo

## Install

Run the install command.

## Usage

Use the CLI with examples.

## Contributing

Maintainers review issues, pull requests, tests, and releases.
""",
        encoding="utf-8",
    )
    (root / "LICENSE").write_text("MIT License\n", encoding="utf-8")
    (root / "CONTRIBUTING.md").write_text("Run tests. Open an issue before a large PR. Keep style consistent.\n", encoding="utf-8")
    (root / "SECURITY.md").write_text("Report vulnerabilities privately.\n", encoding="utf-8")
    (root / "CODE_OF_CONDUCT.md").write_text("Be respectful and constructive.\n", encoding="utf-8")
    (root / "pyproject.toml").write_text("[project]\nname = 'ready'\n", encoding="utf-8")
    (root / "tests").mkdir()
    (root / "tests" / "test_ready.py").write_text("def test_ready():\n    assert True\n", encoding="utf-8")
    (root / ".github" / "ISSUE_TEMPLATE").mkdir(parents=True)
    (root / ".github" / "ISSUE_TEMPLATE" / "bug_report.md").write_text("Bug report\n", encoding="utf-8")
    (root / ".github" / "ISSUE_TEMPLATE" / "feature_request.md").write_text("Feature request\n", encoding="utf-8")
    (root / ".github" / "pull_request_template.md").write_text("Summary\nTests\n", encoding="utf-8")
    (root / ".github" / "workflows").mkdir(parents=True)
    (root / ".github" / "workflows" / "ci.yml").write_text("name: CI\nrun-name: test\njobs:\n  test:\n    steps:\n      - run: pytest\n      - run: ruff check .\n", encoding="utf-8")


if __name__ == "__main__":
    unittest.main()
