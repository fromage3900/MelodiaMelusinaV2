# -*- coding: utf-8 -*-
"""
Melodia Gameplay Loop - Automated Regression Test Suite (UE 5.8).

Validates the full Melodia gameplay pipeline via Monolith MCP on localhost:9316,
using the existing pie_smoke_runner and bp_regression_checker internals.

Modes:
    --quick   ~5 min  (subset, short PIE durations, 1 capture frame)
    --full    ~2+ hr  (all tests, extended PIE, high-res captures, full polls)

Usage:
    python Tools/regression_suite.py --quick
    python Tools/regression_suite.py --full
"""
from __future__ import annotations

import argparse
import base64
import json
import os
import re
import sys
import time
import urllib.error
import urllib.request
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------
TOOLS_DIR = Path(__file__).resolve().parent
PROJECT_DIR = TOOLS_DIR.parent
SAVED_DIR = PROJECT_DIR / "Saved"
REPORT_DIR = SAVED_DIR / "RegressionReports"
SCREENSHOT_DIR = SAVED_DIR / "RegressionScreenshots"
REPORT_DIR.mkdir(parents=True, exist_ok=True)
SCREENSHOT_DIR.mkdir(parents=True, exist_ok=True)

# ---------------------------------------------------------------------------
# Monolith MCP client (compatible w/ pie_smoke_runner & bp_regression_checker)
# ---------------------------------------------------------------------------
MONOLITH_URL = "http://127.0.0.1:9316/mcp"
MONOLITH_URL_RAW = "http://localhost:9316"
_RPC_ID = 0


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


def blueprint_query(action: str, **kwargs: Any) -> dict:
    return _call_tool("blueprint_query", {"action": action, **kwargs})


def project_query(action: str, **kwargs: Any) -> dict:
    return _call_tool("project_query", {"action": action, **kwargs})


def monolith_status() -> dict:
    resp = _post("tools/call", {"name": "monolith_status", "arguments": {}}, timeout=10)
    return resp


def fetch_fingerprint(asset_path: str, mode: str = "topology") -> dict | None:
    payload = json.dumps({"action": "get_graph_fingerprint", "asset_path": asset_path, "mode": mode}).encode()
    req = urllib.request.Request(
        MONOLITH_URL_RAW,
        data=payload,
        headers={"Content-Type": "application/json"},
    )
    try:
        with urllib.request.urlopen(req, timeout=15) as resp:
            return json.loads(resp.read().decode())
    except (urllib.error.URLError, json.JSONDecodeError):
        return None


# ---------------------------------------------------------------------------
# Test result record
# ---------------------------------------------------------------------------
class TestResult:
    def __init__(self, name: str):
        self.name = name
        self.passed: bool | None = None
        self.detail: str = ""
        self.duration_s: float = 0.0
        self.screenshot_path: str | None = None
        self.assertions: list[dict] = []

    def fail(self, detail: str) -> None:
        self.passed = False
        self.detail = (self.detail + "; " if self.detail else "") + detail

    def ok(self, detail: str = "") -> None:
        self.passed = True
        self.detail = detail or "OK"

    def assert_ok(self, label: str, condition: bool, detail: str = "") -> None:
        self.assertions.append({"label": label, "passed": condition, "detail": detail})
        if not condition:
            self.fail(f"{label}: {detail}" if detail else label)

    @property
    def status_text(self) -> str:
        if self.passed is None:
            return "SKIP"
        return "PASS" if self.passed else "FAIL"


