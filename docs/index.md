---
icon: lucide/activity
---

# trainpit

trainpit is a Python package for rich CLI progress monitoring in machine learning training loops.

The project is in early development. The current repository focuses on the package skeleton, test setup, quality checks, distribution builds, and documentation structure.

## Goals

- Make long-running training jobs easier to inspect from a terminal.
- Provide useful progress output for development, debugging, and experiment runs.
- Keep the package simple enough to integrate into existing Python training loops.

## Current status

!!! note "Early development"

    The initial `train` tracker API is available. Terminal rendering is still under development, so behavior-level documentation currently focuses on lifecycle and update calls.

## Requirements

- Python 3.13 or later
- uv

## Quick start

```sh
uv sync --locked --all-extras --dev
uv run pytest
```

After installation, the package can be imported:

```python
from trainpit import train
```

Continue with [Getting started](getting-started.md) for setup details.
See [Tutorial](tutorial.md) for a minimal training loop example.
