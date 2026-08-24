"""Stage the first Gaea/Mesh Terrain proof for Petal Cantata.

This is deliberately additive and isolated:

* source mesh: real ASTER-derived OBJ from the offline world-gen handoff
* UE target: MeshPartition actor only; no classic Landscape actor is created
* material: isolated material instance inheriting the live toon/Substrate
  landscape master
* map: /Game/_PROJECT/ResonantWorld/Offline/GaeaSetups/SakuraTerrace/

Run from UE 5.8 with the editor closed (or from the live editor Python console):

    UnrealEditor-Cmd.exe BS_GodFile.uproject \
      -ExecutePythonScript="Content/Python/stage_gaea_sakura_terrace_p0.py" \
      -unattended -nullrhi
"""
from __future__ import annotations

import json
from pathlib import Path

import unreal


SOURCE_OBJ = Path(
    r"C:\EnvironmentPortfolio\BS_GodFile\Content\MelodiaIntegration\ResonantWorld\OfflineWorldGen"
    r"\PetalCantata_3900\TerrainSources\Yoshino_ASTER_12km_129\PetalCantata_Yoshino_ASTER_12km_129.obj"
)
DEST_DIR = "/Game/_PROJECT/ResonantWorld/Offline/GaeaSetups/SakuraTerrace"
MESH_PATH = f"{DEST_DIR}/SM_Gaea_SakuraTerrace_Source"
MATERIAL_PATH = f"{DEST_DIR}/MI_Gaea_SakuraTerrace_Substrate"
MAP_PATH = f"{DEST_DIR}/L_Gaea_SakuraTerrace"
PARENT_MATERIAL = "/Game/EnvSandbox/Materials/Masters/M_Master_Toon_Landscape_HeightBlend"
REPORT_PATH = Path(unreal.Paths.project_saved_dir()) / "Audit" / "gaea_setups" / "sakura_terrace" / "ue_stage_report.json"


def _load(path: str):
    asset = unreal.load_asset(path)
    if not asset:
        raise RuntimeError(f"UE asset could not be loaded: {path}")
    return asset


def _ensure_mesh():
    mesh = unreal.load_asset(MESH_PATH)
    if mesh:
        return mesh, "existing"
    if not SOURCE_OBJ.is_file():
        raise RuntimeError(f"source OBJ missing: {SOURCE_OBJ}")

    task = unreal.AssetImportTask()
    task.filename = str(SOURCE_OBJ)
    task.destination_path = DEST_DIR
    task.destination_name = "SM_Gaea_SakuraTerrace_Source"
    task.automated = True
    task.replace_existing = True
    task.save = True
    unreal.AssetToolsHelpers.get_asset_tools().import_asset_tasks([task])
    mesh = unreal.load_asset(MESH_PATH)
    if not mesh:
        raise RuntimeError(f"OBJ import did not produce {MESH_PATH}")
    return mesh, "imported"


def _ensure_material():
    parent = _load(PARENT_MATERIAL)
    instance = unreal.load_asset(MATERIAL_PATH)
    created = False
    if not instance:
        instance = unreal.EditorAssetLibrary.create_asset(
            "MI_Gaea_SakuraTerrace_Substrate",
            DEST_DIR,
            unreal.MaterialInstanceConstant,
            unreal.MaterialInstanceConstantFactoryNew(),
        )
        if not instance:
            raise RuntimeError(f"could not create material instance: {MATERIAL_PATH}")
        created = True
    instance.set_editor_property("parent", parent)

    scalar_values = {
        "TriplanarTiling": 280.0,
        "TriplanarBlend": 0.42,
        "SlopeSharpness": 3.2,
        "HeightBlendStrength": 2.2,
        "GrassAmount": 0.72,
        "MudAmount": 0.28,
        "MacroStrength": 0.45,
        "PastelLift": 0.18,
        "DreamSaturation": 0.22,
        "SparkleIntensity": 0.20,
        "ShadowFlowerStrength": 0.50,
        "ShadowFlowerScale": 7.0,
    }
    vector_values = {
        "RockTint": (0.50, 0.46, 0.40, 1.0),
        "GrassTint": (0.40, 0.52, 0.28, 1.0),
        "MudTint": (0.24, 0.30, 0.16, 1.0),
        "ShadowFlowerColor": (0.92, 0.58, 0.75, 1.0),
    }
    applied_scalars = []
    skipped_scalars = []
    for name, value in scalar_values.items():
        try:
            unreal.MaterialEditingLibrary.set_material_instance_scalar_parameter_value(instance, name, value)
            applied_scalars.append(name)
        except Exception:
            skipped_scalars.append(name)
    applied_vectors = []
    skipped_vectors = []
    for name, value in vector_values.items():
        try:
            color = unreal.LinearColor(*value)
            unreal.MaterialEditingLibrary.set_material_instance_vector_parameter_value(instance, name, color)
            applied_vectors.append(name)
        except Exception:
            skipped_vectors.append(name)
    unreal.EditorAssetLibrary.save_loaded_asset(instance, True)
    return instance, {
        "path": MATERIAL_PATH,
        "parent": PARENT_MATERIAL,
        "created": created,
        "applied_scalars": applied_scalars,
        "skipped_scalars": skipped_scalars,
        "applied_vectors": applied_vectors,
        "skipped_vectors": skipped_vectors,
    }


