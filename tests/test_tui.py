from __future__ import annotations

import asyncio

import pytest
from pydantic import BaseModel, ValidationError
from textual.widgets import Static

from trainpit.tui import (
    TrainDashboardApp,
    TrainDashboardSnapshot,
    _format_curves,
    _format_metrics,
    _format_progress,
)


def _static_text(app: TrainDashboardApp, selector: str) -> str:
    return str(app.query_one(selector, Static).render())


def test_train_dashboard_app_renders_snapshot() -> None:
    async def run_app() -> None:
        snapshot = TrainDashboardSnapshot(
            label="test-run",
            total_epochs=3,
            total_steps=8,
        )
        snapshot.current_epoch = 2
        snapshot.update_step(
            4,
            loss=0.42,
            metrics={"acc": 0.88},
            learning_rate=0.0001,
        )
        snapshot.event = "checkpoint saved"
        app = TrainDashboardApp(snapshot)

        async with app.run_test(size=(100, 30)) as pilot:
            await pilot.pause()

            assert _static_text(app, "#status") == "RUNNING"
            assert _static_text(app, "#label") == "test-run"
            assert "epoch 2/3" in _static_text(app, "#progress")
            assert "loss" in _static_text(app, "#metrics")
            assert "0.4200" in _static_text(app, "#metrics")
            assert "acc" in _static_text(app, "#metrics")
            assert "0.8800" in _static_text(app, "#metrics")
            assert "checkpoint saved" in _static_text(app, "#events")

    asyncio.run(run_app())


def test_train_dashboard_app_updates_snapshot_after_mount() -> None:
    async def run_app() -> None:
        app = TrainDashboardApp(TrainDashboardSnapshot(label="before"))

        async with app.run_test(size=(100, 30)) as pilot:
            await pilot.pause()

            snapshot = TrainDashboardSnapshot(label="after", status="finished")
            snapshot.update_step(1, loss=0.5, metrics={"acc": 1.0})
            app.update_snapshot(snapshot)
            await pilot.pause()

            assert _static_text(app, "#status") == "FINISHED"
            assert _static_text(app, "#label") == "after"
            assert "acc" in _static_text(app, "#metrics")
            assert "1.0000" in _static_text(app, "#metrics")

    asyncio.run(run_app())


def test_learning_curve_uses_btop_style_braille_graph() -> None:
    snapshot = TrainDashboardSnapshot()

    for step in range(60):
        snapshot.update_step(step + 1, loss=1.0 / (step + 1))

    curve_text = _format_curves(snapshot)
    lines = curve_text.splitlines()
    graph_lines = lines[1:8]
    graph_cells = [_graph_cells(line) for line in graph_lines]

    assert lines[0].startswith("loss  now")
    assert len(graph_lines) == 7
    assert all(len(cells) == 56 for cells in graph_cells)
    graph_text = "\n".join(graph_cells)
    graph_characters = [character for character in graph_text if character != "\n"]
    braille_characters = [
        character for character in graph_characters if "\u2800" < character <= "\u28ff"
    ]

    assert braille_characters
    assert all(
        character == " " or "\u2800" < character <= "\u28ff"
        for character in graph_characters
    )
    assert graph_cells[-1][-1] in braille_characters
    assert "•" not in graph_text
    assert "·" not in graph_text
    assert "█" not in graph_text
    assert "▓" not in graph_text


def test_learning_curve_shows_readable_epoch_x_axis_when_total_steps_is_known() -> None:
    snapshot = TrainDashboardSnapshot(total_epochs=3, total_steps=4)

    for step in range(12):
        snapshot.update_step(step + 1, loss=1.0 / (step + 1))

    curve_text = _format_curves(snapshot, width=12)
    lines = curve_text.splitlines()

    assert lines[8].count("┬") == 2
    assert lines[9].startswith("     epoch")
    assert "e1" in lines[9]
    assert "e3" in lines[9]
    assert "e1e" not in lines[9]


def test_learning_curve_thins_crowded_epoch_labels() -> None:
    snapshot = TrainDashboardSnapshot(total_epochs=10, total_steps=1)

    for step in range(10):
        snapshot.update_step(step + 1, loss=1.0 / (step + 1))

    curve_text = _format_curves(snapshot, width=20)
    lines = curve_text.splitlines()
    labels = lines[9]

    assert lines[8].count("┬") <= 3
    assert "e1" in labels
    assert "e10" in labels
    assert "e1e" not in labels


def test_progress_uses_epoch_and_step_bars() -> None:
    snapshot = TrainDashboardSnapshot(
        current_epoch=2,
        total_epochs=4,
        current_step=5,
        total_steps=10,
    )

    progress_text = _format_progress(snapshot)
    lines = progress_text.splitlines()

    assert lines[0] == "epoch 2/4 (50.0%)"
    assert lines[2] == "step  5/10 (50.0%)"
    assert _bar_cells(lines[1]) == "████████████░░░░░░░░░░░░"
    assert _bar_cells(lines[3]) == "████████████░░░░░░░░░░░░"
    assert lines[1].endswith("50.0%")
    assert lines[3].endswith("50.0%")


def test_metrics_show_aligned_values_and_delta() -> None:
    snapshot = TrainDashboardSnapshot()
    snapshot.update_step(1, loss=0.6, metrics={"acc": 0.7})
    snapshot.update_step(2, loss=0.5, metrics={"acc": 0.75})

    metrics_text = _format_metrics(snapshot)

    assert "loss" in metrics_text
    assert "0.5000" in metrics_text
    assert "delta -0.1000" in metrics_text
    assert "acc" in metrics_text
    assert "0.7500" in metrics_text
    assert "delta +0.0500" in metrics_text


def test_train_dashboard_snapshot_is_pydantic_model() -> None:
    first = TrainDashboardSnapshot()
    second = TrainDashboardSnapshot()

    first.update_step(1, loss=0.5, metrics={"acc": 0.9})

    assert isinstance(first, BaseModel)
    assert first.model_dump()["loss"] == 0.5
    assert second.loss_history == []
    assert second.metric_history == {}


def test_train_dashboard_snapshot_rejects_invalid_fields() -> None:
    with pytest.raises(ValidationError):
        TrainDashboardSnapshot(total_steps=0)

    with pytest.raises(ValidationError):
        TrainDashboardSnapshot(status="done")

    with pytest.raises(ValidationError):
        TrainDashboardSnapshot(metrics={"": 0.5})

    with pytest.raises(ValidationError):
        TrainDashboardSnapshot(unexpected=True)

    snapshot = TrainDashboardSnapshot()
    with pytest.raises(ValidationError):
        snapshot.current_step = 0


def _graph_cells(line: str) -> str:
    if "┤" in line:
        return line.split("┤", maxsplit=1)[1]

    return line.split("└", maxsplit=1)[1]


def _bar_cells(line: str) -> str:
    return line.split("[", maxsplit=1)[1].split("]", maxsplit=1)[0]
