"""rkbench run: benchmark one converted .rknn model under the frozen protocol.

Protocol v0.1 (see the project SPEC): warmup 10 + 50 measured runs, latency
from the runtime's PERF_RUN hardware counters, CPU-fallback verdict from
PERF_DETAIL with RK Edge Doctor thresholds, memory as file size + process
RSS delta (median of independent probe processes) + PERF_DETAIL RW sum.
"""

import hashlib
import json
import os
import platform
import statistics
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

from . import __version__
from .perf_parse import judge, latency_stats, parse_perf_detail
from .rknn_runtime import ModelLoadError, RknnRuntime, RuntimeUnavailable

PROTOCOL = {"warmup": 10, "runs": 50, "timer": "PERF_RUN",
            "rss_cycles": 3}
THRESHOLDS = {"cpu_heavy_pct": 20.0, "npu_only_fallback_pct": 1.0,
              "single_op_us": 100}


def read_vmrss_kb() -> Optional[int]:
    try:
        with open("/proc/self/status", encoding="utf-8") as handle:
            for line in handle:
                if line.startswith("VmRSS:"):
                    return int(line.split()[1])
    except (OSError, ValueError):
        pass
    return None


def host_info(board_label: str) -> dict:
    soc_model = "unknown"
    try:
        raw = Path("/proc/device-tree/model").read_bytes()
        soc_model = raw.split(b"\x00")[0].decode("utf-8", "replace") or soc_model
    except OSError:
        pass
    os_name = "unknown"
    try:
        for line in Path("/etc/os-release").read_text(encoding="utf-8").splitlines():
            if line.startswith("PRETTY_NAME="):
                os_name = line.split("=", 1)[1].strip().strip('"') or os_name
                break
    except OSError:
        pass
    try:
        loadavg = [round(v, 2) for v in os.getloadavg()]
    except (OSError, AttributeError):
        loadavg = None
    return {"board_label": board_label, "soc_model": soc_model,
            "os": os_name, "kernel": platform.release() or "unknown",
            "hostname": platform.node() or "unknown", "loadavg": loadavg}


def _empty_report(path: Path, meta: dict) -> dict:
    return {
        "schema": 1, "kind": "bench", "tool_version": __version__,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "model": {"display_name": meta.get("name") or path.stem,
                  "task": meta.get("task") or "unknown",
                  "variant": meta.get("variant") or "",
                  "precision": meta.get("precision") or "FP",
                  "source": {"name": meta.get("source_name") or "",
                             "url": meta.get("source_url") or ""},
                  "file": path.name, "size_bytes": None, "sha256": None},
        "board": {"soc": meta.get("soc") or "unknown",
                  "board_label": meta.get("board_label") or "",
                  "os": None, "kernel": None, "soc_model": None,
                  "driver": None, "runtime": None, "loadavg": None},
        "protocol": dict(PROTOCOL),
        "inputs": [], "outputs": [],
        "latency_ms": {"p50": None, "p95": None, "mean": None,
                       "min": None, "max": None},
        "fps_p50": None,
        "verdict": "UNKNOWN",
        "fallback_ops": [], "structural_cpu_ops": [],
        "fallback_share_pct": None,
        "memory": {"file_size_bytes": None, "rss_delta_mb": None,
                   "perf_rw_kb_per_frame": None},
        "notes": [],
    }


