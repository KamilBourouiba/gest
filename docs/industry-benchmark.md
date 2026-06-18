# Industry benchmark

This benchmark compares `.gest` / `.sgm` against concrete industry-like shapes generated from the same numeric samples.

## Methodology

- All artifacts are generated from the same valid .gest scenario documents.
- Industry comparisons are concrete JSON/text shapes inspired by common standards and APIs, not certified exporters.
- glTF is represented as a JSON animation shape; binary GLB packing is intentionally not claimed.
- OpenXR and MediaPipe are APIs/model outputs, so the benchmark uses durable trace shapes for byte comparison.
- Ratios are relative to .sgm v1 bytecode for the same scenario.

## Where `.gest` / `.sgm` is better in this artifact

- SGM bytecode is smaller than compact .gest JSON, MediaPipe-like JSON, OpenXR-like traces, glTF-like JSON, ROS-like JSONL, and CSV rows in every generated scenario.
- SGM bytecode is smaller than BVH-like text in three of four scenarios; the tiny pose7 microclip is the measured exception.
- .gest JSON keeps a stronger validation contract than landmark JSON, BVH-like text, OpenXR-like traces, and ROS-like logs.
- .gest/.sgm preserve a non-semantic execution path; labels or meanings can stay in sidecar governance systems.
- .sgm is directly designed as a runtime artifact, unlike authoring/container/API trace formats.

## Where it is not better

- glTF/VRM are better for shipping meshes, materials, avatars, and full scenes.
- OpenXR is better for live device access.
- MediaPipe is better for extracting landmarks from images/video.
- ROS bags are better for full multi-topic robotics telemetry.
- Compression layers such as gzip can beat small bytecode on tiny repetitive JSON clips, but they are transport/archive layers.

## Scenario measurements

### XR pinch & grasp

- Frames: `32`
- Channels: `gaze, left_hand, right_hand`
- Sample floats: `1056`
- Decoded SGM ops: `192`

| Artifact | Kind | Bytes | Ratio to `.sgm` |
|----------|------|-------|-----------------|
| `.sgm v1 bytecode` | `gest-runtime` | 5426 | 1.0x |
| `.gest JSON compact` | `gest-ir` | 13529 | 2.493x |
| `MediaPipe-like landmark JSON` | `industry-like` | 21022 | 3.874x |
| `OpenXR-like action trace JSON` | `industry-like` | 53036 | 9.774x |
| `glTF animation JSON shape` | `industry-like` | 11183 | 2.061x |
| `BVH-like skeleton text` | `industry-like` | 7235 | 1.333x |
| `ROS-like JSONL topics` | `industry-like` | 67101 | 12.367x |
| `CSV rows` | `baseline` | 15091 | 2.781x |

### Assembly pick & place

- Frames: `40`
- Channels: `gaze, right_hand`
- Sample floats: `720`
- Decoded SGM ops: `160`

| Artifact | Kind | Bytes | Ratio to `.sgm` |
|----------|------|-------|-----------------|
| `.sgm v1 bytecode` | `gest-runtime` | 3875 | 1.0x |
| `.gest JSON compact` | `gest-ir` | 9667 | 2.495x |
| `MediaPipe-like landmark JSON` | `industry-like` | 14493 | 3.74x |
| `OpenXR-like action trace JSON` | `industry-like` | 35881 | 9.26x |
| `glTF animation JSON shape` | `industry-like` | 6652 | 1.717x |
| `BVH-like skeleton text` | `industry-like` | 4364 | 1.126x |
| `ROS-like JSONL topics` | `industry-like` | 43920 | 11.334x |
| `CSV rows` | `baseline` | 10294 | 2.657x |

### Presentation sweep

- Frames: `36`
- Channels: `gaze, right_hand`
- Sample floats: `648`
- Decoded SGM ops: `144`

| Artifact | Kind | Bytes | Ratio to `.sgm` |
|----------|------|-------|-----------------|
| `.sgm v1 bytecode` | `gest-runtime` | 3491 | 1.0x |
| `.gest JSON compact` | `gest-ir` | 8804 | 2.522x |
| `MediaPipe-like landmark JSON` | `industry-like` | 13044 | 3.736x |
| `OpenXR-like action trace JSON` | `industry-like` | 32323 | 9.259x |
| `glTF animation JSON shape` | `industry-like` | 6143 | 1.76x |
| `BVH-like skeleton text` | `industry-like` | 4005 | 1.147x |
| `ROS-like JSONL topics` | `industry-like` | 39520 | 11.321x |
| `CSV rows` | `baseline` | 9262 | 2.653x |

### Rehabilitation symmetry loop

- Frames: `28`
- Channels: `gaze, left_hand, right_hand`
- Sample floats: `1092`
- Decoded SGM ops: `168`

| Artifact | Kind | Bytes | Ratio to `.sgm` |
|----------|------|-------|-----------------|
| `.sgm v1 bytecode` | `gest-runtime` | 5426 | 1.0x |
| `.gest JSON compact` | `gest-ir` | 12738 | 2.348x |
| `MediaPipe-like landmark JSON` | `industry-like` | 21187 | 3.905x |
| `OpenXR-like action trace JSON` | `industry-like` | 54999 | 10.136x |
| `glTF animation JSON shape` | `industry-like` | 12255 | 2.259x |
| `BVH-like skeleton text` | `industry-like` | 7829 | 1.443x |
| `ROS-like JSONL topics` | `industry-like` | 69968 | 12.895x |
| `CSV rows` | `baseline` | 15674 | 2.889x |

### Robot teleoperation reach

- Frames: `24`
- Channels: `gaze, right_hand`
- Sample floats: `432`
- Decoded SGM ops: `96`

| Artifact | Kind | Bytes | Ratio to `.sgm` |
|----------|------|-------|-----------------|
| `.sgm v1 bytecode` | `gest-runtime` | 2339 | 1.0x |
| `.gest JSON compact` | `gest-ir` | 6091 | 2.604x |
| `MediaPipe-like landmark JSON` | `industry-like` | 8757 | 3.744x |
| `OpenXR-like action trace JSON` | `industry-like` | 21633 | 9.249x |
| `glTF animation JSON shape` | `industry-like` | 4772 | 2.04x |
| `BVH-like skeleton text` | `industry-like` | 2964 | 1.267x |
| `ROS-like JSONL topics` | `industry-like` | 26424 | 11.297x |
| `CSV rows` | `baseline` | 6270 | 2.681x |

### Dataset pose7 microclip

- Frames: `8`
- Channels: `gaze, left_hand, right_hand`
- Sample floats: `360`
- Decoded SGM ops: `48`

| Artifact | Kind | Bytes | Ratio to `.sgm` |
|----------|------|-------|-----------------|
| `.sgm v1 bytecode` | `gest-runtime` | 1778 | 1.0x |
| `.gest JSON compact` | `gest-ir` | 4131 | 2.323x |
| `MediaPipe-like landmark JSON` | `industry-like` | 3703 | 2.083x |
| `OpenXR-like action trace JSON` | `industry-like` | 8399 | 4.724x |
| `glTF animation JSON shape` | `industry-like` | 3247 | 1.826x |
| `BVH-like skeleton text` | `industry-like` | 1755 | 0.987x |
| `ROS-like JSONL topics` | `industry-like` | 10260 | 5.771x |
| `CSV rows` | `baseline` | 2898 | 1.63x |

