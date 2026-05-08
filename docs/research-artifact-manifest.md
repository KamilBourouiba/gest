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

- Scenarios: `4`
- Sample floats: `1647`
- Decoded opcodes: `278`
- Industry baseline wins: `27`

## Tracked artifacts

- `schema/gest-0.2.schema.json`: present, `8189` bytes, sha256 `cf28bd22563344ecdb6b8732ab981a6b59aaa93837deac6763774709c28ceb65`
- `spec/gest-spec.md`: present, `7174` bytes, sha256 `c8b25b3e3e091ef879df9eb113095ec23f3529cb99e9d00398affeb077cc30b9`
- `include/sgm_v1.h`: present, `673` bytes, sha256 `e03b8a80c792b89d54255012fe9d03bc0ff4a8b489fbb86f192f3acd9c89b811`
- `src/gest/sgm_constants.py`: present, `512` bytes, sha256 `9334c9545270c70d2ba071f73bef692d62717b65963356133016276eb3fed09d`
- `demo/xr_dual_hand_arc.gest.json`: present, `12477` bytes, sha256 `1ee45c7e785c97ae7b1b794de1761c5fc8692bc74ef15bb40d36f0c32381d751`
- `demo/out/xr_dual_hand_arc.sgm`: present, `1562` bytes, sha256 `33be221c1f7da5389f5a240f8e3cbb5e9d806ab920d187fb99546899e50e9a3f`
- `demo/out/comparison-stats.json`: present, `2288` bytes, sha256 `b33f8acb1649f55d74cf3296a268ff613dcd3f55c8587bed848e619634e0fd50`
- `demo/out/multi-demo-stats.json`: present, `6883` bytes, sha256 `31f07adaf5bdc938cab82a54cf5d1e06132390f7dac46e2b1d1d44bb2b9ae2a4`
- `demo/out/industry-benchmark.json`: present, `12738` bytes, sha256 `4c7473996ef20a992eda620f596154badc282cde3bf1717535ef10a99435c740`
- `docs/research-paper.md`: present, `6695` bytes, sha256 `04918fac4996dfe78395aacf36be6e1343ed33e1cd900d9db8eaddc33b5274fd`
- `docs/industry-benchmark.md`: present, `4569` bytes, sha256 `9871c42ac2e92e6275c5411c32b9c8b9c980b5e20150354445c6fa930b08bf6c`