# ---------------------------------------------------------------------------
# PIE smoke helpers (wraps PieSmokeRunner inline)
# ---------------------------------------------------------------------------
def run_pie_smoke_simple(
    map_path: str,
    duration: int = 10,
    output_dir: str | None = None,
    console_script: list[str] | None = None,
    test_name: str | None = None,
    capture_interval: float = 0.25,
    timeout: int = 120,
) -> dict:
    """Start, poll, and stop a PIE smoke session, returning the report dict."""
    errors: list[str] = []
    session_id: str | None = None
    captured_frames: list[str] = []
    log_matches: dict[str, int] = {}
    must_absent_hits: dict[str, int] = {}
    missing_must_present: list = []
    warnings: list[str] = []
    anim_samples: list[dict] = []

    use_capture = output_dir is not None
    if use_capture:
        Path(output_dir).mkdir(parents=True, exist_ok=True)

    # Start
    try:
        params: dict = {
            "map": map_path,
            "duration": duration,
            "console_script": console_script or [],
        }
        if use_capture:
            params["output_path"] = output_dir
            params["capture_interval"] = capture_interval
            resp = editor_query("capture_pie_movement_clip", **params)
        else:
            resp = editor_query("run_pie_smoke", **params)

        sid = resp.get("session_id")
        if not sid:
            raise RuntimeError(f"No session_id in response: {resp}")
        session_id = sid
    except Exception as e:
        errors.append(f"Start failed: {e}")
        return {"ok": False, "errors": errors, "session_id": None, "captured_frames": [], "log_matches": {}}

    # Poll
    deadline = time.time() + max(timeout, duration + 30)
    try:
        while time.time() < deadline:
            resp = editor_query("poll_pie_smoke", session_id=session_id)
            if isinstance(resp, dict) and "result" in resp and isinstance(resp["result"], dict):
                resp = resp["result"]
            status = resp.get("status", "")
            if isinstance(status, int):
                st_map = {0: "running", 1: "complete", 2: "stopped", -1: "error"}
                status = st_map.get(status, str(status))
            if resp.get("captured_frames"):
                captured_frames = resp["captured_frames"]
            if resp.get("warnings"):
                warnings.extend(resp["warnings"])
            if resp.get("grouped_counts"):
                for bucket in ("active_runtime", "teardown"):
                    bucket_data = resp["grouped_counts"].get(bucket, {})
                    if not isinstance(bucket_data, dict):
                        continue
                    for category in ("must_absent", "must_present", "observe_only", "warn"):
                        patterns = bucket_data.get(category)
                        if isinstance(patterns, dict):
                            for p, c in patterns.items():
                                if isinstance(c, (int, float)):
                                    log_matches[p] = log_matches.get(p, 0) + int(c)
                active = resp["grouped_counts"].get("active_runtime", {})
                if isinstance(active, dict):
                    for p, c in (active.get("must_absent") or {}).items():
                        if isinstance(c, (int, float)) and c > 0:
                            must_absent_hits[p] = int(c)
            if resp.get("missing_must_present"):
                missing_must_present = resp["missing_must_present"]
            samples = resp.get("samples") or resp.get("timeseries") or []
            for s in samples:
                if isinstance(s, dict) and s not in anim_samples:
                    anim_samples.append(s)

            if status == "complete":
                break
            if status in ("stopped", "error"):
                errors.append(f"Session ended status={status}, lifecycle={resp.get('lifecycle','')}")
                break
            time.sleep(1.0)
    except Exception as e:
        errors.append(f"Poll failed: {e}")

    # Stop
    try:
        editor_query("stop_pie_smoke", session_id=session_id)
    except Exception as e:
        errors.append(f"Stop failed: {e}")

    return {
        "ok": len(errors) == 0 and not must_absent_hits and not missing_must_present,
        "errors": errors,
        "session_id": session_id,
        "captured_frames": captured_frames,
        "log_matches": log_matches,
        "must_absent_hits": must_absent_hits,
        "missing_must_present": missing_must_present,
        "warnings": warnings,
        "anim_samples": anim_samples,
    }


# ---------------------------------------------------------------------------
# Test definitions
# ---------------------------------------------------------------------------

def test_monolith_connectivity(result: TestResult, mode: str) -> None:
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


def test_pie_melusina_morning(result: TestResult, mode: str) -> None:
    """Start PIE on L_MelusinaMorning, walk forward 5s (quick) or 30s (full), capture frames."""
    t0 = time.time()
    duration = 30 if mode == "full" else 5
    map_path = "/Game/Melodia/Levels/Opening/L_MelusinaMorning"
    test_tag = f"melusina_morning_{mode}"

    output_dir = str(SCREENSHOT_DIR / test_tag)
    report = run_pie_smoke_simple(
        map_path=map_path,
        duration=duration,
        output_dir=output_dir,
        console_script=["WalkLoop"],
        test_name=test_tag,
        capture_interval=0.5 if mode == "full" else 0.25,
        timeout=180 if mode == "full" else 60,
    )

    result.assert_ok("pie_started", report["session_id"] is not None)
    result.assert_ok("pie_completed", report["ok"], "; ".join(report["errors"]))
    frame_count = len(report["captured_frames"])
    expected_frames = 2 if mode == "quick" else 5
    result.assert_ok("frames_captured", frame_count >= expected_frames, f"got {frame_count}")
    if report["captured_frames"]:
        # embed first frame as inline screenshot reference
        src = report["captured_frames"][0]
        if os.path.isfile(src):
            result.screenshot_path = src
    result.duration_s = time.time() - t0


