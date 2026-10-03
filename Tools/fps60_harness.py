# -*- coding: utf-8 -*-
"""FPS60 harness — foreground PIE capture + CSV/utrace profiling + stat asserts.

One committed driver for the 60fps floor: runs capture_pie_movement_clip with
csv_profile + trace channels, samples live stat groups, parses the profiling
CSV for frame times, and writes an assertion JSON next to the frames.

Usage:
    python Tools/fps60_harness.py --map "/Game/MelodiaIntegration/Maps/MelodiaIntegrationMap" --name sir_perch_baseline --duration 12
    python Tools/fps60_harness.py --map "/Game/MelodiaIntegration/Maps/MelodiaIntegrationMap" --name sir_perch_perf --duration 12 --performance-only

Evidence contract: frames without the adjacent JSON report are not evidence;
a PASS here is live-proven for this slice only, never packaged proof.
Background/minimized PIE runs at ~3fps and MUST NOT be judged — rerun foreground.
"""
from __future__ import annotations

from mcp_client import post_envelope

import argparse
import csv
import json
import math
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

MONOLITH_URL = "http://127.0.0.1:9316/mcp"
REPO = Path(__file__).resolve().parents[1]
_RPC_ID = 0

FPS_TARGET = 60.0
FRAME_BUDGET_MS = 1000.0 / FPS_TARGET  # 16.6ms p95
STAT_BUDGETS = {  # (group, stat-name substring, max avg ms)
    ("Niagara", "Niagara", 1.0),
}


def _next_id() -> int:
    global _RPC_ID
    _RPC_ID += 1
    return _RPC_ID


def _post(method: str, params: dict | None = None, *, timeout: float = 120.0) -> dict:
    payload = {"jsonrpc": "2.0", "id": _next_id(), "method": method, "params": params or {}}
    data = json.dumps(payload).encode("utf-8")
    return post_envelope(data, timeout=timeout, raise_on_error=True)


def _call_tool(name: str, arguments: dict, *, timeout: float = 120.0) -> dict:
    resp = _post("tools/call", {"name": name, "arguments": arguments}, timeout=timeout)
    if "error" in resp:
        raise RuntimeError(f"Monolith RPC error: {resp['error']}")
    result = resp.get("result", resp)
    content = result.get("content") or []
    if content and isinstance(content[0], dict):
        text = content[0].get("text", "")
        if isinstance(text, str) and text.strip():
            try:
                parsed = json.loads(text)
                return parsed if isinstance(parsed, dict) else {"result": parsed}
            except json.JSONDecodeError:
                pass
    return result


def editor_query(action: str, **kwargs) -> dict:
    return _call_tool("editor_query", {"action": action, **kwargs})


def parse_frame_times(csv_path: Path) -> list[float]:
    """UE csv-profiler layout: row = sample, col 0 = event tag, 'FrameTime' col = ms."""
    times: list[float] = []
    with open(csv_path, "r", encoding="utf-8", errors="replace") as f:
        reader = csv.reader(f)
        try:
            hdr = next(reader)
        except StopIteration:
            return []
        try:
            idx = hdr.index("FrameTime")
        except ValueError:
            return []
        for row in reader:
            if idx >= len(row):
                continue
            try:
                v = float(row[idx])
                if math.isfinite(v) and 0.01 < v < 10000:
                    times.append(v)
            except (ValueError, TypeError):
                continue
    # Drop warmup samples (async-load hitches at PIE start).
    return times[3:] if len(times) > 4 else times


