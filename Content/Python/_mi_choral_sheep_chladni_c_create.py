#!/usr/bin/env python3
"""
Create MI_ChoralSheep_Body_Chladni_C - C-root Chladni fleece consumer for hero proof.
Reuses existing MI_ChoralSheep_Body as parent, adds minimal Chladni params.
For first proof: C fixture locked, beat animates intensity only.

Run inside UE Editor Python:
    exec(open(r"C:/EnvironmentPortfolio/BS_GodFile/Content/Python/_mi_choral_sheep_chladni_c_create.py", encoding="utf-8").read())
"""
import unreal

MI_PATH = "/Game/Melodia/Companions/ChoralSheep/Materials/MI_ChoralSheep_Body_Chladni_C"
PARENT_MI_PATH = "/Game/Melodia/Companions/ChoralSheep/MI_ChoralSheep_Body"
TEXTURE_PATH = "/Game/Melodia/Companions/ChoralSheep/Textures/T_Chladni_C_ROOT"
# also accepts T_Chladni_C_Fixture.png if present

# Minimal params per hero spec - pearl/lilac hierarchy, subtle at low
# Beat animates intensity, not identity (ModeN/M locked to C)
CHLADNI_PARAMS_SCALAR = {
    "ChladniIntensity": 0.0,          # 0 at REST, 0.65 hero readable
    "HarmonizeActive": 0.0,           # 0/1 gate from TryBeginHarmonize
    "BeatAccent": 0.0,                # driven by BeatPulse/Cymatic_BeatPulse
    "ChladniEmissiveStrength": 0.5,
    "ChladniSheenStrength": 0.5,
    "Cymatic_ModeN": 2.0,             # C fixture locked
    "Cymatic_ModeM": 3.0,             # C fixture locked
}
CHLADNI_PARAMS_VECTOR = {
    # Pearl silk / lilac halo per visual authority
    "ChladniPearlSilkColor": unreal.LinearColor(0.96, 0.91, 0.96, 1.0),
    "ChladniLilacHaloColor": unreal.LinearColor(0.58, 0.40, 0.72, 1.0),
}
CHLADNI_PARAMS_TEXTURE = {
    "ChladniPatternTexture": TEXTURE_PATH,
}

def create_chladni_c_mi():
    # Load parent
    parent = unreal.EditorAssetLibrary.load_asset(PARENT_MI_PATH)
    if not parent:
        print(f"[chladni_c] ERROR: Parent not found: {PARENT_MI_PATH}")
        return None
    print(f"[chladni_c] Parent: {parent.get_path_name()}")

    # Check existing
    if unreal.EditorAssetLibrary.does_asset_exist(MI_PATH):
        mi = unreal.EditorAssetLibrary.load_asset(MI_PATH)
        print(f"[chladni_c] MI already exists: {MI_PATH} - updating params")
    else:
        asset_tools = unreal.AssetToolsHelpers.get_asset_tools()
        mi_name = "MI_ChoralSheep_Body_Chladni_C"
        mi_dir = "/Game/Melodia/Companions/ChoralSheep/Materials"
        if not unreal.EditorAssetLibrary.does_directory_exist(mi_dir):
            unreal.EditorAssetLibrary.make_directory(mi_dir)
        mi = asset_tools.create_asset(mi_name, mi_dir, unreal.MaterialInstanceConstant, unreal.MaterialInstanceConstantFactoryNew())
        if not mi:
            print("[chladni_c] ERROR: Failed to create MI")
            return None
        print(f"[chladni_c] Created: {MI_PATH}")

    # Set parent to existing sheep body (inherits toon + base)
    try:
        mi.set_editor_property("parent", parent)
        print(f"[chladni_c] Set parent to {PARENT_MI_PATH}")
    except Exception as e:
        print(f"[chladni_c] WARNING parent set failed: {e}")

    # Scalars
    for k, v in CHLADNI_PARAMS_SCALAR.items():
        try:
            unreal.MaterialEditingLibrary.set_material_instance_scalar_parameter_value(mi, k, v)
            print(f"[chladni_c] scalar {k}={v}")
        except Exception as e:
            print(f"[chladni_c] WARNING scalar {k}: {e}")

    # Vectors
    for k, v in CHLADNI_PARAMS_VECTOR.items():
        try:
            unreal.MaterialEditingLibrary.set_material_instance_vector_parameter_value(mi, k, v)
            print(f"[chladni_c] vector {k}={v}")
        except Exception as e:
            print(f"[chladni_c] WARNING vector {k}: {e}")

    # Texture
    for k, tex_path in CHLADNI_PARAMS_TEXTURE.items():
        try:
            tex = unreal.EditorAssetLibrary.load_asset(tex_path)
            if not tex:
                # try alternative fixture
                alt = "/Game/Melodia/Companions/ChoralSheep/Textures/T_Chladni_C_Fixture"
                tex = unreal.EditorAssetLibrary.load_asset(alt)
                if tex:
                    tex_path = alt
                    print(f"[chladni_c] using alt texture {alt}")
                else:
                    print(f"[chladni_c] WARNING texture not found: {tex_path}")
                    continue
            unreal.MaterialEditingLibrary.set_material_instance_texture_parameter_value(mi, k, tex)
            print(f"[chladni_c] texture {k}={tex_path}")
        except Exception as e:
            print(f"[chladni_c] WARNING texture {k}: {e}")

    # Save
    try:
        unreal.EditorAssetLibrary.save_loaded_asset(mi)
        print(f"[chladni_c] Saved: {MI_PATH}")
    except Exception as e:
        print(f"[chladni_c] WARNING save failed: {e}")

    return mi

def main():
    print("="*60)
    print("Creating MI_ChoralSheep_Body_Chladni_C (C-root fixture)")
    print("="*60)
    mi = create_chladni_c_mi()
    if mi:
        print(f"\n[SUCCESS] {MI_PATH}")
        print("Params: ChladniIntensity 0, HarmonizeActive 0, BeatAccent 0, ModeN 2 ModeM 3 locked")
        print("Visual: pearl/lilac embroidery, subtle at low, readable at hero, beat = intensity pulse")
    else:
        print("\n[FAILED]")
    return mi

if __name__ == "__main__":
    main()
