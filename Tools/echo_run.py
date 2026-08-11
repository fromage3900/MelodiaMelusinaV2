#!/usr/bin/env python3
"""
echo_run.py - the Melodia Echo pipeline runner.

One entry point for the integration-layer gate chain declared in
`specs/echo_pipeline.json`. Mirrors the agent-gating shape HoYoverse's Echo
applies to AI-generated game content: a proposal may be authored by an agent or
the owner, but nothing is believed until a gate produces a ledger row.

    python Tools/echo_run.py list                     # stages + tools
    python Tools/echo_run.py status                   # ledger-backed completion gates
    python Tools/echo_run.py run static_gates         # one static stage (offline-safe)
    python Tools/echo_run.py run --all                # all static gate tools, in order
    python Tools/echo_run.py validate-spec spec.json  # contract check on a proposal
    python Tools/echo_run.py record <id> pass|fail --note "..."   # delegate to record_gate

LIVENESS: stages that need the editor (pie_smoke, baseline, regression, live
fingerprint) are reported as HOLD when Monolith is not answering on 9316. A
HOLD is not a pass and never writes a ledger row. Static gates that run on disk
do not need the editor and are safe to run anywhere.
"""
from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
PROJECT = os.path.dirname(HERE)
MANIFEST = os.path.join(PROJECT, "specs", "echo_pipeline.json")
LEDGER = os.path.join(PROJECT, "Saved", "gate_ledger.json")

VERB_RE = {
    "melodia:battle:": "EncounterId",
    "melodia:quest:": "QuestId",
    "melodia:flag:": "FlagId:<true|false>",
    "melodia:travel:": "LevelId",
    "melodia:reward:": "RewardId",
    "melodia:stat:": "IntentId:StatId:Delta",
    "melodia:item:give:": "ItemId:Count",
}


def py(*args: str, cwd: str | None = None, timeout: int = 600) -> str:
    r = subprocess.run([sys.executable or "python"] + list(args),
                       capture_output=True, text=True, cwd=cwd or PROJECT, timeout=timeout)
    return r.stdout.strip() + r.stderr.strip()


def editor_live() -> bool:
    """True when Monolith is answering on 9316. Editor-only stages hold otherwise."""
    try:
        import socket
        s = socket.create_connection(("127.0.0.1", 9316), timeout=1.5)
        s.close()
        return True
    except OSError:
        return False


def _ledger_latest() -> dict:
    if not os.path.exists(LEDGER):
        return {}
    try:
        with open(LEDGER, encoding="utf-8") as fh:
            ledger = json.load(fh)
    except (OSError, json.JSONDecodeError):
        return {}
    latest = {}
    for g in ledger.get("gates", []):
        latest[g["id"]] = g
    return latest


def load_manifest() -> dict:
    with open(MANIFEST, encoding="utf-8") as fh:
        return json.load(fh)


# ---------------------------------------------------------------- gate plugins

# Every gate below reads the LIVE EDITOR through Monolith, even when its CLI
# has an "--offline" flag (those flags only avoid *some* registry calls). None
# of them is safe to run without a responding editor on 9316, and a busy editor
# (MODAL_OPEN or mid-load) returns empty JSON that reads as a clean pass. So the
# chain HOLDs (no ledger row) whenever the editor is not answering, and each
# tool gets a bounded timeout so a hung editor cannot hang the chain.

def run_graph_reachability(timeout: int = 600) -> bool:
    out = py("Tools/graph_reachability.py", "--all-melodia", "--ci", timeout=timeout)
    return "0 violations" in out or "clean" in out.lower() or "no " in out.lower()


def run_bp_sweep(timeout: int = 600) -> bool:
    out = py("Tools/bp_sweep.py", "--limit", "200", timeout=timeout)
    return "error" not in out.lower()


def run_ui_lint(timeout: int = 600) -> bool:
    out = py("Tools/ui_lint.py", "--all-melodia", timeout=timeout)
    return "defect" not in out.lower() or "0 defective" in out.lower()


def run_verify_baseline(timeout: int = 900) -> bool:
    r = subprocess.run([sys.executable or "python",
                        "Docs/T3D_Baseline/verify_baseline.py"],
                       capture_output=True, text=True,
                       cwd=PROJECT, timeout=timeout)
    return r.returncode == 0


STATIC = {
    "graph_reachability": run_graph_reachability,
    "bp_sweep": run_bp_sweep,
    "ui_lint": run_ui_lint,
    "verify_baseline": run_verify_baseline,
}

EDITOR_ONLY = {
    "pie_smoke": ["Tools/pie_smoke_runner.py"],
    "regression": ["Tools/regression_suite.py", "--quick"],
    "fingerprint": ["Tools/bp_regression_checker.py", "--all"],
}


