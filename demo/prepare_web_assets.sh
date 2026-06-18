#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
CLIPS="$ROOT/demo/data/clips"
mkdir -p "$CLIPS"

python "$ROOT/demo/run_demo.py" >/dev/null
python "$ROOT/demo/multi_demos.py" >/dev/null

for slug in xr_dual_hand_arc robot_teleop_reach rehab_symmetry_loop dataset_pose7_microclip; do
  cp "$ROOT/demo/out/${slug}.sgm" "$CLIPS/${slug}.sgm"
  if [[ -f "$ROOT/demo/generated/${slug}.gest.json" ]]; then
    cp "$ROOT/demo/generated/${slug}.gest.json" "$CLIPS/${slug}.gest.json"
  fi
done

cp "$ROOT/demo/xr_dual_hand_arc.gest.json" "$CLIPS/xr_dual_hand_arc.gest.json"

echo "Web clips for breakthrough lab:"
ls -lh "$CLIPS"
