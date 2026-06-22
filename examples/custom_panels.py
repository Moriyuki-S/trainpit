"""Run a trainpit Textual dashboard with user-defined panels."""

from __future__ import annotations

import math

from trainpit.tui import DashboardPanel, TrainDashboardApp, TrainDashboardSnapshot

TOTAL_EPOCHS = 3
TOTAL_STEPS = 24
BATCH_SIZE = 32
SEED = 7


class CustomPanelDashboardApp(TrainDashboardApp):
    """Self-updating dashboard demo with custom panels."""

    def __init__(self) -> None:
        self._absolute_step = 0
        self._gpu_memory_mb = 0.0
        self._gpu_util_percent = 0.0
        self._gpu_temperature_c = 0.0

        super().__init__(
            TrainDashboardSnapshot(
                label="custom-panel-demo",
                total_epochs=TOTAL_EPOCHS,
                total_steps=TOTAL_STEPS,
                event="training ready",
            ),
            extra_panels=[
                DashboardPanel(
                    id="run-config",
                    title="RUN CONFIG",
                    slot="top",
                    render=self._render_run_config,
                ),
                DashboardPanel(
                    id="validation",
                    title="VALIDATION",
                    slot="bottom",
                    render=self._render_validation,
                ),
                DashboardPanel(
                    id="gpu",
                    title="GPU",
                    slot="side",
                    render=self._render_gpu,
                ),
            ],
        )

    def on_mount(self) -> None:
        super().on_mount()
        self.set_interval(0.2, self._advance)

    def _advance(self) -> None:
        if self.snapshot.status == "finished":
            return

        self._absolute_step += 1
        epoch = min((self._absolute_step - 1) // TOTAL_STEPS + 1, TOTAL_EPOCHS)
        step = (self._absolute_step - 1) % TOTAL_STEPS + 1
        ratio = self._absolute_step / (TOTAL_EPOCHS * TOTAL_STEPS)

        loss = 1.1 * math.exp(-2.2 * ratio) + 0.02 * math.sin(step / 2)
        accuracy = 0.48 + 0.46 * ratio
        validation_loss = loss * (1.07 + 0.02 * math.sin(epoch))
        validation_accuracy = max(0.0, accuracy - 0.03 + 0.01 * math.cos(step / 4))
        learning_rate = 0.001 * (1 - 0.75 * ratio)

        self._gpu_memory_mb = 1800 + 520 * ratio + 40 * math.sin(step / 3)
        self._gpu_util_percent = 58 + 34 * ratio + 4 * math.sin(step / 2)
        self._gpu_temperature_c = 54 + 13 * ratio + 2 * math.sin(step / 5)

        self.snapshot.current_epoch = epoch
        self.snapshot.update_step(
            step,
            loss=loss,
            metrics={
                "acc": accuracy,
                "val_loss": validation_loss,
                "val_acc": validation_accuracy,
            },
            learning_rate=learning_rate,
        )
        self.snapshot.event = f"epoch {epoch} step {step}/{TOTAL_STEPS}"

        if self._absolute_step >= TOTAL_EPOCHS * TOTAL_STEPS:
            self.snapshot.mark_finished()
            self.snapshot.event = "training complete"

        self.refresh_dashboard()

    def _render_run_config(self, snapshot: TrainDashboardSnapshot) -> str:
        return "\n".join(
            [
                f"epochs  {snapshot.total_epochs or '-'}",
                f"steps   {snapshot.total_steps or '-'}",
                f"batch   {BATCH_SIZE}",
                f"seed    {SEED}",
            ]
        )

    def _render_validation(self, snapshot: TrainDashboardSnapshot) -> str:
        validation_loss = snapshot.metrics.get("val_loss")
        validation_accuracy = snapshot.metrics.get("val_acc")
        if validation_loss is None or validation_accuracy is None:
            return "validation pending"

        return "\n".join(
            [
                f"val loss {_format_panel_value(validation_loss)}",
                f"val acc  {validation_accuracy * 100:6.2f}%",
            ]
        )

    def _render_gpu(self, snapshot: TrainDashboardSnapshot) -> str:
        del snapshot
        if self._absolute_step == 0:
            return "gpu warming up"

        return "\n".join(
            [
                f"mem  {self._gpu_memory_mb:7.0f} MB",
                f"util {self._gpu_util_percent:7.1f}%",
                f"temp {self._gpu_temperature_c:7.1f} C",
            ]
        )


def _format_panel_value(value: float) -> str:
    if abs(value) >= 1000:
        return f"{value:.3e}"

    return f"{value:.4f}"


def main() -> None:
    CustomPanelDashboardApp().run()


if __name__ == "__main__":
    main()
