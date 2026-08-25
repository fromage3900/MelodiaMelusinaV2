"""Stage Ultra Dynamic Sky on the isolated Gaea world-generation maps.

This is an editor-only, idempotent staging pass. It creates World Partition
test maps when they do not exist, places one project-owned UDS actor, and
saves each map. It does not touch production worlds, gameplay state, or the
RenderTests lookdev namespace.

Run from UE 5.8 with:
    UnrealEditor.exe BS_GodFile.uproject -ExecutePythonScript=.../stage_uds_sky_gaea_levels.py
"""

import json
import os
import unreal


MAPS = [
    ("SakuraTerrace", "/Game/_PROJECT/ResonantWorld/Offline/GaeaSetups/SakuraTerrace/L_Gaea_SakuraTerrace_WP"),
    ("LiquidCathedral", "/Game/_PROJECT/ResonantWorld/Offline/GaeaSetups/LiquidCathedral/L_Gaea_LiquidCathedral_WP"),
    ("CadenceCrystalRidge", "/Game/_PROJECT/ResonantWorld/Offline/GaeaSetups/CadenceCrystalRidge/L_Gaea_CadenceCrystalRidge_WP"),
    ("FugueGrotto", "/Game/_PROJECT/ResonantWorld/Offline/GaeaSetups/FugueGrotto/L_Gaea_FugueGrotto_WP"),
]
UDS_BLUEPRINT = "/Game/UltraDynamicSky/Blueprints/Ultra_Dynamic_Sky"
REPORT_PATH = os.path.abspath(
    os.path.join(unreal.Paths.project_saved_dir(), "Audit", "gaea_setups", "uds_sky_stage_report.json")
)


def _actor_key(actor):
    try:
        return actor.get_actor_label()
    except Exception:
        return actor.get_name()


def _find_uds(actor_subsystem, label):
    for actor in actor_subsystem.get_all_level_actors():
        if _actor_key(actor) == label:
            return actor
    return None


def _stage_one(level_subsystem, actor_subsystem, world, theme, map_path, uds_class):
    created_map = False
    loaded = unreal.EditorAssetLibrary.does_asset_exist(map_path)
    if loaded:
        loaded = bool(level_subsystem.load_level(map_path))
    else:
        loaded = bool(level_subsystem.new_level(map_path, True))
        created_map = loaded
    if not loaded:
        return {
            "theme": theme,
            "map": map_path,
            "status": "ERROR",
            "error": "level load/create failed",
        }

    world = unreal.EditorLevelLibrary.get_editor_world()
    label = "UDS_" + theme
    actor = _find_uds(actor_subsystem, label)
    created_actor = False
    if actor is None:
        actor = actor_subsystem.spawn_actor_from_class(
            uds_class, unreal.Vector(0.0, 0.0, 0.0), unreal.Rotator(0.0, 0.0, 0.0)
        )
        if actor is None:
            return {
                "theme": theme,
                "map": map_path,
                "status": "ERROR",
                "error": "UDS actor spawn failed",
            }
        actor.set_actor_label(label)
        created_actor = True

    actor.set_folder_path("WorldGen/UDS")
    try:
        actor.tags = ["MelodiaWorldGen", "UDS", "GaeaSetup", theme]
    except Exception:
        pass
    try:
        actor.set_is_spatially_loaded(False)
    except Exception:
        pass

    saved = bool(unreal.EditorLoadingAndSavingUtils.save_map(world))
    return {
        "theme": theme,
        "map": map_path,
        "status": "PASS" if saved else "ERROR",
        "created_map": created_map,
        "created_actor": created_actor,
        "actor": _actor_key(actor),
        "uds_blueprint": UDS_BLUEPRINT,
        "world_partition": True,
        "saved": saved,
    }


def main():
    unreal.log("[GAEA_UDS] starting isolated UDS staging")
    uds_class = unreal.EditorAssetLibrary.load_blueprint_class(UDS_BLUEPRINT)
    if uds_class is None:
        raise RuntimeError("UDS Blueprint class not found: " + UDS_BLUEPRINT)

    level_subsystem = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
    actor_subsystem = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
    world = unreal.EditorLevelLibrary.get_editor_world()
    results = []
    for theme, map_path in MAPS:
        results.append(_stage_one(level_subsystem, actor_subsystem, world, theme, map_path, uds_class))

    os.makedirs(os.path.dirname(REPORT_PATH), exist_ok=True)
    with open(REPORT_PATH, "w", encoding="utf-8") as handle:
        json.dump(
            {
                "status": "PASS" if all(item["status"] == "PASS" for item in results) else "ERROR",
                "uds_blueprint": UDS_BLUEPRINT,
                "maps": results,
            },
            handle,
            indent=2,
        )
    unreal.log("[GAEA_UDS] report: " + REPORT_PATH)
    unreal.log("[GAEA_UDS] " + json.dumps(results))


main()
