# Feature Design

This document is for internal development. It describes the intended behavior of
the `train` display.

## API Sketch

The initial API candidate is a context manager.

```python
from trainpit import train

with train(total_epochs=10, total_steps=500, label="experiment-001") as progress:
    for epoch in range(10):
        progress.epoch(epoch + 1)

        for step, batch in enumerate(loader, start=1):
            loss, metrics = train_step(batch)
            progress.step(step, loss=loss, metrics=metrics, lr=0.0001)
```

## State

The `train` display should track:

- `phase`: fixed to `train`
- `label`: experiment or run name
- `current_epoch`
- `total_epochs`
- `current_step`
- `total_steps`
- `loss`
- `metrics`
- `history`
- `learning_rate`
- `event`
- `started_at`
- `updated_at`
- `finished_at`

## Updates

Required update operations:

- `epoch(value)`
- `step(value, loss=None, metrics=None, lr=None)`
- `metrics(values)`
- `event(message)`
- `finish()`
- `fail(error)`

Start with the smallest useful API. Add aliases or helpers later only when they
remove real friction.

## Display Examples

The output should be distinct from `tqdm`. `trainpit` should not use a progress
bar as the primary visual structure or emit `tqdm`-style progress bar log lines.

The initial TTY output may start as one compact line:

```text
train experiment-001 | epoch 2/10 | step 128/500 | loss 0.421 | acc 0.884 | lr 1.0e-4 | 12.4 step/s | elapsed 00:03:12 | eta 00:12:18
```

The intended TTY direction is a compact btop-style dashboard. A future expanded
layout may divide the terminal into sections:

```text
trainpit train  experiment-001
+ progress -----+ metrics --------+ timing --------+
| epoch 2/10    | loss 0.421      | elapsed 00:03 |
| step 128/500  | acc  0.884      | eta     00:12 |
+ curve --------+ events --------------------------+
| loss .:-=+*## | checkpoint saved at step 100     |
+---------------+----------------------------------+
```

Non-TTY output should remain readable as structured log lines. The format should
be searchable and trainpit-specific:

```text
trainpit train label=experiment-001 epoch=2/10 step=128/500 loss=0.421 acc=0.884 lr=1.0e-4 throughput=12.4step/s elapsed=00:03:12 eta=00:12:18
```

Completion example:

```text
trainpit train label=experiment-001 status=finished epoch=10/10 step=500/500 loss=0.183 elapsed=00:16:04
```

Failure example:

```text
trainpit train label=experiment-001 status=failed epoch=2/10 step=128/500 loss=0.421 elapsed=00:03:12
```

## Dashboard UI Direction

The TTY experience should be closer to a terminal monitor than a progress bar.
`btop` is the reference direction: dense, readable, panel-based, and designed for
continuous observation.

The dashboard should prioritize:

- stable panel positions
- clear grouping of progress, metrics, timing, graph, and events
- readable updates without scrolling
- compact layout that still works in smaller terminals
- graceful fallback to the one-line display when space is limited

The dashboard should not require a full-screen alternate buffer for the MVP.
Using an alternate screen can be reconsidered after the core rendering behavior
is stable.

## Progress Behavior

When totals are known, progress may include `current/total`, percent, and ETA.

- `epoch 2/10`
- `step 128/500`
- `25.6%`
- `eta 00:12:18`

When totals are unknown:

- Show `epoch 2`.
- Show `step 128`.
- Do not show percent.
- Do not show ETA.

## Metrics Behavior

Metrics are scalar values.

```python
progress.step(
    step,
    loss=loss,
    metrics={"acc": accuracy, "f1": f1},
)
```

The initial implementation should preserve dictionary order. Handling for
non-numeric values should be decided during implementation.

## Learning Curve Graph Behavior

`trainpit` should support graph-style learning curve display for loss and
selected scalar metrics. The graph is intended for terminal inspection during a
run, not as a replacement for experiment tracking or a dashboard.

The graph display should use metric history collected from `step()` or
`metrics()` updates. It should be able to show:

- loss trend over recent steps
- selected metric trends, such as accuracy
- spikes or regressions
- plateauing behavior

The first graph implementation should be compact and terminal-friendly. Candidate
formats include a sparkline, a small fixed-height text plot, or an optional
expanded view when the terminal has enough space.

Example compact output:

```text
loss 0.842 -> 0.421  .:-=+*##
acc  0.511 -> 0.884  .:--=+*#
```

Graph rendering should follow the same TTY and non-TTY rules as the rest of the
display. TTY output may redraw a graph panel in place. Non-TTY output should
avoid noisy graph spam and may emit periodic summaries instead.

Metric history should be bounded by default so long runs do not grow memory
without limit. The history limit should be configurable once the public API for
graph display is designed.

## Rate Limiting

Rendering should not run more often than the configured interval. State updates
should still happen every time.

- State update: always run.
- Render: run only when the rate limit allows it.
- Finish and fail: always render, regardless of rate limiting.

## Lifecycle

On start:

- Initialize state.
- Select a renderer based on the output stream.
- Record the start time.

On update:

- Update state.
- Render when allowed.

On finish:

- Render the final state.
- Print a newline to close the terminal display.

On exception:

- Render the failed state.
- Print a newline to close the terminal display.
- Re-raise the exception.
