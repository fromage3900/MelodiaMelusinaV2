"""Verify current ZenTrim misuse MI state, then fix properly via direct attribute access."""
import unreal

def check_mi(mi_path, label):
    mi = unreal.load_asset(mi_path)
    print(f"\n=== {label} ===")
    print(f"  Path: {mi_path}")
    if not mi:
        print("  FAIL: not loaded")
        return
    
    # Show all texture params
    print("  Texture params:")
    for i in range(len(mi.texture_parameter_values)):
        tp = mi.texture_parameter_values[i]
        info = tp.parameter_info
        pv = tp.parameter_value
        name = info.name if info else f"p{i}"
        path = pv.get_path_name() if hasattr(pv, 'get_path_name') else '?'
        print(f"    {name}: {path}")
    
    # Show scalar
    print("  Scalar params:")
    for i in range(len(mi.scalar_parameter_values)):
        sp = mi.scalar_parameter_values[i]
        info = sp.parameter_info
        name = info.name if info else f"s{i}"
        print(f"    {name}: {sp.value}")
    
    # Show vector
    print("  Vector params:")
    for i in range(len(mi.vector_parameter_values)):
        vp = mi.vector_parameter_values[i]
        info = vp.parameter_info
        name = info.name if info else f"v{i}"
        print(f"    {name}: {vp.value}")

# Check both MIs
check_mi("/Game/EnvSandbox/Materials/Instances/NikkiHero/MI_NikkiHero_SakuraDream", "SakuraDream (BEFORE)")
check_mi("/Game/EnvSandbox/Materials/Instances/NikkiIntegrated/Mapped/MI_NikkiHero_SakuraDream_IntegratedV1", "SakuraDream_IntegratedV1 (BEFORE)")

print("\n" + "=" * 60)
print("FIXING ZENTRIM MISUSE VIA DIRECT ATTRIBUTE ACCESS")
print("=" * 60)

# KB3D_ATL texture paths
TEX_A = {
    "BaseColor": "/Game/EnvSandbox/Textures/Atlantis/KB3D_ATL_BrickStoneCleanA_basecolor",
    "NormalMap": "/Game/EnvSandbox/Textures/Atlantis/KB3D_ATL_BrickStoneCleanA_normal",
    "RoughnessMap": "/Game/EnvSandbox/Textures/Atlantis/KB3D_ATL_BrickStoneCleanA_roughness",
    "MetallicMap": "/Game/EnvSandbox/Textures/Atlantis/KB3D_ATL_BrickStoneCleanA_metallic",
    "HeightMap": "/Game/EnvSandbox/Textures/Atlantis/KB3D_ATL_BrickStoneCleanA_height",
}
TEX_B = {
    "BaseColor": "/Game/EnvSandbox/Textures/Atlantis/KB3D_ATL_BrickStoneCleanB_basecolor",
    "NormalMap": "/Game/EnvSandbox/Textures/Atlantis/KB3D_ATL_BrickStoneCleanB_normal",
    "RoughnessMap": "/Game/EnvSandbox/Textures/Atlantis/KB3D_ATL_BrickStoneCleanB_roughness",
    "MetallicMap": "/Game/EnvSandbox/Textures/Atlantis/KB3D_ATL_BrickStoneCleanB_metallic",
    "HeightMap": "/Game/EnvSandbox/Textures/Atlantis/KB3D_ATL_BrickStoneCleanB_height",
}

def fix_mi(mi_path, tex_map, label):
    mi = unreal.load_asset(mi_path)
    if not mi:
        print(f"\n{label}: FAIL - not loaded")
        return False
    
    print(f"\n{label}:")
    # Show which params need changing
    for param_name, tex_path in tex_map.items():
        tex = unreal.load_asset(tex_path)
        if not tex:
            print(f"  {param_name}: texture not found at {tex_path}")
            continue
        
        old_val = getattr(mi, param_name, None)
        try:
            setattr(mi, param_name, tex.get_path_name())
            new_val = getattr(mi, param_name, None)
            ok = (new_val == tex.get_path_name())
            print(f"  {param_name}: {old_val} → {new_val} [{'OK' if ok else 'CHECK'}]")
        except Exception as e:
            print(f"  {param_name}: FAIL - {e}")
    
    # Save
    saved = unreal.EditorAssetLibrary.save_loaded_asset(mi)
    print(f"  Save: {'OK' if saved else 'FAIL'}")
    return True

fix_mi("/Game/EnvSandbox/Materials/Instances/NikkiHero/MI_NikkiHero_SakuraDream", TEX_A, "SakuraDream → KB3D_ATL_BrickStoneCleanA")
fix_mi("/Game/EnvSandbox/Materials/Instances/NikkiIntegrated/Mapped/MI_NikkiHero_SakuraDream_IntegratedV1", TEX_B, "SakuraDream_IntegratedV1 → KB3D_ATL_BrickStoneCleanB")

print("\n" + "=" * 60)
print("VERIFICATION (reloaded from disk)")
print("=" * 60)

check_mi("/Game/EnvSandbox/Materials/Instances/NikkiHero/MI_NikkiHero_SakuraDream", "SakuraDream (AFTER)")
check_mi("/Game/EnvSandbox/Materials/Instances/NikkiIntegrated/Mapped/MI_NikkiHero_SakuraDream_IntegratedV1", "SakuraDream_IntegratedV1 (AFTER)")

print("\nDone.")
