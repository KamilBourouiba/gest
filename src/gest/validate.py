from __future__ import annotations

import json
from typing import Any

from gest.invariants import validate_invariants
from gest.schema_path import bundled_schema_path


def validate_document(doc: dict[str, Any]) -> list[str]:
    """
    Validate `doc` against the bundled JSON Schema.
    Returns a list of messages (empty if valid).
    """
    try:
        import jsonschema
    except ImportError:
        return ["jsonschema is not installed; pip install gest-ir[dev]"]

    schema_path = bundled_schema_path()
    if not schema_path.is_file():
        return [f"Schema not found: {schema_path}"]

    schema = json.loads(schema_path.read_text(encoding="utf-8"))
    validator = jsonschema.Draft202012Validator(schema)
    errors = sorted(validator.iter_errors(doc), key=lambda e: e.path)
    return [f"{'/'.join(str(p) for p in e.path)}: {e.message}" for e in errors]


def is_valid(doc: dict[str, Any]) -> bool:
    return len(validate_document(doc)) == 0


def validate_all(doc: dict[str, Any]) -> list[str]:
    """JSON Schema plus IR invariants (poses, strides, etc.)."""
    sch = validate_document(doc)
    inv = [f"invariant: {m}" for m in validate_invariants(doc)]
    return list(sch) + inv


def is_fully_valid(doc: dict[str, Any]) -> bool:
    msgs = validate_all(doc)
    sch = [m for m in msgs if not m.startswith("invariant:")]
    inv = [m for m in msgs if m.startswith("invariant:")]
    if sch and not (len(sch) == 1 and sch[0].startswith("jsonschema")):
        return False
    return len(inv) == 0
