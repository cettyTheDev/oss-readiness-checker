from __future__ import annotations

import json
import re
import subprocess
from dataclasses import asdict, dataclass
from pathlib import Path


@dataclass(frozen=True)
class CheckResult:
    id: str
    title: str
    points: int
    max_points: int
    status: str
    detail: str
    recommendation: str


@dataclass(frozen=True)
class ReadinessReport:
    path: str
    score: int
    passed: int
    partial: int
    failed: int
    checks: list[CheckResult]

    def to_json(self) -> str:
        return json.dumps(asdict(self), indent=2, sort_keys=True)


def analyze_repository(path: str | Path) -> ReadinessReport:
    root = Path(path).expanduser().resolve()
    if not root.exists() or not root.is_dir():
        raise FileNotFoundError(f"Repository path does not exist: {root}")

    checks = [
        check_readme(root),
        check_license(root),
        check_contributing(root),
        check_security(root),
        check_code_of_conduct(root),
        check_issue_templates(root),
        check_pull_request_template(root),
        check_ci(root),
        check_tests(root),
        check_package_metadata(root),
        check_release_tags(root),
        check_recent_activity(root),
        check_secret_hygiene(root),
    ]
    earned = sum(check.points for check in checks)
    possible = sum(check.max_points for check in checks)
    score = round((earned / possible) * 100) if possible else 0
    passed = sum(1 for check in checks if check.status == "pass")
    partial = sum(1 for check in checks if check.status == "partial")
    failed = sum(1 for check in checks if check.status == "fail")
    return ReadinessReport(
        path=str(root),
        score=score,
        passed=passed,
        partial=partial,
        failed=failed,
        checks=checks,
    )


def check_readme(root: Path) -> CheckResult:
    readme = first_existing(root, ["README.md", "README.rst", "README.txt"])
    if not readme:
        return fail(
            "readme",
            "README",
            25,
            "No README file found.",
            "Add a README with purpose, install, usage, examples, and maintenance status.",
        )
    text = safe_read(readme)
    headings = len(re.findall(r"(?m)^(#|[A-Za-z0-9].*\n[=-]{3,}$)", text))
    has_install = bool(re.search(r"\b(install|setup|quickstart|get started)\b", text, re.I))
    has_usage = bool(re.search(r"\b(usage|example|cli|api|configuration)\b", text, re.I))
    has_maintainer_signal = bool(re.search(r"\b(maintain|contribut|issue|pull request|release)\b", text, re.I))

    points = 8
    details = ["README exists"]
    if len(text) >= 900:
        points += 5
        details.append("substantial content")
    if headings >= 3:
        points += 4
        details.append("structured headings")
    if has_install:
        points += 3
        details.append("install/setup guidance")
    if has_usage:
        points += 3
        details.append("usage examples")
    if has_maintainer_signal:
        points += 2
        details.append("maintainer/contribution context")

    return result(
        "readme",
        "README",
        points,
        25,
        "; ".join(details),
        "Add missing install, usage, examples, and maintainer workflow sections.",
    )


def check_license(root: Path) -> CheckResult:
    license_file = first_existing(root, ["LICENSE", "LICENSE.md", "COPYING", "COPYING.md"])
    if not license_file:
        return fail("license", "Open-source license", 15, "No license file found.", "Add an OSI-approved license.")
    text = safe_read(license_file)
    known = ["MIT License", "Apache License", "BSD", "GNU GENERAL PUBLIC LICENSE", "Mozilla Public License"]
    detail = "License file exists"
    if any(name.lower() in text.lower() for name in known):
        detail = "Recognized open-source license text found"
    return pass_check("license", "Open-source license", 15, detail)


def check_contributing(root: Path) -> CheckResult:
    path = first_existing(root, ["CONTRIBUTING.md", "docs/CONTRIBUTING.md", ".github/CONTRIBUTING.md"])
    if not path:
        return fail(
            "contributing",
            "Contribution guide",
            10,
            "No CONTRIBUTING guide found.",
            "Add contribution setup, branch, test, PR, and issue triage guidance.",
        )
    text = safe_read(path)
    score = 5
    if re.search(r"\b(test|tests|pytest|npm test|ci)\b", text, re.I):
        score += 2
    if re.search(r"\b(issue|pull request|PR|branch)\b", text, re.I):
        score += 2
    if re.search(r"\b(style|format|lint)\b", text, re.I):
        score += 1
    return result("contributing", "Contribution guide", score, 10, f"Found {path.relative_to(root)}", "Document tests, style, and PR review expectations.")


