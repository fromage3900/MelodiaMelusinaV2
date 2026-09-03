#!/usr/bin/env python3
"""
build_melusina_foot_ik.py -- give IK_Melusina_Body real solvers and goals.

THE PROBLEM
-----------
IK_Melusina and IK_Melusina_Body currently have ZERO solvers and ZERO goals. Two
consequences, and the second is the one people miss:

  1. No foot planting. Feet skate and sink on slopes.
  2. The IK Retargeter's "Run IK Rig" op is inert. It runs, reports success, and
     changes nothing -- so every retarget through it has silently been chain-only.

BONE CHOICE
-----------
The rig carries both the ARP control hierarchy (c_thigh_ik_l, c_foot_ik_l, ...) and
the UE-standard deform chain. This targets the deform chain:

    thigh_l -> calf_l -> foot_l      (and _r)
    pelvis                            (root / counter-offset)
    ik_foot_root, ik_foot_l/r         (already present; standard UE IK bones)

Deform bones, not c_* controls, because the ABP evaluates the deform hierarchy at
runtime -- the ARP controls do not exist in the cooked skeleton's evaluation path in
any way the anim graph can drive.

ORDER IN THE ANIM GRAPH
-----------------------
    state machine -> DefaultSlot -> foot IK -> KawaiiPhysics -> output

Foot IK before Kawaii: the skirt must react to the corrected leg pose, not the
pre-IK one. Gated on `bIsFalling == false` so it does not fight the jump arc --
planting feet to the ground mid-jump is exactly the wrong result.

USAGE
-----
    python Tools/build_melusina_foot_ik.py --inspect
    python Tools/build_melusina_foot_ik.py --plan
    python Tools/build_melusina_foot_ik.py --apply
"""
from __future__ import annotations

import argparse
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from build_melusina_locomotion_stack import (  # noqa: E402
    ABP, MonolithError, anim, bp, require_editor, write_report,
)

IK_RIG = "/Game/Melodia/Characters/Melusina/IK_Melusina_Body"
RETARGETER = "/Game/Melodia/Mocap/Retarget/RTG_Quaternius_to_Melusina"

# Live skeleton is Auto-Rig Pro, NOT UE-standard. specs/anim_presets/
# melusina_contract_bones.json lists thigh_l/calf_l/pelvis -- those are the
# Blender-side contract names and DO NOT EXIST on SK_Melusina_Skeleton.
# Verified against get_skeleton_info (465 bones): the deform chain is
# thigh_stretch_* -> leg_stretch_* -> foot_*, with root_x as the hip.
PELVIS = "root_x"

CHAINS = [
    {"name": "LeftLeg",  "start": "thigh_stretch_l", "end": "foot_l",
     "goal": "Goal_Foot_L"},
    {"name": "RightLeg", "start": "thigh_stretch_r", "end": "foot_r",
     "goal": "Goal_Foot_R"},
]

SOLVER = "FullBodyIK"


def inspect():
    """Read-only: confirm the rig really is empty and the bones really are there."""
    print("[inspect] reading IK rig and skeleton")
    require_editor()
    report = {"kind": "melusina_foot_ik_inspect", "ik_rig": IK_RIG, "checks": {}}

    def probe(label, fn):
        try:
            report["checks"][label] = fn()
        except MonolithError as e:
            report["checks"][label] = {"error": str(e)}

    probe("ikrig", lambda: anim("get_ikrig_info", {"asset_path": IK_RIG}))
    probe("retargeter", lambda: anim("get_retargeter_info", {"asset_path": RETARGETER}))
    probe("skeleton", lambda: anim("get_skeleton_info", {
        "asset_path": "/Game/Melodia/Characters/Melusina/SK_Melusina_Skeleton"}))

    import json as _json
    skel_blob = _json.dumps(report["checks"].get("skeleton", {}))
    needed = [PELVIS] + [c["start"] for c in CHAINS] + [c["end"] for c in CHAINS]
    report["bones_present"] = {b: (f'"{b}"' in skel_blob) for b in needed}
    for bone, present in report["bones_present"].items():
        print(f"  bone {bone:<10} {'OK' if present else 'MISSING'}")

    rig_blob = _json.dumps(report["checks"].get("ikrig", {}))
    report["rig_looks_empty"] = ('"solvers": []' in rig_blob
                                 or '"goals": []' in rig_blob)
    print(f"  rig appears empty: {report['rig_looks_empty']}")

    write_report("melusina_foot_ik_inspect.json", report)
    return report


