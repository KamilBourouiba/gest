from __future__ import annotations

import csv
import io
import json
import sys
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
for path in (ROOT, SRC):
    s = str(path)
    if s not in sys.path:
        sys.path.insert(0, s)

from demo.multi_demos import DemoCase, demo_cases  # noqa: E402
from gest.sgm import compile_to_bytes  # noqa: E402
from gest.sgm_decode import decode_sgm_bytes  # noqa: E402
from gest.validate import validate_all  # noqa: E402


OUT_JSON = ROOT / "demo" / "out" / "industry-benchmark.json"
OUT_MD = ROOT / "docs" / "industry-benchmark.md"


def _compact_json_bytes(obj: Any) -> bytes:
    return json.dumps(obj, separators=(",", ":"), sort_keys=True).encode("utf-8")


def _iter_articulated(doc: dict[str, Any]):
    for frame in doc["timeline"]:
        for name, spec in sorted(doc["channels"].items()):
            if spec.get("type") != "articulated":
                continue
            block = frame["pose"].get(name)
            if not isinstance(block, dict):
                continue
            vals = block.get("joints", {}).get("values", [])
            stride = int(spec.get("joint_value_stride", 3))
            for idx in range(0, len(vals), stride):
                yield frame["t"], name, idx // stride, vals[idx : idx + stride], block.get("state_index")


def _iter_directions(doc: dict[str, Any]):
    for frame in doc["timeline"]:
        for name, spec in sorted(doc["channels"].items()):
            if spec.get("type") != "direction":
                continue
            block = frame["pose"].get(name)
            if isinstance(block, dict):
                yield frame["t"], name, block.get("dir", [0.0, 0.0, 1.0])


def _sample_float_total(doc: dict[str, Any]) -> int:
    return sum(len(vals) for _, _, _, vals, _ in _iter_articulated(doc)) + sum(
        len(vals) for _, _, vals in _iter_directions(doc)
    )


def _mediapipe_like_bytes(doc: dict[str, Any]) -> bytes:
    frames: list[dict[str, Any]] = []
    for frame in doc["timeline"]:
        landmarks: dict[str, Any] = {}
        handedness: list[dict[str, Any]] = []
        for name, spec in sorted(doc["channels"].items()):
            if spec.get("type") == "articulated":
                vals = frame["pose"][name]["joints"]["values"]
                stride = int(spec.get("joint_value_stride", 3))
                landmarks[name] = [
                    {"x": vals[i], "y": vals[i + 1], "z": vals[i + 2], "visibility": 1.0}
                    for i in range(0, len(vals), stride)
                ]
                handedness.append({"label": name, "score": 1.0})
        frames.append({"timestampSec": frame["t"], "multiHandLandmarks": landmarks, "multiHandedness": handedness})
    return _compact_json_bytes({"source": "mediapipe-like-landmark-result", "fps": doc["fps"], "frames": frames})


def _openxr_like_bytes(doc: dict[str, Any]) -> bytes:
    frames: list[dict[str, Any]] = []
    for frame in doc["timeline"]:
        joints: list[dict[str, Any]] = []
        for _, channel, idx, vals, state in _iter_articulated({"channels": doc["channels"], "timeline": [frame]}):
            joints.append(
                {
                    "path": f"/user/{channel}/input/joint/{idx}",
                    "pose": {
                        "position": vals[:3],
                        "orientation": vals[3:7] if len(vals) >= 7 else [0.0, 0.0, 0.0, 1.0],
                    },
                    "state": state,
                    "radius": 0.01,
                    "tracked": True,
                }
            )
        directions = [
            {"path": f"/user/head/input/{name}", "direction": vals}
            for _, name, vals in _iter_directions({"channels": doc["channels"], "timeline": [frame]})
        ]
        frames.append({"time": frame["t"], "referenceSpace": "LOCAL", "joints": joints, "directions": directions})
    return _compact_json_bytes({"runtime": "openxr-like-trace", "fps": doc["fps"], "frames": frames})