def test_pie_kaleido_battle_trigger(result: TestResult, mode: str) -> None:
    """Start PIE on KaleidoNave, walk toward interaction battle trigger, confirm it fires."""
    t0 = time.time()
    duration = 20 if mode == "full" else 8
    map_path = "/Game/EnvSandbox/Environments/L_KaleidoNave"
    test_tag = f"kaleido_battle_trigger_{mode}"

    report = run_pie_smoke_simple(
        map_path=map_path,
        duration=duration,
        output_dir=str(SCREENSHOT_DIR / test_tag),
        console_script=["WalkForward", "Interact"],
        test_name=test_tag,
        capture_interval=0.5 if mode == "full" else 0.25,
        timeout=180 if mode == "full" else 60,
    )

    result.assert_ok("pie_started", report["session_id"] is not None)
    result.assert_ok("pie_completed", report["ok"], "; ".join(report["errors"]))

    # Check for battle trigger firing in log matches
    found_battle = False
    for pattern in report.get("log_matches", {}):
        if any(kw in pattern.lower() for kw in ["battle", "encounter", "trigger", "interaction"]):
            found_battle = True
            break
    result.assert_ok("battle_trigger_fired", found_battle,
                     f"log_matches={list(report.get('log_matches',{}).keys())}")

    frame_count = len(report["captured_frames"])
    result.assert_ok("frames_captured", frame_count >= 1, f"got {frame_count}")
    if report["captured_frames"]:
        src = report["captured_frames"][0]
        if os.path.isfile(src):
            result.screenshot_path = src
    result.duration_s = time.time() - t0


def test_rhythm_skills_registered(result: TestResult, mode: str) -> None:
    """Verify that all 8 Melodia rhythm skills are registered in the system."""
    t0 = time.time()

    expected_skills = {
        "cadence_strike", "resonant_arc", "lullaby_mend", "downbeat_break",
        "dissonant_silence", "tempo_shift", "crescendo_wave", "harmony_shield",
    }

    registered: set[str] = set()

    # Query the MelodiaIntegrationConfig DataAsset for skill registrations
    try:
        resp = project_query("get_asset_details",
                              asset_path="/Game/MelodiaIntegration/Config/DA_MelodiaIntegrationConfig")
        raw_text = json.dumps(resp).lower()
        for skill in expected_skills:
            if skill.lower() in raw_text:
                registered.add(skill)
    except Exception:
        pass

    # Also query the GameInstance CDO for skills registered via RegisterSkill
    try:
        resp2 = blueprint_query("get_cdo_properties",
                                 asset_path="/Game/MelodiaIntegration/Blueprints/BP_MelodiaJRPGGameInstance.BP_MelodiaJRPGGameInstance_C")
        raw_text2 = json.dumps(resp2).lower()
        for skill in expected_skills:
            if skill.lower() in raw_text2:
                registered.add(skill)
    except Exception:
        pass

    for skill in sorted(expected_skills):
        result.assert_ok(f"skill_{skill}", skill in registered,
                         f"not found in config or game instance")

    # Secondary check: scan the Config directory for DataAsset files
    config_dir = PROJECT_DIR / "Content" / "MelodiaIntegration" / "Config"
    if config_dir.is_dir():
        asset_files = set()
        for f in config_dir.rglob("*.uasset"):
            asset_files.add(f.stem.lower())
        for skill in sorted(expected_skills):
            found_in_dir = any(skill in n for n in asset_files)
            result.assert_ok(f"skill_on_disk_{skill}", found_in_dir,
                             f"not in {config_dir}")

    total_expected = len(expected_skills)
    found_count = len(registered & expected_skills)
    result.assert_ok("all_skills_registered", found_count == total_expected,
                     f"{found_count}/{total_expected} skills found")
    result.duration_s = time.time() - t0


