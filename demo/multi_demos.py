from __future__ import annotations

import csv
import gzip
import io
import json
import math
import sys
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
for path in (ROOT, SRC):
    s = str(path)
    if s not in sys.path:
        sys.path.insert(0, s)

from demo.run_demo import build_demo_document  # noqa: E402
from gest.sgm import compile_to_bytes  # noqa: E402
from gest.sgm_decode import decode_sgm_bytes  # noqa: E402
from gest.validate import validate_all  # noqa: E402


GENERATED_DIR = ROOT / "demo" / "generated"
OUT_DIR = ROOT / "demo" / "out"
DOCS_PATH = ROOT / "docs" / "multi-demo-stats.md"
JSON_PATH = OUT_DIR / "multi-demo-stats.json"


@dataclass(frozen=True)
class DemoCase:
    slug: str
    title: str
    real_life_case: str
    doc: dict[str, Any]


def _round3(v: float) -> float:
    return round(v, 3)


def _unit(v: list[float]) -> list[float]:
    n = math.sqrt(sum(x * x for x in v))
    if n == 0:
        return [0.0, 0.0, 1.0]
    return [_round3(x / n) for x in v]


def _hand_points(root: tuple[float, float, float], count: int, spread: float) -> list[float]:
    x, y, z = root
    values: list[float] = []
    for i in range(count):
        angle = (i / max(1, count - 1) - 0.5) * math.pi * 0.55
        radius = 0.025 + i * 0.012
        values.extend(
            [
                _round3(x + math.sin(angle) * radius * spread),
                _round3(y + 0.035 * i),
                _round3(z + math.cos(angle) * radius * 0.35),
            ]
        )
    return values


def _base_doc(title_capability: str, fps: int = 60) -> dict[str, Any]:
    return {
        "version": "0.2",
        "profile": "full",
        "fps": fps,
        "time_base": "seconds",
        "units": "meters",
        "coordinate_system": {
            "handedness": "right",
            "up": "+Y",
            "forward": "+Z",
        },
        "capabilities": ["hierarchy", title_capability],
        "space": {
            "anchors": {
                "world": {"t": [0.0, 0.0, 0.0], "q": [0.0, 0.0, 0.0, 1.0]},
                "chest": {"parent": "world", "t": [0.0, 1.05, 0.0], "q": [0.0, 0.0, 0.0, 1.0]},
                "head": {"parent": "chest", "t": [0.0, 0.53, 0.0], "q": [0.0, 0.0, 0.0, 1.0]},
            }
        },
    }


def build_robot_teleop_demo() -> DemoCase:
    doc = _base_doc("robot_teleop_demo", fps=90)
    doc["channels"] = {
        "right_hand": {
            "type": "articulated",
            "parent": "chest",
            "joint_count": 4,
            "joint_value_stride": 3,
            "joint_layout": "demo_robot_gripper_proxy_v1",
            "state_enum": ["shape_0", "shape_1", "shape_2"],
        },
        "gaze": {"type": "direction", "parent": "head", "representation": "unit_vector"},
    }
    timeline: list[dict[str, Any]] = []
    for i in range(14):
        u = i / 13
        root = (
            _round3(0.35 - 0.42 * u),
            _round3(1.0 + 0.22 * math.sin(math.pi * u)),
            _round3(0.55 - 0.30 * u),
        )
        target = [-0.10, 1.12, 0.28]
        gaze = _unit([target[0], target[1] - 1.58, target[2]])
        timeline.append(
            {
                "t": _round3(u * 1.6),
                "pose": {
                    "right_hand": {
                        "joints": {"format": "raw_float32", "values": _hand_points(root, 4, 0.8 + 0.4 * u)},
                        "state_index": 0 if u < 0.45 else 1 if u < 0.8 else 2,
                    },
                    "gaze": {"dir": gaze},
                },
            }
        )
    doc["timeline"] = timeline
    return DemoCase(
        slug="robot_teleop_reach",
        title="Robot teleoperation reach",
        real_life_case="A remote operator guides a gripper-like end effector toward a target while gaze stays locked on the workspace.",
        doc=doc,
    )


