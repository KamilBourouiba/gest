from __future__ import annotations

from pathlib import Path


def bundled_schema_path() -> Path:
    """Path to gest-0.2.schema.json (source checkout or wheel with force-include)."""
    here = Path(__file__).resolve().parent
    # Checkout: .../gest/src/gest -> repo root = parent.parent
    repo_root = here.parent.parent
    repo_schema = repo_root / "schema" / "gest-0.2.schema.json"
    if repo_schema.is_file():
        return repo_schema
    wheel = here / "schemas" / "gest-0.2.schema.json"
    return wheel
