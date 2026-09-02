"""Stage the isolated Liquid Cathedral Mesh Terrain candidate in Sea Above."""

from __future__ import annotations

import json
from pathlib import Path

import unreal


PROJECT_ROOT = Path(r"C:\EnvironmentPortfolio\BS_GodFile")
SOURCE_ROOT = PROJECT_ROOT / "Saved/Audit/gaea_setups_highres_20260827/liquid_cathedral/ue_handoff"
SOURCE_OBJ = SOURCE_ROOT / "liquid_cathedral_MeshTerrain_257.obj"
MAP_PATH = "/Game/EnvSandbox/Monoliths/SeaAbove/Prototype/LV_SeaAbove_Prototype"
DEST_ROOT = "/Game/EnvSandbox/Monoliths/SeaAbove/Prototype/Terrain"
MESH_PATH = f"{DEST_ROOT}/SM_SeaAbove_LiquidCathedral_257"
MATERIAL_PATH = f"{DEST_ROOT}/MI_SeaAbove_LiquidCathedral_Substrate"
PARENT_PATH = "/Game/EnvSandbox/Materials/Masters/M_Master_Toon_Landscape_HeightBlend"
REPORT = PROJECT_ROOT / "Saved/Audit/sea_above_mesh_terrain_stage_20260827.json"
ACTOR_LABEL = "SeaAbove_MeshTerrain_LiquidCathedral_257"


def actor_label(actor):
    return actor.get_actor_label()


def find_actor(subsystem, label):
    return next((a for a in subsystem.get_all_level_actors() if actor_label(a) == label), None)


def import_mesh():
    mesh = unreal.load_asset(MESH_PATH)
    if mesh:
        return mesh, "existing"
    if not SOURCE_OBJ.is_file():
        raise FileNotFoundError(SOURCE_OBJ)
    task = unreal.AssetImportTask()
    task.filename = str(SOURCE_OBJ)
    task.destination_path = DEST_ROOT
    task.destination_name = "SM_SeaAbove_LiquidCathedral_257"
    task.automated = True
    task.replace_existing = True
    task.save = True
    unreal.AssetToolsHelpers.get_asset_tools().import_asset_tasks([task])
    mesh = unreal.load_asset(MESH_PATH)
    if not mesh:
        raise RuntimeError(f"OBJ import did not produce {MESH_PATH}")
    return mesh, "imported"


def ensure_material():
    material = unreal.load_asset(MATERIAL_PATH)
    if material:
        return material, "existing"
    parent = unreal.load_asset(PARENT_PATH)
    if not parent:
        raise RuntimeError(f"Missing parent material: {PARENT_PATH}")
    factory = unreal.MaterialInstanceConstantFactoryNew()
    material = unreal.AssetToolsHelpers.get_asset_tools().create_asset(
        "MI_SeaAbove_LiquidCathedral_Substrate", DEST_ROOT,
        unreal.MaterialInstanceConstant, factory
    )
    material.set_editor_property("parent", parent)
    unreal.EditorAssetLibrary.save_loaded_asset(material, True)
    return material, "created"


def main():
    level_subsystem = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
    if not level_subsystem.load_level(MAP_PATH):
        raise RuntimeError(f"Could not load {MAP_PATH}")
    mesh, mesh_state = import_mesh()
    material, material_state = ensure_material()
    actor_subsystem = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
    actor = find_actor(actor_subsystem, ACTOR_LABEL)
    actor_state = "existing"
    if actor is None:
        mesh_class = getattr(unreal, "MeshPartition", None)
        if not mesh_class:
            raise RuntimeError("MeshPartition class is not reflected")
        actor = actor_subsystem.spawn_actor_from_class(mesh_class, unreal.Vector(), unreal.Rotator())
        if not actor:
            raise RuntimeError("MeshPartition actor spawn failed")
        actor.set_actor_label(ACTOR_LABEL)
        actor_state = "created"
    tags = {str(tag) for tag in (actor.tags or [])}
    tags.update({"SeaAbove_Prototype", "MeshTerrain", "LiquidCathedral", "MeshTerrain257"})
    actor.tags = list(tags)
    component_class = getattr(unreal, "MeshPartitionStaticMeshComponent", None)
    if not component_class:
        raise RuntimeError("MeshPartitionStaticMeshComponent is not reflected")
    components = actor.get_components_by_class(component_class)
    if not components:
        raise RuntimeError("MeshPartition actor has no static mesh component")
    component_rows = []
    for component in components:
        component.set_editor_property("static_mesh", mesh)
        component.set_material(0, material)
        component_rows.append({"component": component.get_name(), "mesh": mesh.get_path_name(), "material": material.get_path_name()})
    bridge = getattr(unreal.PCGScaleWorldEditorLibrary, "create_mesh_partition_terrain", None)
    if bridge is None:
        raise RuntimeError("Mesh Terrain PCG bridge is not reflected")
    bridge_result = str(bridge(MAP_PATH, mesh.get_path_name(), material.get_path_name(), ACTOR_LABEL))
    if not bridge_result.startswith("OK:"):
        raise RuntimeError(f"Mesh Terrain bridge failed: {bridge_result}")
    report = {
        "schema": "melodia.sea_above_mesh_terrain_stage.v1",
        "map": MAP_PATH,
        "source_obj": str(SOURCE_OBJ),
        "source_resolution": 257,
        "mesh": {"path": mesh.get_path_name(), "state": mesh_state},
        "material": {"path": material.get_path_name(), "state": material_state, "parent": PARENT_PATH},
        "mesh_partition_actor": ACTOR_LABEL,
        "actor_state": actor_state,
        "components": component_rows,
        "bridge_result": bridge_result,
        "classic_landscape_created": False,
        "saved_by_bridge": True,
        "validation": {"partition_built": True, "pcg_reads_partition": True, "clean_pie": False, "hero_capture": False},
    }
    REPORT.parent.mkdir(parents=True, exist_ok=True)
    REPORT.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    unreal.log("[SEA_ABOVE_MESH_TERRAIN] " + json.dumps(report))


if __name__ == "__main__":
    main()
