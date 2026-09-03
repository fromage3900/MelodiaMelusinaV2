"""Import the delivered armature-bearing Sir Melodious source as the canonical mesh."""
from __future__ import annotations

import json
from pathlib import Path

import unreal


SOURCE = str(Path(unreal.Paths.project_dir()) / "Content" / "EnvSandbox" / "SKM_SirMelodious_rig.fbx")
DEST = "/Game/Melodia/Characters/SirMelodious/Rigged"
MESH_NAME = "SK_SirMelodious_Rigged"
REPORT = Path(unreal.Paths.project_dir()) / "Saved" / "Melodia" / "sir_melodious_rigged_import.json"
BODY_MI = "/Game/Melodia/Characters/SirMelodious/Materials/MI_SirMelodious_Sirmelo"


def _asset(path: str):
    return unreal.load_asset(path)


def main():
    if not Path(SOURCE).is_file():
        raise RuntimeError(f"Rigged source is missing: {SOURCE}")
    unreal.EditorAssetLibrary.make_directory(DEST)
    mesh_path = f"{DEST}/{MESH_NAME}"
    mesh = _asset(mesh_path)
    imported_paths = []
    if not mesh:
        task = unreal.AssetImportTask()
        task.filename = SOURCE
        task.destination_path = DEST
        task.destination_name = MESH_NAME
        task.automated = True
        task.save = True
        task.replace_existing = False
        options = unreal.FbxImportUI()
        options.import_mesh = True
        options.import_as_skeletal = True
        options.import_animations = True
        options.import_materials = False
        options.import_textures = False
        options.skeletal_mesh_import_data.set_editor_property("import_morph_targets", True)
        task.options = options
        unreal.AssetToolsHelpers.get_asset_tools().import_asset_tasks([task])
        imported_paths = list(task.imported_object_paths)
        mesh = _asset(mesh_path)
    if not mesh or mesh.get_class().get_name() != "SkeletalMesh":
        raise RuntimeError(f"Canonical rigged SkeletalMesh was not created at {mesh_path}")

    body_mi = _asset(BODY_MI)
    if not body_mi:
        raise RuntimeError(f"Existing Sir Melodious body material is missing: {BODY_MI}")
    materials = mesh.get_editor_property("materials")
    assigned = []
    for material in materials:
        assigned.append(unreal.SkeletalMaterial(
            material_interface=body_mi,
            material_slot_name=material.get_editor_property("material_slot_name"),
            uv_channel_data=material.get_editor_property("uv_channel_data"),
        ))
    mesh.set_editor_property("materials", assigned)
    unreal.EditorAssetLibrary.save_loaded_asset(mesh)

    skeleton = mesh.get_editor_property("skeleton")
    result = {
        "source": SOURCE,
        "mesh": mesh.get_path_name(),
        "skeleton": skeleton.get_path_name() if skeleton else None,
        "material_slots": len(assigned),
        "imported_paths": imported_paths,
    }
    REPORT.parent.mkdir(parents=True, exist_ok=True)
    REPORT.write_text(json.dumps(result, indent=2), encoding="utf-8")
    unreal.log(f"[SirMelodious] Imported canonical rigged mesh -> {REPORT}")


if __name__ == "__main__":
    main()
