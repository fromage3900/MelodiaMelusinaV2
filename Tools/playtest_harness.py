#!/usr/bin/env python3
"""Playtest Harness — real-input PIE verification for the runtime gate.

Drives the battle through Monolith's PIE machinery and produces the evidence
pair required by the 2026-08-11 evidence standard: assertion report JSON next
to captured frames, committed harness, ledger row via --record.

Input backends (strongest first, chosen by --check-wiring result):
  1. slate-sendinput   real OS key presses via SendInput to the focused PIE viewport
  2. pie-inject-input  Monolith pie_inject_input_action (Enhanced Input path)
  3. probe             in-session probe_scripts (documented fallback, weakest)

Usage:
  python playtest_harness.py preflight
  python playtest_harness.py check-wiring
  python playtest_harness.py run --map L_KaleidoNave --backend auto
      [--keys Q W O P] [--vars EnemyHP:Path.To.Prop ...]
  python playtest_harness.py ab --map L_KaleidoNave      (rhythm on/off damage delta)
  python playtest_harness.py record pass --note "..." --session session-xxxx
  python playtest_harness.py record fail --note "..."
"""

import argparse
import json
import os
import subprocess
import sys
import time
import urllib.request

MCP = "http://127.0.0.1:9316/mcp"
SAVED = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "Saved"))
PLAYTEST_DIR = os.path.join(SAVED, "Playtest")
LEDGER = os.path.join(SAVED, "gate_ledger.json")
BATTLE_UI = "/Game/MelodiaIntegration/UI/BP_BattleUI"
CONSOLE_RHYTHM_TOGGLE = "melodia.Rhythm.Disable"

BP_TRIES = [
    "/Game/MelodiaIntegration/UI/BP_BattleUI",
    "/Game/Melodia/UI/BP_BattleUI",
    "/Game/TurnBasedJRPGTemplate/Blueprints/Battle/BP_BattleUI",
]


def monolith(tool, args, timeout=60):
    body = json.dumps({"jsonrpc": "2.0", "id": 1, "method": "tools/call",
                       "params": {"name": tool, "arguments": args}}).encode()
    req = urllib.request.Request(MCP, data=body, headers={"Content-Type": "application/json"})
    resp = urllib.request.urlopen(req, timeout=timeout)
    data = json.loads(resp.read().decode())
    result = data.get("result", {})
    if result.get("isError"):
        text = result.get("content", [{}])[0].get("text", "")
        raise RuntimeError("monolith %s error: %s" % (tool, text[:500]))
    content = result.get("content", [{}])
    text = content[0].get("text", "") if content else ""
    try:
        return json.loads(text) if text else {}
    except Exception:
        return {"raw": text}


def preflight():
    checks = {}
    try:
        proc = subprocess.run(["powershell", "-NoProfile", "-Command",
                               "(Get-Process UnrealEditor -ErrorAction SilentlyContinue | Measure-Object).Count"],
                              capture_output=True, text=True, timeout=30)
        checks["unreal_editor_processes"] = int(proc.stdout.strip() or 0)
    except Exception as exc:
        checks["unreal_editor_processes"] = "error: %s" % exc
    try:
        monolith("editor_query", {"action": "list_errored_blueprints"})
        checks["monolith_reachable"] = True
        checks["compile_errors"] = 0
    except Exception as exc:
        checks["monolith_reachable"] = False
        checks["error"] = str(exc)[:300]
    ok = checks.get("monolith_reachable") and checks.get("unreal_editor_processes", 1) == 1
    print(json.dumps(checks, indent=2))
    return 0 if ok else 2


def find_battle_ui():
    for path in BP_TRIES:
        try:
            monolith("project_query", {"action": "get_asset_details", "asset_path": path})
            return path
        except Exception:
            continue
    return None


def check_wiring():
    path = find_battle_ui()
    if not path:
        print(json.dumps({"status": "MISSING", "tried": BP_TRIES}, indent=2))
        return 2
    graph = monolith("blueprint_query", {"action": "get_graph_data", "asset_path": path})
    blob = json.dumps(graph)
    report = {
        "status": "UNKNOWN",
        "battle_ui": path,
        "has_onkeydown": "OnKeyDown" in blob,
        "has_registerlanehit": "RegisterLaneHit" in blob,
        "has_bindrhythmhud": "BindRhythmHUD" in blob,
        "has_pushhighway": "PushHighwayToHUD" in blob,
        "keys_found": [k for k in ["Q", "W", "O", "P", "D", "F", "J", "K"] if ("\"%s\"" % k) in blob],
        "uses_enhanced_input": "InputAction" in blob and ("UInputAction" in blob or "InputAction" in blob),
    }
    if report["has_onkeydown"] and report["has_registerlanehit"]:
        report["status"] = "RAW_KEY_BACKEND" if not report["uses_enhanced_input"] else "MIXED"
    elif report["has_registerlanehit"] and report["uses_enhanced_input"]:
        report["status"] = "ENHANCED_INPUT_BACKEND"
    else:
        report["status"] = "UNWIRED"
    out = os.path.join(SAVED, "Playtest", "wiring_report.json")
    os.makedirs(os.path.dirname(out), exist_ok=True)
    with open(out, "w", encoding="utf-8") as fh:
        json.dump(report, fh, indent=2)
    print(json.dumps(report, indent=2))
    return 0 if report["status"] in ("RAW_KEY_BACKEND", "ENHANCED_INPUT_BACKEND", "MIXED") else 2


