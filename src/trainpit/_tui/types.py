"""Shared TUI type aliases."""

from __future__ import annotations

from collections.abc import Callable, Sequence
from typing import Annotated, Literal

from pydantic import Field

Scalar = float | int
DisplayText = Annotated[str, Field(strict=True, min_length=1)]
FiniteFloat = Annotated[float, Field(strict=True, allow_inf_nan=False)]
NonNegativeFiniteFloat = Annotated[
    float,
    Field(strict=True, ge=0, allow_inf_nan=False),
]
PositiveInt = Annotated[int, Field(strict=True, ge=1)]
RunStatus = Literal["running", "finished", "failed"]
PanelSlot = Literal["top", "bottom", "side"]
CurveGraphRenderer = Callable[[Sequence[float], int, int], list[str]]
