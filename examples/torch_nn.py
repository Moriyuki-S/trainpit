"""Train a small PyTorch neural network with trainpit progress updates."""

from __future__ import annotations

import argparse
from collections.abc import Iterator, Sequence
from typing import TypedDict

import torch
from torch import Tensor, nn

from trainpit import train
from trainpit.tui import TrainDashboardApp, TrainDashboardSnapshot


RUN_LABEL = "torch-nn-demo"


class HistoryRow(TypedDict):
    """One recorded training update."""

    epoch: int
    step: int
    loss: float
    acc: float
    lr: float


def make_dataset(samples: int, *, seed: int) -> tuple[Tensor, Tensor]:
    """Create a deterministic binary classification dataset."""

    generator = torch.Generator().manual_seed(seed)
    features = torch.randn(samples, 2, generator=generator)
    logits = features[:, 0] + 0.75 * features[:, 1]
    targets = (logits > 0).long()
    return features, targets


def make_model(*, seed: int) -> nn.Module:
    """Create a small MLP classifier."""

    torch.manual_seed(seed)
    return nn.Sequential(
        nn.Linear(2, 16),
        nn.Tanh(),
        nn.Linear(16, 2),
    )


def batch_starts(samples: int, batch_size: int) -> list[int]:
    """Return starting indexes for fixed-size batches."""

    return list(range(0, samples, batch_size))


def accuracy(logits: Tensor, targets: Tensor) -> float:
    """Calculate classification accuracy."""

    predictions = logits.argmax(dim=1)
    return float((predictions == targets).float().mean().item())


def train_batch(
    *,
    model: nn.Module,
    optimizer: torch.optim.Optimizer,
    criterion: nn.Module,
    features: Tensor,
    targets: Tensor,
) -> tuple[float, float, float]:
    """Run one optimizer step and return loss, accuracy, and learning rate."""

    optimizer.zero_grad()
    logits = model(features)
    loss = criterion(logits, targets)
    loss.backward()
    optimizer.step()

    learning_rate = float(optimizer.param_groups[0]["lr"])
    return float(loss.item()), accuracy(logits, targets), learning_rate


def iter_training(
    *,
    epochs: int,
    samples: int,
    batch_size: int,
    seed: int,
    snapshot: TrainDashboardSnapshot | None = None,
) -> Iterator[HistoryRow]:
    """Yield one row per batch while updating trainpit progress state."""

    features, targets = make_dataset(samples, seed=seed)
    model = make_model(seed=seed)
    criterion = nn.CrossEntropyLoss()
    optimizer = torch.optim.SGD(model.parameters(), lr=0.2)
    starts = batch_starts(samples, batch_size)

    progress = train(total_epochs=epochs, total_steps=len(starts), label=RUN_LABEL)
    progress.start()

    if snapshot is not None:
        snapshot.event = "training started"

    try:
        for epoch in range(1, epochs + 1):
            progress.epoch(epoch)
            if snapshot is not None:
                snapshot.current_epoch = epoch

            for step, start in enumerate(starts, start=1):
                end = min(start + batch_size, samples)
                loss, acc, lr = train_batch(
                    model=model,
                    optimizer=optimizer,
                    criterion=criterion,
                    features=features[start:end],
                    targets=targets[start:end],
                )

                progress.step(
                    step,
                    loss=loss,
                    metrics={"acc": acc},
                    learning_rate=lr,
                )
                if snapshot is not None:
                    snapshot.update_step(
                        step,
                        loss=loss,
                        metrics={"acc": acc},
                        learning_rate=lr,
                    )
                    snapshot.event = f"epoch {epoch} step {step}/{len(starts)}"

                yield {
                    "epoch": epoch,
                    "step": step,
                    "loss": loss,
                    "acc": acc,
                    "lr": lr,
                }

            progress.log(f"epoch {epoch} complete")
            if snapshot is not None:
                snapshot.event = f"epoch {epoch} complete"

    except BaseException as error:
        progress.fail(error)
        if snapshot is not None:
            snapshot.status = "failed"
            snapshot.event = str(error)
        raise

    progress.finish()
    if snapshot is not None:
        snapshot.status = "finished"
        snapshot.event = "training complete"


class TorchNNDashboardApp(TrainDashboardApp):
    """Textual dashboard that advances the PyTorch example one batch at a time."""

    def __init__(
        self,
        *,
        epochs: int,
        samples: int,
        batch_size: int,
        seed: int,
        interval: float,
    ) -> None:
        snapshot = TrainDashboardSnapshot(
            label=RUN_LABEL,
            total_epochs=epochs,
            total_steps=len(batch_starts(samples, batch_size)),
            event="training ready",
        )
        super().__init__(snapshot)
        self._interval = interval
        self._steps = iter_training(
            epochs=epochs,
            samples=samples,
            batch_size=batch_size,
            seed=seed,
            snapshot=self.snapshot,
        )
        self.history: list[HistoryRow] = []

    def on_mount(self) -> None:
        super().on_mount()
        self.set_interval(self._interval, self._advance_training)

    def _advance_training(self) -> None:
        if self.snapshot.status != "running":
            return

        try:
            self.history.append(next(self._steps))
        except StopIteration:
            self.refresh_dashboard()
            return
        except Exception:
            self.refresh_dashboard()
            raise

        self.refresh_dashboard()


def run_training(
    *,
    epochs: int = 5,
    samples: int = 256,
    batch_size: int = 32,
    seed: int = 7,
) -> list[HistoryRow]:
    """Train the demo model and return per-batch training history."""

    return list(
        iter_training(
            epochs=epochs,
            samples=samples,
            batch_size=batch_size,
            seed=seed,
        )
    )


def print_summary(history: Sequence[HistoryRow]) -> None:
    """Print a compact training summary."""

    first = history[0]
    final = history[-1]

    print(f"Recorded {len(history)} training updates")
    print(f"Initial loss: {first['loss']:.4f}")
    print(f"Final loss:   {final['loss']:.4f}")
    print(f"Final acc:    {final['acc']:.4f}")


def parse_args() -> argparse.Namespace:
    """Parse command-line arguments."""

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--epochs", type=int, default=100)
    parser.add_argument("--samples", type=int, default=256)
    parser.add_argument("--batch-size", type=int, default=32)
    parser.add_argument("--seed", type=int, default=7)
    parser.add_argument(
        "--interval",
        type=float,
        default=0.08,
        help="Dashboard update interval in seconds.",
    )
    parser.add_argument(
        "--plain",
        action="store_true",
        help="Run without the Textual dashboard and print a summary.",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    if args.plain:
        history = run_training(
            epochs=args.epochs,
            samples=args.samples,
            batch_size=args.batch_size,
            seed=args.seed,
        )
        print_summary(history)
        return

    TorchNNDashboardApp(
        epochs=args.epochs,
        samples=args.samples,
        batch_size=args.batch_size,
        seed=args.seed,
        interval=args.interval,
    ).run()


if __name__ == "__main__":
    main()
