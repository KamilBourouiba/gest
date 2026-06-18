#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
OUT="$ROOT/unity/GestDemo/StreamingAssets"
mkdir -p "$OUT"

python "$ROOT/demo/run_demo.py" >/dev/null
python "$ROOT/demo/multi_demos.py" >/dev/null

cp "$ROOT/demo/out/xr_pinch_grasp.sgm" "$OUT/xr_pinch_grasp.sgm"
cp "$ROOT/demo/out/xr_dual_hand_arc.sgm" "$OUT/xr_dual_hand_arc.sgm"
cp "$ROOT/demo/xr_pinch_grasp.gest.json" "$OUT/xr_pinch_grasp.gest.json"
cp "$ROOT/demo/xr_dual_hand_arc.gest.json" "$OUT/xr_dual_hand_arc.gest.json"
cp "$ROOT/demo/out/assembly_pick_place.sgm" "$OUT/assembly_pick_place.sgm"
cp "$ROOT/demo/generated/assembly_pick_place.gest.json" "$OUT/assembly_pick_place.gest.json"
cp "$ROOT/demo/out/presentation_sweep.sgm" "$OUT/presentation_sweep.sgm"
cp "$ROOT/demo/generated/presentation_sweep.gest.json" "$OUT/presentation_sweep.gest.json"
cp "$ROOT/demo/out/robot_teleop_reach.sgm" "$OUT/robot_teleop_reach.sgm"
cp "$ROOT/demo/generated/robot_teleop_reach.gest.json" "$OUT/robot_teleop_reach.gest.json"

echo "Wrote Unity StreamingAssets:"
ls -lh "$OUT"
