"""Internal state for train progress tracking."""

from __future__ import annotations

from collections.abc import Mapping
from time import monotonic
from typing import Annotated, Literal

from pydantic import BaseModel, ConfigDict, Field

Scalar = float | int
DisplayText = Annotated[str, Field(strict=True, min_length=1)]
FiniteFloat = Annotated[float, Field(strict=True, allow_inf_nan=False)]
NonNegativeFiniteFloat = Annotated[
    float,
    Field(strict=True, ge=0, allow_inf_nan=False),
]
PositiveInt = Annotated[int, Field(strict=True, ge=1)]
TrainPhase = Literal["train"]


class TrainState(BaseModel):
    """Current state for one train display."""

    model_config = ConfigDict(
        arbitrary_types_allowed=True,
        extra="forbid",
        strict=True,
        validate_assignment=True,
        validate_default=True,
    )

    label: DisplayText | None = Field(
        default=None,
        description="Human-readable label for the training run.",
    )
    total_epochs: PositiveInt | None = Field(
        default=None,
        description="Total epoch count when known.",
    )
    total_steps: PositiveInt | None = Field(
        default=None,
        description="Total step count per epoch when known.",
    )
    phase: TrainPhase = Field(
        default="train",
        description="Current lifecycle phase for the tracker.",
    )
    current_epoch: PositiveInt | None = Field(
        default=None,
        description="Current one-based epoch index.",
    )
    current_step: PositiveInt | None = Field(
        default=None,
        description="Current one-based step index within the active epoch.",
    )
    loss: FiniteFloat | None = Field(
        default=None,
        description="Latest finite loss value.",
    )
    metrics: dict[DisplayText, FiniteFloat] = Field(
        default_factory=dict,
        description="Latest finite scalar metrics keyed by metric name.",
    )
    learning_rate: NonNegativeFiniteFloat | None = Field(
        default=None,
        description="Latest non-negative learning rate.",
    )
    event: DisplayText | None = Field(
        default=None,
        description="Latest event message.",
    )
    started_at: NonNegativeFiniteFloat | None = Field(
        default=None,
        description="Monotonic timestamp when progress tracking started.",
    )
    updated_at: NonNegativeFiniteFloat | None = Field(
        default=None,
        description="Monotonic timestamp for the latest state update.",
    )
    finished_at: NonNegativeFiniteFloat | None = Field(
        default=None,
        description="Monotonic timestamp when progress tracking ended.",
    )
    started: bool = Field(
        default=False,
        description="Whether progress tracking has started.",
    )
    finished: bool = Field(
        default=False,
        description="Whether progress tracking has reached a terminal state.",
    )
    failed: bool = Field(
        default=False,
        description="Whether progress tracking ended with an error.",
    )
    error: BaseException | None = Field(
        default=None,
        description="Error captured when progress tracking fails.",
    )

    def start(self, *, now: Scalar | None = None) -> None:
        timestamp = _resolve_timestamp(now)
        self.started = True
        self.finished = False
        self.failed = False
        self.error = None
        self.started_at = timestamp
        self.updated_at = timestamp
        self.finished_at = None

    def set_epoch(self, value: int, *, now: Scalar | None = None) -> None:
        self.current_epoch = _require_positive_integer("epoch", value)
        self._touch(_resolve_timestamp(now))

    def set_step(
        self,
        value: int,
        *,
        loss: Scalar | None = None,
        metrics: Mapping[str, Scalar] | None = None,
        learning_rate: Scalar | None = None,
        now: Scalar | None = None,
    ) -> None:
        self.current_step = _require_positive_integer("step", value)

        if loss is not None:
            self.loss = _coerce_scalar("loss", loss)
        if metrics is not None:
            self.metrics = {**self.metrics, **_coerce_metrics(metrics)}
        if learning_rate is not None:
            self.learning_rate = _coerce_scalar("learning_rate", learning_rate)

        self._touch(_resolve_timestamp(now))

    def set_metrics(
        self,
        values: Mapping[str, Scalar],
        *,
        now: Scalar | None = None,
    ) -> None:
        self.metrics = {**self.metrics, **_coerce_metrics(values)}
        self._touch(_resolve_timestamp(now))

    def set_event(self, message: str, *, now: Scalar | None = None) -> None:
        self.event = message
        self._touch(_resolve_timestamp(now))

    def finish(self, *, now: Scalar | None = None) -> None:
        timestamp = _resolve_timestamp(now)
        self._touch(timestamp)
        self.finished = True
        self.failed = False
        self.error = None
        self.finished_at = timestamp

    def fail(self, error: BaseException, *, now: Scalar | None = None) -> None:
        timestamp = _resolve_timestamp(now)
        self._touch(timestamp)
        self.finished = True
        self.failed = True
        self.error = error
        self.finished_at = timestamp

    def _touch(self, timestamp: float) -> None:
        if self.started_at is None:
            self.started_at = timestamp
        self.updated_at = timestamp


def _require_positive_integer(name: str, value: int) -> int:
    if isinstance(value, bool) or not isinstance(value, int):
        raise TypeError(f"{name} must be an integer")
    if value < 1:
        raise ValueError(f"{name} must be greater than or equal to 1")
    return value


def _coerce_scalar(name: str, value: Scalar) -> float:
    if isinstance(value, bool) or not isinstance(value, int | float):
        raise TypeError(f"{name} must be a finite scalar")

    return float(value)


def _resolve_timestamp(value: Scalar | None) -> float:
    timestamp = monotonic() if value is None else _coerce_scalar("now", value)
    if timestamp < 0:
        raise ValueError("now must be greater than or equal to 0")

    return timestamp


def _coerce_metrics(values: Mapping[str, Scalar]) -> dict[str, float]:
    return {name: _coerce_scalar(name, value) for name, value in values.items()}
