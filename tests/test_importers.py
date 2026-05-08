from __future__ import annotations

from pathlib import Path

import pytest

from gest.document import load_json_path
from gest.importers import bvh_text_to_gest, mediapipe_json_to_gest, openxr_json_to_gest
from gest.sgm import compile_to_bytes
from gest.validate import validate_all


ROOT = Path(__file__).resolve().parents[1]
IMPORTS = ROOT / "examples" / "imports"


def _assert_valid_and_compilable(doc: dict) -> None:
    pytest.importorskip("jsonschema")
    errors = validate_all(doc)
    assert errors == [], errors
    assert len(compile_to_bytes(doc)) > 0


def test_mediapipe_import_sample():
    doc = mediapipe_json_to_gest(load_json_path(IMPORTS / "mediapipe_sample.json"))
    assert sorted(doc["channels"]) == ["gaze", "left_hand", "right_hand"]
    assert doc["channels"]["left_hand"]["joint_layout"] == "mediapipe_hands_landmarks_v1"
    _assert_valid_and_compilable(doc)


def test_openxr_import_sample():
    doc = openxr_json_to_gest(load_json_path(IMPORTS / "openxr_sample.json"))
    assert sorted(doc["channels"]) == ["right_hand"]
    assert doc["channels"]["right_hand"]["joint_layout"] == "openxr_hand_joint_set_v1"
    _assert_valid_and_compilable(doc)


def test_bvh_import_sample():
    text = (IMPORTS / "simple_sample.bvh").read_text(encoding="utf-8")
    doc = bvh_text_to_gest(text)
    assert sorted(doc["channels"]) == ["bvh_points"]
    assert doc["channels"]["bvh_points"]["joint_count"] == 2
    _assert_valid_and_compilable(doc)

