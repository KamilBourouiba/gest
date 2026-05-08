# Multi-demo comparison stats

Measured from generated `.gest` scenarios in `demo/generated/`.

## Methodology

- Each scenario is generated as a valid .gest document.
- All byte counts are measured from local artifacts produced from the same numeric samples.
- CSV, landmark JSON, and BVH-like baselines are concrete transforms, not official exporters.
- Ratios are relative to .sgm v1 bytecode for that same scenario.

## XR dual-hand arc

A headset or depth-camera clip records coordinated hand motion and gaze for QA replay.

- Frames: `9`
- Duration: `1.2s`
- Channels: `gaze, left_hand, right_hand`
- Sample floats: `297`
- Decoded opcodes: `54`

| Artifact | Kind | Bytes | Ratio to `.sgm` |
|----------|------|-------|-----------------|
| `.sgm v1 bytecode` | `binary` | 1562 | 1.0x |
| `.gest JSON compact` | `json` | 4679 | 2.996x |
| `.gest JSON pretty` | `json` | 12477 | 7.988x |
| `.gest JSON gzip` | `gzip` | 1366 | 0.875x |
| `.gest YAML` | `yaml` | 8245 | 5.278x |
| `Landmark JSON baseline` | `json` | 2536 | 1.624x |
| `CSV rows baseline` | `csv` | 4124 | 2.64x |
| `BVH-like text baseline` | `bvh-like` | 3319 | 2.125x |

## Robot teleoperation reach

A remote operator guides a gripper-like end effector toward a target while gaze stays locked on the workspace.

- Frames: `14`
- Duration: `1.6s`
- Channels: `gaze, right_hand`
- Sample floats: `210`
- Decoded opcodes: `56`

| Artifact | Kind | Bytes | Ratio to `.sgm` |
|----------|------|-------|-----------------|
| `.sgm v1 bytecode` | `binary` | 1211 | 1.0x |
| `.gest JSON compact` | `json` | 3547 | 2.929x |
| `.gest JSON pretty` | `json` | 9627 | 7.95x |
| `.gest JSON gzip` | `gzip` | 942 | 0.778x |
| `.gest YAML` | `yaml` | 6044 | 4.991x |
| `Landmark JSON baseline` | `json` | 2123 | 1.753x |
| `CSV rows baseline` | `csv` | 3025 | 2.498x |
| `BVH-like text baseline` | `bvh-like` | 2026 | 1.673x |

## Rehabilitation symmetry loop

A practice session records bilateral hand movement quality without storing any natural-language instruction or patient notes.

- Frames: `20`
- Duration: `2.2s`
- Channels: `gaze, left_hand, right_hand`
- Sample floats: `780`
- Decoded opcodes: `120`

| Artifact | Kind | Bytes | Ratio to `.sgm` |
|----------|------|-------|-----------------|
| `.sgm v1 bytecode` | `binary` | 3890 | 1.0x |
| `.gest JSON compact` | `json` | 9330 | 2.398x |
| `.gest JSON pretty` | `json` | 26919 | 6.92x |
| `.gest JSON gzip` | `gzip` | 1819 | 0.468x |
| `.gest YAML` | `yaml` | 18010 | 4.63x |
| `Landmark JSON baseline` | `json` | 6517 | 1.675x |
| `CSV rows baseline` | `csv` | 11205 | 2.88x |
| `BVH-like text baseline` | `bvh-like` | 6534 | 1.68x |

## Dataset pose7 microclip

A compact benchmark clip preserves joint translations and quaternions while keeping gloss/meaning labels in a separate approved manifest.

- Frames: `8`
- Duration: `0.7s`
- Channels: `gaze, left_hand, right_hand`
- Sample floats: `360`
- Decoded opcodes: `48`

| Artifact | Kind | Bytes | Ratio to `.sgm` |
|----------|------|-------|-----------------|
| `.sgm v1 bytecode` | `binary` | 1778 | 1.0x |
| `.gest JSON compact` | `json` | 4131 | 2.323x |
| `.gest JSON pretty` | `json` | 12330 | 6.935x |
| `.gest JSON gzip` | `gzip` | 879 | 0.494x |
| `.gest YAML` | `yaml` | 8211 | 4.618x |
| `Landmark JSON baseline` | `json` | 2401 | 1.35x |
| `CSV rows baseline` | `csv` | 2901 | 1.632x |
| `BVH-like text baseline` | `bvh-like` | 2030 | 1.142x |
