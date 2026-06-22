"""Custom panel helpers for the Textual dashboard."""

from __future__ import annotations

from collections.abc import Callable, Sequence
from dataclasses import dataclass

from trainpit._tui.constants import (
    FULLWIDTH_TITLE_TRANSLATION,
    PANEL_ID_CHARACTERS,
)
from trainpit._tui.snapshot import TrainDashboardSnapshot
from trainpit._tui.types import PanelSlot


def _panel_title(value: str) -> str:
    return value.translate(FULLWIDTH_TITLE_TRANSLATION)


def _validate_panel_id(value: str) -> None:
    if not value:
        raise ValueError("panel id must not be empty")
    if any(character not in PANEL_ID_CHARACTERS for character in value):
        raise ValueError(
            "panel id must contain only ASCII letters, numbers, underscores, or hyphens"
        )


@dataclass(frozen=True)
class DashboardPanel:
    """User-defined Textual dashboard panel."""

    id: str
    title: str
    render: Callable[[TrainDashboardSnapshot], str]
    slot: PanelSlot = "side"

    def __post_init__(self) -> None:
        _validate_panel_id(self.id)
        if not self.title:
            raise ValueError("panel title must not be empty")
        if not callable(self.render):
            raise TypeError("panel render must be callable")
        if self.slot not in ("top", "bottom", "side"):
            raise ValueError("panel slot must be one of: top, bottom, side")


def _validate_extra_panels(
    panels: Sequence[DashboardPanel],
) -> tuple[DashboardPanel, ...]:
    seen: set[str] = set()

    for panel in panels:
        if not isinstance(panel, DashboardPanel):
            raise TypeError("extra_panels must contain DashboardPanel instances")
        if panel.id in seen:
            raise ValueError(f"duplicate panel id: {panel.id}")
        seen.add(panel.id)

    return tuple(panels)


def _panel_container_id(panel: DashboardPanel) -> str:
    return f"custom-panel-{panel.id}"


def _panel_body_id(panel: DashboardPanel) -> str:
    return f"custom-{panel.id}"
