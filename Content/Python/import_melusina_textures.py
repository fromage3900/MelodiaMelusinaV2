"""
Phase A of the Melusina finalization plan: import her real Substance Painter
textures (staged from G:\\MelodiaMelusina\\ACTUALCOMPILEDMELUSINATEXTURES\\)
and build one MI_Melusina_<Slot> per confirmed SK_Melusina material slot,
off M_Master_Toon_Universal.

Slot -> source mapping was reconciled by hand (UV-shell visual comparison +
user confirmation) — see Docs/MELUSINA_TEXTURE_IMPORT_PLAN.md. 32 of 35
mesh slots are resolved here; 3 are intentionally skipped (no matching
source found): Material_019 (slot 26), Material_018 (slot 28),
Iridescence_002 (slot 30, needs a dedicated thin-film shader, not a PBR set).

Master static-switch gotcha (verified via export_material_graph before
writing this): bUseSeparateRoughnessMap / bUseSeparateMetallicMap both
default False, meaning the master reads packed ORM unless a MI explicitly
overrides both switches to True. Our source has no packed ORM -> every MI
below sets both switches True.
"""
import os
import shutil
import unreal

SOURCE_NEW_FOLDER = r"G:\MelodiaMelusina\ACTUALCOMPILEDMELUSINATEXTURES\New folder"
SOURCE_MELUSINABODY = r"G:\MelodiaMelusina\ACTUALCOMPILEDMELUSINATEXTURES\melusinabody"
STAGING_DIR = r"G:\EnvironmentPortfolio\BS_GodFile\Imports\MelusinaTextures"
DEST_TEXTURE_PATH = "/Game/Melodia/Characters/Melusina/Textures"
DEST_MI_PATH = "/Game/Melodia/Characters/Melusina/Materials"
MASTER_PATH = "/Game/EnvSandbox/Materials/Masters/M_Master_Toon_Universal"
MESH_PATH = "/Game/Melodia/Characters/Melusina/SK_Melusina"

# slot_index: (slot_name, source_dir, source_prefix)
SLOT_MAP = {
    0: ("Gradient__Radial__002", SOURCE_NEW_FOLDER, "Gradient (Radial)"),
    1: ("SBW_MELUSINA_006", SOURCE_MELUSINABODY, "M_Melusina"),
    2: ("SBW_MELUSINA_007", SOURCE_MELUSINABODY, "M_Melusina"),
    3: ("sleeve_003", SOURCE_NEW_FOLDER, "m_sleeve"),
    4: ("Outline_Shader_*_024", SOURCE_NEW_FOLDER, "Outline"),
    5: ("Metal_2__Matcap__002", SOURCE_NEW_FOLDER, "Metal 2 (Matcap)"),
    6: ("Outline_005", SOURCE_NEW_FOLDER, "Outline"),
    7: ("Material_021", SOURCE_NEW_FOLDER, "Material.001"),
    8: ("Outline_004", SOURCE_NEW_FOLDER, "Outline"),
    9: ("Material_013", SOURCE_NEW_FOLDER, "Material.007"),
    10: ("Halftone_Circles___Circles__3_Inputs__001", SOURCE_NEW_FOLDER, "Halftone Circles & Circles (3 Inputs)"),
    11: ("Material_022", SOURCE_NEW_FOLDER, "Material.008"),
    12: ("Material_023", SOURCE_NEW_FOLDER, "Material.010"),
    13: ("IRISFRONT_001", SOURCE_MELUSINABODY, "M_Iris_front"),
    14: ("Outline_Shader_*_034", SOURCE_NEW_FOLDER, "Outline"),
    15: ("bow_002", SOURCE_NEW_FOLDER, "m_bow"),
    16: ("Outline_Shader_*_029", SOURCE_NEW_FOLDER, "Outline"),
    17: ("Material_024", SOURCE_NEW_FOLDER, "Material.013"),
    18: ("skirtpanel_002", SOURCE_NEW_FOLDER, "skirtpanel.004"),
    19: ("Outline_Shader_*_025", SOURCE_NEW_FOLDER, "Outline"),
    20: ("SHAWL_001", SOURCE_NEW_FOLDER, "m_shawl"),
    21: ("frontpanel_001", SOURCE_NEW_FOLDER, "m_frontpanel"),
    22: ("Outline_Shader_*_023", SOURCE_NEW_FOLDER, "Outline"),
    23: ("GLOVES_001", SOURCE_NEW_FOLDER, "m_gloves"),
    24: ("Outline_Shader_*_030", SOURCE_NEW_FOLDER, "Outline"),
    25: ("Material_017", SOURCE_NEW_FOLDER, "Material.020"),
    # 26: Material_019 -- SKIPPED, no source match (only 6 Material.0NN exist, 8 mesh slots need one)
    27: ("Outline_Shader_*_028", SOURCE_NEW_FOLDER, "Outline"),
    # 28: Material_018 -- SKIPPED, same reason as 26
    29: ("Outline_Shader_*_027", SOURCE_NEW_FOLDER, "Outline"),
    # 30: Iridescence_002 -- SKIPPED, needs dedicated thin-film shader, not PBR
    31: ("Outline_Shader_*_026", SOURCE_NEW_FOLDER, "Outline"),
    32: ("Outline_Shader_*_032", SOURCE_NEW_FOLDER, "Outline"),
    33: ("SKIRT_003", SOURCE_NEW_FOLDER, "m_skirt"),
    34: ("Halftone_3_Inputs_-_Lines___Circles_002", SOURCE_NEW_FOLDER, "Halftone Circles & Circles (3 Inputs)"),
}

