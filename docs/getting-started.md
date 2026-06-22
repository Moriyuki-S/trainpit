---
icon: lucide/play
---

# Getting Started

This page covers the current installation and smoke-test flow for trainpit.

## Install

Install the latest published release:

```sh
pip install trainpit
```

In a uv-managed project:

```sh
uv add trainpit
```

Or install into the active virtual environment with uv:

```sh
uv pip install trainpit
```

For local development, clone the repository and install the locked dependencies:

```sh
uv sync --locked
```

For development, include the development dependency group:

```sh
uv sync --locked --all-extras --dev
```

## API Check

Verify that the package exposes the `train` tracker API:

```python
from trainpit import train

with train(total_epochs=1, total_steps=1, label="smoke-test") as progress:
    progress.epoch(1)
    progress.step(1, loss=0.5, metrics={"acc": 1.0}, learning_rate=0.0001)
```

Continue with [Tutorial](tutorial.md) for a fuller example.

## Build Artifacts

Build the source distribution and wheel:

```sh
uv build
```

The CI also installs the built wheel into a temporary environment to catch packaging issues that source-tree tests may miss.
