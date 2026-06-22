"""Display-ready state for the Textual dashboard."""

from __future__ import annotations

from collections.abc import Mapping
from time import monotonic

from pydantic import BaseModel, ConfigDict, Field

from trainpit._tui.types import (
    DisplayText,
    FiniteFloat,
    NonNegativeFiniteFloat,
    PositiveInt,
    RunStatus,
    Scalar,
)


class TrainDashboardSnapshot(BaseModel):
    """Display-ready training state for the Textual dashboard."""

    model_config = ConfigDict(
        extra="forbid",
        strict=True,
        validate_assignment=True,
        validate_default=True,
    )

    label: DisplayText | None = Field(
        default=None,
        description="Human-readable label for the displayed training run.",
    )
    status: RunStatus = Field(
        default="running",
        description="Lifecycle status shown in the dashboard.",
    )
    current_epoch: PositiveInt | None = Field(
        default=None,
        description="Current one-based epoch index.",
    )
    total_epochs: PositiveInt | None = Field(
        default=None,
        description="Total epoch count when known.",
    )
    current_step: PositiveInt | None = Field(
        default=None,
        description="Current one-based step index within the active epoch.",
    )
    total_steps: PositiveInt | None = Field(
        default=None,
        description="Total step count per epoch when known.",
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
        description="Monotonic timestamp when timing started.",
    )
    updated_at: NonNegativeFiniteFloat | None = Field(
        default=None,
        description="Monotonic timestamp for the latest state update.",
    )
    finished_at: NonNegativeFiniteFloat | None = Field(
        default=None,
        description="Monotonic timestamp when the run reached a terminal state.",
    )
    loss_history: list[FiniteFloat] = Field(
        default_factory=list,
        description="Finite loss values used to render the learning curve.",
    )
    metric_history: dict[DisplayText, list[FiniteFloat]] = Field(
        default_factory=dict,
        description="Finite metric histories used to render learning curves.",
    )

    def update_step(
        self,
        step: int,
        *,
        loss: Scalar | None = None,
        metrics: Mapping[str, Scalar] | None = None,
        learning_rate: Scalar | None = None,
        now: Scalar | None = None,
    ) -> None:
        """Update step-level values and append graph history."""

        self.current_step = step
        timestamp = _resolve_timestamp(now)

        if loss is not None:
            self.loss = _coerce_scalar("loss", loss)
            self.loss_history = [*self.loss_history, self.loss]

        if metrics is not None:
            coerced_metrics = _coerce_metrics(metrics)
            self.metrics = {**self.metrics, **coerced_metrics}
            metric_history = {
                name: [*values] for name, values in self.metric_history.items()
            }
            for name, value in coerced_metrics.items():
                metric_history.setdefault(name, []).append(value)
            self.metric_history = metric_history

        if learning_rate is not None:
            self.learning_rate = _coerce_scalar("learning_rate", learning_rate)

        self._touch(timestamp)

    def mark_finished(self, *, now: Scalar | None = None) -> None:
        """Record a successful terminal timestamp for the dashboard."""

        self._mark_terminal("finished", now=now)

    def mark_failed(self, *, now: Scalar | None = None) -> None:
        """Record a failed terminal timestamp for the dashboard."""

        self._mark_terminal("failed", now=now)

    def _mark_terminal(self, status: RunStatus, *, now: Scalar | None) -> None:
        timestamp = _resolve_timestamp(now)
        self.status = status
        self._touch(timestamp)
        self.finished_at = timestamp

    def _touch(self, timestamp: float) -> None:
        if self.started_at is None:
            self.started_at = timestamp
        self.updated_at = timestamp


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
