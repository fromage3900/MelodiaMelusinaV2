"""Repair the terrain actor/mesh contract for the four WP greyboxes.

This does not regenerate terrain or touch PCG volumes. It only ensures the
existing ``Terrain_<Pillar>`` StaticMeshActor references its authored terrain
mesh and participates in query/physics collision, which is required for Recast
to build a useful greybox nav surface.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import unreal


LEVEL_ROOT = "/Game/EnvSandbox/Environments/WP/L_WP_{}"
MESH_ROOT = "/Game/EnvSandbox/Meshes/WPTerrains/SM_Terrain_{}"
PILLARS = ("SakuraDream", "SpaceCathedral", "BaroqueGrotto", "CosmicOrrery")
ROOT = Path(__file__).resolve().parents[2]
REPORT = ROOT / "Saved" / "Audit" / "wp_terrain_repair.json"


def _stream_all_actors() -> None:
    try:
        descs = unreal.WorldPartitionBlueprintLibrary.get_actor_descs()
        unreal.WorldPartitionBlueprintLibrary.load_actors([d.guid for d in descs])
    except Exception as exc:
        unreal.log_warning(f"[WPTerrainRepair] actor streaming request failed: {exc}")


def _find_or_spawn(eas, label: str):
    for actor in eas.get_all_level_actors() or []:
        if actor.get_actor_label() == label:
            return actor, False
    actor = eas.spawn_actor_from_class(unreal.StaticMeshActor, unreal.Vector(0, 0, 0))
    actor.set_actor_label(label)
    return actor, True


def repair(pillar: str) -> dict:
    les = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
    if not les.load_level(LEVEL_ROOT.format(pillar)):
        return {"pillar": pillar, "error": "level_load_failed"}
    _stream_all_actors()
    eas = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
    actor, spawned = _find_or_spawn(eas, f"Terrain_{pillar}")
    mesh_path = MESH_ROOT.format(pillar)
    mesh = unreal.EditorAssetLibrary.load_asset(mesh_path)
    if not mesh:
        return {"pillar": pillar, "error": "terrain_mesh_missing", "mesh": mesh_path}
    component = actor.static_mesh_component
    component.set_editor_property("static_mesh", mesh)
    component.set_collision_enabled(unreal.CollisionEnabled.QUERY_AND_PHYSICS)
    component.set_collision_profile_name("BlockAll")
    actor.tags = list(actor.tags or [])
    if "MeshTerrain_Seed" not in [str(tag) for tag in actor.tags]:
        actor.tags.append("MeshTerrain_Seed")
    if "Ground" not in [str(tag) for tag in actor.tags]:
        actor.tags.append("Ground")
    actor.modify()
    actor.set_actor_label(f"Terrain_{pillar}")
    unreal.EditorAssetLibrary.save_loaded_asset(actor, False)
    return {
        "pillar": pillar,
        "actor": actor.get_actor_label(),
        "spawned": spawned,
        "mesh": mesh_path,
        "collision_enabled": str(component.get_collision_enabled()),
        "collision_profile": str(component.get_collision_profile_name()),
    }


def main() -> int:
    results = [repair(pillar) for pillar in PILLARS]
    REPORT.parent.mkdir(parents=True, exist_ok=True)
    REPORT.write_text(json.dumps({"results": results}, indent=2), encoding="utf-8")
    unreal.log(f"[WPTerrainRepair] wrote {REPORT}")
    return 0 if all("error" not in result for result in results) else 1


if __name__ == "__main__":
    raise SystemExit(main())
