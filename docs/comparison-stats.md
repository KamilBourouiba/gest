# Demo comparison stats

These numbers are measured from `demo/run_demo.py` for the same generated motion clip.

## Demo shape

- `frames`: `32`
- `duration_seconds`: `2.4`
- `fps`: `60`
- `channels`: `['gaze', 'left_hand', 'right_hand']`
- `floats_per_frame`: `33`
- `sample_floats_total`: `1056`
- `decoded_opcode_count`: `192`

## Artifact sizes

| Artifact | Kind | Bytes | Ratio to `.sgm` | Notes |
|----------|------|-------|-----------------|-------|
| `.gest JSON pretty` | `gest` | 38656 | 7.124x | Readable canonical IR with schema-facing metadata |
| `.gest JSON compact` | `gest` | 13529 | 2.493x | Same IR without whitespace |
| `.gest JSON gzip` | `gest` | 2513 | 0.463x | Compressed compact JSON |
| `.sgm v1 bytecode` | `sgm` | 5426 | 1.0x | Runtime bytecode emitted by the reference compiler |
| `Recovered .gest JSON` | `gest` | 51312 | 9.457x | Lossy draft recovered from .sgm |
| `Decoded SGM dump` | `debug` | 50621 | 9.329x | Debug channel table + reconstructed timeline |
| `Landmark JSON baseline` | `baseline` | 9102 | 1.677x | ML-style landmarks only; no IR validation contract |
| `CSV landmarks baseline` | `baseline` | 13670 | 2.519x | Flat rows; easy to inspect, weak structure |
| `BVH-like text baseline` | `baseline` | 7890 | 1.454x | Sampled skeleton-style text baseline for this clip |

## Methodology

- All byte counts are measured locally from the same generated demo document.
- Baselines are concrete transformations of the same numeric samples, not official exporters.
- BVH-like baseline is a sampled-channel text baseline shaped like BVH, not a DCC-certified BVH exporter.
- Ratios are relative to .sgm v1 bytecode for this demo clip.
