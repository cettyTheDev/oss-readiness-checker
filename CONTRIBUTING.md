# Contributing

Thanks for helping improve OSS Readiness Checker.

## Development Setup

```bash
python -m venv .venv
. .venv/bin/activate
python -m pip install -e .
```

## Tests

```bash
python -m unittest discover -s tests
python -m oss_readiness . --fail-under 80
```

## Pull Requests

- Open an issue before large scoring changes.
- Keep checks deterministic and dependency-free unless there is a clear reason.
- Include tests for every new check.
- Run lint or formatting checks before opening a pull request.
- Update the README when changing CLI behavior.

## Maintainer Notes

The project is designed for repository triage and open-source readiness reviews. Good issues include false positives, missing ecosystem checks, and output formats that help maintainers prepare public project evidence.
