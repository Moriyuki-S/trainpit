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

## Publish

PyPI publishing is handled by the `Publish` GitHub Actions workflow. It runs when
the repository's `develop` branch is merged into `main` with a pull request. The
workflow reads the version from `pyproject.toml`, creates a GitHub release tagged
as `v<version>`, builds the source distribution and wheel with `uv build`, and
uploads the artifacts to PyPI with Trusted Publishing.

If a release for that version already exists, the workflow skips publishing so
the same package version is not uploaded twice. Publishing a GitHub release
manually also triggers the PyPI upload path.

Before the first release, configure a PyPI Trusted Publisher with:

- owner: `Moriyuki-S`
- repository: `trainpit`
- workflow: `publish.yml`
- environment: `pypi`

Before merging `develop` into `main`, update `project.version` in
`pyproject.toml` to the next release version.

trainpit is distributed under the MIT License.

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
