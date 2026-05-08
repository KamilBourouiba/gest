from __future__ import annotations

import pytest

from demo.comparison_stats import build_comparison_stats
from demo.industry_benchmark import build_industry_benchmark
from demo.multi_demos import build_multi_demo_stats, demo_cases
from demo.research_artifact import build_research_artifact_manifest
from demo.run_demo import build_demo_document
from demo.render_avatar_video import avatar_project
from demo.render_video import _sample
from gest.sgm import compile_to_bytes
from gest.sgm_decode import decode_sgm_bytes
from gest.validate import validate_all

ROOT = __import__("pathlib").Path(__file__).resolve().parents[1]


def test_real_demo_document_validates_and_compiles():
    pytest.importorskip("jsonschema")
    doc = build_demo_document()
    errors = validate_all(doc)
    assert errors == [], errors

    blob = compile_to_bytes(doc)
    decoded = decode_sgm_bytes(blob)
    assert decoded.fps == pytest.approx(60)
    assert len(decoded.channels) == 3
    assert sum(1 for op in decoded.ops if op.kind == "frame") == 9


def test_video_renderer_samples_normalized_pose_shape():
    doc = build_demo_document()
    sampled = _sample(doc, 0.15)
    assert len(sampled["pose"]["left_hand"]["points"]) == 5
    assert len(sampled["pose"]["right_hand"]["points"]) == 5
    assert len(sampled["pose"]["gaze"]["dir"]) == 3


def test_avatar_projection_returns_screen_coordinates():
    x, y = avatar_project([0.0, 1.2, 0.2])
    assert isinstance(x, int)
    assert isinstance(y, int)
    assert 0 <= x <= 1280
    assert 0 <= y <= 720


def test_webgl_3d_avatar_viewer_exists():
    html = (ROOT / "demo" / "avatar_3d_viewer.html").read_text(encoding="utf-8")
    assert "getContext(\"webgl\"" in html
    assert "xr_dual_hand_arc.gest.json" in html
    assert "left_hand" in html and "right_hand" in html and "gaze" in html
    assert "FALLBACK_DOC" in html
    assert "playBtn.textContent" in html
    assert "comparison-stats.json" in html
    assert "multi-demo-stats.json" in html
    assert "industry-benchmark.json" in html
    assert "data/comparison-stats.json" in html
    assert "data/multi-demo-stats.json" in html
    assert "data/industry-benchmark.json" in html
    assert "https://github.com/KamilBourouiba/gest" in html
    assert "Industry proof" in html
    assert "gl_PointSize >" not in html
    assert "u_isPoint" in html


def test_2d_avatar_viewer_has_working_play_fallback():
    html = (ROOT / "demo" / "avatar_viewer.html").read_text(encoding="utf-8")
    assert "FALLBACK_DOC" in html
    assert "play.textContent" in html
    assert "setDoc(FALLBACK_DOC" in html


def test_vercel_landing_page_links_demo_github_and_stats():
    html = (ROOT / "index.html").read_text(encoding="utf-8")
    assert "/demo/avatar_3d_viewer" in html
    assert "https://github.com/KamilBourouiba/gest" in html
    assert "27/28" in html
    assert "1,562 B" in html


def test_hosted_industry_benchmark_page_exists():
    html = (ROOT / "docs" / "industry-benchmark.html").read_text(encoding="utf-8")
    assert ".gest Industry Benchmark" in html
    assert "27/28" in html
    assert "Back to WebGL demo" in html
    assert "Raw benchmark JSON" in html


def test_comparison_stats_are_measured_from_demo():
    stats = build_comparison_stats()
    assert stats["demo"]["frames"] == 9
    assert stats["demo"]["sample_floats_total"] == 297
    by_name = {item["name"]: item for item in stats["artifacts"]}
    assert by_name[".sgm v1 bytecode"]["bytes"] == 1562
    assert by_name[".gest JSON gzip"]["bytes"] < by_name[".sgm v1 bytecode"]["bytes"]
    assert by_name["CSV landmarks baseline"]["ratio_to_sgm"] > 1.0


def test_multi_demo_stats_cover_multiple_real_life_cases():
    stats = build_multi_demo_stats()
    assert len(stats["scenarios"]) == 4
    slugs = {scenario["slug"] for scenario in stats["scenarios"]}
    assert {
        "xr_dual_hand_arc",
        "robot_teleop_reach",
        "rehab_symmetry_loop",
        "dataset_pose7_microclip",
    } == slugs
    for scenario in stats["scenarios"]:
        by_name = {item["name"]: item for item in scenario["artifacts"]}
        assert by_name[".sgm v1 bytecode"]["bytes"] > 0
        assert by_name[".gest YAML"]["bytes"] > 0
        assert by_name["CSV rows baseline"]["bytes"] > 0


def test_multi_demo_documents_validate():
    pytest.importorskip("jsonschema")
    for case in demo_cases():
        errors = validate_all(case.doc)
        assert errors == [], (case.slug, errors)


def test_research_artifact_manifest_summarizes_reproducibility():
    manifest = build_research_artifact_manifest()
    assert manifest["artifact"] == ".gest research artifact"
    assert manifest["sgm"]["format_version"] == 1
    assert manifest["multi_demo"]["scenario_count"] == 4
    assert manifest["multi_demo"]["sample_floats_total"] == 1647
    assert manifest["industry_benchmark"]["generated_baseline_wins"] == 27
    assert manifest["multi_demo"]["compact_json_ratio_to_sgm"]["xr_dual_hand_arc"] > 1.0
    assert any(item["path"] == "docs/research-paper.md" for item in manifest["tracked_artifacts"])


def test_industry_benchmark_proves_specific_wins_and_limits():
    stats = build_industry_benchmark()
    assert len(stats["scenarios"]) == 4
    assert any("tiny pose7 microclip" in item for item in stats["proven_better_where"])
    pose7 = next(s for s in stats["scenarios"] if s["slug"] == "dataset_pose7_microclip")
    by_name = {item["name"]: item for item in pose7["artifacts"]}
    assert by_name["MediaPipe-like landmark JSON"]["ratio_to_sgm"] > 1.0
    assert by_name["OpenXR-like action trace JSON"]["ratio_to_sgm"] > 1.0
    assert by_name["glTF animation JSON shape"]["ratio_to_sgm"] > 1.0
    assert by_name["BVH-like skeleton text"]["ratio_to_sgm"] < 1.0

