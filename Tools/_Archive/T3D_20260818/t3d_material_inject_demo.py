#!/usr/bin/env python3
"""
t3d_material_inject_demo.py — Apply TP_Melusina toon profile spec
via the T3D Material Curve Injector pipeline.

Reads  ->  Applies  ->  Verifies

Usage:
    python Tools/t3d_material_inject_demo.py              # apply spec, show summary
    python Tools/t3d_material_inject_demo.py --read       # read-back current state
    python Tools/t3d_material_inject_demo.py --verify     # compile + verify only
    python Tools/t3d_material_inject_demo.py --all        # read → apply → verify
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

from t3d_material_curve_injector import T3DMaterialCurveInjector

SPEC = (Path(__file__).resolve().parent.parent
        / "specs" / "toon_profiles" / "tp_melusina.json")

TOON_PROFILE_ASSET = "/Game/EnvSandbox/Materials/ToonProfiles/TP_Melusina"


def read_state(inj: T3DMaterialCurveInjector) -> dict:
    """Read current TP_Melusina curve keys and return them."""
    curves: dict[str, list] = {}
    for name in ("DiffuseRamp", "SpecularRamp"):
        pts = inj.read_curve_from_asset(TOON_PROFILE_ASSET, name)
        curves[name] = pts or []
    return curves


def apply_spec(inj: T3DMaterialCurveInjector) -> dict:
    spec = json.loads(SPEC.read_bytes())
    print(f"\n  spec: {SPEC}")
    result = inj.apply_toon_profile_spec(spec)
    return result


def verify(inj: T3DMaterialCurveInjector) -> tuple[bool, str]:
    return inj.compile_and_verify(TOON_PROFILE_ASSET)


def _print_curves(curves: dict):
    for name, pts in curves.items():
        print(f"  {name}: {len(pts)} keys")
        for p in pts:
            c = p.get("color", "?")
            print(f"      t={p['time']:.4f}  color=({c['r']:.4f},{c['g']:.4f},{c['b']:.4f},{c['a']:.4f})")


def main() -> int:
    inj = T3DMaterialCurveInjector()

    mode = "apply"
    if "--all" in sys.argv:
        mode = "all"
    elif "--read" in sys.argv:
        mode = "read"
    elif "--verify" in sys.argv:
        mode = "verify"

    if mode in ("read", "all"):
        print("=== Read current state ===")
        curves = read_state(inj)
        _print_curves(curves)

    if mode in ("apply", "all"):
        print("=== Apply spec ===")
        result = apply_spec(inj)
        print(json.dumps(result, indent=2))
        if not result.get("ok"):
            print("  FAILED — see errors above")
            return 1

    if mode in ("verify", "all"):
        print("=== Verify ===")
        ok, stats = verify(inj)
        print(f"  compile: {'OK' if ok else 'ERRORS'}")
        print(f"  {stats}")

    if mode == "all":
        print("=== Read-back after injection ===")
        curves = read_state(inj)
        _print_curves(curves)

    return 0


if __name__ == "__main__":
    sys.exit(main())
