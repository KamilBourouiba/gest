#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
OUT="$ROOT/unity/GestDemo/StreamingAssets"
mkdir -p "$OUT"

python "$ROOT/demo/run_demo.py" >/dev/null
python "$ROOT/demo/multi_demos.py" >/dev/null

cp "$ROOT/demo/out/xr_dual_hand_arc.sgm" "$OUT/xr_dual_hand_arc.sgm"
cp "$ROOT/demo/xr_dual_hand_arc.gest.json" "$OUT/xr_dual_hand_arc.gest.json"
cp "$ROOT/demo/out/robot_teleop_reach.sgm" "$OUT/robot_teleop_reach.sgm"
cp "$ROOT/demo/generated/robot_teleop_reach.gest.json" "$OUT/robot_teleop_reach.gest.json"

echo "Wrote Unity StreamingAssets:"
ls -lh "$OUT"