def benchmark_model(path: Path, meta: dict, runs: int = 50, warmup: int = 10,
                    backend=None, rss_delta_mb: Optional[float] = None) -> dict:
    report = _empty_report(path, meta)
    report["protocol"]["warmup"] = warmup
    report["protocol"]["runs"] = runs
    notes = report["notes"]
    host = host_info(meta.get("board_label") or "")
    report["board"].update({"os": host["os"], "kernel": host["kernel"],
                            "soc_model": host["soc_model"],
                            "loadavg": host["loadavg"]})
    backend = backend if backend is not None else RknnRuntime()

    data = path.read_bytes()
    report["model"]["size_bytes"] = len(data)
    report["model"]["sha256"] = hashlib.sha256(data).hexdigest()
    report["memory"]["file_size_bytes"] = len(data)
    report["memory"]["rss_delta_mb"] = rss_delta_mb

    ok, reason = backend.available()
    if not ok:
        notes.append("runtime unavailable: " + reason)
        return report
    try:
        backend.load(data)
    except (ModelLoadError, RuntimeUnavailable) as error:
        notes.append("model load failed: " + str(error))
        return report
    try:
        try:
            api_version, drv_version = backend.sdk_version()
            report["board"]["runtime"] = api_version
            report["board"]["driver"] = drv_version
        except ModelLoadError as error:
            notes.append("sdk version query failed: " + str(error))
        input_attrs, output_attrs = backend.io_attrs()
        report["inputs"] = [_public_attr(a) for a in input_attrs]
        report["outputs"] = [_public_attr(a) for a in output_attrs]
        if any(dim <= 0 for a in input_attrs for dim in a["dims"]):
            notes.append("dynamic input shape: not measured under the fixed-input protocol")
            return report
        inputs = backend.make_zero_inputs(input_attrs)
        for _ in range(warmup):
            backend.run_once(inputs)
        samples_us = [backend.run_once(inputs) for _ in range(runs)]
        stats = latency_stats(samples_us)
        report["latency_ms"] = {k: (round(v / 1000.0, 3) if v is not None else None)
                                for k, v in stats.items()}
        if stats["p50"]:
            report["fps_p50"] = round(1000000.0 / stats["p50"], 1)
        detail = parse_perf_detail(backend.perf_detail())
        if not detail["layers"]:
            notes.append("PERF_DETAIL returned no layer rows; fallback cannot be judged")
            return report
        result = judge(detail["layers"],
                       cpu_heavy_pct=THRESHOLDS["cpu_heavy_pct"],
                       npu_only_fallback_pct=THRESHOLDS["npu_only_fallback_pct"],
                       single_op_us=THRESHOLDS["single_op_us"])
        report["verdict"] = result["verdict"]
        report["fallback_ops"] = result["fallback_ops"]
        report["structural_cpu_ops"] = result["structural_cpu_ops"]
        report["fallback_share_pct"] = result["fallback_share_pct"]
        report["memory"]["perf_rw_kb_per_frame"] = detail["rw_kb_per_frame"]
        layers_total = result["layers_total_us"]
        reference = detail["total_us"]
        if reference and abs(layers_total - reference) / reference > 0.10:
            notes.append("layer times sum to %d us but runtime total is %d us (>10%% apart)"
                         % (layers_total, reference))
        if detail["parse_warnings"]:
            notes.append("perf detail: %d layer row(s) could not be parsed"
                         % detail["parse_warnings"])
        return report
    except ModelLoadError as error:
        notes.append("benchmark failed: " + str(error))
        report["verdict"] = "UNKNOWN"
        return report
    finally:
        backend.destroy()


def _public_attr(attr: dict) -> dict:
    return {"name": attr["name"], "dims": attr["dims"],
            "type": attr["type_name"], "fmt": attr["fmt_name"]}


def input_shape_of(report: dict) -> str:
    if report.get("inputs"):
        return "x".join(str(d) for d in report["inputs"][0]["dims"])
    return ""


# --- RSS probe: each cycle is a fresh process so allocator reuse cannot
# hide the model's footprint. The child prints one JSON line. ---

def rss_probe_once(path: Path) -> Optional[float]:
    """In-process probe (also the child's work): RSS delta of load+1 run."""
    before = read_vmrss_kb()
    if before is None:
        return None
    backend = RknnRuntime()
    ok, _ = backend.available()
    if not ok:
        return None
    try:
        data = path.read_bytes()
        backend.load(data)
        attrs, _ = backend.io_attrs()
        if any(dim <= 0 for a in attrs for dim in a["dims"]):
            return None
        inputs = backend.make_zero_inputs(attrs)
        backend.run_once(inputs)
        after = read_vmrss_kb()
        if after is None:
            return None
        return round((after - before) / 1024.0, 1)
    except (ModelLoadError, RuntimeUnavailable, OSError):
        return None
    finally:
        backend.destroy()


def rss_probe_child(path: Path) -> int:
    delta = rss_probe_once(path)
    print(json.dumps({"rss_delta_mb": delta}))
    return 0


def measure_rss_delta(path: Path, cycles: int = 3,
                      runner=None) -> Optional[float]:
    """Median RSS delta over `cycles` fresh child processes."""
    if cycles <= 0:
        return None
    runner = runner or _default_probe_runner
    deltas = []
    for _ in range(cycles):
        value = runner(path)
        if value is not None:
            deltas.append(value)
    if not deltas:
        return None
    return float(statistics.median(deltas))


def _default_probe_runner(path: Path) -> Optional[float]:
    env = dict(os.environ)
    src = str(Path(__file__).resolve().parent.parent)
    env["PYTHONPATH"] = src + os.pathsep + env.get("PYTHONPATH", "")
    try:
        out = subprocess.run([sys.executable, "-m", "rkbench", "_rss_probe",
                              str(path)],
                             capture_output=True, text=True, timeout=300,
                             env=env, check=False)
        payload = json.loads(out.stdout.strip().splitlines()[-1])
        value = payload.get("rss_delta_mb")
        return float(value) if value is not None else None
    except (OSError, subprocess.SubprocessError, ValueError, IndexError):
        return None
