#!/usr/bin/env python3
"""
wire_melusina_quaternius_actions.py -- Quaternius clips into Melusina's action montages.

SCOPE
-----
Actions only. Ground locomotion stays on the Mocap RootX set (owner decision), so
Idle_Loop / Walk_Loop / Jog_Fwd_Loop / Sprint_Loop are deliberately NOT wired here --
they belong to BS_Melusina_Locomotion, which build_melusina_locomotion_stack.py owns.
The jump arc is also not here: Jump_Start/Loop/Land are state-machine states, not
montages, and that script wires them.

The seven existing montage assets keep their names. The JRPG battle authority calls
play_montage against those paths, so renaming them breaks combat. Segments are
replaced in place.

Three P0 exploration montages (Interact, PickUp, Roll) are included.  The driver
creates one only when its package is absent; current packages are rebound in place.

OUT OF SCOPE by design: Driving, Fixing_Kneeling, Pistol_*, Punch_*, Push, Swim,
Sitting, Walk_Formal, Idle_Torch, Crouch, Spell_Simple_Enter/Exit/Idle. They are
retargeted and on disk; they are simply not P0. Wiring them now is scope creep.

USAGE
-----
    python Tools/wire_melusina_quaternius_actions.py --plan
    python Tools/wire_melusina_quaternius_actions.py --apply
"""
from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from build_melusina_locomotion_stack import (  # noqa: E402
    MonolithError, anim, bp, require_editor, write_report,
)

PROJECT_DIR = Path(__file__).resolve().parents[1]
ROOT = "/Game/Melodia/Characters/Melusina/Animations"
Q = f"{ROOT}/QuaterniusRetargeted"
M = f"{ROOT}/Montages"
SKELETON = "/Game/Melodia/Characters/Melusina/SK_Melusina_Skeleton"

# Default montage slot. Keep it: the JRPG template's play_montage targets DefaultSlot,
# and the ABP needs a matching Slot node for any of this to be visible.
SLOT = "DefaultSlot"

# (montage_asset, source_clip)
BINDINGS = [
    (f"{M}/AM_Melusina_Death",        f"{Q}/A_Q_Melusina_Death01"),
    (f"{M}/AM_Melusina_Hit_Chest",    f"{Q}/A_Q_Melusina_Hit_Chest"),
    (f"{M}/AM_Melusina_Hit_Head",     f"{Q}/A_Q_Melusina_Hit_Head"),
    (f"{M}/AM_Melusina_Idle_Dance",   f"{Q}/A_Q_Melusina_Dance_Loop"),
    (f"{M}/AM_Melusina_Idle_Talk",    f"{Q}/A_Q_Melusina_Idle_Talking_Loop"),
    (f"{M}/AM_Melusina_Spell_Shoot",  f"{Q}/A_Q_Melusina_Spell_Simple_Shoot"),
    (f"{M}/AM_Melusina_Sword_Attack", f"{Q}/A_Q_Melusina_Sword_Attack"),
    # New for P0 exploration.
    (f"{M}/AM_Melusina_Interact",     f"{Q}/A_Q_Melusina_Interact"),
    (f"{M}/AM_Melusina_PickUp",       f"{Q}/A_Q_Melusina_PickUp_Table"),
    (f"{M}/AM_Melusina_Roll",         f"{Q}/A_Q_Melusina_Roll"),
]


def asset_package_path(asset_path: str) -> Path | None:
    """Resolve a project ``/Game`` asset to its local package path.

    The action tool must not trust a stale hard-coded ``exists_already`` flag:
    Monolith montage creation is not idempotent, while a missing source clip
    makes the subsequent mutation fail after earlier bindings were written.
    """
    if not asset_path.startswith("/Game/"):
        return None
    relative = asset_path.removeprefix("/Game/")
    return PROJECT_DIR / "Content" / f"{relative}.uasset"


def asset_exists_on_disk(asset_path: str) -> bool:
    package = asset_package_path(asset_path)
    return package is not None and package.is_file()