def test_battle_controller_pipeline(result: TestResult, mode: str) -> None:
    """Verify BP_BattleController EventGraph contains all expected pipeline nodes."""
    t0 = time.time()
    bp_path = "/Game/TurnBasedJRPGTemplate/Blueprints/Battle/BP_BattleController"

    expected_nodes = [
        "StartSession",
        "SubmitRatedInput",
        "ConsumePendingRequest",
        "RecordInputNow",
        "CompleteBattle",
        "TryGrantShards",
    ]

    # Export the graph via Monolith
    try:
        resp = blueprint_query("export_graph", asset_path=bp_path)
    except Exception as e:
        result.fail(f"export_graph failed: {e}")
        result.duration_s = time.time() - t0
        return

    graph_text = json.dumps(resp).lower()

    for node_name in expected_nodes:
        found = node_name.lower() in graph_text
        result.assert_ok(f"pipeline_node_{node_name}", found)

    result.duration_s = time.time() - t0


def test_rhythm_highway_texture_layers(result: TestResult, mode: str) -> None:
    """Verify WBP_MelodiaRhythmHighway has 4 Image children (SheetMusicBG, AuroraOverlay, SparkleField, NoteHighwayCanvas)."""
    t0 = time.time()

    expected_children = {"SheetMusicBG", "AuroraOverlay", "SparkleField", "NoteHighwayCanvas"}

    # Locate the widget asset via project_query
    found_asset = None
    for try_path in [
        "/Game/MelodiaIntegration/UI/WBP_MelodiaRhythmHighway",
        "/Game/Melodia/UI/WBP_MelodiaRhythmHighway",
    ]:
        try:
            resp = project_query("get_asset_details", asset_path=try_path)
            if resp and "error" not in str(resp).lower():
                found_asset = try_path
                break
        except Exception:
            pass

    if not found_asset:
        try:
            resp = project_query("find_assets", filter_string="WBP_MelodiaRhythmHighway")
            if isinstance(resp, dict) and resp.get("assets"):
                found_asset = resp["assets"][0]
        except Exception:
            pass

    if not found_asset:
        result.assert_ok("widget_asset_found", False, "WBP_MelodiaRhythmHighway not found on disk")
        result.duration_s = time.time() - t0
        return

    result.assert_ok("widget_asset_found", True, str(found_asset))

    # Query widget tree to find Image children
    def _collect_images(node, acc):
        if not isinstance(node, dict):
            return
        ntype = (node.get("widget_type") or node.get("type") or "").lower()
        nname = node.get("widget_name") or node.get("name") or node.get("variable_name") or ""
        if "image" in ntype and nname:
            acc.add(nname)
        for key in ("children", "slots", "widgets"):
            for child in node.get(key, []):
                _collect_images(child if isinstance(child, dict) else {}, acc)

    found_children = set()
    try:
        tree_resp = blueprint_query("get_widget_tree", asset_path=found_asset)
        if isinstance(tree_resp, dict):
            _collect_images(tree_resp, found_children)
    except Exception:
        pass

    if not found_children:
        # Fallback: export graph and search for widget variable names
        try:
            export_resp = blueprint_query("export_graph", asset_path=found_asset)
            export_text = json.dumps(export_resp).lower()
            found_children = {n for n in expected_children if n.lower() in export_text}
        except Exception as e:
            result.fail(f"Could not query widget tree: {e}")
            result.duration_s = time.time() - t0
            return

    for child_name in sorted(expected_children):
        result.assert_ok(f"widget_child_{child_name}", child_name in found_children,
                         f"not found in widget tree")

    total_expected = len(expected_children)
    found_count = len(found_children)
    result.assert_ok("all_image_children_present", found_count == total_expected,
                     f"{found_count}/{total_expected} Image children found")
    result.duration_s = time.time() - t0


# ---------------------------------------------------------------------------
# Test registry
# ---------------------------------------------------------------------------
def get_all_tests(mode: str) -> list[tuple[str, Any]]:
    tests = [
        ("Monolith Connectivity", test_monolith_connectivity),
        ("PIE L_MelusinaMorning Walk + Capture", test_pie_melusina_morning),
        ("PIE KaleidoNave Battle Trigger", test_pie_kaleido_battle_trigger),
        ("Rhythm Skills Registered (8 Melodia)", test_rhythm_skills_registered),
        ("BP_BattleController Pipeline Nodes", test_battle_controller_pipeline),
        ("WBP_MelodiaRhythmHighway Texture Layers", test_rhythm_highway_texture_layers),
    ]
    return tests


