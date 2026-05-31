# OSS Readiness Checker

OSS Readiness Checker is a small CLI for maintainers who want to audit whether a repository looks ready for public open-source contribution and maintainer programs.

It checks the basics that reviewers and new contributors look for: README quality, license, contribution guide, security policy, issue templates, PR template, CI, tests, release tags, recent activity, package metadata, and obvious secret hygiene.

## Install

Run from a local checkout:

```bash
git clone https://github.com/cettyTheDev/oss-readiness-checker.git
cd oss-readiness-checker
python -m pip install -e .
```

## Usage

Score the current repository:

```bash
oss-readiness .
```

Generate JSON for automation:

```bash
oss-readiness /path/to/repo --format json
```

Generate Markdown for an issue, PR, or maintenance report:

```bash
oss-readiness /path/to/repo --format markdown > readiness-report.md
```

Fail CI if a repository falls below a threshold:

```bash
oss-readiness . --fail-under 80
```

## Example Output

```text
OSS readiness score: 84/100
Path: /work/project
Checks: 10 passed, 2 partial, 1 failed

[PASS] README: 25/25
[FAIL] Release tags: 0/5
  No git tags found.
  Next: Tag releases such as v0.1.0 so users can track versions.
```

## Checks

- README exists and includes structure, install guidance, usage examples, and maintainer context.
- Open-source license exists.
- Contribution, security, and conduct policies exist.
- GitHub issue and pull request templates exist.
- CI runs tests and quality checks.
- Tests and package metadata are present.
- Git release tags and recent commits show maintenance activity.
- Obvious secret files are not tracked.

## Why This Exists

Open-source maintainers are often evaluated by public signals: project clarity, contribution process, issue triage, release hygiene, and evidence of active maintenance. This tool turns those signals into a quick local report so maintainers can fix gaps before sharing a repository or applying to maintainer support programs.

## Development

```bash
python -m pip install -e .
python -m unittest discover -s tests
python -m oss_readiness . --fail-under 80
```

An example GitHub Actions workflow is available at [docs/ci-workflow.example.yml](docs/ci-workflow.example.yml). Copy it to `.github/workflows/ci.yml` when your repository auth allows workflow file updates.

## Roadmap

- Optional GitHub API enrichment for stars, forks, releases, and issue activity.
- Language-specific checks for Python, Node, Rust, and Go.
- SARIF output for code scanning dashboards.
- GitHub Action wrapper.

## License

MIT
