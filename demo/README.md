# Real demo: XR-style dual-hand motion clip

This directory contains a runnable end-to-end demo for `.gest`:

1. Generate a deterministic `.gest` document with two simplified 5-point hands and one gaze channel.
2. Validate it with JSON Schema + IR invariants.
3. Compile it to `.sgm` v1 bytecode.
4. Decode the bytecode back to a human-readable dump.
5. Recover a draft `.gest` document from the bytecode.
6. Render the motion clip as an MP4 video.
7. Drive a simple humanoid avatar rig from the same `.gest` channels.
8. Play the clip in a real WebGL 3D breakthrough lab with an orbiting camera, measured stats, pipeline stages, and a bytecode stream.

The clip is intentionally **non-semantic**. It looks like a coordinated dual-hand arc in front of the torso, but the file does not say what the motion means. It only stores anchors, channels, joint coordinates, state indices, gaze direction, and time.

The video renderer is intentionally presentation-oriented: it adds trails, a status panel, a bytecode strip, and a compact comparison panel against common formats. Those visual overlays are **not** stored in `.gest`; they are generated from the motion data for demos and reviews.

The comparison numbers shown in the video are measured by `demo/comparison_stats.py` from the generated clip itself. They are not hand-written marketing values.

## Run

From the repository root:

```bash
python demo/run_demo.py
```

With the editable package installed:

```bash
pip install -e ".[dev]"
python demo/run_demo.py
gest-validate demo/xr_dual_hand_arc.gest.json
gest-dump-sgm demo/out/xr_dual_hand_arc.sgm
gest-sgm-to-gest demo/out/xr_dual_hand_arc.sgm demo/out/recovered_from_cli.gest.json
python demo/render_video.py
python demo/render_avatar_video.py
python demo/comparison_stats.py
python demo/multi_demos.py
python demo/industry_benchmark.py
python demo/research_artifact.py
```

Avatar viewers:

```bash
python -m http.server 8000
open http://localhost:8000/demo/avatar_viewer.html
open http://localhost:8000/demo/avatar_3d_viewer.html
```

## Generated files

`run_demo.py` writes:

| File | Purpose |
|------|---------|
| `demo/xr_dual_hand_arc.gest.json` | Source `.gest` clip (committable, readable JSON) |
| `demo/out/xr_dual_hand_arc.sgm` | Runtime bytecode artifact |
| `demo/out/xr_dual_hand_arc.dump.json` | Decoded channel table + timeline for debugging |
| `demo/out/xr_dual_hand_arc.recovered.gest.json` | Lossy draft `.gest` recovered from `.sgm` |
| `demo/out/xr_dual_hand_arc.mp4` | Rendered video preview |
| `demo/out/xr_avatar_playback.mp4` | Stylized avatar playback video |
| `demo/avatar_viewer.html` | Browser viewer that plays `.gest` on an avatar rig |
| `demo/avatar_3d_viewer.html` | WebGL 3D avatar viewer with perspective camera |
| `demo/out/comparison-stats.json` | Machine-readable measured comparison stats |
| `docs/comparison-stats.md` | Human-readable measured comparison stats |
| `demo/generated/*.gest.json` | Multiple real-life scenario demos |
| `demo/out/*_*.sgm` | SGM bytecode for generated scenarios |
| `demo/out/multi-demo-stats.json` | Machine-readable multi-scenario comparison stats |
| `docs/multi-demo-stats.md` | Human-readable multi-scenario comparison stats |
| `demo/out/industry-benchmark.json` | Machine-readable industry-facing benchmark |
| `docs/industry-benchmark.md` | Human-readable comparison against BVH/glTF/OpenXR/MediaPipe/ROS-like shapes |
| `demo/out/research-artifact-manifest.json` | Machine-readable reproducibility manifest |
| `docs/research-artifact-manifest.md` | Human-readable reproducibility manifest with hashes |

`demo/out/` is ignored by Git because those are generated artifacts.

## WebGL breakthrough lab

`demo/avatar_3d_viewer.html` is the most complete interactive demo. It loads the same `.gest` clip, plays it on a 3D avatar, and overlays the full runtime story:

- `.gest -> validate -> .sgm -> decode -> avatar` pipeline stages.
- Measured artifact sizes from `demo/out/comparison-stats.json`.
- Multi-scenario benchmark results from `demo/out/multi-demo-stats.json`.
- A bytecode-style stream synchronized with the playback timeline.

If the page is opened directly from the filesystem, it falls back to an embedded clip so the Play button still works. To show the measured comparison panels, serve the repository root with `python -m http.server 8000` after running `python demo/run_demo.py`, `python demo/comparison_stats.py`, and `python demo/multi_demos.py`.

## What this demonstrates

- **Motion capture ingest:** a sensor or rig can emit `.gest` as a stable interchange file.
- **CI validation:** bad frame shapes fail before runtime (`joint_count * joint_value_stride`, state bounds, direction length).
- **Runtime packaging:** `.gest` compiles to compact `.sgm` bytecode.
- **Device debugging:** a runtime artifact can be decoded and compared in Git-friendly JSON form.
- **Visual review:** the same clip can be rendered to MP4 for a README, design review, or QA report.
- **Avatar playback:** the same `.gest` hand/gaze channels can drive a simple humanoid rig.
- **3D playback:** the WebGL breakthrough lab uses perspective projection, orbit camera, trails, live pipeline status, bytecode visualization, and measured comparison panels.
- **Format positioning:** the overlay highlights why `.gest` is an IR layer rather than a replacement for every existing animation format.
- **Measured comparison:** the stats compare `.sgm`, `.gest` JSON/gzip, CSV, landmark JSON, and BVH-like baselines generated from the same clip.
- **Multi-scenario benchmarking:** generated demos compare `.sgm`, JSON, YAML, CSV, landmark JSON, and BVH-like text across XR, robot teleoperation, rehabilitation, and dataset microclip cases.
- **Industry-facing comparison:** generated demos are also transformed into BVH-like, glTF animation JSON-like, OpenXR trace-like, MediaPipe landmark-like, and ROS JSONL-like artifacts to show exactly where `.gest` / `.sgm` is smaller or stricter.
- **Research archiving:** the artifact manifest records claims, aggregate benchmark evidence, SGM version identity, and SHA-256 hashes for important generated files.

