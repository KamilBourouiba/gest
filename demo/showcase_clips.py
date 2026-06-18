from __future__ import annotations

import math
from typing import Any

from demo.motion_library import (
    HEAD,
    WORK_LEFT,
    WORK_MID,
    WORK_RIGHT,
    bezier4,
    dual_hand_channel_spec,
    ease_in_out,
    five_point_hand,
    gaze_toward,
    pinch_state,
    round3,
    six_point_hand,
    smoothstep,
    unit,
)


def build_xr_pinch_grasp_document() -> dict[str, Any]:
    """
    Flagship XR clip: hands reach from rest pose, pinch an imaginary object at
  work_mid, lift slightly, then release. Readable on the 3D mannequin.
    """
    frame_count = 32
    duration = 2.4
    timeline: list[dict[str, Any]] = []

    rest_left = (-0.34, 1.14, 0.30)
    rest_right = (0.34, 1.14, 0.30)
    approach_left = (-0.10, 1.06, 0.37)
    approach_right = (0.10, 1.06, 0.37)
    grasp_left = (-0.06, 1.02, 0.36)
    grasp_right = (0.06, 1.02, 0.36)
    lift_left = (-0.05, 1.14, 0.34)
    lift_right = (0.05, 1.14, 0.34)

    for i in range(frame_count):
        u = i / (frame_count - 1)
        t = round3(duration * u)

        if u < 0.38:
            p = smoothstep(u / 0.38)
            left_root = bezier4(rest_left, (-0.22, 1.10, 0.33), approach_left, grasp_left, p)
            right_root = bezier4(rest_right, (0.22, 1.10, 0.33), approach_right, grasp_right, p)
            pinch = smoothstep(max(0.0, (u - 0.18) / 0.20))
            spread_l = 1.05 - 0.55 * pinch
            spread_r = 1.05 - 0.55 * pinch
        elif u < 0.62:
            p = smoothstep((u - 0.38) / 0.24)
            left_root = lerp3_tuple(grasp_left, lift_left, p)
            right_root = lerp3_tuple(grasp_right, lift_right, p)
            pinch = 1.0
            spread_l = 0.48
            spread_r = 0.48
        else:
            p = smoothstep((u - 0.62) / 0.38)
            left_root = lerp3_tuple(lift_left, rest_left, p)
            right_root = lerp3_tuple(lift_right, rest_right, p)
            pinch = 1.0 - p
            spread_l = 0.48 + 0.57 * p
            spread_r = 0.48 + 0.57 * p

        focus = (
            (left_root[0] + right_root[0]) / 2,
            (left_root[1] + right_root[1]) / 2,
            (left_root[2] + right_root[2]) / 2,
        )
        timeline.append(
            {
                "t": t,
                "pose": {
                    "left_hand": {
                        "joints": {"format": "raw_float32", "values": five_point_hand(left_root, spread_l, pinch)},
                        "state_index": pinch_state(u),
                    },
                    "right_hand": {
                        "joints": {"format": "raw_float32", "values": five_point_hand(right_root, spread_r, pinch)},
                        "state_index": pinch_state(u),
                    },
                    "gaze": {"dir": gaze_toward(HEAD, focus)},
                },
            }
        )

    return _wrap_doc(
        "xr_pinch_grasp",
        timeline,
        channels=dual_hand_channel_spec(),
        fps=60,
        named_points=True,
    )


