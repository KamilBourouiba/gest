"""Compile .gest -> .sgm -> draft .gest and validate."""

from __future__ import annotations

from pathlib import Path

import pytest

from gest.document import load_json_path
from gest.sgm import compile_to_bytes
from gest.sgm_roundtrip import gest_document_from_sgm_bytes
from gest.validate import validate_all

ROOT = Path(__file__).resolve().parents[1]
EXAMPLE = ROOT / "examples" / "minimal.gest.json"


def test_gest_sgm_gest_validate_all():
    pytest.importorskip("jsonschema")
    orig = load_json_path(EXAMPLE)
    blob = compile_to_bytes(orig)
    draft = gest_document_from_sgm_bytes(blob)
    errs = validate_all(draft)
    assert errs == [], errs


def test_gest_sgm_gest_timeline_matches():
    pytest.importorskip("jsonschema")
    orig = load_json_path(EXAMPLE)
    blob = compile_to_bytes(orig)
    draft = gest_document_from_sgm_bytes(blob)
    assert len(draft["timeline"]) == len(orig["timeline"])
    for a, b in zip(draft["timeline"], orig["timeline"]):
        assert a["t"] == pytest.approx(b["t"])
        assert set(a["pose"]) == set(b["pose"])
