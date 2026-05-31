from __future__ import annotations

import argparse
import sys
from pathlib import Path

from .checks import ReadinessReport, analyze_repository


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="oss-readiness",
        description="Score a repository for open-source maintainer readiness.",
    )
    parser.add_argument("path", nargs="?", default=".", help="Repository path to inspect.")
    parser.add_argument(
        "--format",
        choices=["text", "json", "markdown"],
        default="text",
        help="Output format.",
    )
    parser.add_argument(
        "--fail-under",
        type=int,
        default=None,
        metavar="SCORE",
        help="Exit with status 1 when the score is below SCORE.",
    )
    args = parser.parse_args(argv)

    try:
        report = analyze_repository(Path(args.path))
    except Exception as exc:
        print(f"oss-readiness: {exc}", file=sys.stderr)
        return 2

    if args.format == "json":
        print(report.to_json())
    elif args.format == "markdown":
        print(render_markdown(report))
    else:
        print(render_text(report))

    if args.fail_under is not None and report.score < args.fail_under:
        return 1
    return 0


def render_text(report: ReadinessReport) -> str:
    lines = [
        f"OSS readiness score: {report.score}/100",
        f"Path: {report.path}",
        f"Checks: {report.passed} passed, {report.partial} partial, {report.failed} failed",
        "",
    ]
    for check in report.checks:
        marker = {"pass": "[PASS]", "partial": "[WARN]", "fail": "[FAIL]"}[check.status]
        lines.append(f"{marker} {check.title}: {check.points}/{check.max_points}")
        lines.append(f"  {check.detail}")
        if check.recommendation:
            lines.append(f"  Next: {check.recommendation}")
    return "\n".join(lines)


def render_markdown(report: ReadinessReport) -> str:
    lines = [
        f"# OSS Readiness Report",
        "",
        f"- Score: **{report.score}/100**",
        f"- Path: `{report.path}`",
        f"- Checks: {report.passed} passed, {report.partial} partial, {report.failed} failed",
        "",
        "| Check | Status | Points | Detail |",
        "| --- | --- | ---: | --- |",
    ]
    for check in report.checks:
        detail = check.detail.replace("|", "\\|")
        lines.append(f"| {check.title} | {check.status} | {check.points}/{check.max_points} | {detail} |")
    recommendations = [check for check in report.checks if check.recommendation]
    if recommendations:
        lines.extend(["", "## Recommended Next Steps", ""])
        for check in recommendations:
            lines.append(f"- **{check.title}:** {check.recommendation}")
    return "\n".join(lines)


if __name__ == "__main__":
    raise SystemExit(main())

