"""Constants used by trainpit TUI rendering."""

from __future__ import annotations

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
PANEL_ID_CHARACTERS = frozenset(
    "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789_-"
)
FULLWIDTH_TITLE_TRANSLATION = str.maketrans(
    {
        " ": " ",
        **{chr(value): chr(value + 0xFEE0) for value in range(ord("A"), ord("Z") + 1)},
    }
)
