---
icon: lucide/git-pull-request
---

# CI

GitHub Actions validates code quality, packaging, and cross-platform test behavior.

## Quality

The quality workflow runs on Ubuntu and checks:

- lockfile consistency with `uv lock --check`
- dependency installation with `uv sync --locked --all-extras --dev`
- formatting with `ruff format --check`
- linting with `ruff check`
- Python compilation with `compileall`
- package builds with `uv build`
- wheel installation in a temporary environment

## Tests

pytest runs on:

- Linux
- macOS
- Windows

Each test job installs the locked development environment and runs:

```sh
uv run pytest
```

## Coverage

The coverage workflow runs on Ubuntu and writes both terminal output and
`coverage.xml`:

```sh
uv run pytest --cov=trainpit --cov-report=term-missing --cov-report=xml
```

The workflow uploads `coverage.xml` as a GitHub Actions artifact named
`coverage-xml`.

## Dependency Updates

Dependabot is configured for:

- GitHub Actions
- uv
- devcontainers
