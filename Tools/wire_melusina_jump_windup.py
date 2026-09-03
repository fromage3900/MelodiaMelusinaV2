#!/usr/bin/env python3
"""
wire_melusina_jump_windup.py -- SpaceBar hold triggers the jump wind-up.

THE REQUIREMENT
---------------
The INITIAL HOLD of SpaceBar must trigger the wind-up animation. Owner-stated,
non-negotiable, and the single easiest thing here to get subtly wrong.

WHY THE OBVIOUS WIRING IS WRONG
-------------------------------
The reflex is to call Jump() on Pressed and let the AnimBP react to IsFalling. That
cannot produce an anticipation pose: by the time IsFalling is true she has already
left the ground, so the "wind-up" would play in mid-air, after the launch it was
supposed to precede. The crouch has to happen while she is still standing.

So the press sets a flag and does NOT launch. The launch comes from inside the
wind-up clip:

    Pressed  -> bJumpWindup = true          (no Jump() call -- this is the point)
             -> ABP enters JumpWindup, plays A_Q_Melusina_Jump_Start
             -> AnimNotify JumpLaunch fires mid-clip -> Jump()
             -> IsFalling goes true -> Airborne

    Released -> bJumpWindup = false
    OnLanded -> bJumpWindup = false          (covers a Released swallowed by a
                                              state change; without it a swallowed
                                              release latches her in the wind-up)

INPUT
-----
MelodiaTraversalJump is a legacy ActionMapping on SpaceBar
(Config/DefaultInput.ini:115), so it yields Pressed/Released exec pins directly.
No Enhanced Input / IMC work is required, and none should be added -- the stock JRPG
input authority owns this path.

WHY NOT T3D HERE
----------------
MONOLITH_GUIDE Recipe 16 is the right tool when a cluster has no first-class action,
but its step 1 requires a hand-captured clipboard payload from the editor. That is a
manual step and cannot be authored blind. blueprint_query exposes add_event_node /
add_node / connect_pins / set_pin_default, which build the same cluster with per-node
validation. If this proves too fiddly in practice, fall back to Recipe 16 and capture
the payload by hand -- see --emit-contract for the exact shape to wire.

USAGE
-----
    python Tools/wire_melusina_jump_windup.py --live-path
    python Tools/wire_melusina_jump_windup.py --emit-contract
    python Tools/wire_melusina_jump_windup.py --plan
    python Tools/wire_melusina_jump_windup.py --apply
"""
from __future__ import annotations

import argparse
import os
import subprocess
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from build_melusina_locomotion_stack import (  # noqa: E402
    ABP, AUDIT_DIR, MonolithError, bp, require_editor, write_report,
)

PAWN = "/Game/MelodiaIntegration/Blueprints/BP_MelusinaJRPGCharacter"
ACTION = "MelodiaTraversalJump"
FLAG = "bJumpWindup"
NOTIFY = "JumpLaunch"
GRAPH = "EventGraph"

CONTRACT = f"""\
BP_MelusinaJRPGCharacter :: {GRAPH}

  InputAction {ACTION} (SpaceBar, legacy ActionMapping)
    Pressed  --> Get Mesh --> Get Anim Instance --> Cast To ABP_Melusina_Current
                 --> Set {FLAG} = TRUE
                 (NO Jump() call on this pin)
    Released --> [same cast] --> Set {FLAG} = FALSE

  AnimNotify_{NOTIFY}   (forwarded from ABP_Melusina_Current)
             --> Jump()
             --> [cast] --> Set {FLAG} = FALSE

  Event OnLanded
             --> [cast] --> Set {FLAG} = FALSE

The cast result should be promoted to a variable and cached on BeginPlay rather than
re-cast on every press. Casting per-press works but runs a class check on the hot
input path for no reason.

VERIFY IN PIE:
  - tap Space          -> wind-up plays, then she launches
  - hold Space         -> wind-up plays on the PRESS, not on the release
  - re-press mid-clip  -> wind-up RESTARTS (JumpWindup is always_reset_on_entry)
  - land               -> {FLAG} is false; she does not latch in the crouch
"""


