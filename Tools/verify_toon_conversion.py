"""Disk-verify Substrate Toon status for the ED + remaining-master conversion set
and rebuild a consolidated audit at Saved/Audit/substrate_toon_conversion_2026-08-13.json.

Pure disk scan (no unreal import). Checks the .uasset bytes for the
MaterialExpressionSubstrateToonBSDF class string.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CONTENT = ROOT / "Content"

TARGETS = {
    # Electric Dreams / Megascans master set
    "/Game/Custom/CustomMaterials/Materials/Master_Materials/Custom_Decal/M_MS_CustomDecal_CNR": "ed",
    "/Game/Custom/CustomMaterials/Materials/Master_Materials/Custom_Decal/M_MS_CustomDecal_CR": "ed",
    "/Game/Custom/CustomMaterials/Materials/Master_Materials/Custom_MS_Master/M_MS_Default_Overwrite/M_MS_CustomDefault": "ed",
    "/Game/Custom/CustomMaterials/Materials/Master_Materials/Custom_MS_Master/M_MS_Foliage_Overwrite/M_MS_CustomFoliage": "ed",
    "/Game/Custom/CustomMaterials/Materials/Master_Materials/Custom_MS_Master/M_MS_Foliage_Overwrite/M_MS_CustomFoliageNoOpacity": "ed",
    "/Game/Custom/CustomMaterials/Materials/Master_Materials/Custom_MS_Master/M_MS_Foliage_Overwrite/M_MS_CustomFoliageNoOpacityNoWPO": "ed",
    "/Game/Custom/CustomMaterials/Materials/Master_Materials/Custom_MS_Master/M_MS_Foliage_Overwrite/M_MS_CustomFoliageNoWPO": "ed",
    "/Game/Custom/CustomMaterials/Materials/Master_Materials/M_DefaultTextEmissive": "ed",
    "/Game/Custom/CustomMaterials/Materials/Master_Materials/M_MS_Default_Material_VT_DynamicLayering": "ed",
    "/Game/MSPresets/MS_Foliage_Material_LATEST/AssetZooMaterials/M_FloorGrid_Master": "ed",
    "/Game/MSPresets/MS_Foliage_Material_LATEST/GlobalFoliageActor/Materials/M_UI_Element": "ed",
    "/Game/MSPresets/MS_Foliage_Material_LATEST/MasterMaterials/M_Foliage": "ed",
    "/Game/MSPresets/M_MS_Billboard_Material/M_MS_Billboard_Material": "ed",
    "/Game/MSPresets/M_MS_Decal_Material_VT/M_MS_Decal_Material_VT": "ed",
    "/Game/MSPresets/M_MS_Decal_Material_VT/M_MS_Decal_Material_VT_NoNormalAlbedo1": "ed",
    "/Game/MSPresets/M_MS_Default_Material/M_MS_Default_Material": "ed",
    "/Game/MSPresets/M_MS_Default_Material_VT/M_MS_Default_Material_VT": "ed",
    "/Game/MSPresets/M_MS_Default_Material_VT/M_MS_Default_Material_VT_WaterTest": "ed",
    "/Game/MSPresets/M_MS_Foliage_Material/M_MS_Foliage_Material": "ed",
    "/Game/MSPresets/M_MS_Surface_Material/M_MS_Surface_Material": "ed",
    "/Game/MSPresets/M_MS_Surface_Material_VT/M_MS_Surface_Material_VT": "ed",
    # Remaining EnvSandbox masters
    "/Game/EnvSandbox/Materials/Masters/M_Master_Simple_Universal": "env",
    "/Game/EnvSandbox/Materials/Masters/M_Master_Toon_Universal_NikkiChainRepair": "env",
    "/Game/EnvSandbox/Materials/Masters/M_Melodia_StarryNight_Impressionist": "env",
    "/Game/EnvSandbox/Materials/Masters/M_Melodia_StarryNight_VanGogh": "env",
    "/Game/EnvSandbox/Materials/Masters/M_MelodiaVoidGradient": "env",
    "/Game/EnvSandbox/Materials/Masters/M_PP_Underwater": "env",
    "/Game/EnvSandbox/Materials/Masters/M_SpaceParallax_Test": "env",
    "/Game/EnvSandbox/Materials/Masters/M_Water_Master_Grand_v10_Substrate": "env",
    "/Game/EnvSandbox/Materials/Masters/M_Water_Master_Grand_v10_Upgrade": "env",
    "/Game/EnvSandbox/Materials/Masters/M_Water_Master_Grand_v7": "env",
    "/Game/EnvSandbox/Materials/Masters/M_Water_Master_Grand_v9": "env",
    "/Game/EnvSandbox/Materials/Masters/M_Water_Underwater_Post_v10": "env",
    "/Game/EnvSandbox/Materials/Masters/M_Water_Underwater_Post_v9": "env",
    "/Game/EnvSandbox/Materials/Masters/M_WaterCausticsProjector_v7": "env",
}


def game_to_disk(game: str) -> Path:
    rel = game.removeprefix("/Game/").replace("/", "\\")
    return CONTENT / rel


def main() -> int:
    rows = []
    for path, kind in TARGETS.items():
        disk = Path(str(game_to_disk(path)) + ".uasset")
        if not disk.exists():
            rows.append({"path": path, "group": kind, "status": "missing"})
            continue
        txt = disk.read_bytes().decode("ascii", "ignore")
        has_toon = "ToonBSDF" in txt and "SubstrateToon" in txt
        rows.append({"path": path, "group": kind, "status": "toon" if has_toon else "not_toon"})

    summary = {
        "total": len(rows),
        "toon": sum(1 for r in rows if r["status"] == "toon"),
        "not_toon": sum(1 for r in rows if r["status"] == "not_toon"),
        "missing": sum(1 for r in rows if r["status"] == "missing"),
    }
    report = {
        "generated": "2026-08-13",
        "title": "Substrate Toon conversion verify - ED masters + remaining EnvSandbox masters",
        "method": "disk byte scan for MaterialExpressionSubstrateToonBSDF (ToonBSDF + SubstrateToon)",
        "summary": summary,
        "rows": rows,
    }
    out = ROOT / "Saved" / "Audit" / "substrate_toon_conversion_2026-08-13.json"
    out.write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(json.dumps(summary, indent=2))
    for r in rows:
        if r["status"] != "toon":
            print(f"  [{r['status']}] {r['path']}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
