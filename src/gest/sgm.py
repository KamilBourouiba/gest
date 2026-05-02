from __future__ import annotations

import struct
from io import BytesIO
from typing import Any

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


class GestCompileError(ValueError):
    """Error compiling .gest to .sgm."""


def _pack_utf8(s: str, max_len: int = 255) -> bytes:
    b = s.encode("utf-8")
    if len(b) > max_len:
        raise GestCompileError(f"Channel name too long (> {max_len} UTF-8 bytes).")
    return b


def compile_to_bytes(doc: dict[str, Any]) -> bytes:
    """
    Emit .sgm v1 bytecode (little-endian).

    Layout: magic + version + fps + channel table (sorted names),
    then per frame: time marker + ops per channel (same sorted order).
    """
    fps = doc.get("fps")
    if not isinstance(fps, (int, float)) or fps <= 0:
        raise GestCompileError("fps must be a number > 0.")

    channels = doc.get("channels")
    if not isinstance(channels, dict) or not channels:
        raise GestCompileError("channels must be a non-empty object.")

    timeline = doc.get("timeline")
    if not isinstance(timeline, list) or not timeline:
        raise GestCompileError("timeline must be a non-empty array.")

    names = sorted(channels.keys())
    id_by_name = {n: i for i, n in enumerate(names)}

    buf = BytesIO()
    buf.write(MAGIC)
    buf.write(struct.pack("<H", FORMAT_VERSION))
    buf.write(struct.pack("<f", float(fps)))
    buf.write(struct.pack("<H", len(names)))

    for name in names:
        spec = channels[name]
        if not isinstance(spec, dict):
            raise GestCompileError(f"Channel {name!r}: invalid specification.")
        typ = spec.get("type")
        nb = _pack_utf8(name)
        if typ == "articulated":
            jc = spec.get("joint_count")
            if not isinstance(jc, int) or jc < 1:
                raise GestCompileError(f"Channel {name}: joint_count must be an integer >= 1.")
            se = spec.get("state_enum")
            sc = len(se) if isinstance(se, list) else 0
            buf.write(struct.pack("<BB", KIND_ARTICULATED, len(nb)))
            buf.write(nb)
            buf.write(struct.pack("<HH", jc, sc))
        elif typ == "direction":
            buf.write(struct.pack("<BB", KIND_DIRECTION, len(nb)))
            buf.write(nb)
        else:
            raise GestCompileError(
                f"Channel {name}: type {typ!r} is not supported by emitter v1 "
                "(only articulated | direction)."
            )

    for frame in timeline:
        if not isinstance(frame, dict):
            raise GestCompileError("Each timeline entry must be an object.")
        t = frame.get("t")
        if not isinstance(t, (int, float)):
            raise GestCompileError("Each frame must have a numeric t.")
        pose = frame.get("pose")
        if not isinstance(pose, dict):
            raise GestCompileError("Each frame must have an object pose.")

        buf.write(struct.pack("<B", OP_FRAME))
        buf.write(struct.pack("<d", float(t)))

        for name in names:
            if name not in pose:
                continue
            pdata = pose[name]
            if not isinstance(pdata, dict):
                continue
            spec = channels[name]
            cid = id_by_name[name]
            typ = spec.get("type") if isinstance(spec, dict) else None

            if typ == "articulated":
                joints = pdata.get("joints")
                if isinstance(joints, dict):
                    if joints.get("blob_ref") is not None and joints.get("values") is None:
                        raise GestCompileError(
                            f"Frame t={t}: channel {name} uses blob_ref; "
                            "emitter v1 requires inline values."
                        )
                    vals = joints.get("values")
                    if isinstance(vals, list):
                        raw = [float(x) for x in vals]
                        buf.write(struct.pack("<B", OP_JOINTS_F32))
                        buf.write(struct.pack("<HI", cid, len(raw)))
                        buf.write(struct.pack(f"<{len(raw)}f", *raw))
                si = pdata.get("state_index")
                if isinstance(si, int) and si >= 0:
                    buf.write(struct.pack("<B", OP_STATE))
                    buf.write(struct.pack("<HH", cid, si))

            elif typ == "direction":
                d = pdata.get("dir")
                if isinstance(d, list) and len(d) == 3:
                    buf.write(struct.pack("<B", OP_DIR_F32))
                    buf.write(struct.pack("<H", cid))
                    buf.write(
                        struct.pack(
                            "<fff",
                            float(d[0]),
                            float(d[1]),
                            float(d[2]),
                        )
                    )

    buf.write(struct.pack("<B", OP_END))
    return buf.getvalue()
