from __future__ import annotations

import hashlib
import json
import platform
import sys
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
for path in (ROOT, SRC):
    s = str(path)
    if s not in sys.path:
        sys.path.insert(0, s)

from demo.comparison_stats import build_comparison_stats  # noqa: E402
from demo.industry_benchmark import build_industry_benchmark  # noqa: E402
from demo.multi_demos import build_multi_demo_stats  # noqa: E402
from gest.sgm_constants import FORMAT_VERSION, MAGIC  # noqa: E402


OUT_JSON = ROOT / "demo" / "out" / "research-artifact-manifest.json"
OUT_MD = ROOT / "docs" / "research-artifact-manifest.md"

TRACKED_ARTIFACTS = (
    "schema/gest-0.2.schema.json",
    "spec/gest-spec.md",
    "include/sgm_v1.h",
    "src/gest/sgm_constants.py",
    "demo/xr_dual_hand_arc.gest.json",
    "demo/out/xr_dual_hand_arc.sgm",
    "demo/out/comparison-stats.json",
    "demo/out/multi-demo-stats.json",
    "demo/out/industry-benchmark.json",
    "docs/research-paper.md",
    "docs/industry-benchmark.md",
)


def _sha256(path: Path) -> str | None:
    if not path.exists() or not path.is_file():
        return None
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


def _artifact_entry(rel_path: str) -> dict[str, Any]:
    path = ROOT / rel_path
    digest = _sha256(path)
    return {
        "path": rel_path,
        "exists": digest is not None,
        "bytes": path.stat().st_size if digest is not None else None,
        "sha256": digest,
    }


def _sgm_vs_json_ratios(multi: dict[str, Any]) -> dict[str, float]:
    ratios: dict[str, float] = {}
    for scenario in multi["scenarios"]:
        compact = next(item for item in scenario["artifacts"] if item["name"] == ".gest JSON compact")
        ratios[scenario["slug"]] = compact["ratio_to_sgm"]
    return ratios


def build_research_artifact_manifest() -> dict[str, Any]:
    comparison = build_comparison_stats()
    multi = build_multi_demo_stats()
    industry = build_industry_benchmark()
    ratios = _sgm_vs_json_ratios(multi)
    industry_wins = sum(len(scenario["sgm_smaller_than"]) for scenario in industry["scenarios"])
    return {
        "artifact": ".gest research artifact",
        "status": "draft",
        "python": platform.python_version(),
        "sgm": {
            "format_version": FORMAT_VERSION,
            "magic_hex": MAGIC.hex(),
        },
        "test_command": "PYTHONPATH=src:. pytest -q",
        "claims": [
            "Motion representation is intentionally non-semantic.",
            "The reference pipeline validates .gest before compiling .sgm.",
            "SGM v1 is smaller than compact .gest JSON in every generated scenario.",
            "All byte-size comparisons are generated from local transforms of the same samples.",
            "Industry-facing comparisons distinguish byte-size wins from cases where existing standards remain better tools.",
        ],
        "single_demo": {
            "frames": comparison["demo"]["frames"],
            "sample_floats_total": comparison["demo"]["sample_floats_total"],
            "decoded_opcode_count": comparison["demo"]["decoded_opcode_count"],
        },
        "multi_demo": {
            "scenario_count": len(multi["scenarios"]),
            "sample_floats_total": sum(s["sample_floats_total"] for s in multi["scenarios"]),
            "decoded_opcode_count": sum(s["decoded_opcode_count"] for s in multi["scenarios"]),
            "compact_json_ratio_to_sgm": ratios,
        },
        "industry_benchmark": {
            "scenario_count": len(industry["scenarios"]),
            "generated_baseline_wins": industry_wins,
            "not_better_where": industry["not_better_where"],
        },
        "tracked_artifacts": [_artifact_entry(path) for path in TRACKED_ARTIFACTS],
    }


def write_research_artifact_manifest() -> dict[str, Any]:
    OUT_JSON.parent.mkdir(parents=True, exist_ok=True)
    OUT_MD.parent.mkdir(parents=True, exist_ok=True)
    manifest = build_research_artifact_manifest()
    OUT_JSON.write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    lines = [
        "# Research artifact manifest",
        "",
        "This manifest records the reproducible surface for the `.gest` draft artifact.",
        "",
        "## Claims",
        "",
    ]
    lines.extend(f"- {claim}" for claim in manifest["claims"])
    lines.extend(
        [
            "",
            "## Reproducibility",
            "",
            f"- Python: `{manifest['python']}`",
            f"- SGM format version: `{manifest['sgm']['format_version']}`",
            f"- SGM magic: `{manifest['sgm']['magic_hex']}`",
            f"- Test command: `{manifest['test_command']}`",
            "",
            "## Aggregate evidence",
            "",
            f"- Scenarios: `{manifest['multi_demo']['scenario_count']}`",
            f"- Sample floats: `{manifest['multi_demo']['sample_floats_total']}`",
            f"- Decoded opcodes: `{manifest['multi_demo']['decoded_opcode_count']}`",
            f"- Industry baseline wins: `{manifest['industry_benchmark']['generated_baseline_wins']}`",
            "",
            "## Tracked artifacts",
            "",
        ]
    )
    for item in manifest["tracked_artifacts"]:
        status = "present" if item["exists"] else "missing"
        size = item["bytes"] if item["bytes"] is not None else "n/a"
        digest = item["sha256"] if item["sha256"] is not None else "n/a"
        lines.append(f"- `{item['path']}`: {status}, `{size}` bytes, sha256 `{digest}`")
    OUT_MD.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return manifest


def main() -> int:
    manifest = write_research_artifact_manifest()
    print(f"Wrote {OUT_JSON.relative_to(ROOT)}")
    print(f"Wrote {OUT_MD.relative_to(ROOT)}")
    print(f"Tracked {len(manifest['tracked_artifacts'])} artifacts")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
