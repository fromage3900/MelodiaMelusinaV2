"""Audit ProceduralDungeon RoomData level references and room-level script identity."""

import json
from pathlib import Path

import unreal


ROOM_DATA_ROOT = "/Game/Melodia/Roguelike/RoomData"
REPORT_PATH = Path(unreal.Paths.project_saved_dir()) / "Audit" / "melodia_room_level_contract.json"


def object_path(value) -> str | None:
    if value is None:
        return None
    try:
        return value.get_path_name()
    except Exception:
        return str(value)


def main() -> None:
    asset_registry = unreal.AssetRegistryHelpers.get_asset_registry()
    level_subsystem = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
    room_assets = asset_registry.get_assets_by_path(ROOM_DATA_ROOT, recursive=True)
    rows = []

    for asset_data in sorted(room_assets, key=lambda item: str(item.asset_name)):
        room_data = asset_data.get_asset()
        try:
            level_ref = room_data.get_editor_property("level")
            level_path = level_ref.get_path_name() if level_ref else None
            if level_path and "." in level_path:
                level_path = level_path.rsplit(".", 1)[0]
        except Exception as error:
            rows.append({"room_data": str(asset_data.package_name), "error": str(error)})
            continue

        row = {"room_data": str(asset_data.package_name), "level": level_path, "room_level_data": None, "matches": False}
        if level_path:
            level_script = None
            level_name = level_path.rsplit("/", 1)[-1]
            try:
                level_class = unreal.load_class(None, f"{level_path}.{level_name}_C")
                level_script = unreal.get_default_object(level_class) if level_class else None
            except Exception:
                pass
            if level_script is None and level_subsystem.load_level(level_path):
                world = unreal.EditorLevelLibrary.get_editor_world()
                try:
                    level_script = world.get_level_script_actor()
                except Exception:
                    pass
            if level_script is None:
                try:
                    level_script = unreal.EditorLevelLibrary.get_level_script_actor()
                except Exception:
                    pass
            if level_script is None:
                world = unreal.EditorLevelLibrary.get_editor_world()
                actors = unreal.get_editor_subsystem(unreal.EditorActorSubsystem).get_all_level_actors()
                level_script = next((actor for actor in actors if isinstance(actor, unreal.RoomLevel)), None)
            if level_script is not None:
                assigned = level_script.get_editor_property("data")
                row["room_level_data"] = object_path(assigned)
                row["matches"] = assigned == room_data
            else:
                row["error"] = "Loaded map has no ARoomLevel level script actor"
        rows.append(row)

    report = {
        "room_data_count": len(rows),
        "matching_count": sum(1 for row in rows if row.get("matches")),
        "mismatches": [row for row in rows if not row.get("matches")],
        "rows": rows,
    }
    REPORT_PATH.parent.mkdir(parents=True, exist_ok=True)
    REPORT_PATH.write_text(json.dumps(report, indent=2), encoding="utf-8")
    unreal.log(f"[MelodiaRoomContractAudit] {REPORT_PATH}")


if __name__ == "__main__":
    main()
