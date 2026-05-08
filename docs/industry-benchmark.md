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

### XR dual-hand arc

- Frames: `9`
- Channels: `gaze, left_hand, right_hand`
- Sample floats: `297`
- Decoded SGM ops: `54`

| Artifact | Kind | Bytes | Ratio to `.sgm` |
|----------|------|-------|-----------------|
| `.sgm v1 bytecode` | `gest-runtime` | 1562 | 1.0x |
| `.gest JSON compact` | `gest-ir` | 4679 | 2.996x |
| `MediaPipe-like landmark JSON` | `industry-like` | 5897 | 3.775x |
| `OpenXR-like action trace JSON` | `industry-like` | 14914 | 9.548x |
| `glTF animation JSON shape` | `industry-like` | 5488 | 3.513x |
| `BVH-like skeleton text` | `industry-like` | 3019 | 1.933x |
| `ROS-like JSONL topics` | `industry-like` | 18710 | 11.978x |
| `CSV rows` | `baseline` | 4121 | 2.638x |

### Robot teleoperation reach

- Frames: `14`
- Channels: `gaze, right_hand`
- Sample floats: `210`
- Decoded SGM ops: `56`

| Artifact | Kind | Bytes | Ratio to `.sgm` |
|----------|------|-------|-----------------|
| `.sgm v1 bytecode` | `gest-runtime` | 1211 | 1.0x |
| `.gest JSON compact` | `gest-ir` | 3547 | 2.929x |
| `MediaPipe-like landmark JSON` | `industry-like` | 4419 | 3.649x |
| `OpenXR-like action trace JSON` | `industry-like` | 10455 | 8.633x |
| `glTF animation JSON shape` | `industry-like` | 2878 | 2.377x |
| `BVH-like skeleton text` | `industry-like` | 1633 | 1.348x |
| `ROS-like JSONL topics` | `industry-like` | 12558 | 10.37x |
| `CSV rows` | `baseline` | 3022 | 2.495x |

### Rehabilitation symmetry loop

- Frames: `20`
- Channels: `gaze, left_hand, right_hand`
- Sample floats: `780`
- Decoded SGM ops: `120`

| Artifact | Kind | Bytes | Ratio to `.sgm` |
|----------|------|-------|-----------------|
| `.sgm v1 bytecode` | `gest-runtime` | 3890 | 1.0x |
| `.gest JSON compact` | `gest-ir` | 9330 | 2.398x |
| `MediaPipe-like landmark JSON` | `industry-like` | 15139 | 3.892x |
| `OpenXR-like action trace JSON` | `industry-like` | 39287 | 10.099x |
| `glTF animation JSON shape` | `industry-like` | 9941 | 2.556x |
| `BVH-like skeleton text` | `industry-like` | 6067 | 1.56x |
| `ROS-like JSONL topics` | `industry-like` | 49968 | 12.845x |
| `CSV rows` | `baseline` | 11202 | 2.88x |

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