# ---------------------------------------------------------------------------
# HTML report generator
# ---------------------------------------------------------------------------
def generate_html_report(
    results: list[TestResult],
    mode: str,
    start_time: float,
) -> str:
    total = len(results)
    passed = sum(1 for r in results if r.passed is True)
    failed = sum(1 for r in results if r.passed is False)
    skipped = sum(1 for r in results if r.passed is None)
    elapsed = time.time() - start_time
    pct = (passed / total * 100) if total > 0 else 0

    rows = ""
    for r in results:
        icon = "&#9989;" if r.passed else ("&#10060;" if r.passed is False else "&#11088;")
        color = "#22c55e" if r.passed else ("#ef4444" if r.passed is False else "#facc15")
        status = r.status_text
        detail = r.detail.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
        screenshot_html = ""
        if r.screenshot_path:
            rel = os.path.relpath(r.screenshot_path, str(REPORT_DIR))
            screenshot_html = f'<br><img src="{rel}" style="max-width:400px;border:1px solid #38293b;border-radius:4px;margin-top:4px">'
        assertions_html = ""
        for a in r.assertions:
            aicon = "&#9989;" if a["passed"] else "&#10060;"
            ac = "#22c55e" if a["passed"] else "#ef4444"
            ad = a.get("detail", "").replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
            assertions_html += (
                f'<tr><td style="font-size:16px">{aicon}</td>'
                f'<td style="color:{ac}">{a["label"]}</td>'
                f'<td style="color:#aaa;font-size:12px">{ad}</td></tr>'
            )

        rows += f"""
        <tr>
            <td style="font-size:20px;text-align:center">{icon}</td>
            <td style="padding:8px;font-weight:bold">{r.name}</td>
            <td style="color:{color};font-weight:bold">{status}</td>
            <td style="color:#aaa;font-size:12px">{detail}</td>
            <td style="color:#666;font-size:12px">{r.duration_s:.1f}s</td>
            <td>{screenshot_html}</td>
        </tr>"""

    status_color = "#22c55e" if passed == total else "#eab308" if failed == 0 else "#ef4444"

    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Melodia Regression Suite - {mode.upper()}</title>
