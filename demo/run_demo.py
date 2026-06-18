from __future__ import annotations

import json
import sys
from dataclasses import asdict
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
for path in (ROOT, SRC):
    s = str(path)
    if s not in sys.path:
        sys.path.insert(0, s)

from demo.showcase_clips import build_xr_pinch_grasp_document  # noqa: E402
from gest.sgm import compile_to_bytes  # noqa: E402
from gest.sgm_decode import decode_sgm_bytes, decoded_to_pose_timeline  # noqa: E402
from gest.sgm_roundtrip import gest_document_from_sgm_bytes  # noqa: E402
from gest.validate import validate_all  # noqa: E402


DEMO_DIR = ROOT / "demo"
OUT_DIR = DEMO_DIR / "out"
GEST_PATH = DEMO_DIR / "xr_pinch_grasp.gest.json"
LEGACY_GEST_PATH = DEMO_DIR / "xr_dual_hand_arc.gest.json"
SGM_PATH = OUT_DIR / "xr_pinch_grasp.sgm"
LEGACY_SGM_PATH = OUT_DIR / "xr_dual_hand_arc.sgm"
DUMP_PATH = OUT_DIR / "xr_pinch_grasp.dump.json"
RECOVERED_PATH = OUT_DIR / "xr_pinch_grasp.recovered.gest.json"


def build_demo_document() -> dict[str, Any]:
    """Primary flagship clip used by comparison stats and legacy viewers."""
    return build_xr_pinch_grasp_document()


def _write_json(path: Path, data: Any) -> None:
    path.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")


def run_demo() -> int:
    OUT_DIR.mkdir(parents=True, exist_ok=True)

    doc = build_demo_document()
    _write_json(GEST_PATH, doc)
    _write_json(LEGACY_GEST_PATH, doc)

    errors = validate_all(doc)
    fatal = [e for e in errors if not e.startswith("jsonschema")]
    if fatal:
        for err in fatal:
            print(f"validation: {err}", file=sys.stderr)
        return 1
    if errors:
        for err in errors:
            print(f"warning: {err}", file=sys.stderr)

    blob = compile_to_bytes(doc)
    SGM_PATH.write_bytes(blob)
    LEGACY_SGM_PATH.write_bytes(blob)

    decoded = decode_sgm_bytes(blob)
    dump = {
        "format_version": decoded.format_version,
        "fps": decoded.fps,
        "channels": [asdict(c) for c in decoded.channels],
        "timeline": decoded_to_pose_timeline(decoded),
    }
    _write_json(DUMP_PATH, dump)
    _write_json(RECOVERED_PATH, gest_document_from_sgm_bytes(blob))

    print("Demo complete")
    print(f"- .gest source: {GEST_PATH.relative_to(ROOT)}")
    print(f"- legacy alias: {LEGACY_GEST_PATH.relative_to(ROOT)}")
    print(f"- .sgm bytecode: {SGM_PATH.relative_to(ROOT)} ({len(blob)} bytes)")
    print(f"- decoded dump: {DUMP_PATH.relative_to(ROOT)}")
    print(f"- recovered draft .gest: {RECOVERED_PATH.relative_to(ROOT)}")
    print(f"- frames: {len(doc['timeline'])}")
    print(f"- channels: {', '.join(sorted(doc['channels']))}")
    return 0


if __name__ == "__main__":
    raise SystemExit(run_demo())
