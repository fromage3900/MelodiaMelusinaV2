
import unreal

def fix_param(mi_path, param_name, tex_path, label):
    mi = unreal.load_asset(mi_path)
    tex = unreal.load_asset(tex_path)
    if not mi or not tex:
        print(f"  FAIL: load error ({'mi' if not mi else 'tex'})")
        return False

    # Current value
    cur_path = None
    for i in range(len(mi.texture_parameter_values)):
        tp = mi.texture_parameter_values[i]
        info = tp.parameter_info
        if info and info.name == param_name:
            pv = tp.parameter_value
            cur_path = pv.get_path_name() if hasattr(pv, 'get_path_name') else '?'
            break

    print(f"  {param_name}: {cur_path} → {tex_path}", end=" ... ")

    # Approach 1: setattr
    ok = False
    try:
        setattr(mi, param_name, tex)
        chk = getattr(mi, param_name, None)
        if chk and hasattr(chk, 'get_path_name'):
            if chk.get_path_name() == tex_path:
                ok = True
    except Exception as e:
        print(f"setattr-error-{e}", end=" ... ")

    # Approach 2: MEL
    if not ok:
        try:
            r = unreal.MaterialEditingLibrary.set_material_instance_texture_parameter_value(mi, param_name, tex)
            if r:
                ok = True
        except Exception as e:
            print(f"MEL-err-{e}", end=" ... ")

    # Approach 3: override
    if not ok:
        try:
            r = unreal.MaterialEditingLibrary.set_material_instance_parameter_override(mi, param_name, tex)
            if r:
                ok = True
        except Exception as e:
            print(f"override-err-{e}", end=" ... ")

    saved = unreal.EditorAssetLibrary.save_loaded_asset(mi)
    print(f"→ {'OK' if ok else 'FAIL'} (save {'OK' if saved else 'FAIL'})")
    return ok

def verify(mi_path, label):
    print(f"\n  --- {label} ---")
    mi = unreal.load_asset(mi_path)
    if not mi:
        print("  FAIL: reload"); return
    for i in range(len(mi.texture_parameter_values)):
        tp = mi.texture_parameter_values[i]
        info = tp.parameter_info
        pv = tp.parameter_value
        nm = info.name if info else f"p{i}"
        path = pv.get_path_name() if hasattr(pv, 'get_path_name') else '?'
        print(f"    {nm}: {path}")

print("=" * 55)
print("ZEN TRIM MISUSE FIX")
print("=" * 55)

fix_param("/Game/EnvSandbox/Materials/Instances/NikkiHero/MI_NikkiHero_SakuraDream",
          "Albedo", "/Game/EnvSandbox/Textures/Atlantis/KB3D_ATL_BrickStoneCleanA_basecolor",
          "SakuraDream > Albedo")
fix_param("/Game/EnvSandbox/Materials/Instances/NikkiHero/MI_NikkiHero_SakuraDream",
          "NormalMap", "/Game/EnvSandbox/Textures/Atlantis/KB3D_ATL_BrickStoneCleanA_normal",
          "SakuraDream > NormalMap")

fix_param("/Game/EnvSandbox/Materials/Instances/NikkiIntegrated/Mapped/MI_NikkiHero_SakuraDream_IntegratedV1",
          "Albedo", "/Game/EnvSandbox/Textures/Atlantis/KB3D_ATL_BrickStoneCleanB_basecolor",
          "SakuraDream_IntegratedV1 > Albedo")
fix_param("/Game/EnvSandbox/Materials/Instances/NikkiIntegrated/Mapped/MI_NikkiHero_SakuraDream_IntegratedV1",
          "NormalMap", "/Game/EnvSandbox/Textures/Atlantis/KB3D_ATL_BrickStoneCleanB_normal",
          "SakuraDream_IntegratedV1 > NormalMap")

print("\n" + "=" * 55)
print("VERIFICATION (reloaded from disk)")
print("=" * 55)
verify("/Game/EnvSandbox/Materials/Instances/NikkiHero/MI_NikkiHero_SakuraDream", "MI_NikkiHero_SakuraDream")
verify("/Game/EnvSandbox/Materials/Instances/NikkiIntegrated/Mapped/MI_NikkiHero_SakuraDream_IntegratedV1", "MI_NikkiHero_SakuraDream_IntegratedV1")
print("\nDone.")
