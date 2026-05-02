from __future__ import annotations

from typing import Any


def _articulated_meta(ch: dict[str, Any]) -> tuple[int, int] | None:
    if ch.get("type") != "articulated":
        return None
    jc = ch.get("joint_count")
    if not isinstance(jc, int) or jc < 1:
        return None
    stride = ch.get("joint_value_stride", 3)
    if stride not in (3, 7):
        return None
    return jc, int(stride)


def validate_invariants(doc: dict[str, Any]) -> list[str]:
    """
    Structural rules not covered by JSON Schema:
    `values` length vs joint_count * stride, state indices, direction vectors.
    """
    errors: list[str] = []
    channels = doc.get("channels")
    if not isinstance(channels, dict):
        return errors

    meta: dict[str, tuple[int, int]] = {}
    state_sizes: dict[str, int] = {}
    for cname, spec in channels.items():
        if not isinstance(spec, dict):
            continue
        m = _articulated_meta(spec)
        if m:
            meta[cname] = m
            se = spec.get("state_enum")
            if isinstance(se, list):
                state_sizes[cname] = len(se)

    timeline = doc.get("timeline")
    if not isinstance(timeline, list):
        return errors

    for fi, frame in enumerate(timeline):
        if not isinstance(frame, dict):
            continue
        t = frame.get("t")
        pose = frame.get("pose")
        if not isinstance(pose, dict):
            continue
        prefix = f"timeline[{fi}] (t={t!r})"

        for cname, pdata in pose.items():
            if cname not in channels:
                errors.append(f"{prefix} / pose / {cname}: channel missing from channels")
                continue
            ch = channels[cname]
            if not isinstance(ch, dict) or not isinstance(pdata, dict):
                continue

            if ch.get("type") == "articulated" and cname in meta:
                jc, stride = meta[cname]
                joints = pdata.get("joints")
                if isinstance(joints, dict):
                    vals = joints.get("values")
                    bref = joints.get("blob_ref")
                    if vals is not None and bref is not None:
                        errors.append(
                            f"{prefix} / pose / {cname} / joints: "
                            "values and blob_ref are mutually exclusive"
                        )
                    if isinstance(vals, list):
                        expected = jc * stride
                        if len(vals) != expected:
                            errors.append(
                                f"{prefix} / pose / {cname} / joints / values: "
                                f"length {len(vals)} != joint_count * stride ({jc}*{stride}={expected})"
                            )
                    elif bref is None and vals is None:
                        errors.append(
                            f"{prefix} / pose / {cname} / joints: "
                            "neither values nor blob_ref (missing joint payload)"
                        )
                si = pdata.get("state_index")
                if si is not None:
                    if not isinstance(si, int) or si < 0:
                        errors.append(
                            f"{prefix} / pose / {cname} / state_index: expected integer >= 0"
                        )
                    elif cname in state_sizes and si >= state_sizes[cname]:
                        errors.append(
                            f"{prefix} / pose / {cname} / state_index: {si} out of range "
                            f"(state_enum length={state_sizes[cname]})"
                        )

            if ch.get("type") == "direction":
                d = pdata.get("dir")
                if d is not None:
                    if not isinstance(d, list) or len(d) != 3:
                        errors.append(
                            f"{prefix} / pose / {cname} / dir: exactly 3 numbers required"
                        )

    return errors
