"""Stage the four high-resolution Gaea/DEM handoffs in isolated UE 5.8 maps.

This script is intentionally editor-only and namespace-scoped. It imports the
four metric OBJ handoffs produced by
Tools/WorldGen/build_highres_dem_mesh_terrain_handoffs.py, creates one isolated
material instance per setup, assigns the mesh to a MeshPartition actor, and
places Ultra Dynamic Sky. It never creates a classic Landscape and never loads
or edits production, gameplay, RenderTests, or webfront maps.

Run only after the gameplay lane releases the editor lease:

    UnrealEditor.exe BS_GodFile.uproject \
      -ExecutePythonScript="Content/Python/stage_highres_gaea_mesh_terrain_import.py"
"""

from __future__ import annotations

import json
import os
from pathlib import Path

import unreal


PROJECT_ROOT = Path(r"C:\EnvironmentPortfolio\BS_GodFile")
HANDOFF_ROOT = PROJECT_ROOT / "Saved/Audit/gaea_setups_highres_20260825_1025"
DEST_ROOT = "/Game/_PROJECT/ResonantWorld/Offline/GaeaSetups"
PARENT_MATERIAL = "/Game/EnvSandbox/Materials/Masters/M_Master_Toon_Landscape_HeightBlend"
UDS_BLUEPRINT = "/Game/UltraDynamicSky/Blueprints/Ultra_Dynamic_Sky"
REPORT_PATH = HANDOFF_ROOT / "ue_import_stage_report.json"

SETUPS = [
    {
        "id": "sakura_terrace",
        "folder": "SakuraTerrace",
        "label": "Sakura Terrace",
        "pcg_profile": "waltz_garden",
        "obj": HANDOFF_ROOT / "sakura_terrace/ue_handoff/sakura_terrace_MeshTerrain_1025.obj",
    },
    {
        "id": "liquid_cathedral",
        "folder": "LiquidCathedral",
        "label": "Liquid Cathedral",
        "pcg_profile": "cathedral",
        "obj": HANDOFF_ROOT / "liquid_cathedral/ue_handoff/liquid_cathedral_MeshTerrain_1025.obj",
    },
    {
        "id": "cadence_crystal_ridge",
        "folder": "CadenceCrystalRidge",
        "label": "Cadence Crystal Ridge",
        "pcg_profile": "crystalline",
        "obj": HANDOFF_ROOT / "cadence_crystal_ridge/ue_handoff/cadence_crystal_ridge_MeshTerrain_1025.obj",
    },
    {
        "id": "fugue_grotto",
        "folder": "FugueGrotto",
        "label": "Fugue Grotto",
        "pcg_profile": "fugue_maze",
        "obj": HANDOFF_ROOT / "fugue_grotto/ue_handoff/fugue_grotto_MeshTerrain_1025.obj",
    },
]


def _asset_path(folder: str, name: str) -> str:
    return f"{DEST_ROOT}/{folder}/{name}"


def _actor_label(actor) -> str:
    try:
        return actor.get_actor_label()
    except Exception:
        return actor.get_name()


def _find_actor(actor_subsystem, label: str):
    return next((actor for actor in actor_subsystem.get_all_level_actors() if _actor_label(actor) == label), None)


def _import_mesh(setup: dict) -> tuple[object, str]:
    folder = setup["folder"]
    mesh_name = f"SM_Gaea_{folder}_1025"
    mesh_path = _asset_path(folder, mesh_name)
    existing = unreal.load_asset(mesh_path)
    if existing:
        return existing, "existing"
    source = setup["obj"]
    if not source.is_file():
        raise FileNotFoundError(source)
    task = unreal.AssetImportTask()
    task.filename = str(source)
    task.destination_path = f"{DEST_ROOT}/{folder}"
    task.destination_name = mesh_name
    task.automated = True
    task.replace_existing = True
    task.save = True
    unreal.AssetToolsHelpers.get_asset_tools().import_asset_tasks([task])
    mesh = unreal.load_asset(mesh_path)
    if not mesh:
        raise RuntimeError(f"OBJ import did not produce {mesh_path}")
    return mesh, "imported"


def _ensure_material(setup: dict):
    folder = setup["folder"]
    name = f"MI_Gaea_{folder}_Substrate"
    path = _asset_path(folder, name)
    instance = unreal.load_asset(path)
    if instance:
        return instance, "existing"
    parent = unreal.load_asset(PARENT_MATERIAL)
    if not parent:
        raise RuntimeError(f"landscape/Substrate parent missing: {PARENT_MATERIAL}")
    factory = unreal.MaterialInstanceConstantFactoryNew()
    instance = unreal.AssetToolsHelpers.get_asset_tools().create_asset(name, f"{DEST_ROOT}/{folder}", unreal.MaterialInstanceConstant, factory)
    if not instance:
        raise RuntimeError(f"could not create material instance: {path}")
    instance.set_editor_property("parent", parent)
    unreal.EditorAssetLibrary.save_loaded_asset(instance, True)
    return instance, "created"


