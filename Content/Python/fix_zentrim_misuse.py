"""Fix ZenTrim misuse on 2 NikkiHero MIs.

MI_NikkiHero_SakuraDream:
  - BaseColor: ZenTrim_Base4K_BaseColor -> KB3D_ATL_BrickStoneCleanA_basecolor
  - Normal: T_Soil_Normal -> KB3D_ATL_BrickStoneCleanA_normal
  - Also set height/metallic/roughness params if present

MI_NikkiHero_SakuraDream_IntegratedV1:
  - Same but with BrickStoneCleanB variant
"""
import unreal

TEX_A = {
    "BaseColor": "/Game/EnvSandbox/Textures/Atlantis/KB3D_ATL_BrickStoneCleanA_basecolor",
    "Normal": "/Game/EnvSandbox/Textures/Atlantis/KB3D_ATL_BrickStoneCleanA_normal",
    "Roughness": "/Game/EnvSandbox/Textures/Atlantis/KB3D_ATL_BrickStoneCleanA_roughness",
    "Metallic": "/Game/EnvSandbox/Textures/Atlantis/KB3D_ATL_BrickStoneCleanA_metallic",
    "Height": "/Game/EnvSandbox/Textures/Atlantis/KB3D_ATL_BrickStoneCleanA_height",
}
TEX_B = {
    "BaseColor": "/Game/EnvSandbox/Textures/Atlantis/KB3D_ATL_BrickStoneCleanB_basecolor",
    "Normal": "/Game/EnvSandbox/Textures/Atlantis/KB3D_ATL_BrickStoneCleanB_normal",
    "Roughness": "/Game/EnvSandbox/Textures/Atlantis/KB3D_ATL_BrickStoneCleanB_roughness",
    "Metallic": "/Game/EnvSandbox/Textures/Atlantis/KB3D_ATL_BrickStoneCleanB_metallic",
    "Height": "/Game/EnvSandbox/Textures/Atlantis/KB3D_ATL_BrickStoneCleanB_height",
}

def fix_mi(mi_path, tex_map, label):
    mi = unreal.load_asset(mi_path)
    if mi is None:
        print(f"  FAIL: could not load {mi_path}")
        return False
    
    print(f"\n=== Fixing {label} ===")
    print(f"  Path: {mi_path}")
    
    # Show current texture params
    tparams = mi.texture_parameter_values
    print(f"  Current texture params ({len(tparams)}):")
    for i in range(len(tparams)):
        tp = tparams[i]
        pv = tp.parameter_value
        path = pv.get_path_name() if hasattr(pv, 'get_path_name') else str(pv)
        print(f"    [{i}] {path}")
    
    # Apply new textures
    for tex_name, tex_path in tex_map.items():
        tex_asset = unreal.load_asset(tex_path)
        if tex_asset is None:
            print(f"  WARN: could not load {tex_path}")
            continue
        result = unreal.MaterialEditingLibrary.set_material_instance_texture_parameter_value(mi, tex_name, tex_asset)
        print(f"  Set {tex_name}: {'OK' if result else 'FAIL'}")
    
    # Save
    unreal.EditorAssetLibrary.save_loaded_asset(mi)
    print(f"  Saved: OK")
    return True

fix_mi(
    "/Game/EnvSandbox/Materials/Instances/NikkiHero/MI_NikkiHero_SakuraDream",
    TEX_A,
    "MI_NikkiHero_SakuraDream"
)
fix_mi(
    "/Game/EnvSandbox/Materials/Instances/NikkiIntegrated/Mapped/MI_NikkiHero_SakuraDream_IntegratedV1",
    TEX_B,
    "MI_NikkiHero_SakuraDream_IntegratedV1"
)
print("\n=== Done ===")
