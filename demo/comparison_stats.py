from __future__ import annotations

import csv
import gzip
import io
import json
import sys
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
for path in (ROOT, SRC):
    s = str(path)
    if s not in sys.path:
        sys.path.insert(0, s)

from gest.sgm import compile_to_bytes  # noqa: E402
from gest.sgm_decode import decode_sgm_bytes, decoded_to_pose_timeline  # noqa: E402
from gest.sgm_roundtrip import gest_document_from_sgm_bytes  # noqa: E402

from demo.run_demo import build_demo_document  # noqa: E402


OUT_DIR = ROOT / "demo" / "out"
STATS_JSON = OUT_DIR / "comparison-stats.json"
STATS_MD = ROOT / "docs" / "comparison-stats.md"


@dataclass(frozen=True)
class ArtifactStat:
    name: str
    kind: str
    bytes: int
    ratio_to_sgm: float
    notes: str


def _compact_json_bytes(obj: Any) -> bytes:
    return json.dumps(obj, separators=(",", ":"), sort_keys=True).encode("utf-8")


def _pretty_json_bytes(obj: Any) -> bytes:
    return (json.dumps(obj, indent=2, sort_keys=True) + "\n").encode("utf-8")


def _csv_landmarks_bytes(doc: dict[str, Any]) -> bytes:
    """
    CSV baseline: one row per frame/channel/joint xyz point.

    This is a real transform of the same motion data, but intentionally lacks
    hierarchy, schema, state enum metadata, and runtime opcodes.
    """
    sio = io.StringIO()
    writer = csv.writer(sio)
    writer.writerow(["t", "channel", "joint_index", "x", "y", "z", "state_index"])
    for frame in doc["timeline"]:
        for channel in ("left_hand", "right_hand"):
            block = frame["pose"][channel]
            vals = block["joints"]["values"]
            for idx in range(0, len(vals), 3):
                writer.writerow(
                    [
                        frame["t"],
                        channel,
                        idx // 3,
                        vals[idx],
                        vals[idx + 1],
                        vals[idx + 2],
                        block["state_index"],
                    ]
                )
        gaze = frame["pose"]["gaze"]["dir"]
        writer.writerow([frame["t"], "gaze", 0, gaze[0], gaze[1], gaze[2], ""])
    return sio.getvalue().encode("utf-8")


def _landmark_json_bytes(doc: dict[str, Any]) -> bytes:
    """
    Landmark baseline resembling common ML detector outputs: frame -> landmarks.

    It preserves numeric samples but drops .gest channel declarations, state enum,
    validation-oriented schema fields, and compile/recovery metadata.
    """
    frames: list[dict[str, Any]] = []
    for frame in doc["timeline"]:
        entry: dict[str, Any] = {"t": frame["t"], "landmarks": {}}
        for channel in ("left_hand", "right_hand"):
            vals = frame["pose"][channel]["joints"]["values"]
            entry["landmarks"][channel] = [
                vals[idx : idx + 3] for idx in range(0, len(vals), 3)
            ]
        entry["landmarks"]["gaze"] = [frame["pose"]["gaze"]["dir"]]
        frames.append(entry)
    return _compact_json_bytes({"fps": doc["fps"], "frames": frames})


def _bvh_like_bytes(doc: dict[str, Any]) -> bytes:
    """
    BVH-like skeleton baseline for the same point tracks.

    It is not a production BVH exporter; it is a concrete sampled-channel text
    baseline with BVH-style hierarchy and MOTION rows for this demo clip.
    """
    joint_names = [
        "left_root",
        "left_thumb",
        "left_index",
        "left_middle",
        "left_outer",
        "right_root",
        "right_thumb",
        "right_index",
        "right_middle",
        "right_outer",
        "gaze",
    ]
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
    lines.extend(["}", "MOTION", f"Frames: {len(doc['timeline'])}", "Frame Time: 0.0166667"])
    for frame in doc["timeline"]:
        values: list[str] = []
        for channel in ("left_hand", "right_hand"):
            values.extend(str(x) for x in frame["pose"][channel]["joints"]["values"])
        values.extend(str(x) for x in frame["pose"]["gaze"]["dir"])
        lines.append(" ".join(values))
    return ("\n".join(lines) + "\n").encode("utf-8")


