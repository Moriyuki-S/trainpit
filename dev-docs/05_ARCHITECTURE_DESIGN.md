# Architecture Design

This document is for internal development. It defines the internal structure and
responsibility boundaries for the `train` display.

## Overview

```text
training loop
    |
    v
trainpit.train(...)
    |
    v
TrainTracker
    |
    +--> TrainState
    |
    +--> MetricHistory
    |
    +--> Clock
    |
    +--> RateLimiter
    |
    +--> Renderer
            |
            +--> TtyRenderer
            |
            +--> DashboardRenderer
            |
            +--> PlainRenderer
            |
            +--> GraphRenderer
```

## Components

### TrainTracker

The public API implementation used by the training loop.

- Manage context manager lifecycle.
- Update state.
- Call the renderer.
- Guarantee final output on finish or failure.

### TrainState

The current values needed by the display.

- Focus on storing values.
- Do not depend on output streams.
- Do not depend on rendering.
- Stay close to pure data so tests remain simple.

### MetricHistory

Bounded time series data used by the learning curve graph display.

- Store sampled loss and selected scalar metrics.
- Preserve enough history to show useful trends.
- Bound memory use for long runs.
- Stay independent of terminal rendering.

### Clock

The source of time.

- Use monotonic time in production.
- Use a fake clock in tests.
- Keep elapsed, throughput, and ETA calculations deterministic in tests.

### RateLimiter

Controls render frequency.

- Prevent high-frequency training loops from rendering too often.
- Never block state updates.
- Always allow finish and failure renders.

### Renderer

Converts state into output.

- Use separate implementations for TTY and non-TTY output.
- Do not own state update logic.
- Move shared formatting into `_format.py`.

### DashboardRenderer

Owns the btop-style TTY dashboard direction.

- Compose progress, metrics, timing, graph, and events into stable sections.
- Fall back to compact one-line output when the terminal is too small.
- Avoid `tqdm`-style progress bar semantics as the primary UI.
- Keep layout decisions separate from state update logic.

### GraphRenderer

Converts metric history into a terminal-friendly learning curve graph.

- Render compact trends for loss and selected metrics.
- Avoid excessive output in non-TTY mode.
- Share rate limiting with the main display.
- Keep graph layout optional so the basic one-line display remains usable.

## Data Flow

1. The user starts `train(...)`.
2. `TrainTracker` initializes `TrainState`.
3. The output stream `isatty()` result selects the renderer.
4. The user calls `epoch()` or `step()`.
5. `TrainTracker` updates `TrainState`.
6. Metric values are appended to `MetricHistory` when graphing is enabled.
7. `RateLimiter` decides whether rendering should run.
8. `Renderer` writes the current state and optional graph output.
9. On finish or exception, the final state is rendered.

## Module Boundaries

`_tracker.py`
: Orchestration close to the public API. Connects state, clock, renderer, and
rate limiter.

`_state.py`
: State definitions and minimal state update logic.

`_history.py`
: Bounded metric history for learning curve display.

`_render.py`
: TTY and plain text renderers. Owns writing to output streams.

`_layout.py`
: Terminal dashboard layout sections and sizing decisions.

`_graph.py`
: Terminal-friendly graph rendering for learning curves.

`_format.py`
: String formatting for numbers, durations, progress, and metrics.

`_clock.py`
: Monotonic clock and fake clock abstraction.

## Dependency Policy

Start with the Python standard library.

Add an external dependency only when:

- terminal rendering becomes too complex,
- cross-platform terminal control is unstable with the standard library, or
- the dependency clearly simplifies the API or implementation.

## Testing Architecture

Tests should inject output streams and clocks.

- Use fake streams to control `isatty()`.
- Use fake clocks to fix elapsed time, throughput, and ETA.
- Verify renderers through strings or captured stream output.
- Verify lifecycle behavior for normal completion and exception paths.

## Implementation Risks

- TTY control can vary by OS and terminal.
- Rendering too frequently can slow the training loop.
- Keeping full metric history can grow memory during long runs.
- Dashboard layout can become hard to maintain if layout and state logic mix.
- Publishing the API too early can make later changes painful.
- Ambiguous metric types or ordering can confuse users.

## Risk Mitigation

- Implement the non-TTY renderer first to stabilize behavior.
- Keep the TTY renderer minimal at first.
- Keep metric history bounded by default.
- Keep dashboard layout logic isolated from state and tracking logic.
- Keep the public API small.
- Do not publish unimplemented or undecided behavior in public docs.
