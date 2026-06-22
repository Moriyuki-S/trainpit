"""Terminal graph renderers for dashboard learning curves."""

from __future__ import annotations

from collections.abc import Sequence

from trainpit._tui.constants import (
    BRAILLE_BASE,
    BRAILLE_COLUMNS,
    BRAILLE_ROWS_PER_CELL,
    SAMPLES_PER_BRAILLE,
)
from trainpit._tui.values import _format_graph_value


def line_graph(values: Sequence[float], width: int, height: int) -> list[str]:
    """Render values as a connected braille line graph."""

    return _braille_graph(values, width=width, height=height, connect_points=True)


def scatter_graph(values: Sequence[float], width: int, height: int) -> list[str]:
    """Render values as unconnected braille scatter points."""

    return _braille_graph(values, width=width, height=height, connect_points=False)


def _braille_graph(
    values: Sequence[float],
    *,
    width: int,
    height: int,
    connect_points: bool,
) -> list[str]:
    if not values:
        return []

    samples = _left_aligned_samples(values, width * SAMPLES_PER_BRAILLE)
    levels = _scale_braille_levels(
        samples, minimum=min(values), maximum=max(values), height=height
    )
    point_sets = (
        _connect_braille_levels(levels) if connect_points else _point_levels(levels)
    )
    rows: list[str] = []

    for row in range(height, 0, -1):
        axis = "└" if row == 1 else "┤"
        rows.append(
            f"{_format_axis_label(row, height, min(values), max(values))} {axis}"
            f"{_format_braille_row(point_sets, row, width)}"
        )

    return rows


def _left_aligned_samples(
    values: Sequence[float],
    sample_capacity: int,
) -> list[float | None]:
    samples = _sample(values, sample_capacity)
    padding = sample_capacity - len(samples)

    if padding <= 0:
        return list(samples)

    return [*samples, *([None] * padding)]


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


def _point_levels(
    levels: Sequence[int | None],
) -> list[frozenset[int] | None]:
    return [frozenset({level}) if level is not None else None for level in levels]


def _connect_braille_levels(
    levels: Sequence[int | None],
) -> list[frozenset[int] | None]:
    connected_levels: list[frozenset[int] | None] = []
    previous_level: int | None = None

    for level in levels:
        if level is None:
            connected_levels.append(None)
            previous_level = None
            continue

        if previous_level is None:
            connected_levels.append(frozenset({level}))
        else:
            minimum = min(previous_level, level)
            maximum = max(previous_level, level)
            connected_levels.append(frozenset(range(minimum, maximum + 1)))

        previous_level = level

    return connected_levels


def _format_braille_row(
    point_sets: Sequence[frozenset[int] | None],
    row: int,
    width: int,
) -> str:
    cells: list[str] = []

    for index in range(width):
        sample_index = index * SAMPLES_PER_BRAILLE
        cells.append(
            _format_braille_cell(
                point_sets[sample_index],
                point_sets[sample_index + 1],
                row,
            )
        )

    return "".join(cells)


def _format_braille_cell(
    left_levels: frozenset[int] | None,
    right_levels: frozenset[int] | None,
    row: int,
) -> str:
    mask = 0

    for column_index, levels in enumerate((left_levels, right_levels)):
        if levels is None:
            continue

        for dot_index, dot in enumerate(BRAILLE_COLUMNS[column_index]):
            unit_from_bottom = (row - 1) * BRAILLE_ROWS_PER_CELL
            unit_from_bottom += BRAILLE_ROWS_PER_CELL - dot_index
            if unit_from_bottom in levels:
                mask |= dot

    if mask == 0:
        return " "

    return chr(BRAILLE_BASE + mask)


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


def _sample(values: Sequence[float], width: int) -> list[float]:
    if len(values) <= width:
        return list(values)

    return [
        values[round(index * (len(values) - 1) / (width - 1))] for index in range(width)
    ]
