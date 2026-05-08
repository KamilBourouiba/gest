from __future__ import annotations

from typing import Any

from gest.importers.common import base_document


def _joint_values(joints: list[dict[str, Any]]) -> list[float]:
    out: list[float] = []
    for joint in joints:
        pos = joint.get("position")
        if not isinstance(pos, list) or len(pos) != 3:
            raise ValueError("OpenXR joint position must be [x, y, z].")
        out.extend([float(pos[0]), float(pos[1]), float(pos[2])])
    return out


def openxr_json_to_gest(data: dict[str, Any]) -> dict[str, Any]:
    """
    Convert an OpenXR-like hand tracking capture into .gest.

    Expected shape:
    {
      "fps": 90,
      "frames": [
        {
          "t": 0.0,
          "hands": {
            "left": [{"name": "WRIST", "position": [x,y,z]}, ...],
            "right": [...]
          }
        }
      ]
    }
    """
    frames = data.get("frames")
    if not isinstance(frames, list) or not frames:
        raise ValueError("OpenXR input must contain a non-empty frames array.")
    fps = float(data.get("fps", 90))
    first_hands = frames[0].get("hands", {})
    if not isinstance(first_hands, dict):
        raise ValueError("OpenXR frame hands must be an object.")

    channels: dict[str, Any] = {}
    for side in ("left", "right"):
        joints = first_hands.get(side)
        if isinstance(joints, list) and joints:
            channels[f"{side}_hand"] = {
                "type": "articulated",
                "parent": "chest",
                "joint_count": len(joints),
                "joint_value_stride": 3,
                "joint_layout": "openxr_hand_joint_set_v1",
                "state_enum": ["shape_0"],
            }
    if not channels:
        raise ValueError("OpenXR input did not expose supported hand channels.")

    timeline: list[dict[str, Any]] = []
    for i, frame in enumerate(frames):
        hands = frame.get("hands", {})
        if not isinstance(hands, dict):
            hands = {}
        pose: dict[str, Any] = {}
        for side in ("left", "right"):
            cname = f"{side}_hand"
            joints = hands.get(side)
            if cname in channels and isinstance(joints, list):
                pose[cname] = {
                    "joints": {"format": "raw_float32", "values": _joint_values(joints)},
                    "state_index": 0,
                }
        if pose:
            timeline.append({"t": float(frame.get("t", i / fps)), "pose": pose})

    doc = base_document(fps=fps, capability="openxr_import")
    doc["channels"] = channels
    doc["timeline"] = timeline
    doc["producer_notes"] = {
        "source_format": "OpenXR-like hand tracking",
        "runtime_note": "Importer preserves joint positions; action semantics remain external.",
    }
    return doc

