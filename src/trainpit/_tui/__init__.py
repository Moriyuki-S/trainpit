"""Internal modules backing the public trainpit.tui facade."""

from __future__ import annotations

from trainpit._tui.app import TrainDashboardApp as TrainDashboardApp
from trainpit._tui.formatting import (
    _format_curves as _format_curves,
    _format_metrics as _format_metrics,
    _format_progress as _format_progress,
    _format_timing as _format_timing,
)
from trainpit._tui.graphs import line_graph as line_graph
from trainpit._tui.graphs import scatter_graph as scatter_graph
from trainpit._tui.panels import DashboardPanel as DashboardPanel
from trainpit._tui.snapshot import TrainDashboardSnapshot as TrainDashboardSnapshot
from trainpit._tui.types import CurveGraphRenderer as CurveGraphRenderer
from trainpit._tui.types import DisplayText as DisplayText
from trainpit._tui.types import FiniteFloat as FiniteFloat
from trainpit._tui.types import NonNegativeFiniteFloat as NonNegativeFiniteFloat
from trainpit._tui.types import PanelSlot as PanelSlot
from trainpit._tui.types import PositiveInt as PositiveInt
from trainpit._tui.types import RunStatus as RunStatus
from trainpit._tui.types import Scalar as Scalar

__all__ = [
    "CurveGraphRenderer",
    "DashboardPanel",
    "DisplayText",
    "FiniteFloat",
    "NonNegativeFiniteFloat",
    "PanelSlot",
    "PositiveInt",
    "RunStatus",
    "Scalar",
    "TrainDashboardApp",
    "TrainDashboardSnapshot",
    "_format_curves",
    "_format_metrics",
    "_format_progress",
    "_format_timing",
    "line_graph",
    "scatter_graph",
]