MAP_TYPES = ["BaseColor", "Normal", "Roughness", "Metallic", "Alpha", "Emission", "Displacement"]


KNOWN_BROKEN_SIBLING_MIS = [
    # Content validation on save can auto-open OTHER MaterialInstanceConstants
    # of the same parent (M_Master_Toon_Universal) that already fail to
    # compile for unrelated reasons, blocking the game thread until closed.
    # Observed: MI_Zen_MossStone (MF_Madoka references a 3rd MaterialParameterCollection,
    # exceeding UE's 2-collection-per-material limit). Defensively close it
    # after every save so this can't accumulate into a hang.
    "/Game/EnvSandbox/Materials/Instances/Environment/Zen/MI_Zen_MossStone",
]


def _close_stray_editors(saved_asset=None):
    aes = unreal.get_editor_subsystem(unreal.AssetEditorSubsystem)
    targets = list(KNOWN_BROKEN_SIBLING_MIS)
    if saved_asset is not None:
        try:
            targets.append(saved_asset.get_path_name().split(".")[0])
        except Exception:
            pass
    for path in targets:
        try:
            obj = unreal.load_asset(path)
            if obj:
                aes.close_all_editors_for_asset(obj)
        except Exception:
            pass

# master texture-param name -> source map-type suffix
PARAM_TO_MAP = {
    "Albedo": "BaseColor",
    "NormalMap": "Normal",
    "RoughnessMap": "Roughness",
    "MetallicMap": "Metallic",
    "HeightMap": "Displacement",
}


def stage_files():
    os.makedirs(STAGING_DIR, exist_ok=True)
    copied = set()
    for slot_idx, (slot_name, src_dir, prefix) in SLOT_MAP.items():
        for map_type in MAP_TYPES:
            src = os.path.join(src_dir, f"{prefix}_{map_type}.png")
            if not os.path.isfile(src):
                continue
            dst_name = f"{prefix}_{map_type}.png".replace(" ", "_").replace("(", "").replace(")", "").replace("&", "and").replace("*", "star")
            dst = os.path.join(STAGING_DIR, dst_name)
            if dst not in copied:
                shutil.copyfile(src, dst)
                copied.add(dst)
    print(f"Staged {len(copied)} unique texture files")
    return copied


def staged_name(prefix, map_type):
    return f"{prefix}_{map_type}.png".replace(" ", "_").replace("(", "").replace(")", "").replace("&", "and").replace("*", "star")


def import_texture(staged_path, dest_name, map_type):
    existing = unreal.EditorAssetLibrary.find_asset_data(f"{DEST_TEXTURE_PATH}/{dest_name}")
    if existing.is_valid():
        return unreal.load_asset(f"{DEST_TEXTURE_PATH}/{dest_name}")

    task = unreal.AssetImportTask()
    task.filename = staged_path
    task.destination_path = DEST_TEXTURE_PATH
    task.destination_name = dest_name
    task.automated = True
    task.save = False
    task.replace_existing = True
    unreal.AssetToolsHelpers.get_asset_tools().import_asset_tasks([task])

    imported_paths = task.imported_object_paths
    if not imported_paths:
        print(f"  FAILED to import {staged_path}")
        return None
    tex = unreal.load_asset(imported_paths[0])
    if not tex:
        return None

    if map_type in ("Normal",):
        tex.set_editor_property("compression_settings", unreal.TextureCompressionSettings.TC_NORMALMAP)
        tex.set_editor_property("srgb", False)
    elif map_type in ("Roughness", "Metallic", "Displacement"):
        tex.set_editor_property("compression_settings", unreal.TextureCompressionSettings.TC_MASKS)
        tex.set_editor_property("srgb", False)
    elif map_type == "Alpha":
        tex.set_editor_property("compression_settings", unreal.TextureCompressionSettings.TC_MASKS)
        tex.set_editor_property("srgb", False)
    # BaseColor / Emission keep default (TC_Default, sRGB True)

    unreal.EditorAssetLibrary.save_loaded_asset(tex)
    _close_stray_editors(tex)
    return tex


