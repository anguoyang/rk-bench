# Changelog

## v0.4.0 — 2026-11-06

- Leaderboard grows from 15 to 19 rows on RK3588: YOLOv8n-seg FP,
  PP-YOLOE-s FP, YOLOv8n-pose INT8, and YOLOv8s-seg INT8, all `NPU_ONLY`.
- All new models use official RKNN Model Zoo ONNX downloads and recipes,
  converted with rknn-toolkit2 2.3.2. INT8 calibration uses the Zoo's
  20-image COCO subset; pose follows its two-step hybrid recipe with
  the specified FP16 ranges retained.
- DeepLabV3 FP was skipped: the Zoo example supplies a TensorFlow `.pb`
  model and converter, without an ONNX download/recipe for this task.
- [Conversion provenance](docs/CONVERSION_V0.4.0.md) records sources,
  full ONNX/RKNN SHA-256 hashes, calibration, and the skipped target.
  The priming + three-session protocol and existing entries are unchanged.

## v0.3.0 — 2026-11-02

- `rkbench run --core-mask` pins NPU cores via `rknn_set_core_mask`
  (auto / 0 / 1 / 2 / 0_1 / 0_2 / 1_2 / all; default = never called).
  The setting is recorded in every report's protocol block.
- New study: docs/CORE_MASK_STUDY.md — core assignment on RK3588 is a
  ≤5% lever for single-stream models; single-core pinning costs the
  segmentation model 9.6%; two cores capture nearly all of the gain.

## v0.2.0 — 2026-11-02

- Leaderboard grows to 15 rows on RK3588:
  - PP-OCRv4-Det (FP, NPU_ONLY, 47.86 ms) and PP-OCRv4-Rec (FP, **MIXED** —
    one Reshape after the softmax runs on CPU, 2.58%).
  - INT8 twins for YOLOv8n / YOLOv5s / YOLO11n, quantized with the zoo's
    own recipe and its 20-image COCO calibration subset: 19.17 / 20.52 /
    31.20 ms vs FP 37.50 / 37.80 / 43.67 ms, all still `NPU_ONLY`. The
    calibration set is documented in each entry's notes.
- `rkbench run --note` records provenance notes in the report.
- Fixed: leaderboard row identity now includes precision — an INT8 report
  previously replaced its FP twin instead of sitting next to it.

## v0.1.0 — 2026-11-02

- First leaderboard: 10 public models measured on RK3588 under the frozen
  v0.1 protocol (priming + 3 independent sessions, median p50/p95,
  PERF_RUN hardware timing). Nine models are `NPU_ONLY`; RetinaFace
  Mobile320 is `MIXED` (five Reshape ops fall back to the CPU, 4.05%).
- `rkbench run` benchmarks one model: p50/p95 latency, CPU-fallback verdict
  (NPU_ONLY / MIXED / CPU_HEAVY / UNKNOWN), memory (file size, RSS delta,
  PERF_DETAIL RW per frame).
- `rkbench add` validates SoC/runtime/driver consistency before a report
  may enter a board table; `rkbench table` generates the published tables
  from `data/leaderboard.json`, the single source of truth.
- Measurement method and verdict thresholds match RK Edge Doctor, whose
  model health table now links here instead of duplicating the data.
