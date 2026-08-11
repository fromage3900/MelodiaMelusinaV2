"""Compile and save the Melusina Blueprints required for hands-on JRPG testing."""
from __future__ import annotations

import json
from pathlib import Path
import unreal

ASSETS = [
    "/Game/MelodiaIntegration/Blueprints/BP_MelusinaJRPGCharacter",
    "/Game/Melodia/Characters/Melusina/Hair/ABP_Melusina_WaterHair",
    "/Game/Melodia/Characters/Melusina/ABP_Melusina_Current",
    "/Game/Melodia/Characters/Melusina/BP_Melusina",
]
OUT = Path(unreal.Paths.project_dir()) / "Saved" / "Audit" / "melusina_blueprint_compile.json"

rows = []
for asset_path in ASSETS:
    asset = unreal.load_asset(asset_path)
    row = {"asset": asset_path, "loads": bool(asset), "saved": False}
    if asset:
        unreal.BlueprintEditorLibrary.compile_blueprint(asset)
        row["generated_class"] = asset.generated_class().get_path_name() if asset.generated_class() else ""
        row["saved"] = bool(unreal.EditorAssetLibrary.save_loaded_asset(asset, only_if_is_dirty=False))
    rows.append(row)

report = {"assets": rows}
report["ok"] = all(row["loads"] and row["saved"] and row.get("generated_class") for row in rows)
OUT.parent.mkdir(parents=True, exist_ok=True)
OUT.write_text(json.dumps(report, indent=2), encoding="utf-8")
unreal.log("MELUSINA_BLUEPRINT_COMPILE: " + json.dumps(report, sort_keys=True))
if not report["ok"]:
    raise RuntimeError("One or more required Melusina Blueprints failed to load, compile, or save")
