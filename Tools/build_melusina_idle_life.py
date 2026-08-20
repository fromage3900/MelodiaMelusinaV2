#!/usr/bin/env python3
"""
build_melusina_idle_life.py -- blink + breathing curves on Melusina's idle.

WHY THE CURVE NAMES MATTER MORE THAN THE CURVES
-----------------------------------------------
Of the 103 morph targets on SK_Melusina_V2_Body, only 68 carry real deltas.
The entire 52-key ARKit block is bit-identical to Basis -- named, never sculpted --
so Unreal correctly discards them on import. Tools/populate_melusina_arkit_shapekeys.py
documents this in full.

That makes `eyeBlinkLeft` / `eyeBlinkRight` a trap: they are ARKit names, they do not
exist on the imported mesh, and a curve driving them compiles clean and does nothing.
The FACS twins are what actually imported:

    eyeBlinkLeft   -> eyesCloseL      (populate_melusina_arkit_shapekeys.py:61)
    eyeBlinkRight  -> eyesCloseR      (populate_melusina_arkit_shapekeys.py:62)

So this script drives eyesCloseL/R. --check-names verifies them against the live
skeleton before writing anything, because a silently inert curve is the failure mode
that looks like success.

BLINK CADENCE
-------------
A metronomic blink reads as robotic. Real blinks cluster: roughly 2 per 7s at rest,
irregular spacing, 0.12s close-open, with the close faster than the open. The pattern
below is authored irregular on purpose and is one full idle loop long.

USAGE
-----
    python Tools/build_melusina_idle_life.py --check-names
    python Tools/build_melusina_idle_life.py --plan
    python Tools/build_melusina_idle_life.py --apply
"""
from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from build_melusina_locomotion_stack import (  # noqa: E402
    AUDIT_DIR, MonolithError, anim, require_editor, write_report,
)

IDLE = "/Game/Melodia/Characters/Melusina/Animations/Locomotion/A_Melusina_Idle_Mocap_RootX"
MESH = "/Game/Melodia/Characters/Melusina/SK_Melusina_V2_Body"

# A blink pattern only makes sense if the loop is long enough to hold one.
# The approved mocap idle is 0.5s (melusina_idle_restore_mocap_2026-08-13.json).
# Baking 5 blinks into that is 10 blinks/second -- a seizure, not idle life.
# Below this length, blinks must be driven from the AnimBP on a randomised timer
# instead of baked as curves. This script refuses rather than producing that.
MIN_LOOP_FOR_BAKED_BLINK = 3.0

BLINK_CURVES = ("eyesCloseL", "eyesCloseR")

# ARKit names that look right and are inert. Refuse to use these.
# browInnerUp is the combined ARKit shape; its FACS sources are innerBrowRaiserL/R
# (populate_melusina_arkit_shapekeys.py:65). Driving browInnerUp does nothing.
FORBIDDEN = ("eyeBlinkLeft", "eyeBlinkRight", "eyeBlink_L", "eyeBlink_R",
             "browInnerUp", "browInnerUpL", "browInnerUpR")

# Breathing: low amplitude, slower than the blink, on the FACS names that imported.
BREATH_CURVES = ("innerBrowRaiserL", "innerBrowRaiserR")

# (time_fraction, value). Close fast, open slower -- 0.04s down, 0.08s up at 0.12s total.
BLINK_SHAPE = ((0.0, 0.0), (0.33, 1.0), (1.0, 0.0))
BLINK_DURATION = 0.12
# Irregular, clustered. Fractions of the idle loop.
BLINK_STARTS = (0.08, 0.21, 0.55, 0.63, 0.87)

BREATH_SHAPE = ((0.0, 0.0), (0.5, 0.15), (1.0, 0.0))


def check_names():
    """Prove the curve targets exist before writing curves against them."""
    print("[check-names] verifying morph targets on the live mesh")
    require_editor()
    info = anim("get_skeletal_mesh_info", {"asset_path": MESH})
    blob = json.dumps(info)

    report = {"kind": "melusina_idle_life_name_check", "mesh": MESH, "targets": {}}
    ok = True
    for name in BLINK_CURVES + BREATH_CURVES:
        present = f'"{name}"' in blob
        report["targets"][name] = present
        print(f"  {name:<16} {'OK' if present else 'MISSING'}")
        ok = ok and present

    for name in FORBIDDEN:
        if f'"{name}"' in blob:
            print(f"  NOTE: {name} unexpectedly present -- re-read the ARKit situation "
                  f"before trusting it; it was empty at last export.")

    report["ok"] = ok
    write_report("melusina_idle_life_name_check.json", report)
    if not ok:
        print("\n  Refusing to author curves for missing targets. A curve on a name the "
              "mesh does not have compiles clean and does nothing.")
    return report


