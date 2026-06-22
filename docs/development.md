---
icon: lucide/wrench
---

# Development

trainpit uses Python 3.13, uv, pytest, ruff, pre-commit, and zensical.

## Setup

```sh
uv sync --locked --all-extras --dev
```

Install the local Git hooks:

```sh
uv run pre-commit install --install-hooks
```

The configured hooks run ruff and lockfile checks before commits. The slower
pytest and documentation build checks run before pushes.

You can also run them manually:

```sh
uv run pre-commit run --all-files
uv run pre-commit run --hook-stage pre-push --all-files
```

## Test

```sh
uv run pytest
```

Run tests with coverage and write `coverage.xml`:

```sh
uv run pytest --cov=trainpit --cov-report=term-missing --cov-report=xml
```

## Format and Lint

Check formatting:

```sh
uv run ruff format --check .
```

Run lint checks:

```sh
uv run ruff check .
```

## Build

```sh
uv build
```

## Documentation

Build the documentation site:

```sh
uv run zensical build
```

Preview it locally:

```sh
uv run zensical serve --dev-addr 0.0.0.0:8010
```

In a dev container, open the forwarded port at
`http://localhost:8010/trainpit/`.

If the browser shows `{"detail":"Not Found"}`, the request is probably reaching
another service on the same port. Stop that service or switch `8010` to another
free port in both the command and `.devcontainer/devcontainer.json`.

## Pull Request Checklist

- Keep the change focused.
- Add or update tests when behavior changes.
- Run the test and quality commands before opening a pull request.
- Avoid documenting APIs that are not implemented yet.
