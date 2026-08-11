"""Fix Sir Melodious material instances, texture references, and mesh slot assignments.

Must run audit_sirmelodious_materials.py FIRST to see current state.
This script is idempotent (safe to rerun).

Run in UE Python console:
    exec(open(r'G:/EnvironmentPortfolio/BS_GodFile/Content/Python/fix_sirmelodious_materials.py').read())
"""

from __future__ import annotations

import os
import unreal


SIRMELO_ROOT = "/Game/Melodia/Characters/SirMelodious"
MASTER = "/Game/EnvSandbox/Materials/Masters/M_Master_Toon_Universal"
SOURCE_TEXTURES_DIR = r"G:\sirmelo"
DEST_TEXTURE_PATH = f"{SIRMELO_ROOT}/Textures"
DEST_MI_PATH = f"{SIRMELO_ROOT}/Materials"

MAP_TYPES = ["BaseColor", "Normal", "Roughness", "Metallic", "Alpha", "Emission", "Displacement"]

SIRMELO_SETS = {
    "sirmelo": ["body", "coat", "collar", "cloth", "ruffle", "tie", "shirt", "main"],
    "feet": ["feet", "foot", "shoe", "boot"],
}

PARAM_TO_MAP = {
    "Albedo": "BaseColor",
    "NormalMap": "Normal",
    "RoughnessMap": "Roughness",
    "MetallicMap": "Metallic",
    "HeightMap": "Displacement",
}


def fix_material_instances():
    """Ensure MIs have correct parent, static switches, and texture references."""
    print("=== Step 1: Fix Material Instances ===")
    mi_lib = unreal.MaterialEditingLibrary
    master = unreal.load_asset(MASTER)
    if not master:
        raise RuntimeError(f"Master material missing: {MASTER}")

    mi_paths = {
        "sirmelo": f"{DEST_MI_PATH}/MI_SirMelodious_Sirmelo",
        "feet": f"{DEST_MI_PATH}/MI_SirMelodious_Feet",
    }

    results = {}
    for prefix, mi_path in mi_paths.items():
        mi = unreal.load_asset(mi_path)
        if not mi:
            print(f"  MI not found: {mi_path} (will create)")
            asset_tools = unreal.AssetToolsHelpers.get_asset_tools()
            factory = unreal.MaterialInstanceConstantFactoryNew()
            mi_name = f"MI_SirMelodious_{prefix.capitalize()}"
            mi = asset_tools.create_asset(mi_name, DEST_MI_PATH, unreal.MaterialInstanceConstant, factory)

        if not mi:
            print(f"  FAILED to get/create {mi_path}")
            results[prefix] = False
            continue

        # Fix parent
        current_parent = mi.get_editor_property("parent")
        if not current_parent or current_parent.get_path_name() != master.get_path_name():
            mi_lib.set_material_instance_parent(mi, master)
            print(f"  {prefix}: set parent to M_Master_Toon_Universal")

        # Fix texture references
        for param, maptype in PARAM_TO_MAP.items():
            tex_path = f"{DEST_TEXTURE_PATH}/T_SirMelodious_{prefix}_{maptype}"
            current_tex = mi_lib.get_material_instance_texture_parameter_value(mi, param)
            expected = unreal.load_asset(tex_path)
            if expected and current_tex != expected:
                mi_lib.set_material_instance_texture_parameter_value(mi, param, expected)
                print(f"  {prefix}: set {param} -> T_SirMelodious_{prefix}_{maptype}")
            elif not expected:
                print(f"  {prefix}: texture missing for {param} ({tex_path})")

        # Fix static switches
        for sw in ("bUseSeparateRoughnessMap", "bUseSeparateMetallicMap"):
            try:
                current = mi_lib.get_material_instance_static_switch_parameter_value(mi, sw)
                if not current:
                    mi_lib.set_material_instance_static_switch_parameter_value(mi, sw, True)
                    print(f"  {prefix}: set {sw} = True (was {current})")
            except Exception:
                try:
                    mi_lib.set_material_instance_static_switch_parameter_value(mi, sw, True)
                    print(f"  {prefix}: set {sw} = True (was unreadable)")
                except Exception as exc:
                    print(f"  {prefix}: FAILED {sw}: {exc}")

        unreal.EditorAssetLibrary.save_loaded_asset(mi)
        results[prefix] = True
        print(f"  {prefix}: saved")

    return results


