from __future__ import annotations

import argparse
import math
import shutil
import subprocess
from pathlib import Path
from typing import Any

from demo.render_video import (
    BG,
    CHEST,
    GAZE,
    GRID,
    HEIGHT,
    LEFT,
    MUTED,
    RIGHT,
    TEXT,
    WIDTH,
    Canvas,
    _draw_grid,
    _draw_particles,
    _load,
    _sample,
    draw_text,
)


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_INPUT = ROOT / "demo" / "xr_dual_hand_arc.gest.json"
DEFAULT_OUTPUT = ROOT / "demo" / "out" / "xr_avatar_playback.mp4"
FPS = 30
SECONDS_PAD = 0.6


def avatar_project(p: tuple[float, float, float] | list[float]) -> tuple[int, int]:
    x, y, z = float(p[0]), float(p[1]), float(p[2])
    return WIDTH // 2 + int(x * 650), HEIGHT - 70 - int((y - 0.72) * 600) - int(z * 50)


def _midpoint(
    a: tuple[float, float, float] | list[float],
    b: tuple[float, float, float] | list[float],
    bias: float = 0.5,
) -> tuple[float, float, float]:
    return (
        float(a[0]) + (float(b[0]) - float(a[0])) * bias,
        float(a[1]) + (float(b[1]) - float(a[1])) * bias,
        float(a[2]) + (float(b[2]) - float(a[2])) * bias,
    )


def _draw_limb(
    c: Canvas,
    a: tuple[float, float, float] | list[float],
    b: tuple[float, float, float] | list[float],
    color: tuple[int, int, int],
    thickness: int,
) -> None:
    ax, ay = avatar_project(a)
    bx, by = avatar_project(b)
    c.line(ax, ay, bx, by, color, thickness)
    c.circle(ax, ay, max(4, thickness + 2), color)
    c.circle(bx, by, max(4, thickness + 2), color)


def _draw_avatar_hand(
    c: Canvas, points: list[tuple[float, float, float]], color: tuple[int, int, int]
) -> None:
    root = avatar_project(points[0])
    c.circle(root[0], root[1], 12, color)
    for p in points[1:]:
        sx, sy = avatar_project(p)
        c.line(root[0], root[1], sx, sy, color, 4)
        c.circle(sx, sy, 7, color)


def _draw_floor(c: Canvas, t: float) -> None:
    horizon = HEIGHT - 104
    c.line(120, horizon, WIDTH - 120, horizon, GRID, 2)
    for i in range(15):
        y = horizon + i * 18
        c.line(180 - i * 18, y, WIDTH - 180 + i * 18, y, (24, 32, 48))
    for i in range(-7, 8):
        x = WIDTH // 2 + i * 72 + int(math.sin(t + i) * 4)
        c.line(x, horizon, WIDTH // 2 + i * 130, HEIGHT - 20, (24, 32, 48))


def draw_avatar_frame(c: Canvas, doc: dict[str, Any], t: float, frame_idx: int, total: int) -> None:
    _draw_grid(c)
    _draw_floor(c, t)
    _draw_particles(c, t)
    sample = _sample(doc, min(t, float(doc["timeline"][-1]["t"])))
    left = sample["pose"]["left_hand"]["points"]
    right = sample["pose"]["right_hand"]["points"]
    gaze = sample["pose"]["gaze"]["dir"]

    pelvis = (0.0, 0.92, 0.05)
    chest = (0.0, 1.28, 0.08)
    neck = (0.0, 1.50, 0.05)
    head = (0.0, 1.64, 0.03)
    l_shoulder = (-0.22, 1.42, 0.08)
    r_shoulder = (0.22, 1.42, 0.08)
    l_wrist = left[0]
    r_wrist = right[0]
    l_elbow = _midpoint(l_shoulder, l_wrist, 0.55)
    r_elbow = _midpoint(r_shoulder, r_wrist, 0.55)

    # Core avatar.
    _draw_limb(c, pelvis, chest, CHEST, 8)
    _draw_limb(c, chest, neck, CHEST, 8)
    _draw_limb(c, l_shoulder, r_shoulder, CHEST, 7)
    _draw_limb(c, l_shoulder, l_elbow, LEFT, 7)
    _draw_limb(c, l_elbow, l_wrist, LEFT, 7)
    _draw_limb(c, r_shoulder, r_elbow, RIGHT, 7)
    _draw_limb(c, r_elbow, r_wrist, RIGHT, 7)

    hx, hy = avatar_project(head)
    c.circle(hx, hy, 30, CHEST)
    c.circle(hx - 9, hy - 7, 3, BG)
    c.circle(hx + 9, hy - 7, 3, BG)

    # Hands and gaze.
    _draw_avatar_hand(c, left, LEFT)
    _draw_avatar_hand(c, right, RIGHT)
    gaze_end = [head[0] + gaze[0] * 0.45, head[1] + gaze[1] * 0.45, head[2] + gaze[2] * 0.45]
    gx, gy = avatar_project(gaze_end)
    c.line(hx, hy, gx, gy, GAZE, 3)
    c.circle(gx, gy, 7, GAZE)

    # HUD.
    draw_text(c, 48, 34, ".gest on avatar", TEXT, 4)
    draw_text(c, 50, 84, "same motion IR driving a simple humanoid rig", MUTED, 2)
    draw_text(c, 48, HEIGHT - 64, f"avatar playback  t={t:0.2f}s  frame={frame_idx + 1}/{total}", TEXT, 3)
    draw_text(c, WIDTH - 392, HEIGHT - 64, "left/right hands + gaze from .gest", MUTED, 2)


def render_avatar_video(input_path: Path, output_path: Path) -> None:
    ffmpeg = shutil.which("ffmpeg")
    if not ffmpeg:
        raise RuntimeError("ffmpeg is required to encode the MP4 video")
    doc = _load(input_path)
    last_t = float(doc["timeline"][-1]["t"])
    total = int(math.ceil((last_t + SECONDS_PAD) * FPS))
    frame_dir = output_path.parent / "avatar_frames"
    frame_dir.mkdir(parents=True, exist_ok=True)
    for old in frame_dir.glob("*.ppm"):
        old.unlink()
    output_path.parent.mkdir(parents=True, exist_ok=True)

    for idx in range(total):
        t = min(last_t, idx / FPS)
        c = Canvas(WIDTH, HEIGHT, BG)
        draw_avatar_frame(c, doc, t, idx, total)
        c.write_ppm(frame_dir / f"frame_{idx:04d}.ppm")

    subprocess.run(
        [
            ffmpeg,
            "-y",
            "-framerate",
            str(FPS),
            "-i",
            str(frame_dir / "frame_%04d.ppm"),
            "-c:v",
            "libx264",
            "-pix_fmt",
            "yuv420p",
            "-movflags",
            "+faststart",
            str(output_path),
        ],
        check=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description="Render a .gest clip on a stylized avatar.")
    p.add_argument("--input", type=Path, default=DEFAULT_INPUT)
    p.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    args = p.parse_args(argv)
    render_avatar_video(args.input, args.output)
    print(f"Wrote avatar video -> {args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
