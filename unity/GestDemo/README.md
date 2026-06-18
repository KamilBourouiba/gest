# Unity demo: `.gest` / SGM in a game engine

This folder is a drop-in Unity project slice that shows why `.gest` is useful in a real runtime:

1. Load **compact SGM v1 bytecode** from `StreamingAssets` (runtime path).
2. Decode it with a **native C# decoder** aligned with `include/sgm_v1.h`.
3. Play the clip on a **procedural mannequin** (capsules + spheres) with **hands + gaze**.
4. Overlay **measured stats** (artifact size, decode time, compact JSON ratio).

No semantic labels. Only motion channels, time, and machine states — the same non-semantic contract as the Python/WebGL demos.

## Quick start

### 1. Prepare assets

From the repository root:

```bash
python demo/run_demo.py
./unity/prepare_assets.sh
```

This copies:

| File | Purpose |
|------|---------|
| `StreamingAssets/xr_dual_hand_arc.sgm` | Runtime bytecode (primary path) |
| `StreamingAssets/xr_dual_hand_arc.gest.json` | Optional JSON path for comparison |

### 2. Create or open a Unity project

- Unity **2021.3 LTS** or newer (any render pipeline).
- Copy `unity/GestDemo/Scripts` into `Assets/Scripts/Gest` (or open this repo and symlink).

### 3. Scene setup

**Automatic (recommended):** press **Play** in any scene — `GestDemoBootstrap` spawns `GestDemo` with the mannequin.

**Manual / persistent scene:**

1. Menu **Gest → Setup Demo Scene** (adds ground + camera framing).
2. Or create an empty GameObject named `GestDemo` and add:
   - `GestPlayer`
   - `GestMannequinVisualizer` (solid mannequin) or `GestRigVisualizer` (wireframe)
   - `GestDemoHud`
3. Press **Play**.

The player loads `xr_dual_hand_arc.sgm` by default, decodes it once, then samples the timeline every frame.

### 4. Switch source

On `GestPlayer`:

| Field | Value |
|-------|-------|
| `source` | `SgmBytecode` (default) or `GestJson` |
| `sgmAsset` | `xr_dual_hand_arc` (without extension) |
| `gestJsonAsset` | `xr_dual_hand_arc.gest` |

Compare both modes in the HUD: SGM is smaller and skips JSON parsing. Press **N** to switch between XR and robot-teleop benchmark clips.

## What this demonstrates

| Capability | Shown here |
|------------|------------|
| **Bytecode runtime** | SGM decoded directly in Unity without Python |
| **Cross-language constants** | `SgmConstants.cs` mirrors `include/sgm_v1.h` |
| **Non-semantic motion** | Hands + gaze only; no glosses or NL labels |
| **Measured efficiency** | HUD shows byte sizes and decode microseconds |
| **Engine integration** | Positions drive transforms / line renderers in 3D |

## Coordinate space

`.gest` clips use right-handed **Y-up**, **+Z forward** (meters). Unity is left-handed Y-up. `GestSpace.ToUnity()` applies a simple conversion (`z -> -z`) used by the WebGL demo family.

Adjust in `GestSpace.cs` if your avatar root uses a different convention.

## Scripts

| Script | Role |
|--------|------|
| `SgmConstants.cs` | Wire opcodes / magic (must match `sgm_v1.h`) |
| `SgmDecoder.cs` | Parse `.sgm` bytes into a pose timeline |
| `GestClip.cs` | In-memory clip + sampling |
| `GestJsonLoader.cs` | Optional JSON load via `JsonUtility` |
| `GestPlayer.cs` | Load, decode, play loop |
| `GestMannequinVisualizer.cs` | Procedural 3D mannequin (default demo) |
| `GestRigVisualizer.cs` | Wireframe rig lines + joint markers |
| `GestRigPose.cs` | Shared skeleton landmarks from .gest channels |
| `GestDemoEnvironment.cs` | Ground plane + camera framing |
| `GestDemoBootstrap.cs` | Auto-spawn demo on Play |
| `GestDemoHud.cs` | On-screen stats panel |
| `GestSpace.cs` | .gest → Unity coordinates |

## Next steps

- Stream SGM chunks for live XR input.
- Retarget channels to Unity Humanoid / XR Hands.
- Compile clips at build time with `gest-compile` and ship only `.sgm`.
- Add a second scenario (`robot_teleop_reach.sgm`) from `demo/out/`. **Done** — press **N** in the Unity HUD.

## Links

- Hosted WebGL demo: https://gest-olive.vercel.app/demo/avatar_3d_viewer
- Public Unity project: https://github.com/KamilBourouiba/testgest
- Repository: https://github.com/KamilBourouiba/gest
- Industry benchmark: https://gest-olive.vercel.app/docs/industry-benchmark
