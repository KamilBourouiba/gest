from __future__ import annotations

from typing import Any

from gest.importers.common import base_document, flatten_xyz


def mediapipe_json_to_gest(data: dict[str, Any]) -> dict[str, Any]:
    """
    Convert a MediaPipe-like landmark JSON document into .gest.

    Expected shape:
    {
      "fps": 30,
      "frames": [
        {
          "t": 0.0,
          "hands": {
            "left": [{"x": ..., "y": ..., "z": ...}, ...],
            "right": [[x, y, z], ...]
          },
          "gaze": [x, y, z]
        }
      ]
    }
    """
    frames = data.get("frames")
    if not isinstance(frames, list) or not frames:
        raise ValueError("MediaPipe input must contain a non-empty frames array.")

    fps = float(data.get("fps", 30))
    first_hands = frames[0].get("hands", {})
    if not isinstance(first_hands, dict):
        raise ValueError("MediaPipe frame hands must be an object.")

    channels: dict[str, Any] = {}
    for side in ("left", "right"):
        pts = first_hands.get(side)
        if isinstance(pts, list) and pts:
            channels[f"{side}_hand"] = {
                "type": "articulated",
                "parent": "chest",
                "joint_count": len(pts),
                "joint_value_stride": 3,
                "joint_layout": "mediapipe_hands_landmarks_v1",
                "state_enum": ["shape_0"],
            }
    if any(isinstance(frame.get("gaze"), list) for frame in frames):
        channels["gaze"] = {
            "type": "direction",
            "parent": "head",
            "representation": "unit_vector",
        }
    if not channels:
        raise ValueError("MediaPipe input did not expose supported hand or gaze channels.")

    timeline: list[dict[str, Any]] = []
    for i, frame in enumerate(frames):
        hands = frame.get("hands", {})
        if not isinstance(hands, dict):
            hands = {}
        pose: dict[str, Any] = {}
        for side in ("left", "right"):
            cname = f"{side}_hand"
            pts = hands.get(side)
            if cname in channels and isinstance(pts, list):
                pose[cname] = {
                    "joints": {"format": "raw_float32", "values": flatten_xyz(pts)},
                    "state_index": 0,
                }
        gaze = frame.get("gaze")
        if "gaze" in channels and isinstance(gaze, list) and len(gaze) == 3:
            pose["gaze"] = {"dir": [float(gaze[0]), float(gaze[1]), float(gaze[2])]}
        if pose:
            timeline.append({"t": float(frame.get("t", i / fps)), "pose": pose})

    doc = base_document(fps=fps, capability="mediapipe_import")
    doc["channels"] = channels
    doc["timeline"] = timeline
    doc["producer_notes"] = {
        "source_format": "mediapipe-like landmarks",
        "runtime_note": "Importer keeps landmarks only; semantic labels remain external.",
    }
    return doc

