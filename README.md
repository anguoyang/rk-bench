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
Board: rk3588 (Rockchip RK3588) · runtime 2.3.2 · driver 0.9.8

| Model | Task | Input | Precision | p50 (ms) | p95 (ms) | FPS (p50) | Verdict | CPU fallback | RSS Δ (MB) | Model size (MB) |
| --- | --- | --- | --- | ---: | ---: | ---: | --- | ---: | ---: | ---: |
| MobileNetV2 | classify | 1x224x224x3 | FP | 8.63 | 8.89 | 115.9 | NPU_ONLY | 0% | 23.9 | 7.31 |
| ResNet50-v2 | classify | 1x224x224x3 | FP | 25.4 | 29.34 | 39.4 | NPU_ONLY | 0% | 110.1 | 49.92 |
| YOLOv8n | detect | 1x640x640x3 | FP | 37.5 | 38.58 | 26.7 | NPU_ONLY | 0% | 47.4 | 7.25 |
| YOLOv5s ReLU | detect | 1x640x640x3 | FP | 37.8 | 38.58 | 26.5 | NPU_ONLY | 0% | 52.8 | 15.56 |
| YOLO11n | detect | 1x640x640x3 | FP | 43.67 | 49.79 | 22.9 | NPU_ONLY | 0% | 46.1 | 6.71 |
| YOLOv10s | detect | 1x640x640x3 | FP | 88.09 | 90.49 | 11.4 | NPU_ONLY | 0% | 78.3 | 15.81 |
| YOLOv8n-obb | detect-obb | 1x640x640x3 | FP | 37.65 | 38.26 | 26.6 | NPU_ONLY | 0% | 44.8 | 7.3 |
| RetinaFace Mobile320 | face-detect | 1x320x320x3 | FP | 6.43 | 6.68 | 155.6 | MIXED | 4.05% | 12.9 | 1.49 |
| YOLOv8n-pose | pose | 1x640x640x3 | FP | 49.73 | 51.27 | 20.1 | NPU_ONLY | 0% | 47.6 | 8.17 |
| YOLOv8s-seg | segment | 1x640x640x3 | FP | 104.53 | 113.08 | 9.6 | NPU_ONLY | 0% | 112.1 | 24.46 |
<!-- LEADERBOARD:END -->

Full table with method notes: [docs/LEADERBOARD.md](docs/LEADERBOARD.md).
Raw data (the single source of truth): [data/leaderboard.json](data/leaderboard.json).

[中文说明](README.zh-CN.md)

## How it is measured

- Board: RK3588 (Ubuntu 22.04, kernel 6.1.118), rknpu driver 0.9.8, librknnrt 2.3.2.
  The board is busy (load ≈ 16); that is exactly why latency uses the
  runtime's hardware counters instead of wall-clock time.
- Protocol: a priming cycle first (one sacrificial load + 5 runs in a
  separate process), then **3 independent sessions** (separate processes),
  each warmup 10 + 50 measured runs; the published p50/p95 are the medians
  across sessions and the verdict is the worst session's. Zero inputs
  shaped by the model's own input attributes, default NPU core assignment.
  Single sessions on a busy board can sit ~15% off the sustained state —
  one YOLOv5s session measured 43.2 ms against 37.8–38.5 ms in three
  repeat processes — which is why no leaderboard number here ever comes
  from a single session.
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
