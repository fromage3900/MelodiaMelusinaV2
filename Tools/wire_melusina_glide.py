#!/usr/bin/env python3
"""
wire_melusina_glide.py — add Glide state to ABP_Melusina_Current's state machine.

THE FEATURE
-----------
Melusina is a magical girl — she needs a glide/float locomotion state that feels
like flying. The ABP already has:
  - bIsGliding variable (set by BP_MelusinaJRPGCharacter)
  - Speed, Velocity, Acceleration, bIsMoving, WasInAir variables
  - Ground locomotion states (Idle, Locomotion, JumpWindup, Airborne, Land)

THE FIX
-------
Add a Glide state that:
  - Plays a glide animation (in-place float)
  - Entry: bIsGliding == true (from any state)
  - Exit: bIsGliding == false → Land (airborne), Idle (grounded, stopped),
    or Locomotion (grounded, moving)

SOURCE
------
  - Glide loop: A_Mocap_LittleDance_001 (Mocap/, placeholder) or
    A_Q_Melusina_Sprint_Loop (QuaterniusRetargeted/, if registry is fixed)
  - The ABP already has bIsGliding variable

USAGE
-----
    # Dry run
    python Tools/wire_melusina_glide.py --plan

    # Apply (requires editor)
    python Tools/wire_melusina_glide.py --apply

    # Verify after
    python Tools/wire_melusina_glide.py --verify
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
from build_melusina_locomotion_stack import (  # noqa: E402
    ABP, AUDIT_DIR, STATE_MACHINE, MonolithError, anim, bp,
    require_editor, write_report,
)

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

# Placeholder glide animation (will be replaced with proper authored clip)
# A_Mocap_LittleDance_001 is a gentle, floaty motion that reads as magical girl glide
GLIDE_ANIM = "/Game/Melodia/Characters/Melusina/Animations/Mocap/A_Mocap_LittleDance_001"

# Alternative (if Quaternius packages become loadable):
# GLIDE_ANIM = "/Game/Melodia/Characters/Melusina/Animations/QuaterniusRetargeted/A_Q_Melusina_Sprint_Loop"

GLIDE_STATE_NAME = "Glide"
GLIDE_STATE_POSITION = [400, 160]  # position in the state machine graph

# ---------------------------------------------------------------------------
# Actions
# ---------------------------------------------------------------------------

def get_live_state_names() -> set[str]:
    """Read live ABP state names."""
    sm = anim("get_state_machines", {"asset_path": ABP})
    names = set()
    machines = sm.get("state_machines") or sm.get("machines") or []
    for machine in machines:
        if machine.get("name") != STATE_MACHINE:
            continue
        for state in machine.get("states") or []:
            if isinstance(state, dict) and state.get("name"):
                names.add(state.get("name"))
    return names


def plan_glide() -> dict:
    """Dry run — show what would change."""
    require_editor()

    existing = get_live_state_names()
    report = {
        "kind": "melusina_glide_plan",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "dry_run": True,
        "existing_states": sorted(existing),
    }

    already_exists = GLIDE_STATE_NAME in existing
    report["glide_state_exists"] = already_exists

    if already_exists:
        report["action"] = f"Glide state already exists — would only update animation binding"
        report["steps"] = [
            f"1. set_state_animation: Glide → {GLIDE_ANIM}",
        ]
    else:
        report["action"] = f"Add Glide state + wire transitions"
        report["steps"] = [
            f"1. add_state_to_machine: Glide @ {GLIDE_STATE_POSITION}",
            f"2. set_state_animation: Glide → {GLIDE_ANIM}",
            f"3. add_transition: Idle → Glide (rule: bIsGliding)",
            f"4. add_transition: Locomotion → Glide (rule: bIsGliding)",
            f"5. add_transition: Glide → Idle (rule: !bIsGliding AND Speed<10)",
            f"6. add_transition: Glide → Locomotion (rule: !bIsGliding AND Speed>10)",
            f"7. add_transition: Glide → Airborne (rule: !bIsGliding AND !bIsOnGround)",
            f"8. compile ABP",
            f"9. save ABP",
        ]

    report["ok"] = True
    write_report("melusina_glide_plan.json", report)

    print(f"[PLAN] Existing states: {sorted(existing)}")
    print(f"[PLAN] Glide exists:    {already_exists}")
    print(f"[PLAN] Steps: {len(report['steps'])}")
    for step in report["steps"]:
        print(f"  {step}")

    return report


def apply_glide() -> dict:
    """Apply — add Glide state + wire transitions."""
    mode = "APPLY"
    print(f"[{mode}] adding Glide state to {STATE_MACHINE}")

    require_editor()

    existing = get_live_state_names()
    report = {
        "kind": "melusina_glide_apply",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "dry_run": False,
        "existing_states_before": sorted(existing),
    }

    steps = []

    # 1. Add Glide state (if not exists)
    if GLIDE_STATE_NAME not in existing:
        steps.append({
            "label": "add_glide_state",
            "tool": "animation_query",
            "action": "add_state_to_machine",
            "params": {
                "asset_path": ABP,
                "machine_name": STATE_MACHINE,
                "state_name": GLIDE_STATE_NAME,
                "position_x": GLIDE_STATE_POSITION[0],
                "position_y": GLIDE_STATE_POSITION[1],
            },
        })

    # 2. Bind animation
    steps.append({
        "label": "bind_glide_anim",
        "tool": "animation_query",
        "action": "set_state_animation",
        "params": {
            "asset_path": ABP,
            "machine_name": STATE_MACHINE,
            "state_name": GLIDE_STATE_NAME,
            "anim_asset_path": GLIDE_ANIM,
            "loop": True,
        },
    })

    # 3. Transitions (only add if they don't exist)
    transitions = [
        {
            "label": "trans_idle_to_glide",
            "from": "Idle", "to": GLIDE_STATE_NAME,
            "rule": {"kind": "bool", "variable": "bIsGliding"},
            "blend": 0.2,
        },
        {
            "label": "trans_loco_to_glide",
            "from": "Locomotion", "to": GLIDE_STATE_NAME,
            "rule": {"kind": "bool", "variable": "bIsGliding"},
            "blend": 0.2,
        },
        {
            "label": "trans_glide_to_idle",
            "from": GLIDE_STATE_NAME, "to": "Idle",
            "rule": {"kind": "expression", "expression": "!bIsGliding AND Speed < 10"},
            "blend": 0.3,
        },
        {
            "label": "trans_glide_to_loco",
            "from": GLIDE_STATE_NAME, "to": "Locomotion",
            "rule": {"kind": "expression", "expression": "!bIsGliding AND Speed > 10"},
            "blend": 0.2,
        },
        {
            "label": "trans_glide_to_airborne",
            "from": GLIDE_STATE_NAME, "to": "Airborne",
            "rule": {"kind": "expression", "expression": "!bIsGliding AND WasInAir"},
            "blend": 0.15,
        },
    ]

    for t in transitions:
        steps.append({
            "label": t["label"] + "_add",
            "tool": "animation_query",
            "action": "add_transition",
            "params": {
                "asset_path": ABP,
                "machine_name": STATE_MACHINE,
                "from_state": t["from"],
                "to_state": t["to"],
            },
        })
        steps.append({
            "label": t["label"] + "_rule",
            "tool": "animation_query",
            "action": "set_transition_rule",
            "params": {
                "asset_path": ABP,
                "machine_name": STATE_MACHINE,
                "from_state": t["from"],
                "to_state": t["to"],
                "rule": t["rule"],
            },
        })

    # 4. Compile + save
    steps.append({
        "label": "compile",
        "tool": "blueprint_query",
        "action": "compile_blueprint",
        "params": {"asset_path": ABP},
    })
    steps.append({
        "label": "save",
        "tool": "blueprint_query",
        "action": "save_asset",
        "params": {"asset_path": ABP},
    })

    report["steps"] = []
    for s in steps:
        print(f"  {s['tool']}:{s['action']}  [{s['label']}]")
        try:
            result = monolith(f"{s['tool']}:{s['action']}", s["params"], timeout=60)
            report["steps"].append({**s, "result": result, "ok": True})
        except MonolithError as e:
            report["steps"].append({**s, "error": str(e), "ok": False})
            report["aborted_at"] = s["label"]
            write_report("melusina_glide_apply.json", report)
            raise SystemExit(f"ABORTED at [{s['label']}]: {e}")

    # Verify artifact
    uasset = (Path(__file__).resolve().parent.parent / "Content" /
              ABP.replace("/Game/", "").replace("/", os.sep)).with_suffix(".uasset")
    if uasset.exists():
        mtime = datetime.fromtimestamp(uasset.stat().st_mtime, timezone.utc)
        age_s = (datetime.now(timezone.utc) - mtime).total_seconds()
        report["uasset_mtime"] = mtime.isoformat()
        report["uasset_written_this_run"] = age_s < 600
        if age_s >= 600:
            print(f"\n  WARNING: {uasset.name} is {age_s/3600:.1f}h old — work may be in-memory only")
        else:
            print(f"\n  disk write confirmed: {uasset.name} @ {mtime:%H:%M:%S}Z")

    after = get_live_state_names()
    report["existing_states_after"] = sorted(after)
    report["ok"] = GLIDE_STATE_NAME in after

    write_report("melusina_glide_apply.json", report)
    print(f"\n  States after: {sorted(after)}")
    return report


def verify_glide() -> dict:
    """Verify — prove the Glide state landed."""
    require_editor()

    existing = get_live_state_names()
    report = {
        "kind": "melusina_glide_verify",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "existing_states": sorted(existing),
        "glide_state_exists": GLIDE_STATE_NAME in existing,
        "ok": GLIDE_STATE_NAME in existing,
    }

    write_report("melusina_glide_verify.json", report)

    if report["ok"]:
        print(f"[VERIFY OK] Glide state present in {STATE_MACHINE}")
    else:
        print(f"[VERIFY FAIL] Glide state NOT found. States: {sorted(existing)}")

    return report


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--plan", action="store_true", help="dry run")
    ap.add_argument("--apply", action="store_true", help="apply (requires editor)")
    ap.add_argument("--verify", action="store_true", help="verify")
    args = ap.parse_args()

    if not any(vars(args).values()):
        ap.print_help()
        return 0

    try:
        if args.plan:
            plan_glide()
        if args.apply:
            apply_glide()
        if args.verify:
            verify_glide()
    except MonolithError as e:
        print(f"\nERROR: {e}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