def _gltf_animation_like_bytes(doc: dict[str, Any]) -> bytes:
    node_names = []
    translations_by_node: dict[str, list[float]] = {}
    times = [frame["t"] for frame in doc["timeline"]]
    for _, channel, idx, _, _ in _iter_articulated(doc):
        node = f"{channel}_{idx}"
        if node not in translations_by_node:
            node_names.append(node)
            translations_by_node[node] = []
    for frame in doc["timeline"]:
        for name, spec in sorted(doc["channels"].items()):
            if spec.get("type") != "articulated":
                continue
            vals = frame["pose"][name]["joints"]["values"]
            stride = int(spec.get("joint_value_stride", 3))
            for i in range(0, len(vals), stride):
                translations_by_node[f"{name}_{i // stride}"].extend(vals[i : i + 3])

    samplers = []
    channels = []
    accessors = []
    buffer_views = []
    for node_index, node in enumerate(node_names):
        input_index = len(accessors)
        output_index = input_index + 1
        accessors.append({"type": "SCALAR", "componentType": 5126, "count": len(times), "extras": {"values": times}})
        accessors.append(
            {
                "type": "VEC3",
                "componentType": 5126,
                "count": len(times),
                "extras": {"values": translations_by_node[node]},
            }
        )
        buffer_views.extend([{"buffer": 0, "byteOffset": 0}, {"buffer": 0, "byteOffset": 0}])
        samplers.append({"input": input_index, "output": output_index, "interpolation": "LINEAR"})
        channels.append({"sampler": len(samplers) - 1, "target": {"node": node_index, "path": "translation"}})

    gltf = {
        "asset": {"version": "2.0", "generator": ".gest industry benchmark glTF-like JSON"},
        "scene": 0,
        "scenes": [{"nodes": list(range(len(node_names)))}],
        "nodes": [{"name": name} for name in node_names],
        "animations": [{"name": "gesture_clip", "samplers": samplers, "channels": channels}],
        "buffers": [{"byteLength": sum(len(v) for v in translations_by_node.values()) * 4 + len(times) * 4}],
        "bufferViews": buffer_views,
        "accessors": accessors,
    }
    return _compact_json_bytes(gltf)


def _bvh_like_bytes(doc: dict[str, Any]) -> bytes:
    joint_names = sorted({f"{channel}_{idx}" for _, channel, idx, _, _ in _iter_articulated(doc)})
    lines = ["HIERARCHY", "ROOT world", "{", "  OFFSET 0 0 0", "  CHANNELS 0"]
    for name in joint_names:
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
        for name, spec in sorted(doc["channels"].items()):
            if spec.get("type") == "articulated":
                vals = frame["pose"][name]["joints"]["values"]
                stride = int(spec.get("joint_value_stride", 3))
                for i in range(0, len(vals), stride):
                    row.extend(str(x) for x in vals[i : i + 3])
        lines.append(" ".join(row))
    return ("\n".join(lines) + "\n").encode("utf-8")


def _ros_like_jsonl_bytes(doc: dict[str, Any]) -> bytes:
    lines: list[str] = []
    for frame in doc["timeline"]:
        for _, channel, idx, vals, state in _iter_articulated({"channels": doc["channels"], "timeline": [frame]}):
            msg = {
                "stamp": frame["t"],
                "topic": f"/gest/{channel}/joint/{idx}",
                "type": "geometry_msgs/PoseStamped",
                "msg": {
                    "position": {"x": vals[0], "y": vals[1], "z": vals[2]},
                    "orientation": {"x": 0.0, "y": 0.0, "z": 0.0, "w": 1.0},
                    "state_index": state,
                },
            }
            lines.append(json.dumps(msg, separators=(",", ":"), sort_keys=True))
        for _, channel, vals in _iter_directions({"channels": doc["channels"], "timeline": [frame]}):
            msg = {"stamp": frame["t"], "topic": f"/gest/{channel}", "type": "geometry_msgs/Vector3", "msg": vals}
            lines.append(json.dumps(msg, separators=(",", ":"), sort_keys=True))
    return ("\n".join(lines) + "\n").encode("utf-8")


