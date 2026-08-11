"""Import UpdatedShirt FBX + textures and integrate into Melusina production assets.

Steps:
1. Import UpdatedShirt.fbx as a Static Mesh
2. Import MelusinaUpdatedShirt_*.png textures with correct compression
3. Create MI_Melusina_UpdatedShirt material instance
4. Update slot 17 (Material_024) on SK_Melusina with new textures

Run in UE Python console:
    exec(open(r'G:/EnvironmentPortfolio/BS_GodFile/Content/Python/import_melusina_updated_shirt.py').read())
"""

from __future__ import annotations

import os
import unreal


STAGING_DIR = r"G:\EnvironmentPortfolio\BS_GodFile\Imports\MelusinaTextures"
FBX_SRC = os.path.join(STAGING_DIR, "UpdatedShirt.fbx")
DEST_TEXTURE_PATH = "/Game/Melodia/Characters/Melusina/Textures"
DEST_STATIC_MESH_PATH = "/Game/Melodia/Characters/Melusina/Meshes"
DEST_MI_PATH = "/Game/Melodia/Characters/Melusina/Materials"
MASTER_PATH = "/Game/EnvSandbox/Materials/Masters/M_Master_Toon_Universal"
MESH_PATH = "/Game/Melodia/Characters/Melusina/SK_Melusina"

MAP_TYPES = ["BaseColor", "Normal", "Roughness", "Metallic", "Alpha", "Emission", "Displacement"]

PARAM_TO_MAP = {
    "Albedo": "BaseColor",
    "NormalMap": "Normal",
    "RoughnessMap": "Roughness",
    "MetallicMap": "Metallic",
    "HeightMap": "Displacement",
}


def import_fbx_as_static_mesh() -> str:
    """Import UpdatedShirt.fbx as a StaticMesh."""
    print("--- Step 1: Import FBX as Static Mesh ---")

    if not os.path.isfile(FBX_SRC):
        print(f"  FBX not found: {FBX_SRC}")
        return ""

    unreal.EditorAssetLibrary.make_directory(DEST_STATIC_MESH_PATH)

    task = unreal.AssetImportTask()
    task.set_editor_property("filename", FBX_SRC)
    task.set_editor_property("destination_path", DEST_STATIC_MESH_PATH)
    task.set_editor_property("destination_name", "SM_Melusina_Shirt_Updated")
    task.set_editor_property("replace_existing", True)
    task.set_editor_property("automated", True)
    task.set_editor_property("save", True)

    options = unreal.FbxImportUI()
    options.set_editor_property("import_mesh", True)
    options.set_editor_property("mesh_type_to_import", unreal.FBXImportType.FBXIT_STATIC_MESH)
    options.set_editor_property("import_as_skeletal", False)
    options.set_editor_property("import_materials", False)
    options.set_editor_property("import_textures", False)

    task.set_editor_property("options", options)

    asset_tools = unreal.AssetToolsHelpers.get_asset_tools()
    asset_tools.import_asset_tasks([task])

    imported = task.get_editor_property("imported_object_paths")
    if imported:
        print(f"  Imported: {imported[0]}")
        return str(imported[0])
    else:
        print("  FBX import produced no output paths (may have been skipped or empty)")
        return ""


def import_shirt_textures() -> dict[str, object]:
    """Import 7 shirt texture maps with correct compression/sRGB settings."""
    print("--- Step 2: Import Shirt Textures ---")

    unreal.EditorAssetLibrary.make_directory(DEST_TEXTURE_PATH)
    imported = {}

    prefix = "MelusinaUpdatedShirt"
    for map_type in MAP_TYPES:
        staged = os.path.join(STAGING_DIR, f"{prefix}_{map_type}.png")
        if not os.path.isfile(staged):
            print(f"  MISSING: {staged}")
            continue

        dest_name = f"T_Melusina_UpdatedShirt_{map_type}"

        task = unreal.AssetImportTask()
        task.set_editor_property("filename", staged)
        task.set_editor_property("destination_path", DEST_TEXTURE_PATH)
        task.set_editor_property("destination_name", dest_name)
        task.set_editor_property("replace_existing", True)
        task.set_editor_property("automated", True)
        task.set_editor_property("save", False)

        asset_tools = unreal.AssetToolsHelpers.get_asset_tools()
        asset_tools.import_asset_tasks([task])

        imported_paths = task.get_editor_property("imported_object_paths")
        if not imported_paths:
            print(f"  FAIL: {dest_name}")
            continue

        tex = unreal.load_asset(imported_paths[0])
        if not tex:
            print(f"  LOAD FAIL: {dest_name}")
            continue

        # Correct compression per map type
        if map_type == "Normal":
            tex.set_editor_property("compression_settings", unreal.TextureCompressionSettings.TC_NORMALMAP)
            tex.set_editor_property("srgb", False)
        elif map_type in ("Roughness", "Metallic", "Displacement", "Alpha"):
            tex.set_editor_property("compression_settings", unreal.TextureCompressionSettings.TC_MASKS)
            tex.set_editor_property("srgb", False)
        # BaseColor / Emission keep defaults (sRGB=True, TC_Default)

        unreal.EditorAssetLibrary.save_loaded_asset(tex)
        imported[map_type] = tex
        print(f"  OK: {dest_name}")

    return imported


