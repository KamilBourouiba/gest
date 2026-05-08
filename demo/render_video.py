from __future__ import annotations

import argparse
import json
import math
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
for path in (ROOT, SRC):
    s = str(path)
    if s not in sys.path:
        sys.path.insert(0, s)

DEFAULT_INPUT = ROOT / "demo" / "xr_dual_hand_arc.gest.json"
DEFAULT_OUTPUT = ROOT / "demo" / "out" / "xr_dual_hand_arc.mp4"
DEFAULT_STATS = ROOT / "demo" / "out" / "comparison-stats.json"

WIDTH = 1280
HEIGHT = 720
FPS = 30
SECONDS_PAD = 0.4


Color = tuple[int, int, int]

BG: Color = (10, 14, 22)
GRID: Color = (32, 40, 58)
TEXT: Color = (230, 236, 248)
MUTED: Color = (126, 146, 174)
LEFT: Color = (82, 160, 255)
RIGHT: Color = (255, 138, 76)
GAZE: Color = (160, 255, 190)
CHEST: Color = (220, 220, 220)
PANEL: Color = (18, 24, 36)
PANEL_LINE: Color = (58, 70, 96)


def _load(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _load_or_build_stats(path: Path) -> dict[str, Any]:
    if path.is_file():
        return _load(path)
    from demo.comparison_stats import write_stats

    return write_stats()


def _hand_points(frame: dict[str, Any], channel: str) -> list[tuple[float, float, float]]:
    values = frame["pose"][channel]["joints"]["values"]
    return [
        (float(values[i]), float(values[i + 1]), float(values[i + 2]))
        for i in range(0, len(values), 3)
    ]


def _lerp(a: float, b: float, u: float) -> float:
    return a + (b - a) * u


def _mix(a: Color, b: Color, u: float) -> Color:
    return (
        int(_lerp(a[0], b[0], u)),
        int(_lerp(a[1], b[1], u)),
        int(_lerp(a[2], b[2], u)),
    )


def _lerp_points(
    a: list[tuple[float, float, float]], b: list[tuple[float, float, float]], u: float
) -> list[tuple[float, float, float]]:
    return [
        (
            _lerp(pa[0], pb[0], u),
            _lerp(pa[1], pb[1], u),
            _lerp(pa[2], pb[2], u),
        )
        for pa, pb in zip(a, b)
    ]


def _sample(doc: dict[str, Any], t: float) -> dict[str, Any]:
    frames = doc["timeline"]
    if t <= frames[0]["t"]:
        src = frames[0]
        return {
            "t": src["t"],
            "pose": {
                "left_hand": {
                    "points": _hand_points(src, "left_hand"),
                    "state_index": src["pose"]["left_hand"]["state_index"],
                },
                "right_hand": {
                    "points": _hand_points(src, "right_hand"),
                    "state_index": src["pose"]["right_hand"]["state_index"],
                },
                "gaze": {"dir": src["pose"]["gaze"]["dir"]},
            },
        }
    if t >= frames[-1]["t"]:
        src = frames[-1]
        return {
            "t": src["t"],
            "pose": {
                "left_hand": {
                    "points": _hand_points(src, "left_hand"),
                    "state_index": src["pose"]["left_hand"]["state_index"],
                },
                "right_hand": {
                    "points": _hand_points(src, "right_hand"),
                    "state_index": src["pose"]["right_hand"]["state_index"],
                },
                "gaze": {"dir": src["pose"]["gaze"]["dir"]},
            },
        }

    for i in range(len(frames) - 1):
        a = frames[i]
        b = frames[i + 1]
        if a["t"] <= t <= b["t"]:
            u = (t - a["t"]) / (b["t"] - a["t"])
            left = _lerp_points(_hand_points(a, "left_hand"), _hand_points(b, "left_hand"), u)
            right = _lerp_points(_hand_points(a, "right_hand"), _hand_points(b, "right_hand"), u)
            gaze_a = a["pose"]["gaze"]["dir"]
            gaze_b = b["pose"]["gaze"]["dir"]
            gaze = [_lerp(float(gaze_a[j]), float(gaze_b[j]), u) for j in range(3)]
            return {
                "t": t,
                "pose": {
                    "left_hand": {"points": left, "state_index": a["pose"]["left_hand"]["state_index"]},
                    "right_hand": {"points": right, "state_index": a["pose"]["right_hand"]["state_index"]},
                    "gaze": {"dir": gaze},
                },
            }
    return frames[-1]


class Canvas:
    def __init__(self, width: int, height: int, bg: Color) -> None:
        self.width = width
        self.height = height
        self.pixels = bytearray(bg * (width * height))

    def set_px(self, x: int, y: int, color: Color) -> None:
        if 0 <= x < self.width and 0 <= y < self.height:
            idx = (y * self.width + x) * 3
            self.pixels[idx : idx + 3] = bytes(color)

    def line(self, x0: int, y0: int, x1: int, y1: int, color: Color, thickness: int = 1) -> None:
        dx = abs(x1 - x0)
        sx = 1 if x0 < x1 else -1
        dy = -abs(y1 - y0)
        sy = 1 if y0 < y1 else -1
        err = dx + dy
        while True:
            self.circle(x0, y0, max(0, thickness - 1), color)
            if x0 == x1 and y0 == y1:
                break
            e2 = 2 * err
            if e2 >= dy:
                err += dy
                x0 += sx
            if e2 <= dx:
                err += dx
                y0 += sy

    def circle(self, cx: int, cy: int, r: int, color: Color) -> None:
        if r <= 0:
            self.set_px(cx, cy, color)
            return
        rr = r * r
        for y in range(cy - r, cy + r + 1):
            for x in range(cx - r, cx + r + 1):
                if (x - cx) * (x - cx) + (y - cy) * (y - cy) <= rr:
                    self.set_px(x, y, color)

    def rect(self, x0: int, y0: int, x1: int, y1: int, color: Color) -> None:
        for y in range(max(0, y0), min(self.height, y1)):
            for x in range(max(0, x0), min(self.width, x1)):
                self.set_px(x, y, color)

    def rect_outline(self, x0: int, y0: int, x1: int, y1: int, color: Color) -> None:
        self.line(x0, y0, x1, y0, color)
        self.line(x1, y0, x1, y1, color)
        self.line(x1, y1, x0, y1, color)
        self.line(x0, y1, x0, y0, color)

    def write_ppm(self, path: Path) -> None:
        header = f"P6\n{self.width} {self.height}\n255\n".encode("ascii")
        path.write_bytes(header + self.pixels)


# Tiny 5x7 bitmap font for labels without external dependencies.
FONT: dict[str, list[str]] = {
    " ": ["00000"] * 7,
    ".": ["00000", "00000", "00000", "00000", "00000", "01100", "01100"],
    ":": ["00000", "01100", "01100", "00000", "01100", "01100", "00000"],
    "-": ["00000", "00000", "00000", "11111", "00000", "00000", "00000"],
    "_": ["00000", "00000", "00000", "00000", "00000", "00000", "11111"],
    "/": ["00001", "00010", "00100", "01000", "10000", "00000", "00000"],
    "0": ["01110", "10001", "10011", "10101", "11001", "10001", "01110"],
    "1": ["00100", "01100", "00100", "00100", "00100", "00100", "01110"],
    "2": ["01110", "10001", "00001", "00010", "00100", "01000", "11111"],
    "3": ["11110", "00001", "00001", "01110", "00001", "00001", "11110"],
    "4": ["00010", "00110", "01010", "10010", "11111", "00010", "00010"],
    "5": ["11111", "10000", "11110", "00001", "00001", "10001", "01110"],
    "6": ["00110", "01000", "10000", "11110", "10001", "10001", "01110"],
    "7": ["11111", "00001", "00010", "00100", "01000", "01000", "01000"],
    "8": ["01110", "10001", "10001", "01110", "10001", "10001", "01110"],
    "9": ["01110", "10001", "10001", "01111", "00001", "00010", "11100"],
}


def _font_rows(ch: str) -> list[str]:
    if ch in FONT:
        return FONT[ch]
    c = ch.upper()
    raw = {
        "A": ["01110", "10001", "10001", "11111", "10001", "10001", "10001"],
        "B": ["11110", "10001", "10001", "11110", "10001", "10001", "11110"],
        "C": ["01110", "10001", "10000", "10000", "10000", "10001", "01110"],
        "D": ["11110", "10001", "10001", "10001", "10001", "10001", "11110"],
        "E": ["11111", "10000", "10000", "11110", "10000", "10000", "11111"],
        "F": ["11111", "10000", "10000", "11110", "10000", "10000", "10000"],
        "G": ["01110", "10001", "10000", "10111", "10001", "10001", "01110"],
        "H": ["10001", "10001", "10001", "11111", "10001", "10001", "10001"],
        "I": ["01110", "00100", "00100", "00100", "00100", "00100", "01110"],
        "J": ["00001", "00001", "00001", "00001", "10001", "10001", "01110"],
        "K": ["10001", "10010", "10100", "11000", "10100", "10010", "10001"],
        "L": ["10000", "10000", "10000", "10000", "10000", "10000", "11111"],
        "M": ["10001", "11011", "10101", "10101", "10001", "10001", "10001"],
        "N": ["10001", "11001", "10101", "10011", "10001", "10001", "10001"],
        "O": ["01110", "10001", "10001", "10001", "10001", "10001", "01110"],
        "P": ["11110", "10001", "10001", "11110", "10000", "10000", "10000"],
        "Q": ["01110", "10001", "10001", "10001", "10101", "10010", "01101"],
        "R": ["11110", "10001", "10001", "11110", "10100", "10010", "10001"],
        "S": ["01111", "10000", "10000", "01110", "00001", "00001", "11110"],
        "T": ["11111", "00100", "00100", "00100", "00100", "00100", "00100"],
        "U": ["10001", "10001", "10001", "10001", "10001", "10001", "01110"],
        "V": ["10001", "10001", "10001", "10001", "10001", "01010", "00100"],
        "W": ["10001", "10001", "10001", "10101", "10101", "11011", "10001"],
        "X": ["10001", "10001", "01010", "00100", "01010", "10001", "10001"],
        "Y": ["10001", "10001", "01010", "00100", "00100", "00100", "00100"],
        "Z": ["11111", "00001", "00010", "00100", "01000", "10000", "11111"],
    }
    return raw.get(c, FONT[" "])


def draw_text(canvas: Canvas, x: int, y: int, text: str, color: Color, scale: int = 3) -> None:
    cursor = x
    for ch in text:
        rows = _font_rows(ch)
        for yy, row in enumerate(rows):
            for xx, bit in enumerate(row):
                if bit == "1":
                    canvas.rect(
                        cursor + xx * scale,
                        y + yy * scale,
                        cursor + (xx + 1) * scale,
                        y + (yy + 1) * scale,
                        color,
                    )
        cursor += 6 * scale


def project(p: tuple[float, float, float] | list[float]) -> tuple[int, int]:
    # Orthographic front view: x horizontal, y vertical; z subtly shifts depth upward.
    x, y, z = float(p[0]), float(p[1]), float(p[2])
    sx = WIDTH // 2 + int(x * 760)
    sy = HEIGHT - 80 - int((y - 0.8) * 650) - int(z * 75)
    return sx, sy


def _draw_grid(c: Canvas) -> None:
    for x in range(140, WIDTH - 140, 80):
        c.line(x, 90, x, HEIGHT - 90, GRID)
    for y in range(110, HEIGHT - 90, 60):
        c.line(140, y, WIDTH - 140, y, GRID)
    c.line(WIDTH // 2, 90, WIDTH // 2, HEIGHT - 90, (52, 64, 88), 1)


def _draw_trails(c: Canvas, doc: dict[str, Any], t: float) -> None:
    trail_steps = 10
    trail_span = 0.42
    for step in range(trail_steps, 0, -1):
        past_t = max(0.0, t - (trail_span * step / trail_steps))
        sample = _sample(doc, past_t)
        fade = step / trail_steps
        for channel, base in (("left_hand", LEFT), ("right_hand", RIGHT)):
            pts = sample["pose"][channel]["points"]
            root = project(pts[0])
            tip = project(pts[2])
            color = _mix(base, BG, fade * 0.78)
            c.line(root[0], root[1], tip[0], tip[1], color, max(1, 4 - step // 3))
            c.circle(tip[0], tip[1], max(1, 5 - step // 3), color)


def _draw_particles(c: Canvas, t: float) -> None:
    for i in range(34):
        phase = i * 0.37
        x = 180 + int(((math.sin(t * 1.9 + phase) + 1) / 2) * (WIDTH - 360))
        y = 130 + int(((math.cos(t * 1.3 + phase * 1.7) + 1) / 2) * (HEIGHT - 280))
        r = 1 + (i % 3)
        c.circle(x, y, r, (30 + i % 30, 42 + i % 22, 62 + i % 28))


def _draw_hand(
    c: Canvas, points: list[tuple[float, float, float]], color: Color, label: str
) -> None:
    screen = [project(p) for p in points]
    root = screen[0]
    for pt in screen[1:]:
        c.line(root[0], root[1], pt[0], pt[1], color, 4)
    c.circle(root[0], root[1], 10, color)
    for pt in screen[1:]:
        c.circle(pt[0], pt[1], 8, color)
    draw_text(c, root[0] - 42, root[1] + 22, label, color, 2)


def _stat_bytes(stats: dict[str, Any], name: str) -> int:
    for item in stats["artifacts"]:
        if item["name"] == name:
            return int(item["bytes"])
    return 0


def _draw_pipeline_panel(
    c: Canvas, doc: dict[str, Any], stats: dict[str, Any], t: float, total_t: float
) -> None:
    x0, y0, x1, y1 = 820, 108, 1228, 326
    c.rect(x0, y0, x1, y1, PANEL)
    c.rect_outline(x0, y0, x1, y1, PANEL_LINE)
    draw_text(c, x0 + 18, y0 + 18, "PIPELINE", TEXT, 3)

    sgm_bytes = _stat_bytes(stats, ".sgm v1 bytecode")
    rows = [
        (".gest JSON", "validated IR"),
        ("IR invariants", "joint stride / states"),
        (".sgm v1", f"{sgm_bytes} byte runtime clip"),
        ("debug path", "dump / recover / diff"),
    ]
    yy = y0 + 62
    for i, (left, right) in enumerate(rows):
        color = GAZE if i == min(3, int((t / max(total_t, 0.01)) * 4)) else MUTED
        draw_text(c, x0 + 18, yy, left, color, 2)
        draw_text(c, x0 + 210, yy, right, MUTED, 2)
        yy += 34

    bar_x0, bar_y0 = x0 + 18, y1 - 34
    bar_x1 = x1 - 18
    c.rect(bar_x0, bar_y0, bar_x1, bar_y0 + 10, (34, 42, 58))
    filled = bar_x0 + int((bar_x1 - bar_x0) * min(1.0, t / max(total_t, 0.01)))
    c.rect(bar_x0, bar_y0, filled, bar_y0 + 10, GAZE)


def _draw_comparison_panel(c: Canvas, stats: dict[str, Any]) -> None:
    x0, y0, x1, y1 = 820, 350, 1228, 608
    c.rect(x0, y0, x1, y1, PANEL)
    c.rect_outline(x0, y0, x1, y1, PANEL_LINE)
    draw_text(c, x0 + 18, y0 + 18, "REAL SIZE STATS", TEXT, 3)
    rows = [
        (".SGM", _stat_bytes(stats, ".sgm v1 bytecode"), GAZE),
        ("GEST.GZ", _stat_bytes(stats, ".gest JSON gzip"), LEFT),
        ("LANDMARK", _stat_bytes(stats, "Landmark JSON baseline"), MUTED),
        ("BVH-LIKE", _stat_bytes(stats, "BVH-like text baseline"), MUTED),
        ("CSV", _stat_bytes(stats, "CSV landmarks baseline"), MUTED),
        ("GEST JSON", _stat_bytes(stats, ".gest JSON compact"), RIGHT),
    ]
    max_bytes = max(size for _, size, _ in rows)
    yy = y0 + 56
    for name, size, color in rows:
        draw_text(c, x0 + 18, yy, name, color, 2)
        bar_x = x0 + 132
        bar_w = int((x1 - bar_x - 86) * (size / max_bytes))
        c.rect(bar_x, yy + 2, x1 - 74, yy + 14, (32, 40, 58))
        c.rect(bar_x, yy + 2, bar_x + bar_w, yy + 14, color)
        draw_text(c, x1 - 66, yy, str(size), TEXT, 2)
        yy += 30
    draw_text(c, x0 + 18, y1 - 28, "measured from this generated clip", MUTED, 2)


def _draw_bytecode_strip(c: Canvas, frame_index: int) -> None:
    x0, y0 = 50, 604
    draw_text(c, x0, y0 - 28, "SGM OPCODES", MUTED, 2)
    ops = ["30", "31", "32", "31", "32", "33", "30", "31", "FF"]
    for i, op in enumerate(ops):
        x = x0 + i * 52
        active = (frame_index + i) % 9 < 4
        c.rect(x, y0, x + 38, y0 + 28, GAZE if active else (35, 44, 62))
        draw_text(c, x + 8, y0 + 7, op, BG if active else TEXT, 2)


def _draw_spectacle_rings(c: Canvas, t: float) -> None:
    center = project([0.0, 1.25, 0.32])
    for i in range(6):
        rx = 150 + i * 34 + int(math.sin(t * 2.2 + i) * 12)
        ry = 56 + i * 10
        color = _mix(GAZE if i % 2 == 0 else LEFT, BG, 0.35 + i * 0.08)
        # Draw ellipse with many short line segments.
        prev: tuple[int, int] | None = None
        for step in range(80):
            a = step / 80 * math.tau + t * 0.45
            x = center[0] + int(math.cos(a) * rx)
            y = center[1] + int(math.sin(a) * ry)
            if prev is not None:
                c.line(prev[0], prev[1], x, y, color)
            prev = (x, y)


def _draw_frame(
    c: Canvas, doc: dict[str, Any], stats: dict[str, Any], t: float, frame_index: int, total: int
) -> None:
    _draw_grid(c)
    _draw_particles(c, t)
    _draw_spectacle_rings(c, t)
    _draw_trails(c, doc, t)
    sample = _sample(doc, t)
    left = sample["pose"]["left_hand"]["points"]
    right = sample["pose"]["right_hand"]["points"]
    gaze = sample["pose"]["gaze"]["dir"]

    chest = project([0.0, 1.05, 0.0])
    head = project([0.0, 1.58, 0.0])
    c.line(chest[0], chest[1], head[0], head[1], CHEST, 5)
    c.circle(chest[0], chest[1], 13, CHEST)
    c.circle(head[0], head[1], 18, CHEST)

    gaze_end = project([gaze[0] * 0.35, 1.58 + gaze[1] * 0.35, gaze[2] * 0.35])
    c.line(head[0], head[1], gaze_end[0], gaze_end[1], GAZE, 3)
    c.circle(gaze_end[0], gaze_end[1], 6, GAZE)

    _draw_hand(c, left, LEFT, "LEFT")
    _draw_hand(c, right, RIGHT, "RIGHT")

    draw_text(c, 50, 34, ".gest cinematic demo", TEXT, 4)
    draw_text(c, 52, 82, "dual hands + gaze + timeline + real artifact stats", MUTED, 2)
    _draw_pipeline_panel(c, doc, stats, t, float(doc["timeline"][-1]["t"]))
    _draw_comparison_panel(c, stats)
    _draw_bytecode_strip(c, frame_index)
    draw_text(c, 50, HEIGHT - 64, f"t={t:0.2f}s  frame={frame_index + 1}/{total}", TEXT, 3)
    draw_text(c, WIDTH - 392, HEIGHT - 64, "blue=left orange=right green=gaze", MUTED, 2)


def render_video(input_path: Path, output_path: Path) -> None:
    ffmpeg = shutil.which("ffmpeg")
    if not ffmpeg:
        raise RuntimeError("ffmpeg is required to encode the MP4 video")

    doc = _load(input_path)
    stats = _load_or_build_stats(DEFAULT_STATS)
    frames = doc["timeline"]
    duration = float(frames[-1]["t"]) + SECONDS_PAD
    total = int(math.ceil(duration * FPS))

    frame_dir = output_path.parent / "frames"
    if frame_dir.exists():
        for p in frame_dir.glob("*.ppm"):
            p.unlink()
    else:
        frame_dir.mkdir(parents=True, exist_ok=True)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    for idx in range(total):
        t = min(float(frames[-1]["t"]), idx / FPS)
        c = Canvas(WIDTH, HEIGHT, BG)
        _draw_frame(c, doc, stats, t, idx, total)
        c.write_ppm(frame_dir / f"frame_{idx:04d}.ppm")

    cmd = [
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
    ]
    subprocess.run(cmd, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description="Render the .gest demo clip to MP4.")
    p.add_argument("--input", type=Path, default=DEFAULT_INPUT, help="Input .gest JSON")
    p.add_argument("--output", type=Path, default=DEFAULT_OUTPUT, help="Output MP4 path")
    args = p.parse_args(argv)

    render_video(args.input, args.output)
    print(f"Wrote video demo -> {args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