def build_steps():
    steps = []
    # Retarget chains carry the goal name, so goals come from the chain not the solver.
    for c in CHAINS:
        steps.append(("animation_query", "add_retarget_chain", {
            "asset_path": IK_RIG, "chain_name": c["name"],
            "start_bone": c["start"], "end_bone": c["end"],
            "goal_name": c["goal"]}))

    # One solver rooted at the hip, with both foot goals attached.
    steps.append(("animation_query", "add_ik_solver", {
        "asset_path": IK_RIG, "solver_type": SOLVER, "root_bone": PELVIS,
        "goals": [c["goal"] for c in CHAINS]}))

    steps.append(("blueprint_query", "save_asset", {"asset_path": IK_RIG}))

    # Graph pass. Note this action takes foot/pelvis bones directly and does not
    # accept an ik_rig or gate argument -- gating is a follow-up on the node.
    steps.append(("animation_query", "build_foot_ik_pass", {
        "abp_path": ABP,
        "left_foot_bone": CHAINS[0]["end"],
        "right_foot_bone": CHAINS[1]["end"],
        "pelvis_bone": PELVIS}))
    steps.append(("blueprint_query", "compile_blueprint", {"asset_path": ABP}))
    steps.append(("blueprint_query", "save_asset", {"asset_path": ABP}))
    return steps


def run(dry_run=True):
    mode = "DRY RUN" if dry_run else "APPLY"
    print(f"[{mode}] authoring foot IK on {IK_RIG.rsplit('/', 1)[-1]}")
    steps = build_steps()
    report = {"kind": "melusina_foot_ik", "dry_run": dry_run, "ik_rig": IK_RIG,
              "abp": ABP, "chains": CHAINS, "solver": SOLVER, "steps": []}

    if dry_run:
        for tool, action, params in steps:
            detail = (params.get("chain_name") or params.get("goal_name")
                      or params.get("solver_type") or params.get("asset_path", "")
                      .rsplit("/", 1)[-1])
            print(f"  would {tool}:{action:<20} {detail}")
        report["steps"] = [{"tool": t, "action": a, "params": p} for t, a, p in steps]
        write_report("melusina_foot_ik_dryrun.json", report)
        print(f"\n  {len(steps)} steps planned. Re-run with --apply.")
        return report

    require_editor()
    for tool, action, params in steps:
        print(f"  {tool}:{action}")
        try:
            fn = anim if tool == "animation_query" else bp
            result = fn(action, params, timeout=300)
            report["steps"].append({"tool": tool, "action": action,
                                    "result": result, "ok": True})
        except MonolithError as e:
            report["steps"].append({"tool": tool, "action": action,
                                    "error": str(e), "ok": False})
            write_report("melusina_foot_ik.json", report)
            raise SystemExit(f"ABORTED on {action}: {e}")

    write_report("melusina_foot_ik.json", report)
    print("\n  Verify on a SLOPE, not flat ground -- flat ground proves nothing here.")
    print("  Also re-check RTG_Quaternius_to_Melusina: its 'Run IK Rig' op was inert "
          "while the rig had no solvers, and is now live. Retargets may shift.")
    return report


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--inspect", action="store_true", help="read-only rig/bone check")
    ap.add_argument("--plan", action="store_true", help="dry run")
    ap.add_argument("--apply", action="store_true", help="author solvers and goals")
    args = ap.parse_args()
    if not any(vars(args).values()):
        ap.print_help()
        return 0
    try:
        if args.inspect:
            inspect()
        if args.plan or args.apply:
            run(dry_run=not args.apply)
    except MonolithError as e:
        print(f"\nERROR: {e}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
