"""Shared procedural motion helpers for .gest demo clips."""

from __future__ import annotations

import math
from typing import Any


def round3(v: float) -> float:
    return round(v, 3)


def lerp(a: float, b: float, u: float) -> float:
    return a + (b - a) * u


def lerp3(a: tuple[float, float, float], b: tuple[float, float, float], u: float) -> tuple[float, float, float]:
    return (lerp(a[0], b[0], u), lerp(a[1], b[1], u), lerp(a[2], b[2], u))


def smoothstep(u: float) -> float:
    u = max(0.0, min(1.0, u))
    return u * u * (3.0 - 2.0 * u)


def ease_in_out(u: float) -> float:
    u = max(0.0, min(1.0, u))
    return 0.5 - 0.5 * math.cos(math.pi * u)


def bezier4(
    p0: tuple[float, float, float],
    p1: tuple[float, float, float],
    p2: tuple[float, float, float],
    p3: tuple[float, float, float],
    u: float,
) -> tuple[float, float, float]:
    u = max(0.0, min(1.0, u))
    a = lerp3(p0, p1, u)
    b = lerp3(p1, p2, u)
    c = lerp3(p2, p3, u)
    d = lerp3(a, b, u)
    e = lerp3(b, c, u)
    return lerp3(d, e, u)


def unit(v: list[float]) -> list[float]:
    n = math.sqrt(sum(x * x for x in v))
    if n == 0:
        return [0.0, 0.0, 1.0]
    return [round3(x / n) for x in v]


def gaze_toward(head: tuple[float, float, float], target: tuple[float, float, float]) -> list[float]:
    return unit([target[i] - head[i] for i in range(3)])


HEAD = (0.0, 1.58, 0.0)
WORK_MID = (0.0, 1.02, 0.36)
WORK_LEFT = (-0.22, 1.0, 0.34)
WORK_RIGHT = (0.22, 1.0, 0.34)


def five_point_hand(
    root: tuple[float, float, float],
    spread: float = 1.0,
    pinch: float = 0.0,
) -> list[float]:
    """Five joint proxies: wrist + thumb/index/middle/outer with optional pinch closure."""
    x, y, z = root
    pinch = max(0.0, min(1.0, pinch))
    close = 1.0 - 0.72 * pinch
    offsets = [
        (0.0, 0.0, 0.0),
        (-0.048 * spread * close, 0.038, 0.022),
        (-0.020 * spread * close, 0.088, 0.014),
        (0.020 * spread * close, 0.092, 0.012),
        (0.052 * spread * close, 0.068, 0.018),
    ]
    values: list[float] = []
    for dx, dy, dz in offsets:
        values.extend([round3(x + dx), round3(y + dy), round3(z + dz)])
    return values


def six_point_hand(root: tuple[float, float, float], spread: float = 1.0, pinch: float = 0.0) -> list[float]:
    x, y, z = root
    pinch = max(0.0, min(1.0, pinch))
    close = 1.0 - 0.68 * pinch
    values: list[float] = []
    for i in range(6):
        angle = (i / 5 - 0.5) * math.pi * 0.62
        radius = (0.022 + i * 0.011) * spread * close
        values.extend([
            round3(x + math.sin(angle) * radius),
            round3(y + 0.032 * i + 0.012 * pinch),
            round3(z + math.cos(angle) * radius * 0.42),
        ])
    return values


def dual_hand_channel_spec() -> dict[str, Any]:
    return {
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
        "gaze": {"type": "direction", "parent": "head", "representation": "unit_vector"},
    }


def pinch_state(u: float) -> int:
    if u < 0.30:
        return 0
    if u < 0.72:
        return 1
    return 2