def build_rehab_symmetry_demo() -> DemoCase:
    doc = _base_doc("rehab_symmetry_demo", fps=60)
    doc["channels"] = {
        "left_hand": {
            "type": "articulated",
            "parent": "chest",
            "joint_count": 6,
            "joint_value_stride": 3,
            "joint_layout": "demo_rehab_six_point_hand_v1",
            "state_enum": ["shape_0", "shape_1"],
        },
        "right_hand": {
            "type": "articulated",
            "parent": "chest",
            "joint_count": 6,
            "joint_value_stride": 3,
            "joint_layout": "demo_rehab_six_point_hand_v1",
            "state_enum": ["shape_0", "shape_1"],
        },
        "gaze": {"type": "direction", "parent": "head", "representation": "unit_vector"},
    }
    timeline: list[dict[str, Any]] = []
    for i in range(20):
        u = i / 19
        wave = math.sin(math.tau * u)
        lift = 0.10 + 0.12 * abs(wave)
        left_root = (-0.30 + 0.12 * wave, 1.02 + lift, 0.38)
        right_root = (0.30 - 0.12 * wave, 1.02 + lift * 0.92, 0.38)
        timeline.append(
            {
                "t": _round3(u * 2.2),
                "pose": {
                    "left_hand": {
                        "joints": {"format": "raw_float32", "values": _hand_points(left_root, 6, 0.9)},
                        "state_index": 0 if wave >= 0 else 1,
                    },
                    "right_hand": {
                        "joints": {"format": "raw_float32", "values": _hand_points(right_root, 6, 0.9)},
                        "state_index": 0 if wave >= 0 else 1,
                    },
                    "gaze": {"dir": _unit([0.0, -0.42, 0.42])},
                },
            }
        )
    doc["timeline"] = timeline
    return DemoCase(
        slug="rehab_symmetry_loop",
        title="Rehabilitation symmetry loop",
        real_life_case="A practice session records bilateral hand movement quality without storing any natural-language instruction or patient notes.",
        doc=doc,
    )


def build_dataset_microclip_demo() -> DemoCase:
    doc = _base_doc("dataset_microclip_demo", fps=30)
    doc["channels"] = {
        "left_hand": {
            "type": "articulated",
            "parent": "chest",
            "joint_count": 3,
            "joint_value_stride": 7,
            "joint_layout": "demo_dataset_pose7_v1",
            "state_enum": ["shape_0", "shape_1", "shape_2"],
        },
        "right_hand": {
            "type": "articulated",
            "parent": "chest",
            "joint_count": 3,
            "joint_value_stride": 7,
            "joint_layout": "demo_dataset_pose7_v1",
            "state_enum": ["shape_0", "shape_1", "shape_2"],
        },
        "gaze": {"type": "direction", "parent": "head", "representation": "unit_vector"},
    }
    timeline: list[dict[str, Any]] = []
    for i in range(8):
        u = i / 7
        left_xyz = _hand_points((-0.22 + 0.10 * u, 1.12, 0.32 + 0.05 * u), 3, 1.0)
        right_xyz = _hand_points((0.22 - 0.08 * u, 1.08 + 0.08 * u, 0.36), 3, 1.0)
        def pose7(vals: list[float]) -> list[float]:
            out: list[float] = []
            for idx in range(0, len(vals), 3):
                out.extend(vals[idx : idx + 3] + [0.0, 0.0, 0.0, 1.0])
            return out
        timeline.append(
            {
                "t": _round3(u * 0.7),
                "pose": {
                    "left_hand": {
                        "joints": {"format": "raw_float32", "values": pose7(left_xyz)},
                        "state_index": i % 3,
                    },
                    "right_hand": {
                        "joints": {"format": "raw_float32", "values": pose7(right_xyz)},
                        "state_index": (i + 1) % 3,
                    },
                    "gaze": {"dir": _unit([0.05 * math.sin(u * math.pi), -0.35, 0.45])},
                },
            }
        )
    doc["timeline"] = timeline
    return DemoCase(
        slug="dataset_pose7_microclip",
        title="Dataset pose7 microclip",
        real_life_case="A compact benchmark clip preserves joint translations and quaternions while keeping gloss/meaning labels in a separate approved manifest.",
        doc=doc,
    )


def demo_cases() -> list[DemoCase]:
    xr = DemoCase(
        slug="xr_dual_hand_arc",
        title="XR dual-hand arc",
        real_life_case="A headset or depth-camera clip records coordinated hand motion and gaze for QA replay.",
        doc=build_demo_document(),
    )
    return [xr, build_robot_teleop_demo(), build_rehab_symmetry_demo(), build_dataset_microclip_demo()]


def _compact_json_bytes(obj: Any) -> bytes:
    return json.dumps(obj, separators=(",", ":"), sort_keys=True).encode("utf-8")


def _pretty_json_bytes(obj: Any) -> bytes:
    return (json.dumps(obj, indent=2, sort_keys=True) + "\n").encode("utf-8")


def _yaml_bytes(obj: Any) -> bytes:
    try:
        import yaml
    except ImportError:
        return b""
    return yaml.safe_dump(obj, sort_keys=True).encode("utf-8")


