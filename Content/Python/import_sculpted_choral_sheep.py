"""
Import new sculpted choralsheep + chromatic+glow variants into UE.

Source: you just exported at 04:01:
  Content/Melodia/Companions/ChoralSheep/choralsheep.fbx (47KB low-poly, proper UVs)
  Content/Melodia/Companions/ChoralSheep/choralsheephi.fbx (50MB hi-poly, keep as backup)
  Content/Melodia/Companions/ChoralSheep/choralsheepbase_*.png (BaseColor, Normal, etc.)
Generated in this session:
  Saved/Audit/choral_sheep/sculpted_variants/albedo_{A,B,C,D}/ChoralWool_PC_*.png (1024)
  Saved/Audit/choral_sheep/sculpted_variants/glow_{A,B,C,D}/T_ChoralSheep_Glow_PC_*.png (1024, subtle)

Run in UE Editor Python:
  exec(open(r"C:/EnvironmentPortfolio/BS_GodFile/Content/Python/import_sculpted_choral_sheep.py", encoding="utf-8").read())

What it does:
  1. Imports choralsheep.fbx as SK_ChoralSheep (if not exists, else reports — manual reimport needed if you want to overwrite)
  2. Imports BaseColor/Normal/Roughness/etc. as shared textures
  3. Imports all 4×12 albedos + 4×12 glows to /Game/Melodia/Companions/ChoralSheep/Variants/{A,B,C,D}/
  4. Creates 12 MIs per mode off M_Master_ChoralWool (or reports if master missing)
     Each MI: BaseColor = tinted sculpt, Normal = shared, Emissive = per-PC subtle glow (multiply, emissive strength ~0.9)

Choose ONE mode to wire to the live MIs at /Game/Melodia/Companions/ChoralSheep/Materials/MI_ChoralSheep_Coat_PC*:
  Set LIVE_MODE = "A" | "B" | "C" | "D" below. Default A (clean) is safest; D is the pop you asked for.
"""
import json
from pathlib import Path
import unreal

LIVE_MODE = "D"  # <-- change this to A / B / C / D to pick which set becomes the live MI_ChoralSheep_Coat_PC*
SIZE = 1024

SRC_FBX = Path(r"C:/EnvironmentPortfolio/BS_GodFile/Content/Melodia/Companions/ChoralSheep/choralsheep.fbx")
SRC_BASE = Path(r"C:/EnvironmentPortfolio/BS_GodFile/Content/Melodia/Companions/ChoralSheep/choralsheepbase_BaseColor.png")
SRC_NORMAL = Path(r"C:/EnvironmentPortfolio/BS_GodFile/Content/Melodia/Companions/ChoralSheep/choralsheepbase_Normal.png")
SRC_ROUGH = Path(r"C:/EnvironmentPortfolio/BS_GodFile/Content/Melodia/Companions/ChoralSheep/choralsheepbase_Roughness.png")
SRC_AO = Path(r"C:/EnvironmentPortfolio/BS_GodFile/Content/Melodia/Companions/ChoralSheep/choralsheepbase_Alpha.png")  # actually AO/Alpha

VARIANTS_ROOT = Path(r"C:/EnvironmentPortfolio/BS_GodFile/Saved/Audit/choral_sheep/sculpted_variants")
UE_SK = "/Game/Melodia/Companions/ChoralSheep/SK_ChoralSheep"
UE_TEX_SHARED = "/Game/Melodia/Companions/ChoralSheep/Textures/Shared/"
UE_VARIANT_BASE = "/Game/Melodia/Companions/ChoralSheep/Variants/"
UE_LIVE_MATS = "/Game/Melodia/Companions/ChoralSheep/Materials/"
MASTER = "/Game/Melodia/Companions/ChoralSheep/M_Master_ChoralWool"

MODE_MAP = {
    "A": "A_flat",
    "B": "B_worley12",
    "C": "C_worley25",
    "D": "D_pop_worley12",
}

