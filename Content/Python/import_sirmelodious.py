"""
From-scratch Sir Melodious import: brings the character into Unreal for the
first time (zero prior footprint in Content/, confirmed via
Docs/SIR_MELODIOUS_ASSESSMENT_2026-07-11.md) and wires his real painted
textures. Mirrors the structure of import_melusina_textures.py, but this is
a fresh SkeletalMesh import (Stage 0) rather than a texture-only pass, since
no SK_SirMelodious asset exists yet.

Source mesh: sirmelodiousalmostdone07.fbx -- already the canonical source in
this project's existing Blender-side tooling (Tools/fix_sirmelodious_and_poses.py
BIRD_FBX constant), so this script reuses the same file rather than picking a
new one. NOTE: as of 2026-07-11 the coat/collar version baked into this FBX
has NOT been visually confirmed against the separate, later-dated
melodiousupdatedcoat.fbx / melodiousupdatedcollar.fbx (2026-03-05, two days
newer than the base melodiouscoat.fbx / melodiouscollar.fbx from 2026-03-03).
Do not run Stage 0 until that's confirmed -- see the open task "Confirm Sir
Melodious coat/collar version via Blender inspection". If almostdone07 turns
out to have the OLD coat, the fix is to re-export a merged FBX in Blender
(swap in melodiousupdatedcoat.fbx/melodiousupdatedcollar.fbx as replacement
objects) before running this script, not to patch it in UE afterward.

Source textures: G:\\sirmelo\\ -- two painted sets, `sirmelo_*` (main
body/coat/clothing) and `feet_*`, each with the standard 7-map Substance
Painter export: BaseColor, Normal, Roughness, Metallic, Alpha, Emission,
Displacement. No reconciliation ambiguity here (unlike Melusina's 3-source,
244-PNG situation) -- one clean source, already confirmed real/painted (not
placeholder) per the assessment doc.

Slot mapping is NOT hardcoded (unlike Melusina's SLOT_MAP) because
SK_SirMelodious doesn't exist yet -- Stage 0 must run first and Stage 1
resolves slot names to texture sets by substring match against SIRMELO_SETS
below. Inspect the printed slot names after Stage 0 and adjust SLOT_KEYWORDS
if the match heuristic picks wrong.

Standing rules: serialize editor access (no parallel Unreal instances/heavy
Monolith calls -- check nothing else is mid-operation first). sRGB gotcha:
BaseColor/Emission = sRGB True (default), Normal = TC_Normalmap sRGB False,
Roughness/Metallic/Alpha/Displacement = TC_Masks sRGB False -- getting this
wrong is the most common toon-shader break (monolith-material-editing-gotchas
memory).
"""
import os
import unreal

SOURCE_FBX = r"G:\EnvironmentPortfolio\BS_GodFile\Exports\SirMelodious\SK_SirMelodious.fbx"
# Legacy mesh-only (no armature) — forensics 2026-07-13: do NOT prefer this for gameplay.
SOURCE_FBX_FALLBACK = r"F:\_FromG_Archive\cinnbunrender\sirmelodiousalmostdone07.fbx"
SOURCE_TEXTURES_DIR = r"G:\sirmelo"
DEST_MESH_PATH = "/Game/Melodia/Characters/SirMelodious"
DEST_TEXTURE_PATH = "/Game/Melodia/Characters/SirMelodious/Textures"
DEST_MI_PATH = "/Game/Melodia/Characters/SirMelodious/Materials"
MASTER_PATH = "/Game/EnvSandbox/Materials/Masters/M_Master_Toon_Universal"
MESH_NAME = "SK_SirMelodious"

MAP_TYPES = ["BaseColor", "Normal", "Roughness", "Metallic", "Alpha", "Emission", "Displacement"]

# texture-set prefix -> keywords used to match against mesh material slot names
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


def _skeletal_meshes_in_destination():
    """Return every skeletal component emitted by this multi-mesh FBX."""
    result = []
    for path in unreal.EditorAssetLibrary.list_assets(DEST_MESH_PATH, recursive=True, include_folder=False):
        asset = unreal.load_asset(path)
        if asset and asset.get_class().get_name() == "SkeletalMesh":
            result.append(asset)
    return result


