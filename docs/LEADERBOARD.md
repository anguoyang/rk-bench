# RKNN leaderboard — rk3588

Measured with rk-bench under one frozen protocol (warmup 10 + 50 runs,
PERF_RUN hardware timing, zero inputs). Generated from
`data/leaderboard.json` — do not edit numbers here by hand.

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

Verdicts: `NPU_ONLY` means no operator fell back to the CPU (input/output
staging excluded), `MIXED` / `CPU_HEAVY` mean real fallback work runs on
the CPU, `UNKNOWN` means the model could not be measured. RSS Δ is the
process memory increase for load + one run (median of 3 fresh processes).
Input is the model's declared tensor shape (the RKNN model zoo FP
models are NHWC, e.g. 1x640x640x3). p50/p95 are medians of 3
independent sessions after a priming cycle; see the README's
"How it is measured" section for why both steps exist.
