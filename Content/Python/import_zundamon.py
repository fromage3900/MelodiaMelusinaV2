"""Zundamon Unreal Import Script ΓÇö run in UE Python console or via MCP.

Imports the Zundamon FBX, creates materials, and sets up the skeletal mesh.
Run: Window ΓåÆ Developer Tools ΓåÆ Python Console
  import import_zundamon; import_zundamon.run()

Or via MCP:
  POST to :9316/mcp with tool editor_query, action run_python
"""

import unreal

# Paths
FBX_PATH = r"G:\EnvironmentPortfolio\BS_GodFile\Content\Melodia\Characters\Zundamon\Zundamon.fbx"
IMPORT_DEST = "/Game/Melodia/Characters/Zundamon"
TEXTURE_DEST = "/Game/Melodia/Characters/Zundamon/Textures"

# Material mapping: Zundamon texture ΓåÆ Melodia material slot
MATERIAL_LAYOUT = {
    "Body":  {"texture": "Body.png",  "slot_name": "Body"},
    "Cloth": {"texture": "Cloth.png", "slot_name": "Cloth"},
    "Hair":  {"texture": "Hair.png",  "slot_name": "Hair"},
    "Head":  {"texture": "Head.png",  "slot_name": "Head"},
    "Eye":   {"texture": "Eye.png",   "slot_name": "Eye"},
}


def create_folder_structure():
    """Ensure target folders exist."""
    paths = [IMPORT_DEST, TEXTURE_DEST]
    for p in paths:
        if not unreal.EditorAssetLibrary.does_directory_exist(p):
            unreal.EditorAssetLibrary.make_directory(p)
            print(f"  Created: {p}")


def import_textures():
    """Import all Zundamon PNG textures into Unreal."""
    import os
    tex_dir = os.path.dirname(FBX_PATH) + "\\Textures"
    imported = []
    for fname in os.listdir(tex_dir):
        if not fname.lower().endswith(".png"):
            continue
        src = os.path.join(tex_dir, fname)
        asset_name = f"T_Zundamon_{os.path.splitext(fname)[0]}"
        asset_path = f"{TEXTURE_DEST}/{asset_name}"

        # Skip if already exists
        if unreal.EditorAssetLibrary.does_asset_exist(asset_path):
            imported.append(asset_path)
            continue

        task = unreal.AssetImportTask()
        task.filename = src
        task.destination_path = TEXTURE_DEST
        task.destination_name = asset_name
        task.replace_existing = True
        task.automated = True
        task.save = True

        factory = unreal.TextureFactory()
        factory.set_editor_property("no_compression", False)
        task.factory = factory

        unreal.AssetToolsHelpers.get_asset_tools().import_asset_tasks([task])
        for obj_path in task.imported_object_paths:
            imported.append(obj_path)
            print(f"  Imported: {obj_path}")

    return imported


def import_fbx():
    """Import the Zundamon FBX as a skeletal mesh."""
    if unreal.EditorAssetLibrary.does_asset_exist(f"{IMPORT_DEST}/SK_Zundamon"):
        print(f"  SK_Zundamon already exists ΓÇö skipping FBX import")
        return f"{IMPORT_DEST}/SK_Zundamon"

    task = unreal.AssetImportTask()
    task.filename = FBX_PATH
    task.destination_path = IMPORT_DEST
    task.destination_name = "SK_Zundamon"
    task.replace_existing = False
    task.automated = True
    task.save = True

    # Configure FBX import settings
    fbx_options = unreal.FbxImportUI()
    fbx_options.set_editor_property("import_mesh", True)
    fbx_options.set_editor_property("import_as_skeletal", True)
    fbx_options.set_editor_property("import_materials", False)
    fbx_options.set_editor_property("import_textures", False)
    fbx_options.set_editor_property("import_animations", False)

    # Skeletal mesh options
    sk_options = unreal.FbxMeshImportData()
    sk_options.set_editor_property("normal_import_method", unreal.FBXNormalImportMethod.FBXNIM_IMPORT_NORMALS_AND_TANGENTS)
    sk_options.set_editor_property("normal_generation_method", unreal.FBXNormalGenerationMethod.BUILT_IN)

    fbx_options.set_editor_property("mesh_type_to_import", unreal.FBXImportType.FBXIT_SKELETAL_MESH)
    fbx_options.skeletal_mesh_import_data = sk_options

    task.options = fbx_options

    unreal.AssetToolsHelpers.get_asset_tools().import_asset_tasks([task])

    mesh_path = f"{IMPORT_DEST}/SK_Zundamon"
    if unreal.EditorAssetLibrary.does_asset_exist(mesh_path):
        print(f"  Imported: {mesh_path}")

        # Save the skeletal mesh
        unreal.EditorAssetLibrary.save_asset(mesh_path)

        # Auto-generate physics asset
        try:
            sk = unreal.EditorAssetLibrary.load_asset(mesh_path)
            if sk:
                phys_asset = unreal.EditorAssetLibrary.load_asset(f"{IMPORT_DEST}/SK_Zundamon_PhysicsAsset")
                if not phys_asset:
                    # Create physics asset
                    phys_path = f"{IMPORT_DEST}/SK_Zundamon_PhysicsAsset"
                    # Note: physics asset auto-creation requires manual step or additional API
                    print(f"  Physics asset needs manual creation at: {phys_path}")
        except Exception as e:
            print(f"  Physics asset creation note: {e}")
    else:
        print(f"  WARNING: SK_Zundamon import may have failed")

    return mesh_path


