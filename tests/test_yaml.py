from pathlib import Path

import pytest

from gest.document import load_path, load_yaml_path
from gest.validate import is_fully_valid

ROOT = Path(__file__).resolve().parents[1]
YAML_EX = ROOT / "examples" / "minimal.gest.yaml"


def test_load_yaml_example():
    pytest.importorskip("yaml")
    pytest.importorskip("jsonschema")
    doc = load_yaml_path(YAML_EX)
    assert doc["version"] == "0.2"
    assert is_fully_valid(doc)


def test_load_path_dispatches_suffix():
    pytest.importorskip("yaml")
    pytest.importorskip("jsonschema")
    doc = load_path(YAML_EX)
    assert doc["fps"] == 60
