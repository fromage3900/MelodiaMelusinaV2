#!/usr/bin/env python3
"""
wire_melusina_idle.py - fix Melusina's idle state (repoint to the verified arms-down idle).

Uses Monolith MCP convention: namespace as method, action in args dict.
"""
from __future__ import annotations

import argparse
import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from mcp_client import monolith  # noqa: E402

ABP = "/Game/Melodia/Characters/Melusina/ABP_Melusina_Current"
STATE_MACHINE = "MelusinaLocomotion"
AUDIT_DIR = Path(__file__).resolve().parent.parent / "Saved" / "Audit"

OLD_IDLE = "/Game/Melodia/Characters/Melusina/Animations/Locomotion/A_Melusina_Idle_Mocap_RootX"
# Temporary non-bind fallback only. The authored MUAL target is rejected: its sampled
# frames are the skeleton bind pose. Do not promote this fallback as final art without
# a fresh visual approval; the current lane still needs a production-quality idle.
NEW_IDLE = "/Game/Melodia/Characters/Melusina/Animations/Locomotion/A_Melusina_Idle"


def anim(action, params=None, timeout=60):
    """Call animation_query namespace."""
    args = {"action": action, **(params or {})}
    return monolith("animation_query", args, timeout)


def bp(action, params=None, timeout=60):
    """Call blueprint_query namespace."""
    args = {"action": action, **(params or {})}
    return monolith("blueprint_query", args, timeout)


def require_editor():
    raw = monolith("monolith_status", {})
    if isinstance(raw, str) and raw.startswith("ERROR"):
        raise RuntimeError(f"Monolith unreachable: {raw}")
    return raw


def write_report(name, data):
    AUDIT_DIR.mkdir(parents=True, exist_ok=True)
    data.setdefault("generated_at", datetime.now(timezone.utc).isoformat())
    path = AUDIT_DIR / name
    path.write_text(json.dumps(data, indent=2), encoding="utf-8")
    print(f"  report -> {path}")
    return path


def get_idle_state_binding():
    raw = anim("get_state_machines", {"asset_path": ABP})
    if isinstance(raw, str):
        try:
            sm = json.loads(raw)
        except json.JSONDecodeError:
            return None
    else:
        sm = raw
    machines = sm.get("state_machines") or sm.get("machines") or []
    for machine in machines:
        if machine.get("name") != STATE_MACHINE:
            continue
        for state in machine.get("states") or []:
            if isinstance(state, dict) and state.get("name") == "Idle":
                return state
    return None


def plan_fix():
    require_editor()
    current = get_idle_state_binding()
    report = {
        "kind": "melusina_idle_fix_plan",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "dry_run": True,
        "current_state": current,
        "target_animation": NEW_IDLE,
        "needs_fix": current is None or current.get("animation") != NEW_IDLE,
    }
    write_report("melusina_idle_fix_plan.json", report)
    print(f"[PLAN] Current idle: {current.get('animation') if current else 'NOT FOUND'}")
    print(f"[PLAN] Target idle:  {NEW_IDLE}")
    print(f"[PLAN] Needs fix:    {report['needs_fix']}")
    return report


def apply_fix():
    print("[APPLY] fixing idle state binding")
    require_editor()

    before = get_idle_state_binding()
    report = {
        "kind": "melusina_idle_fix_apply",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "dry_run": False,
        "binding_before": before,
    }

    # 1. Rebind animation
    print("  animation_query: set_state_animation [rebind_idle]")
    result = anim("set_state_animation", {
        "asset_path": ABP,
        "machine_name": STATE_MACHINE,
        "state_name": "Idle",
        "anim_asset_path": NEW_IDLE,
        "loop": True,
    })
    report["rebind_result"] = result

    # 2. Compile
    print("  blueprint_query: compile_blueprint [compile]")
    result = bp("compile_blueprint", {"asset_path": ABP})
    report["compile_result"] = result

    # 3. Save
    print("  blueprint_query: save_asset [save]")
    result = bp("save_asset", {"asset_path": ABP})
    report["save_result"] = result

    # Verify artifact
    uasset = (Path(__file__).resolve().parent.parent / "Content" /
              ABP.replace("/Game/", "").replace("/", os.sep)).with_suffix(".uasset")
    if uasset.exists():
        mtime = datetime.fromtimestamp(uasset.stat().st_mtime, timezone.utc)
        age_s = (datetime.now(timezone.utc) - mtime).total_seconds()
        report["uasset_mtime"] = mtime.isoformat()
        report["uasset_written_this_run"] = age_s < 600
        if age_s >= 600:
            print(f"\n  WARNING: {uasset.name} is {age_s/3600:.1f}h old - work may be in-memory only")
        else:
            print(f"\n  disk write confirmed: {uasset.name} @ {mtime:%H:%M:%S}Z")

    after = get_idle_state_binding()
    report["binding_after"] = after
    report["ok"] = after is not None and after.get("animation") == NEW_IDLE

    write_report("melusina_idle_fix_apply.json", report)
    print(f"\n  Idle state now bound to: {after.get('animation') if after else 'UNKNOWN'}")
    return report


def verify_fix():
    require_editor()
    current = get_idle_state_binding()
    report = {
        "kind": "melusina_idle_fix_verify",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "current_state": current,
        "expected_animation": NEW_IDLE,
        "ok": current is not None and current.get("animation") == NEW_IDLE,
    }
    write_report("melusina_idle_fix_verify.json", report)
    if report["ok"]:
        print(f"[VERIFY OK] Idle bound to: {current.get('animation')}")
    else:
        print(f"[VERIFY FAIL] Idle bound to: {current.get('animation')}")
    return report


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--plan", action="store_true")
    ap.add_argument("--apply", action="store_true")
    ap.add_argument("--verify", action="store_true")
    args = ap.parse_args()
    if not any(vars(args).values()):
        ap.print_help()
        return 0
    try:
        if args.plan: plan_fix()
        if args.apply: apply_fix()
        if args.verify: verify_fix()
    except Exception as e:
        print(f"ERROR: {e}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
