#!/usr/bin/env python3
"""
record_gate.py — PIE gate recording tool.

Appends dated pass/fail observations to Saved/gate_ledger.json and optionally
annotates the scope doc. Integrates with Monolith MCP for session tracking.

Usage:
    python Tools/record_gate.py <gate-id> pass|fail --note "..."
    python Tools/record_gate.py --list
    python Tools/record_gate.py --report
"""
from __future__ import annotations

import argparse
import json
import sys
import time
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

SAVED_DIR = Path(__file__).resolve().parent.parent / "Saved"
LEDGER_PATH = SAVED_DIR / "gate_ledger.json"

KNOWN_GATES = [
    "dialogue_visible",
    "travel_allowlist",
    "battle_encounter",
    "save_create",
    "save_load",
    "victory_result",
    "defeat_result",
    "fled_result",
    "rhythm_seam_a",
    "rhythm_seam_b",
    "pie_smoke",
    "package_build",
    "runtime",
    "repeat_consume",
    "hair_emissive",
    "iris_weighting",
    "jump_windup",
    "sprint_speed",
    "material_slots",
    "tp_melusina",
    "waterfx",
    "water_hair_material",
    "material_switches",
    "frontpanel_textures",
    "graph_reachability",
    "ui_lint",
    "save_system",
    "reward_restore",
    "package_launch",
    "static_gates",
]


def _load_ledger() -> dict:
    if LEDGER_PATH.exists():
        try:
            return json.loads(LEDGER_PATH.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            pass
    return {"gates": [], "sessions": {}}


def _save_ledger(ledger: dict) -> None:
    SAVED_DIR.mkdir(parents=True, exist_ok=True)
    LEDGER_PATH.write_text(json.dumps(ledger, indent=2, default=str), encoding="utf-8")


def _session_id(ledger: dict) -> str:
    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    for sid, sdata in ledger.get("sessions", {}).items():
        if sdata.get("date") == today:
            return sid
    sid = f"session-{uuid.uuid4().hex[:8]}"
    ledger.setdefault("sessions", {})[sid] = {"date": today, "gates_passed": [], "gates_failed": []}
    return sid


def record_gate(gate_id: str, status: str, note: str = "") -> dict:
    if gate_id not in KNOWN_GATES:
        print(f"Warning: '{gate_id}' is not in the known gate list: {KNOWN_GATES}", file=sys.stderr)

    ledger = _load_ledger()
    now = datetime.now(timezone.utc)
    sid = _session_id(ledger)

    entry = {
        "id": gate_id,
        "status": status,
        "date": now.strftime("%Y-%m-%d"),
        "time": now.strftime("%H:%M:%S"),
        "note": note,
        "session": sid,
    }
    ledger["gates"].append(entry)

    session = ledger["sessions"].get(sid, {})
    target_list = session.setdefault("gates_passed" if status == "pass" else "gates_failed", [])
    if gate_id not in target_list:
        target_list.append(gate_id)

    _save_ledger(ledger)
    print(f"Recorded {gate_id} -> {status} [{entry['date']} {entry['time']}]")
    return entry


def list_gates() -> None:
    ledger = _load_ledger()
    gates = ledger.get("gates", [])
    latest: dict[str, dict] = {}
    for g in gates:
        latest[g["id"]] = g

    print(f"{'Gate ID':<25} {'Status':<8} {'Date':<12} {'Note'}")
    print("-" * 80)
    for gid in KNOWN_GATES:
        rec = latest.get(gid)
        if rec:
            status = rec["status"]
            date = rec["date"]
            note = rec.get("note", "")[:50]
        else:
            status = "—"
            date = "—"
            note = "not recorded"
        print(f"{gid:<25} {status:<8} {date:<12} {note}")


def generate_report() -> str:
    ledger = _load_ledger()
    gates = ledger.get("gates", [])
    sessions = ledger.get("sessions", {})
    latest: dict[str, dict] = {}
    for g in gates:
        latest[g["id"]] = g

    passed = sum(1 for g in gates if g["status"] == "pass")
    failed = sum(1 for g in gates if g["status"] == "fail")
    total = len(gates)

    lines = [
        "# Gate Ledger Report",
        "",
        f"**Generated:** {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S UTC')}",
        f"**Total records:** {total}  **Passed:** {passed}  **Failed:** {failed}",
        "",
        "## Gate Summary",
        "",
        "| Gate ID | Status | Date | Note |",
        "|---------|--------|------|------|",
    ]
    for gid in KNOWN_GATES:
        rec = latest.get(gid)
        if rec:
            lines.append(f"| {gid} | {rec['status']} | {rec['date']} | {rec.get('note', '')} |")
        else:
            lines.append(f"| {gid} | — | — | not recorded |")

    lines += ["", "## Sessions", ""]
    for sid, sdata in sessions.items():
        p = ", ".join(sdata.get("gates_passed", [])) or "—"
        f_ = ", ".join(sdata.get("gates_failed", [])) or "—"
        lines.append(f"- **{sid}** ({sdata.get('date', '?')})")
        lines.append(f"  - Passed: {p}")
        lines.append(f"  - Failed: {f_}")

    report = "\n".join(lines)
    report_path = SAVED_DIR / "gate_ledger_report.md"
    report_path.write_text(report, encoding="utf-8")
    print(f"Report written to {report_path}")
    return report


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Record a PIE gate observation.")
    p.add_argument("gate_id", nargs="?", help="Gate ID from known list")
    p.add_argument("status", nargs="?", choices=["pass", "fail"], help="pass or fail")
    p.add_argument("--note", default="", help="Observation note")
    p.add_argument("--list", action="store_true", help="Show all known gates and current status")
    p.add_argument("--report", action="store_true", help="Generate markdown summary")
    return p.parse_args(argv)


def main() -> None:
    args = parse_args()

    if args.list:
        list_gates()
        return
    if args.report:
        generate_report()
        return
    if args.gate_id and args.status:
        record_gate(args.gate_id, args.status, note=args.note)
        return

    print("Usage: python Tools/record_gate.py <gate-id> pass|fail --note \"...\"")
    print("       python Tools/record_gate.py --list")
    print("       python Tools/record_gate.py --report")
    sys.exit(1)


if __name__ == "__main__":
    main()