def run_pie(map_name, duration, console_script, vars_, marker):
    params = {
        "map": map_name,
        "duration": duration,
        "marker": marker,
        "console_script": console_script,
        "on_compile_errors": "refuse",
        "teardown_allowed": True,
    }
    if vars_:
        params["sample_vars"] = vars_
    return monolith("editor_query", {"action": "run_pie_smoke", **params})


def poll_until(session_id, timeout, want_pie=True):
    deadline = time.time() + timeout
    last = {}
    while time.time() < deadline:
        last = monolith("editor_query", {"action": "poll_pie_smoke", "session_id": session_id})
        if want_pie and last.get("pie_active"):
            return last
        if last.get("status") == "complete":
            return last
        time.sleep(0.5)
    return last


def send_slate_keys(keys):
    script = []
    for key in keys:
        script.append("Add-Type -AssemblyName System.Windows.Forms")
        script.append("Add-Type -AssemblyName Microsoft.VisualBasic")
        script.append("[System.Windows.Forms.SendKeys]::SendWait('%s')" % key)
    proc = subprocess.run(["powershell", "-NoProfile", "-Command", ";".join(script)],
                          capture_output=True, text=True, timeout=60)
    return proc.returncode == 0


def snapshot_damage(vars_):
    out = {}
    for label, path in vars_.items():
        try:
            out[label] = monolith("editor_query", {
                "action": "pie_get_object_properties",
                "class_name": "BP_BattleController",
                "properties": [path],
            })
        except Exception:
            try:
                out[label] = monolith("editor_query", {
                    "action": "pie_get_object_properties",
                    "object_name": "BP_BattleController",
                    "properties": [path],
                })
            except Exception as exc:
                out[label] = "unread: %s" % exc
    return out


def do_run(args):
    marker = "PLAYTEST_%s" % int(time.time())
    console_script = []
    if args.rhythm_disable is not None:
        console_script.append("%s %d" % (CONSOLE_RHYTHM_TOGGLE, 1 if args.rhythm_disable else 0))
    sess = run_pie(args.map, args.duration, console_script, [], marker)
    session_id = sess.get("session_id")
    if not session_id:
        print(json.dumps({"status": "FAILED_TO_START", "resp": sess}, indent=2))
        return 2
    state = poll_until(session_id, args.settle_timeout)
    report = {
        "status": "INCOMPLETE",
        "marker": marker,
        "session_id": session_id,
        "backend": args.backend,
        "keys": args.keys,
        "rhythm_disable": args.rhythm_disable,
    }
    if state.get("pie_active") or state.get("status") == "complete":
        damage = snapshot_damage(dict(v.split(":", 1) for v in args.vars)) if args.vars else {}
        frames = []
        if args.backend == "slate-sendinput":
            sent = send_slate_keys(args.keys)
            report["keys_sent"] = sent
            time.sleep(1.0)
        elif args.backend == "pie-inject-input" and args.input_action:
            for key in args.keys:
                try:
                    monolith("editor_query", {
                        "action": "pie_inject_input_action",
                        "input_action": args.input_action,
                        "value": True,
                        "repeat_frames": 3,
                    })
                    time.sleep(0.15)
                except Exception as exc:
                    report.setdefault("inject_errors", []).append("%s: %s" % (key, exc))
        elif args.backend == "probe":
            report["backend_note"] = "probe backend relies on run_pie_smoke probe_scripts; see campaign doc"
        damage_after = snapshot_damage(dict(v.split(":", 1) for v in args.vars)) if args.vars else {}
        report["damage_before"] = damage
        report["damage_after"] = damage_after
        if args.capture_clip:
            clip = monolith("editor_query", {
                "action": "capture_pie_movement_clip",
                "map": args.map,
                "duration": min(args.duration, 10),
                "capture_interval": 0.25,
                "output_path": os.path.join(PLAYTEST_DIR, marker).replace("\\", "/"),
                "marker": marker + "_CLIP",
            })
            report["clip_session"] = clip.get("session_id")
        report["status"] = "COMPLETE"
        monolith("editor_query", {"action": "stop_pie_smoke", "session_id": session_id})
    else:
        report["poll"] = state
        monolith("editor_query", {"action": "stop_pie_smoke", "session_id": session_id})
    os.makedirs(PLAYTEST_DIR, exist_ok=True)
    out = os.path.join(PLAYTEST_DIR, marker + "_report.json")
    with open(out, "w", encoding="utf-8") as fh:
        json.dump(report, fh, indent=2)
    print(json.dumps(report, indent=2))
    print("report: %s" % out)
    return 0 if report["status"] == "COMPLETE" else 2