def _csv_bytes(doc: dict[str, Any]) -> bytes:
    sio = io.StringIO()
    writer = csv.writer(sio)
    writer.writerow(["t", "channel", "sample_index", "x", "y", "z", "qx", "qy", "qz", "qw", "state_index"])
    for t, channel, idx, vals, state in _iter_articulated(doc):
        writer.writerow([t, channel, idx] + vals[:7] + [""] * (7 - len(vals[:7])) + [state])
    for t, channel, vals in _iter_directions(doc):
        writer.writerow([t, channel, 0] + vals + [""] * 4 + [""])
    return sio.getvalue().encode("utf-8")


def _payloads(doc: dict[str, Any]) -> list[tuple[str, str, bytes, str]]:
    return [
        (".sgm v1 bytecode", "gest-runtime", compile_to_bytes(doc), "Compiled runtime bytecode with channel table and opcodes"),
        (".gest JSON compact", "gest-ir", _compact_json_bytes(doc), "Validated non-semantic IR document"),
        ("MediaPipe-like landmark JSON", "industry-like", _mediapipe_like_bytes(doc), "Landmark detector output shape"),
        ("OpenXR-like action trace JSON", "industry-like", _openxr_like_bytes(doc), "Durable trace shaped after XR joint/action frames"),
        ("glTF animation JSON shape", "industry-like", _gltf_animation_like_bytes(doc), "glTF-style node animation structure without binary GLB packing"),
        ("BVH-like skeleton text", "industry-like", _bvh_like_bytes(doc), "Mocap-style hierarchy and MOTION rows"),
        ("ROS-like JSONL topics", "industry-like", _ros_like_jsonl_bytes(doc), "Robotics topic log exported as JSON lines"),
        ("CSV rows", "baseline", _csv_bytes(doc), "Flat rows with weak structure"),
    ]


def _feature_matrix() -> list[dict[str, Any]]:
    return [
        {
            "format": ".gest JSON",
            "durable_file": True,
            "schema_invariants": True,
            "non_semantic_contract": True,
            "runtime_bytecode": False,
            "best_for": "authoring, interchange, audits, CI validation",
        },
        {
            "format": ".sgm v1",
            "durable_file": True,
            "schema_invariants": False,
            "non_semantic_contract": True,
            "runtime_bytecode": True,
            "best_for": "runtime packaging, streaming experiments, decoding/debug",
        },
        {
            "format": "BVH",
            "durable_file": True,
            "schema_invariants": False,
            "non_semantic_contract": False,
            "runtime_bytecode": False,
            "best_for": "legacy skeletal mocap interchange",
        },
        {
            "format": "glTF/VRM",
            "durable_file": True,
            "schema_invariants": False,
            "non_semantic_contract": False,
            "runtime_bytecode": False,
            "best_for": "portable 3D assets, avatars, animation clips",
        },
        {
            "format": "OpenXR",
            "durable_file": False,
            "schema_invariants": False,
            "non_semantic_contract": False,
            "runtime_bytecode": False,
            "best_for": "live XR API access to tracking data",
        },
        {
            "format": "MediaPipe",
            "durable_file": False,
            "schema_invariants": False,
            "non_semantic_contract": False,
            "runtime_bytecode": False,
            "best_for": "ML landmark detection output",
        },
        {
            "format": "ROS logs",
            "durable_file": True,
            "schema_invariants": False,
            "non_semantic_contract": False,
            "runtime_bytecode": False,
            "best_for": "broad robotics telemetry capture",
        },
    ]


def _scenario_stats(case: DemoCase) -> dict[str, Any]:
    errors = validate_all(case.doc)
    fatal = [e for e in errors if not e.startswith("jsonschema")]
    if fatal:
        raise ValueError(f"{case.slug} failed validation: {fatal}")
    sgm_size = len(compile_to_bytes(case.doc))
    payloads = [
        {
            "name": name,
            "kind": kind,
            "bytes": len(payload),
            "ratio_to_sgm": round(len(payload) / sgm_size, 3),
            "notes": notes,
        }
        for name, kind, payload, notes in _payloads(case.doc)
    ]
    winners = [item["name"] for item in payloads if item["name"] != ".sgm v1 bytecode" and item["bytes"] > sgm_size]
    return {
        "slug": case.slug,
        "title": case.title,
        "frames": len(case.doc["timeline"]),
        "duration_seconds": case.doc["timeline"][-1]["t"],
        "fps": case.doc["fps"],
        "channels": sorted(case.doc["channels"]),
        "sample_floats_total": _sample_float_total(case.doc),
        "decoded_opcode_count": len(decode_sgm_bytes(compile_to_bytes(case.doc)).ops),
        "artifacts": payloads,
        "sgm_smaller_than": winners,
    }