def live_path():
    """Recipe 16 step 0. Abort on ORPHAN/AMBIGUOUS before touching the graph."""
    script = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                          "bp_live_path.py")
    print(f"[live-path] {PAWN}")
    proc = subprocess.run([sys.executable, script, "BP_MelusinaJRPGCharacter"],
                          capture_output=True, text=True)
    out = (proc.stdout or "") + (proc.stderr or "")
    print(out.strip() or "(no output)")
    if "ORPHAN" in out.upper() or "AMBIGUOUS" in out.upper():
        raise SystemExit(
            "\nABORT: graph is ORPHAN or AMBIGUOUS. Injecting into an unreachable "
            "graph is worse than a bad payload because it SUCCEEDS -- you get a clean "
            "compile and a dead feature. Resolve which copy is live first."
        )
    return out


def emit_contract():
    AUDIT_DIR.mkdir(parents=True, exist_ok=True)
    path = AUDIT_DIR / "melusina_jump_windup_wiring.md"
    path.write_text(CONTRACT, encoding="utf-8")
    print(CONTRACT)
    print(f"  written -> {path}")
    return path


def build_steps():
    """Variable first; the graph nodes are meaningless without it."""
    return [
        ("blueprint_query", "add_variable", {
            "blueprint_path": PAWN, "variable_name": FLAG,
            "variable_type": "bool", "default_value": False}),
        ("blueprint_query", "add_event_node", {
            "blueprint_path": PAWN, "graph_name": GRAPH,
            "event_name": f"InputAction {ACTION}"}),
        ("blueprint_query", "add_event_node", {
            "blueprint_path": PAWN, "graph_name": GRAPH,
            "event_name": "OnLanded"}),
        ("blueprint_query", "add_event_node", {
            "blueprint_path": PAWN, "graph_name": GRAPH,
            "event_name": f"AnimNotify_{NOTIFY}"}),
        ("blueprint_query", "compile_blueprint", {"blueprint_path": PAWN}),
        ("blueprint_query", "save_asset", {"asset_path": PAWN}),
    ]


def run(dry_run=True):
    mode = "DRY RUN" if dry_run else "APPLY"
    print(f"[{mode}] wiring {ACTION} wind-up on BP_MelusinaJRPGCharacter")
    steps = build_steps()
    report = {"kind": "melusina_jump_windup", "dry_run": dry_run, "pawn": PAWN,
              "abp": ABP, "flag": FLAG, "notify": NOTIFY, "steps": []}

    if dry_run:
        for tool, action, params in steps:
            detail = params.get("event_name") or params.get("variable_name") or ""
            print(f"  would {tool}:{action:<18} {detail}")
        report["steps"] = [{"tool": t, "action": a, "params": p} for t, a, p in steps]
        write_report("melusina_jump_windup_dryrun.json", report)
        print(f"\n  {len(steps)} steps planned.")
        print("  NOTE: event nodes only. The Set/Cast/Jump wiring between them still "
              "needs connect_pins with real node ids, which only exist after the "
              "events are spawned -- run --apply, then read the graph and wire, or "
              "capture the cluster by hand per Recipe 16 (--emit-contract).")
        return report

    live_path()
    require_editor()
    for tool, action, params in steps:
        print(f"  {tool}:{action}")
        try:
            result = bp(action, params)
            report["steps"].append({"tool": tool, "action": action,
                                    "result": result, "ok": True})
        except MonolithError as e:
            report["steps"].append({"tool": tool, "action": action,
                                    "error": str(e), "ok": False})
            write_report("melusina_jump_windup.json", report)
            raise SystemExit(f"ABORTED on {action}: {e}")

    write_report("melusina_jump_windup.json", report)
    print("\n  Events spawned. Now read the graph and connect pins:")
    print(f"    blueprint_query get_graph_data {PAWN} {GRAPH}")
    print("  Then verify in PIE per --emit-contract.")
    return report


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--live-path", action="store_true",
                    help="Recipe 16 step 0: abort on ORPHAN/AMBIGUOUS")
    ap.add_argument("--emit-contract", action="store_true",
                    help="print/write the exact wiring + PIE checks")
    ap.add_argument("--plan", action="store_true", help="dry run")
    ap.add_argument("--apply", action="store_true", help="spawn the event nodes")
    args = ap.parse_args()
    if not any(vars(args).values()):
        ap.print_help()
        return 0
    try:
        if args.live_path:
            live_path()
        if args.emit_contract:
            emit_contract()
        if args.plan or args.apply:
            run(dry_run=not args.apply)
    except MonolithError as e:
        print(f"\nERROR: {e}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
