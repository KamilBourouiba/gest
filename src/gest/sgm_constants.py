"""
SGM v1 bytecode constants.

Keep in sync with `include/sgm_v1.h` for non-Python runtimes.
"""

from __future__ import annotations

from typing import Final

# Magic: 'S','G','M', version nibble in last byte for wire identification.
MAGIC: Final[bytes] = b"SGM\x01"

FORMAT_VERSION: Final[int] = 1

KIND_ARTICULATED: Final[int] = 1
KIND_DIRECTION: Final[int] = 2

OP_FRAME: Final[int] = 0x30
OP_JOINTS_F32: Final[int] = 0x31
OP_STATE: Final[int] = 0x32
OP_DIR_F32: Final[int] = 0x33
OP_END: Final[int] = 0xFF