def import_missing_textures():
    """Import any textures from G:\sirmelo that are missing from the UE project."""
    print("=== Step 2: Check/Import Missing Textures ===")
    imported = 0
    skipped = 0

    for prefix in SIRMELO_SETS:
        for maptype in MAP_TYPES:
            tex_name = f"T_SirMelodious_{prefix}_{maptype}"
            tex_path = f"{DEST_TEXTURE_PATH}/{tex_name}"

            if unreal.EditorAssetLibrary.does_asset_exist(tex_path):
                skipped += 1
                continue

            src = os.path.join(SOURCE_TEXTURES_DIR, f"{prefix}_{maptype}.png")
            if not os.path.isfile(src):
                print(f"  NO SOURCE: {prefix}_{maptype}.png")
                continue

            task = unreal.AssetImportTask()
            task.set_editor_property("filename", src)
            task.set_editor_property("destination_path", DEST_TEXTURE_PATH)
            task.set_editor_property("destination_name", tex_name)
            task.set_editor_property("replace_existing", True)
            task.set_editor_property("automated", True)
            task.set_editor_property("save", False)

            asset_tools = unreal.AssetToolsHelpers.get_asset_tools()
            asset_tools.import_asset_tasks([task])
            imported_paths = task.get_editor_property("imported_object_paths")

            if not imported_paths:
                print(f"  IMPORT FAILED: {tex_name}")
                continue

            tex = unreal.load_asset(imported_paths[0])
            if not tex:
                continue

            if maptype == "Normal":
                tex.set_editor_property("compression_settings", unreal.TextureCompressionSettings.TC_NORMALMAP)
                tex.set_editor_property("srgb", False)
            elif maptype in ("Roughness", "Metallic", "Displacement", "Alpha"):
                tex.set_editor_property("compression_settings", unreal.TextureCompressionSettings.TC_MASKS)
                tex.set_editor_property("srgb", False)

            unreal.EditorAssetLibrary.save_loaded_asset(tex)
            imported += 1
            print(f"  Imported: {tex_name}")

    print(f"  Imported: {imported}, Already present: {skipped}")
    return imported


def assign_materials_to_all_meshes():
    """Assign proper MIs to ALL Sir Melodious mesh slots."""
    print("=== Step 3: Assign Materials to Meshes ===")

    sirmelo_mi = unreal.load_asset(f"{DEST_MI_PATH}/MI_SirMelodious_Sirmelo")
    feet_mi = unreal.load_asset(f"{DEST_MI_PATH}/MI_SirMelodious_Feet")

    if not sirmelo_mi:
        print("  ERROR: MI_SirMelodious_Sirmelo missing!")
        return

    mesh_paths = []
    # Collect all skeletal meshes under the SirMelodious directory
    for path in unreal.EditorAssetLibrary.list_assets(SIRMELO_ROOT, recursive=True, include_folder=False):
        asset = unreal.load_asset(path)
        if asset and asset.get_class().get_name() in ("SkeletalMesh", "StaticMesh"):
            mesh_paths.append(path)

    print(f"  Found {len(mesh_paths)} mesh assets")

    for mp in mesh_paths:
        mesh = unreal.load_asset(mp)
        if not mesh:
            continue

        materials = mesh.get_editor_property("materials") or []
        if not materials:
            continue

        new_materials = []
        changed = 0
        for slot in materials:
            slot_name = str(slot.get_editor_property("material_slot_name")).lower()
            matched_mi = sirmelo_mi  # default: body set
            for prefix, keywords in SIRMELO_SETS.items():
                if any(kw in slot_name for kw in keywords):
                    if prefix == "feet":
                        matched_mi = feet_mi if feet_mi else sirmelo_mi
                    break

            mi_class = slot.get_editor_property("material_interface")
            is_fbx_stub = True
            if mi_class:
                try:
                    is_fbx_stub = mi_class.get_class().get_name() not in ("MaterialInstanceConstant",)
                except Exception:
                    is_fbx_stub = True

            if is_fbx_stub or mi_class != matched_mi:
                new_materials.append(unreal.SkeletalMaterial(
                    material_interface=matched_mi,
                    material_slot_name=slot.get_editor_property("material_slot_name"),
                    uv_channel_data=slot.get_editor_property("uv_channel_data"),
                ))
                changed += 1
            else:
                new_materials.append(slot)

        if changed > 0:
            mesh.set_editor_property("materials", new_materials)
            unreal.EditorAssetLibrary.save_loaded_asset(mesh)
            print(f"  {mesh.get_name()}: {changed}/{len(materials)} slots updated")
        else:
            print(f"  {mesh.get_name()}: all {len(materials)} slots already correct")


def main():
    print("=" * 60)
    print("Sir Melodious Material Fix")
    print("=" * 60)

    # Step 1: Import any missing textures
    import_missing_textures()

    # Step 2: Fix material instances (parent, switches, texture refs)
    fix_material_instances()

    # Step 3: Assign materials to all mesh slots
    assign_materials_to_all_meshes()

    print("=" * 60)
    print("DONE. Run audit_sirmelodious_materials.py to verify.")
    print("=" * 60)


if __name__ == "__main__":
    main()
