"""Reparent roguelike room Level Blueprints to ProceduralDungeon.RoomLevel."""
from __future__ import annotations

import json
from pathlib import Path

import unreal

ROOT = "/Game/Melodia/Roguelike/Rooms"
LEVELS = [
    "L_MelodiaGrove", "L_WhisperingGrove", "L_EverburningClearing",
    "L_BossArena", "L_TokenShrine", "L_AbandonedCache",
    "L_StarlightReverie", "L_BlessingAltar",
]
REPORT = Path("G:/EnvironmentPortfolio/BS_GodFile/Saved/Melodia/roguelike_room_level_blueprints.json")


def main() -> dict:
    level_editor = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
    unreal_editor = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem)
    parent = unreal.load_class(None, "/Script/ProceduralDungeon.RoomLevel")
    rows = []
    for name in LEVELS:
        path = f"{ROOT}/{name}"
        loaded = bool(level_editor.load_level(path))
        world = unreal_editor.get_editor_world() if loaded else None
        level = level_editor.get_current_level() if world else None
        blueprint = None
        error = ""
        try:
            blueprint = level.get_level_script_blueprint(True) if level else None
            unreal.BlueprintEditorLibrary.reparent_blueprint(blueprint, parent)
            unreal.BlueprintEditorLibrary.compile_blueprint(blueprint)
            level_editor.save_current_level()
        except Exception as exc:
            error = str(exc)
        generated_parent = blueprint.generated_class().get_super_class() if blueprint and blueprint.generated_class() else None
        rows.append({
            "level": path,
            "loaded": loaded,
            "blueprint": blueprint.get_path_name() if blueprint else "",
            "parent": generated_parent.get_path_name() if generated_parent else "",
            "error": error,
            "ok": bool(blueprint and generated_parent is parent and not error),
        })
    result = {"levels": rows, "ok": all(row["ok"] for row in rows)}
    REPORT.parent.mkdir(parents=True, exist_ok=True)
    REPORT.write_text(json.dumps(result, indent=2), encoding="utf-8")
    print(json.dumps(result, indent=2))
    return result


if __name__ == "__main__":
    main()