def check_security(root: Path) -> CheckResult:
    path = first_existing(root, ["SECURITY.md", "docs/SECURITY.md", ".github/SECURITY.md"])
    if not path:
        return fail(
            "security",
            "Security policy",
            8,
            "No SECURITY policy found.",
            "Add supported versions and private vulnerability reporting instructions.",
        )
    return pass_check("security", "Security policy", 8, f"Found {path.relative_to(root)}")


def check_code_of_conduct(root: Path) -> CheckResult:
    path = first_existing(root, ["CODE_OF_CONDUCT.md", "docs/CODE_OF_CONDUCT.md", ".github/CODE_OF_CONDUCT.md"])
    if not path:
        return fail(
            "code_of_conduct",
            "Code of conduct",
            5,
            "No code of conduct found.",
            "Add a short conduct policy so contributors know expected behavior.",
        )
    return pass_check("code_of_conduct", "Code of conduct", 5, f"Found {path.relative_to(root)}")


def check_issue_templates(root: Path) -> CheckResult:
    issue_dir = root / ".github" / "ISSUE_TEMPLATE"
    if not issue_dir.exists():
        return fail(
            "issue_templates",
            "Issue templates",
            7,
            "No GitHub issue templates found.",
            "Add bug report and feature request templates under .github/ISSUE_TEMPLATE.",
        )
    templates = [path for path in issue_dir.glob("*") if path.is_file() and path.suffix.lower() in {".md", ".yml", ".yaml"}]
    if len(templates) >= 2:
        return pass_check("issue_templates", "Issue templates", 7, f"Found {len(templates)} issue templates")
    return result(
        "issue_templates",
        "Issue templates",
        4,
        7,
        f"Found {len(templates)} issue template",
        "Add separate templates for bugs and feature requests.",
    )


def check_pull_request_template(root: Path) -> CheckResult:
    path = first_existing(root, [".github/pull_request_template.md", "PULL_REQUEST_TEMPLATE.md"])
    if not path:
        return fail(
            "pull_request_template",
            "Pull request template",
            5,
            "No pull request template found.",
            "Add a PR template with summary, tests, screenshots, and risk notes.",
        )
    return pass_check("pull_request_template", "Pull request template", 5, f"Found {path.relative_to(root)}")


def check_ci(root: Path) -> CheckResult:
    workflow_dir = root / ".github" / "workflows"
    if not workflow_dir.exists():
        return fail("ci", "Continuous integration", 10, "No GitHub Actions workflows found.", "Add CI that runs tests and lint checks.")
    workflows = [path for path in workflow_dir.glob("*") if path.suffix.lower() in {".yml", ".yaml"}]
    if not workflows:
        return fail("ci", "Continuous integration", 10, "Workflow directory is empty.", "Add at least one workflow YAML.")
    content = "\n".join(safe_read(path) for path in workflows)
    points = 5
    if re.search(r"\b(test|pytest|unittest|npm test|go test|cargo test)\b", content, re.I):
        points += 3
    if re.search(r"\b(lint|ruff|eslint|tsc|mypy|check)\b", content, re.I):
        points += 2
    return result("ci", "Continuous integration", points, 10, f"Found {len(workflows)} workflow file(s)", "Run both tests and lint/type checks in CI.")


def check_tests(root: Path) -> CheckResult:
    test_markers = [
        "tests",
        "test",
        "spec",
        "pytest.ini",
        "tox.ini",
        "jest.config.js",
        "vitest.config.ts",
    ]
    found = [marker for marker in test_markers if (root / marker).exists()]
    if found:
        return pass_check("tests", "Tests", 10, f"Found test marker(s): {', '.join(found[:3])}")
    nested_test_dirs = [
        path.relative_to(root).as_posix()
        for path in root.glob("*/tests")
        if path.is_dir()
    ]
    if nested_test_dirs:
        return pass_check("tests", "Tests", 10, f"Found nested test directory: {', '.join(nested_test_dirs[:3])}")
    test_files = list(root.rglob("test_*.py")) + list(root.rglob("*_test.py")) + list(root.rglob("*.test.ts"))
    if test_files:
        return result("tests", "Tests", 7, 10, f"Found {len(test_files)} test-like file(s)", "Group tests under a clear tests/ directory.")
    return fail("tests", "Tests", 10, "No tests found.", "Add smoke tests or unit tests for the primary workflow.")


