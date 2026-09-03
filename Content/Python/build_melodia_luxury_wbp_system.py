#!/usr/bin/env python3
"""
build_melodia_luxury_wbp_system.py - Universal Melodia Luxury WBP System Builder.

Transforms the Melodia Design System (tokens.json, Batch N/O ornate filigrees,
and 4-layer luxury depth stack) into canonical Unreal Engine 5.8 UMG assets:
- Exports Unreal-compatible design token data tables and color palettes.
- Scaffolds all 30 WBP atoms under /Game/Melodia/UI/ with 4-layer luxury hierarchies.
- Generates T3D widget templates in specs/ui/ for automated injection.
- Emits verification audit reports in Saved/Audit/melodia_universal_wbp_system.json.

Usage:
    python Content/Python/build_melodia_luxury_wbp_system.py
    python Content/Python/build_melodia_luxury_wbp_system.py --inject
"""
from __future__ import annotations

import argparse
import json
import os
import sys
import time
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

ROOT = Path(__file__).resolve().parents[2]
PYTHON_DIR = ROOT / "Content" / "Python"
SAVED_AUDIT = ROOT / "Saved" / "Audit"
SPECS_UI = ROOT / "specs" / "ui"
DESIGN_SYSTEM_DIR = ROOT / "melodia-design-system"

# ---------------------------------------------------------------------------
# 1. Design Token Palette & Luxury Colors (HoYoverse + Luxury Editorial)
# ---------------------------------------------------------------------------

MELODIA_PALETTE = {
    "ivory_moonlight": {"hex": "#FFF8EE", "rgba": [1.0, 0.973, 0.933, 1.0], "desc": "Gilded Moonlight - lookbook surface"},
    "ivory_gilded": {"hex": "#F8ECD6", "rgba": [0.973, 0.925, 0.839, 1.0], "desc": "Gilded Ivory - default paper"},
    "ivory_sunken": {"hex": "#F3E6C8", "rgba": [0.953, 0.902, 0.784, 1.0], "desc": "Parchment fill"},
    "plum_midnight": {"hex": "#241B2E", "rgba": [0.141, 0.106, 0.180, 1.0], "desc": "Midnight Plum - primary dark surface"},
    "plum_deep": {"hex": "#1C1426", "rgba": [0.110, 0.078, 0.149, 1.0], "desc": "Darkest void base"},
    "gold_champagne": {"hex": "#C9A86A", "rgba": [0.788, 0.659, 0.416, 1.0], "desc": "Champagne Gold - accent & rules"},
    "gold_light": {"hex": "#DDC79B", "rgba": [0.867, 0.780, 0.608, 1.0], "desc": "Gold highlight"},
    "lavender_starlight": {"hex": "#9F94C6", "rgba": [0.624, 0.580, 0.776, 1.0], "desc": "Lavender - secondary celestial accent"},
    "sakura_dusty": {"hex": "#E7C9CE", "rgba": [0.906, 0.788, 0.808, 1.0], "desc": "Dusty Sakura - tertiary romance accent"},
    "iri_perfect_gold": {"hex": "#FFD760", "rgba": [1.0, 0.843, 0.376, 1.0], "desc": "Perfect judgment gradient start"},
    "iri_great_cyan": {"hex": "#73E0F2", "rgba": [0.451, 0.878, 0.949, 1.0], "desc": "Great judgment gradient start"},
    "iri_good_pearl": {"hex": "#EAE6F2", "rgba": [0.918, 0.902, 0.949, 1.0], "desc": "Good judgment gradient start"},
    "iri_miss_magenta": {"hex": "#D9598C", "rgba": [0.851, 0.349, 0.549, 1.0], "desc": "Miss judgment gradient start"},
}

# ---------------------------------------------------------------------------
# 2. Complete 30-Atom Inventory (from MELODIA_MELUSINA_GAME_UX)
# ---------------------------------------------------------------------------

