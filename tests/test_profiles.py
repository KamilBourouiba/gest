from __future__ import annotations

from pathlib import Path

import pytest

from gest.document import load_json_path
from gest.profiles import get_profile, normalize_profile, profile_names
from gest.validate import validate_all


ROOT = Path(__file__).resolve().parents[1]
PROFILE_EXAMPLES = ROOT / "examples" / "profiles"


def test_profile_registry_contains_canonical_profiles():
    assert profile_names() == ("full", "rt", "cmp", "neural")
    assert normalize_profile("neural_bundle") == "neural"
    assert get_profile("rt").file_suffix == ".gest.rt.json"


@pytest.mark.parametrize("path", sorted(PROFILE_EXAMPLES.glob("*.gest.json")))
def test_profile_examples_validate(path: Path):
    pytest.importorskip("jsonschema")
    doc = load_json_path(path)
    errors = validate_all(doc)
    assert errors == [], (path, errors)