def build_comparison_stats() -> dict[str, Any]:
    doc = build_demo_document()
    sgm = compile_to_bytes(doc)
    decoded = decode_sgm_bytes(sgm)
    recovered = gest_document_from_sgm_bytes(sgm)
    dump = {
        "format_version": decoded.format_version,
        "fps": decoded.fps,
        "channels": [asdict(c) for c in decoded.channels],
        "timeline": decoded_to_pose_timeline(decoded),
    }

    artifacts: list[tuple[str, str, bytes, str]] = [
        (
            ".gest JSON pretty",
            "gest",
            _pretty_json_bytes(doc),
            "Readable canonical IR with schema-facing metadata",
        ),
        (
            ".gest JSON compact",
            "gest",
            _compact_json_bytes(doc),
            "Same IR without whitespace",
        ),
        (
            ".gest JSON gzip",
            "gest",
            gzip.compress(_compact_json_bytes(doc), mtime=0),
            "Compressed compact JSON",
        ),
        (
            ".sgm v1 bytecode",
            "sgm",
            sgm,
            "Runtime bytecode emitted by the reference compiler",
        ),
        (
            "Recovered .gest JSON",
            "gest",
            _pretty_json_bytes(recovered),
            "Lossy draft recovered from .sgm",
        ),
        (
            "Decoded SGM dump",
            "debug",
            _pretty_json_bytes(dump),
            "Debug channel table + reconstructed timeline",
        ),
        (
            "Landmark JSON baseline",
            "baseline",
            _landmark_json_bytes(doc),
            "ML-style landmarks only; no IR validation contract",
        ),
        (
            "CSV landmarks baseline",
            "baseline",
            _csv_landmarks_bytes(doc),
            "Flat rows; easy to inspect, weak structure",
        ),
        (
            "BVH-like text baseline",
            "baseline",
            _bvh_like_bytes(doc),
            "Sampled skeleton-style text baseline for this clip",
        ),
    ]

    sgm_size = len(sgm)
    stats = [
        ArtifactStat(
            name=name,
            kind=kind,
            bytes=len(payload),
            ratio_to_sgm=round(len(payload) / sgm_size, 3),
            notes=notes,
        )
        for name, kind, payload, notes in artifacts
    ]

    frame_count = len(doc["timeline"])
    channels = doc["channels"]
    floats_per_frame = (
        channels["left_hand"]["joint_count"] * channels["left_hand"]["joint_value_stride"]
        + channels["right_hand"]["joint_count"] * channels["right_hand"]["joint_value_stride"]
        + 3
    )
    opcode_count = len(decoded.ops)

    return {
        "demo": {
            "frames": frame_count,
            "duration_seconds": doc["timeline"][-1]["t"],
            "fps": doc["fps"],
            "channels": sorted(channels.keys()),
            "floats_per_frame": floats_per_frame,
            "sample_floats_total": floats_per_frame * frame_count,
            "decoded_opcode_count": opcode_count,
        },
        "artifacts": [asdict(s) for s in stats],
        "methodology": [
            "All byte counts are measured locally from the same generated demo document.",
            "Baselines are concrete transformations of the same numeric samples, not official exporters.",
            "BVH-like baseline is a sampled-channel text baseline shaped like BVH, not a DCC-certified BVH exporter.",
            "Ratios are relative to .sgm v1 bytecode for this demo clip.",
        ],
    }


def write_stats() -> dict[str, Any]:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    STATS_MD.parent.mkdir(parents=True, exist_ok=True)
    stats = build_comparison_stats()
    STATS_JSON.write_text(json.dumps(stats, indent=2) + "\n", encoding="utf-8")

    lines = [
        "# Demo comparison stats",
        "",
        "These numbers are measured from `demo/run_demo.py` for the same generated motion clip.",
        "",
        "## Demo shape",
        "",
    ]
    demo = stats["demo"]
    for key, value in demo.items():
        lines.append(f"- `{key}`: `{value}`")
    lines.extend(["", "## Artifact sizes", ""])
    lines.append("| Artifact | Kind | Bytes | Ratio to `.sgm` | Notes |")
    lines.append("|----------|------|-------|-----------------|-------|")
    for item in stats["artifacts"]:
        lines.append(
            f"| `{item['name']}` | `{item['kind']}` | {item['bytes']} | "
            f"{item['ratio_to_sgm']}x | {item['notes']} |"
        )
    lines.extend(["", "## Methodology", ""])
    for line in stats["methodology"]:
        lines.append(f"- {line}")
    STATS_MD.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return stats


def main() -> int:
    stats = write_stats()
    print(f"Wrote {STATS_JSON.relative_to(ROOT)}")
    print(f"Wrote {STATS_MD.relative_to(ROOT)}")
    for item in stats["artifacts"]:
        print(f"- {item['name']}: {item['bytes']} bytes ({item['ratio_to_sgm']}x .sgm)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
