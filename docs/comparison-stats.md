# Demo comparison stats

These numbers are measured from `demo/run_demo.py` for the same generated motion clip.

## Demo shape

- `frames`: `9`
- `duration_seconds`: `1.2`
- `fps`: `60`
- `channels`: `['gaze', 'left_hand', 'right_hand']`
- `floats_per_frame`: `33`
- `sample_floats_total`: `297`
- `decoded_opcode_count`: `54`

## Artifact sizes

| Artifact | Kind | Bytes | Ratio to `.sgm` | Notes |
|----------|------|-------|-----------------|-------|
| `.gest JSON pretty` | `gest` | 12477 | 7.988x | Readable canonical IR with schema-facing metadata |
| `.gest JSON compact` | `gest` | 4679 | 2.996x | Same IR without whitespace |
| `.gest JSON gzip` | `gest` | 1366 | 0.875x | Compressed compact JSON |
| `.sgm v1 bytecode` | `sgm` | 1562 | 1.0x | Runtime bytecode emitted by the reference compiler |
| `Recovered .gest JSON` | `gest` | 15348 | 9.826x | Lossy draft recovered from .sgm |
| `Decoded SGM dump` | `debug` | 14657 | 9.383x | Debug channel table + reconstructed timeline |
| `Landmark JSON baseline` | `baseline` | 2536 | 1.624x | ML-style landmarks only; no IR validation contract |
| `CSV landmarks baseline` | `baseline` | 3712 | 2.376x | Flat rows; easy to inspect, weak structure |
| `BVH-like text baseline` | `baseline` | 3309 | 2.118x | Sampled skeleton-style text baseline for this clip |

## Methodology

- All byte counts are measured locally from the same generated demo document.
- Baselines are concrete transformations of the same numeric samples, not official exporters.
- BVH-like baseline is a sampled-channel text baseline shaped like BVH, not a DCC-certified BVH exporter.
- Ratios are relative to .sgm v1 bytecode for this demo clip.
