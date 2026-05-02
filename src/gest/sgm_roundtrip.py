from __future__ import annotations

from typing import Any

from gest.sgm_decode import decode_sgm_bytes, decoded_to_pose_timeline


def _infer_joint_value_stride(
    timeline: list[dict[str, Any]], channel_name: str, joint_count: int
) -> int | None:
    if joint_count < 1:
        return None
    for fr in timeline:
        pose = fr.get("pose") or {}
        block = pose.get(channel_name) or {}
        joints = block.get("joints") or {}
        vals = joints.get("values")
        if isinstance(vals, list) and len(vals) % joint_count == 0:
            stride = len(vals) // joint_count
            if stride in (3, 7):
                return stride
    return None


def gest_document_from_sgm_bytes(data: bytes) -> dict[str, Any]:
    """
    Rebuild a draft .gest document from SGM v1 bytecode.

    Lossy / synthetic fields (not present on the wire):
    - `space` is a minimal single-anchor rig (`world` at origin).
    - Every channel `parent` is set to `world`.
    - `joint_layout` is `recovered_from_sgm_v1`.
    - `state_enum` is `s0`..`s{n-1}` when `state_count` > 0 (labels are placeholders).
    - `joint_value_stride` is inferred from the first frame whose `values` length is
      divisible by `joint_count` with quotient 3 or 7; otherwise omitted (validator
      defaults to 3 — may mismatch originals that used stride 7 without inferrable frames).

    Intended for inspection, diffing, and round-trip tests — not a bit-identical restore
    of an arbitrary source .gest file.
    """
    dec = decode_sgm_bytes(data)
    timeline = decoded_to_pose_timeline(dec)

    channels: dict[str, Any] = {}
    for ch in dec.channels:
        if ch.kind == "articulated":
            jc = ch.joint_count or 1
            sc = ch.state_count or 0
            spec: dict[str, Any] = {
                "type": "articulated",
                "parent": "world",
                "joint_count": jc,
                "joint_layout": "recovered_from_sgm_v1",
            }
            if sc > 0:
                spec["state_enum"] = [f"s{i}" for i in range(sc)]
            stride = _infer_joint_value_stride(timeline, ch.name, jc)
            if stride is not None:
                spec["joint_value_stride"] = stride
            channels[ch.name] = spec
        else:
            channels[ch.name] = {
                "type": "direction",
                "parent": "world",
                "representation": "unit_vector",
            }

    return {
        "version": "0.2",
        "profile": "rt",
        "fps": dec.fps,
        "time_base": "seconds",
        "units": "meters",
        "coordinate_system": {
            "handedness": "right",
            "up": "+Y",
            "forward": "+Z",
        },
        "capabilities": ["sgm_roundtrip"],
        "space": {
            "anchors": {
                "world": {"t": [0.0, 0.0, 0.0], "q": [0.0, 0.0, 0.0, 1.0]},
            },
        },
        "channels": channels,
        "timeline": timeline,
    }
