"""Repair the one-to-one ProceduralDungeon RoomData <-> ARoomLevel identity contract."""

import json
import os
import re
from pathlib import Path

import unreal


ROOM_DATA_ROOT = "/Game/Melodia/Roguelike/RoomData"
REPORT_PATH = Path(unreal.Paths.project_saved_dir()) / "Audit" / "melodia_room_level_repair.json"
VARIANT_PATTERN = re.compile(r"^(?P<stem>.+)_V(?P<variant>\d+)$")


def generated_level_cdo(level_path: str):
    level_name = level_path.rsplit("/", 1)[-1]
    level_class = unreal.load_class(None, f"{level_path}.{level_name}_C")
    return unreal.get_default_object(level_class) if level_class else None


def main() -> None:
    registry = unreal.AssetRegistryHelpers.get_asset_registry()
    editor_assets = unreal.EditorAssetLibrary
    level_subsystem = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
    rows = []

    room_assets = sorted(registry.get_assets_by_path(ROOM_DATA_ROOT, recursive=True), key=lambda item: str(item.asset_name))
    requested_name = os.environ.get("MELODIA_ROOM_REPAIR_NAME", "").strip()
    if requested_name:
        room_assets = [item for item in room_assets if str(item.asset_name) == requested_name]
        if len(room_assets) != 1:
            raise RuntimeError(f"Expected exactly one RoomData named {requested_name}; found {len(room_assets)}")
    for asset_data in room_assets:
        room_data = asset_data.get_asset()
        room_data_path = str(asset_data.package_name)
        source_world = room_data.get_editor_property("level")
        if source_world is None:
            rows.append({"room_data": room_data_path, "ok": False, "error": "RoomData Level is null"})
            continue

        source_level = source_world.get_path_name().rsplit(".", 1)[0]
        match = VARIANT_PATTERN.match(str(asset_data.asset_name))
        variant = int(match.group("variant")) if match else 1
        base_level = re.sub(r"(?:_V\d+)+$", "", source_level)
        target_level = base_level if variant == 1 else f"{base_level}_V{variant}"

        if target_level != source_level and not editor_assets.does_asset_exist(target_level):
            duplicated = editor_assets.duplicate_asset(source_level, target_level)
            if duplicated is None:
                rows.append({"room_data": room_data_path, "level": target_level, "ok": False, "error": "Level duplication failed"})
                continue

        target_world = editor_assets.load_asset(target_level)
        if target_world is None:
            rows.append({"room_data": room_data_path, "level": target_level, "ok": False, "error": "Target level load failed"})
            continue

        room_data.set_editor_property("level", target_world)
        editor_assets.save_loaded_asset(room_data, only_if_is_dirty=False)

        # World wrappers held by Python prevent ULevelEditorSubsystem from collecting the
        # previous editor world. RoomData stores a soft reference, so release wrappers here.
        source_world = None
        target_world = None
        duplicated = None
        unreal.SystemLibrary.collect_garbage()

        if not level_subsystem.load_level(target_level):
            rows.append({"room_data": room_data_path, "level": target_level, "ok": False, "error": "Editor level load failed"})
            continue

        level_cdo = generated_level_cdo(target_level)
        if level_cdo is None or not isinstance(level_cdo, unreal.RoomLevel):
            rows.append({"room_data": room_data_path, "level": target_level, "ok": False, "error": "Level script is not ARoomLevel"})
            continue

        level_cdo.set_editor_property("data", room_data)
        saved = level_subsystem.save_current_level()
        assigned = level_cdo.get_editor_property("data")
        ok = bool(saved and assigned == room_data)
        rows.append({
            "room_data": room_data_path,
            "level": target_level,
            "level_script_data": assigned.get_path_name() if assigned else None,
            "ok": ok,
            "error": None if ok else "Map save or post-save identity check failed",
        })

    report = {
        "total": len(rows),
        "passed": sum(1 for row in rows if row.get("ok")),
        "failed": sum(1 for row in rows if not row.get("ok")),
        "rows": rows,
    }
    report_path = REPORT_PATH if not requested_name else REPORT_PATH.with_name(f"melodia_room_level_repair_{requested_name}.json")
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text(json.dumps(report, indent=2), encoding="utf-8")
    unreal.log(f"[MelodiaRoomContractRepair] {report_path}")
    if report["failed"]:
        raise RuntimeError(f"Room contract repair failed for {report['failed']} assets")


if __name__ == "__main__":
    main()
