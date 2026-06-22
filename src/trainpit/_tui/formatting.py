"""String formatting helpers for Textual dashboard widgets."""

from __future__ import annotations

from collections.abc import Sequence
from time import monotonic

from trainpit._tui.constants import (
    EPOCH_AXIS_LABEL_PADDING,
    EPOCH_AXIS_MIN_LABEL_SPACING,
    GRAPH_WIDTH,
    PRIMARY_GRAPH_HEIGHT,
    PROGRESS_BAR_WIDTH,
    SAMPLES_PER_BRAILLE,
    SECONDARY_GRAPH_HEIGHT,
)
from trainpit._tui.graphs import line_graph
from trainpit._tui.snapshot import TrainDashboardSnapshot, _resolve_timestamp
from trainpit._tui.types import CurveGraphRenderer, Scalar
from trainpit._tui.values import _format_graph_value


def _format_progress(snapshot: TrainDashboardSnapshot) -> str:
    return "\n".join(
        [
            _format_progress_row(
                "epoch", snapshot.current_epoch, snapshot.total_epochs
            ),
            _format_progress_bar(snapshot.current_epoch, snapshot.total_epochs),
            _format_progress_row("step", snapshot.current_step, snapshot.total_steps),
            _format_progress_bar(snapshot.current_step, snapshot.total_steps),
        ]
    )


def _format_metrics(snapshot: TrainDashboardSnapshot) -> str:
    lines: list[str] = []

    if snapshot.loss is not None:
        lines.append(_format_metric_row("loss", snapshot.loss, snapshot.loss_history))

    for name, value in snapshot.metrics.items():
        lines.append(
            _format_metric_row(name, value, snapshot.metric_history.get(name, []))
        )

    if snapshot.learning_rate is not None:
        lines.append(_format_metric_row("lr", snapshot.learning_rate, []))

    return "\n".join(lines) if lines else "metrics warming up"


def _format_curves(
    snapshot: TrainDashboardSnapshot,
    width: int = GRAPH_WIDTH,
    graph_renderer: CurveGraphRenderer = line_graph,
) -> str:
    lines: list[str] = []

    if snapshot.loss_history:
        lines.append(
            _format_curve_block(
                "loss",
                snapshot.loss_history,
                width=width,
                height=PRIMARY_GRAPH_HEIGHT,
                total_steps=snapshot.total_steps,
                total_epochs=snapshot.total_epochs,
                graph_renderer=graph_renderer,
            )
        )

    for name, values in snapshot.metric_history.items():
        lines.append(
            _format_curve_block(
                name,
                values,
                width=width,
                height=SECONDARY_GRAPH_HEIGHT,
                total_steps=snapshot.total_steps,
                total_epochs=snapshot.total_epochs,
                graph_renderer=graph_renderer,
            )
        )

    return "\n\n".join(lines) if lines else "Waiting for history"


def _format_timing(
    snapshot: TrainDashboardSnapshot,
    *,
    now: Scalar | None = None,
) -> str:
    if snapshot.started_at is None:
        return "\n".join(
            [
                "elapsed --:--:--",
                "step/s  --",
                "eta     --:--:--",
                "last    --:--:--",
            ]
        )

    timestamp = _resolve_timing_now(snapshot, now)
    elapsed = max(0.0, timestamp - snapshot.started_at)
    completed_steps, total_steps = _timing_step_counts(snapshot)
    active_elapsed = _active_elapsed_seconds(snapshot)
    step_rate = _step_rate(completed_steps, active_elapsed)
    eta = _eta_seconds(
        snapshot,
        completed_steps=completed_steps,
        total_steps=total_steps,
        step_rate=step_rate,
    )
    last_update_age = _last_update_age(snapshot, timestamp)

    return "\n".join(
        [
            f"elapsed {_format_duration(elapsed)}",
            f"step/s  {_format_rate(step_rate)}",
            f"eta     {_format_optional_duration(eta)}",
            f"last    {_format_duration(last_update_age)}",
        ]
    )