def _ensure_map_and_actors(setup: dict, mesh, material, uds_class) -> dict:
    folder = setup["folder"]
    map_path = _asset_path(folder, f"L_Gaea_{folder}_WP")
    level_subsystem = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
    if unreal.EditorAssetLibrary.does_asset_exist(map_path):
        if not level_subsystem.load_level(map_path):
            raise RuntimeError(f"could not load isolated map: {map_path}")
        map_state = "existing"
    else:
        if not level_subsystem.new_level(map_path, is_partitioned_world=True):
            raise RuntimeError(f"could not create isolated map: {map_path}")
        map_state = "created"

    actor_subsystem = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
    mesh_label = f"MeshTerrain_{folder}_1025"
    mesh_actor = _find_actor(actor_subsystem, mesh_label)
    mesh_actor_state = "existing"
    mesh_partition_class = getattr(unreal, "MeshPartition", None)
    if not mesh_partition_class:
        raise RuntimeError("UE 5.8 MeshPartition class is not reflected")
    if mesh_actor is None:
        mesh_actor = actor_subsystem.spawn_actor_from_class(mesh_partition_class, unreal.Vector(), unreal.Rotator())
        if not mesh_actor:
            raise RuntimeError(f"MeshPartition spawn failed for {folder}")
        mesh_actor.set_actor_label(mesh_label)
        mesh_actor_state = "created"
    mesh_actor.tags = list({str(tag) for tag in (mesh_actor.tags or [])} | {"MelodiaGaeaSetup", setup["id"], "MeshTerrain1025"})
    try:
        mesh_actor.set_is_spatially_loaded(False)
    except Exception:
        pass
    component_class = getattr(unreal, "MeshPartitionStaticMeshComponent", None)
    components = mesh_actor.get_components_by_class(component_class or unreal.StaticMeshComponent)
    component_report = []
    for component in components:
        component.set_editor_property("static_mesh", mesh)
        component.set_material(0, material)
        component_report.append({"component": component.get_name(), "mesh": mesh.get_path_name(), "material": material.get_path_name()})

    uds_label = f"UDS_{folder}"
    uds_actor = _find_actor(actor_subsystem, uds_label)
    uds_state = "existing"
    if uds_actor is None:
        uds_actor = actor_subsystem.spawn_actor_from_class(uds_class, unreal.Vector(), unreal.Rotator())
        if not uds_actor:
            raise RuntimeError(f"UDS spawn failed for {folder}")
        uds_actor.set_actor_label(uds_label)
        uds_state = "created"
    uds_actor.tags = ["MelodiaWorldGen", "UDS", "GaeaSetup", setup["id"]]
    uds_actor.set_folder_path("WorldGen/UDS")
    try:
        uds_actor.set_is_spatially_loaded(False)
    except Exception:
        pass
    bridge = getattr(unreal.PCGScaleWorldEditorLibrary, "create_mesh_partition_terrain", None)
    if bridge is None:
        raise RuntimeError("PCGScaleWorldEditorLibrary.create_mesh_partition_terrain is not reflected")
    bridge_result = str(
        bridge(
            map_path,
            mesh.get_path_name(),
            material.get_path_name(),
            mesh_label,
        )
    )
    if not bridge_result.startswith("OK:"):
        raise RuntimeError(f"MeshPartition bridge failed for {folder}: {bridge_result}")
    # The editor-only bridge performs the map save after the MeshPartition
    # preview/base modifier is built. A second save here can re-enter
    # MeshPartition serialization and crash UE 5.8 (StaticConstructObject while
    # serializing object data), so treat the bridge's OK result as the save gate.
    saved = True
    return {
        "map": map_path,
        "map_state": map_state,
        "world_partition": True,
        "mesh_actor": mesh_label,
        "mesh_actor_state": mesh_actor_state,
        "mesh_actor_class": mesh_actor.get_class().get_name(),
        "mesh_components": component_report,
        "uds_actor": uds_label,
        "uds_state": uds_state,
        "uds_blueprint": UDS_BLUEPRINT,
        "mesh_partition_bridge": bridge_result,
        "saved": saved,
        "classic_landscape_created": False,
    }


def main() -> None:
    unreal.log("[GAEA_HIGHRES] starting isolated four-map staging")
    uds_class = unreal.EditorAssetLibrary.load_blueprint_class(UDS_BLUEPRINT)
    if not uds_class:
        raise RuntimeError(f"UDS Blueprint class not found: {UDS_BLUEPRINT}")
    results = []
    for setup in SETUPS:
        mesh, mesh_state = _import_mesh(setup)
        material, material_state = _ensure_material(setup)
        map_report = _ensure_map_and_actors(setup, mesh, material, uds_class)
        results.append(
            {
                "setup_id": setup["id"],
                "source_obj": str(setup["obj"]),
                "mesh": {"path": mesh.get_path_name(), "state": mesh_state},
                "material": {"path": material.get_path_name(), "state": material_state, "parent": PARENT_MATERIAL},
                "pcg_profile": setup["pcg_profile"],
                **map_report,
            }
        )
    REPORT_PATH.parent.mkdir(parents=True, exist_ok=True)
    REPORT_PATH.write_text(json.dumps({"schema": "melodia.gaea_highres_ue_stage.v1", "mesh_terrain_only": True, "setups": results}, indent=2) + "\n", encoding="utf-8")
    unreal.log("[GAEA_HIGHRES] report: " + str(REPORT_PATH))


if __name__ == "__main__":
    main()
