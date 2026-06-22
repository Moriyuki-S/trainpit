from __future__ import annotations

import importlib.util
import subprocess
import sys
from pathlib import Path

import pytest


ROOT = Path(__file__).resolve().parents[1]


def test_custom_panels_example_imports_and_defines_panels() -> None:
    spec = importlib.util.spec_from_file_location(
        "custom_panels",
        ROOT / "examples" / "custom_panels.py",
    )
    assert spec is not None
    assert spec.loader is not None

    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)

    app = module.CustomPanelDashboardApp()

    assert [panel.id for panel in app.extra_panels] == [
        "run-config",
        "validation",
        "gpu",
    ]
    assert app.extra_panels[0].render(app.snapshot).startswith("epochs")
    assert app.extra_panels[1].render(app.snapshot) == "validation pending"
    assert app.extra_panels[2].render(app.snapshot) == "gpu warming up"


def test_torch_nn_example_runs() -> None:
    if importlib.util.find_spec("torch") is None:
        pytest.skip("torch is installed only with the examples dependency group")

    result = subprocess.run(
        [
            sys.executable,
            str(ROOT / "examples" / "torch_nn.py"),
            "--plain",
            "--epochs",
            "2",
            "--samples",
            "64",
            "--batch-size",
            "16",
        ],
        check=True,
        capture_output=True,
        text=True,
    )

    assert "Recorded 8 training updates" in result.stdout
    assert "Initial loss:" in result.stdout
    assert "Final loss:" in result.stdout
    assert "Final acc:" in result.stdout
