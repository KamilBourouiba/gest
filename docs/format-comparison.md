# `.gest` compared with existing motion formats

`.gest` is not trying to replace every animation or tracking format. It fills a narrower gap: a **non-semantic gesture IR** that is structured enough to validate, compact enough to compile, and low-level enough for runtime execution.

For measured byte-size data from the concrete demo clip, see [`comparison-stats.md`](comparison-stats.md). For a broader industry-facing benchmark against BVH-like text, glTF animation JSON-like shape, OpenXR trace-like JSON, MediaPipe landmark-like JSON, ROS-like JSONL, and CSV rows, see [`industry-benchmark.md`](industry-benchmark.md). Those numbers are generated from the same motion samples used in the demos.

## BVH

**Best at:** simple skeletal motion interchange, especially older mocap pipelines.

**Where it differs from `.gest`:**

- BVH is centered on a skeleton hierarchy and sampled channel curves.
- It is weak for rich hand state, face/gaze side channels, streaming metadata, and validation invariants.
- It does not define a bytecode path for small runtime processors.

**When to use together:** import BVH body motion into `.gest` as torso / arm channels, then add hand, gaze, and runtime-oriented metadata.

## FBX

**Best at:** full DCC interchange across Autodesk / game pipelines.

**Where it differs from `.gest`:**

- FBX carries rich scene, mesh, materials, rigging, and animation data.
- It is heavy and ecosystem-dependent.
- It is not designed as a minimal, auditable motion IR or firmware/runtime bytecode source.

**When to use together:** author in FBX-friendly tools, then export only the executable motion subset to `.gest` for validation and `.sgm` compilation.

## glTF / VRM

**Best at:** portable 3D assets, avatars, animations, and web-friendly runtime loading.

**Where it differs from `.gest`:**

- glTF/VRM are asset/container formats; `.gest` is a gesture/motion IR.
- glTF can store animation clips, but its core concern is scene delivery, not strict non-semantic gesture channels.
- `.gest` can be used upstream of a glTF/VRM avatar runtime: the avatar is the body; `.gest` is the motion feed.

**When to use together:** use VRM/glTF for the avatar, `.gest`/`.sgm` for generated or captured gesture motion.

## OpenXR hand tracking

**Best at:** live device APIs for XR hand poses.

**Where it differs from `.gest`:**

- OpenXR is an API surface, not a durable dataset or interchange file.
- `.gest` can record, validate, replay, and compile the motion that came from OpenXR.

**When to use together:** capture OpenXR frames into `.gest`, use `.sgm` for deterministic replay, QA, or network packaging.

## MediaPipe landmarks

**Best at:** extracting 2D/3D landmarks from camera input.

**Where it differs from `.gest`:**

- MediaPipe gives landmark arrays and model outputs.
- `.gest` wraps such arrays in a formal IR: coordinate conventions, channels, timeline, validation, and optional compilation.

**When to use together:** treat MediaPipe as an encoder that emits `.gest` hand, face, or body channels.

## ROS bags / robotics logs

**Best at:** timestamped multi-topic robotics data capture.

**Where it differs from `.gest`:**

- ROS bags are broad logging containers.
- `.gest` is a narrow, normalized motion artifact that can be inspected, validated, compiled, and replayed without the full ROS environment.

**When to use together:** archive raw ROS bags, extract normalized gesture/control trajectories into `.gest` for review or runtime packaging.

## Summary

Use `.gest` when you need:

- low-level motion without embedded semantics;
- JSON/YAML authoring plus machine validation;
- strict IR invariants beyond JSON Schema;
- a documented compile path to `.sgm` bytecode;
- reversible-enough debug tooling from runtime artifact back to human-readable JSON.

Use existing formats alongside `.gest`, not necessarily instead of them: BVH/FBX/glTF/VRM can stay in authoring and asset pipelines, OpenXR/MediaPipe can stay in capture pipelines, and ROS bags can stay in robotics logging. `.gest` becomes the normalized motion layer between those systems and execution.

The measured industry benchmark currently shows `.sgm` smaller than compact `.gest` JSON, MediaPipe-like JSON, OpenXR-like JSON traces, glTF-like animation JSON, ROS-like JSONL, and CSV rows in all generated scenarios. The important caveat is that a tiny pose7 microclip produces a BVH-like text baseline that is slightly smaller than `.sgm`; the win for `.gest` there is validation, semantic separation, and compilation, not raw bytes.

