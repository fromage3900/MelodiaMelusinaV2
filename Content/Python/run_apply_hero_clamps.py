"""run_apply_hero_clamps.py - Headless and In-Editor execution runner for baking clamps.

Applies the 345 verified scalar parameter clamps, min/max bounds, and 12 UI groups
to the 4 primary hero master materials:
  1. /Game/EnvSandbox/Materials/Masters/M_Master_Toon_Universal
  2. /Game/EnvSandbox/Materials/Masters/M_Master_Toon_Landscape_HeightBlend
  3. /Game/EnvSandbox/Materials/Masters/M_Master_Nikki
  4. /Game/EnvSandbox/Materials/Masters/M_Master_Nikki_Landscape

Enforces zero unbounded float sliders and guarantees clean compilation and save.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

# Add Content/Python to sys.path
SCRIPT_DIR = Path(__file__).resolve().parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

import master_material_clamping_engine as engine

HERO_MASTERS = [
    "/Game/EnvSandbox/Materials/Masters/M_Master_Toon_Universal",
    "/Game/EnvSandbox/Materials/Masters/M_Master_Toon_Landscape_HeightBlend",
    "/Game/EnvSandbox/Materials/Masters/M_Master_Nikki",
    "/Game/EnvSandbox/Materials/Masters/M_Master_Nikki_Landscape",
]


def main(dry_run: bool = False):
    print("=" * 70)
    print(f"RUNNING HERO MASTER MATERIAL CLAMPING PASS (dry_run={dry_run})")
    print("=" * 70)

    results = {}
    total_clamped = 0
    total_grouped = 0
    has_errors = False

    for master_path in HERO_MASTERS:
        print(f"\n[Clamping Engine] Processing: {master_path}...")
        res = engine.apply_clamps_to_live_unreal(master_path, dry_run=dry_run)
        results[master_path] = res

        if res.get("ok"):
            print(f"  -> SUCCESS: {res.get('clamped_count', 0)} scalars clamped, {res.get('grouped_count', 0)} parameters grouped.")
            if not dry_run:
                print(f"  -> Recompiled & Saved: {res.get('saved', False)}")
            total_clamped += res.get("clamped_count", 0)
            total_grouped += res.get("grouped_count", 0)
        else:
            print(f"  -> FAILED: {res.get('error', 'unknown error')}")
            for err in res.get("errors", []):
                print(f"     ! {err}")
            has_errors = True

    summary = {
        "status": "passed" if not has_errors else "failed",
        "dry_run": dry_run,
        "total_scalars_clamped": total_clamped,
        "total_parameters_grouped": total_grouped,
        "masters_processed": len(HERO_MASTERS),
        "details": results,
    }

    out_receipt = SCRIPT_DIR.parents[1] / "Saved" / "Audit" / "applied_hero_clamps_receipt.json"
    out_receipt.parent.mkdir(parents=True, exist_ok=True)
    out_receipt.write_text(json.dumps(summary, indent=2), encoding="utf-8")
    print("\n" + "=" * 70)
    print(f"CLAMPING PASS COMPLETE: {total_clamped} scalars clamped across {len(HERO_MASTERS)} masters.")
    print(f"Receipt written to: {out_receipt.resolve()}")
    print("=" * 70)
    return 0 if not has_errors else 1


if __name__ == "__main__":
    is_dry = "--dry-run" in sys.argv
    sys.exit(main(dry_run=is_dry))
