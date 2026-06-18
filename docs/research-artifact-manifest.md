# Research artifact manifest

This manifest records the reproducible surface for the `.gest` draft artifact.

## Claims

- Motion representation is intentionally non-semantic.
- The reference pipeline validates .gest before compiling .sgm.
- SGM v1 is smaller than compact .gest JSON in every generated scenario.
- All byte-size comparisons are generated from local transforms of the same samples.
- Industry-facing comparisons distinguish byte-size wins from cases where existing standards remain better tools.

## Reproducibility

- Python: `3.10.14`
- SGM format version: `1`
- SGM magic: `53474d01`
- Test command: `PYTHONPATH=src:. pytest -q`

## Aggregate evidence

- Scenarios: `6`
- Sample floats: `4308`
- Decoded opcodes: `808`
- Industry baseline wins: `41`

## Tracked artifacts

- `schema/gest-0.2.schema.json`: present, `8189` bytes, sha256 `cf28bd22563344ecdb6b8732ab981a6b59aaa93837deac6763774709c28ceb65`
- `spec/gest-spec.md`: present, `7174` bytes, sha256 `c8b25b3e3e091ef879df9eb113095ec23f3529cb99e9d00398affeb077cc30b9`
- `include/sgm_v1.h`: present, `673` bytes, sha256 `e03b8a80c792b89d54255012fe9d03bc0ff4a8b489fbb86f192f3acd9c89b811`
- `src/gest/sgm_constants.py`: present, `512` bytes, sha256 `9334c9545270c70d2ba071f73bef692d62717b65963356133016276eb3fed09d`
- `demo/xr_dual_hand_arc.gest.json`: present, `38656` bytes, sha256 `2da30074436bef2e5c065acddb35cd237b40e64ad4c4c92451f76179c4b61b7d`
- `demo/out/xr_dual_hand_arc.sgm`: present, `5426` bytes, sha256 `e8a3f4378d133063d46a718c53dc51058aa8016fc94c492551a79248720ba334`
- `demo/out/comparison-stats.json`: present, `2293` bytes, sha256 `30497912cfc8d5ee54fbe4c3d0283fe347e69b4b5b015f5b3e4441261266cc85`
- `demo/out/multi-demo-stats.json`: present, `10057` bytes, sha256 `355d466d87c553545c3b3ad93e37341318ca1d487ee9bea5dda29c28430a01a8`
- `demo/out/industry-benchmark.json`: present, `17444` bytes, sha256 `fdf9e1ebf227b85e072c25bb419fd7ff14e034f110847bc19902cd32c6f4f557`
- `docs/research-paper.md`: present, `7002` bytes, sha256 `c9548fcef201c1f92f22cc3757ac1a2ba2534ceb58f80544ea2e8280dedfef86`
- `docs/industry-benchmark.md`: present, `5976` bytes, sha256 `9547372a1b4ab278d707977752f6f345b388000b5f24a4b0d2bb7eab7531bd96`