def stage0_import_meshes():
    """Import the Sir Melodious FBX and return all of its skeletal components.

    Prefer the ARP Unreal export (`Exports/SirMelodious/SK_SirMelodious.fbx`).
    Falls back to the legacy mesh-only almostdone07 FBX only if the ARP file
    is missing (static-only / no real armature — see forensics).
    """
    unreal.EditorAssetLibrary.make_directory(DEST_MESH_PATH)
    existing = _skeletal_meshes_in_destination()
    if existing:
        print(f"  found {len(existing)} existing Sir Melodious skeletal components, skipping re-import")
        return existing

    fbx = SOURCE_FBX if os.path.isfile(SOURCE_FBX) else SOURCE_FBX_FALLBACK
    if not os.path.isfile(fbx):
        raise RuntimeError(
            "Stage 0 FAILED: no FBX at "
            f"{SOURCE_FBX} (ARP export) or {SOURCE_FBX_FALLBACK}. "
            "Run Tools/export_sirmelodious_arp_ue.py in Blender first."
        )
    if fbx == SOURCE_FBX_FALLBACK:
        print(
            "  WARNING: using legacy mesh-only FBX (no armature). "
            "Export ARP Unreal FBX to Exports/SirMelodious/SK_SirMelodious.fbx first."
        )
    else:
        print(f"  using ARP Unreal export: {fbx}")

    task = unreal.AssetImportTask()
    task.filename = fbx
    task.destination_path = DEST_MESH_PATH
    task.destination_name = MESH_NAME
    task.automated = True
    task.save = True
    task.replace_existing = False

    options = unreal.FbxImportUI()
    options.import_mesh = True
    options.import_as_skeletal = True
    options.import_animations = False
    options.import_materials = True
    options.import_textures = False  # we import the real G:\sirmelo set ourselves
    options.skeletal_mesh_import_data.set_editor_property("import_morph_targets", True)
    task.options = options

    unreal.AssetToolsHelpers.get_asset_tools().import_asset_tasks([task])

    imported_paths = task.imported_object_paths
    if not imported_paths:
        raise RuntimeError("Stage 0 FAILED: no objects imported from SOURCE_FBX")

    meshes = []
    for path in imported_paths:
        asset = unreal.load_asset(path)
        if asset and asset.get_class().get_name() == "SkeletalMesh":
            meshes.append(asset)
            print(f"  imported skeletal component {path}")
    if not meshes:
        raise RuntimeError("Stage 0 FAILED: FBX produced no SkeletalMesh assets")
    return meshes


def report_slots(mesh):
    materials = mesh.get_editor_property("materials")
    print(f"  {len(materials)} material slots:")
    for i, m in enumerate(materials):
        print(f"    [{i}] {m.get_editor_property('material_slot_name')}")
    return materials


def import_all_textures():
    unreal.EditorAssetLibrary.make_directory(DEST_TEXTURE_PATH)
    imported = {}  # (prefix, map_type) -> Texture2D
    for prefix in SIRMELO_SETS:
        for map_type in MAP_TYPES:
            src = os.path.join(SOURCE_TEXTURES_DIR, f"{prefix}_{map_type}.png")
            if not os.path.isfile(src):
                print(f"  MISSING {src}")
                continue
            dest_name = f"T_SirMelodious_{prefix}_{map_type}"
            existing = unreal.EditorAssetLibrary.find_asset_data(f"{DEST_TEXTURE_PATH}/{dest_name}")
            if existing.is_valid():
                imported[(prefix, map_type)] = unreal.load_asset(f"{DEST_TEXTURE_PATH}/{dest_name}")
                continue

            task = unreal.AssetImportTask()
            task.filename = src
            task.destination_path = DEST_TEXTURE_PATH
            task.destination_name = dest_name
            task.automated = True
            task.save = False
            task.replace_existing = True
            unreal.AssetToolsHelpers.get_asset_tools().import_asset_tasks([task])

            if not task.imported_object_paths:
                print(f"  FAILED to import {dest_name}")
                imported[(prefix, map_type)] = None
                continue

            tex = unreal.load_asset(task.imported_object_paths[0])
            if map_type == "Normal":
                tex.set_editor_property("compression_settings", unreal.TextureCompressionSettings.TC_NORMALMAP)
                tex.set_editor_property("srgb", False)
            elif map_type in ("Roughness", "Metallic", "Alpha", "Displacement"):
                tex.set_editor_property("compression_settings", unreal.TextureCompressionSettings.TC_MASKS)
                tex.set_editor_property("srgb", False)
            # BaseColor / Emission keep default (TC_Default, sRGB True)

            unreal.EditorAssetLibrary.save_loaded_asset(tex)
            imported[(prefix, map_type)] = tex
            print(f"  imported {dest_name}")
    return imported


