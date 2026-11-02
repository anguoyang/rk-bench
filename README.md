# rk-bench

[![tests](https://github.com/anguoyang/rk-bench/actions/workflows/ci.yml/badge.svg)](https://github.com/anguoyang/rk-bench/actions/workflows/ci.yml)
[![License](https://img.shields.io/badge/license-Apache--2.0-blue.svg)](LICENSE)
[![Python](https://img.shields.io/badge/python-3.9%2B-blue.svg)](pyproject.toml)

**Which model should you run on RK3588 — and how fast will it actually go?**

rk-bench is a measured leaderboard of public RKNN models on Rockchip boards.
Every number is produced on real hardware under one frozen protocol, by a
zero-dependency tool you can re-run yourself: no copied vendor tables, no
wall-clock timing, no guessed figures. Latency comes from the NPU runtime's
own PERF_RUN hardware counters, and every model also gets a CPU-fallback
verdict, so a "fast" model that secretly runs half its layers on the CPU
cannot hide.

```sh
PYTHONPATH=src python3 -m rkbench run yolov8n.rknn --name YOLOv8n --task detect \
  --soc rk3588 --json report.json
```

## Leaderboard — RK3588

<!-- LEADERBOARD:BEGIN -->
_The first board is being measured; this table is generated from
`data/leaderboard.json` and appears here with the v0.1 release._
<!-- LEADERBOARD:END -->

Full table with method notes: [docs/LEADERBOARD.md](docs/LEADERBOARD.md).
Raw data (the single source of truth): [data/leaderboard.json](data/leaderboard.json).

[中文说明](README.zh-CN.md)

## How it is measured

- Board: RK3588 (Ubuntu 22.04, kernel 6.1.118), rknpu driver 0.9.8, librknnrt 2.3.2.
  The board is busy (load ≈ 16); that is exactly why latency uses the
  runtime's hardware counters instead of wall-clock time.
- Protocol: a priming cycle first (one sacrificial load + 5 runs in a
  separate process), then warmup 10 + 50 measured runs, zero inputs shaped
  by the model's own input attributes, default NPU core assignment.
  The priming step exists because of a measured quirk: on RK3588 with the
  `rknpu_ondemand` governor, the first RKNN process after an idle gap is
  ~15% slower across *all* runs (YOLO11n: 51.4 ms vs 44.0 ms primed), and
  warmup inside that process does not cure it. rkbench primes by default,
  so the numbers here are the sustained state and a single `rkbench run`
  reproduces them; `--no-prime` skips it and says so in the report.
- CPU fallback: PERF_DETAIL per-layer accounting. `InputOperator` /
  `OutputOperator` staging is structural and never counted as fallback.
  Fallback share < 1% and no single fallback op ≥ 100 µs → `NPU_ONLY`;
  1–20% → `MIXED`; > 20% → `CPU_HEAVY`; unmeasurable → `UNKNOWN`.
  These thresholds match [RK Edge Doctor](https://github.com/anguoyang/rk-edge-doctor),
  the sister project that diagnoses a single model in depth; rk-bench is the
  cross-model leaderboard, and this repository is now the single source of
  truth for the model health data both projects publish.
- Memory: model file size; process RSS increase for load + one run (median
  of 3 fresh probe processes); PERF_DETAIL per-layer RW total per frame.
- Privacy: reports record the model file name and SHA-256 only, never paths,
  and no board serial numbers.

## Usage

```sh
# benchmark one model (run this on the Rockchip board)
PYTHONPATH=src python3 -m rkbench run model.rknn --name YOLOv8n --task detect \
  --soc rk3588 --source-name "RKNN Model Zoo" --json report.json

# add the report to the leaderboard (rejects mismatched runtime/driver/SoC)
PYTHONPATH=src python3 -m rkbench add report.json --into data/leaderboard.json

# regenerate the published tables from the data
PYTHONPATH=src python3 -m rkbench table --from data/leaderboard.json \
  --out docs/LEADERBOARD.md --readme README.md

PYTHONPATH=src python3 -m rkbench --version
```

An optional installation exposes the `rkbench` console command:
`python3 -m pip install .` — running from source above needs no packages.

Exit codes: usage errors 2; a generated report (including an `UNKNOWN` one)
0; `add` environment-validation failures 1.

## Adding a model or a board

Run `rkbench run` on your board and open a **bench-report issue** with the
JSON attached. Entries are only merged into a board table when SoC, runtime
and driver match that table — other boards get their own table instead of a
mixed one. See [CONTRIBUTING.md](CONTRIBUTING.md).

## What this is not

No accuracy/mAP evaluation (consult the model's own paper or the official
model zoo), no power measurement, no model conversion, no proprietary
models. Only public models, measured in the open.

Maintained alongside [RK Edge Doctor](https://github.com/anguoyang/rk-edge-doctor)
and the open-source notes at https://site-ai-gateway.com — if rk-bench saved
you a day of guessing, a star helps other Rockchip developers find it.
