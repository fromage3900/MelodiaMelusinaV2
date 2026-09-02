import unreal
import os

# Reimport Reef meshes that were beveled via Houdini SOP polyBevel
reef_dir = "/Game/EnvSandbox/Monoliths/SeaAbove/Prototype/Reef/Meshes"

targets = [
    "SM_Clutter_Starfish",
    "SM_Kelp_Cluster",
    "SM_Kelp_Mid",
    "SM_Kelp_Tall",
    "SM_Coral_Fan",
    "SM_Coral_Table",
    "SM_Coral_TubeSponges",
    "SM_RockChunk_L",
    "SM_RockChunk_M",
]

print("="*60)
print("REIMPORT BEVELED REEF MESHES")
print("="*60)

for name in targets:
    asset_path = f"{reef_dir}/{name}.{name}"
    # Try reimport via asset import task
    try:
        tasks = unreal.AssetImportTask()
        tasks.set_editor_property("filename", f"C:/EnvironmentPortfolio/BS_GodFile/Content/EnvSandbox/Monoliths/SeaAbove/Prototype/Reef/Meshes/{name}.obj")
        tasks.set_editor_property("destination_path", reef_dir)
        tasks.set_editor_property("destination_name", name)
        tasks.set_editor_property("replace_existing", True)
        tasks.set_editor_property("automated", True)
        tasks.set_editor_property("save", True)
        # Use FBX factory options for static mesh
        opts = unreal.FbxImportUI()
        opts.set_editor_property("import_mesh", True)
        opts.set_editor_property("import_as_skeletal", False)
        opts.set_editor_property("import_materials", False)
        opts.set_editor_property("import_textures", False)
        opts.static_mesh_import_data.set_editor_property("build_reverb_correction", False)
        opts.static_mesh_import_data.set_editor_property("generate_lightmap_u_vs", True)
        opts.static_mesh_import_data.set_editor_property("auto_generate_collision", True)
        opts.static_mesh_import_data.set_editor_property("combine_meshes", True)
        tasks.set_editor_property("options", opts)
        unreal.AssetToolsHelpers.get_asset_tools().import_asset_tasks([tasks])
        print(f"  Reimported {name}")
        # Ensure collision enabled
        mesh = unreal.EditorAssetLibrary.load_asset(asset_path)
        if mesh:
            # Set collision trace to use complex as simple for polished bevel accuracy
            try:
                body = mesh.get_editor_property("body_setup")
                if body:
                    body.set_editor_property("collision_trace_flag", unreal.CollisionTraceFlag.CTF_USE_COMPLEX_AS_SIMPLE)
                    print(f"    Set CTF_UseComplexAsSimple on {name}")
            except Exception as e:
                print(f"    collision flag skip: {e}")
            unreal.EditorAssetLibrary.save_asset(asset_path)
    except Exception as e:
        print(f"  FAIL {name}: {e}")
        import traceback; traceback.print_exc()

print("REIMPORT DONE")
