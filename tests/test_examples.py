from __future__ import annotations

import importlib.util
import subprocess
import sys
from pathlib import Path

import pytest


ROOT = Path(__file__).resolve().parents[1]


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
