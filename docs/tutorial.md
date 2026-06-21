---
icon: lucide/book-open
---

# Tutorial

This tutorial shows how to add the current `train` API to a small training loop.
The repository also includes a runnable notebook at
`examples/train_tutorial.ipynb`.

To preview the Textual dashboard demo, run:

```sh
uv run python examples/textual_dashboard.py
```

To run the PyTorch neural network example, install the example dependency group:

```sh
uv run --group examples python examples/torch_nn.py
```

This opens a Textual dashboard that updates while the model trains. Press `q` to
close the dashboard. Use `--plain` for non-interactive output:

```sh
uv run --group examples python examples/torch_nn.py --plain
```

!!! note "Current implementation"

    The public tracker API is available now. Terminal rendering is still under
    development, so this tutorial focuses on integrating the lifecycle and update
    calls that renderers will consume.

## Basic Training Loop

Import `train` from `trainpit` and wrap the training loop in a context manager:

```python
from trainpit import train


def run_training() -> None:
    with train(total_epochs=3, total_steps=5, label="demo-run") as progress:
        for epoch in range(1, 4):
            progress.epoch(epoch)

            for step in range(1, 6):
                loss = 1.0 / (epoch * step)
                accuracy = step / 5

                progress.step(
                    step,
                    loss=loss,
                    metrics={"acc": accuracy},
                    learning_rate=0.0001,
                )

        progress.log("training complete")
```

The context manager records normal completion automatically when the block exits.

## Updating Progress

Use `epoch()` when the training loop moves to a new epoch:

```python
progress.epoch(2)
```

Use `step()` for batch or step-level updates:

```python
progress.step(
    128,
    loss=0.421,
    metrics={"acc": 0.884, "f1": 0.76},
    learning_rate=0.0001,
)
```

Use `update_metrics()` when metrics are updated separately from a step:

```python
progress.update_metrics({"acc": 0.891})
```

Use `log()` for notable training events:

```python
progress.log("checkpoint saved")
```

## Exception Handling

If the training loop raises an exception, the tracker records failure and then
lets the original exception propagate:

```python
from trainpit import train


def run_training() -> None:
    with train(total_epochs=3, total_steps=5, label="demo-run") as progress:
        progress.epoch(1)
        progress.step(1, loss=0.9)

        raise RuntimeError("training failed")
```

This keeps trainpit from hiding errors raised by the user's training code.

## Manual Lifecycle

The tracker can also be used without a context manager:

```python
from trainpit import train

progress = train(total_steps=5, label="manual-run")
progress.epoch(1)
progress.step(1, loss=0.9)
progress.finish()
```

For most training loops, prefer the context manager because it handles normal and
exceptional exits automatically.