def build_shirt_material_instance(textures: dict[str, object]) -> object | None:
    """Create MI_Melusina_UpdatedShirt with new textures."""
    print("--- Step 3: Build Material Instance ---")

    mi_name = "MI_Melusina_UpdatedShirt"
    unreal.EditorAssetLibrary.make_directory(DEST_MI_PATH)

    asset_tools = unreal.AssetToolsHelpers.get_asset_tools()
    master = unreal.load_asset(MASTER_PATH)
    mi_lib = unreal.MaterialEditingLibrary

    existing_data = unreal.EditorAssetLibrary.find_asset_data(f"{DEST_MI_PATH}/{mi_name}")
    if existing_data.is_valid():
        mi = unreal.load_asset(f"{DEST_MI_PATH}/{mi_name}")
        print(f"  Loaded existing {mi_name}")
    else:
        factory = unreal.MaterialInstanceConstantFactoryNew()
        mi = asset_tools.create_asset(mi_name, DEST_MI_PATH, unreal.MaterialInstanceConstant, factory)
        if mi:
            mi_lib.set_material_instance_parent(mi, master)
            print(f"  Created {mi_name}")

    if not mi:
        print("  FAILED to create MI")
        return None

    if mi.get_editor_property("parent") != master:
        mi_lib.set_material_instance_parent(mi, master)

    for param_name, map_type in PARAM_TO_MAP.items():
        tex = textures.get(map_type)
        if tex:
            mi_lib.set_material_instance_texture_parameter_value(mi, param_name, tex)

    mi_lib.set_material_instance_static_switch_parameter_value(mi, "bUseSeparateRoughnessMap", True)
    mi_lib.set_material_instance_static_switch_parameter_value(mi, "bUseSeparateMetallicMap", True)

    unreal.EditorAssetLibrary.save_loaded_asset(mi)
    print(f"  Saved {mi_name}")
    return mi


def update_mesh_slot_17(shirt_mi: object | None):
    """Replace material on SK_Melusina slot 17 (Material_024) with the updated shirt MI."""
    print("--- Step 4: Update SK_Melusina Slot 17 ---")

    mesh = unreal.load_asset(MESH_PATH)
    if not mesh:
        print("  Failed to load SK_Melusina")
        return

    materials = mesh.get_editor_property("materials")
    slot_target = 17

    if slot_target >= len(materials):
        print(f"  Slot {slot_target} out of range ({len(materials)} slots)")
        return

    slot_name = materials[slot_target].get_editor_property("material_slot_name")
    print(f"  Slot {slot_target}: {slot_name}")

    new_materials = []
    for i, m in enumerate(materials):
        if i == slot_target and shirt_mi:
            new_materials.append(unreal.SkeletalMaterial(
                material_interface=shirt_mi,
                material_slot_name=m.get_editor_property("material_slot_name"),
                uv_channel_data=m.get_editor_property("uv_channel_data"),
            ))
        else:
            # If we also want to swap existing MI_Melusina_Material_024 to use new textures,
            # load it and update its texture params:
            if i == slot_target and not shirt_mi:
                existing_mi = m.get_editor_property("material_interface")
                if existing_mi and isinstance(existing_mi, unreal.MaterialInstanceConstant):
                    mi_lib = unreal.MaterialEditingLibrary
                    for param_name, map_type in PARAM_TO_MAP.items():
                        tex_path = f"{DEST_TEXTURE_PATH}/T_Melusina_UpdatedShirt_{map_type}"
                        tex = unreal.load_asset(tex_path)
                        if tex:
                            mi_lib.set_material_instance_texture_parameter_value(existing_mi, param_name, tex)
                    mi_lib.set_material_instance_static_switch_parameter_value(existing_mi, "bUseSeparateRoughnessMap", True)
                    mi_lib.set_material_instance_static_switch_parameter_value(existing_mi, "bUseSeparateMetallicMap", True)
                    unreal.EditorAssetLibrary.save_loaded_asset(existing_mi)
                    print(f"  Updated existing MI on slot 17 with new textures")
            new_materials.append(m)

    mesh.set_editor_property("materials", new_materials)
    unreal.EditorAssetLibrary.save_loaded_asset(mesh)
    print(f"  SK_Melusina slot 17 updated + saved")


def main():
    print("=" * 60)
    print("Melusina Updated Shirt Import")
    print("=" * 60)

    # Step 1: Import FBX
    mesh_path = import_fbx_as_static_mesh()

    # Step 2: Import textures
    textures = import_shirt_textures()

    # Step 3: Build material instance
    shirt_mi = build_shirt_material_instance(textures) if textures else None

    # Step 4: Update mesh slot 17
    update_mesh_slot_17(shirt_mi)

    print("=" * 60)
    print("DONE")
    if mesh_path:
        print(f"  Static Mesh: {mesh_path}")
    if textures:
        print(f"  Textures imported: {len(textures)}/7")
    if shirt_mi:
        print(f"  Material Instance: {shirt_mi.get_path_name()}")
    print("=" * 60)


if __name__ == "__main__":
    main()
