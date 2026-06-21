"""Textual TUI components for trainpit."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from typing import Annotated, Literal

from pydantic import BaseModel, ConfigDict, Field
from textual.app import App, ComposeResult
from textual.containers import Horizontal, Vertical
from textual.widgets import Footer, Header, Static

Scalar = float | int
DisplayText = Annotated[str, Field(strict=True, min_length=1)]
FiniteFloat = Annotated[float, Field(strict=True, allow_inf_nan=False)]
NonNegativeFiniteFloat = Annotated[
    float,
    Field(strict=True, ge=0, allow_inf_nan=False),
]
PositiveInt = Annotated[int, Field(strict=True, ge=1)]
RunStatus = Literal["running", "finished", "failed"]
GRAPH_WIDTH = 56
PRIMARY_GRAPH_HEIGHT = 7
SECONDARY_GRAPH_HEIGHT = 3
PROGRESS_BAR_WIDTH = 24
BRAILLE_BASE = 0x2800
BRAILLE_COLUMNS = (
    (0x01, 0x02, 0x04, 0x40),
    (0x08, 0x10, 0x20, 0x80),
)
BRAILLE_ROWS_PER_CELL = 4
SAMPLES_PER_BRAILLE = 2
EPOCH_AXIS_MIN_LABEL_SPACING = 8
EPOCH_AXIS_LABEL_PADDING = 1
FULLWIDTH_TITLE_TRANSLATION = str.maketrans(
    {
        " ": "　",
        **{chr(value): chr(value + 0xFEE0) for value in range(ord("A"), ord("Z") + 1)},
    }
)


def _panel_title(value: str) -> str:
    return value.translate(FULLWIDTH_TITLE_TRANSLATION)


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
    ) -> None:
        """Update step-level values and append graph history."""

        self.current_step = step

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


class TrainDashboardApp(App[None]):
    """A compact Textual dashboard for train progress."""

    CSS = """
    Screen {
        background: #07090d;
        color: #d7dee8;
    }

    Header,
    Footer {
        background: #0b0f14;
        color: #97a3b6;
    }

    #dashboard {
        height: 1fr;
        padding: 0 1 1 1;
    }

    #top-row {
        height: 10;
        min-height: 9;
    }

    #bottom-row {
        height: 1fr;
        min-height: 16;
    }

    .panel {
        background: #0c1117;
        border: round #27313f;
        padding: 0 1;
        margin: 0 1 1 0;
        min-width: 24;
    }

    #status-panel {
        width: 1fr;
        min-width: 22;
    }

    #progress-panel {
        width: 2fr;
        min-width: 34;
    }

    #metrics-panel {
        width: 2fr;
        min-width: 32;
    }

    .graph-panel {
        width: 4fr;
        min-width: 60;
    }

    #bottom-side {
        width: 1fr;
        min-width: 24;
    }

    .side-panel {
        height: 1fr;
    }

    .panel-title {
        background: #101b24;
        color: #6ee7f9;
        text-style: bold reverse;
        padding: 0 1;
        margin-bottom: 1;
        width: 1fr;
    }

    #status {
        color: #7ee787;
        text-style: bold;
    }

    .status-running {
        color: #7ee787;
    }

    .status-finished {
        color: #6ee7f9;
    }

    .status-failed {
        color: #ff7b72;
    }

    #label {
        color: #f0f4fa;
    }

    #curve {
        color: #7ee787;
    }

    #progress {
        color: #f0c36a;
    }

    #metrics {
        color: #f0f4fa;
    }

    #timing {
        color: #97a3b6;
    }

    #events {
        color: #d7dee8;
    }
    """

    TITLE = "trainpit"
    SUB_TITLE = "training monitor"
    ENABLE_COMMAND_PALETTE = False
    BINDINGS = [("q", "quit", "Quit")]

    def __init__(self, snapshot: TrainDashboardSnapshot | None = None) -> None:
        super().__init__()
        self.snapshot = snapshot or TrainDashboardSnapshot()

    def compose(self) -> ComposeResult:
        yield Header(show_clock=True)
        with Vertical(id="dashboard"):
            with Horizontal(id="top-row"):
                with Vertical(id="status-panel", classes="panel"):
                    yield Static(_panel_title("STATUS"), classes="panel-title")
                    yield Static("", id="status")
                    yield Static("", id="label")
                with Vertical(id="progress-panel", classes="panel"):
                    yield Static(_panel_title("PROGRESS"), classes="panel-title")
                    yield Static("", id="progress")
                with Vertical(id="metrics-panel", classes="panel"):
                    yield Static(_panel_title("METRICS"), classes="panel-title")
                    yield Static("", id="metrics")
            with Horizontal(id="bottom-row"):
                with Vertical(classes="panel graph-panel"):
                    yield Static(_panel_title("LEARNING CURVE"), classes="panel-title")
                    yield Static("", id="curve")
                with Vertical(id="bottom-side"):
                    with Vertical(classes="panel side-panel"):
                        yield Static(_panel_title("TIMING"), classes="panel-title")
                        yield Static("", id="timing")
                    with Vertical(classes="panel side-panel"):
                        yield Static(_panel_title("EVENTS"), classes="panel-title")
                        yield Static("", id="events")
        yield Footer()

    def on_mount(self) -> None:
        self.refresh_dashboard()

    def refresh_dashboard(self) -> None:
        """Render the current snapshot into dashboard widgets."""

        snapshot = self.snapshot
        status = self.query_one("#status", Static)
        status.update(snapshot.status.upper())
        for value in ("running", "finished", "failed"):
            status.set_class(snapshot.status == value, f"status-{value}")

        self.query_one("#label", Static).update(snapshot.label or "unlabeled run")
        self.query_one("#progress", Static).update(_format_progress(snapshot))
        self.query_one("#metrics", Static).update(_format_metrics(snapshot))
        self.query_one("#curve", Static).update(_format_curves(snapshot))
        self.query_one("#timing", Static).update(_format_timing(snapshot))
        self.query_one("#events", Static).update(snapshot.event or "waiting for events")

    def update_snapshot(self, snapshot: TrainDashboardSnapshot) -> None:
        """Replace the dashboard snapshot and refresh visible widgets."""

        self.snapshot = snapshot
        if self.is_mounted:
            self.refresh_dashboard()


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


def _format_curves(snapshot: TrainDashboardSnapshot, width: int = GRAPH_WIDTH) -> str:
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
            )
        )

    return "\n\n".join(lines) if lines else "Waiting for history"


def _format_curve_block(
    name: str,
    values: Sequence[float],
    *,
    width: int,
    height: int,
    total_steps: int | None,
    total_epochs: int | None,
) -> str:
    return "\n".join(
        [
            _format_curve_header(name, values),
            *_braille_area_graph(values, width=width, height=height),
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


def _format_timing(snapshot: TrainDashboardSnapshot) -> str:
    del snapshot
    return "elapsed --:--:--\neta     --:--:--"


def _coerce_scalar(name: str, value: Scalar) -> float:
    if isinstance(value, bool) or not isinstance(value, int | float):
        raise TypeError(f"{name} must be a finite scalar")

    return float(value)


def _coerce_metrics(values: Mapping[str, Scalar]) -> dict[str, float]:
    return {name: _coerce_scalar(name, value) for name, value in values.items()}


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


def _braille_area_graph(
    values: Sequence[float],
    *,
    width: int,
    height: int,
) -> list[str]:
    if not values:
        return []

    samples = _right_aligned_samples(values, width * SAMPLES_PER_BRAILLE)
    levels = _scale_braille_levels(
        samples, minimum=min(values), maximum=max(values), height=height
    )
    rows: list[str] = []

    for row in range(height, 0, -1):
        axis = "└" if row == 1 else "┤"
        rows.append(
            f"{_format_axis_label(row, height, min(values), max(values))} {axis}"
            f"{_format_braille_row(levels, row, width)}"
        )

    return rows


def _right_aligned_samples(
    values: Sequence[float],
    sample_capacity: int,
) -> list[float | None]:
    samples = _sample(values, sample_capacity)
    padding = sample_capacity - len(samples)

    if padding <= 0:
        return list(samples)

    return [None] * padding + samples


def _scale_braille_levels(
    values: Sequence[float | None],
    *,
    minimum: float,
    maximum: float,
    height: int,
) -> list[int | None]:
    total_units = height * BRAILLE_ROWS_PER_CELL

    if maximum == minimum:
        midpoint = max(1, total_units // 2)
        return [midpoint if value is not None else None for value in values]

    levels: list[int | None] = []
    for value in values:
        if value is None:
            levels.append(None)
            continue

        ratio = (value - minimum) / (maximum - minimum)
        levels.append(max(1, round(ratio * total_units)))

    return levels


def _format_braille_row(
    levels: Sequence[int | None],
    row: int,
    width: int,
) -> str:
    cells: list[str] = []

    for index in range(width):
        sample_index = index * SAMPLES_PER_BRAILLE
        cells.append(
            _format_braille_cell(
                levels[sample_index],
                levels[sample_index + 1],
                row,
            )
        )

    return "".join(cells)


def _format_braille_cell(
    left_level: int | None,
    right_level: int | None,
    row: int,
) -> str:
    mask = 0

    for column_index, level in enumerate((left_level, right_level)):
        if level is None:
            continue

        for dot_index, dot in enumerate(BRAILLE_COLUMNS[column_index]):
            unit_from_bottom = (row - 1) * BRAILLE_ROWS_PER_CELL
            unit_from_bottom += BRAILLE_ROWS_PER_CELL - dot_index
            if level >= unit_from_bottom:
                mask |= dot

    if mask == 0:
        return " "

    return chr(BRAILLE_BASE + mask)


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
        return sample_capacity - value_count + history_index - 1

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


def _format_axis_label(
    row: int,
    height: int,
    minimum: float,
    maximum: float,
) -> str:
    if row == height:
        return f"{_format_graph_value(maximum):>10}"
    if row == 1:
        return f"{_format_graph_value(minimum):>10}"

    return " " * 10


def _format_graph_value(value: float) -> str:
    absolute = abs(value)
    if absolute != 0 and (absolute < 0.001 or absolute >= 1000):
        return f"{value:.3e}"

    return f"{value:.4f}"


def _sample(values: Sequence[float], width: int) -> list[float]:
    if len(values) <= width:
        return list(values)

    return [
        values[round(index * (len(values) - 1) / (width - 1))] for index in range(width)
    ]