def _ensure_map(mesh, material):
    level_editor = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
    if unreal.EditorAssetLibrary.does_asset_exist(MAP_PATH):
        if not level_editor.load_level(MAP_PATH):
            raise RuntimeError(f"could not load isolated map: {MAP_PATH}")
        map_state = "existing"
    else:
        if not level_editor.new_level(MAP_PATH, is_partitioned_world=True):
            raise RuntimeError(f"could not create isolated map: {MAP_PATH}")
        map_state = "created"

    actor_subsystem = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
    actors = actor_subsystem.get_all_level_actors() or []
    actor = next((a for a in actors if a.get_actor_label() == "MeshTerrain_SakuraTerrace"), None)
    actor_state = "existing"
    if not actor:
        mesh_partition_class = getattr(unreal, "MeshPartition", None)
        if not mesh_partition_class:
            raise RuntimeError("UE 5.8 MeshPartition class is not reflected")
        actor = actor_subsystem.spawn_actor_from_class(
            mesh_partition_class,
            unreal.Vector(0.0, 0.0, 0.0),
            unreal.Rotator(0.0, 0.0, 0.0),
        )
        if not actor:
            raise RuntimeError("MeshPartition actor spawn failed")
        actor_state = "created"
        actor.set_actor_label("MeshTerrain_SakuraTerrace")
    actor.tags = list({str(tag) for tag in (actor.tags or [])} | {
        "MelodiaGaeaSetup",
        "SakuraTerrace",
        "MeshTerrainSource",
    })
    try:
        actor.set_editor_property("is_spatially_loaded", False)
    except Exception:
        pass

    components = actor.get_components_by_class(unreal.MeshPartitionStaticMeshComponent)
    if not components:
        components = actor.get_components_by_class(unreal.StaticMeshComponent)
    component_report = []
    for component in components:
        try:
            component.set_editor_property("static_mesh", mesh)
        except Exception as exc:
            component_report.append({"component": component.get_name(), "mesh_error": str(exc)})
            continue
        try:
            component.set_material(0, material)
            material_state = "assigned"
        except Exception as exc:
            material_state = f"assignment_error: {exc}"
        component_report.append({
            "component": component.get_name(),
            "class": component.get_class().get_name(),
            "mesh": MESH_PATH,
            "material": MATERIAL_PATH,
            "material_state": material_state,
        })
    level_editor.save_current_level()
    return {
        "path": MAP_PATH,
        "state": map_state,
        "actor": actor.get_actor_label(),
        "actor_state": actor_state,
        "actor_class": actor.get_class().get_name(),
        "components": component_report,
        "world_partition": True,
        "classic_landscape_created": False,
    }


def main() -> dict:
    mesh, mesh_state = _ensure_mesh()
    material, material_report = _ensure_material()
    map_report = _ensure_map(mesh, material)
    report = {
        "schema": "melodia.gaea_ue_stage.v1",
        "setup_id": "sakura_terrace",
        "mesh_terrain_only": True,
        "source_obj": str(SOURCE_OBJ),
        "mesh": {"path": MESH_PATH, "state": mesh_state, "class": mesh.get_class().get_name()},
        "material": material_report,
        "map": map_report,
        "production_maps_touched": False,
        "lookdev_maps_touched": False,
        "next_gate": "build_mesh_terrain_partition_and_run_clean_pie",
    }
    REPORT_PATH.parent.mkdir(parents=True, exist_ok=True)
    REPORT_PATH.write_text(json.dumps(report, indent=2), encoding="utf-8")
    unreal.log(f"[Gaea Sakura Terrace] {json.dumps(report)}")
    return report


if __name__ == "__main__":
    try:
        main()
        print("GAEA_SAKURA_STAGE_OK")
    except Exception as exc:
        unreal.log_error(f"[Gaea Sakura Terrace] {exc}")
        raise
