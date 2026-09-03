"""Repair the minimum ProceduralDungeon room-loading contract for the slice."""
from __future__ import annotations

import json
from pathlib import Path

import unreal

ROOT = "/Game/Melodia/Roguelike"
ROOM_DATA = f"{ROOT}/RoomData"
ROOM_LEVELS = f"{ROOT}/Rooms"
REPORT = Path("G:/EnvironmentPortfolio/BS_GodFile/Saved/Melodia/roguelike_room_loading_repair.json")

LEVEL_BY_FAMILY = {
    "MelodiaGrove": "L_MelodiaGrove",
    "WhisperingGrove": "L_WhisperingGrove",
    "EverburningClearing": "L_EverburningClearing",
    "BossArena": "L_BossArena",
    "TokenShrine": "L_TokenShrine",
    "AbandonedCache": "L_AbandonedCache",
    "PhotoSpot": "L_StarlightReverie",
    "BlessingAltar": "L_BlessingAltar",
}


def main() -> dict:
    rows = []
    for asset_data in unreal.EditorAssetLibrary.list_assets(ROOM_DATA, recursive=False, include_folder=False):
        asset_path = asset_data.split(".")[0]
        name = asset_path.rsplit("/", 1)[-1]
        room = unreal.load_object(None, asset_path)
        family = next((key for key in LEVEL_BY_FAMILY if key in name), None)
        if room is None or family is None:
            rows.append({"asset": asset_path, "ok": False, "error": "unmapped or unloadable"})
            continue
        level_path = f"{ROOM_LEVELS}/{LEVEL_BY_FAMILY[family]}"
        level_exists = unreal.EditorAssetLibrary.does_asset_exist(level_path)
        level_asset = unreal.EditorAssetLibrary.load_asset(level_path) if level_exists else None
        error = ""
        try:
            # UE 5.8 nativizes TSoftObjectPtr<UWorld> from a loaded World object,
            # not from an unreal.SoftObjectPath wrapper.
            room.set_editor_property("level", level_asset)
            room.modify()
            saved = unreal.EditorAssetLibrary.save_asset(asset_path, only_if_is_dirty=False)
        except Exception as exc:
            saved = False
            error = str(exc)
        resolved = str(room.get_editor_property("level")) if room else ""
        rows.append({
            "asset": asset_path,
            "level": level_path,
            "level_exists": level_exists,
            "resolved": resolved,
            "saved": bool(saved),
            "error": error,
            "ok": level_exists and bool(resolved) and bool(saved),
        })
    result = {"rooms": rows, "ok": bool(rows) and all(row["ok"] for row in rows)}
    REPORT.parent.mkdir(parents=True, exist_ok=True)
    REPORT.write_text(json.dumps(result, indent=2), encoding="utf-8")
    print(json.dumps(result, indent=2))
    return result


if __name__ == "__main__":
    main()
