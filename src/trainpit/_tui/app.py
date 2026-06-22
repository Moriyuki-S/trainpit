"""Textual app implementation for the trainpit dashboard."""

from __future__ import annotations

from collections.abc import Sequence

from textual.app import App, ComposeResult
from textual.containers import Horizontal, Vertical
from textual.widgets import Footer, Header, Static

from trainpit._tui.formatting import (
    _format_curves,
    _format_metrics,
    _format_progress,
    _format_timing,
)
from trainpit._tui.graphs import line_graph
from trainpit._tui.panels import (
    DashboardPanel,
    _panel_body_id,
    _panel_container_id,
    _panel_title,
    _validate_extra_panels,
)
from trainpit._tui.snapshot import TrainDashboardSnapshot
from trainpit._tui.types import CurveGraphRenderer, PanelSlot


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

    .bottom-panel {
        width: 2fr;
        min-width: 32;
    }

    .custom-panel {
        color: #d7dee8;
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

    def __init__(
        self,
        snapshot: TrainDashboardSnapshot | None = None,
        *,
        extra_panels: Sequence[DashboardPanel] | None = None,
        graph_renderer: CurveGraphRenderer = line_graph,
    ) -> None:
        super().__init__()
        self.snapshot = snapshot or TrainDashboardSnapshot()
        self.extra_panels = _validate_extra_panels(extra_panels or ())
        self.graph_renderer = _validate_graph_renderer(graph_renderer)

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
                for panel in self._panels_for_slot("top"):
                    with Vertical(
                        id=_panel_container_id(panel),
                        classes="panel custom-panel",
                    ):
                        yield Static(
                            _panel_title(panel.title),
                            classes="panel-title",
                        )
                        yield Static("", id=_panel_body_id(panel))
            with Horizontal(id="bottom-row"):
                with Vertical(classes="panel graph-panel"):
                    yield Static(_panel_title("LEARNING CURVE"), classes="panel-title")
                    yield Static("", id="curve")
                for panel in self._panels_for_slot("bottom"):
                    with Vertical(
                        id=_panel_container_id(panel),
                        classes="panel bottom-panel custom-panel",
                    ):
                        yield Static(
                            _panel_title(panel.title),
                            classes="panel-title",
                        )
                        yield Static("", id=_panel_body_id(panel))
                with Vertical(id="bottom-side"):
                    with Vertical(classes="panel side-panel"):
                        yield Static(_panel_title("TIMING"), classes="panel-title")
                        yield Static("", id="timing")
                    with Vertical(classes="panel side-panel"):
                        yield Static(_panel_title("EVENTS"), classes="panel-title")
                        yield Static("", id="events")
                    for panel in self._panels_for_slot("side"):
                        with Vertical(
                            id=_panel_container_id(panel),
                            classes="panel side-panel custom-panel",
                        ):
                            yield Static(
                                _panel_title(panel.title),
                                classes="panel-title",
                            )
                            yield Static("", id=_panel_body_id(panel))
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
        self.query_one("#curve", Static).update(
            _format_curves(snapshot, graph_renderer=self.graph_renderer)
        )
        self.query_one("#timing", Static).update(_format_timing(snapshot))
        self.query_one("#events", Static).update(snapshot.event or "waiting for events")
        for panel in self.extra_panels:
            self.query_one(f"#{_panel_body_id(panel)}", Static).update(
                panel.render(snapshot)
            )

    def update_snapshot(self, snapshot: TrainDashboardSnapshot) -> None:
        """Replace the dashboard snapshot and refresh visible widgets."""

        self.snapshot = snapshot
        if self.is_mounted:
            self.refresh_dashboard()

    def _panels_for_slot(self, slot: PanelSlot) -> tuple[DashboardPanel, ...]:
        return tuple(panel for panel in self.extra_panels if panel.slot == slot)


def _validate_graph_renderer(renderer: CurveGraphRenderer) -> CurveGraphRenderer:
    if not callable(renderer):
        raise TypeError("graph_renderer must be callable")

    return renderer