def _curve_keys(starts, shape, duration, seq_length):
    keys = []
    for start in starts:
        t0 = start * seq_length
        for frac, value in shape:
            keys.append({"time": round(t0 + frac * duration, 4), "value": value})
    return sorted(keys, key=lambda k: k["time"])


def build(dry_run=True, breath_only=False):
    mode = "DRY RUN" if dry_run else "APPLY"
    scope = "breathing only" if breath_only else "blink + breathing"
    print(f"[{mode}] authoring {scope} on {IDLE}")

    if not dry_run:
        require_editor()
        names = check_names()
        if not names["ok"]:
            raise SystemExit("Aborted: curve targets missing. Nothing written.")
        info = anim("get_sequence_info", {"asset_path": IDLE})
        seq_length = float(info.get("length") or info.get("sequence_length") or 0) or None
        if not seq_length:
            raise SystemExit(
                f"Could not read sequence length from get_sequence_info: {info}")
        if seq_length < MIN_LOOP_FOR_BAKED_BLINK and not breath_only:
            rate = len(BLINK_STARTS) / seq_length
            raise SystemExit(
                f"\nREFUSING: {IDLE.rsplit('/', 1)[-1]} is {seq_length:.2f}s. Baking "
                f"{len(BLINK_STARTS)} blinks into it gives {rate:.1f} blinks/second.\n"
                f"A short mocap loop cannot carry a natural blink cadence -- the cadence "
                f"is longer than the clip.\n\n"
                f"Do one of these instead:\n"
                f"  1. Drive eyesCloseL/R from ABP_Melusina_Current on a randomised "
                f"timer (~2 per 7s). Correct for any loop length, and the right answer "
                f"here.\n"
                f"  2. Bake onto a longer idle if one is authored later.\n"
                f"Breathing curves alone are still valid on a short loop; re-run with "
                f"--breath-only for those.")
    else:
        seq_length = 1.0
        print("  (dry run assumes a 1.0s loop; --apply reads the real length)")

    steps = []
    for name in (() if breath_only else BLINK_CURVES):
        keys = _curve_keys(BLINK_STARTS, BLINK_SHAPE, BLINK_DURATION, seq_length)
        steps.append(("add_curve", {"asset_path": IDLE, "curve_name": name}))
        steps.append(("set_curve_keys",
                      {"asset_path": IDLE, "curve_name": name, "keys": keys}))
    for name in BREATH_CURVES:
        keys = _curve_keys((0.0,), BREATH_SHAPE, seq_length, seq_length)
        steps.append(("add_curve", {"asset_path": IDLE, "curve_name": name}))
        steps.append(("set_curve_keys",
                      {"asset_path": IDLE, "curve_name": name, "keys": keys}))

    report = {"kind": "melusina_idle_life", "sequence": IDLE, "dry_run": dry_run,
              "sequence_length": seq_length, "blink_curves": list(BLINK_CURVES),
              "breath_curves": list(BREATH_CURVES), "steps": []}

    if dry_run:
        for action, params in steps:
            n = len(params.get("keys", []))
            print(f"  would animation_query:{action:<15} {params['curve_name']}"
                  + (f"  ({n} keys)" if n else ""))
        report["steps"] = [{"action": a, "params": p} for a, p in steps]
        write_report("melusina_idle_life_dryrun.json", report)
        print(f"\n  {len(steps)} steps planned. Re-run with --apply.")
        return report

    for action, params in steps:
        print(f"  animation_query:{action}  {params['curve_name']}")
        try:
            result = anim(action, params)
            report["steps"].append({"action": action, "curve": params["curve_name"],
                                    "result": result, "ok": True})
        except MonolithError as e:
            report["steps"].append({"action": action, "curve": params["curve_name"],
                                    "error": str(e), "ok": False})
            write_report("melusina_idle_life.json", report)
            raise SystemExit(f"ABORTED on {action}/{params['curve_name']}: {e}")

    write_report("melusina_idle_life.json", report)
    print("\n  Curves written. They carry through BS_Melusina_Locomotion, so the blink "
          "survives into walk/run -- no per-clip duplication needed.")
    return report


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--check-names", action="store_true",
                    help="read-only: prove the morph targets exist")
    ap.add_argument("--plan", action="store_true", help="dry run")
    ap.add_argument("--breath-only", action="store_true",
                    help="skip blinks; author breathing curves only (short loops)")
    ap.add_argument("--apply", action="store_true", help="write the curves")
    args = ap.parse_args()

    if not any(vars(args).values()):
        ap.print_help()
        return 0
    try:
        if args.check_names:
            check_names()
        if args.plan or args.apply or args.breath_only:
            build(dry_run=not args.apply, breath_only=args.breath_only)
    except MonolithError as e:
        print(f"\nERROR: {e}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