def percentile(xs: list[float], q: float) -> float:
    if not xs:
        return 0.0
    s = sorted(xs)
    i = min(len(s) - 1, int(q * len(s)))
    return s[i]


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--map", required=True)
    ap.add_argument("--name", required=True)
    ap.add_argument("--duration", type=int, default=12)
    ap.add_argument("--capture-interval", type=float, default=0.25)
    ap.add_argument("--performance-only", action="store_true",
                    help="Use run_pie_smoke without viewport PNG capture/readbacks.")
    args = ap.parse_args()

    stamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    outdir = REPO / "Saved" / "Audit" / f"fps60_{args.name}_{stamp}"
    outdir.mkdir(parents=True, exist_ok=True)
    report: dict = {
        "harness": "Tools/fps60_harness.py",
        "map": args.map,
        "name": args.name,
        "fps_target": FPS_TARGET,
        "frame_budget_ms_p95": FRAME_BUDGET_MS,
        "foreground_note": "judge foreground PIE only; background/minimized PIE ~3fps is invalid",
        "mode": "performance_only" if args.performance_only else "capture_and_profile",
        "png_capture": not args.performance_only,
        "timing_scope": ("PIE runtime without viewport PNG capture/readbacks" if args.performance_only
                         else "PIE runtime including periodic viewport PNG capture/readbacks"),
        "assertions": {},
    }

    # 0. Precondition: no errored blueprints.
    err = editor_query("list_errored_blueprints")
    report["errored_blueprints"] = err.get("count", -1)
    report["assertions"]["zero_errored_blueprints"] = err.get("count", -1) == 0

    # 1. Capture + profile.
    capture_action = "run_pie_smoke" if args.performance_only else "capture_pie_movement_clip"
    capture_params = {
        "map": args.map,
        "duration": args.duration,
        "csv_profile": True,
        "trace_channels": ["cpu", "frame"],
    }
    if not args.performance_only:
        capture_params.update({
            "capture_interval": args.capture_interval,
            "output_path": str(outdir),
            "discard_first_frames": 1,
        })
    start = editor_query(capture_action, **capture_params)
    session_id = start.get("session_id")
    report["capture_start"] = {k: start.get(k) for k in ("status", "started", "session_id", "error")}
    # Enable live stat collection while PIE is up (required for settled reads).
    try:
        editor_query("run_console_command", command="stat Niagara")
    except Exception:  # noqa: BLE001 — recorded below if stats stay unsettled
        pass
    deadline = time.time() + args.duration + 180
    final: dict = {}
    poll_error: str | None = None
    mid_stats: dict | None = None
    mid_sampled = False
    t0 = time.time()
    while session_id and time.time() < deadline:
        time.sleep(5)
        try:
            final = editor_query("poll_pie_smoke", session_id=session_id, include_samples=True)
        except Exception as e:  # noqa: BLE001 — preserve a failed receipt on poll errors
            poll_error = str(e)[:500]
            break
        # Sample stat groups mid-run while the PIE stream is alive.
        if not mid_sampled and (time.time() - t0) > args.duration / 2 and final.get("pie_active", True):
            try:
                mid_stats = editor_query("get_stat_group_values", group_name="Niagara", sample_frames=24)
            except Exception as e:  # noqa: BLE001
                mid_stats = {"error": str(e)[:200]}
            mid_sampled = True
        if final.get("status") in ("complete", "completed", "done", "stopped", "error"):
            break
    terminal_statuses = ("complete", "completed", "done", "stopped", "error")
    if not session_id:
        poll_error = "capture start returned no session_id"
        final = {"status": start.get("status", "error"),
                 "error": start.get("error") or poll_error, "ok": False}
    elif final.get("status") not in terminal_statuses and not poll_error:
        poll_error = "poll deadline expired before a final session report"
    if poll_error:
        report["poll_error"] = poll_error
    report["pie"] = {k: final.get(k) for k in ("status", "elapsed_seconds", "sample_count", "frames_captured", "capture_validity", "post_marker_counts")}
    report["pie"]["ok"] = final.get("ok")
    report["pie"]["error"] = final.get("error")
    validity = (final.get("capture_validity") or {}) if isinstance(final, dict) else {}
    terminal_status = final.get("status")
    completed = terminal_status in ("complete", "completed", "done")
    report["assertions"]["capture_completed_without_error"] = bool(
        completed and final.get("ok") is True and not final.get("error") and not poll_error
    )
    report["assertions"]["pie_samples_positive"] = (final.get("sample_count") or 0) > 0
    if not args.performance_only:
        report["assertions"]["frames_captured_positive"] = (validity.get("valid_frames") or 0) > 0
        report["assertions"]["capture_frames_valid"] = (
            validity.get("captured_ok") is True
            and (validity.get("invalid_frames") or 0) == 0
        )

    # 2. Stat groups (mid-run read preferred; unsettled is recorded, not hidden).
    stat_checks = []
    for group, substr, budget in STAT_BUDGETS:
        try:
            g = mid_stats if (mid_stats and group == "Niagara") else editor_query("get_stat_group_values", group_name=group, sample_frames=60)
            stats = g.get("stats", []) if isinstance(g, dict) else []
            hit = [s for s in stats if isinstance(s, dict) and s.get("kind") == "cycle"
                   and substr.lower() in str(s.get("name", "")).lower()]
            vals = [h.get("avg", h.get("value", 0)) for h in hit]
            worst = max(vals) if vals else None
            stat_checks.append({"group": group, "settled": g.get("settled"), "worst_avg_ms": worst,
                                "budget_ms": budget, "pass": bool(g.get("settled")) and worst is not None and worst <= budget})
        except Exception as e:  # noqa: BLE001 — record, don't hide
            stat_checks.append({"group": group, "error": str(e)[:200], "pass": False})
    report["stat_checks"] = stat_checks
    report["assertions"]["stat_budgets"] = all(s.get("pass") for s in stat_checks) if stat_checks else False

    # 3. Read the artifact path returned by this session. Never select another
    # session's newest global CSV, which can silently misattribute timings.
    profiling = final.get("profiling") if isinstance(final.get("profiling"), dict) else {}
    csv_info = profiling.get("csv") if isinstance(profiling.get("csv"), dict) else {}
    csv_raw_path = profiling.get("csv_path") or csv_info.get("csv_path")
    csv_path = Path(csv_raw_path) if csv_raw_path else None
    if csv_path and not csv_path.is_absolute():
        csv_path = REPO / csv_path
    times: list[float] = []
    if csv_path:
        for _ in range(12):
            try:
                times = parse_frame_times(csv_path)
                if times:
                    break
            except (FileNotFoundError, PermissionError):
                time.sleep(5)
    report["csv_path"] = str(csv_path) if csv_path else None
    report["csv_frame_count"] = len(times)
    report["csv_profile"] = {
        "available": csv_info.get("available"),
        "capturing": csv_info.get("capturing"),
        "status": csv_info.get("status"),
    }
    report["assertions"]["csv_samples_usable"] = bool(
        csv_path and csv_info.get("available") is True
        and csv_info.get("capturing") is False and len(times) >= 5
    )
    if times:
        report["csv"] = {"min_ms": min(times), "p50_ms": percentile(times, 0.5),
                         "p95_ms": percentile(times, 0.95), "max_ms": max(times),
                         "derived_fps_p50": 1000.0 / percentile(times, 0.5) if percentile(times, 0.5) else 0}
        report["assertions"]["p95_within_60fps_budget"] = (
            report["assertions"]["csv_samples_usable"]
            and percentile(times, 0.95) <= FRAME_BUDGET_MS
        )
    else:
        report["assertions"]["p95_within_60fps_budget"] = False

    report["pass"] = all(report["assertions"].values())
    (outdir / "fps60_report.json").write_text(json.dumps(report, indent=1), encoding="utf-8")
    print(json.dumps(report, indent=1))
    return 0 if report["pass"] else 1


if __name__ == "__main__":
    sys.exit(main())
