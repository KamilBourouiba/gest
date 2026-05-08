from __future__ import annotations

from typing import Any


def base_document(
    *,
    fps: float,
    capability: str,
    profile: str = "full",
    time_base: str = "seconds",
) -> dict[str, Any]:
    return {
        "version": "0.2",
        "profile": profile,
        "fps": fps,
        "time_base": time_base,
        "units": "meters",
        "coordinate_system": {
            "handedness": "right",
            "up": "+Y",
            "forward": "+Z",
        },
        "capabilities": ["hierarchy", capability],
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
            }
        },
    }


def flatten_xyz(points: list[dict[str, Any]] | list[list[float]]) -> list[float]:
    out: list[float] = []
    for p in points:
        if isinstance(p, dict):
            out.extend([float(p["x"]), float(p["y"]), float(p["z"])])
        else:
            out.extend([float(p[0]), float(p[1]), float(p[2])])
    return out

