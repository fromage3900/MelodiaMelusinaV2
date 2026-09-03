"""Author a human-scale greybox spine in each WP pillar level.

This is the structural companion to the PCG scatter graphs. It provides a
deterministic floor, corridor walls, and destination hall so PCG dressing has
an actual level-design scaffold to inhabit.

Scale contract (UE units are centimetres):
  primary corridor: 300 cm wide x 240 cm clear height
  floor: 20 cm thick
  destination hall: 1200 cm wide x 900 cm deep x 360 cm clear height
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import unreal


ROOT = Path(__file__).resolve().parents[2]
REPORT = ROOT / "Saved" / "Audit" / "wp_human_scale_blockout.json"
LEVELS = {
    "SakuraDream": 1200.0,
    "SpaceCathedral": 1600.0,
    "BaroqueGrotto": 1600.0,
    "CosmicOrrery": 1600.0,
}
LEVEL_ROOT = "/Game/EnvSandbox/Environments/WP/L_WP_{}"
CUBE = "/Game/EnvSandbox/Greybox_Kit/SM_Greybox_Cube_1m.SM_Greybox_Cube_1m"


def _spawn(eas, mesh, label, location, scale, tags):
    actor = eas.spawn_actor_from_class(unreal.StaticMeshActor, unreal.Vector(*location))
    # Keep the authored greybox in the persistent WP layer so reopening the
    # map does not unload the route and leave nav bounds over empty space.
    try:
        actor.set_editor_property("is_spatially_loaded", False)
    except Exception:
        pass
    actor.set_actor_label(label)
    actor.set_actor_scale3d(unreal.Vector(*scale))
    actor.static_mesh_component.set_editor_property("static_mesh", mesh)
    actor.static_mesh_component.set_collision_enabled(unreal.CollisionEnabled.QUERY_AND_PHYSICS)
    actor.static_mesh_component.set_collision_profile_name("BlockAll")
    actor.tags = [unreal.Name(tag) for tag in tags]
    actor.modify()
    return actor


def build_level(key: str, length: float) -> dict:
    les = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
    if not les.load_level(LEVEL_ROOT.format(key)):
        return {"level": key, "error": "load_failed"}
    try:
        ds = unreal.WorldPartitionBlueprintLibrary.get_actor_descs()
        unreal.WorldPartitionBlueprintLibrary.load_actors([d.guid for d in ds])
    except Exception:
        pass
    eas = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
    prefix = f"GB_{key}_"
    for actor in eas.get_all_level_actors() or []:
        if actor.get_actor_label().startswith(prefix):
            eas.destroy_actor(actor)
    mesh = unreal.EditorAssetLibrary.load_asset(CUBE)
    if not mesh:
        return {"level": key, "error": "cube_mesh_missing"}
    actors = []
    tags = ["WP_PrimaryRoute", "WP_NoScatter", "GB_HumanScale"]
    wall_tags = tags + ["PCG_Exclude"]
    half = length / 2.0
    actors.append(_spawn(eas, mesh, f"{prefix}Floor", (0, half, 0), (6.0, length / 200.0, 0.1), tags))
    actors.append(_spawn(eas, mesh, f"{prefix}Wall_L", (-165, half, 120), (0.15, length / 200.0, 1.2), wall_tags))
    actors.append(_spawn(eas, mesh, f"{prefix}Wall_R", (165, half, 120), (0.15, length / 200.0, 1.2), wall_tags))
    hall_y = length + 450.0
    actors.append(_spawn(eas, mesh, f"{prefix}HallFloor", (0, hall_y, 0), (6.0, 4.5, 0.1), ["WP_LandmarkClear", "WP_EncounterClear", "GB_HumanScale"]))
    for side in (-1, 1):
        for offset in (-350, 350):
            actors.append(_spawn(eas, mesh, f"{prefix}HallColumn_{side}_{offset}", (side * 450, hall_y + offset, 180), (0.6, 0.6, 1.8), ["WP_LandmarkClear", "GB_HumanScale", "PCG_Exclude"]))
    world = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_editor_world()
    unreal.EditorLoadingAndSavingUtils.save_map(world, LEVEL_ROOT.format(key))
    return {
        "level": key,
        "route_length_cm": length,
        "corridor_width_cm": 300,
        "corridor_clear_height_cm": 240,
        "hall_width_cm": 1200,
        "hall_depth_cm": 900,
        "hall_clear_height_cm": 360,
        "actor_count": len(actors),
        "tags": tags,
    }


def main() -> int:
    results = [build_level(key, length) for key, length in LEVELS.items()]
    REPORT.parent.mkdir(parents=True, exist_ok=True)
    REPORT.write_text(json.dumps({"results": results}, indent=2), encoding="utf-8")
    unreal.log(f"[WPHumanScale] wrote {REPORT}")
    return 0 if all("error" not in item for item in results) else 1


if __name__ == "__main__":
    raise SystemExit(main())
