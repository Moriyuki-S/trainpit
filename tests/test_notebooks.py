from __future__ import annotations

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
TRAIN_TUTORIAL_NOTEBOOK = ROOT / "examples" / "train_tutorial.ipynb"


def test_train_tutorial_notebook_runs() -> None:
    notebook = json.loads(TRAIN_TUTORIAL_NOTEBOOK.read_text())
    namespace = {"__name__": "__notebook_test__"}

    for cell in notebook["cells"]:
        if cell["cell_type"] != "code":
            continue

        source = "".join(cell["source"])
        exec(compile(source, str(TRAIN_TUTORIAL_NOTEBOOK), "exec"), namespace)


def test_train_tutorial_notebook_uses_portable_kernel_metadata() -> None:
    notebook = json.loads(TRAIN_TUTORIAL_NOTEBOOK.read_text())

    assert notebook["metadata"]["kernelspec"] == {
        "display_name": "Python 3",
        "language": "python",
        "name": "python3",
    }

    for cell in notebook["cells"]:
        if cell["cell_type"] == "code":
            assert cell["outputs"] == []
