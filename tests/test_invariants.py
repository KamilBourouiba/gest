import pytest

from gest.invariants import validate_invariants


def test_stride_mismatch():
    doc = {
        "channels": {
            "h": {
                "type": "articulated",
                "parent": "chest",
                "joint_count": 2,
                "joint_layout": "x",
                "joint_value_stride": 3,
            }
        },
        "timeline": [
            {
                "t": 0,
                "pose": {
                    "h": {
                        "joints": {"values": [0, 0, 0]},
                    }
                },
            }
        ],
    }
    err = validate_invariants(doc)
    assert any("length 3" in e and "2*3=6" in e for e in err)


def test_state_index_out_of_range():
    doc = {
        "channels": {
            "h": {
                "type": "articulated",
                "parent": "chest",
                "joint_count": 1,
                "joint_layout": "x",
                "state_enum": ["a", "b"],
            }
        },
        "timeline": [
            {
                "t": 0,
                "pose": {
                    "h": {
                        "joints": {"values": [0, 0, 0]},
                        "state_index": 2,
                    }
                },
            }
        ],
    }
    err = validate_invariants(doc)
    assert any("out of range" in e for e in err)


def test_direction_dir_length():
    doc = {
        "channels": {
            "g": {"type": "direction", "parent": "chest", "representation": "unit_vector"}
        },
        "timeline": [{"t": 0, "pose": {"g": {"dir": [1, 2]}}}],
    }
    err = validate_invariants(doc)
    assert any("dir" in e for e in err)
