"""Ensure include/sgm_v1.h stays aligned with src/gest/sgm_constants.py."""

from __future__ import annotations

import re
from pathlib import Path

import gest.sgm_constants as py

ROOT = Path(__file__).resolve().parents[1]
HEADER = ROOT / "include" / "sgm_v1.h"


def _parse_u_define(name: str, text: str) -> int:
    m = re.search(
        rf"#define\s+{re.escape(name)}\s+((?:0[xX])[0-9A-Fa-f]+|[0-9]+)u",
        text,
    )
    assert m, f"missing #define {name}"
    s = m.group(1)
    if s.lower().startswith("0x"):
        return int(s, 16)
    return int(s, 10)


def test_header_matches_python_constants():
    text = HEADER.read_text(encoding="utf-8")
    assert bytes(
        [
            _parse_u_define("SGM_V1_MAGIC0", text),
            _parse_u_define("SGM_V1_MAGIC1", text),
            _parse_u_define("SGM_V1_MAGIC2", text),
            _parse_u_define("SGM_V1_MAGIC3", text),
        ]
    ) == py.MAGIC
    assert _parse_u_define("SGM_V1_FORMAT_VERSION", text) == py.FORMAT_VERSION
    assert _parse_u_define("SGM_V1_KIND_ARTICULATED", text) == py.KIND_ARTICULATED
    assert _parse_u_define("SGM_V1_KIND_DIRECTION", text) == py.KIND_DIRECTION
    assert _parse_u_define("SGM_V1_OP_FRAME", text) == py.OP_FRAME
    assert _parse_u_define("SGM_V1_OP_JOINTS_F32", text) == py.OP_JOINTS_F32
    assert _parse_u_define("SGM_V1_OP_STATE", text) == py.OP_STATE
    assert _parse_u_define("SGM_V1_OP_DIR_F32", text) == py.OP_DIR_F32
    assert _parse_u_define("SGM_V1_OP_END", text) == py.OP_END
