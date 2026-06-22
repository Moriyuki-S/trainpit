"""Numeric formatting helpers for TUI output."""

from __future__ import annotations


def _format_graph_value(value: float) -> str:
    absolute = abs(value)
    if absolute != 0 and (absolute < 0.001 or absolute >= 1000):
        return f"{value:.3e}"

    return f"{value:.4f}"
