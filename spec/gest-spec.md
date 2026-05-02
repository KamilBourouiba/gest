# .gest specification (gesture IR)

**Document version:** 0.2  
**Status:** working draft

## 1. Scope

The **.gest** format encodes only:

- spatial positions and orientations;
- motion over time;
- discrete and continuous body states (hands, face, skeleton, gaze);
- temporal sequencing.

It does **not** encode natural-language semantics (no lexicon, glosses, or sentences). Identifiers such as `chest` or `p0` are **technical frame labels**, not meaning units.

## 2. Interchange representations

- **Canonical for validation:** JSON (`.gest.json` or a suffix documented by the tool).
- **Human / pipelines:** YAML with the same key tree as JSON (aside from YAML-specific quirks).

The machine-readable schema is `schema/gest-0.2.schema.json`.

## 3. Metadata (`metadata`)

| Field | Type | Description |
|-------|------|-------------|
| `version` | string | Format semver (e.g. `"0.2"`). |
| `profile` | string | `full`, `rt`, `cmp`, `neural_bundle`. |
| `fps` | number | Nominal rate (> 0). |
| `time_base` | string | `seconds` or `ticks`. |
| `units` | string | e.g. `meters`. |
| `coordinate_system` | object | `handedness`, `up`, `forward` (axis conventions). |
| `capabilities` | array of strings | Explicit extensions claimed by the file. |

## 4. Space (`space`)

- **`anchors`:** named frames with `parent` (reference to another anchor, or absent for root), `t` translation `[x,y,z]`, `q` quaternion `[x,y,z,w]` (documented order here: **xyzw** in JSON; implementations must stay consistent).
- **`named_points`:** points in a `parent` frame with `local: [x,y,z]`.

No free-form prose fields on the SGPU hot path.

## 5. Channels (`channels`)

Each key is a channel id. Each value is an object with at least:

- `type`: `articulated` | `blendshape_set` | `direction` | `scalar` (profile-extensible).
- `parent`: anchor or parent channel when applicable.

Common types:

- **articulated:** `joint_count`, `joint_layout` (topology id, e.g. a known rig), `state_enum` (closed list of **non-linguistic** state labels).
- **blendshape_set:** `blendshape_names_sha256` or an external table referenced by hash.
- **direction:** `representation: unit_vector`.

## 6. Interpolation (`interpolation_defaults`)

Keys: modes for `translation`, `rotation`, `scalar` (e.g. `linear`, `cubic_hermite`, `slerp`).

## 7. Timeline (`timeline`)

Array of frame objects, each with:

- `t`: number (seconds when `time_base` = `seconds`).
- `pose`: tree parallel to `channels` (subset allowed per frame).
- Optional: `interpolation_override`, `in_tangent`, `out_tangent` (curves).

### Poses and blobs

- Large payloads may use `blob_ref` (opaque int or string) pointing to a root-level `blobs` table (see JSON schema).
- Formats: `packed_float16`, `raw_float32`, etc. (enumerated in the schema).

## 8. Streaming (`stream`, optional)

Segments with `seq`, `channels_digest`, `byte_range` for chunked files or containers.

## 9. Profiles

| Profile | Use |
|---------|-----|
| `full` | Keyframes, tangents, full hierarchy. |
| `rt` | Low latency, compact poses, few or no external blobs. |
| `cmp` | Pose dictionaries, sparsity, strong deltas. |
| `neural_bundle` | Latents + numeric control; decode outside low-level execution spec. |

## 10. Compilation to `.sgm` (informative)

Logical steps: hierarchy resolution → time discretization to ticks → buffer flattening → opcode emission (`ALLOC_CHANNEL`, `WRITE_JOINT_BUFFER`, `SET_DISCRETE_STATE`, `SCHEDULE_FRAME`, …). No natural-language table on the hot path.

## 11. Producer metadata (`producer_notes`, optional)

Off the SGPU execution path; may hold tooling info. **Do not** put engine-facing gesture semantics here.

## 12. Conformance

A file is **0.2-conformant** if it validates against `gest-0.2.schema.json` and satisfies the invariants in this document (axes, quaternion order, declared profile).

## 13. YAML

`.yaml` / `.yml` files with the **same tree** as JSON are accepted by the tools (`load_path`, `gest-validate`). Dependency: `pip install gest-ir[yaml]` (PyYAML).

## 14. `joint_value_stride` (articulated channel)

Integer **3** or **7** (default **3**). Expected `joints.values` length: `joint_count * joint_value_stride` (floats: 3 = translation per joint; 7 = translation + `xyzw` quaternion per joint).

## 15. Invariants (beyond JSON Schema)

Additional checks implemented in tooling:

- `values` length vs `joint_count` and `joint_value_stride`;
- `state_index` within `state_enum` when that list is present;
- `dir` length 3 for `direction` channels;
- `values` and `blob_ref` mutually exclusive on the same `joints` block.

## 16. `.sgm` v1 bytecode (reference sketch)

Shared numeric constants for ports:

- C: `include/sgm_v1.h` (`SGM_V1_*` macros — **must match** the Python module below).
- Python: `src/gest/sgm_constants.py` (used by `compile_to_bytes` / `decode_sgm_bytes`).

The test suite parses the header and asserts equality with the Python values.

Little-endian wire layout. Sequence:

1. **Magic:** 4 bytes `SGM\x01`.
2. **Fixed header:** `u16` `format_version` (=1), `f32` `fps`, `u16` `channel_count`.
3. **Channel table** (names sorted lexicographically):
   - `u8` `kind`: `1` articulated, `2` direction;
   - `u8` `name_len` then UTF-8 name;
   - if articulated: `u16` `joint_count`, `u16` `state_count` (length of `state_enum`, 0 if absent).
4. **Timeline:** for each frame, `u8` opcode `0x30` then `f64` `t`; for each channel present in `pose` (same sorted order):
   - articulated: `0x31` `u16` `channel_id`, `u32` `n_floats`, then `n_floats`×`f32`; optionally `0x32` `u16` `channel_id`, `u16` `state_index`;
   - direction: `0x33` `u16` `channel_id`, then 3×`f32`.
5. **End:** byte `0xFF`.

The reference emitter **rejects** articulated poses that use only `blob_ref` without inline `values` (future extension may decode `blobs`).

## 17. Decoding (reference tooling)

`decode_sgm_bytes` in the Python package parses v1 bytecode: magic, header, channel table, then a linear opcode list (`frame` with `t`, `joints_f32`, `state_index`, `direction_f32`). `decoded_to_pose_timeline` rebuilds a minimal `timeline`-shaped structure (channel names from ids, merged `pose` entries per frame). The CLI `gest-dump-sgm` prints that structure as JSON for debugging and tests.

## 18. Full `.gest` recovery from `.sgm` (lossy)

`gest_document_from_sgm_bytes` builds a **draft** 0.2 document that passes schema + IR invariants when the bytecode was produced by the reference emitter: minimal `space` (`world` anchor only), synthetic `joint_layout` / `state_enum`, all channels parented to `world`, optional `joint_value_stride` inferred from the first well-shaped `values` buffer, `profile: rt`, and `capabilities` including `sgm_roundtrip`. This is **not** a bit-identical restore of an arbitrary source file (original anchors, blendshapes, producer text, etc. are not on the wire). CLI: `gest-sgm-to-gest input.sgm out.json`.
