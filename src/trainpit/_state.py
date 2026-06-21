"""Internal state for train progress tracking."""

from __future__ import annotations

from collections.abc import Mapping
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

    def start(self) -> None:
        self.started = True
        self.finished = False
        self.failed = False
        self.error = None

    def set_epoch(self, value: int) -> None:
        self.current_epoch = _require_positive_integer("epoch", value)

    def set_step(
        self,
        value: int,
        *,
        loss: Scalar | None = None,
        metrics: Mapping[str, Scalar] | None = None,
        learning_rate: Scalar | None = None,
    ) -> None:
        self.current_step = _require_positive_integer("step", value)

        if loss is not None:
            self.loss = _coerce_scalar("loss", loss)
        if metrics is not None:
            self.metrics = {**self.metrics, **_coerce_metrics(metrics)}
        if learning_rate is not None:
            self.learning_rate = _coerce_scalar("learning_rate", learning_rate)

    def set_metrics(self, values: Mapping[str, Scalar]) -> None:
        self.metrics = {**self.metrics, **_coerce_metrics(values)}

    def set_event(self, message: str) -> None:
        self.event = message

    def finish(self) -> None:
        self.finished = True
        self.failed = False
        self.error = None

    def fail(self, error: BaseException) -> None:
        self.finished = True
        self.failed = True
        self.error = error


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


def _coerce_metrics(values: Mapping[str, Scalar]) -> dict[str, float]:
    return {name: _coerce_scalar(name, value) for name, value in values.items()}
