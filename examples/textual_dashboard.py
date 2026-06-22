"""Run a demo trainpit Textual dashboard."""

from __future__ import annotations

import math

from trainpit.tui import TrainDashboardApp, TrainDashboardSnapshot

TOTAL_EPOCHS = 3
TOTAL_STEPS = 24


class DemoTrainDashboardApp(TrainDashboardApp):
    """Self-updating dashboard demo."""

    def __init__(self) -> None:
        super().__init__(
            TrainDashboardSnapshot(
                label="textual-demo",
                total_epochs=TOTAL_EPOCHS,
                total_steps=TOTAL_STEPS,
            )
        )
        self._absolute_step = 0

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
        learning_rate = 0.001 * (1 - 0.75 * ratio)

        self.snapshot.current_epoch = epoch
        self.snapshot.update_step(
            step,
            loss=loss,
            metrics={"acc": accuracy},
            learning_rate=learning_rate,
        )
        self.snapshot.event = f"updated step {self._absolute_step}"

        if self._absolute_step >= TOTAL_EPOCHS * TOTAL_STEPS:
            self.snapshot.mark_finished()
            self.snapshot.event = "training complete"

        self.refresh_dashboard()


def main() -> None:
    DemoTrainDashboardApp().run()


if __name__ == "__main__":
    main()