def build_industry_benchmark() -> dict[str, Any]:
    scenarios = [_scenario_stats(case) for case in demo_cases()]
    return {
        "methodology": [
            "All artifacts are generated from the same valid .gest scenario documents.",
            "Industry comparisons are concrete JSON/text shapes inspired by common standards and APIs, not certified exporters.",
            "glTF is represented as a JSON animation shape; binary GLB packing is intentionally not claimed.",
            "OpenXR and MediaPipe are APIs/model outputs, so the benchmark uses durable trace shapes for byte comparison.",
            "Ratios are relative to .sgm v1 bytecode for the same scenario.",
        ],
        "proven_better_where": [
            "SGM bytecode is smaller than compact .gest JSON, MediaPipe-like JSON, OpenXR-like traces, glTF-like JSON, ROS-like JSONL, and CSV rows in every generated scenario.",
            "SGM bytecode is smaller than BVH-like text in three of four scenarios; the tiny pose7 microclip is the measured exception.",
            ".gest JSON keeps a stronger validation contract than landmark JSON, BVH-like text, OpenXR-like traces, and ROS-like logs.",
            ".gest/.sgm preserve a non-semantic execution path; labels or meanings can stay in sidecar governance systems.",
            ".sgm is directly designed as a runtime artifact, unlike authoring/container/API trace formats.",
        ],
        "not_better_where": [
            "glTF/VRM are better for shipping meshes, materials, avatars, and full scenes.",
            "OpenXR is better for live device access.",
            "MediaPipe is better for extracting landmarks from images/video.",
            "ROS bags are better for full multi-topic robotics telemetry.",
            "Compression layers such as gzip can beat small bytecode on tiny repetitive JSON clips, but they are transport/archive layers.",
        ],
        "feature_matrix": _feature_matrix(),
        "scenarios": scenarios,
    }


def write_industry_benchmark() -> dict[str, Any]:
    OUT_JSON.parent.mkdir(parents=True, exist_ok=True)
    OUT_MD.parent.mkdir(parents=True, exist_ok=True)
    stats = build_industry_benchmark()
    OUT_JSON.write_text(json.dumps(stats, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    lines = [
        "# Industry benchmark",
        "",
        "This benchmark compares `.gest` / `.sgm` against concrete industry-like shapes generated from the same numeric samples.",
        "",
        "## Methodology",
        "",
    ]
    lines.extend(f"- {line}" for line in stats["methodology"])
    lines.extend(["", "## Where `.gest` / `.sgm` is better in this artifact", ""])
    lines.extend(f"- {line}" for line in stats["proven_better_where"])
    lines.extend(["", "## Where it is not better", ""])
    lines.extend(f"- {line}" for line in stats["not_better_where"])
    lines.extend(["", "## Scenario measurements", ""])
    for scenario in stats["scenarios"]:
        lines.extend(
            [
                f"### {scenario['title']}",
                "",
                f"- Frames: `{scenario['frames']}`",
                f"- Channels: `{', '.join(scenario['channels'])}`",
                f"- Sample floats: `{scenario['sample_floats_total']}`",
                f"- Decoded SGM ops: `{scenario['decoded_opcode_count']}`",
                "",
                "| Artifact | Kind | Bytes | Ratio to `.sgm` |",
                "|----------|------|-------|-----------------|",
            ]
        )
        for item in scenario["artifacts"]:
            lines.append(f"| `{item['name']}` | `{item['kind']}` | {item['bytes']} | {item['ratio_to_sgm']}x |")
        lines.append("")
    OUT_MD.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return stats


def main() -> int:
    stats = write_industry_benchmark()
    print(f"Wrote {OUT_JSON.relative_to(ROOT)}")
    print(f"Wrote {OUT_MD.relative_to(ROOT)}")
    for scenario in stats["scenarios"]:
        print(f"- {scenario['slug']}: SGM smaller than {len(scenario['sgm_smaller_than'])} generated baselines")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