def create_materials():
    """Create material instances for Zundamon using Melodia character material base."""
    # Use existing Melusina material instance as parent, or create standalone
    material_instances = {}

    # Try to find a parent material
    parent_mat = unreal.EditorAssetLibrary.load_asset(
        "/Game/EnvSandbox/Materials/Masters/M_UniversalSurface"
    )
    if not parent_mat:
        # Fallback: use any existing master material
        parent_mat = unreal.EditorAssetLibrary.load_asset(
            "/Game/EnvSandbox/Materials/M_ToonSubstrate"
        )
    if not parent_mat:
        print("  WARNING: No parent material found. Creating basic material instances.")
        # Use a simple default
        parent_mat = None

    materials_to_create = [
        ("MI_Zundamon_Body",  "Body.png"),
        ("MI_Zundamon_Cloth", "Cloth.png"),
        ("MI_Zundamon_Hair",  "Hair.png"),
        ("MI_Zundamon_Head",  "Head.png"),
        ("MI_Zundamon_Eye",   "Eye.png"),
    ]

    for mi_name, tex_name in materials_to_create:
        mi_path = f"{IMPORT_DEST}/{mi_name}"
        if unreal.EditorAssetLibrary.does_asset_exist(mi_path):
            material_instances[mi_name] = mi_path
            continue

        # Create material instance
        asset_tools = unreal.AssetToolsHelpers.get_asset_tools()
        mi = asset_tools.create_asset(
            mi_name, IMPORT_DEST,
            unreal.MaterialInstanceConstant,
            unreal.MaterialInstanceConstantFactoryNew()
        )

        if parent_mat:
            mi.set_editor_property("parent", parent_mat)

        # Try to set the base color texture parameter
        tex_path = f"{TEXTURE_DEST}/T_Zundamon_{tex_name.replace('.png', '')}"
        tex = unreal.EditorAssetLibrary.load_asset(tex_path)
        if tex:
            try:
                unreal.MaterialEditingLibrary.set_material_instance_texture_parameter_value(
                    mi, "BaseColor", tex
                )
            except Exception:
                # Parameter name might differ
                try:
                    unreal.MaterialEditingLibrary.set_material_instance_texture_parameter_value(
                        mi, "Base_Color", tex
                    )
                except Exception:
                    print(f"  Could not set texture param on {mi_name}")

        unreal.EditorAssetLibrary.save_asset(mi_path)
        material_instances[mi_name] = mi_path
        print(f"  Created: {mi_path}")

    return material_instances


def apply_materials_to_mesh(mesh_path: str, material_instances: dict):
    """Assign materials to the skeletal mesh material slots by name matching."""
    sk = unreal.EditorAssetLibrary.load_asset(mesh_path)
    if not sk:
        print("  Cannot load skeletal mesh for material assignment")
        return

    materials = sk.get_editor_property("materials")
    print(f"  Mesh has {len(materials)} material slots")

    # Map slot names to material instances
    for i, mat_slot in enumerate(materials):
        slot_name = str(mat_slot.get_editor_property("material_slot_name") or f"Slot_{i}")
        print(f"    Slot {i}: {slot_name}")

        # Try to match by name
        for mi_name, mi_path in material_instances.items():
            mat_part = mi_name.replace("MI_Zundamon_", "").lower()
            if mat_part in slot_name.lower() or slot_name.lower() in mat_part:
                mi = unreal.EditorAssetLibrary.load_asset(mi_path)
                if mi:
                    materials[i].set_editor_property("material_interface", mi)
                    sk.set_editor_property("materials", materials)
                    unreal.EditorAssetLibrary.save_asset(mesh_path)
                    print(f"    ΓåÆ Assigned {mi_name} to slot {i}")

    unreal.EditorAssetLibrary.save_asset(mesh_path)


def run():
    """Main entry point ΓÇö import Zundamon into Unreal."""
    print("=" * 60)
    print("ZUNDAMON UNREAL IMPORT")
    print("=" * 60)

    create_folder_structure()

    print("\n[1/4] Importing textures...")
    import_textures()

    print("\n[2/4] Importing FBX...")
    mesh_path = import_fbx()

    print("\n[3/4] Creating materials...")
    material_instances = create_materials()

    print("\n[4/4] Applying materials to mesh...")
    if mesh_path:
        apply_materials_to_mesh(mesh_path, material_instances)

    print("\n" + "=" * 60)
    print("IMPORT COMPLETE")
    print(f"  Skeletal mesh: {mesh_path}")
    print(f"  Materials: {list(material_instances.keys())}")
    print("=" * 60)
    print("\nNext steps:")
    print("  1. Open SK_Zundamon ΓåÆ create Physics Asset (right-click ΓåÆ Create Physics Asset)")
    print("  2. Create IK Rig for retargeting (or assign to UE5 mannequin skeleton)")
    print("  3. Create Animation Blueprint ΓåÆ ABP_Zundamon")
    print("  4. Create Blueprint ΓåÆ BP_Zundamon_NPC")

    return mesh_path


if __name__ == "__main__":
    run()
