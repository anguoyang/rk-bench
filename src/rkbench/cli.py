"""rkbench command line: run / add / table."""

import argparse
import json
import sys
from pathlib import Path

from . import __version__
from .bench import (PROTOCOL, aggregate_reports, benchmark_model,
                    measure_rss_delta, prime, prime_child, rss_probe_child,
                    spawn_child)
from .leaderboard import (LeaderboardError, add_entry, empty_leaderboard,
                          entry_from_report, load_leaderboard,
                          render_leaderboard_md, save_leaderboard,
                          update_readme)


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(
        prog="rkbench",
        description="Measured RKNN model benchmarks for Rockchip boards.")
    parser.add_argument("--version", action="version",
                        version="rkbench %s" % __version__)
    sub = parser.add_subparsers(dest="command")

    run_p = sub.add_parser("run", help="benchmark one .rknn model")
    run_p.add_argument("model")
    run_p.add_argument("--name", default="", help="display name, e.g. YOLOv8n")
    run_p.add_argument("--task", default="unknown",
                       help="detect / classify / segment / pose / face-detect / ...")
    run_p.add_argument("--variant", default="")
    run_p.add_argument("--precision", default="FP")
    run_p.add_argument("--soc", default="", help="e.g. rk3588")
    run_p.add_argument("--board-label", default="")
    run_p.add_argument("--source-name", default="")
    run_p.add_argument("--source-url", default="")
    run_p.add_argument("--runs", type=int, default=PROTOCOL["runs"])
    run_p.add_argument("--warmup", type=int, default=PROTOCOL["warmup"])
    run_p.add_argument("--rss-cycles", type=int, default=PROTOCOL["rss_cycles"],
                       help="fresh probe processes for the RSS delta (0 skips it)")
    run_p.add_argument("--no-prime", action="store_true",
                       help="skip the priming cycle (first process after idle "
                            "measures ~15%% slower on RK3588; see README)")
    run_p.add_argument("--sessions", type=int, default=PROTOCOL["sessions"],
                       help="independent sessions (separate processes) whose "
                            "p50/p95 are aggregated by median; 1 = single session")
    run_p.add_argument("--json", required=True, help="output report path")

    add_p = sub.add_parser("add", help="add a bench report to a leaderboard")
    add_p.add_argument("report")
    add_p.add_argument("--into", required=True, help="leaderboard.json path")

    table_p = sub.add_parser("table", help="render tables from a leaderboard")
    table_p.add_argument("--from", dest="source", required=True)
    table_p.add_argument("--out", default="", help="write docs/LEADERBOARD.md here")
    table_p.add_argument("--readme", default="", help="also refresh this README")

    probe_p = sub.add_parser("_rss_probe", help=argparse.SUPPRESS)
    probe_p.add_argument("model")

    prime_p = sub.add_parser("_prime", help=argparse.SUPPRESS)
    prime_p.add_argument("model")

    sess_p = sub.add_parser("_session", help=argparse.SUPPRESS)
    sess_p.add_argument("model")
    sess_p.add_argument("--name", default="")
    sess_p.add_argument("--task", default="unknown")
    sess_p.add_argument("--variant", default="")
    sess_p.add_argument("--precision", default="FP")
    sess_p.add_argument("--soc", default="")
    sess_p.add_argument("--board-label", default="")
    sess_p.add_argument("--source-name", default="")
    sess_p.add_argument("--source-url", default="")
    sess_p.add_argument("--runs", type=int, default=PROTOCOL["runs"])
    sess_p.add_argument("--warmup", type=int, default=PROTOCOL["warmup"])
    sess_p.add_argument("--json", required=True)

    args = parser.parse_args(argv)
    if args.command == "run":
        return _cmd_run(args)
    if args.command == "add":
        return _cmd_add(args)
    if args.command == "table":
        return _cmd_table(args)
    if args.command == "_rss_probe":
        path = Path(args.model)
        if not path.is_file():
            return 2
        return rss_probe_child(path)
    if args.command == "_prime":
        path = Path(args.model)
        if not path.is_file():
            return 2
        return prime_child(path)
    if args.command == "_session":
        path = Path(args.model)
        if not path.is_file():
            return 2
        meta = {"name": args.name, "task": args.task, "variant": args.variant,
                "precision": args.precision, "soc": args.soc,
                "board_label": args.board_label or args.soc,
                "source_name": args.source_name, "source_url": args.source_url}
        report = benchmark_model(path, meta, runs=args.runs,
                                 warmup=args.warmup)
        Path(args.json).write_text(
            json.dumps(report, indent=2, ensure_ascii=False) + "\n",
            encoding="utf-8")
        return 0
    parser.print_help()
    return 2