def _format_curve_block(
    name: str,
    values: Sequence[float],
    *,
    width: int,
    height: int,
    total_steps: int | None,
    total_epochs: int | None,
    graph_renderer: CurveGraphRenderer,
) -> str:
    return "\n".join(
        [
            _format_curve_header(name, values),
            *graph_renderer(values, width, height),
            *_format_epoch_axis(
                values,
                total_steps=total_steps,
                total_epochs=total_epochs,
                width=width,
            ),
        ]
    )


def _format_curve_header(name: str, values: Sequence[float]) -> str:
    return (
        f"{name:<5} now {_format_graph_value(values[-1])}  "
        f"min {_format_graph_value(min(values))}  "
        f"max {_format_graph_value(max(values))}  n {len(values)}"
    )


def _resolve_timing_now(
    snapshot: TrainDashboardSnapshot,
    value: Scalar | None,
) -> float:
    if snapshot.finished_at is not None:
        return snapshot.finished_at
    if value is not None:
        return _resolve_timestamp(value)

    return monotonic()


def _active_elapsed_seconds(snapshot: TrainDashboardSnapshot) -> float:
    if snapshot.started_at is None or snapshot.updated_at is None:
        return 0.0

    return max(0.0, snapshot.updated_at - snapshot.started_at)


def _timing_step_counts(
    snapshot: TrainDashboardSnapshot,
) -> tuple[int | None, int | None]:
    if snapshot.current_step is None:
        return None, None

    completed_steps = snapshot.current_step
    total_steps = snapshot.total_steps

    if snapshot.total_steps is not None and snapshot.current_epoch is not None:
        completed_steps = (
            (snapshot.current_epoch - 1) * snapshot.total_steps
        ) + snapshot.current_step
        total_steps = (
            snapshot.total_steps * snapshot.total_epochs
            if snapshot.total_epochs is not None
            else None
        )

    return completed_steps, total_steps


def _step_rate(completed_steps: int | None, elapsed: float) -> float | None:
    if completed_steps is None or completed_steps <= 0 or elapsed <= 0:
        return None

    return completed_steps / elapsed


def _eta_seconds(
    snapshot: TrainDashboardSnapshot,
    *,
    completed_steps: int | None,
    total_steps: int | None,
    step_rate: float | None,
) -> float | None:
    if snapshot.status == "finished":
        return 0.0
    if snapshot.status == "failed":
        return None
    if completed_steps is None or total_steps is None or step_rate is None:
        return None

    remaining_steps = max(0, total_steps - completed_steps)
    return remaining_steps / step_rate


def _last_update_age(snapshot: TrainDashboardSnapshot, now: float) -> float:
    if snapshot.updated_at is None:
        return 0.0

    return max(0.0, now - snapshot.updated_at)


def _format_optional_duration(value: float | None) -> str:
    if value is None:
        return "--:--:--"

    return _format_duration(value)


def _format_duration(seconds: float) -> str:
    total_seconds = max(0, int(seconds))
    hours, remainder = divmod(total_seconds, 3600)
    minutes, seconds = divmod(remainder, 60)
    return f"{hours:02d}:{minutes:02d}:{seconds:02d}"


def _format_rate(value: float | None) -> str:
    if value is None:
        return "--"

    return f"{value:.2f}"


def _format_current_total(current: int | None, total: int | None) -> str:
    if current is None:
        return "-"
    if total is None:
        return str(current)
    if total <= 0:
        return f"{current}/{total}"

    percent = current / total * 100
    return f"{current}/{total} ({percent:.1f}%)"


def _format_progress_row(name: str, current: int | None, total: int | None) -> str:
    return f"{name:<5} {_format_current_total(current, total)}"


