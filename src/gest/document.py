from __future__ import annotations

import json
from pathlib import Path
from typing import Any


def load_json_path(path: str | Path) -> dict[str, Any]:
    """Load a .gest document from a path (UTF-8 JSON)."""
    p = Path(path)
    text = p.read_text(encoding="utf-8")
    data = json.loads(text)
    if not isinstance(data, dict):
        raise ValueError("JSON root must be an object.")
    return data


def load_json_bytes(data: bytes) -> dict[str, Any]:
    """Parse JSON bytes (UTF-8)."""
    data_obj = json.loads(data.decode("utf-8"))
    if not isinstance(data_obj, dict):
        raise ValueError("JSON root must be an object.")
    return data_obj


def load_yaml_path(path: str | Path) -> dict[str, Any]:
    """Load a .gest YAML document (same key tree as JSON)."""
    try:
        import yaml
    except ImportError as e:
        raise ImportError(
            "PyYAML is required for YAML files: pip install gest-ir[yaml]"
        ) from e
    p = Path(path)
    text = p.read_text(encoding="utf-8")
    try:
        data = yaml.safe_load(text)
    except yaml.YAMLError as e:
        raise ValueError(f"Invalid YAML: {e}") from e
    if data is None:
        raise ValueError("YAML document is empty.")
    if not isinstance(data, dict):
        raise ValueError("YAML root must be a mapping (object).")
    return data


def load_path(path: str | Path) -> dict[str, Any]:
    """Load `.json`, `.yaml`, or `.yml` based on suffix."""
    p = Path(path)
    suf = p.suffix.lower()
    if suf in (".yaml", ".yml"):
        return load_yaml_path(p)
    if suf in (".json", ".gest", ""):
        return load_json_path(p)
    return load_json_path(p)