def _iter_articulated_samples(doc: dict[str, Any]) -> list[tuple[float, str, int, list[float], int | None]]:
    out: list[tuple[float, str, int, list[float], int | None]] = []
    channels = doc["channels"]
    for frame in doc["timeline"]:
        for name, spec in channels.items():
            if spec.get("type") != "articulated":
                continue
            block = frame["pose"].get(name)
            if not isinstance(block, dict):
                continue
            vals = block.get("joints", {}).get("values")
            if not isinstance(vals, list):
                continue
            stride = int(spec.get("joint_value_stride", 3))
            for idx in range(0, len(vals), stride):
                out.append((float(frame["t"]), name, idx // stride, vals[idx : idx + stride], block.get("state_index")))
    return out


def _iter_direction_samples(doc: dict[str, Any]) -> list[tuple[float, str, list[float]]]:
    out: list[tuple[float, str, list[float]]] = []
    for frame in doc["timeline"]:
        for name, spec in doc["channels"].items():
            if spec.get("type") != "direction":
                continue
            block = frame["pose"].get(name)
            if isinstance(block, dict) and isinstance(block.get("dir"), list):
                out.append((float(frame["t"]), name, block["dir"]))
    return out


def _csv_bytes(doc: dict[str, Any]) -> bytes:
    sio = io.StringIO()
    writer = csv.writer(sio)
    writer.writerow(["t", "channel", "sample_index", "v0", "v1", "v2", "v3", "v4", "v5", "v6", "state_index"])
    for t, channel, idx, vals, state in _iter_articulated_samples(doc):
        row = [t, channel, idx] + vals + [""] * (7 - len(vals)) + [state]
        writer.writerow(row)
    for t, channel, vals in _iter_direction_samples(doc):
        writer.writerow([t, channel, 0] + vals + [""] * 4 + [""])
    return sio.getvalue().encode("utf-8")


def _landmark_json_bytes(doc: dict[str, Any]) -> bytes:
    frames: list[dict[str, Any]] = []
    for frame in doc["timeline"]:
        entry: dict[str, Any] = {"t": frame["t"], "landmarks": {}}
        for name, spec in doc["channels"].items():
            block = frame["pose"].get(name)
            if not isinstance(block, dict):
                continue
            if spec.get("type") == "articulated":
                vals = block.get("joints", {}).get("values")
                if isinstance(vals, list):
                    stride = int(spec.get("joint_value_stride", 3))
                    entry["landmarks"][name] = [vals[idx : idx + stride] for idx in range(0, len(vals), stride)]
            elif spec.get("type") == "direction":
                entry["landmarks"][name] = [block.get("dir")]
        frames.append(entry)
    return _compact_json_bytes({"fps": doc["fps"], "frames": frames})


def _bvh_like_bytes(doc: dict[str, Any]) -> bytes:
    samples = _iter_articulated_samples(doc)
    joint_names = sorted({f"{channel}_{idx}" for _, channel, idx, _, _ in samples})
    direction_names = sorted({channel for _, channel, _ in _iter_direction_samples(doc)})
    lines = ["HIERARCHY", "ROOT world", "{", "  OFFSET 0 0 0", "  CHANNELS 0"]
    for name in joint_names + direction_names:
        lines.extend(
            [
                f"  JOINT {name}",
                "  {",
                "    OFFSET 0 0 0",
                "    CHANNELS 3 Xposition Yposition Zposition",
                "    End Site",
                "    {",
                "      OFFSET 0 0 0",
                "    }",
                "  }",
            ]
        )
    lines.extend(["}", "MOTION", f"Frames: {len(doc['timeline'])}", f"Frame Time: {1 / float(doc['fps']):0.7f}"])
    for frame in doc["timeline"]:
        row: list[str] = []
        for name, spec in doc["channels"].items():
            block = frame["pose"].get(name)
            if spec.get("type") == "articulated" and isinstance(block, dict):
                vals = block.get("joints", {}).get("values", [])
                stride = int(spec.get("joint_value_stride", 3))
                for idx in range(0, len(vals), stride):
                    row.extend(str(x) for x in vals[idx : idx + 3])
            elif spec.get("type") == "direction" and isinstance(block, dict):
                row.extend(str(x) for x in block.get("dir", [0, 0, 1]))
        lines.append(" ".join(row))
    return ("\n".join(lines) + "\n").encode("utf-8")


def _sample_float_total(doc: dict[str, Any]) -> int:
    total = 0
    for _, _, _, vals, _ in _iter_articulated_samples(doc):
        total += len(vals)
    for _, _, vals in _iter_direction_samples(doc):
        total += len(vals)
    return total


def _artifact_stats(doc: dict[str, Any]) -> list[dict[str, Any]]:
    sgm = compile_to_bytes(doc)
    artifacts: list[tuple[str, str, bytes]] = [
        (".sgm v1 bytecode", "binary", sgm),
        (".gest JSON compact", "json", _compact_json_bytes(doc)),
        (".gest JSON pretty", "json", _pretty_json_bytes(doc)),
        (".gest JSON gzip", "gzip", gzip.compress(_compact_json_bytes(doc), mtime=0)),
        (".gest YAML", "yaml", _yaml_bytes(doc)),
        ("Landmark JSON baseline", "json", _landmark_json_bytes(doc)),
        ("CSV rows baseline", "csv", _csv_bytes(doc)),
        ("BVH-like text baseline", "bvh-like", _bvh_like_bytes(doc)),
    ]
    sgm_size = len(sgm)
    return [
        {
            "name": name,
            "kind": kind,
            "bytes": len(payload),
            "ratio_to_sgm": round(len(payload) / sgm_size, 3) if sgm_size else None,
        }
        for name, kind, payload in artifacts
        if len(payload) > 0
    ]


def build_multi_demo_stats() -> dict[str, Any]:
    cases = demo_cases()
    scenario_stats: list[dict[str, Any]] = []
    for case in cases:
        errors = validate_all(case.doc)
        fatal = [e for e in errors if not e.startswith("jsonschema")]
        if fatal:
            raise ValueError(f"{case.slug} failed validation: {fatal}")
        decoded = decode_sgm_bytes(compile_to_bytes(case.doc))
        scenario_stats.append(
            {
                "slug": case.slug,
                "title": case.title,
                "real_life_case": case.real_life_case,
                "frames": len(case.doc["timeline"]),
                "duration_seconds": case.doc["timeline"][-1]["t"],
                "fps": case.doc["fps"],
                "channels": sorted(case.doc["channels"]),
                "sample_floats_total": _sample_float_total(case.doc),
                "decoded_opcode_count": len(decoded.ops),
                "artifacts": _artifact_stats(case.doc),
            }
        )
    return {
        "methodology": [
            "Each scenario is generated as a valid .gest document.",
            "All byte counts are measured from local artifacts produced from the same numeric samples.",
            "CSV, landmark JSON, and BVH-like baselines are concrete transforms, not official exporters.",
            "Ratios are relative to .sgm v1 bytecode for that same scenario.",
        ],
        "scenarios": scenario_stats,
    }


def write_multi_demo_artifacts() -> dict[str, Any]:
    GENERATED_DIR.mkdir(parents=True, exist_ok=True)
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    DOCS_PATH.parent.mkdir(parents=True, exist_ok=True)
    cases = demo_cases()
    for case in cases:
        source_path = GENERATED_DIR / f"{case.slug}.gest.json"
        sgm_path = OUT_DIR / f"{case.slug}.sgm"
        source_path.write_text(json.dumps(case.doc, indent=2) + "\n", encoding="utf-8")
        sgm_path.write_bytes(compile_to_bytes(case.doc))

    stats = build_multi_demo_stats()
    JSON_PATH.write_text(json.dumps(stats, indent=2) + "\n", encoding="utf-8")

    lines = [
        "# Multi-demo comparison stats",
        "",
        "Measured from generated `.gest` scenarios in `demo/generated/`.",
        "",
        "## Methodology",
        "",
    ]
    lines.extend(f"- {line}" for line in stats["methodology"])
    for scenario in stats["scenarios"]:
        lines.extend(
            [
                "",
                f"## {scenario['title']}",
                "",
                scenario["real_life_case"],
                "",
                f"- Frames: `{scenario['frames']}`",
                f"- Duration: `{scenario['duration_seconds']}s`",
                f"- Channels: `{', '.join(scenario['channels'])}`",
                f"- Sample floats: `{scenario['sample_floats_total']}`",
                f"- Decoded opcodes: `{scenario['decoded_opcode_count']}`",
                "",
                "| Artifact | Kind | Bytes | Ratio to `.sgm` |",
                "|----------|------|-------|-----------------|",
            ]
        )
        for item in scenario["artifacts"]:
            lines.append(
                f"| `{item['name']}` | `{item['kind']}` | {item['bytes']} | {item['ratio_to_sgm']}x |"
            )
    DOCS_PATH.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return stats


def main() -> int:
    stats = write_multi_demo_artifacts()
    print(f"Wrote {JSON_PATH.relative_to(ROOT)}")
    print(f"Wrote {DOCS_PATH.relative_to(ROOT)}")
    for scenario in stats["scenarios"]:
        sgm = next(item for item in scenario["artifacts"] if item["name"] == ".sgm v1 bytecode")
        compact = next(item for item in scenario["artifacts"] if item["name"] == ".gest JSON compact")
        print(
            f"- {scenario['slug']}: {scenario['frames']} frames, "
            f"SGM={sgm['bytes']} B, compact JSON={compact['bytes']} B"
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
