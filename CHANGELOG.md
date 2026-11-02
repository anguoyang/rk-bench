# Changelog

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
