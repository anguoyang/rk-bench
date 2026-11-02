"""rk-bench tests. Runnable with both pytest and stdlib unittest."""

import json
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from rkbench.bench import benchmark_model  # noqa: E402
from rkbench.cli import main  # noqa: E402
from rkbench.leaderboard import (LeaderboardError, add_entry,  # noqa: E402
                                 empty_leaderboard, entry_from_report,
                                 render_table, update_readme)
from rkbench.perf_parse import judge, latency_stats, parse_perf_detail  # noqa: E402

FIXTURE = Path(__file__).resolve().parent / "fixtures" / "perf_detail_yolov8n.txt"


def layer(op, target, time_us, rw=0):
    return {"id": 0, "op_type": op, "data_type": "FLOAT16", "target": target,
            "time_us": time_us, "rw_kb": rw, "full_name": op + ":x"}


class PerfParseTests(unittest.TestCase):
    def test_real_capture(self):
        detail = parse_perf_detail(FIXTURE.read_text(encoding="utf-8"))
        self.assertEqual(len(detail["layers"]), 108)
        self.assertEqual(detail["total_us"], 38199)
        self.assertEqual(sum(l["time_us"] for l in detail["layers"]), 38199)
        self.assertEqual(detail["ranking"][0]["op_type"], "ConvExSwish")
        self.assertEqual(detail["ranking"][0]["total_us"], 29047)
        self.assertEqual(detail["rw_kb_per_frame"], 74336)
        result = judge(detail["layers"])
        self.assertEqual(result["verdict"], "NPU_ONLY")
        self.assertEqual(result["fallback_ops"], [])
        self.assertEqual(len(result["structural_cpu_ops"]), 10)

    def test_empty_text(self):
        detail = parse_perf_detail("")
        self.assertEqual(detail["layers"], [])
        self.assertIsNone(detail["rw_kb_per_frame"])


class JudgeTests(unittest.TestCase):
    def test_three_verdicts(self):
        base = [layer("InputOperator", "CPU", 10), layer("Conv", "NPU", 10000)]
        self.assertEqual(judge(base)["verdict"], "NPU_ONLY")
        mixed = base + [layer("Odd", "CPU", 500)]
        self.assertEqual(judge(mixed)["verdict"], "MIXED")
        heavy = base + [layer("Odd", "CPU", 9000)]
        self.assertEqual(judge(heavy)["verdict"], "CPU_HEAVY")

    def test_single_big_op_is_mixed(self):
        layers = [layer("Conv", "NPU", 100000), layer("Odd", "CPU", 150)]
        self.assertEqual(judge(layers)["verdict"], "MIXED")

    def test_latency_stats(self):
        stats = latency_stats([100, 200, 300, 400])
        self.assertEqual(stats["p50"], 200)
        self.assertEqual(stats["p95"], 400)
        self.assertEqual(stats["mean"], 250.0)
        self.assertIsNone(latency_stats([])["p50"])


class FakeBackend:
    lib_path = "/fake/librknnrt.so"

    def available(self):
        return True, ""

    def load(self, data):
        self.data = data

    def sdk_version(self):
        return "2.3.2", "0.9.8"

    def io_attrs(self):
        attr = {"index": 0, "name": "images", "dims": [1, 3, 640, 640],
                "type": 2, "type_name": "FLOAT16", "fmt": 0,
                "fmt_name": "NCHW", "n_elems": 1228800, "size": 2457600}
        out = dict(attr, name="out", dims=[1, 84, 8400])
        return [attr], [out]

    def make_zero_inputs(self, attrs):
        return (attrs, len(attrs))

    def run_once(self, inputs):
        return 41000

    def perf_detail(self):
        return FIXTURE.read_text(encoding="utf-8")

    def destroy(self):
        pass


class BenchTests(unittest.TestCase):
    def test_benchmark_with_fake_backend(self):
        with tempfile.TemporaryDirectory() as tmp:
            model = Path(tmp) / "yolov8n.rknn"
            model.write_bytes(b"fake-model-bytes")
            meta = {"name": "YOLOv8n", "task": "detect", "soc": "rk3588",
                    "board_label": "rk3588", "precision": "FP",
                    "source_name": "RKNN Model Zoo", "source_url": "https://example.invalid/zoo"}
            report = benchmark_model(model, meta, runs=5, warmup=2,
                                     backend=FakeBackend(), rss_delta_mb=42.0)
        self.assertEqual(report["verdict"], "NPU_ONLY")
        self.assertEqual(report["latency_ms"]["p50"], 41.0)
        self.assertEqual(report["fps_p50"], 24.4)
        self.assertEqual(report["board"]["runtime"], "2.3.2")
        self.assertEqual(report["memory"]["perf_rw_kb_per_frame"], 74336)
        self.assertEqual(report["memory"]["rss_delta_mb"], 42.0)
        self.assertEqual(len(report["model"]["sha256"]), 64)

    def test_unknown_without_runtime(self):
        import os
        old = os.environ.get("RKBENCH_RKNNRT")
        os.environ["RKBENCH_RKNNRT"] = "/nonexistent/librknnrt.so"
        try:
            with tempfile.TemporaryDirectory() as tmp:
                model = Path(tmp) / "x.rknn"
                model.write_bytes(b"nope")
                report = benchmark_model(model, {"name": "X", "task": "detect"})
        finally:
            if old is None:
                os.environ.pop("RKBENCH_RKNNRT", None)
            else:
                os.environ["RKBENCH_RKNNRT"] = old
        self.assertEqual(report["verdict"], "UNKNOWN")
        self.assertTrue(report["notes"])


