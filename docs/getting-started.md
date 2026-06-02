---
icon: lucide/play
---

# Getting Started

This page covers the current installation and smoke-test flow for trainpit.

## Install

Clone the repository and install the locked dependencies:

```sh
uv sync --locked
```

For development, include the development dependency group:

```sh
uv sync --locked --all-extras --dev
```

## Import Check

The public API is still being designed. For now, verify that the package imports correctly:

```python
import trainpit

assert trainpit.__name__ == "trainpit"
```

## Build Artifacts

Build the source distribution and wheel:

```sh
uv build
```

The CI also installs the built wheel into a temporary environment to catch packaging issues that source-tree tests may miss.
