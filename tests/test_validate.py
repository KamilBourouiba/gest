from pathlib import Path

import pytest

from gest.document import load_json_path
from gest.validate import is_fully_valid, is_valid, validate_all, validate_document

ROOT = Path(__file__).resolve().parents[1]
EXAMPLE = ROOT / "examples" / "minimal.gest.json"


def test_minimal_example_validates():
    doc = load_json_path(EXAMPLE)
    errors = validate_document(doc)
    jsonschema = pytest.importorskip("jsonschema")
    assert jsonschema is not None
    assert errors == [], errors


def test_is_valid():
    pytest.importorskip("jsonschema")
    doc = load_json_path(EXAMPLE)
    assert is_valid(doc) is True


def test_validate_all_minimal():
    pytest.importorskip("jsonschema")
    doc = load_json_path(EXAMPLE)
    assert validate_all(doc) == []
    assert is_fully_valid(doc) is True