def _cmd_run(args) -> int:
    path = Path(args.model)
    if not path.is_file():
        print("rkbench: model file not found: %s" % path, file=sys.stderr)
        return 2
    primed = False
    if not args.no_prime:
        primed = prime(path)
    rss_delta = measure_rss_delta(path, cycles=args.rss_cycles)
    meta = {"name": args.name, "task": args.task, "variant": args.variant,
            "precision": args.precision, "soc": args.soc,
            "board_label": args.board_label or args.soc,
            "source_name": args.source_name, "source_url": args.source_url}
    if args.sessions and args.sessions > 1:
        report = _run_sessions(path, meta, args, rss_delta)
        if report is None:
            print("rkbench: session runs failed", file=sys.stderr)
            return 1
    else:
        report = benchmark_model(path, meta, runs=args.runs,
                                 warmup=args.warmup, rss_delta_mb=rss_delta)
        report["protocol"]["sessions"] = 1
        report["protocol"]["aggregation"] = "single session (no aggregation)"
    if args.no_prime:
        report["protocol"]["priming"] = "skipped (--no-prime)"
        report["notes"].append(
            "priming skipped: on RK3588 the first process after idle can "
            "measure ~15% slower; this report may reflect that state")
    out = Path(args.json)
    out.write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n",
                   encoding="utf-8")
    latency = report["latency_ms"]
    print("%s (%s) on %s: %s" % (report["model"]["display_name"],
                                 report["model"]["task"],
                                 report["board"]["soc"], report["verdict"]))
    if latency["p50"] is not None:
        print("p50 %.2f ms · p95 %.2f ms · %.1f FPS · fallback %s%% · RSS Δ %s MB"
              % (latency["p50"], latency["p95"], report["fps_p50"] or 0,
                 report["fallback_share_pct"], report["memory"]["rss_delta_mb"]))
    for note in report["notes"]:
        print("note: %s" % note)
    print("Report: %s" % out)
    return 0


def _run_sessions(path, meta, args, rss_delta):
    import tempfile
    reports = []
    with tempfile.TemporaryDirectory() as tmp:
        for i in range(args.sessions):
            out = Path(tmp) / ("session%d.json" % i)
            argv = ["_session", str(path),
                    "--name", meta["name"], "--task", meta["task"],
                    "--variant", meta["variant"],
                    "--precision", meta["precision"], "--soc", meta["soc"],
                    "--board-label", meta["board_label"],
                    "--source-name", meta["source_name"],
                    "--source-url", meta["source_url"],
                    "--runs", str(args.runs), "--warmup", str(args.warmup),
                    "--json", str(out)]
            if not spawn_child(argv) or not out.is_file():
                return None
            reports.append(json.loads(out.read_text(encoding="utf-8")))
    return aggregate_reports(reports, rss_delta_mb=rss_delta)


def _cmd_add(args) -> int:
    report_path = Path(args.report)
    if not report_path.is_file():
        print("rkbench: report not found: %s" % report_path, file=sys.stderr)
        return 2
    try:
        report = json.loads(report_path.read_text(encoding="utf-8"))
    except ValueError as error:
        print("rkbench: invalid report JSON: %s" % error, file=sys.stderr)
        return 2
    if report.get("kind") != "bench" or report.get("schema") != 1:
        print("rkbench: %s is not a schema-1 rkbench report" % report_path,
              file=sys.stderr)
        return 2
    entry = entry_from_report(report)
    into = Path(args.into)
    try:
        if into.is_file():
            data = load_leaderboard(into)
        else:
            data = empty_leaderboard(entry["board"])
        add_entry(data, entry)
    except LeaderboardError as error:
        print("rkbench: %s" % error, file=sys.stderr)
        return 1
    save_leaderboard(into, data)
    print("Added %s (%s, %s) to %s — %d entries"
          % (entry["model"], entry["task"], entry["verdict"], into,
             len(data["entries"])))
    return 0


def _cmd_table(args) -> int:
    source = Path(args.source)
    if not source.is_file():
        print("rkbench: leaderboard not found: %s" % source, file=sys.stderr)
        return 2
    try:
        data = load_leaderboard(source)
        if args.out:
            Path(args.out).write_text(render_leaderboard_md(data),
                                      encoding="utf-8")
            print("Wrote %s" % args.out)
        if args.readme:
            update_readme(Path(args.readme), data)
            print("Updated %s" % args.readme)
    except LeaderboardError as error:
        print("rkbench: %s" % error, file=sys.stderr)
        return 1
    if not args.out and not args.readme:
        print(render_leaderboard_md(data))
    return 0
