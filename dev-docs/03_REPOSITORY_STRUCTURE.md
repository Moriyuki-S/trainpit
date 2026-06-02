# Repository Structure

This document is for internal development. It defines the expected repository
shape after the `train` display implementation lands.

## Current Structure

```text
trainpit/
├── docs/                  # Public documentation
├── dev-docs/              # Internal development documents
├── src/
│   └── trainpit/
│       └── __init__.py
├── tests/
│   └── test_import.py
├── main.py
├── pyproject.toml
├── README.md
└── zensical.toml
```

## Proposed Structure

```text
trainpit/
├── docs/
├── dev-docs/
│   ├── 01_PRD.md
│   ├── 02_DEVELOPMENT_GUIDELINES.md
│   ├── 03_REPOSITORY_STRUCTURE.md
│   ├── 04_FEATURE_DESIGN.md
│   └── 05_ARCHITECTURE_DESIGN.md
├── src/
│   └── trainpit/
│       ├── __init__.py
│       ├── _clock.py
│       ├── _format.py
│       ├── _graph.py
│       ├── _history.py
│       ├── _layout.py
│       ├── _render.py
│       ├── _state.py
│       └── _tracker.py
├── tests/
│   ├── test_import.py
│   ├── test_train_state.py
│   ├── test_train_render.py
│   └── test_train_tracker.py
├── main.py
├── pyproject.toml
├── README.md
└── zensical.toml
```

## Module Responsibilities

`src/trainpit/__init__.py`
: Exports the public API. The initial candidate is `train`.

`src/trainpit/_state.py`
: Stores the state needed for the `train` display, including epoch, step,
metrics, events, and timing data.

`src/trainpit/_tracker.py`
: Implements the public-facing tracker behavior. It coordinates state updates,
render calls, and context manager lifecycle.

`src/trainpit/_render.py`
: Provides TTY and plain text renderers.

`src/trainpit/_format.py`
: Contains formatting helpers for numbers, durations, metrics, and progress.

`src/trainpit/_history.py`
: Stores sampled loss and metric values for learning curve display.

`src/trainpit/_graph.py`
: Converts metric history into terminal-friendly learning curve graphs.

`src/trainpit/_layout.py`
: Describes dashboard-style terminal layout sections for TTY output.

`src/trainpit/_clock.py`
: Abstracts time access. Tests should be able to use a fake clock.

## Public API And Private Modules

External users should import only from `trainpit`. Private modules use the `_`
prefix and are not part of the supported API.

```python
from trainpit import train
```

## docs And dev-docs

- `docs/` is public documentation.
- `dev-docs/` is internal development documentation.
- Do not document unimplemented APIs in `docs/`.
- Keep design notes and open decisions in `dev-docs/`.
