"""Leaderboard data: the single source of truth and its rendering.

data/leaderboard.json (schema 1) is the only place benchmark numbers live.
README tables and docs/LEADERBOARD.md are generated from it; nobody edits
numbers by hand. Entries may only be added when the board environment
(SoC, runtime, driver) matches the board the leaderboard belongs to, so a
table never mixes incomparable measurements.
"""

import json
from datetime import datetime, timezone
from pathlib import Path

from .bench import input_shape_of

ENV_KEYS = ("soc", "runtime", "driver")


class LeaderboardError(Exception):
    pass


def empty_leaderboard(board: dict) -> dict:
    return {"schema": 1,
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "board": {k: board.get(k) for k in
                      ("soc", "board_label", "os", "kernel", "soc_model",
                       "driver", "runtime")},
            "entries": []}


def entry_from_report(report: dict) -> dict:
    model = report["model"]
    latency = report["latency_ms"]
    return {
        "model": model["display_name"],
        "task": model["task"],
        "variant": model["variant"],
        "precision": model["precision"],
        "input_shape": input_shape_of(report),
        "source": model["source"],
        "file": {"basename": model["file"], "sha256": model["sha256"],
                 "size_bytes": model["size_bytes"]},
        "board": report["board"],
        "measured_at": report["generated_at"],
        "protocol": report["protocol"],
        "latency_ms": latency,
        "fps_p50": report["fps_p50"],
        "verdict": report["verdict"],
        "fallback_ops": report["fallback_ops"],
        "fallback_share_pct": report["fallback_share_pct"],
        "memory": report["memory"],
        "notes": report["notes"],
    }


def check_env_compatible(board_env: dict, entry: dict) -> None:
    entry_board = entry.get("board") or {}
    for key in ENV_KEYS:
        expected = board_env.get(key)
        actual = entry_board.get(key)
        if expected and actual and expected != actual:
            raise LeaderboardError(
                "environment mismatch on %s: leaderboard is %r but the "
                "report was measured with %r; start a separate board table "
                "instead of mixing environments" % (key, expected, actual))


def add_entry(data: dict, entry: dict) -> dict:
    """Insert or replace the entry for the same model+variant. Returns data."""
    check_env_compatible(data.get("board") or {}, entry)
    entries = data.setdefault("entries", [])
    for i, existing in enumerate(entries):
        if (existing["model"] == entry["model"]
                and existing.get("variant", "") == entry.get("variant", "")):
            entries[i] = entry
            data["generated_at"] = datetime.now(timezone.utc).isoformat()
            return data
    entries.append(entry)
    data["generated_at"] = datetime.now(timezone.utc).isoformat()
    return data


def load_leaderboard(path: Path) -> dict:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError) as error:
        raise LeaderboardError("cannot read leaderboard %s: %s" % (path, error))
    if data.get("schema") != 1 or not isinstance(data.get("entries"), list):
        raise LeaderboardError("%s is not a schema-1 leaderboard" % path)
    return data


def save_leaderboard(path: Path, data: dict) -> None:
    path.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n",
                    encoding="utf-8")


def sorted_entries(data: dict) -> list:
    def key(entry):
        p50 = entry["latency_ms"].get("p50")
        return (entry["task"], p50 is None, p50 if p50 is not None else 0,
                entry["model"])
    return sorted(data.get("entries", []), key=key)


def _fmt(value, digits=1):
    if value is None:
        return "—"
    if isinstance(value, float):
        return ("%.*f" % (digits, value)).rstrip("0").rstrip(".") if digits else str(value)
    return str(value)


def render_table(data: dict) -> str:
    board = data.get("board") or {}
    lines = [
        "| Model | Task | Input | Precision | p50 (ms) | p95 (ms) | FPS (p50) | Verdict | CPU fallback | RSS Δ (MB) | Model size (MB) |",
        "| --- | --- | --- | --- | ---: | ---: | ---: | --- | ---: | ---: | ---: |",
    ]
    for e in sorted_entries(data):
        latency = e["latency_ms"]
        memory = e.get("memory") or {}
        fallback = e.get("fallback_share_pct")
        size_mb = None
        if memory.get("file_size_bytes"):
            size_mb = round(memory["file_size_bytes"] / 1048576.0, 2)
        lines.append(
            "| {model} | {task} | {shape} | {prec} | {p50} | {p95} | {fps} | {verdict} | {fb} | {rss} | {size} |".format(
                model=e["model"] + ((" " + e["variant"]) if e.get("variant") else ""),
                task=e["task"], shape=e.get("input_shape") or "—",
                prec=e.get("precision") or "—",
                p50=_fmt(latency.get("p50"), 2), p95=_fmt(latency.get("p95"), 2),
                fps=_fmt(e.get("fps_p50"), 1), verdict=e["verdict"],
                fb=("—" if fallback is None else _fmt(fallback, 2) + "%"),
                rss=_fmt(memory.get("rss_delta_mb"), 1),
                size=_fmt(size_mb, 2)))
    header = ("Board: {label} ({soc_model}) · runtime {runtime} · driver {driver}"
              .format(label=board.get("board_label") or "?",
                      soc_model=board.get("soc_model") or board.get("soc") or "?",
                      runtime=board.get("runtime") or "?",
                      driver=board.get("driver") or "?"))
    return header + "\n\n" + "\n".join(lines) + "\n"


def render_leaderboard_md(data: dict) -> str:
    board = data.get("board") or {}
    parts = [
        "# RKNN leaderboard — %s" % (board.get("board_label") or "board"),
        "",
        "Measured with rk-bench under one frozen protocol (warmup 10 + 50 runs,",
        "PERF_RUN hardware timing, zero inputs). Generated from",
        "`data/leaderboard.json` — do not edit numbers here by hand.",
        "",
        render_table(data).rstrip(),
        "",
        "Verdicts: `NPU_ONLY` means no operator fell back to the CPU (input/output",
        "staging excluded), `MIXED` / `CPU_HEAVY` mean real fallback work runs on",
        "the CPU, `UNKNOWN` means the model could not be measured. RSS Δ is the",
        "process memory increase for load + one run (median of 3 fresh processes).",
        "",
    ]
    return "\n".join(parts)


README_BEGIN = "<!-- LEADERBOARD:BEGIN -->"
README_END = "<!-- LEADERBOARD:END -->"


def update_readme(readme_path: Path, data: dict) -> None:
    text = readme_path.read_text(encoding="utf-8")
    if README_BEGIN not in text or README_END not in text:
        raise LeaderboardError(
            "README %s lacks the %s / %s markers" % (readme_path, README_BEGIN, README_END))
    before, rest = text.split(README_BEGIN, 1)
    _, after = rest.split(README_END, 1)
    block = README_BEGIN + "\n" + render_table(data).rstrip() + "\n" + README_END
    readme_path.write_text(before + block + after, encoding="utf-8")
