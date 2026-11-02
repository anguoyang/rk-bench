# Contributing to rk-bench

rk-bench grows by measured reports, not by opinions. Three ways to help:

## 1. Submit a benchmark report (most valuable)

1. On your Rockchip board, run:

   ```sh
   PYTHONPATH=src python3 -m rkbench run your_model.rknn \
     --name "Model Name" --task detect --soc rk3588 \
     --source-name "where the model came from" --json report.json
   ```

2. Open a **bench-report** issue and attach `report.json`. It contains the
   model file name and SHA-256 only — never paths or serial numbers.
3. A maintainer checks the environment fields and merges it with
   `rkbench add`. A report whose SoC, runtime or driver differs from an
   existing board table starts a new board table instead of mixing in.

Only public models are accepted (official model-zoo models or public
conversions of public ONNX models). Please name the source.

## 2. Add a board

Boards get their own table in `data/` (e.g. `leaderboard-rk3576.json`).
Measure at least three well-known models under the same frozen protocol so
the new table is cross-checkable against the RK3588 one.

## 3. Code

- Python 3.9+, standard library only. No new runtime dependencies, ever.
- Tests must pass on Python 3.9 and 3.12 (`python -m pytest tests/ -q`).
  The PERF_DETAIL parser is regression-tested against a real captured
  fixture; do not weaken those assertions.
- Numbers in the README and `docs/LEADERBOARD.md` are generated from
  `data/*.json` by `rkbench table`. Never edit them by hand.

## Ground rules

- No proprietary models, no private board data, no benchmarketing: if a
  number cannot be reproduced from the attached JSON, it does not ship.
- Unknown stays `UNKNOWN`. A measurement we could not make is reported as
  such, with the reason — that honesty is the project's whole point.
