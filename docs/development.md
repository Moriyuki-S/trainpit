---
icon: lucide/wrench
---

# Development

trainpit uses Python 3.13, uv, pytest, and ruff.

## Setup

```sh
uv sync --locked --all-extras --dev
```

## Test

```sh
uv run pytest
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
