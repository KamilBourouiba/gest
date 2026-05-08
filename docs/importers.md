# Import adapters

These adapters are proof-oriented bridges from common capture/animation shapes into `.gest`.

They are intentionally conservative: they preserve motion samples and timing, create explicit `.gest` channels, and leave natural-language meaning outside the artifact.

## CLI

```bash
gest-import mediapipe examples/imports/mediapipe_sample.json /tmp/mediapipe.gest.json
gest-import openxr examples/imports/openxr_sample.json /tmp/openxr.gest.json
gest-import bvh examples/imports/simple_sample.bvh /tmp/bvh.gest.json
```

Then validate / compile:

```bash
gest-validate /tmp/mediapipe.gest.json
gest-compile /tmp/mediapipe.gest.json /tmp/mediapipe.sgm
```

## MediaPipe-like JSON

Expected input:

- root `fps`
- `frames[]`
- each frame may contain `hands.left`, `hands.right`, and `gaze`
- landmarks can be objects `{x,y,z}` or lists `[x,y,z]`

Output:

- `left_hand` / `right_hand` articulated channels
- `joint_layout: mediapipe_hands_landmarks_v1`
- optional `gaze` direction channel

## OpenXR-like JSON

Expected input:

- root `fps`
- `frames[]`
- each frame may contain `hands.left` / `hands.right`
- each hand is a list of joints with `position: [x,y,z]`

Output:

- articulated hand channels
- `joint_layout: openxr_hand_joint_set_v1`

## BVH / BVH-like text

Expected input:

- `HIERARCHY`
- `MOTION`
- `Frames: N`
- `Frame Time: T`
- one numeric row per frame

Output:

- one `bvh_points` articulated channel
- numeric MOTION rows chunked into XYZ triples

The BVH importer does **not** interpret rotations or DCC rig semantics yet; it is a bridge for sampled channel rows into a validated `.gest` shape.

