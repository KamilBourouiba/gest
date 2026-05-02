from __future__ import annotations

import struct
from dataclasses import dataclass, field
from typing import Any, Final, Literal

from gest.sgm_constants import (
    FORMAT_VERSION,
    KIND_ARTICULATED,
    KIND_DIRECTION,
    MAGIC,
    OP_DIR_F32,
    OP_END,
    OP_FRAME,
    OP_JOINTS_F32,
    OP_STATE,
)

OpKind = Literal[
    "frame",
    "joints_f32",
    "state_index",
    "direction_f32",
]


@dataclass
class SgmDecodedOp:
    kind: OpKind
    t: float | None = None
    channel_id: int | None = None
    values: list[float] = field(default_factory=list)
    state_index: int | None = None


@dataclass
class SgmDecodedChannel:
    name: str
    kind: Literal["articulated", "direction"]
    joint_count: int | None = None
    state_count: int | None = None


@dataclass
class SgmDecoded:
    format_version: int
    fps: float
    channels: list[SgmDecodedChannel]
    ops: list[SgmDecodedOp]


class GestDecodeError(ValueError):
    """Error decoding .sgm bytecode."""


def _need(data: bytes, pos: int, n: int) -> None:
    if pos + n > len(data):
        raise GestDecodeError(f"Unexpected EOF at offset {pos} (need {n} bytes).")


def decode_sgm_bytes(data: bytes) -> SgmDecoded:
    """
    Parse .sgm v1 bytecode produced by `compile_to_bytes`.

    Returns a structural summary (channel table + flat opcode stream with frame markers).
    """
    pos = 0
    _need(data, pos, 4)
    if data[pos : pos + 4] != MAGIC:
        raise GestDecodeError(f"Bad magic: expected {MAGIC!r}, got {data[:4]!r}.")
    pos += 4

    _need(data, pos, 2 + 4 + 2)
    (fmt_ver,) = struct.unpack_from("<H", data, pos)
    pos += 2
    if fmt_ver != FORMAT_VERSION:
        raise GestDecodeError(f"Unsupported format_version {fmt_ver} (expected {FORMAT_VERSION}).")
    (fps,) = struct.unpack_from("<f", data, pos)
    pos += 4
    (n_ch,) = struct.unpack_from("<H", data, pos)
    pos += 2

    channels: list[SgmDecodedChannel] = []
    for _ in range(n_ch):
        _need(data, pos, 2)
        (kind, nlen) = struct.unpack_from("<BB", data, pos)
        pos += 2
        _need(data, pos, nlen)
        name = data[pos : pos + nlen].decode("utf-8")
        pos += nlen
        if kind == KIND_ARTICULATED:
            _need(data, pos, 4)
            (jc, sc) = struct.unpack_from("<HH", data, pos)
            pos += 4
            channels.append(
                SgmDecodedChannel(
                    name=name,
                    kind="articulated",
                    joint_count=jc,
                    state_count=sc,
                )
            )
        elif kind == KIND_DIRECTION:
            channels.append(SgmDecodedChannel(name=name, kind="direction"))
        else:
            raise GestDecodeError(f"Unknown channel kind byte {kind} for channel {name!r}.")

    ops: list[SgmDecodedOp] = []
    while pos < len(data):
        _need(data, pos, 1)
        (op,) = struct.unpack_from("<B", data, pos)
        pos += 1
        if op == OP_END:
            if pos != len(data):
                raise GestDecodeError(f"Trailing data after OP_END at offset {pos}.")
            break
        if op == OP_FRAME:
            _need(data, pos, 8)
            (t,) = struct.unpack_from("<d", data, pos)
            pos += 8
            ops.append(SgmDecodedOp(kind="frame", t=float(t)))
        elif op == OP_JOINTS_F32:
            _need(data, pos, 6)
            (cid, n_floats) = struct.unpack_from("<HI", data, pos)
            pos += 6
            _need(data, pos, 4 * n_floats)
            fmt = f"<{n_floats}f"
            vals = list(struct.unpack_from(fmt, data, pos))
            pos += 4 * n_floats
            ops.append(
                SgmDecodedOp(
                    kind="joints_f32",
                    channel_id=cid,
                    values=vals,
                )
            )
        elif op == OP_STATE:
            _need(data, pos, 4)
            (cid, si) = struct.unpack_from("<HH", data, pos)
            pos += 4
            ops.append(
                SgmDecodedOp(
                    kind="state_index",
                    channel_id=cid,
                    state_index=si,
                )
            )
        elif op == OP_DIR_F32:
            _need(data, pos, 2 + 12)
            (cid,) = struct.unpack_from("<H", data, pos)
            pos += 2
            (x, y, z) = struct.unpack_from("<fff", data, pos)
            pos += 12
            ops.append(
                SgmDecodedOp(
                    kind="direction_f32",
                    channel_id=cid,
                    values=[x, y, z],
                )
            )
        else:
            raise GestDecodeError(f"Unknown opcode 0x{op:02x} at offset {pos - 1}.")

    return SgmDecoded(format_version=fmt_ver, fps=float(fps), channels=channels, ops=ops)


def decoded_to_pose_timeline(decoded: SgmDecoded) -> list[dict[str, Any]]:
    """
    Rebuild a minimal timeline: list of { "t", "pose": { channel_name: {...} } } from decoded ops.

    Channel order in the table matches sorted names at compile time; ids index that list.
    """
    id_to_name = {i: ch.name for i, ch in enumerate(decoded.channels)}
    timeline: list[dict[str, Any]] = []
    current_t: float | None = None
    current_pose: dict[str, Any] = {}

    def flush_frame() -> None:
        nonlocal current_t, current_pose
        if current_t is not None:
            timeline.append({"t": current_t, "pose": dict(current_pose)})
        current_pose = {}

    for op in decoded.ops:
        if op.kind == "frame":
            flush_frame()
            current_t = op.t if op.t is not None else 0.0
        elif op.channel_id is None:
            continue
        else:
            name = id_to_name.get(op.channel_id)
            if name is None:
                raise GestDecodeError(f"Unknown channel_id {op.channel_id}")
            if op.kind == "joints_f32":
                entry = current_pose.setdefault(name, {})
                entry["joints"] = {"format": "raw_float32", "values": list(op.values)}
            elif op.kind == "state_index":
                entry = current_pose.setdefault(name, {})
                entry["state_index"] = op.state_index
            elif op.kind == "direction_f32":
                current_pose[name] = {"dir": list(op.values)}

    flush_frame()
    return timeline