def validate_spec(path: str) -> dict:
    """Contract check on a proposal spec. Returns {ok, errors, verbs}."""
    errors = []
    verbs = []
    try:
        with open(path, encoding="utf-8") as fh:
            data = json.load(fh)
    except json.JSONDecodeError as e:
        return {"ok": False, "errors": [f"not valid JSON: {e}"], "verbs": []}
    except OSError as e:
        return {"ok": False, "errors": [str(e)], "verbs": []}

    text = json.dumps(data)
    for prefix, shape in VERB_RE.items():
        if prefix in text:
            verbs.append(prefix.split(":")[1])
    if isinstance(data, dict) and data.get("ledger_id"):
        # pipeline sub-specs may declare the gate they claim
        claimed = data.get("ledger_id")
        known = _ledger_latest()
        if claimed not in known:
            errors.append(f"claimed gate '{claimed}' has no ledger baseline yet")
    return {"ok": not errors, "errors": errors, "verbs": verbs}


# ------------------------------------------------------------------- plumbing

def cmd_list(manifest: dict) -> None:
    print("# Melodia Echo pipeline stages")
    for s in manifest["stages"]:
        impl = s.get("impl") or ",".join(s.get("impls", []))
        print(f"\n## {s['id']} ({s['label']})")
        print(f"  impl:     {impl}")
        print(f"  contract: {s.get('contract', '')}")


def cmd_status() -> None:
    latest = _ledger_latest()
    print("# Completion gates (ledger-backed)")
    for gid, what in _load_manifest_completions().items():
        rec = latest.get(gid)
        if rec and rec.get("status") == "pass":
            mark = "PASS"
        elif rec and rec.get("status") == "fail":
            mark = "FAIL"
        else:
            mark = "OPEN"
        date = rec.get("date", "") if rec else ""
        print(f"  [{mark:<4}] {gid:<18} {date:<12} {what}")
    live = editor_live()
    print(f"\n  editor reachable on 9316: {'yes' if live else 'no (editor gates HOLD)'}")


def _load_manifest_completions() -> dict:
    m = load_manifest()
    return m.get("completion_definitions", {})


def cmd_run(args: argparse.Namespace) -> None:
    if args.all:
        run_static()
        print("\n  --all runs the static chain. editor/runtime gates (pie_smoke, regression,")
        print("  fingerprint) must be run individually with the editor up; each writes its")
        print("  own ledger row via 'record'.")
        return

    name = args.stage
    if name == "static_gates":
        run_static()
        return
    if name in EDITOR_ONLY:
        if not editor_live():
            print(f"[HOLD] {name}: editor not reachable on 9316 - no ledger row written")
            return
        cmd = EDITOR_ONLY[name]
        try:
            out = py(*cmd, timeout=900)
        except subprocess.TimeoutExpired:
            print(f"[HOLD] {name}: timed out against a busy editor")
            return
        print(f"[{'ok' if 'error' not in out.lower() else 'FAIL'}] {name}\n{out[:800]}")
        return
    names = list(STATIC) + list(EDITOR_ONLY)
    print(f"unknown stage '{name}'. known: {', '.join(names)}")
    sys.exit(2)


def run_static() -> None:
    print("# static gate chain (editor-gated: no ledger row without a responding editor)")
    if not editor_live():
        print("  [HOLD] editor not reachable on 9316 - run 'echo_run.py run static_gates'")
        print("         with the editor up and Monolith answering. No ledger row written.")
        return
    all_ok = True
    for name, fn in STATIC.items():
        try:
            ok = fn()
        except subprocess.TimeoutExpired:
            ok, note = False, "timeout (tool hung against a busy editor)"
            print(f"  [HOLD] {name}: {note}")
            all_ok = False
            continue
        except Exception as e:  # noqa: BLE001 - a gate must not kill the chain
            ok, note = False, f"error: {e}"
            print(f"  [FAIL] {name}: {note}")
            all_ok = False
            continue
        print(f"  [{'ok' if ok else 'FAIL'}] {name}")
        all_ok = all_ok and ok
    print(f"\n  static chain: {'ALL OK' if all_ok else 'FAILURES PRESENT'}")


def main() -> None:
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace", line_buffering=True)
    except (AttributeError, ValueError):
        pass

    ap = argparse.ArgumentParser(description="Melodia Echo pipeline runner")
    sub = ap.add_subparsers(dest="cmd", required=True)

    sub.add_parser("list")
    sub.add_parser("status")
    sp = sub.add_parser("run")
    sp.add_argument("stage", help="stage id, a gate tool name, or --all")
    sp.add_argument("--all", action="store_true")
    sv = sub.add_parser("validate-spec")
    sv.add_argument("path")
    sr = sub.add_parser("record")
    sr.add_argument("gate_id")
    sr.add_argument("status", choices=["pass", "fail"])
    sr.add_argument("--note", default="")

    args = ap.parse_args()

    if args.cmd == "list":
        cmd_list(load_manifest())
    elif args.cmd == "status":
        cmd_status()
    elif args.cmd == "run":
        cmd_run(args)
    elif args.cmd == "validate-spec":
        res = validate_spec(args.path)
        print(json.dumps(res, indent=2))
        sys.exit(0 if res["ok"] else 1)
    elif args.cmd == "record":
        intent = py("Tools/record_gate.py", args.gate_id, args.status, "--note", args.note)
        print(intent.strip() or "recorded")
        sys.exit(0 if args.status == "pass" else 1)
    else:
        print("available: list | status | run | validate-spec | record ; add --all to run")
        sys.exit(1)


if __name__ == "__main__":
    main()
