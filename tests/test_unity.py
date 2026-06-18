from __future__ import annotations

from pathlib import Path

from gest.sgm_decode import decode_sgm_bytes, decoded_to_pose_timeline

ROOT = Path(__file__).resolve().parents[1]
UNITY = ROOT / "unity" / "GestDemo"


def test_unity_package_scripts_exist():
    scripts = UNITY / "Scripts" / "Gest"
    expected = [
        "SgmConstants.cs",
        "SgmDecoder.cs",
        "GestClip.cs",
        "GestPlayer.cs",
        "GestRigVisualizer.cs",
        "GestMannequinVisualizer.cs",
        "GestRigPose.cs",
        "GestDemoEnvironment.cs",
        "GestDemoHud.cs",
        "GestDemoBootstrap.cs",
        "GestDemoClips.cs",
        "GestJsonLoader.cs",
        "GestSpace.cs",
    ]
    for name in expected:
        assert (scripts / name).is_file(), name


def test_unity_streaming_assets_match_python_decoder():
    sgm_path = UNITY / "StreamingAssets" / "xr_dual_hand_arc.sgm"
    assert sgm_path.is_file()
    decoded = decode_sgm_bytes(sgm_path.read_bytes())
    timeline = decoded_to_pose_timeline(decoded)
    assert len(decoded.channels) == 3
    assert len(timeline) == 9
    assert timeline[0]["pose"]["left_hand"]["joints"]["values"][0] < 0

    robot = UNITY / "StreamingAssets" / "robot_teleop_reach.sgm"
    assert robot.is_file()
    robot_decoded = decode_sgm_bytes(robot.read_bytes())
    assert len(robot_decoded.channels) == 2
    assert len(decoded_to_pose_timeline(robot_decoded)) == 14


def test_unity_readme_mentions_runtime_path():
    readme = (UNITY / "README.md").read_text(encoding="utf-8")
    assert "SgmBytecode" in readme
    assert "StreamingAssets" in readme
    assert "GestMannequinVisualizer" in readme
    assert "testgest" in readme
    assert "gest-olive.vercel.app" in readme