def sample_report(**board_override):
    board = {"soc": "rk3588", "board_label": "rk3588", "os": "Ubuntu 22.04",
             "kernel": "6.1.118", "soc_model": "Rockchip RK3588",
             "driver": "0.9.8", "runtime": "2.3.2", "loadavg": [16.0, 16.0, 16.0]}
    board.update(board_override)
    return {
        "schema": 1, "kind": "bench", "tool_version": "0.1.0",
        "generated_at": "2026-11-02T00:00:00+00:00",
        "model": {"display_name": "YOLOv8n", "task": "detect", "variant": "",
                  "precision": "FP", "source": {"name": "zoo", "url": ""},
                  "file": "yolov8n.rknn", "size_bytes": 6400000,
                  "sha256": "a" * 64},
        "board": board, "protocol": {"warmup": 10, "runs": 50},
        "inputs": [{"name": "images", "dims": [1, 3, 640, 640],
                    "type": "FLOAT16", "fmt": "NCHW"}],
        "latency_ms": {"p50": 41.0, "p95": 42.0, "mean": 41.2,
                       "min": 40.0, "max": 43.0},
        "fps_p50": 24.4, "verdict": "NPU_ONLY", "fallback_ops": [],
        "fallback_share_pct": 0.0,
        "memory": {"file_size_bytes": 6400000, "rss_delta_mb": 30.0,
                   "perf_rw_kb_per_frame": 74336},
        "notes": [],
    }


class LeaderboardTests(unittest.TestCase):
    def test_add_and_replace(self):
        entry = entry_from_report(sample_report())
        data = empty_leaderboard(entry["board"])
        add_entry(data, entry)
        self.assertEqual(len(data["entries"]), 1)
        newer = entry_from_report(sample_report())
        newer["latency_ms"]["p50"] = 39.0
        add_entry(data, newer)
        self.assertEqual(len(data["entries"]), 1)
        self.assertEqual(data["entries"][0]["latency_ms"]["p50"], 39.0)

    def test_env_mismatch_rejected(self):
        entry = entry_from_report(sample_report())
        data = empty_leaderboard(entry["board"])
        bad = entry_from_report(sample_report(runtime="9.9.9"))
        bad["model"] = "Other"
        with self.assertRaises(LeaderboardError):
            add_entry(data, bad)

    def test_render_and_readme(self):
        entry = entry_from_report(sample_report())
        data = empty_leaderboard(entry["board"])
        add_entry(data, entry)
        table = render_table(data)
        self.assertIn("YOLOv8n", table)
        self.assertIn("41", table)
        with tempfile.TemporaryDirectory() as tmp:
            readme = Path(tmp) / "README.md"
            readme.write_text("head\n<!-- LEADERBOARD:BEGIN -->\nold\n"
                              "<!-- LEADERBOARD:END -->\ntail\n", encoding="utf-8")
            update_readme(readme, data)
            text = readme.read_text(encoding="utf-8")
            self.assertIn("YOLOv8n", text)
            self.assertNotIn("\nold\n", text)


class CliTests(unittest.TestCase):
    def test_prime_child_without_runtime(self):
        with tempfile.TemporaryDirectory() as tmp:
            model = Path(tmp) / "x.rknn"
            model.write_bytes(b"nope")
            self.assertEqual(main(["_prime", str(model)]), 0)
            self.assertEqual(main(["_prime", str(Path(tmp) / "nope.rknn")]), 2)

    def test_missing_model_exit_2(self):
        with tempfile.TemporaryDirectory() as tmp:
            code = main(["run", str(Path(tmp) / "nope.rknn"),
                         "--json", str(Path(tmp) / "r.json"), "--rss-cycles", "0"])
            self.assertEqual(code, 2)

    def test_run_add_table_roundtrip(self):
        import os
        old = os.environ.get("RKBENCH_RKNNRT")
        os.environ["RKBENCH_RKNNRT"] = "/nonexistent/librknnrt.so"
        try:
            with tempfile.TemporaryDirectory() as tmp:
                tmp = Path(tmp)
                model = tmp / "x.rknn"
                model.write_bytes(b"nope")
                report = tmp / "r.json"
                self.assertEqual(main(["run", str(model), "--name", "X",
                                       "--task", "detect", "--soc", "rk3588",
                                       "--json", str(report),
                                       "--rss-cycles", "0"]), 0)
                payload = json.loads(report.read_text(encoding="utf-8"))
                self.assertEqual(payload["verdict"], "UNKNOWN")
                board = tmp / "leaderboard.json"
                self.assertEqual(main(["add", str(report), "--into", str(board)]), 0)
                out = tmp / "LEADERBOARD.md"
                self.assertEqual(main(["table", "--from", str(board),
                                       "--out", str(out)]), 0)
                self.assertIn("UNKNOWN", out.read_text(encoding="utf-8"))
        finally:
            if old is None:
                os.environ.pop("RKBENCH_RKNNRT", None)
            else:
                os.environ["RKBENCH_RKNNRT"] = old


if __name__ == "__main__":
    unittest.main()
