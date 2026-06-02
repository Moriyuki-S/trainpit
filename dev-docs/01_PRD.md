# Train Display PRD

This document is for internal development. It defines what to build for the first
`train` display in `trainpit`, why it exists, and what belongs in the initial
scope.

## Background

Machine learning training loops can run for a long time, and it is often hard to
inspect current progress and recent metrics from the terminal. Plain `print`
calls and simple progress bars do not consistently show epoch, step, loss,
accuracy, learning rate, throughput, and ETA in one readable format.

`trainpit` should provide CLI progress monitoring that is easy to add to a
training loop and useful while a run is active.

The output should be intentionally different from `tqdm`. `trainpit` should not
look like a single progress bar with metrics appended to it. The target
experience is closer to a compact terminal monitor, similar in spirit to `btop`,
where progress, metrics, learning curves, timing, and events are separate pieces
of a structured view.

Latest scalar values are useful, but they do not show whether training is
improving, plateauing, or diverging. `trainpit` should also support a learning
curve graph display so users can inspect the trend of loss and selected metrics
without opening a separate dashboard.

## What To Build

The first development target is the `train` display for the training phase.

- A small API that training loops can use to update progress and metrics
- State for the current `train` display
- A TTY renderer that can evolve into a compact dashboard-like terminal UI
- A plain text renderer with a trainpit-specific log format
- A planned learning curve graph display for loss and selected scalar metrics
- Rate limiting for render frequency
- Lifecycle behavior that leaves the final state on completion or failure
- Tests for state, rendering, and lifecycle behavior

## Users

The primary users are developers writing machine learning training loops in
Python.

- They want to inspect progress and metrics during local experiments.
- They want readable logs in CI or remote execution environments.
- They want to add monitoring without restructuring the training loop.

## Goals

- Make it obvious that the active phase is `train`.
- Show epoch and step progress.
- Show the latest loss and scalar metrics.
- Show learning curve trends for loss and selected scalar metrics.
- Show elapsed time, throughput, and ETA when the data is available.
- Keep both TTY and non-TTY output readable.
- Make the output visually and semantically distinct from `tqdm`.
- Prefer a compact terminal dashboard direction over a progress-bar-only design.
- Avoid adding meaningful overhead to the training loop.

## Non-Goals

The initial implementation will not include:

- Integrated validation or test phase displays
- Multiple concurrent training job displays
- Distributed training output by rank
- A web dashboard UI
- Metrics persistence
- Framework-specific adapters for PyTorch, TensorFlow, or similar libraries

## Output Direction

`trainpit` should use two related output modes.

TTY mode should aim for a compact terminal dashboard. The design can start with a
small text layout, but it should leave room for btop-style panels such as:

- run status
- epoch and step progress
- current metrics
- learning curve graph
- timing and throughput
- recent events

Non-TTY mode should use readable structured log lines. It should not mimic
`tqdm` progress bar logs such as `100%|...|`. Each line should identify
`trainpit`, the phase, and the changed state so CI logs remain searchable.

## Planned Learning Curve Feature

The learning curve display should render graph-style trends for training loss and
selected metrics. The first version should target terminal output, not a web
dashboard.

The graph display should help users answer:

- Is training loss decreasing?
- Are metrics improving or plateauing?
- Did a recent update cause a spike or regression?
- Is the run still worth continuing?

The MVP does not need to render the graph immediately, but the state model should
not prevent adding metric history and graph rendering later.

## MVP Requirements

The MVP should focus on one process and one terminal.

- Start, update, and finish a `train` display.
- Update epoch and step progress.
- Update loss, metrics, learning rate, and events.
- Render in place when the output stream is a TTY.
- Avoid terminal control sequences when the output stream is not a TTY.
- Avoid percent and ETA output when totals are unknown.
- On exceptions, render the last known state before re-raising the exception.

## Success Criteria

- A minimal README-ready usage example is implemented.
- `uv run pytest` passes.
- TTY and non-TTY output behavior is covered by tests.
- The API is small and natural to insert into a training loop.
- The API behavior is stable enough to document publicly.

## Open Decisions

- Whether the public API should be a context manager, a tracker object, or both.
- Whether to start with the standard library only or add a terminal rendering
  dependency.
- Whether metric order should be caller-defined or update-order based.
- Numeric formatting rules for loss, learning rate, throughput, and metrics.
- Whether checkpoint and other events need a dedicated API.