def _format_progress_bar(
    current: int | None,
    total: int | None,
    width: int = PROGRESS_BAR_WIDTH,
) -> str:
    progress = _progress_fraction(current, total)
    if progress is None:
        return f"[{'░' * width}] --.-%"

    filled = round(progress * width)
    empty = width - filled
    return f"[{'█' * filled}{'░' * empty}] {progress * 100:5.1f}%"


def _format_metric_row(name: str, value: float, history: Sequence[float]) -> str:
    return (
        f"{name:<8} {_format_graph_value(value):>10}  {_format_metric_delta(history)}"
    )


def _format_metric_delta(history: Sequence[float]) -> str:
    if len(history) < 2:
        return "delta --"

    return f"delta {history[-1] - history[-2]:+.4f}"


def _progress_fraction(current: int | None, total: int | None) -> float | None:
    if current is None or total is None or total <= 0:
        return None

    return min(max(current / total, 0.0), 1.0)


def _format_epoch_axis(
    values: Sequence[float],
    *,
    total_steps: int | None,
    total_epochs: int | None,
    width: int,
) -> list[str]:
    if total_steps is None or not values:
        return []

    positions = _epoch_label_positions(
        value_count=len(values),
        total_steps=total_steps,
        total_epochs=total_epochs,
        width=width,
    )
    if not positions:
        return []

    positions = _select_epoch_axis_labels(positions, width=width)
    ticks = [" "] * width
    labels = [" "] * width

    for epoch, position in positions:
        if _place_axis_label(labels, position, f"e{epoch}"):
            ticks[position] = "┬"

    return [
        f"{'':>10}  {''.join(ticks).rstrip()}",
        f"{'epoch':>10}  {''.join(labels).rstrip()}",
    ]


def _epoch_label_positions(
    *,
    value_count: int,
    total_steps: int,
    total_epochs: int | None,
    width: int,
) -> list[tuple[int, int]]:
    if value_count < 1 or total_steps < 1:
        return []

    max_epoch = (value_count - 1) // total_steps + 1
    if total_epochs is not None:
        max_epoch = min(max_epoch, total_epochs)

    sample_capacity = width * SAMPLES_PER_BRAILLE
    positions: list[tuple[int, int]] = []

    for epoch in range(1, max_epoch + 1):
        history_index = (epoch - 1) * total_steps + 1
        if history_index > value_count:
            continue

        sample_position = _history_index_to_sample_position(
            history_index,
            value_count=value_count,
            sample_capacity=sample_capacity,
        )
        graph_position = min(width - 1, max(0, sample_position // SAMPLES_PER_BRAILLE))
        positions.append((epoch, graph_position))

    return positions


def _select_epoch_axis_labels(
    positions: Sequence[tuple[int, int]],
    *,
    width: int,
) -> list[tuple[int, int]]:
    if len(positions) <= 2:
        return list(positions)

    max_label_count = max(2, width // EPOCH_AXIS_MIN_LABEL_SPACING)
    if len(positions) <= max_label_count:
        return list(positions)

    last_index = len(positions) - 1
    selected_indexes = {
        round(index * last_index / (max_label_count - 1))
        for index in range(max_label_count)
    }
    return [positions[index] for index in sorted(selected_indexes)]


def _history_index_to_sample_position(
    history_index: int,
    *,
    value_count: int,
    sample_capacity: int,
) -> int:
    if value_count <= sample_capacity:
        return history_index - 1

    return round((history_index - 1) * (sample_capacity - 1) / (value_count - 1))


def _place_axis_label(cells: list[str], center: int, label: str) -> bool:
    if len(label) > len(cells):
        return False

    start = min(max(center - len(label) // 2, 0), len(cells) - len(label))
    end = start + len(label)
    padded_start = max(0, start - EPOCH_AXIS_LABEL_PADDING)
    padded_end = min(len(cells), end + EPOCH_AXIS_LABEL_PADDING)

    if any(character != " " for character in cells[padded_start:padded_end]):
        return False

    cells[start:end] = label
    return True