def check_package_metadata(root: Path) -> CheckResult:
    metadata_files = [
        "pyproject.toml",
        "package.json",
        "Cargo.toml",
        "go.mod",
        "pom.xml",
        "setup.py",
        "requirements.txt",
    ]
    found = [name for name in metadata_files if (root / name).exists()]
    if not found:
        for metadata_file in metadata_files:
            found.extend(path.relative_to(root).as_posix() for path in root.glob(f"*/*/{metadata_file}"))
            found.extend(path.relative_to(root).as_posix() for path in root.glob(f"*/{metadata_file}"))
    if found:
        return pass_check("package_metadata", "Package metadata", 5, f"Found {', '.join(found[:3])}")
    return fail("package_metadata", "Package metadata", 5, "No common package metadata found.", "Add package metadata for your ecosystem.")


def check_release_tags(root: Path) -> CheckResult:
    tags = git_lines(root, ["tag", "--list"])
    if tags:
        return pass_check("release_tags", "Release tags", 5, f"Found {len(tags)} git tag(s)")
    return fail("release_tags", "Release tags", 5, "No git tags found.", "Tag releases such as v0.1.0 so users can track versions.")


def check_recent_activity(root: Path) -> CheckResult:
    commits = git_lines(root, ["log", "--since=90 days ago", "--format=%H"])
    if len(commits) >= 5:
        return pass_check("recent_activity", "Recent maintenance activity", 5, f"Found {len(commits)} commits in the last 90 days")
    if commits:
        return result(
            "recent_activity",
            "Recent maintenance activity",
            3,
            5,
            f"Found {len(commits)} commit(s) in the last 90 days",
            "Keep a visible trail of fixes, docs, tests, and releases.",
        )
    return fail(
        "recent_activity",
        "Recent maintenance activity",
        5,
        "No recent git commits found or this is not a git repository.",
        "Commit real maintenance work before using the repo as evidence.",
    )


def check_secret_hygiene(root: Path) -> CheckResult:
    tracked = tracked_files(root)
    safe_env_examples = {".env.example", "env.example"}
    risky_patterns = [
        re.compile(r"(^|/)\.env($|\.)"),
        re.compile(r"(^|/)(id_rsa|id_dsa|id_ed25519)$"),
        re.compile(r"\.(pem|key|p12)$", re.I),
    ]
    risky = [
        path
        for path in tracked
        if Path(path).name not in safe_env_examples and any(pattern.search(path) for pattern in risky_patterns)
    ]
    if risky:
        return fail(
            "secret_hygiene",
            "Secret hygiene",
            5,
            f"Potential secret files are tracked: {', '.join(risky[:5])}",
            "Remove secrets from git history and keep only safe .env.example files.",
        )
    return pass_check("secret_hygiene", "Secret hygiene", 5, "No obvious tracked secret files found")


def result(
    check_id: str,
    title: str,
    points: int,
    max_points: int,
    detail: str,
    recommendation: str,
) -> CheckResult:
    if points >= max_points:
        status = "pass"
    elif points <= 0:
        status = "fail"
    else:
        status = "partial"
    if status == "pass":
        recommendation = ""
    return CheckResult(
        id=check_id,
        title=title,
        points=points,
        max_points=max_points,
        status=status,
        detail=detail,
        recommendation=recommendation,
    )


def pass_check(check_id: str, title: str, max_points: int, detail: str) -> CheckResult:
    return result(check_id, title, max_points, max_points, detail, "")


def fail(check_id: str, title: str, max_points: int, detail: str, recommendation: str) -> CheckResult:
    return result(check_id, title, 0, max_points, detail, recommendation)


def first_existing(root: Path, candidates: list[str]) -> Path | None:
    for candidate in candidates:
        path = root / candidate
        if path.exists() and path.is_file():
            return path
    return None


def safe_read(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8")
    except UnicodeDecodeError:
        return path.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return ""


def git_lines(root: Path, args: list[str]) -> list[str]:
    try:
        proc = subprocess.run(
            ["git", "-C", str(root), *args],
            check=False,
            stdout=subprocess.PIPE,
            stderr=subprocess.DEVNULL,
            text=True,
        )
    except OSError:
        return []
    if proc.returncode != 0:
        return []
    return [line.strip() for line in proc.stdout.splitlines() if line.strip()]


def tracked_files(root: Path) -> list[str]:
    tracked = git_lines(root, ["ls-files"])
    if tracked:
        return tracked
    files: list[str] = []
    for path in root.rglob("*"):
        if path.is_file() and ".git" not in path.parts:
            files.append(path.relative_to(root).as_posix())
    return files