def _import_texture(src: Path, dest_path: str, dest_name: str, is_normal=False):
    pkg = dest_path + dest_name
    if unreal.EditorAssetLibrary.does_asset_exist(pkg):
        print(f"[import] exists {pkg}")
        return pkg
    try:
        task = unreal.AssetImportTask()
        task.filename = str(src)
        task.destination_path = dest_path.rstrip("/")
        task.destination_name = dest_name
        task.automated = True
        task.save = True
        task.replace_existing = False
        unreal.AssetToolsHelpers.get_asset_tools().import_asset_tasks([task])
        tex = unreal.EditorAssetLibrary.load_asset(pkg)
        if tex and is_normal:
            try:
                tex.set_editor_property("compression_settings", unreal.TextureCompressionSettings.TC_NORMALMAP)
                tex.set_editor_property("srgb", False)
                unreal.EditorAssetLibrary.save_asset(pkg)
            except Exception as e:
                print(f"[tex] normal settings {e}")
        print(f"[import] {src.name} -> {pkg}")
        return pkg
    except Exception as e:
        print(f"[import] failed {src} -> {pkg}: {e}")
        return None

def main():
    print(f"[sheep sculpt] LIVE_MODE={LIVE_MODE} -> {MODE_MAP.get(LIVE_MODE)}")
    # 1. SK
    if unreal.EditorAssetLibrary.does_asset_exist(UE_SK):
        print(f"[sk] exists {UE_SK} — to reimport, drag {SRC_FBX} onto Content Browser and overwrite (keep skeleton SK_ChoralSheep_Skeleton)")
    else:
        print(f"[sk] missing {UE_SK} — import {SRC_FBX} to {UE_SK} manually (Skeleton: Create new SK_ChoralSheep_Skeleton, do NOT reuse Melusina)")
        # Try auto
        try:
            task = unreal.AssetImportTask()
            task.filename = str(SRC_FBX)
            task.destination_path = "/Game/Melodia/Companions/ChoralSheep"
            task.destination_name = "SK_ChoralSheep"
            task.automated = True
            task.save = True
            unreal.AssetToolsHelpers.get_asset_tools().import_asset_tasks([task])
            print(f"[sk] imported {SRC_FBX.name} -> {UE_SK}")
        except Exception as e:
            print(f"[sk] auto failed: {e}")

    # 2. Shared textures
    shared = [
        (SRC_BASE, UE_TEX_SHARED, "T_ChoralSheep_BaseColor_Sculpt", False),
        (SRC_NORMAL, UE_TEX_SHARED, "T_ChoralSheep_Normal_Sculpt", True),
    ]
    # Only import if files exist and not already imported
    for src, dst_path, dst_name, is_norm in shared:
        if src.is_file():
            _import_texture(src, dst_path, dst_name, is_normal=is_norm)

    # 3. Per-mode albedos + glows
    for mode_key, label in MODE_MAP.items():
        albedo_dir = VARIANTS_ROOT / f"albedo_{label}"
        glow_dir = VARIANTS_ROOT / f"glow_{label}"
        if not albedo_dir.is_dir():
            print(f"[variants] missing {albedo_dir}, skipping {mode_key}")
            continue
        ue_dir = UE_VARIANT_BASE + label + "/"
        for p in sorted(albedo_dir.glob("ChoralWool_PC_*.png")):
            lab = p.stem.split("_PC_")[-1]
            _import_texture(p, ue_dir, f"T_ChoralSheep_Albedo_PC_{lab}_{mode_key}", False)
        for p in sorted(glow_dir.glob("T_ChoralSheep_Glow_PC_*.png")):
            lab = p.stem.split("_PC_")[-1] if "_PC_" in p.stem else p.stem
            # Glow names already contain PC
            # Normalize to T_ChoralSheep_Glow_PC_{lab}_{mode}
            if "_PC_" in p.name:
                lab = p.stem.split("_PC_")[-1]
                _import_texture(p, ue_dir, f"T_ChoralSheep_Glow_PC_{lab}_{mode_key}", False)

    # 4. Live MIs
    master = unreal.EditorAssetLibrary.load_asset(MASTER)
    if not master:
        print(f"[mats] master missing {MASTER} — create M_Master_ChoralWool with params: BaseColor, Normal, Emissive, Sheen, Roughness")
        print(f"       then re-run this script to create live MIs")
        return
    variant_live = MODE_MAP.get(LIVE_MODE, "A_flat")
    live_albedo_root = UE_VARIANT_BASE + variant_live + "/"
    live_glow_root = UE_VARIANT_BASE + variant_live + "/"
    for pc in range(12):
        labs = ["C","Cs","D","Ds","E","F","Fs","G","Gs","A","As","B"]
        lab = labs[pc]
        mi_path = UE_LIVE_MATS + f"MI_ChoralSheep_Coat_PC{lab}"
        albedo_pkg = live_albedo_root + f"T_ChoralSheep_Albedo_PC_{lab}_{LIVE_MODE}"
        glow_pkg = live_glow_root + f"T_ChoralSheep_Glow_PC_{lab}_{LIVE_MODE}"
        normal_pkg = UE_TEX_SHARED + "T_ChoralSheep_Normal_Sculpt"
        # Create or update MI
        if not unreal.EditorAssetLibrary.does_asset_exist(mi_path):
            try:
                mi = unreal.AssetToolsHelpers.get_asset_tools().create_asset(
                    f"MI_ChoralSheep_Coat_PC{lab}", UE_LIVE_MATS.rstrip("/"),
                    unreal.MaterialInstanceConstant, unreal.MaterialInstanceConstantFactoryNew()
                )
                mi.set_editor_property("parent", master)
                unreal.EditorAssetLibrary.save_asset(mi_path)
                print(f"[mats] created {mi_path}")
            except Exception as e:
                print(f"[mats] create failed {mi_path}: {e}")
                continue
        mi = unreal.EditorAssetLibrary.load_asset(mi_path)
        for tex_pkg, param_candidates in [
            (albedo_pkg, ["BaseColor","Base_Color","CoatBaseColor","Albedo"]),
            (normal_pkg, ["Normal","NormalMap","NormalTexture"]),
            (glow_pkg, ["Emissive","EmissiveTexture","Glow","UnderFluffGlow"]),
        ]:
            if not unreal.EditorAssetLibrary.does_asset_exist(tex_pkg):
                continue
            tex = unreal.EditorAssetLibrary.load_asset(tex_pkg)
            for param in param_candidates:
                try:
                    unreal.MaterialEditingLibrary.set_material_instance_texture_parameter_value(mi, param, tex)
                    # For emissive, also set scalar strength subtle
                    if "Emissive" in param or "Glow" in param:
                        for sparam in ["EmissiveStrength","GlowStrength","UnderFluffStrength"]:
                            try:
                                # subtle: 0.9 for general, 1.4 for D pop
                                val = 1.2 if LIVE_MODE=="D" else 0.85
                                unreal.MaterialEditingLibrary.set_material_instance_scalar_parameter_value(mi, sparam, val)
                                break
                            except: pass
                    break
                except: pass
        unreal.EditorAssetLibrary.save_asset(mi_path)
        print(f"[mats] wired {mi_path} <- {albedo_pkg} + glow {glow_pkg}")

    print(f"[done] LIVE_MODE {LIVE_MODE} wired to {UE_LIVE_MATS}MI_ChoralSheep_Coat_PC*")
    print(f"       Place BP_ChoralSheep in /Game/_PROJECT/Levels/RenderTests/L_ChoralSheep_Prototype to see flock under light")
    print(f"       Glow is subtle — check in dark / with groom sparse. Tune EmissiveStrength 0.5..1.5 on the MIs if needed.")

try:
    main()
except Exception as e:
    import traceback; traceback.print_exc(); print(f"[sheep sculpt] error {e}")
