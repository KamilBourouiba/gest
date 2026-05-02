from pathlib import Path

import pytest

from gest.document import load_json_path
from gest.sgm import compile_to_bytes
from gest.sgm_constants import MAGIC, OP_END

ROOT = Path(__file__).resolve().parents[1]
EXAMPLE = ROOT / "examples" / "minimal.gest.json"


def test_compile_minimal():
    pytest.importorskip("jsonschema")
    doc = load_json_path(EXAMPLE)
    b = compile_to_bytes(doc)
    assert b[:4] == MAGIC
    assert b[-1] == OP_END
    assert len(b) > 40


def test_compile_rejects_blob_ref():
    doc = load_json_path(EXAMPLE)
    doc = dict(doc)
    doc["timeline"] = [
        {
            "t": 0,
            "pose": {
                "right_hand": {"joints": {"blob_ref": 1}},
                "gaze": {"dir": [0, 0, 1]},
            },
        }
    ]
    from gest.sgm import GestCompileError

    with pytest.raises(GestCompileError):
        compile_to_bytes(doc)
