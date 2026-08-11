"""Move MI_Universal_* into theme subfolders under Instances/Environment.

  Environment/Stylized/  — temporal, anime, ink
  Environment/Magical/   — fairy, celestial, dreamy, gold sparkle
  Environment/Biomes/    — already used
  Environment/Triplanar/ — already used

Run via run_material_work_plan.py or:
  py "G:/EnvironmentPortfolio/BS_GodFile/Content/Python/organize_universal_instances.py"
"""
from __future__ import annotations

import json
from pathlib import Path

import material_lib as lib

REPORT = Path(__file__).resolve().parents[2] / "Saved" / "Audit" / "organize_universal_instances.json"
ENV = lib.ENV_INST_DIR

STYLIZED = {
    "MI_Universal_TemporalInk", "MI_Universal_WindSmear", "MI_Universal_InkBoil",
    "MI_Universal_WatercolorDrift", "MI_Universal_AnimeCel", "MI_Universal_SketchLines",
    "MI_Universal_HeatHaze", "MI_Universal_CometTrail",
}

MAGICAL = {
    "MI_Universal_DreamyPastel", "MI_Universal_Constellation", "MI_Universal_CelestialNebula",
    "MI_Universal_GoldLeaf", "MI_Universal_FairyHearts", "MI_Universal_FairyStars",
    "MI_Universal_FairyGarden", "MI_Universal_FairyMoon", "MI_Universal_FairyPetals",
    "MI_Universal_FairyFirefly", "MI_Universal_FairySnowflake", "MI_Universal_MoonlitMetal",
    "MI_Universal_AuroraBorealis", "MI_Universal_MidnightGalaxy", "MI_Universal_Starfield",
    "MI_Universal_SolarCorona", "MI_Universal_DeepSpace", "MI_Universal_NebulaPink",
    "MI_Universal_TwilightSky", "MI_Universal_GlitterGold", "MI_Universal_DiamondSpark",
    "MI_Universal_CottonCandy", "MI_Universal_BlushSatin", "MI_Universal_LavenderMist",
    "MI_Universal_PeachGlow", "MI_Universal_CherryBlossom", "MI_Universal_SakuraPath",
}


def _target_folder(name: str) -> str | None:
    if name in STYLIZED:
        return f"{ENV}/Stylized"
    if name in MAGICAL:
        return f"{ENV}/Magical"
    return None


def main() -> int:
    import unreal

    report: dict = {"moved": [], "skipped": [], "errors": []}

    for sub in ("Stylized", "Magical"):
        lib.ensure_directory(f"{ENV}/{sub}")

    for path in unreal.EditorAssetLibrary.list_assets(ENV, recursive=False, include_folder=False):
        name = path.rsplit("/", 1)[-1].split(".", 1)[0]
        if not name.startswith("MI_Universal_"):
            continue
        dest_folder = _target_folder(name)
        if not dest_folder:
            report["skipped"].append(name)
            continue
        dest_path = f"{dest_folder}/{name}"
        if unreal.EditorAssetLibrary.does_asset_exist(dest_path):
            report["skipped"].append(name)
            continue
        if unreal.EditorAssetLibrary.rename_asset(path, dest_path):
            report["moved"].append({"from": path, "to": dest_path})
            unreal.log(f"[Organize] {name} -> {dest_folder}")
        else:
            report["errors"].append(f"rename failed: {path}")

    REPORT.parent.mkdir(parents=True, exist_ok=True)
    REPORT.write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(json.dumps(report, indent=2))
    return 0 if not report["errors"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
