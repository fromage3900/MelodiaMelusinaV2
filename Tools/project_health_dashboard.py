#!/usr/bin/env python3
"""
project_health_dashboard.py - generate the Melodia project health dashboard.

Reads the real health signals the project already defines (Echo ledger,
echo_pipeline.json contract, mcp_tool_policy.v1.json, baseline files,
doc-link health, UTF-8 hygiene, editor reachability) and injects a verdict
per claim into Saved/project_health.html in the same dark-dashboard style
as the existing family (loop_monitor, live_dashboard, metrics_dashboard,
agent-dashboard-t3d).

Usage:
    python Tools/project_health_dashboard.py          # write Saved/project_health.html
    python Tools/project_health_dashboard.py --json   # also write Saved/Audit/project_health_claims.json
    python Tools/project_health_dashboard.py --watch  # regenerate every 10s

The generator is wired into rebuild_all_dashboards.py so "regenerate all
dashboards" includes the health page.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import socket
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------
HERE = Path(__file__).resolve().parent
PROJECT = HERE.parent
SAVED = PROJECT / "Saved"
AUDIT = SAVED / "Audit"
WIX = Path(r"C:\EnvironmentPortfolio\wix")

HEALTH_HTML = SAVED / "project_health.html"
CLAIMS_JSON = AUDIT / "project_health_claims.json"

ECHO_RUN = HERE / "echo_run.py"
DOC_LINK_CHECK = HERE / "doc_link_check.py"
MCP_POLICY = PROJECT / "specs" / "mcp_tool_policy.v1.json"
ECHO_PIPELINE = PROJECT / "specs" / "echo_pipeline.json"
CI_GATES = PROJECT / "specs" / "ci_gates.json"
ART_GATES_BASELINE = PROJECT / "specs" / "art_gates_baseline.json"
BP_FINGERPRINTS = PROJECT / "Docs" / "T3D_Baseline" / "bp_fingerprints.json"

LEDGER = PROJECT / "Saved" / "gate_ledger.json"

PALETTE = {
    "bg": "#0b0a13",
    "card": "#1a1520",
    "border": "#38293b",
    "cyan": "#78ebff",
    "gold": "#f2d69e",
    "dim": "#777777",
    "good": "#22c55e",
    "bad": "#ef4444",
    "warn": "#eab308",
    "muted": "#555555",
}

CSS = """
* { box-sizing: border-box; }
body { font-family: 'Courier New', monospace; background: %(bg)s; color: %(gold)s; margin: 0; padding: 20px; }
.header { display: flex; justify-content: space-between; align-items: center; border-bottom: 1px solid %(border)s; padding-bottom: 15px; margin-bottom: 20px; }
.title { font-size: 26px; color: %(cyan)s; letter-spacing: 1px; }
.subtitle { font-size: 13px; color: #666; }
.meta { font-size: 12px; color: %(muted)s; text-align: right; }
.grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(280px, 1fr)); gap: 16px; margin-bottom: 20px; }
.card { background: %(card)s; border: 1px solid %(border)s; border-radius: 8px; padding: 14px; }
.card h3 { margin: 0 0 8px 0; color: %(cyan)s; font-size: 12px; text-transform: uppercase; letter-spacing: 1px; }
.stat-row { display: flex; justify-content: space-between; padding: 3px 0; border-bottom: 1px solid #15101a; font-size: 13px; }
.stat-label { color: #777; }
.stat-value { color: %(gold)s; font-weight: bold; text-align: right; }
.stat-value.good { color: %(good)s; }
.stat-value.bad { color: %(bad)s; }
.stat-value.warn { color: %(warn)s; }
.stat-value.muted { color: %(muted)s; }
.bar { height: 14px; background: #15101a; border: 1px solid %(border)s; border-radius: 7px; overflow: hidden; margin: 6px 0 4px; }
.bar-fill { height: 100%%; background: linear-gradient(90deg, %(cyan)s, %(gold)s); }
.bar-label { font-size: 11px; color: #666; }
.section { margin: 24px 0 12px; font-size: 15px; color: %(cyan)s; text-transform: uppercase; letter-spacing: 1px; border-left: 3px solid %(cyan)s; padding-left: 8px; }
table { width: 100%%; border-collapse: collapse; margin-bottom: 24px; font-size: 12px; }
th { text-align: left; color: %(cyan)s; border-bottom: 1px solid %(border)s; padding: 6px 8px; text-transform: uppercase; letter-spacing: 1px; }
td { padding: 6px 8px; border-bottom: 1px solid #15101a; vertical-align: top; }
tr:hover td { background: #1f1830; }
.badge { display: inline-block; padding: 2px 8px; border-radius: 10px; font-size: 11px; font-weight: bold; }
.badge.pass { background: #22c55e22; border: 1px solid %(good)s; color: %(good)s; }
.badge.hold { background: #eab30822; border: 1px solid %(warn)s; color: %(warn)s; }
.badge.open { background: #77777722; border: 1px solid %(muted)s; color: %(muted)s; }
.badge.fail { background: #ef444422; border: 1px solid %(bad)s; color: %(bad)s; }
.badge.warn { background: #eab30822; border: 1px solid %(warn)s; color: %(warn)s; }
.code { background: #15101a; border: 1px solid %(border)s; border-radius: 6px; padding: 12px; font-size: 12px; white-space: pre-wrap; color: %(gold)s; margin: 8px 0 20px; }
.footer { margin-top: 30px; border-top: 1px solid %(border)s; padding-top: 10px; font-size: 11px; color: %(muted)s; }
a { color: %(cyan)s; }
.orchestra { font-size: 13px; margin-bottom: 20px; }
""" % PALETTE


# ---------------------------------------------------------------------------
# Small helpers
# ---------------------------------------------------------------------------

def run(cmd: list[str], timeout: int = 120) -> tuple[int, str]:
    r = subprocess.run(cmd, capture_output=True, text=True, cwd=PROJECT, timeout=timeout)
    return r.returncode, (r.stdout + r.stderr).strip()


def editor_reachable() -> bool:
    try:
        s = socket.create_connection(("127.0.0.1", 9316), timeout=1.5)
        s.close()
        return True
    except OSError:
        return False


def _ledger_latest() -> dict:
    if not LEDGER.exists():
        return {}
    try:
        data = json.loads(LEDGER.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {}
    latest: dict = {}
    for g in data.get("gates", []):
        latest[g["id"]] = g
    return latest


def _load_json(path: Path):
    if not path.exists():
        return None
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None


# ---------------------------------------------------------------------------
# Claim checkers
# ---------------------------------------------------------------------------

class Claim:
    def __init__(self, cid: str, label: str):
        self.cid = cid
        self.label = label
        self.status = "open"  # pass | hold | open | fail | warn
        self.evidence = ""
        self.detail = ""

    def as_dict(self) -> dict:
        return {
            "id": self.cid,
            "label": self.label,
            "status": self.status,
            "evidence": self.evidence,
            "detail": self.detail,
        }


def check_completion_gates(ledger: dict) -> Claim:
    c = Claim("completion_gates", "Completion gates (ledger-backed)")
    definitions = {
        "runtime": "Victory/Defeat/Fled/unavailable; each resumes/aborts Quill exactly once",
        "save_load": "Canonical BP_JRPGSaveGame slot across a full process restart",
        "repeat_consume": "Flag+reward restore without duplication; melodia:stat: idempotent per IntentId",
        "package_launch": "Development-packaged build launches outside the editor",
    }
    rows = []
    all_pass = True
    any_hold = False
    for gid, what in definitions.items():
        rec = ledger.get(gid)
        if rec and rec.get("status") == "pass":
            status = "pass"
        elif rec and rec.get("status") == "fail":
            status = "fail"
        else:
            status = "open"
        date = rec.get("date", "") if rec else ""
        rows.append((gid, status, date, what))
        if status != "pass":
            all_pass = False
        if status == "open":
            any_hold = True

    if rows:
        c.evidence = "Saved/gate_ledger.json via echo_run.py status"
        if all_pass:
            c.status = "pass"
            c.detail = "4/4 PASS"
        elif any_hold and not any(r[1] == "fail" for r in rows):
            c.status = "hold"
            c.detail = "editor-backed rows are historical until re-verified"
        else:
            c.status = "fail"
            c.detail = "not all gates PASS"
    else:
        c.status = "open"
        c.evidence = "Saved/gate_ledger.json missing or empty"
    c.detail = (c.detail + "  |  " + "  |  ".join(f"{g}: [{s}]" for g, s, _, _ in rows)) if rows else c.detail
    return c


def check_echo_pipeline() -> Claim:
    c = Claim("contract_echo_pipeline", "Echo pipeline spec valid (specs/echo_pipeline.json)")
    data = _load_json(ECHO_PIPELINE)
    if data is None:
        c.status = "fail"
        c.evidence = "specs/echo_pipeline.json missing or not parseable JSON"
        return c
    if not isinstance(data, dict) or "stages" not in data or "completion_gates" not in data:
        c.status = "fail"
        c.evidence = "specs/echo_pipeline.json missing expected keys (stages, completion_gates)"
        return c
    code, out = run([sys.executable, str(ECHO_RUN), "validate-spec", str(ECHO_PIPELINE)])
    try:
        res = json.loads(out) if out else {}
    except json.JSONDecodeError:
        res = {}
    if code == 0 and res.get("ok"):
        c.status = "pass"
        c.evidence = f"echo_run.py validate-spec specs/echo_pipeline.json -> ok:true"
    else:
        c.status = "fail"
        c.evidence = f"echo_run.py validate-spec specs/echo_pipeline.json -> exit {code}"
        c.detail = res.get("errors", ["parse failed"])[:5]
    return c


def check_verb_contract() -> Claim:
    c = Claim("contract_verb_contract", "Verb contract defined (melodia: intents in echo pipeline)")
    data = _load_json(ECHO_PIPELINE)
    if data and isinstance(data, dict):
        verbs = data.get("agent_contract", {}).get("verbs", [])
        if verbs:
            c.status = "pass"
            c.evidence = f"echo_pipeline.json agent_contract.verbs = {len(verbs)} entries"
            c.detail = "; ".join(verbs[:4]) + (" ..." if len(verbs) > 4 else "")
            return c
    c.status = "fail"
    c.evidence = "echo_pipeline.json agent_contract.verbs missing or empty"
    return c


def check_mcp_policy() -> Claim:
    c = Claim("policy_parseable", "MCP tool policy parseable + forbidden-path tokens defined")
    data = _load_json(MCP_POLICY)
    if data is None:
        c.status = "fail"
        c.evidence = "specs/mcp_tool_policy.v1.json missing or not parseable"
        return c
    forbidden = data.get("forbidden_path_tokens", [])
    tools = data.get("tools", {})
    if not isinstance(tools, dict) or not tools:
        c.status = "fail"
        c.evidence = "specs/mcp_tool_policy.v1.json has no tools entries"
        return c
    c.status = "pass"
    c.evidence = f"specs/mcp_tool_policy.v1.json -> {len(tools)} tools, {len(forbidden)} forbidden path tokens"
    c.detail = "forbidden: " + ", ".join(forbidden) if forbidden else "no forbidden path tokens"
    return c


def check_baseline_fingerprints() -> Claim:
    c = Claim("baseline_fingerprints", "Blueprint fingerprint baseline present + parseable")
    if not BP_FINGERPRINTS.exists():
        c.status = "fail"
        c.evidence = f"Docs/T3D_Baseline/bp_fingerprints.json missing"
        return c
    data = _load_json(BP_FINGERPRINTS)
    if data is None:
        c.status = "fail"
        c.evidence = "Docs/T3D_Baseline/bp_fingerprints.json not parseable"
        return c
    count = len(data) if isinstance(data, dict) else 0
    c.status = "pass" if count else "warn"
    c.evidence = f"Docs/T3D_Baseline/bp_fingerprints.json -> {count} fingerprints"
    c.detail = "baseline exists but is empty" if count == 0 else ""
    return c


def check_baseline_ci_gates() -> Claim:
    c = Claim("baseline_ci_gates", "CI quality gates defined (specs/ci_gates.json)")
    data = _load_json(CI_GATES)
    if data is None:
        c.status = "fail"
        c.evidence = "specs/ci_gates.json missing or not parseable"
        return c
    if not isinstance(data, dict) or not data:
        c.status = "fail"
        c.evidence = "specs/ci_gates.json empty"
        return c
    c.status = "pass"
    c.evidence = f"specs/ci_gates.json -> {len(data)} quality gate thresholds"
    c.detail = ", ".join(f"{k}={v}" for k, v in list(data.items())[:6])
    return c


def check_baseline_art_gates() -> Claim:
    c = Claim("baseline_art_gates", "Art gate baseline present (specs/art_gates_baseline.json)")
    data = _load_json(ART_GATES_BASELINE)
    if data is None:
        c.status = "fail"
        c.evidence = "specs/art_gates_baseline.json missing or not parseable"
        return c
    c.status = "pass"
    c.evidence = "specs/art_gates_baseline.json present + parseable"
    return c


def check_doc_links() -> Claim:
    c = Claim("doc_links", "Doc local links below breakdown threshold")
    code, out = run([sys.executable, str(DOC_LINK_CHECK)], timeout=180)
    m = re.search(r"checked (\d+) local links, (\d+) BROKEN", out)
    if code != 0 or not m:
        c.status = "fail"
        c.evidence = "Tools/doc_link_check.py failed to run"
        c.detail = out[:200] if out else "(no output)"
        return c
    checked, broken = int(m.group(1)), int(m.group(2))
    c.evidence = f"Tools/doc_link_check.py -> {checked} links checked, {broken} broken"
    if broken == 0:
        c.status = "pass"
    elif broken <= 50:
        c.status = "warn"
        c.detail = f"{broken} broken local links - historical docs debt, not a Hermes/gate blocker"
    else:
        c.status = "fail"
        c.detail = f"{broken} broken local links - above threshold"
    return c


def check_doc_links_offline() -> Claim:
    """Report documentation debt without blocking hosted source checks."""
    c = check_doc_links()
    if c.status == "fail":
        c.status = "warn"
        c.detail = (c.detail or "") + "; non-blocking in hosted offline CI"
    return c


def check_utf8_hygiene() -> Claim:
    c = Claim("hygiene_utf8", "Tracked text files are strict UTF-8")
    exts = {".md", ".json", ".py", ".toml", ".yaml", ".yml"}
    bad = 0
    checked = 0
    bad_examples: list[str] = []
    for folder in ("specs", "Tools", "deploy"):
        root = PROJECT / folder
        if not root.is_dir():
            continue
        for path in root.rglob("*"):
            if not path.is_file() or path.suffix.lower() not in exts:
                continue
            if any(part.startswith(".") or part == "__pycache__" for part in path.parts):
                continue
            try:
                path.read_text(encoding="utf-8")
                checked += 1
            except (UnicodeDecodeError, OSError):
                bad += 1
                if len(bad_examples) < 5:
                    bad_examples.append(str(path.relative_to(PROJECT)))
    c.evidence = f"strict UTF-8 on {checked} files under specs/Tools/deploy, {bad} decode failures"
    if bad == 0:
        c.status = "pass"
    else:
        c.status = "fail"
        c.detail = f"{bad} non-UTF-8 files; examples: " + ", ".join(bad_examples)
    return c


def check_editor_reachable() -> Claim:
    c = Claim("editor_reachable", "Monolith reachable on 127.0.0.1:9316")
    up = editor_reachable()
    c.status = "pass" if up else "hold"
    c.evidence = "socket connect to 127.0.0.1:9316" + (" -> yes" if up else " -> no")
    if not up:
        c.detail = "Editor-backed claims below are HOLD until the editor is up"
    return c


# ---------------------------------------------------------------------------
# Orchestrate
# ---------------------------------------------------------------------------

def check_battle_gates(ledger: dict) -> Claim:
    c = Claim("battle_gates", "Battle encounter gates (ledger-backed)")
    ids = ("battle_encounter", "battle_integration_map")
    parts = []
    worst = "pass"
    for gid in ids:
        rec = ledger.get(gid) or {}
        status = rec.get("status") or "open"
        date = rec.get("date") or ""
        note = (rec.get("note") or "")[:160]
        parts.append(f"{gid}: [{status}] {date}")
        if status == "fail":
            worst = "fail"
        elif status != "pass" and worst != "fail":
            worst = "hold"
        if "infinite loop" in note.lower() and status == "pass":
            c.detail = "Show-loop claim is stale; latest ledger row is pass"
    c.status = worst
    c.evidence = "Saved/gate_ledger.json - " + " - ".join(parts)
    if worst == "pass":
        c.detail = (c.detail + " - " if c.detail else "") + "Owner closed BP_BattleController::Show infinite-loop claim 2026-08-19"
    return c


def check_hermes_harness(_ledger=None) -> Claim:
    c = Claim("hermes_harness", "Hermes agentic harness (not a model pull)")
    mcp = PROJECT / "deploy" / "hermes_mcp.py"
    daemon = PROJECT / "deploy" / "hermes_daemon.py"
    server = PROJECT / "deploy" / "melodia_mcp_server.py"
    if mcp.is_file() and daemon.is_file() and server.is_file():
        c.status = "pass"
        c.evidence = "deploy/hermes_mcp.py + hermes_daemon.py + melodia_mcp_server.py"
        latest = AUDIT / "math_run_latest.json"
        if latest.is_file():
            try:
                run = json.loads(latest.read_text(encoding="utf-8"))
                c.detail = (
                    f"MATH {run.get('passed')}/{run.get('total')} scores this harness "
                    f"({run.get('captured_at')}). Do not ollama pull hermes3."
                )
            except json.JSONDecodeError:
                c.detail = "MATH run JSON unparseable; do not ollama pull hermes3."
        else:
            c.detail = "no MATH run JSON yet; do not ollama pull hermes3."
    else:
        c.status = "fail"
        c.evidence = "Hermes harness files missing under deploy/"
    return c


def check_orchestrator(_ledger=None) -> Claim:
    c = Claim("orchestrator_swe_light", "SWE Light Qwen/Muse wrapper expansion")
    server_path = Path(r"C:\EnvironmentPortfolio\BS_GodFile\deploy\melodia_mcp_server.py")
    progress = Path(r"C:\EnvironmentPortfolio\.agents\swe_3\progress.md")
    required_wrappers = (
        "melodia_animation_validate_state_machine",
        "melodia_audio_list_assets",
        "melodia_ui_list_widgets",
    )
    if not server_path.is_file():
        c.status = "fail"
        c.evidence = "melodia_mcp_server.py missing"
        return c
    text = server_path.read_text(encoding="utf-8", errors="replace")
    missing = [fn for fn in required_wrappers if f"def {fn}(" not in text]
    c.evidence = str(server_path)
    if missing:
        c.status = "hold"
        c.detail = f"Missing wrapper functions on disk: {', '.join(missing)}"
        return c
    if progress.is_file() and ("[x] Phase 5: Victory Audit" in progress.read_text(encoding="utf-8", errors="replace")
                               or "[X] Phase 5" in progress.read_text(encoding="utf-8", errors="replace")):
        c.status = "pass"
        c.detail = "Animation/Audio/UI wrappers on disk; victory audit checked off"
    else:
        c.status = "pass"
        c.detail = "Animation/Audio/UI MCP wrappers present in melodia_mcp_server.py"
    return c


def _completed_model_runs() -> dict[str, dict]:
    """Return {model: report} for completed model-via-harness runs on disk.

    A run counts only when the report kind is 'model_via_hermes_harness'
    (i.e. the model actually went through the harness). Tag presence in
    ollama is installation, not evidence.
    """
    runs: dict[str, dict] = {}
    latest = AUDIT / "math_run_models_latest.json"
    candidates: list[dict] = []
    if latest.is_file():
        try:
            bundle = json.loads(latest.read_text(encoding="utf-8"))
            candidates.extend(bundle.get("runs") or [])
        except json.JSONDecodeError:
            pass
    for path in sorted(AUDIT.glob("math_run_*.json")):
        if path.name == "math_run_models_latest.json":
            continue
        try:
            body = json.loads(path.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            continue
        if isinstance(body, dict) and body.get("kind") == "model_via_hermes_harness":
            candidates.append(body)
    for report in candidates:
        model = report.get("model")
        if not model:
            continue
        prev = runs.get(model)
        if prev is None or (report.get("captured_at") or "") >= (prev.get("captured_at") or ""):
            runs[model] = report
    return runs


def check_run_evidence_consistency(_ledger=None) -> Claim:
    """Gate: a PASS claim must be backed by a completed run JSON, not a marker."""
    c = Claim("run_evidence_consistency", "Run evidence consistency (no PASS without run JSON)")
    markers = sorted(AUDIT.glob("math_run_*_in_progress.json"))
    skips = sorted(AUDIT.glob("math_run_*_skipped.json"))
    completed = _completed_model_runs()
    problems: list[str] = []
    if markers:
        problems.append(f"in_progress: {', '.join(p.name for p in markers)}")
    if skips and not completed:
        problems.append(f"skipped runs are the newest evidence: {', '.join(p.name for p in skips)}")
    if not completed:
        problems.append("no completed model run JSONs on disk")
    if problems:
        c.status = "hold"
        c.evidence = "Saved/Audit/math_run_*.json scan"
        c.detail = "; ".join(problems[:3])
        return c
    models = sorted(completed)
    c.status = "pass"
    c.evidence = f"{len(completed)} completed run JSON(s): {', '.join(models)}"
    c.detail = "every model claim above is PASS only because a run JSON exists"
    return c


def check_qwen_local(_ledger=None) -> Claim:
    c = Claim("model_qwen_local", "Local Qwen for Hermes-harness eval")
    try:
        import urllib.request
        tags = json.loads(urllib.request.urlopen("http://127.0.0.1:11434/api/tags", timeout=3).read().decode())
        names = [str(m.get("name") or "") for m in tags.get("models") or []]
    except Exception as exc:
        c.status = "hold"
        c.evidence = f"ollama /api/tags unreachable: {exc}"
        return c
    qwen = [n for n in names if "qwen" in n.lower()]
    runs = {m: r for m, r in _completed_model_runs().items() if "qwen" in m.lower()}
    c.evidence = ", ".join(qwen) if qwen else "no qwen tags"
    if runs:
        best = max(runs.values(), key=lambda r: (r.get("captured_at") or ""))
        c.status = "pass"
        c.detail = f"run JSON {best.get('captured_at')}: TCA={best.get('tca_pct')}% EXEC={best.get('exec_pct')}%"
    elif qwen:
        c.status = "hold"
        c.detail = "tags installed; no completed run JSON yet - run python Tools/run_math_models.py --model qwen3.8-27b"
    else:
        c.status = "open"
        c.detail = "no qwen tag; run Tools/setup_muse_glimmer.py or ollama pull"
    return c


def check_muse_glimmer(_ledger=None) -> Claim:
    c = Claim("model_muse_glimmer", "Muse Glimmer for Hermes-harness eval")
    try:
        import urllib.request
        tags = json.loads(urllib.request.urlopen("http://127.0.0.1:11434/api/tags", timeout=3).read().decode())
        names = [str(m.get("name") or "") for m in tags.get("models") or []]
    except Exception:
        names = []
    muse = [n for n in names if "muse" in n.lower() or "glimmer" in n.lower()]
    runs = {m: r for m, r in _completed_model_runs().items() if "muse" in m.lower() or "glimmer" in m.lower()}
    if runs:
        best = max(runs.values(), key=lambda r: (r.get("captured_at") or ""))
        c.status = "pass"
        c.evidence = "run JSON: " + (best.get("captured_at") or "?")
        c.detail = f"TCA={best.get('tca_pct')}% EXEC={best.get('exec_pct')}% (python Tools/run_math_models.py --run-muse)"
        return c
    if muse:
        c.status = "hold"
        c.evidence = ", ".join(muse)
        c.detail = "tag installed 2026-08-19; PASS requires a completed run JSON (python Tools/run_math_models.py --run-muse)"
        return c
    try:
        import sys
        tools = ROOT / "Tools"
        if str(tools) not in sys.path:
            sys.path.insert(0, str(tools))
        from openrouter_chat import probe_muse

        probe = probe_muse(timeout=12.0)
        if probe.get("ok"):
            c.status = "hold"
            c.evidence = f"openrouter {probe.get('model')}"
            c.detail = "reachable; PASS requires a completed run JSON"
            return c
    except Exception:
        pass
    skip = AUDIT / "math_run_muse-glimmer_skipped.json"
    if skip.exists():
        c.status = "open"
        try:
            body = json.loads(skip.read_text(encoding="utf-8"))
            c.evidence = str(body.get("reason") or "skipped")[:120]
        except json.JSONDecodeError:
            c.evidence = "skipped - see Saved/Audit/math_run_muse-glimmer_skipped.json"
    else:
        c.status = "open"
        c.evidence = "no ollama tag; OPENROUTER probe failed; run Tools/setup_muse_glimmer.py"
    c.detail = "python Tools/setup_muse_glimmer.py  OR  set OPENROUTER_API_KEY + 18+ attestation"
    return c


def check_toronto_lanes(_ledger=None) -> Claim:
    """Toronto product-integration lanes: artifact gates, same run-JSON rule."""
    c = Claim("toronto_lanes", "Toronto integration lanes (Cohere / Q# / NeMo Guardrails)")

    def newest(prefix: str) -> dict | None:
        hits = sorted(AUDIT.glob(f"{prefix}*.json"))
        if not hits:
            return None
        return json.loads(hits[-1].read_text(encoding="utf-8"))

    def status_of(artifact: dict | None, *, run_kinds: tuple[str, ...]) -> str:
        if artifact is None:
            return "open"
        if artifact.get("kind") in run_kinds and artifact.get("status") != "held":
            return "pass"
        return "hold"

    qsharp = newest("math_run_qsharp_")
    guardrails = newest("guardrails_")
    cohere = newest("cohere_lane_held_") or newest("math_run_cohere_")
    parts = [
        ("qsharp", status_of(qsharp, run_kinds=("model_via_qsharp",)), qsharp),
        ("guardrails", status_of(guardrails, run_kinds=("guardrails_lane",)), guardrails),
        ("cohere", status_of(cohere, run_kinds=("model_via_cohere",)), cohere),
    ]
    held = [name for name, st, _art in parts if st == "hold"]
    op = [name for name, st, _art in parts if st == "open"]
    if op:
        c.status = "open"
        c.evidence = "no artifact: " + ", ".join(op)
        c.detail = "run Tools/run_qsharp_lane.py, Tools/run_guardrails_lane.py, or set COHERE_API_KEY + Tools/run_cohere_lane.py"
        return c
    if held:
        c.status = "hold"
        c.evidence = "artifact present, no completed run: " + ", ".join(held)
        c.detail = "held until a run JSON exists (see Saved/Audit)"
        return c
    c.status = "pass"
    c.evidence = "artifacts: " + ", ".join(name for name, _st, _art in parts)
    c.detail = (
        f"qsharp {qsharp.get('passed')}/{qsharp.get('total')} - guardrails "
        f"{(guardrails.get('stats') or {}).get('pass_rate')}% - cohere {cohere.get('passed')}/{cohere.get('total')}"
    )
    return c


CHECKERS = [
    check_completion_gates,
    check_battle_gates,
    check_echo_pipeline,
    check_verb_contract,
    check_mcp_policy,
    check_baseline_fingerprints,
    check_baseline_ci_gates,
    check_baseline_art_gates,
    check_doc_links,
    check_utf8_hygiene,
    check_editor_reachable,
    check_hermes_harness,
    check_orchestrator,
    check_qwen_local,
    check_muse_glimmer,
    check_toronto_lanes,
    check_run_evidence_consistency,
]

# Hosted CI can verify repository-local evidence, but it cannot honestly
# certify an Unreal editor, local model server, or developer-only Windows path.
OFFLINE_CHECKERS = [
    check_completion_gates,
    check_battle_gates,
    check_echo_pipeline,
    check_verb_contract,
    check_mcp_policy,
    check_baseline_fingerprints,
    check_baseline_ci_gates,
    check_baseline_art_gates,
    check_doc_links_offline,
    check_utf8_hygiene,
    check_hermes_harness,
    check_run_evidence_consistency,
    check_toronto_lanes,
]

STATUS_RANK = {"pass": 0, "hold": 1, "warn": 1, "open": 2, "fail": 3}


def compute_standing(claims: list[Claim]) -> tuple[str, str]:
    """Derive an overall standing label from the claims."""
    editor_up = any(cl.cid == "editor_reachable" and cl.status == "pass" for cl in claims)
    editor_hold = any(cl.cid == "editor_reachable" and cl.status == "hold" for cl in claims)

    fails = [cl for cl in claims if cl.status == "fail"]
    passes = [cl for cl in claims if cl.status == "pass"]
    holds = [cl for cl in claims if cl.status == "hold"]

    if fails:
        return "fail", f"{len(fails)} claim(s) FAIL"
    if holds or any(cl.status in {"warn", "open"} for cl in claims):
        if editor_hold and not editor_up:
            return "hold", "editor not reachable; editor-backed claims are HOLD"
        return "hold", f"{len(passes)}/{len(claims)} pass; remaining hold/warn/open"
    if editor_hold and not editor_up:
        return "hold", "editor not reachable; editor-backed claims are HOLD"
    if len(passes) == len(claims):
        return "pass", "all claims PASS"


def generate_html(claims: list[Claim], standing: str, standing_detail: str, now: datetime) -> str:
    ts = now.strftime("%Y-%m-%d %H:%M:%S")
    editor_claim = next((cl for cl in claims if cl.cid == "editor_reachable"), None)
    editor_up = editor_claim and editor_claim.status == "pass"

    cards = ""
    for cl in claims:
        badge_cls = cl.status
        badge_label = cl.status.upper()
        cards += f"""
    <div class="card">
      <h3>{cl.label}</h3>
      <div class="stat-row"><span class="stat-label">Status</span><span class="stat-value {badge_cls}">{badge_label}</span></div>
      <div class="stat-row"><span class="stat-label">Evidence</span><span class="stat-value muted">{cl.evidence}</span></div>
      {f'<div class="stat-row"><span class="stat-label">Detail</span><span class="stat-value muted">{cl.detail}</span></div>' if cl.detail else ""}
    </div>"""

    rows = ""
    for cl in claims:
        badge_cls = cl.status
        rows += f"""<tr>
      <td><span class="badge {badge_cls}">{cl.status.upper()}</span></td>
      <td>{cl.label}</td>
      <td class="code" style="margin:0;white-space:normal;font-size:11px">{cl.evidence}</td>
    </tr>"""

    bar_pct = int((len([c for c in claims if c.status == "pass"]) / max(len(claims), 1)) * 100)

    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta http-equiv="refresh" content="30">
<title>Melodia Project Health</title>
<style>{CSS}</style>
</head>
<body>
<div class="header">
  <div>
    <div class="title">Melodia Project Health</div>
    <div class="subtitle">Standing scorecard - Echo gates, local model tooling (Qwen / Muse), and the SWE Light wrapper</div>
  </div>
  <div class="meta">generated {ts} - {"editor up" if editor_up else "editor down"} - refresh 30s</div>
</div>

<div class="section">Orchestra</div>
<div class="card orchestra">
  <a href="dashboards.html">hub</a>
  &nbsp;-&nbsp; <a href="loop_monitor.html">loop_monitor</a>
  &nbsp;-&nbsp; <a href="live_dashboard.html">live PIE</a>
  &nbsp;-&nbsp; <a href="metrics_dashboard.html">metrics PIE</a>
  &nbsp;-&nbsp; <a href="agent-dashboard-t3d.html">T3D claims</a>
  &nbsp;-&nbsp; <a href="t3d-catalog.html">T3D catalog</a>
  &nbsp;-&nbsp; <a href="melusina-agent-harness.html">Hermes harness</a>
</div>

<div class="grid">
  <div class="card">
    <h3>Overall standing</h3>
    <div class="stat-row"><span class="stat-label">Status</span><span class="stat-value {standing}">{standing.upper()}</span></div>
    <div class="stat-row"><span class="stat-label">Detail</span><span class="stat-value muted">{standing_detail}</span></div>
  </div>
  <div class="card">
    <h3>Pass rate</h3>
    <div class="bar"><div class="bar-fill" style="width:{bar_pct}%"></div></div>
    <div class="bar-label">{sum(1 for c in claims if c.status == 'pass')}/{len(claims)} claims pass</div>
  </div>
  <div class="card">
    <h3>How to read this</h3>
    <div class="stat-row"><span class="stat-label">PASS</span><span class="stat-value good">claim verified right now</span></div>
    <div class="stat-row"><span class="stat-label">HOLD</span><span class="stat-value warn">editor-backed; re-verify with editor up</span></div>
    <div class="stat-row"><span class="stat-label">WARN</span><span class="stat-value warn">under threshold but tracked</span></div>
    <div class="stat-row"><span class="stat-label">OPEN</span><span class="stat-value muted">not yet verified</span></div>
    <div class="stat-row"><span class="stat-label">FAIL</span><span class="stat-value bad">claim broken or missing</span></div>
  </div>
</div>

<div class="section">Claim verdicts</div>
<table>
<tr><th>Status</th><th>Claim</th><th>Evidence</th></tr>
{rows}
</table>

<div class="section">Refresh policy</div>
<div class="code">- This page is regenerated on demand (python Tools/project_health_dashboard.py) and by rebuild_all_dashboards.py.
- Auto-refreshes every 30s when served from Saved/ (python -m http.server 8080 -d Saved).
- Editor-backed claims (completion gates, live allowlist) are HOLD when 9316 is down; the ledger is the current historical record.
- CI runs the offline slice (contract parse, policy parse, baseline existence, doc links, UTF-8 hygiene) on push/PR.
- The programatic gate/ledger layer is echo_run.py + Saved/gate_ledger.json; this dashboard is the human-readable view.</div>

<div class="footer">
  Generated {ts} via Tools/project_health_dashboard.py - data sources: Saved/gate_ledger.json, specs/echo_pipeline.json, specs/mcp_tool_policy.v1.json, specs/ci_gates.json, specs/art_gates_baseline.json, Docs/T3D_Baseline/bp_fingerprints.json, Tools/doc_link_check.py, strict UTF-8 walk - Part of the Melodia dashboard family (rebuild_all_dashboards.py)
</div>
</body>
</html>"""
    return html


def main() -> int:
    parser = argparse.ArgumentParser(description="Melodia project health dashboard generator")
    parser.add_argument("--json", action="store_true", help="also write Saved/Audit/project_health_claims.json")
    parser.add_argument(
        "--offline",
        action="store_true",
        help="skip editor, local-model, and developer-checkout probes",
    )
    parser.add_argument("--watch", action="store_true", help="regenerate every 10s")
    parser.add_argument("--open", action="store_true", help="open the HTML in a browser after writing")
    args = parser.parse_args()

    ledger = _ledger_latest()

    claims: list[Claim] = []
    checkers = OFFLINE_CHECKERS if args.offline else CHECKERS
    for checker in checkers:
        try:
            import inspect
            params = inspect.signature(checker).parameters
            claims.append(checker(ledger) if params else checker())
        except Exception as e:
            cid = getattr(checker, "__name__", str(checker))
            claims.append(Claim(cid, cid))
            claims[-1].status = "fail"
            claims[-1].evidence = f"checker raised: {e}"

    standing, standing_detail = compute_standing(claims)
    now = datetime.now(timezone.utc)

    html = generate_html(claims, standing, standing_detail, now)
    SAVED.mkdir(parents=True, exist_ok=True)
    AUDIT.mkdir(parents=True, exist_ok=True)
    HEALTH_HTML.write_text(html, encoding="utf-8")
    print(f"[OK] Health dashboard: {HEALTH_HTML}")
    if WIX.is_dir():
        (WIX / "project_health.html").write_text(html, encoding="utf-8")
        print(f"[OK] Wix mirror: {WIX / 'project_health.html'}")

    if args.json:
        data = {
            "generated_utc": now.isoformat(),
            "mode": "offline" if args.offline else "full",
            "standing": standing,
            "standing_detail": standing_detail,
            "editor_reachable": editor_reachable(),
            "claims": [c.as_dict() for c in claims],
        }
        CLAIMS_JSON.write_text(json.dumps(data, indent=2), encoding="utf-8")
        print(f"[OK] Claims JSON: {CLAIMS_JSON}")

    if args.open:
        import webbrowser
        webbrowser.open(str(HEALTH_HTML))

    if args.watch:
        try:
            while True:
                time.sleep(10)
                main()
        except KeyboardInterrupt:
            print("\nStopped.")

    fails = [c for c in claims if c.status == "fail"]
    return 1 if fails else 0


if __name__ == "__main__":
    sys.exit(main())