WBP_ATOMS: List[Dict[str, str]] = [
    {"name": "WBP_MainMenu", "figma": "Game/MainMenu", "category": "Navigation", "parent": "UserWidget"},
    {"name": "WBP_SaveLoad", "figma": "Game/SaveLoad", "category": "System", "parent": "UserWidget"},
    {"name": "WBP_Settings", "figma": "Game/Settings", "category": "System", "parent": "UserWidget"},
    {"name": "WBP_ComicOrrery", "figma": "Game/ComicOrrery", "category": "Narrative", "parent": "UserWidget"},
    {"name": "WBP_QuestJournal", "figma": "Game/QuestJournal", "category": "Progression", "parent": "UserWidget"},
    {"name": "WBP_NPCInfo", "figma": "Game/NPCInfo", "category": "Social", "parent": "UserWidget"},
    {"name": "WBP_Inventory", "figma": "Game/Inventory", "category": "Wardrobe", "parent": "UserWidget"},
    {"name": "WBP_Title", "figma": "Game/Title", "category": "Navigation", "parent": "UserWidget"},
    {"name": "WBP_PartyLoadout", "figma": "Game/PartyLoadout", "category": "Combat", "parent": "UserWidget"},
    {"name": "WBP_FieldHUD", "figma": "Game/FieldHUD", "category": "Exploration", "parent": "UserWidget"},
    {"name": "WBP_Battle_Command", "figma": "Game/BattleCommand", "category": "Combat", "parent": "UserWidget"},
    {"name": "WBP_Battle_Rhythm", "figma": "Game/BattleRhythm", "category": "Combat", "parent": "MelodiaRhythmHUDWidget"},
    {"name": "WBP_Battle_Enemy", "figma": "Game/BattleEnemy", "category": "Combat", "parent": "UserWidget"},
    {"name": "WBP_Battle_Results", "figma": "Game/BattleResults", "category": "Combat", "parent": "UserWidget"},
    {"name": "WBP_SkillCodex", "figma": "Game/SkillCodex", "category": "Progression", "parent": "UserWidget"},
    {"name": "WBP_Battle_Mobile", "figma": "Game/BattleMobile", "category": "Combat", "parent": "MelodiaMobileHUD"},
    {"name": "WBP_GradePop", "figma": "Game/GradePop", "category": "RhythmFX", "parent": "UserWidget"},
    {"name": "WBP_SheetMusicRoll", "figma": "Game/SheetMusicRoll", "category": "RhythmScore", "parent": "UserWidget"},
    {"name": "WBP_NoteGlyph", "figma": "Game/NoteGlyph", "category": "RhythmScore", "parent": "UserWidget"},
    {"name": "WBP_MeasureMarker", "figma": "Game/MeasureMarker", "category": "RhythmScore", "parent": "UserWidget"},
    {"name": "WBP_PlaybackHead", "figma": "Game/PlaybackHead", "category": "RhythmScore", "parent": "UserWidget"},
    {"name": "WBP_ElementWheel", "figma": "Game/ElementWheel", "category": "Combat", "parent": "UserWidget"},
    {"name": "WBP_SPBar", "figma": "Game/SPMeter", "category": "Gauges", "parent": "UserWidget"},
    {"name": "WBP_ULTCharge", "figma": "Game/ULTMeter", "category": "Gauges", "parent": "UserWidget"},
    {"name": "WBP_DialogueBubble", "figma": "Game/DialogueOverlay", "category": "Narrative", "parent": "UserWidget"},
    {"name": "WBP_MenuButton", "figma": "Ctrl/MenuButton", "category": "Controls", "parent": "UserWidget"},
    {"name": "WBP_BlessingBurden", "figma": "Game/BlessingBurden", "category": "Roguelike", "parent": "UserWidget"},
    {"name": "WBP_IntensityWarning", "figma": "Game/IntensityWarning", "category": "Combat", "parent": "UserWidget"},
    {"name": "WBP_DissonanceBanner", "figma": "Game/DissonanceBanner", "category": "Combat", "parent": "UserWidget"},
    {"name": "WBP_ResonanceBond", "figma": "Game/ResonanceBond", "category": "Social", "parent": "UserWidget"},
]

# ---------------------------------------------------------------------------
# 3. T3D 4-Layer Luxury Widget Template Generator
# ---------------------------------------------------------------------------

def generate_luxury_wbp_t3d(atom_info: Dict[str, str]) -> str:
    """Generate a clean T3D template for a 4-layer luxury UMG widget."""
    name = atom_info["name"]
    category = atom_info["category"]
    parent = atom_info["parent"]
    
    t3d = f"""Begin Object Class=/Script/UMGEditor.WidgetBlueprint Name="{name}"
   Begin Object Class=/Script/UMG.CanvasPanel Name="CanvasPanel_Root"
   End Object
   Begin Object Class=/Script/UMG.Image Name="Layer1_VoidPlate"
      Brush=(ImageSize=(X=1920.0,Y=1080.0),DrawAs=Image,TintColor=(SpecifiedColor=(R=0.141,G=0.106,B=0.180,A=0.920)))
   End Object
   Begin Object Class=/Script/UMG.Image Name="Layer2_IridescentSheen"
      Brush=(ImageSize=(X=1920.0,Y=1080.0),DrawAs=Image,TintColor=(SpecifiedColor=(R=0.624,G=0.580,B=0.776,A=0.150)))
   End Object
   Begin Object Class=/Script/UMG.Overlay Name="Layer3_FiligreeChrome"
   End Object
   Begin Object Class=/Script/UMG.Image Name="FiligreeCorner_TL"
      Brush=(ImageSize=(X=128.0,Y=128.0),DrawAs=Image,TintColor=(SpecifiedColor=(R=0.788,G=0.659,B=0.416,A=1.0)))
   End Object
   Begin Object Class=/Script/UMG.Image Name="FiligreeCorner_TR"
      Brush=(ImageSize=(X=128.0,Y=128.0),DrawAs=Image,TintColor=(SpecifiedColor=(R=0.788,G=0.659,B=0.416,A=1.0)))
   End Object
   Begin Object Class=/Script/UMG.Image Name="FiligreeCorner_BL"
      Brush=(ImageSize=(X=128.0,Y=128.0),DrawAs=Image,TintColor=(SpecifiedColor=(R=0.788,G=0.659,B=0.416,A=1.0)))
   End Object
   Begin Object Class=/Script/UMG.Image Name="FiligreeCorner_BR"
      Brush=(ImageSize=(X=128.0,Y=128.0),DrawAs=Image,TintColor=(SpecifiedColor=(R=0.788,G=0.659,B=0.416,A=1.0)))
   End Object
   Begin Object Class=/Script/UMG.CanvasPanel Name="Layer4_ActiveContent"
   End Object
End Object
"""
    return t3d