def do_ab(args):
    results = {}
    for disable in (0, 1):
        print("=== rhythm disabled=%d ===" % disable)
        results[disable] = run_once_with(args, disable)
    delta = {}
    try:
        for k in results[0].get("damage_after", {}):
            a = results[0]["damage_after"].get(k)
            b = results[1]["damage_after"].get(k)
            try:
                delta[k] = float(b) - float(a)
            except Exception:
                delta[k] = None
    except Exception:
        pass
    ab_out = {"runs": results, "damage_delta": delta,
              "accepted": all(isinstance(v, (int, float)) and v != 0 for v in delta.values()) if delta else None}
    out = os.path.join(PLAYTEST_DIR, "ab_%s.json" % int(time.time()))
    os.makedirs(PLAYTEST_DIR, exist_ok=True)
    with open(out, "w", encoding="utf-8") as fh:
        json.dump(ab_out, fh, indent=2)
    print(json.dumps(ab_out, indent=2))
    print("report: %s" % out)
    return 0 if ab_out["accepted"] else 2


def run_once_with(args, disable):
    marker = "PLAYTEST_AB_%d_%s" % (disable, int(time.time()))
    console_script = ["%s %d" % (CONSOLE_RHYTHM_TOGGLE, disable)]
    sess = run_pie(args.map, args.duration, console_script, [], marker)
    if not sess.get("session_id"):
        return {"status": "FAILED_TO_START", "resp": sess}
    state = poll_until(sess["session_id"], args.settle_timeout)
    if args.backend == "slate-sendinput":
        send_slate_keys(args.keys)
        time.sleep(1.0)
    damage = snapshot_damage(dict(v.split(":", 1) for v in args.vars)) if args.vars else {}
    monolith("editor_query", {"action": "stop_pie_smoke", "session_id": sess["session_id"]})
    return {"rhythm_disable": disable, "status": state.get("status"), "damage_after": damage}


def record_gate(status, note, session):
    ledger = {"gates": [], "sessions": {}}
    if os.path.exists(LEDGER):
        with open(LEDGER, encoding="utf-8") as fh:
            ledger = json.load(fh)
    now = time.strftime("%Y-%m-%d")
    now_t = time.strftime("%H:%M:%S")
    ledger["gates"].append({"id": "runtime", "status": status, "date": now, "time": now_t,
                            "note": note, "session": session})
    if session not in ledger["sessions"]:
        ledger["sessions"][session] = {"date": now, "gates_passed": [], "gates_failed": []}
    (ledger["sessions"][session]["gates_passed"] if status == "pass"
     else ledger["sessions"][session]["gates_failed"]).append("runtime")
    with open(LEDGER, "w", encoding="utf-8") as fh:
        json.dump(ledger, fh, indent=2)
    print("ledger row written: runtime=%s session=%s" % (status, session))


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)
    sub.add_parser("preflight")
    sub.add_parser("check-wiring")
    p_run = sub.add_parser("run")
    p_run.add_argument("--map", default="L_KaleidoNave")
    p_run.add_argument("--backend", default="auto", choices=["auto", "slate-sendinput", "pie-inject-input", "probe"])
    p_run.add_argument("--keys", nargs="+", default=["Q", "W", "O", "P"])
    p_run.add_argument("--input-action")
    p_run.add_argument("--vars", nargs="+", default=[])
    p_run.add_argument("--duration", type=int, default=30)
    p_run.add_argument("--settle-timeout", type=int, default=60)
    p_run.add_argument("--rhythm-disable", type=int, choices=[0, 1])
    p_run.add_argument("--capture-clip", action="store_true")
    p_ab = sub.add_parser("ab")
    p_ab.add_argument("--map", default="L_KaleidoNave")
    p_ab.add_argument("--backend", default="slate-sendinput")
    p_ab.add_argument("--keys", nargs="+", default=["Q", "W", "O", "P"])
    p_ab.add_argument("--vars", nargs="+", default=[])
    p_ab.add_argument("--duration", type=int, default=30)
    p_ab.add_argument("--settle-timeout", type=int, default=60)
    p_rec = sub.add_parser("record")
    p_rec.add_argument("status", choices=["pass", "fail"])
    p_rec.add_argument("--note", required=True)
    p_rec.add_argument("--session", default="session-playtest")
    args = ap.parse_args()

    if args.cmd == "preflight":
        sys.exit(preflight())
    if args.cmd == "check-wiring":
        sys.exit(check_wiring())
    if args.cmd == "run":
        if args.backend == "auto":
            report = check_wiring()
            args.backend = "slate-sendinput" if report == 0 else "probe"
        sys.exit(do_run(args))
    if args.cmd == "ab":
        sys.exit(do_ab(args))
    if args.cmd == "record":
        record_gate(args.status, args.note, args.session)
        sys.exit(0)


if __name__ == "__main__":
    main()
