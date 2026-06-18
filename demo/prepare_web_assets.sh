#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
CLIPS="$ROOT/demo/data/clips"
mkdir -p "$CLIPS"

python "$ROOT/demo/run_demo.py" >/dev/null
python "$ROOT/demo/multi_demos.py" >/dev/null

cd "$ROOT"
PYTHONPATH="$ROOT:$ROOT/src" python - <<'PY'
from pathlib import Path
from demo.multi_demos import demo_cases

clips = Path("demo/data/clips")
for case in demo_cases():
    sgm = Path("demo/out") / f"{case.slug}.sgm"
    gest = Path("demo/generated") / f"{case.slug}.gest.json"
    if sgm.is_file():
        (clips / sgm.name).write_bytes(sgm.read_bytes())
    if gest.is_file():
        (clips / gest.name).write_text(gest.read_text(encoding="utf-8"), encoding="utf-8")

# Legacy aliases for older viewer paths
src_sgm = clips / "xr_pinch_grasp.sgm"
src_gest = clips / "xr_pinch_grasp.gest.json"
if src_sgm.is_file():
    (clips / "xr_dual_hand_arc.sgm").write_bytes(src_sgm.read_bytes())
if src_gest.is_file():
    (clips / "xr_dual_hand_arc.gest.json").write_text(src_gest.read_text(encoding="utf-8"), encoding="utf-8")

print("Web clips:")
for p in sorted(clips.iterdir()):
    print(f"  {p.name} ({p.stat().st_size} B)")
PY

bash "$ROOT/unity/prepare_assets.sh"
