import pytest
from pydantic import BaseModel, ValidationError

from trainpit import TrainTracker, train
from trainpit._state import TrainState


def test_train_context_manager_updates_progress_state() -> None:
    with train(total_epochs=10, total_steps=500, label="experiment-001") as progress:
        progress.epoch(2)
        progress.step(
            128,
            loss=0.421,
            metrics={"acc": 0.884},
            learning_rate=0.0001,
        )
        progress.update_metrics({"f1": 0.76})
        progress.log("checkpoint saved")

        snapshot = progress.snapshot
        assert isinstance(progress, TrainTracker)
        assert isinstance(snapshot, BaseModel)
        assert snapshot.started is True
        assert snapshot.label == "experiment-001"
        assert snapshot.total_epochs == 10
        assert snapshot.total_steps == 500
        assert snapshot.current_epoch == 2
        assert snapshot.current_step == 128
        assert snapshot.loss == 0.421
        assert snapshot.metrics == {"acc": 0.884, "f1": 0.76}
        assert snapshot.learning_rate == 0.0001
        assert snapshot.event == "checkpoint saved"

    snapshot = progress.snapshot
    assert snapshot.finished is True
    assert snapshot.failed is False


def test_train_context_manager_records_failure_and_reraises() -> None:
    with pytest.raises(RuntimeError, match="boom") as exc_info:
        with train() as progress:
            progress.epoch(1)
            raise RuntimeError("boom")

    snapshot = progress.snapshot
    assert snapshot.finished is True
    assert snapshot.failed is True
    assert isinstance(snapshot.error, RuntimeError)
    assert str(snapshot.error) == str(exc_info.value)


def test_train_tracker_can_be_finished_without_context_manager() -> None:
    progress = train(total_steps=3)

    progress.start()
    progress.epoch(1)
    progress.step(1, loss=1)
    progress.finish()

    snapshot = progress.snapshot
    assert snapshot.started is True
    assert snapshot.finished is True
    assert snapshot.current_step == 1


def test_train_tracker_can_be_failed_without_context_manager() -> None:
    progress = train()
    error = RuntimeError("manual failure")

    progress.fail(error)

    snapshot = progress.snapshot
    assert snapshot.finished is True
    assert snapshot.failed is True
    assert isinstance(snapshot.error, RuntimeError)
    assert str(snapshot.error) == str(error)


def test_train_tracker_keeps_compatibility_aliases() -> None:
    progress = train(total_steps=2)

    progress.start()
    progress.step(1, loss=0.5, lr=0.001)
    progress.metrics({"acc": 0.9})
    progress.event("alias event")

    snapshot = progress.snapshot
    assert snapshot.learning_rate == 0.001
    assert snapshot.metrics == {"acc": 0.9}
    assert snapshot.event == "alias event"


def test_train_state_records_timing_timestamps() -> None:
    state = TrainState()

    state.start(now=10.0)
    state.set_epoch(1, now=11.0)
    state.set_step(2, loss=0.5, now=12.0)
    state.finish(now=15.0)

    assert state.started_at == 10.0
    assert state.updated_at == 15.0
    assert state.finished_at == 15.0


def test_train_tracker_rejects_learning_rate_alias_conflict() -> None:
    progress = train()

    with pytest.raises(ValueError, match="learning_rate or lr"):
        progress.step(1, learning_rate=0.1, lr=0.1)


def test_train_rejects_invalid_totals() -> None:
    with pytest.raises(ValueError, match="total_epochs"):
        train(total_epochs=0)

    with pytest.raises(TypeError, match="total_steps"):
        train(total_steps=1.5)  # type: ignore[arg-type]

    with pytest.raises(TypeError, match="total_steps"):
        train(total_steps=True)  # type: ignore[arg-type]


def test_train_state_rejects_invalid_pydantic_fields() -> None:
    with pytest.raises(ValidationError):
        TrainState(total_epochs=0)

    with pytest.raises(ValidationError):
        TrainState(phase="eval")

    state = TrainState()

    with pytest.raises(ValidationError):
        state.metrics = {"": 0.5}

    with pytest.raises(ValidationError):
        state.learning_rate = -0.1
