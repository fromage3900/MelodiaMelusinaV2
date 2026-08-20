#!/usr/bin/env python3
"""
wire_melusina_spatial_puzzles.py -- spatial puzzle + interaction BP kit.

THE GAP
-------
Source/BS_GodFile/MelodiaIntegration/MelodiaExplorationActors.h already ships a
complete, Melusina-aware, Blueprintable surface:

  AMelodiaPuzzleRelayVolume
      ActivateRelay(AActor*) / ResetRelay()          BlueprintCallable
      PuzzleId, bRequireMelusina, bOneShot            EditAnywhere
      OnPuzzleActivated                               BlueprintAssignable

  AMelodiaExplorationInteractionVolume
      TryInteract(AActor*) / SetInteractionActive()   BlueprintCallable
      InteractionId, PromptText, bRequireMelusina     EditAnywhere
      OnMelusinaEntered / OnMelusinaExited /
      OnInteractionRequested                          BlueprintAssignable

  AMelodiaMovingPlatform                              (platform motion)

The C++ is not the gap. The gap is that **nothing instantiates it**:
Content/MelodiaIntegration/Blueprints/ holds Portal, StateAnchor, TraversalGate,
WorldChallenge, Encounter, Enemy and TravelVolume children -- and no puzzle or
interaction child at all. Docs/Reviews/CORE_4_EDITABLE_BP_SYSTEMS_2026-08-09.md
names this exactly: "volumes are native actors, level BP must wire travel by hand."

So this authors thin presentation shells over existing authority, per
Docs/Plans/LONG_TERM_GAMEPLAY_BP_T3D_PLAN_2026-08-14.md:
"adding a skill, enemy, portal, traversal capability, or world challenge means
authoring a DataAsset plus a small verified Blueprint child -- not inventing a
new subsystem."

NO NEW AUTHORITY IS CREATED. Puzzle/interaction state stays in the native actors;
these children only expose designer-set ids and route events to the UI.

UI ROUTE
--------
Content/MelodiaIntegration/UI/ has BP_MelodiaRhythmPrompt but no interaction
prompt. OnInteractionRequested carries PromptText, which is what a prompt widget
needs. WBP_MelodiaInteractionPrompt is created here and driven by the volume's
event -- the "callable by BP_Melusina and WBP UI" leg.

USAGE
-----
    python Tools/wire_melusina_spatial_puzzles.py --audit
    python Tools/wire_melusina_spatial_puzzles.py --plan
    python Tools/wire_melusina_spatial_puzzles.py --apply
"""
from __future__ import annotations

import argparse
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from build_melusina_locomotion_stack import (  # noqa: E402
    MonolithError, bp, require_editor, write_report,
)

BPDIR = "/Game/MelodiaIntegration/Blueprints"
UIDIR = "/Game/MelodiaIntegration/UI"
MAP = "/Game/MelodiaIntegration/Maps/MelodiaIntegrationMap"
PAWN = f"{BPDIR}/BP_MelusinaJRPGCharacter"

# Native parents (already compiled into BS_GodFile.dll, rebuilt 2026-08-16 01:04).
PARENT_PUZZLE = "MelodiaPuzzleRelayVolume"
PARENT_INTERACT = "MelodiaExplorationInteractionVolume"
PARENT_PLATFORM = "MelodiaMovingPlatform"

# Base + one authored fixture each, mirroring the existing kit's Base/_Fixture shape.
BLUEPRINTS = [
    {"path": f"{BPDIR}/BP_MelodiaPuzzleRelay_Base", "parent": PARENT_PUZZLE,
     "defaults": {"bRequireMelusina": True, "bOneShot": True}},
    {"path": f"{BPDIR}/BP_MelodiaPuzzleRelay_FirstResonance", "parent": PARENT_PUZZLE,
     "defaults": {"PuzzleId": "first_resonance_relay",
                  "bRequireMelusina": True, "bOneShot": True}},
    {"path": f"{BPDIR}/BP_MelodiaInteraction_Base", "parent": PARENT_INTERACT,
     "defaults": {"bRequireMelusina": True, "bOneShot": False}},
    {"path": f"{BPDIR}/BP_MelodiaInteraction_DreamAnchor", "parent": PARENT_INTERACT,
     "defaults": {"InteractionId": "dream_anchor_touch",
                  "PromptText": "Touch the anchor",
                  "bRequireMelusina": True, "bOneShot": True}},
    {"path": f"{BPDIR}/BP_MelodiaMovingPlatform_Base", "parent": PARENT_PLATFORM,
     "defaults": {}},
]

WIDGET = f"{UIDIR}/WBP_MelodiaInteractionPrompt"

# Fixture placements in the proof map. Spread apart so overlaps cannot chain.
PLACEMENTS = [
    {"blueprint": f"{BPDIR}/BP_MelodiaPuzzleRelay_FirstResonance",
     "location": [1200.0, 0.0, 100.0]},
    {"blueprint": f"{BPDIR}/BP_MelodiaInteraction_DreamAnchor",
     "location": [1600.0, 400.0, 100.0]},
]


