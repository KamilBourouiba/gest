from __future__ import annotations

import json
import math
import sys
from dataclasses import asdict
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from gest.sgm import compile_to_bytes  # noqa: E402
from gest.sgm_decode import decode_sgm_bytes, decoded_to_pose_timeline  # noqa: E402
from gest.sgm_roundtrip import gest_document_from_sgm_bytes  # noqa: E402
from gest.validate import validate_all  # noqa: E402


DEMO_DIR = ROOT / "demo"
OUT_DIR = DEMO_DIR / "out"
GEST_PATH = DEMO_DIR / "xr_dual_hand_arc.gest.json"
SGM_PATH = OUT_DIR / "xr_dual_hand_arc.sgm"
DUMP_PATH = OUT_DIR / "xr_dual_hand_arc.dump.json"
RECOVERED_PATH = OUT_DIR / "xr_dual_hand_arc.recovered.gest.json"


def _round3(v: float) -> float:
    return round(v, 3)


def _lerp(a: float, b: float, u: float) -> float:
    return a + (b - a) * u


def _unit(v: list[float]) -> list[float]:
    n = math.sqrt(sum(x * x for x in v))
    if n == 0:
        return [0.0, 0.0, 1.0]
    return [_round3(x / n) for x in v]


def _hand_values(root: tuple[float, float, float], spread: float) -> list[float]:
    x, y, z = root
    offsets = [
        (0.000, 0.000, 0.000),  # wrist / palm root
        (-0.045 * spread, 0.035, 0.020),  # thumb proxy
        (-0.018 * spread, 0.080, 0.012),  # index proxy
        (0.018 * spread, 0.082, 0.010),  # middle proxy
        (0.048 * spread, 0.060, 0.014),  # outer finger proxy
    ]
    values: list[float] = []
    for dx, dy, dz in offsets:
        values.extend([_round3(x + dx), _round3(y + dy), _round3(z + dz)])
    return values


def build_demo_document() -> dict[str, Any]:
    """
    Build a deterministic, non-semantic XR-style motion clip.

    The clip contains two simplified 5-point articulated hands and one gaze
    direction channel. No text labels describe intent or meaning; only motion,
    geometry, closed state indices, and time are encoded.
    """
    timeline: list[dict[str, Any]] = []
    frame_count = 9
    duration = 1.2

    for i in range(frame_count):
        u = i / (frame_count - 1)
        t = _round3(duration * u)
        arc = math.sin(math.pi * u)

        left_root = (
            _lerp(-0.30, -0.12, u),
            1.12 + 0.06 * arc,
            _lerp(0.35, 0.27, u),
        )
        right_root = (
            _lerp(0.34, 0.06, u),
            1.08 + 0.14 * arc,
            _lerp(0.48, 0.26, u),
        )

        left_spread = _lerp(1.00, 0.62, u)
        right_spread = _lerp(0.72, 1.05, u)

        midpoint = [
            (left_root[0] + right_root[0]) / 2,
            (left_root[1] + right_root[1]) / 2,
            (left_root[2] + right_root[2]) / 2,
        ]
        head = [0.0, 1.58, 0.0]
        gaze = _unit([midpoint[j] - head[j] for j in range(3)])

        state = 0 if u < 0.34 else 1 if u < 0.67 else 2
        timeline.append(
            {
                "t": t,
                "pose": {
                    "left_hand": {
                        "joints": {
                            "format": "raw_float32",
                            "values": _hand_values(left_root, left_spread),
                        },
                        "state_index": state,
                    },
                    "right_hand": {
                        "joints": {
                            "format": "raw_float32",
                            "values": _hand_values(right_root, right_spread),
                        },
                        "state_index": state,
                    },
                    "gaze": {"dir": gaze},
                },
            }
        )

    return {
        "version": "0.2",
        "profile": "full",
        "fps": 60,
        "time_base": "seconds",
        "units": "meters",
        "coordinate_system": {
            "handedness": "right",
            "up": "+Y",
            "forward": "+Z",
        },
        "capabilities": ["hierarchy", "demo_clip", "sgm_roundtrip"],
        "space": {
            "anchors": {
                "world": {"t": [0.0, 0.0, 0.0], "q": [0.0, 0.0, 0.0, 1.0]},
                "chest": {
                    "parent": "world",
                    "t": [0.0, 1.05, 0.0],
                    "q": [0.0, 0.0, 0.0, 1.0],
                },
                "head": {
                    "parent": "chest",
                    "t": [0.0, 0.53, 0.0],
                    "q": [0.0, 0.0, 0.0, 1.0],
                },
            },
            "named_points": {
                "work_left": {"parent": "chest", "local": [-0.25, 0.15, 0.35]},
                "work_mid": {"parent": "chest", "local": [0.0, 0.20, 0.30]},
                "work_right": {"parent": "chest", "local": [0.25, 0.15, 0.35]},
            },
        },
        "channels": {
            "left_hand": {
                "type": "articulated",
                "parent": "chest",
                "joint_count": 5,
                "joint_value_stride": 3,
                "joint_layout": "demo_five_point_hand_v1",
                "state_enum": ["shape_0", "shape_1", "shape_2"],
            },
            "right_hand": {
                "type": "articulated",
                "parent": "chest",
                "joint_count": 5,
                "joint_value_stride": 3,
                "joint_layout": "demo_five_point_hand_v1",
                "state_enum": ["shape_0", "shape_1", "shape_2"],
            },
            "gaze": {
                "type": "direction",
                "parent": "head",
                "representation": "unit_vector",
            },
        },
        "interpolation_defaults": {
            "translation": "cubic_hermite",
            "rotation": "slerp",
            "scalar": "linear",
        },
        "timeline": timeline,
        "producer_notes": {
            "demo": "XR-style dual-hand arc; producer_notes are off the SGPU path.",
        },
    }


def _write_json(path: Path, data: Any) -> None:
    path.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")


def run_demo() -> int:
    OUT_DIR.mkdir(parents=True, exist_ok=True)

    doc = build_demo_document()
    _write_json(GEST_PATH, doc)

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
    print(f"- .sgm bytecode: {SGM_PATH.relative_to(ROOT)} ({len(blob)} bytes)")
    print(f"- decoded dump: {DUMP_PATH.relative_to(ROOT)}")
    print(f"- recovered draft .gest: {RECOVERED_PATH.relative_to(ROOT)}")
    print(f"- frames: {len(doc['timeline'])}")
    print(f"- channels: {', '.join(sorted(doc['channels']))}")
    return 0


if __name__ == "__main__":
    raise SystemExit(run_demo())
