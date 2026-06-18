# Multi-demo comparison stats

Measured from generated `.gest` scenarios in `demo/generated/`.

## Methodology

- Each scenario is generated as a valid .gest document.
- All byte counts are measured from local artifacts produced from the same numeric samples.
- CSV, landmark JSON, and BVH-like baselines are concrete transforms, not official exporters.
- Ratios are relative to .sgm v1 bytecode for that same scenario.

## XR pinch & grasp

Both hands converge on a workspace object, pinch, lift, and release — readable XR manipulation without semantic labels.

- Frames: `32`
- Duration: `2.4s`
- Channels: `gaze, left_hand, right_hand`
- Sample floats: `1056`
- Decoded opcodes: `192`

| Artifact | Kind | Bytes | Ratio to `.sgm` |
|----------|------|-------|-----------------|
| `.sgm v1 bytecode` | `binary` | 5426 | 1.0x |
| `.gest JSON compact` | `json` | 13529 | 2.493x |
| `.gest JSON pretty` | `json` | 38656 | 7.124x |
| `.gest JSON gzip` | `gzip` | 2513 | 0.463x |
| `.gest YAML` | `yaml` | 25471 | 4.694x |
| `Landmark JSON baseline` | `json` | 9102 | 1.677x |
| `CSV rows baseline` | `csv` | 15094 | 2.782x |
| `BVH-like text baseline` | `bvh-like` | 7900 | 1.456x |

## Assembly pick & place

A single manipulator cycle: approach, grasp, lift, translate, and release over a bin.

- Frames: `40`
- Duration: `2.2s`
- Channels: `gaze, right_hand`
- Sample floats: `720`
- Decoded opcodes: `160`

| Artifact | Kind | Bytes | Ratio to `.sgm` |
|----------|------|-------|-----------------|
| `.sgm v1 bytecode` | `binary` | 3875 | 1.0x |
| `.gest JSON compact` | `json` | 9667 | 2.495x |
| `.gest JSON pretty` | `json` | 27691 | 7.146x |
| `.gest JSON gzip` | `gzip` | 1963 | 0.507x |
| `.gest YAML` | `yaml` | 17648 | 4.554x |
| `Landmark JSON baseline` | `json` | 6811 | 1.758x |
| `CSV rows baseline` | `csv` | 10297 | 2.657x |
| `BVH-like text baseline` | `bvh-like` | 5211 | 1.345x |

## Presentation sweep

A presenter sweeps one hand across a virtual panel while gaze tracks the gesture.

- Frames: `36`
- Duration: `2.0s`
- Channels: `gaze, right_hand`
- Sample floats: `648`
- Decoded opcodes: `144`

| Artifact | Kind | Bytes | Ratio to `.sgm` |
|----------|------|-------|-----------------|
| `.sgm v1 bytecode` | `binary` | 3491 | 1.0x |
| `.gest JSON compact` | `json` | 8804 | 2.522x |
| `.gest JSON pretty` | `json` | 25092 | 7.188x |
| `.gest JSON gzip` | `gzip` | 2092 | 0.599x |
| `.gest YAML` | `yaml` | 16005 | 4.585x |
| `Landmark JSON baseline` | `json` | 6157 | 1.764x |
| `CSV rows baseline` | `csv` | 9265 | 2.654x |
| `BVH-like text baseline` | `bvh-like` | 4811 | 1.378x |

## Rehabilitation symmetry loop

Bilateral hand symmetry practice with larger amplitude and visible open/close phases.

- Frames: `28`
- Duration: `2.6s`
- Channels: `gaze, left_hand, right_hand`
- Sample floats: `1092`
- Decoded opcodes: `168`

| Artifact | Kind | Bytes | Ratio to `.sgm` |
|----------|------|-------|-----------------|
| `.sgm v1 bytecode` | `binary` | 5426 | 1.0x |
| `.gest JSON compact` | `json` | 12738 | 2.348x |
| `.gest JSON pretty` | `json` | 37079 | 6.834x |
| `.gest JSON gzip` | `gzip` | 1368 | 0.252x |
| `.gest YAML` | `yaml` | 24810 | 4.572x |
| `Landmark JSON baseline` | `json` | 9133 | 1.683x |
| `CSV rows baseline` | `csv` | 15677 | 2.889x |
| `BVH-like text baseline` | `bvh-like` | 8432 | 1.554x |

## Robot teleoperation reach

A remote operator guides a gripper-like end effector toward a target while gaze stays locked on the workspace.

- Frames: `24`
- Duration: `1.8s`
- Channels: `gaze, right_hand`
- Sample floats: `432`
- Decoded opcodes: `96`

| Artifact | Kind | Bytes | Ratio to `.sgm` |
|----------|------|-------|-----------------|
| `.sgm v1 bytecode` | `binary` | 2339 | 1.0x |
| `.gest JSON compact` | `json` | 6091 | 2.604x |
| `.gest JSON pretty` | `json` | 17141 | 7.328x |
| `.gest JSON gzip` | `gzip` | 1392 | 0.595x |
| `.gest YAML` | `yaml` | 10958 | 4.685x |
| `Landmark JSON baseline` | `json` | 4179 | 1.787x |
| `CSV rows baseline` | `csv` | 6273 | 2.682x |
| `BVH-like text baseline` | `bvh-like` | 3571 | 1.527x |

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
