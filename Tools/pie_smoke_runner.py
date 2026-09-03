# -*- coding: utf-8 -*-
"""PIE smoke runner - wraps Monolith's run_pie_smoke, poll_pie_smoke, and capture_pie_movement_clip.

Usage:
    python pie_smoke_runner.py ^
        --map "/Game/EnvSandbox/Environments/L_KaleidoNave" ^
        --duration 10 ^
        --output "C:/Captures" ^
        --console-script WalkLoop BowLoop ^
        --name melusina_walk_smoke
"""
from __future__ import annotations

import argparse
import json
import sys
import time
import urllib.error
import urllib.request
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

MONOLITH_URL = "http://127.0.0.1:9316/mcp"
_RPC_ID = 0


# ---------------------------------------------------------------------------
# Monolith MCP helpers
# ---------------------------------------------------------------------------

def _next_id() -> int:
    global _RPC_ID
    _RPC_ID += 1
    return _RPC_ID


def _post(method: str, params: dict | None = None, *, timeout: float = 120.0) -> dict:
    payload = {"jsonrpc": "2.0", "id": _next_id(), "method": method, "params": params or {}}
    data = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(
        MONOLITH_URL,
        data=data,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        body = resp.read().decode("utf-8")
    return json.loads(body)


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


def editor_query(action: str, **kwargs: Any) -> dict:
    return _call_tool("editor_query", {"action": action, **kwargs})


# ---------------------------------------------------------------------------
# PIE smoke runner
# ---------------------------------------------------------------------------

class PieSmokeRunner:
    """Orchestrates a PIE smoke test session via Monolith MCP."""

    def __init__(
        self,
        map_path: str,
        duration: int = 10,
        output_dir: str | None = None,
        console_script: list[str] | None = None,
        test_name: str | None = None,
        capture_interval: float = 0.25,
        sample_vars: list[str] | None = None,
        pawn_class: str | None = None,
        discard_first_frames: int = 1,
        poll_interval: float = 1.0,
        timeout: int = 300,
    ):
        self.map_path = map_path
        self.duration = duration
        self.output_dir = Path(output_dir) if output_dir else None
        self.console_script = console_script or []
        self.test_name = test_name or f"pie_smoke_{int(time.time())}"
        self.capture_interval = capture_interval
        self.sample_vars = sample_vars or ["GroundSpeed", "bShouldMove", "bIsMoving"]
        self.pawn_class = pawn_class
        self.discard_first_frames = discard_first_frames
        self.poll_interval = poll_interval
        self.timeout = timeout

        self.session_id: str | None = None
        self.captured_frames: list[str] = []
        self.anim_samples: list[dict] = []
        self.log_matches: dict[str, int] = {}
        self.raw_grouped: dict = {}
        self.missing_must_present: list = []
        self.errors: list[str] = []
        self.warnings: list[str] = []
        self.elapsed_seconds: float = 0.0
        self.frames_captured: int = 0

    # ------------------------------------------------------------------
    # Session lifecycle
    # ------------------------------------------------------------------

    def start(self) -> str:
        """Start a PIE smoke session (with capture if output_dir is set)."""
        use_capture = self.output_dir is not None

        if use_capture:
            self.output_dir.mkdir(parents=True, exist_ok=True)
            params = {
                "map": self.map_path,
                "duration": self.duration,
                "sample_vars": self.sample_vars,
                "console_script": self.console_script,
                "capture_interval": self.capture_interval,
                "output_path": str(self.output_dir),
                "discard_first_frames": self.discard_first_frames,
            }
            if self.pawn_class:
                params["pawn_class"] = self.pawn_class
            resp = editor_query("capture_pie_movement_clip", **params)
        else:
            params = {
                "map": self.map_path,
                "duration": self.duration,
                "sample_vars": self.sample_vars,
                "console_script": self.console_script,
            }
            if self.pawn_class:
                params["pawn_class"] = self.pawn_class
            resp = editor_query("run_pie_smoke", **params)

        sid = resp.get("session_id")
        if not sid:
            raise RuntimeError(f"Failed to start PIE smoke session. Response: {resp}")
        self.session_id = sid
        print(f"[PieSmoke] Started session {sid}")
        return sid

    def poll_until_complete(self) -> dict:
        """Poll the session until complete or timeout."""
        if not self.session_id:
            raise RuntimeError("No active session to poll.")

        deadline = time.time() + self.timeout
        last_report: dict = {}

        while time.time() < deadline:
            resp = editor_query("poll_pie_smoke", session_id=self.session_id)
            status = resp.get("status", "")
            lifecycle = resp.get("lifecycle", "")

            if resp.get("sample_count", 0) > 0:
                self._collect_samples(resp)
            if resp.get("captured_frames"):
                self.captured_frames = resp["captured_frames"]
            if resp.get("warnings"):
                self.warnings.extend(resp["warnings"])
            if resp.get("grouped_counts"):
                self._collect_log_matches(resp["grouped_counts"])
                self.raw_grouped = resp["grouped_counts"]
            if resp.get("missing_must_present"):
                self.missing_must_present = resp["missing_must_present"]

            self.elapsed_seconds = resp.get("elapsed_seconds", self.elapsed_seconds)
            self.frames_captured = resp.get("frames_captured", self.frames_captured)

            last_report = resp

            if status == "complete":
                print(f"[PieSmoke] Session complete (lifecycle={lifecycle})")
                return resp
            if status in ("stopped", "error"):
                self.errors.append(f"Session ended with status={status}")
                return resp

            time.sleep(self.poll_interval)

        raise TimeoutError(f"Session {self.session_id} did not complete within {self.timeout}s")

    def stop(self) -> dict:
        """Force-stop the session."""
        if not self.session_id:
            return {}
        resp = editor_query("stop_pie_smoke", session_id=self.session_id)
        print(f"[PieSmoke] Stopped session {self.session_id}")
        return resp

    # ------------------------------------------------------------------
    # Data collection
    # ------------------------------------------------------------------

    def _collect_samples(self, resp: dict) -> None:
        samples = resp.get("samples") or resp.get("timeseries") or []
        for s in samples:
            if isinstance(s, dict) and s not in self.anim_samples:
                self.anim_samples.append(s)

    def _collect_log_matches(self, grouped: dict) -> None:
        for bucket in ("active_runtime", "teardown"):
            bucket_data = grouped.get(bucket)
            if not isinstance(bucket_data, dict):
                continue
            for category in ("must_absent", "must_present", "observe_only", "warn"):
                patterns = bucket_data.get(category)
                if isinstance(patterns, dict):
                    for pattern, count in patterns.items():
                        if isinstance(count, (int, float)):
                            self.log_matches[pattern] = self.log_matches.get(pattern, 0) + int(count)

    # ------------------------------------------------------------------
    # Test report
    # ------------------------------------------------------------------

    def generate_report(self) -> dict:
        """Build the structured test report.

        ok mirrors the Monolith server's rule (MonolithEditorActions.cpp #3):
        every must_absent pattern must have zero hits in the ACTIVE bucket AND
        every must_present pattern must have matched at least once. Teardown-
        bucket must_absent hits never fail ok (server default teardown_allowed).
        Previously ok only reflected session-lifecycle errors, so runs with
        "Blueprint Runtime Error"/"Accessed None" in the active bucket reported
        ok:true - the silent-null-success false positive.
        """
        lifecycle_ok = len(self.errors) == 0

        active = self.raw_grouped.get("active_runtime", {}) if self.raw_grouped else {}
        must_absent_hits: list[tuple[str, int]] = []
        if isinstance(active, dict):
            for pattern, count in (active.get("must_absent") or {}).items():
                if isinstance(count, (int, float)) and count > 0:
                    must_absent_hits.append((pattern, int(count)))
        log_gate_ok = len(must_absent_hits) == 0
        present_ok = len(self.missing_must_present) == 0

        if not self.raw_grouped:
            self.warnings.append(
                "Log gating not applied: server returned no grouped_counts; ok reflects lifecycle errors only."
            )

        ok = lifecycle_ok and log_gate_ok and present_ok
        ok_reason = []
        if not lifecycle_ok:
            ok_reason.append(f"session lifecycle errors: {len(self.errors)}")
        if must_absent_hits:
            ok_reason.append(
                "active must_absent hits: "
                + ", ".join(f"{p} x{c}" for p, c in must_absent_hits)
            )
        if not present_ok:
            ok_reason.append(f"missing must_present: {self.missing_must_present}")

        report = {
            "test_name": self.test_name,
            "session_id": self.session_id,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "ok": ok,
            "ok_reason": "; ".join(ok_reason) or "clean",
            "map": self.map_path,
            "duration": self.duration,
            "captured_frames": self.captured_frames,
            "frame_count": len(self.captured_frames),
            "anim_samples": self.anim_samples,
            "sample_count": len(self.anim_samples),
            "log_matches": self.log_matches,
            "must_absent_hits": dict(must_absent_hits),
            "missing_must_present": self.missing_must_present,
            "console_script": self.console_script,
            "errors": self.errors,
            "warnings": self.warnings,
            "elapsed_seconds": self.elapsed_seconds,
            "frames_captured": self.frames_captured,
        }

        if self.output_dir:
            report["output_dir"] = str(self.output_dir)
            report_path = self.output_dir / f"{self.test_name}_report.json"
        else:
            report_path = Path(f"{self.test_name}_report.json")

        report_path.write_text(json.dumps(report, indent=2, default=str), encoding="utf-8")
        print(f"[PieSmoke] Report written to {report_path}")
        return report

    # ------------------------------------------------------------------
    # Full run
    # ------------------------------------------------------------------

    def run(self) -> dict:
        """Run the full PIE smoke lifecycle: start, poll, report, stop."""
        errors: list[str] = []

        try:
            self.start()
        except Exception as e:
            errors.append(f"Start failed: {e}")
            return self._early_report(errors)

        try:
            self.poll_until_complete()
        except Exception as e:
            errors.append(f"Poll failed: {e}")

        try:
            self.stop()
        except Exception as e:
            errors.append(f"Stop failed: {e}")

        self.errors.extend(errors)
        return self.generate_report()

    def _early_report(self, errors: list[str]) -> dict:
        self.errors = errors
        return self.generate_report()


# ---------------------------------------------------------------------------
# Connectivity test
# ---------------------------------------------------------------------------

def monolith_status() -> dict:
    """Query Monolith server status. Returns raw MCP response envelope."""
    return _post("tools/call", {"name": "monolith_status", "arguments": {}}, timeout=10)


def test_monolith_connectivity(result, mode: str) -> None:
    """Test Monolith MCP connectivity.

    Compatible with regression_suite.py dispatcher (result, mode).
    ``result`` must expose ``assert_ok(label, condition, detail="")``
    and ``fail(detail)`` methods, plus a ``duration_s`` float attribute.
    """
    t0 = time.time()
    try:
        resp = monolith_status()
        content = resp.get("result", {}).get("content") or []
        if content and isinstance(content[0], dict):
            status = json.loads(content[0].get("text", "{}"))
            running = status.get("server_running", False)
            version = status.get("version", "?")
            result.assert_ok("server_running", running, f"v{version}")
        else:
            result.assert_ok("server_running", False, "no content in response")
    except Exception as e:
        result.fail(f"Monolith unreachable: {e}")
    result.duration_s = time.time() - t0


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    p = argparse.ArgumentParser(
        description="Run a PIE smoke test via Monolith MCP.",
    )
    p.add_argument("--map", required=True, help="Map content path, e.g. /Game/...")
    p.add_argument("--duration", type=int, default=10, help="Test duration in seconds (default 10)")
    p.add_argument("--output", help="Output directory for captured frames and report")
    p.add_argument(
        "--console-script",
        nargs="*",
        default=[],
        help="Console commands to drive the player (e.g. WalkLoop BowLoop)",
    )
    p.add_argument("--name", help="Test name for reporting (default auto-generated)")
    p.add_argument("--capture-interval", type=float, default=0.25, help="Frame capture interval (default 0.25)")
    p.add_argument("--pawn-class", help="Pawn class substring for target resolution")
    p.add_argument("--sample-vars", nargs="*", default=["GroundSpeed", "bShouldMove", "bIsMoving"],
                    help="AnimInstance variables to sample per frame")
    p.add_argument("--poll-interval", type=float, default=1.0, help="Poll interval in seconds (default 1.0)")
    p.add_argument("--timeout", type=int, default=300, help="Max wait for completion in seconds (default 300)")
    return p.parse_args(argv)


def main() -> None:
    args = parse_args()
    runner = PieSmokeRunner(
        map_path=args.map,
        duration=args.duration,
        output_dir=args.output,
        console_script=args.console_script,
        test_name=args.name,
        capture_interval=args.capture_interval,
        sample_vars=args.sample_vars,
        pawn_class=args.pawn_class,
        poll_interval=args.poll_interval,
        timeout=args.timeout,
    )
    report = runner.run()

    summary = "OK" if report["ok"] else "FAIL"
    print(f"\n[PieSmoke] {summary}: {report['test_name']}")
    print(f"  Frames: {report['frame_count']}  Samples: {report['sample_count']}  Errors: {len(report['errors'])}")
    if report["errors"]:
        for e in report["errors"]:
            print(f"  Error: {e}")
    sys.exit(0 if report["ok"] else 1)


if __name__ == "__main__":
    main()
