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
uv run zensical serve
```

## Pull Request Checklist

- Keep the change focused.
- Add or update tests when behavior changes.
- Run the test and quality commands before opening a pull request.
- Avoid documenting APIs that are not implemented yet.