def import_all_textures():
    unreal.EditorAssetLibrary.make_directory(DEST_TEXTURE_PATH)
    imported = {}  # (prefix, map_type) -> Texture2D
    for slot_idx, (slot_name, src_dir, prefix) in SLOT_MAP.items():
        for map_type in MAP_TYPES:
            key = (prefix, map_type)
            if key in imported:
                continue
            staged = os.path.join(STAGING_DIR, staged_name(prefix, map_type))
            if not os.path.isfile(staged):
                continue
            dest_name = f"T_Melusina_{prefix}_{map_type}".replace(" ", "_").replace("(", "").replace(")", "").replace("&", "and").replace("*", "star").replace(".", "_")
            try:
                tex = import_texture(staged, dest_name, map_type)
            except Exception as exc:
                print(f"  imported {dest_name}: EXCEPTION {exc}")
                imported[key] = None
                continue
            imported[key] = tex
            print(f"  imported {dest_name}: {'OK' if tex else 'FAIL'}")
    return imported


def build_material_instances(imported_textures):
    unreal.EditorAssetLibrary.make_directory(DEST_MI_PATH)
    asset_tools = unreal.AssetToolsHelpers.get_asset_tools()
    master = unreal.load_asset(MASTER_PATH)
    mi_lib = unreal.MaterialEditingLibrary
    results = {}

    for slot_idx, (slot_name, src_dir, prefix) in SLOT_MAP.items():
        mi_name = f"MI_Melusina_{slot_name}".replace("*", "star")
        try:
            existing = unreal.EditorAssetLibrary.find_asset_data(f"{DEST_MI_PATH}/{mi_name}")
            if existing.is_valid():
                mi = unreal.load_asset(f"{DEST_MI_PATH}/{mi_name}")
            else:
                factory = unreal.MaterialInstanceConstantFactoryNew()
                mi = asset_tools.create_asset(mi_name, DEST_MI_PATH, unreal.MaterialInstanceConstant, factory)
                if mi:
                    mi_lib.set_material_instance_parent(mi, master)

            if not mi:
                print(f"  FAILED to create {mi_name}")
                continue

            if mi.get_editor_property("parent") != master:
                mi_lib.set_material_instance_parent(mi, master)

            for param_name, map_type in PARAM_TO_MAP.items():
                tex = imported_textures.get((prefix, map_type))
                if tex:
                    mi_lib.set_material_instance_texture_parameter_value(mi, param_name, tex)

            mi_lib.set_material_instance_static_switch_parameter_value(mi, "bUseSeparateRoughnessMap", True)
            mi_lib.set_material_instance_static_switch_parameter_value(mi, "bUseSeparateMetallicMap", True)

            unreal.EditorAssetLibrary.save_loaded_asset(mi)
            _close_stray_editors(mi)
            results[slot_idx] = mi
            print(f"  built {mi_name}")
        except Exception as exc:
            print(f"  built {mi_name}: EXCEPTION {exc}")
            continue

    return results


def assign_to_mesh(mi_results):
    # NOTE: mesh.get_editor_property("materials") returns TEMPORARY struct
    # copies per-element in this UE5.8 Python binding -- mutating
    # materials[i].set_editor_property(...) in place does NOT propagate back,
    # even with mesh.modify() + save. Must rebuild the whole list with fresh
    # unreal.SkeletalMaterial(...) instances and assign it wholesale.
    mesh = unreal.load_asset(MESH_PATH)
    materials = mesh.get_editor_property("materials")
    changed = 0
    new_materials = []
    for i, m in enumerate(materials):
        if i in mi_results:
            new_materials.append(unreal.SkeletalMaterial(
                material_interface=mi_results[i],
                material_slot_name=m.get_editor_property("material_slot_name"),
                uv_channel_data=m.get_editor_property("uv_channel_data"),
            ))
            changed += 1
        else:
            new_materials.append(m)
    mesh.set_editor_property("materials", new_materials)
    unreal.EditorAssetLibrary.save_loaded_asset(mesh)
    _close_stray_editors(mesh)
    print(f"Assigned {changed} slots on SK_Melusina")


def main():
    print("=== Stage 1: staging files ===")
    stage_files()
    print("=== Stage 2: importing textures ===")
    imported = import_all_textures()
    print("=== Stage 3: building material instances ===")
    mi_results = build_material_instances(imported)
    print("=== Stage 4: assigning to mesh ===")
    assign_to_mesh(mi_results)
    print(f"=== DONE: {len(mi_results)}/{len(SLOT_MAP)} slots processed (3 intentionally skipped: 26, 28, 30) ===")


if __name__ == "__main__":
    main()