def audit():
    """Read-only: what exists, what is missing."""
    print("[audit] spatial puzzle kit")
    require_editor()
    report = {"kind": "melusina_spatial_puzzle_audit", "map": MAP, "assets": {}}
    for item in BLUEPRINTS + [{"path": WIDGET, "parent": "UserWidget"}]:
        p = item["path"]
        try:
            info = bp("get_blueprint_info", {"asset_path": p})
            exists = not (isinstance(info, dict) and info.get("error"))
        except MonolithError:
            exists = False
        report["assets"][p] = exists
        print(f"  {'EXISTS ' if exists else 'MISSING'}  {p.rsplit('/', 1)[-1]}")
    report["missing"] = [k for k, v in report["assets"].items() if not v]
    write_report("melusina_spatial_puzzle_audit.json", report)
    return report


def _exists(path):
    """create_blueprint errors on an existing asset, so creation must be skipped."""
    try:
        info = bp("get_blueprint_info", {"asset_path": path}, timeout=120)
        return not (isinstance(info, dict) and info.get("error"))
    except MonolithError:
        return False


def build_steps(check_existing=False):
    steps = []
    for b in BLUEPRINTS:
        if not (check_existing and _exists(b["path"])):
            steps.append(("create_blueprint", {
                "save_path": b["path"], "parent_class": b["parent"]}))
        else:
            print(f"  {b['path'].rsplit('/', 1)[-1]} exists -- properties only")
        if b["defaults"]:
            steps.append(("set_cdo_properties", {
                "asset_path": b["path"], "properties": b["defaults"]}))
        steps.append(("compile_blueprint", {"asset_path": b["path"]}))
        steps.append(("save_asset", {"asset_path": b["path"]}))

    if not (check_existing and _exists(WIDGET)):
        steps.append(("create_blueprint", {
            "save_path": WIDGET, "parent_class": "UserWidget",
            "blueprint_type": "Widget"}))
    steps.append(("compile_blueprint", {"asset_path": WIDGET}))
    steps.append(("save_asset", {"asset_path": WIDGET}))

    for pl in PLACEMENTS:
        steps.append(("spawn_blueprint_actor", {
            "blueprint": pl["blueprint"], "location": pl["location"],
            "label": pl["blueprint"].rsplit("/", 1)[-1]}))
    return steps


def run(dry_run=True):
    mode = "DRY RUN" if dry_run else "APPLY"
    print(f"[{mode}] spatial puzzle kit -> {MAP.rsplit('/', 1)[-1]}")
    steps = build_steps(check_existing=not dry_run)
    report = {"kind": "melusina_spatial_puzzles", "dry_run": dry_run,
              "map": MAP, "blueprints": [b["path"] for b in BLUEPRINTS],
              "widget": WIDGET, "steps": []}

    if dry_run:
        for action, params in steps:
            label = (params.get("save_path") or params.get("asset_path")
                     or params.get("blueprint") or "").rsplit("/", 1)[-1]
            print(f"  would blueprint_query:{action:<24} {label}")
        report["steps"] = [{"action": a, "params": p} for a, p in steps]
        write_report("melusina_spatial_puzzles_dryrun.json", report)
        print(f"\n  {len(steps)} steps planned.")
        print("  Event wiring (OnInteractionRequested -> prompt, OnPuzzleActivated")
        print("  -> anchor) needs node ids that exist only after creation -- same")
        print("  limit as the jump wind-up driver. Run --apply, then wire from a")
        print("  graph read or capture per MONOLITH_GUIDE Recipe 16.")
        return report

    require_editor()
    for action, params in steps:
        label = (params.get("save_path") or params.get("asset_path")
                 or params.get("blueprint") or "").rsplit("/", 1)[-1]
        print(f"  blueprint_query:{action}  {label}")
        try:
            result = bp(action, params, timeout=300)
            report["steps"].append({"action": action, "asset": label,
                                    "result": result, "ok": True})
        except MonolithError as e:
            report["steps"].append({"action": action, "asset": label,
                                    "error": str(e), "ok": False})
            write_report("melusina_spatial_puzzles.json", report)
            raise SystemExit(f"ABORTED on {action} / {label}: {e}")

    write_report("melusina_spatial_puzzles.json", report)
    return report


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--audit", action="store_true", help="read-only existence check")
    ap.add_argument("--plan", action="store_true", help="dry run")
    ap.add_argument("--apply", action="store_true", help="create the kit")
    args = ap.parse_args()
    if not any(vars(args).values()):
        ap.print_help()
        return 0
    try:
        if args.audit:
            audit()
        if args.plan or args.apply:
            run(dry_run=not args.apply)
    except MonolithError as e:
        print(f"\nERROR: {e}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
