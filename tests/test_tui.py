from __future__ import annotations

import asyncio
from collections.abc import Sequence

import pytest
from pydantic import BaseModel, ValidationError
from textual.widgets import Static

from trainpit.tui import (
    DashboardPanel,
    TrainDashboardApp,
    TrainDashboardSnapshot,
    _format_curves,
    _format_metrics,
    _format_progress,
    _format_timing,
    line_graph,
    scatter_graph,
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


def test_train_dashboard_app_renders_custom_panels() -> None:
    async def run_app() -> None:
        snapshot = TrainDashboardSnapshot(label="custom-run")
        snapshot.update_step(1, metrics={"gpu_mem": 128.0})
        app = TrainDashboardApp(
            snapshot,
            extra_panels=[
                DashboardPanel(
                    id="gpu",
                    title="GPU",
                    slot="side",
                    render=lambda value: (
                        f"gpu {value.metrics.get('gpu_mem', 0.0):.0f} MB"
                    ),
                ),
                DashboardPanel(
                    id="validation",
                    title="VALIDATION",
                    slot="bottom",
                    render=lambda value: f"status {value.status}",
                ),
            ],
        )

        async with app.run_test(size=(120, 34)) as pilot:
            await pilot.pause()

            assert _static_text(app, "#custom-gpu") == "gpu 128 MB"
            assert _static_text(app, "#custom-validation") == "status running"

            snapshot.update_step(2, metrics={"gpu_mem": 256.0})
            app.update_snapshot(snapshot)
            await pilot.pause()

            assert _static_text(app, "#custom-gpu") == "gpu 256 MB"

    asyncio.run(run_app())


def test_dashboard_panel_rejects_invalid_values() -> None:
    with pytest.raises(ValueError, match="panel id"):
        DashboardPanel(id="bad id", title="BAD", render=lambda snapshot: "")

    with pytest.raises(ValueError, match="panel title"):
        DashboardPanel(id="bad-title", title="", render=lambda snapshot: "")

    with pytest.raises(TypeError, match="panel render"):
        DashboardPanel(id="bad-render", title="BAD", render="not callable")  # type: ignore[arg-type]

    with pytest.raises(ValueError, match="panel slot"):
        DashboardPanel(
            id="bad-slot",
            title="BAD",
            slot="middle",  # type: ignore[arg-type]
            render=lambda snapshot: "",
        )


def test_train_dashboard_app_rejects_duplicate_custom_panel_ids() -> None:
    panel = DashboardPanel(id="gpu", title="GPU", render=lambda snapshot: "")

    with pytest.raises(ValueError, match="duplicate panel id"):
        TrainDashboardApp(extra_panels=[panel, panel])


def test_train_dashboard_app_rejects_invalid_custom_panel_objects() -> None:
    with pytest.raises(TypeError, match="DashboardPanel"):
        TrainDashboardApp(extra_panels=["not a panel"])  # type: ignore[list-item]


def test_train_dashboard_app_rejects_invalid_graph_renderer() -> None:
    with pytest.raises(TypeError, match="graph_renderer"):
        TrainDashboardApp(graph_renderer="not callable")  # type: ignore[arg-type]


def test_learning_curve_uses_braille_line_graph_by_default() -> None:
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
    assert any(cells[0] in braille_characters for cells in graph_cells)
    assert all(cells[-1] == " " for cells in graph_cells)
    assert "•" not in graph_text
    assert "·" not in graph_text
    assert "█" not in graph_text
    assert "▓" not in graph_text


def test_learning_curve_can_use_scatter_graph_renderer() -> None:
    snapshot = TrainDashboardSnapshot()

    for step in range(60):
        snapshot.update_step(step + 1, loss=1.0 / (step + 1))

    line_text = _format_curves(snapshot, graph_renderer=line_graph)
    scatter_text = _format_curves(snapshot, graph_renderer=scatter_graph)
    graph_lines = scatter_text.splitlines()[1:8]
    graph_text = "\n".join(_graph_cells(line) for line in graph_lines)
    graph_characters = [character for character in graph_text if character != "\n"]

    assert scatter_text != line_text
    assert all(
        _braille_dot_count(character) <= 2
        for character in graph_characters
        if character != " "
    )


def test_learning_curve_accepts_custom_graph_renderer() -> None:
    snapshot = TrainDashboardSnapshot()

    for step in range(3):
        snapshot.update_step(step + 1, loss=1.0 / (step + 1))

    def marker_graph(values: Sequence[float], width: int, height: int) -> list[str]:
        return [f"custom n={len(values)} width={width} height={height}"]

    curve_text = _format_curves(snapshot, width=12, graph_renderer=marker_graph)

    assert "custom n=3 width=12 height=7" in curve_text


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


def test_timing_panel_shows_elapsed_rate_eta_and_last_update_age() -> None:
    snapshot = TrainDashboardSnapshot(
        total_epochs=2,
        total_steps=5,
        current_epoch=1,
        started_at=100.0,
    )
    snapshot.update_step(4, loss=0.5, now=112.0)

    timing_text = _format_timing(snapshot, now=115.0)

    assert "elapsed 00:00:15" in timing_text
    assert "step/s  0.33" in timing_text
    assert "eta     00:00:18" in timing_text
    assert "last    00:00:03" in timing_text


def test_timing_panel_reports_unknown_values_until_history_exists() -> None:
    snapshot = TrainDashboardSnapshot()

    assert _format_timing(snapshot) == (
        "elapsed --:--:--\nstep/s  --\neta     --:--:--\nlast    --:--:--"
    )


def test_dashboard_snapshot_records_terminal_timestamp() -> None:
    snapshot = TrainDashboardSnapshot()
    snapshot.update_step(1, loss=0.5, now=10.0)
    snapshot.mark_finished(now=15.0)

    assert snapshot.status == "finished"
    assert snapshot.started_at == 10.0
    assert snapshot.updated_at == 15.0
    assert snapshot.finished_at == 15.0
    assert "elapsed 00:00:05" in _format_timing(snapshot, now=20.0)
    assert "eta     00:00:00" in _format_timing(snapshot, now=20.0)


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


def _braille_dot_count(character: str) -> int:
    return bin(ord(character) - 0x2800).count("1")
