---
icon: lucide/activity
---

# trainpit

trainpit is a Python package for rich CLI progress monitoring in machine
learning training loops.

The project is in early development, but the core tracker API and a Textual
dashboard demo are available. The dashboard shows progress, scalar metrics,
learning curves, timing, and events while a training loop runs.

## Goals

- Make long-running training jobs easier to inspect from a terminal.
- Provide useful progress output for development, debugging, and experiment runs.
- Keep the package simple enough to integrate into existing Python training loops.

## Current status

!!! note "Early development"

    The public `train` tracker API is available. The Textual dashboard is also
    available for examples and direct use through `trainpit.tui`, while the
    renderer integration around the public tracker API is still evolving.

Available dashboard features include:

- progress bars for epoch and step
- latest loss, metrics, and learning rate
- terminal learning curves for loss and scalar metrics
- timing values for elapsed time, throughput, ETA, and last update age
- user-defined dashboard panels
- configurable graph renderers such as line and scatter plots

## Requirements

- Python 3.11 or later
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
See [Tutorial](tutorial.md) for a minimal training loop example and dashboard
customization details.
