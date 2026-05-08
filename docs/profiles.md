# `.gest` profiles

Profiles are named operating modes for the same core IR. They do **not** change the rule that `.gest` is non-semantic; they constrain how motion data is packaged for different runtimes and pipelines.

The canonical profile names are:

- `full`
- `rt`
- `cmp`
- `neural`

`neural_bundle` is accepted as a compatibility alias for `neural` in code, but new files should use `neural`.

## `full`

**Suffix:** `.gest.full.json`  
**Use:** authoring, archival interchange, dataset storage, offline compilation.

This is the most expressive profile. It can contain hierarchy, named points, interpolation defaults, tangents, inline or blob-backed samples, and producer notes off the runtime path.

Recommended capabilities:

- `hierarchy`
- `hermite_tangents`
- `blob_external`

Example: [`examples/profiles/full.gest.json`](../examples/profiles/full.gest.json)

## `rt`

**Suffix:** `.gest.rt.json`  
**Use:** low-latency playback, streaming, embedded runtimes, SGPU queues.

The `rt` profile favors short chunks, predictable channel declarations, and inline pose payloads that can be copied directly into runtime buffers. It normally uses integer-like ticks in `t` and may include a `stream` table for segment lookup.

Recommended capabilities:

- `streaming_segments`
- `inline_pose`

Example: [`examples/profiles/rt.gest.json`](../examples/profiles/rt.gest.json)

## `cmp`

**Suffix:** `.gest.cmp.json`  
**Use:** compact storage, network transport, delta frames, pose dictionaries, external payload blobs.

The `cmp` profile is for compressed artifacts. The core JSON may mostly describe channels, segment metadata, and `blob_ref` handles; numeric payloads can move into `blobs` or an external container. Decoders must still recover the same structural poses, but not necessarily from inline arrays.

Recommended capabilities:

- `blob_external`
- `delta_frames`
- `pose_dictionary`

Example: [`examples/profiles/cmp.gest.json`](../examples/profiles/cmp.gest.json)

## `neural`

**Suffix:** `.gest.neural.json`  
**Use:** latent motion bundles, learned motion upsampling, neural decoder inputs.

The `neural` profile stores **non-semantic** latent tensors and numeric controls. It must not store natural-language prompts, glosses, or meanings on the runtime path. A `latent` channel declares tensor `dtype`, `shape`, and an opaque `decoder_hint`; timeline frames then reference latent payloads through `blob_ref` or inline numeric arrays.

Recommended capabilities:

- `latent_channels`
- `decoder_hint`
- `numeric_control`

Example: [`examples/profiles/neural.gest.json`](../examples/profiles/neural.gest.json)

## Profile selection

Use this decision rule:

- Need editing, review, archival quality, or all metadata? Use **`full`**.
- Need immediate playback or streaming to a runtime? Use **`rt`**.
- Need storage/network efficiency? Use **`cmp`**.
- Need a learned decoder or latent motion representation? Use **`neural`**.

All profiles still validate against the same base schema and invariants.