def binding_preflight() -> dict[str, object]:
    """Return the package-backed preflight used by plan and apply modes."""
    montage_status = {
        montage: asset_exists_on_disk(montage) for montage, _clip in BINDINGS
    }
    clip_status = {
        clip: asset_exists_on_disk(clip) for _montage, clip in BINDINGS
    }
    return {
        "montages": montage_status,
        "clips": clip_status,
        "missing_montages": sorted(path for path, exists in montage_status.items() if not exists),
        "missing_clips": sorted(path for path, exists in clip_status.items() if not exists),
    }


def build_steps():
    steps = []
    for montage, clip in BINDINGS:
        exists = asset_exists_on_disk(montage)
        if not exists:
            steps.append(("animation_query", "create_montage", {
                "asset_path": montage, "skeleton_path": SKELETON}))
            steps.append(("animation_query", "add_montage_anim_segment", {
                "asset_path": montage, "anim_path": clip}))
        else:
            # Replace the segment in place; the asset path is the contract.
            steps.append(("animation_query", "add_montage_anim_segment", {
                "asset_path": montage, "anim_path": clip}))
        steps.append(("blueprint_query", "save_asset", {"asset_path": montage}))
    return steps


def run(dry_run=True):
    mode = "DRY RUN" if dry_run else "APPLY"
    print(f"[{mode}] wiring {len(BINDINGS)} Quaternius action montages")
    preflight = binding_preflight()
    steps = build_steps()
    report = {"kind": "melusina_quaternius_actions", "dry_run": dry_run,
              "slot": SLOT, "bindings": [
                  {"montage": m, "clip": c,
                   "pre_existing": bool(preflight["montages"][m])}
                  for m, c in BINDINGS],
              "preflight": preflight,
              "steps": []}

    if dry_run:
        for montage, clip in BINDINGS:
            exists = bool(preflight["montages"][montage])
            verb = "bind " if exists else "CREATE"
            print(f"  {verb} {montage.rsplit('/', 1)[-1]:<26} <- "
                  f"{clip.rsplit('/', 1)[-1]}")
        for missing in preflight["missing_clips"]:
            print(f"  MISSING SOURCE CLIP: {missing}")
        report["steps"] = [{"tool": t, "action": a, "params": p} for t, a, p in steps]
        write_report("melusina_quaternius_actions_dryrun.json", report)
        print(f"\n  {len(steps)} steps planned. Re-run with --apply.")
        return report

    require_editor()
    if preflight["missing_clips"]:
        write_report("melusina_quaternius_actions.json", report)
        missing = ", ".join(preflight["missing_clips"])
        raise SystemExit(
            "ABORTED before mutation: source animation package(s) are missing: "
            + missing
        )
    for tool, action, params in steps:
        label = params["asset_path"].rsplit("/", 1)[-1]
        print(f"  {tool}:{action}  {label}")
        try:
            fn = anim if tool == "animation_query" else bp
            result = fn(action, params, timeout=300)
            report["steps"].append({"tool": tool, "action": action, "asset": label,
                                    "result": result, "ok": True})
        except MonolithError as e:
            report["steps"].append({"tool": tool, "action": action, "asset": label,
                                    "error": str(e), "ok": False})
            write_report("melusina_quaternius_actions.json", report)
            raise SystemExit(f"ABORTED on {action} / {label}: {e}")

    write_report("melusina_quaternius_actions.json", report)
    print("\n  Montage names unchanged, so existing play_montage calls still resolve.")
    print(f"  ABP_Melusina_Current needs a Slot node named '{SLOT}' after the state "
          "machine or none of this renders.")
    return report


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--plan", action="store_true", help="dry run")
    ap.add_argument("--apply", action="store_true", help="write the montages")
    args = ap.parse_args()
    if not any(vars(args).values()):
        ap.print_help()
        return 0
    try:
        run(dry_run=not args.apply)
    except MonolithError as e:
        print(f"\nERROR: {e}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
