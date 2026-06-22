# trainpit

[![Quality](https://github.com/Moriyuki-S/trainpit/actions/workflows/quality.yml/badge.svg)](https://github.com/Moriyuki-S/trainpit/actions/workflows/quality.yml)
[![Pytest Linux](https://github.com/Moriyuki-S/trainpit/actions/workflows/pytest-linux.yml/badge.svg)](https://github.com/Moriyuki-S/trainpit/actions/workflows/pytest-linux.yml)
[![Pytest macOS](https://github.com/Moriyuki-S/trainpit/actions/workflows/pytest-macos.yml/badge.svg)](https://github.com/Moriyuki-S/trainpit/actions/workflows/pytest-macos.yml)
[![Pytest Windows](https://github.com/Moriyuki-S/trainpit/actions/workflows/pytest-windows.yml/badge.svg)](https://github.com/Moriyuki-S/trainpit/actions/workflows/pytest-windows.yml)
[![Coverage](https://github.com/Moriyuki-S/trainpit/actions/workflows/coverage.yml/badge.svg)](https://github.com/Moriyuki-S/trainpit/actions/workflows/coverage.yml)

trainpit is a Python package for rich CLI progress monitoring in machine learning training loops.

The goal is to make long-running training jobs easier to inspect from a terminal, with progress output that is useful during development, debugging, and experiment runs.

## Status

trainpit is in early development. The public `train` tracker API is available,
and the Textual dashboard demo can display progress, metrics, learning curves,
timing, events, custom panels, and configurable graph renderers. Renderer
integration around the public tracker API is still evolving.

## Requirements

- Python 3.13 or later
- uv

## Installation

Install from a local checkout:

```sh
uv sync --locked
```

For development, include the development dependency group:

```sh
uv sync --locked --all-extras --dev
```

Install Git hooks for local quality checks:

```sh
uv run pre-commit install --install-hooks
```

## Usage

Wrap a training loop with the `train` tracker:

```python
from trainpit import train

with train(total_epochs=3, total_steps=5, label="demo-run") as progress:
    for epoch in range(1, 4):
        progress.epoch(epoch)

        for step in range(1, 6):
            loss = 1.0 / (epoch * step)
            progress.step(
                step,
                loss=loss,
                metrics={"acc": step / 5},
                learning_rate=0.0001,
            )
```

See the documentation tutorial for a fuller walkthrough.

A runnable notebook version is available at `examples/train_tutorial.ipynb`.

To run a small PyTorch neural network example:

```sh
uv run --group examples python examples/torch_nn.py
```

This opens the Textual dashboard and updates progress, metrics, and learning
curves while the model trains. Press `q` to close the dashboard after inspecting
the final state.

For non-interactive output:

```sh
uv run --group examples python examples/torch_nn.py --plain
```

To preview the Textual dashboard demo:

```sh
uv run python examples/textual_dashboard.py
```

To preview user-defined dashboard panels:

```sh
uv run python examples/custom_panels.py
```

## Development

Run the test suite:

```sh
uv run pytest
```

Run tests with coverage:

```sh
uv run pytest --cov=trainpit --cov-report=term-missing --cov-report=xml
```

Run the configured pre-commit checks manually:

```sh
uv run pre-commit run --all-files
uv run pre-commit run --hook-stage pre-push --all-files
```

Check formatting:

```sh
uv run ruff format --check .
```

Run lint checks:

```sh
uv run ruff check .
```

Build distribution artifacts:

```sh
uv build
```

Before opening a pull request, run:

```sh
uv lock --check
uv run ruff format --check .
uv run ruff check .
uv run pytest
uv run pytest --cov=trainpit --cov-report=term-missing --cov-report=xml
uv build
```

## CI

GitHub Actions checks the following:

- lockfile validation
- formatting and linting with ruff
- Python file compilation
- package build
- wheel installation in a temporary environment
- pytest on Linux, macOS, and Windows
- coverage on Linux with `coverage.xml` uploaded as an artifact

Dependabot is configured for GitHub Actions, uv, and devcontainer updates.

## Contributing

Issues and pull requests are welcome while the project is taking shape.

For code changes, please keep the scope focused and include tests when the change affects behavior. For larger changes, open an issue first so the approach can be discussed before implementation.

## License

No license file has been added yet.
