#!/usr/bin/env python3
"""
materialize_melodia_wbp_assets.py - Materialize all 30 Melodia WBP assets in Unreal.

Creates any missing WidgetBlueprint assets under /Game/Melodia/UI/ and configures
their parent classes (UUserWidget, UMelodiaRhythmHUDWidget, UMelodiaMobileHUD).

Usage (inside Unreal or via UnrealEditor-Cmd):
    py Content/Python/materialize_melodia_wbp_assets.py
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SPECS_DIR = ROOT / "specs" / "ui"

WBP_SPECS = [
    ("WBP_MainMenu", "UserWidget"),
    ("WBP_SaveLoad", "UserWidget"),
    ("WBP_Settings", "UserWidget"),
    ("WBP_ComicOrrery", "UserWidget"),
    ("WBP_QuestJournal", "UserWidget"),
    ("WBP_NPCInfo", "UserWidget"),
    ("WBP_Inventory", "UserWidget"),
    ("WBP_Title", "UserWidget"),
    ("WBP_PartyLoadout", "UserWidget"),
    ("WBP_FieldHUD", "UserWidget"),
    ("WBP_Battle_Command", "UserWidget"),
    ("WBP_Battle_Rhythm", "MelodiaRhythmHUDWidget"),
    ("WBP_Battle_Enemy", "UserWidget"),
    ("WBP_Battle_Results", "UserWidget"),
    ("WBP_SkillCodex", "UserWidget"),
    ("WBP_Battle_Mobile", "MelodiaMobileHUD"),
    ("WBP_GradePop", "UserWidget"),
    ("WBP_SheetMusicRoll", "UserWidget"),
    ("WBP_NoteGlyph", "UserWidget"),
    ("WBP_MeasureMarker", "UserWidget"),
    ("WBP_PlaybackHead", "UserWidget"),
    ("WBP_ElementWheel", "UserWidget"),
    ("WBP_SPBar", "UserWidget"),
    ("WBP_ULTCharge", "UserWidget"),
    ("WBP_DialogueBubble", "UserWidget"),
    ("WBP_MenuButton", "UserWidget"),
    ("WBP_BlessingBurden", "UserWidget"),
    ("WBP_IntensityWarning", "UserWidget"),
    ("WBP_DissonanceBanner", "UserWidget"),
    ("WBP_ResonanceBond", "UserWidget"),
]


def materialize():
    import unreal

    asset_tools = unreal.AssetToolsHelpers.get_asset_tools()
    factory = unreal.WidgetBlueprintFactory()
    editor_asset_lib = unreal.EditorAssetLibrary

    dest_folder = "/Game/Melodia/UI"
    created = []
    existing = []

    for name, parent_type in WBP_SPECS:
        asset_path = f"{dest_folder}/{name}"
        if editor_asset_lib.does_asset_exist(asset_path):
            existing.append(name)
            continue

        parent_cls = unreal.UserWidget
        if parent_type == "MelodiaRhythmHUDWidget":
            cls = getattr(unreal, "MelodiaRhythmHUDWidget", None)
            if cls:
                parent_cls = cls
        elif parent_type == "MelodiaMobileHUD":
            cls = getattr(unreal, "MelodiaMobileHUD", None)
            if cls:
                parent_cls = cls

        factory.set_editor_property("ParentClass", parent_cls)
        new_asset = asset_tools.create_asset(name, dest_folder, unreal.WidgetBlueprint, factory)
        if new_asset:
            created.append(name)
            editor_asset_lib.save_asset(asset_path)
            print(f"[WBP Materializer] Created {name} (parent: {parent_cls.__name__})")
        else:
            print(f"[WBP Materializer] Failed to create {name}")

    print(f"\n[WBP Materializer] Complete:")
    print(f"  - Created: {len(created)} assets: {created}")
    print(f"  - Already Existing: {len(existing)} assets")

    # Save summary report
    report = {
        "total": len(WBP_SPECS),
        "created_count": len(created),
        "existing_count": len(existing),
        "created": created,
        "existing": existing,
    }
    report_path = ROOT / "Saved" / "Audit" / "melodia_wbp_materialize_report.json"
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text(json.dumps(report, indent=2), encoding="utf-8")


if __name__ == "__main__":
    materialize()
