#!/usr/bin/env python
"""
Copernicus Fabric Sheen — velvet/silk highlight for FarawayMother.

The 6 FarawayMother P2 suites have Sheen maps (Gown/Corset/Mantle/Ornament/Veil):
  T_FarawayMother_*_Gown_CelestialSilkJacquard_Sheen.png (8 maps, Sheen is 8th)
  T_FarawayMother_*_Mantle_NightSkyVelvet_Sheen.png

Current: ORM packed, Sheen as separate gray mask, consumed by M_Master_Nikki sheen lane (no COP).

This COP replaces ad-hoc PIL compositing:
  File COP (BaseColor) + File COP (Sheen) → Composite COP (screen/soft-light)
  → Curvature-driven sheen falloff → File Output (Sheen mask for M_Master_Nikki)

Params match M_Master_Nikki sheen: NikkiPearlSheen 0.4, NikkiPastelStrength 0.65,
ShadowDreamStrength 0.60, with Infinity Nikki-style versatile fabric merge (one master, blend textures).

Run: hython Tools/Houdini/copernicus/copernicus_fabric_sheen.py --suite Gown

Refs: Docs/Plans/MATERIAL_ORCHESTRATION_TRIMSHEET_2026-08-30.md §1.2 (Faraway P2)
      Docs/Research/UE58_TOON_MATERIAL_INTAKE_INFINITY_NIKKI_2026-08-08.md §8 (versatile fabric master).
"""
from __future__ import annotations
import argparse
import json
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[3]
SEED = 20260828

SUITES = [
    "T_FarawayMother_Corset_GildedAcanthusBrocade",
    "T_FarawayMother_Cradle_CarvedAlabasterWood",
    "T_FarawayMother_Gown_CelestialSilkJacquard",
    "T_FarawayMother_Mantle_NightSkyVelvet",
    "T_FarawayMother_Ornament_NacreMusicBoxJewel",
    "T_FarawayMother_Veil_AquaticLullabyLace",
]

HIP_CODE = r'''
import hou
hou.hipFile.clear(suppress_save_prompt=True)
img = hou.node("/img")
copnet = img.createNode("copnet", "cop_fabric_sheen")
# BaseColor file
base = copnet.createNode("file", "IN_BaseColor")
base.parm("filename1").set("{basecolor_path}")
# Sheen mask file (gray)
sheen = copnet.createNode("file", "IN_Sheen")
sheen.parm("filename1").set("{sheen_path}")
# Composite: sheen over base (screen)
comp = copnet.createNode("composite", "Sheen_Composite")
comp.parm("operation").set(3)  # screen
comp.setInput(0, base)
comp.setInput(1, sheen)
# Curvature falloff (grazing-angle sim via COP curvature)
curv = copnet.createNode("curvature", "Sheen_Falloff")
curv.setInput(0, comp)
# File output
out = copnet.createNode("file", "OUT_SheenMask")
out.parm("filename").set("$HIP/../../Saved/Audit/copernicus_fabric/T_FarawayMother_{suite}_SheenMask.png")
out.setInput(0, curv)
copnet.layoutChildren()
hou.hipFile.save("{hip_path}")
print("[Copernicus Fabric] HIP: {hip_path} suite={suite}")
'''

def main():
    ap = argparse.ArgumentParser(description="Copernicus fabric sheen COP builder")
    ap.add_argument("--suite", choices=["Gown","Mantle","Corset","Cradle","Ornament","Veil","all"], default="Gown")
    ap.add_argument("--hip", type=str, default=str(PROJECT_ROOT / "Tools/Houdini/copernicus/fabric_sheen.hip"))
    ap.add_argument("--dry", action="store_true")
    args = ap.parse_args()

    suites = SUITES if args.suite == "all" else [s for s in SUITES if args.suite.lower() in s.lower()]
    if not suites:
        print(f"[Copernicus Fabric] no suites match {args.suite}")
        return

    for suite in suites:
        code = HIP_CODE.format(
            basecolor_path=f"$HIP/../../Content/Textures/FarawayMother_Suites/{suite}_BaseColor.png",
            sheen_path=f"$HIP/../../Content/Textures/FarawayMother_Suites/{suite}_Sheen.png",
            suite=suite.split("_")[-1],
            hip_path=args.hip.replace("\\","/"),
        )
        if args.dry:
            print(f"[Copernicus Fabric] DRY suite={suite}")
            print(code[:3000])
            continue
        try:
            import hou
        except ImportError:
            print("[Copernicus Fabric] hou missing — dry preview:")
            print(code[:3000])
            return
        hip = Path(args.hip)
        hip.parent.mkdir(parents=True, exist_ok=True)
        exec(code)

    manifest = {
        "schema": "melodia.copernicus_fabric_sheen.v1",
        "seed": SEED,
        "suites": suites,
        "hip": args.hip,
        "outputs": [f"Saved/Audit/copernicus_fabric/T_FarawayMother_{s.split('_')[-1]}_SheenMask.png" for s in suites],
        "contract": "M_Master_Nikki sheen lane: NikkiPearlSheen 0.4, velvet R0.92 silk R0.32, one master versatile merge per Nikki intake §8",
    }
    out_json = PROJECT_ROOT / "Saved/Audit/copernicus_fabric_manifest.json"
    out_json.parent.mkdir(parents=True, exist_ok=True)
    out_json.write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    print(f"[Copernicus Fabric] Manifest → {out_json}")

if __name__ == "__main__":
    main()
