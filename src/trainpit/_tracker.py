"""Public train tracker entry point implementation."""

from __future__ import annotations

from collections.abc import Mapping
from types import TracebackType
from typing import Self

from trainpit._state import Scalar, TrainState


class TrainTracker:
    """Context manager used to update one train progress display."""

    def __init__(
        self,
        *,
        total_epochs: int | None = None,
        total_steps: int | None = None,
        label: str | None = None,
    ) -> None:
        self._state = TrainState(
            label=label,
            total_epochs=_optional_positive_integer("total_epochs", total_epochs),
            total_steps=_optional_positive_integer("total_steps", total_steps),
        )

    @property
    def snapshot(self) -> TrainState:
        """Return a copy of the current progress state."""

        return self._state.model_copy(deep=True)

    def __enter__(self) -> Self:
        self.start()
        return self

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc: BaseException | None,
        traceback: TracebackType | None,
    ) -> bool:
        del exc_type, traceback

        if exc is None:
            self.finish()
        else:
            self.fail(exc)

        return False

    def epoch(self, value: int) -> None:
        self._state.set_epoch(value)

    def start(self) -> None:
        self._state.start()

    def step(
        self,
        value: int,
        *,
        loss: Scalar | None = None,
        metrics: Mapping[str, Scalar] | None = None,
        learning_rate: Scalar | None = None,
        lr: Scalar | None = None,
    ) -> None:
        self._state.set_step(
            value,
            loss=loss,
            metrics=metrics,
            learning_rate=_resolve_learning_rate(learning_rate, lr),
        )

    def update_metrics(self, values: Mapping[str, Scalar]) -> None:
        self._state.set_metrics(values)

    def metrics(self, values: Mapping[str, Scalar]) -> None:
        self.update_metrics(values)

    def log(self, message: str) -> None:
        self._state.set_event(message)

    def event(self, message: str) -> None:
        self.log(message)

    def finish(self) -> None:
        self._state.finish()

    def fail(self, error: BaseException) -> None:
        self._state.fail(error)


def train(
    *,
    total_epochs: int | None = None,
    total_steps: int | None = None,
    label: str | None = None,
) -> TrainTracker:
    """Create a tracker for one training loop."""

    return TrainTracker(
        total_epochs=total_epochs,
        total_steps=total_steps,
        label=label,
    )


def _optional_positive_integer(name: str, value: int | None) -> int | None:
    if value is None:
        return None
    if isinstance(value, bool) or not isinstance(value, int):
        raise TypeError(f"{name} must be an integer")
    if value < 1:
        raise ValueError(f"{name} must be greater than or equal to 1")
    return value


def _resolve_learning_rate(
    learning_rate: Scalar | None,
    lr: Scalar | None,
) -> Scalar | None:
    if learning_rate is not None and lr is not None:
        raise ValueError("Use either learning_rate or lr, not both")

    return learning_rate if learning_rate is not None else lr