def build_assembly_pick_place_document() -> dict[str, Any]:
    """Pick-and-place cycle: approach shelf, grasp, lift, translate, release."""
    frame_count = 40
    duration = 2.2
    timeline: list[dict[str, Any]] = []

    rest = (0.38, 1.02, 0.22)
    above_part = (0.12, 0.98, 0.42)
    at_part = (0.08, 0.94, 0.44)
    lifted = (0.08, 1.18, 0.40)
    over_bin = (-0.28, 1.12, 0.38)
    release = (-0.30, 1.06, 0.36)

    for i in range(frame_count):
        u = i / (frame_count - 1)
        t = round3(duration * u)

        if u < 0.22:
            root = bezier4(rest, (0.28, 1.00, 0.30), (0.18, 0.99, 0.38), above_part, smoothstep(u / 0.22))
            pinch, spread, state = 0.0, 1.0, 0
        elif u < 0.35:
            root = lerp3_tuple(above_part, at_part, smoothstep((u - 0.22) / 0.13))
            pinch, spread, state = smoothstep((u - 0.28) / 0.07), 0.95, 1
        elif u < 0.50:
            root = lerp3_tuple(at_part, lifted, smoothstep((u - 0.35) / 0.15))
            pinch, spread, state = 1.0, 0.42, 1
        elif u < 0.72:
            root = bezier4(lifted, (0.0, 1.16, 0.42), (-0.14, 1.14, 0.40), over_bin, smoothstep((u - 0.50) / 0.22))
            pinch, spread, state = 1.0, 0.42, 2
        else:
            root = lerp3_tuple(over_bin, release, smoothstep((u - 0.72) / 0.28))
            pinch = 1.0 - smoothstep((u - 0.82) / 0.18)
            spread, state = 0.42 + 0.58 * (1.0 - pinch), 2 if pinch > 0.2 else 0

        target = (0.08, 0.94, 0.44)
        timeline.append(
            {
                "t": t,
                "pose": {
                    "right_hand": {
                        "joints": {"format": "raw_float32", "values": five_point_hand(root, spread, pinch)},
                        "state_index": state,
                    },
                    "gaze": {"dir": gaze_toward(HEAD, target)},
                },
            }
        )

    return _wrap_doc(
        "assembly_pick_place",
        timeline,
        channels={
            "right_hand": dual_hand_channel_spec()["right_hand"],
            "gaze": dual_hand_channel_spec()["gaze"],
        },
        fps=60,
    )


def build_presentation_sweep_document() -> dict[str, Any]:
    """Presenter sweeps the right hand across a holographic panel; gaze tracks the hand."""
    frame_count = 36
    duration = 2.0
    timeline: list[dict[str, Any]] = []

    for i in range(frame_count):
        u = i / (frame_count - 1)
        t = round3(duration * u)
        sweep = math.sin(math.pi * u)
        root = (
            round3(0.34 - 0.58 * u + 0.06 * math.sin(math.tau * u * 2)),
            round3(1.22 + 0.10 * sweep),
            round3(0.40 + 0.04 * math.cos(math.pi * u)),
        )
        spread = 0.88 + 0.18 * sweep
        timeline.append(
            {
                "t": t,
                "pose": {
                    "right_hand": {
                        "joints": {"format": "raw_float32", "values": five_point_hand(root, spread, 0.05 * sweep)},
                        "state_index": 0 if u < 0.33 else 1 if u < 0.66 else 2,
                    },
                    "gaze": {"dir": gaze_toward(HEAD, root)},
                },
            }
        )

    return _wrap_doc(
        "presentation_sweep",
        timeline,
        channels={
            "right_hand": dual_hand_channel_spec()["right_hand"],
            "gaze": dual_hand_channel_spec()["gaze"],
        },
        fps=60,
    )


def lerp3_tuple(a: tuple[float, float, float], b: tuple[float, float, float], u: float) -> tuple[float, float, float]:
    return (
        round3(a[0] + (b[0] - a[0]) * u),
        round3(a[1] + (b[1] - a[1]) * u),
        round3(a[2] + (b[2] - a[2]) * u),
    )


def _wrap_doc(
    capability: str,
    timeline: list[dict[str, Any]],
    channels: dict[str, Any],
    fps: int,
    named_points: bool = False,
) -> dict[str, Any]:
    space: dict[str, Any] = {
        "anchors": {
            "world": {"t": [0.0, 0.0, 0.0], "q": [0.0, 0.0, 0.0, 1.0]},
            "chest": {"parent": "world", "t": [0.0, 1.05, 0.0], "q": [0.0, 0.0, 0.0, 1.0]},
            "head": {"parent": "chest", "t": [0.0, 0.53, 0.0], "q": [0.0, 0.0, 0.0, 1.0]},
        },
    }
    if named_points:
        space["named_points"] = {
            "work_left": {"parent": "chest", "local": list(WORK_LEFT)},
            "work_mid": {"parent": "chest", "local": list(WORK_MID)},
            "work_right": {"parent": "chest", "local": list(WORK_RIGHT)},
        }
    return {
        "version": "0.2",
        "profile": "full",
        "fps": fps,
        "time_base": "seconds",
        "units": "meters",
        "coordinate_system": {"handedness": "right", "up": "+Y", "forward": "+Z"},
        "capabilities": ["hierarchy", capability, "sgm_roundtrip"],
        "space": space,
        "channels": channels,
        "interpolation_defaults": {
            "translation": "cubic_hermite",
            "rotation": "slerp",
            "scalar": "linear",
        },
        "timeline": timeline,
    }