<style>
  * {{ box-sizing: border-box; margin: 0; padding: 0; }}
  body {{ font-family: 'Courier New', monospace; background: #0b0a13; color: #f2d69e; padding: 24px; }}
  h1 {{ color: #78ebff; font-size: 28px; margin-bottom: 4px; }}
  .sub {{ color: #888; font-size: 14px; margin-bottom: 24px; }}
  .summary {{ display: flex; gap: 16px; margin-bottom: 24px; flex-wrap: wrap; }}
  .stat {{ padding: 12px 24px; border-radius: 8px; font-weight: bold; font-size: 18px; text-align: center; min-width: 120px; }}
  table {{ width: 100%; border-collapse: collapse; margin-top: 12px; }}
  th {{ text-align: left; padding: 10px 8px; color: #78ebff; border-bottom: 2px solid #38293b; font-size: 14px; }}
  td {{ padding: 10px 8px; border-bottom: 1px solid #1a1520; vertical-align: top; }}
  tr:hover {{ background: #1a152055; }}
  .footer {{ color: #555; font-size: 12px; margin-top: 32px; text-align: center; }}
  .assertions {{ margin-top: 8px; }}
  .assertions table {{ width: auto; }}
  .assertions td {{ padding: 2px 8px; border: none; font-size: 13px; }}
  .pass {{ color: #22c55e; }}
  .fail {{ color: #ef4444; }}
  .skip {{ color: #facc15; }}
  @media (prefers-color-scheme: light) {{
    body {{ background: #f5f0e8; color: #2d1b0e; }}
    h1 {{ color: #1a6b7a; }}
    th {{ color: #1a6b7a; border-bottom-color: #c4b5a0; }}
    td {{ border-bottom-color: #ddd; }}
    .sub {{ color: #888; }}
    .footer {{ color: #aaa; }}
    tr:hover {{ background: #e8e0d0; }}
  }}
</style>
</head>
<body>

<h1>&#9835; Melodia Regression Suite</h1>
<div class="sub">
  {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} &middot;
  mode: <strong>{mode.upper()}</strong> &middot;
  elapsed: {elapsed:.0f}s
</div>

<div class="summary">
  <div class="stat" style="background:#22c55e22;color:#22c55e;border:1px solid #22c55e">{passed} PASS</div>
  <div class="stat" style="background:#ef444422;color:#ef4444;border:1px solid #ef4444">{failed} FAIL</div>
  <div class="stat" style="background:#facc1522;color:#facc15;border:1px solid #facc15">{skipped} SKIP</div>
  <div class="stat" style="background:#78ebff22;color:#78ebff;border:1px solid #78ebff">{pct:.0f}%</div>
</div>

<table>
<tr>
  <th style="width:40px"></th>
  <th>Test</th>
  <th style="width:80px">Status</th>
  <th>Detail</th>
  <th style="width:60px">Time</th>
  <th>Screenshot</th>
</tr>
{rows}
</table>

<div class="footer">
  Generated by regression_suite.py &middot;
  Melodia Gameplay Loop &middot; UE 5.8
</div>

<script>
  // Auto-refresh for --watch mode; one-shot otherwise
  const params = new URLSearchParams(window.location.search);
  if (params.get('watch') === '1') {{
    setTimeout(() => location.reload(), 5000);
  }}
</script>
</body>
</html>"""
    return html


# ---------------------------------------------------------------------------
# Main orchestration
# ---------------------------------------------------------------------------
def run_suite(mode: str) -> int:
    print(f"\n{'=' * 60}")
    print(f"  Melodia Regression Suite - mode: {mode.upper()}")
    print(f"  Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"{'=' * 60}\n")

    if mode not in ("quick", "full"):
        print(f"[ERROR] Unknown mode: {mode}. Use --quick or --full.")
        return 1

    # Pre-flight: check Monolith
    print("[PREFLIGHT] Checking Monolith MCP on localhost:9316 ...")
    try:
        monolith_status()
        print("[PREFLIGHT] Monolith is reachable.\n")
    except Exception as e:
        print(f"[PREFLIGHT] Monolith NOT reachable: {e}")
        print("[PREFLIGHT] Continuing - tests that require Monolith will fail gracefully.\n")

    tests = get_all_tests(mode)
    results: list[TestResult] = []
    start_time = time.time()

    for name, test_fn in tests:
        result = TestResult(name)
        print(f"  [{len(results)+1}/{len(tests)}] {name} ... ", end="", flush=True)
        try:
            test_fn(result, mode)
        except Exception as e:
            result.fail(f"Unhandled exception: {e}")
            import traceback
            traceback.print_exc()

        status = result.status_text
        elapsed_s = result.duration_s
        if result.passed:
            print(f"PASS ({elapsed_s:.1f}s)")
        elif result.passed is False:
            print(f"FAIL ({elapsed_s:.1f}s) - {result.detail[:120]}")
        else:
            print(f"SKIP ({elapsed_s:.1f}s)")
        results.append(result)

    # Generate HTML report
    html = generate_html_report(results, mode, start_time)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    report_path = REPORT_DIR / f"regression_{mode}_{timestamp}.html"
    report_path.write_text(html, encoding="utf-8")
    print(f"\n  Report: file://{report_path}")

    # Summary
    total = len(results)
    passed = sum(1 for r in results if r.passed is True)
    failed = sum(1 for r in results if r.passed is False)
    skipped = sum(1 for r in results if r.passed is None)
    elapsed = time.time() - start_time
    pct = (passed / total * 100) if total > 0 else 0

    print(f"\n{'=' * 60}")
    print(f"  RESULTS: {passed}/{total} passed ({pct:.0f}%)")
    if failed:
        print(f"  FAILED:")
        for r in results:
            if r.passed is False:
                print(f"    - {r.name}: {r.detail[:200]}")
    if skipped:
        print(f"  SKIPPED: {skipped}")
    print(f"  Elapsed: {elapsed:.0f}s")
    print(f"  Report:  {report_path}")
    print(f"{'=' * 60}\n")

    return 0 if failed == 0 else 1


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    p = argparse.ArgumentParser(
        description="Melodia Gameplay Loop - Automated Regression Test Suite",
    )
    p.add_argument("--quick", action="store_true", help="Quick mode (~5 min)")
    p.add_argument("--full", action="store_true", help="Full overnight mode (~2+ hr)")
    return p.parse_args(argv)


def main() -> int:
    args = parse_args()
    if args.quick:
        mode = "quick"
    elif args.full:
        mode = "full"
    else:
        print("Usage: python Tools/regression_suite.py --quick | --full")
        return 1

    return run_suite(mode)


if __name__ == "__main__":
    sys.exit(main())