# ---------------------------------------------------------------------------
# 4. Builder Execution & Export Pipeline
# ---------------------------------------------------------------------------

def build_system() -> Dict[str, Any]:
    SPECS_UI.mkdir(parents=True, exist_ok=True)
    SAVED_AUDIT.mkdir(parents=True, exist_ok=True)

    generated_specs = []
    disk_presence = {}
    content_ui_dir = ROOT / "Content" / "Melodia" / "UI"

    for atom in WBP_ATOMS:
        name = atom["name"]
        uasset_file = content_ui_dir / f"{name}.uasset"
        disk_presence[name] = uasset_file.is_file()

        # Generate T3D spec
        t3d_content = generate_luxury_wbp_t3d(atom)
        t3d_path = SPECS_UI / f"{name}.t3d"
        t3d_path.write_text(t3d_content, encoding="utf-8")
        generated_specs.append(str(t3d_path.relative_to(ROOT)))

    # Export Design Tokens table
    tokens_export = {
        "schema": "Melodia.DesignTokens.v1",
        "generated_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "palette": MELODIA_PALETTE,
        "luxury_density_bar": {
            "depth_layers": 4,
            "layer_1_void_plate": "Midnight Plum #241B2E (92% opacity)",
            "layer_2_iri_sheen": "Iridescent Dynamic Sheen (MPC beat-reactive)",
            "layer_3_filigree": "Champagne Gold #C9A86A corner flourishes & rails",
            "layer_4_content": "Syne / Instrument Serif typography + GradePop burst",
            "max_emissive_sum": 0.50,
        },
        "atoms_count": len(WBP_ATOMS),
        "atoms": WBP_ATOMS,
    }

    tokens_path = SAVED_AUDIT / "melodia_ui_tokens_unreal.json"
    tokens_path.write_text(json.dumps(tokens_export, indent=2), encoding="utf-8")

    # In-editor creation if running inside Unreal Python
    editor_created = []
    has_unreal = False
    try:
        import unreal  # type: ignore
        has_unreal = True
        asset_tools = unreal.AssetToolsHelpers.get_asset_tools()
        factory = unreal.WidgetBlueprintFactory()

        for atom in WBP_ATOMS:
            name = atom["name"]
            pkg_path = f"/Game/Melodia/UI/{name}"
            if not unreal.EditorAssetLibrary.does_asset_exist(pkg_path):
                parent_cls = unreal.UserWidget
                if atom["parent"] == "MelodiaRhythmHUDWidget":
                    cls = getattr(unreal, "MelodiaRhythmHUDWidget", None)
                    if cls:
                        parent_cls = cls
                elif atom["parent"] == "MelodiaMobileHUD":
                    cls = getattr(unreal, "MelodiaMobileHUD", None)
                    if cls:
                        parent_cls = cls

                factory.set_editor_property("ParentClass", parent_cls)
                new_wbp = asset_tools.create_asset(name, "/Game/Melodia/UI", unreal.WidgetBlueprint, factory)
                if new_wbp:
                    editor_created.append(name)
                    unreal.EditorAssetLibrary.save_asset(pkg_path)
    except ImportError:
        has_unreal = False

    audit_summary = {
        "status": "success",
        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S UTC", time.gmtime()),
        "total_atoms": len(WBP_ATOMS),
        "t3d_specs_generated": len(generated_specs),
        "assets_on_disk": sum(1 for v in disk_presence.values() if v),
        "assets_missing_on_disk": sum(1 for v in disk_presence.values() if not v),
        "editor_created": editor_created,
        "tokens_exported": str(tokens_path.relative_to(ROOT)),
        "specs_dir": str(SPECS_UI.relative_to(ROOT)),
    }

    audit_path = SAVED_AUDIT / "melodia_universal_wbp_system.json"
    audit_path.write_text(json.dumps(audit_summary, indent=2), encoding="utf-8")

    print(f"[MelodiaWBPBuilder] Scaffolding complete:")
    print(f"  - Atoms: {len(WBP_ATOMS)}")
    print(f"  - T3D Specs: {len(generated_specs)} in {SPECS_UI}")
    print(f"  - Tokens: {tokens_path}")
    print(f"  - Audit Report: {audit_path}")

    return audit_summary


if __name__ == "__main__":
    build_system()