def build_material_instances(imported_textures):
    unreal.EditorAssetLibrary.make_directory(DEST_MI_PATH)
    asset_tools = unreal.AssetToolsHelpers.get_asset_tools()
    master = unreal.load_asset(MASTER_PATH)
    mi_lib = unreal.MaterialEditingLibrary
    results = {}

    for prefix in SIRMELO_SETS:
        mi_name = f"MI_SirMelodious_{prefix.capitalize()}"
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

        for param_name, map_type in PARAM_TO_MAP.items():
            tex = imported_textures.get((prefix, map_type))
            if tex:
                mi_lib.set_material_instance_texture_parameter_value(mi, param_name, tex)

        mi_lib.set_material_instance_static_switch_parameter_value(mi, "bUseSeparateRoughnessMap", True)
        mi_lib.set_material_instance_static_switch_parameter_value(mi, "bUseSeparateMetallicMap", True)

        unreal.EditorAssetLibrary.save_loaded_asset(mi)
        results[prefix] = mi
        print(f"  built {mi_name}")

    return results


def assign_to_mesh(mesh, materials, mi_results):
    new_materials = []
    changed = 0
    for m in materials:
        slot_name = str(m.get_editor_property("material_slot_name")).lower()
        matched_mi = None
        for prefix, keywords in SIRMELO_SETS.items():
            if any(kw in slot_name for kw in keywords):
                matched_mi = mi_results.get(prefix)
                break
        if matched_mi is None:
            # default: everything unmatched falls back to the main body set
            matched_mi = mi_results.get("sirmelo")

        if matched_mi:
            new_materials.append(unreal.SkeletalMaterial(
                material_interface=matched_mi,
                material_slot_name=m.get_editor_property("material_slot_name"),
                uv_channel_data=m.get_editor_property("uv_channel_data"),
            ))
            changed += 1
        else:
            new_materials.append(m)

    mesh.set_editor_property("materials", new_materials)
    unreal.EditorAssetLibrary.save_loaded_asset(mesh)
    print(f"Assigned {changed}/{len(materials)} slots on {mesh.get_name()}")


def main():
    print("=== Stage 0: importing SkeletalMesh ===")
    meshes = stage0_import_meshes()
    material_sets = [(mesh, report_slots(mesh)) for mesh in meshes]
    print("=== Stage 1: importing textures ===")
    imported = import_all_textures()
    print("=== Stage 2: building material instances ===")
    mi_results = build_material_instances(imported)
    print("=== Stage 3: assigning to mesh ===")
    for mesh, materials in material_sets:
        assign_to_mesh(mesh, materials, mi_results)
    slot_count = sum(len(materials) for _, materials in material_sets)
    print(f"=== DONE: {len(mi_results)} texture sets, {len(meshes)} skeletal components, {slot_count} slots processed ===")
    print("Review the printed slot list above -- if SIRMELO_SETS keyword matching")
    print("picked the wrong texture set for any slot, fix SLOT_KEYWORDS and rerun")
    print("(idempotent: existing textures/MIs are reused, not re-imported).")


if __name__ == "__main__":
    main()
