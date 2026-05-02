from pathlib import Path

import pytest

from gest.document import load_json_path
from gest.sgm import compile_to_bytes
from gest.sgm_decode import GestDecodeError, decode_sgm_bytes, decoded_to_pose_timeline

ROOT = Path(__file__).resolve().parents[1]
EXAMPLE = ROOT / "examples" / "minimal.gest.json"


def test_roundtrip_minimal_timeline():
    doc = load_json_path(EXAMPLE)
    blob = compile_to_bytes(doc)
    dec = decode_sgm_bytes(blob)
    assert dec.fps == doc["fps"]
    assert [c.name for c in dec.channels] == sorted(doc["channels"].keys())
    tl = decoded_to_pose_timeline(dec)
    assert len(tl) == len(doc["timeline"])
    for got, orig in zip(tl, doc["timeline"]):
        assert got["t"] == pytest.approx(orig["t"])
        assert set(got["pose"].keys()) == set(orig["pose"].keys())
        for ch in got["pose"]:
            og = orig["pose"][ch]
            g = got["pose"][ch]
            if "dir" in og:
                assert g["dir"] == pytest.approx(list(og["dir"]))
            if "joints" in og and "values" in og["joints"]:
                assert g["joints"]["values"] == pytest.approx(list(og["joints"]["values"]))
            if "state_index" in og:
                assert g["state_index"] == og["state_index"]


def test_decode_bad_magic():
    with pytest.raises(GestDecodeError):
        decode_sgm_bytes(b"XXXX" + b"\x00" * 20)
