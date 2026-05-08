from __future__ import annotations

from typing import Any

from gest.importers.common import base_document


def _parse_channel_count(lines: list[str]) -> int:
    total = 0
    for line in lines:
        s = line.strip()
        if s.startswith("CHANNELS "):
            parts = s.split()
            if len(parts) >= 2:
                total += int(parts[1])
    return total


def bvh_text_to_gest(text: str, *, fps: float | None = None) -> dict[str, Any]:
    """
    Convert a simple BVH/BVH-like MOTION section into one articulated .gest channel.

    This parser targets sampled position channels. It is deliberately conservative:
    each frame's numeric MOTION row is chunked into XYZ triples and stored as a
    `bvh_points` articulated channel. Rotation semantics are not interpreted.
    """
    lines = [line.rstrip() for line in text.splitlines() if line.strip()]
    try:
        motion_idx = next(i for i, line in enumerate(lines) if line.strip() == "MOTION")
    except StopIteration as e:
        raise ValueError("BVH input must contain a MOTION section.") from e

    channel_count = _parse_channel_count(lines[:motion_idx])
    frames_line = lines[motion_idx + 1].strip()
    frame_time_line = lines[motion_idx + 2].strip()
    if not frames_line.startswith("Frames:"):
        raise ValueError("BVH MOTION must contain a Frames line.")
    if not frame_time_line.startswith("Frame Time:"):
        raise ValueError("BVH MOTION must contain a Frame Time line.")
    frame_count = int(frames_line.split(":", 1)[1].strip())
    frame_time = float(frame_time_line.split(":", 1)[1].strip())
    effective_fps = fps if fps is not None else (1.0 / frame_time if frame_time > 0 else 60.0)

    motion_rows = lines[motion_idx + 3 : motion_idx + 3 + frame_count]
    if len(motion_rows) != frame_count:
        raise ValueError("BVH MOTION row count does not match Frames.")

    timeline: list[dict[str, Any]] = []
    joint_count = 0
    for i, row in enumerate(motion_rows):
        nums = [float(x) for x in row.split()]
        if channel_count and len(nums) != channel_count:
            raise ValueError(
                f"BVH frame {i} has {len(nums)} values, expected {channel_count} channels."
            )
        usable = nums[: len(nums) - (len(nums) % 3)]
        joint_count = max(joint_count, len(usable) // 3)
        timeline.append(
            {
                "t": round(i * frame_time, 6),
                "pose": {
                    "bvh_points": {
                        "joints": {"format": "raw_float32", "values": usable},
                        "state_index": 0,
                    }
                },
            }
        )

    if joint_count < 1:
        raise ValueError("BVH input did not contain enough numeric channels for XYZ points.")

    doc = base_document(fps=float(effective_fps), capability="bvh_import")
    doc["channels"] = {
        "bvh_points": {
            "type": "articulated",
            "parent": "world",
            "joint_count": joint_count,
            "joint_value_stride": 3,
            "joint_layout": "bvh_xyz_triplets_v1",
            "state_enum": ["shape_0"],
        }
    }
    doc["timeline"] = timeline
    doc["producer_notes"] = {
        "source_format": "BVH/BVH-like MOTION",
        "runtime_note": "Importer chunks sampled channels into XYZ triples; rotation interpretation is out of scope.",
    }
    return doc

