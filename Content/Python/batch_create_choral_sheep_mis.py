"""
Batch-create 12 MI_ChoralSheep_Coat_PC* instances from one master.

Run inside UE Editor Python AFTER the Houdini/blender PNGs are generated and
after the master material exists at:
    /Game/Melodia/Companions/ChoralSheep/M_Master_ChoralWool

Each MI sets:
  - BaseColor (or CoatBaseColor) param to pastel base
  - AccentEmissive to accent
  - Sheen / CoatWeight mapped from sheen
  - Normal map wired if T_ChoralSheep_Normal_PC* exists

Also drives houdini_variants PNGs as texture params if you want texture-backed coats.

Usage inside Editor:
    exec(open(r"C:/EnvironmentPortfolio/BS_GodFile/Content/Python/batch_create_choral_sheep_mis.py", encoding="utf-8").read())
"""
import colorsys
import json
from pathlib import Path
import unreal

MASTER_PATH = "/Game/Melodia/Companions/ChoralSheep/M_Master_ChoralWool"
MATERIAL_DIR = "/Game/Melodia/Companions/ChoralSheep/Materials/"
TEXTURE_DIR = "/Game/Melodia/Companions/ChoralSheep/Textures/"
HOUDINI_VARIANT_DIR = Path(r"C:/EnvironmentPortfolio/BS_GodFile/Saved/Audit/choral_sheep/houdini_variants")

PITCH_CLASS_HUES = {
    0:  ("C",  0.000), 1:  ("Cs", 0.083), 2:  ("D",  0.167), 3:  ("Ds", 0.250),
    4:  ("E",  0.333), 5:  ("F",  0.417), 6:  ("Fs", 0.500), 7:  ("G",  0.583),
    8:  ("Gs", 0.667), 9:  ("A",  0.750), 10: ("As", 0.833), 11: ("B",  0.917),
}
def _pastel_pair(hue, sat=0.38, val=0.92):
    base = colorsys.hsv_to_rgb(hue, sat * 0.55, val)
    accent = colorsys.hsv_to_rgb(hue, sat, min(1.0, val * 1.06))
    return base, accent

def main():
    master = unreal.EditorAssetLibrary.load_asset(MASTER_PATH)
    if not master:
        print(f"[batch] master not found: {MASTER_PATH}")
        print(f"       create a master at that path from M_Master_Toon or fur master, with params:")
        print(f"       CoatBaseColor (Vector), AccentColor (Vector), Sheen (Scalar), Normal (Texture)")
        print(f"       then re-run this script. For now, will still report chromatic values.")
        # still print values for manual work
        for pc,(label,hue) in PITCH_CLASS_HUES.items():
            base,accent = _pastel_pair(hue)
            sheen = 0.46 + pc/12*0.18
            print(f"  PC{pc:02d} {label}: base {[round(c,4) for c in base]} accent {[round(c,4) for c in accent]} sheen {sheen:.3f}")
        return

    # ensure dirs
    for pc,(label,hue) in PITCH_CLASS_HUES.items():
        base,accent = _pastel_pair(hue)
        sheen = 0.46 + pc/12*0.18
        base_lin = unreal.LinearColor(base[0], base[1], base[2], 1.0)
        accent_lin = unreal.LinearColor(accent[0], accent[1], accent[2], 1.0)
        mi_path = MATERIAL_DIR + f"MI_ChoralSheep_Coat_PC{label}"
        if unreal.EditorAssetLibrary.does_asset_exist(mi_path):
            mi = unreal.EditorAssetLibrary.load_asset(mi_path)
            print(f"[batch] exists {mi_path} — updating params")
        else:
            mi = unreal.AssetToolsHelpers.get_asset_tools().create_asset(
                f"MI_ChoralSheep_Coat_PC{label}",
                MATERIAL_DIR.rstrip("/"),
                unreal.MaterialInstanceConstant,
                unreal.MaterialInstanceConstantFactoryNew()
            )
            try:
                mi.set_editor_property("parent", master)
            except Exception:
                pass
            print(f"[batch] created {mi_path}")

        # try common param names — project may use CoatBaseColor / BaseColor / etc.
        for param, value in [
            ("CoatBaseColor", base_lin), ("BaseColor", base_lin), ("CoatColor", base_lin),
            ("AccentColor", accent_lin), ("TrimEmissive", accent_lin), ("BellColor", accent_lin),
        ]:
            try:
                unreal.MaterialEditingLibrary.set_material_instance_vector_parameter_value(mi, param, value)
            except Exception:
                pass
        for param, val in [("Sheen", sheen), ("SheenWeight", sheen), ("CoatWeight", 0.5), ("TrimEmissiveStrength", 1.2)]:
            try:
                unreal.MaterialEditingLibrary.set_material_instance_scalar_parameter_value(mi, param, val)
            except Exception:
                pass

        # wire Houdini texture if imported already
        tex_name = f"ChoralWool_PC_{label}"
        tex_path = TEXTURE_DIR + tex_name
        tex_png = HOUDINI_VARIANT_DIR / f"ChoralWool_PC_{label}.png"
        if unreal.EditorAssetLibrary.does_asset_exist(tex_path):
            tex = unreal.EditorAssetLibrary.load_asset(tex_path)
            for tparam in ("CoatTexture", "BaseTexture", "WoolTexture"):
                try:
                    unreal.MaterialEditingLibrary.set_material_instance_texture_parameter_value(mi, tparam, tex)
                    print(f"  -> wired {tex_path} to {tparam}")
                    break
                except Exception:
                    pass
        elif tex_png.is_file():
            print(f"  [batch] PNG ready but not yet imported: {tex_png} -> import to {tex_path} then re-run batch")

        # wire normal if present
        for npath in [TEXTURE_DIR + f"T_ChoralSheep_Normal_PC{label}", TEXTURE_DIR + "T_ChoralSheep_Normal"]:
            if unreal.EditorAssetLibrary.does_asset_exist(npath):
                ntex = unreal.EditorAssetLibrary.load_asset(npath)
                for nparam in ("Normal", "NormalMap", "NormalTexture"):
                    try:
                        unreal.MaterialEditingLibrary.set_material_instance_texture_parameter_value(mi, nparam, ntex)
                        break
                    except Exception:
                        pass
                break

        unreal.EditorAssetLibrary.save_asset(mi_path)

    print("[batch] done — 12 MIs at", MATERIAL_DIR)
    print("       Assign via DA_ChoralSheepDefinition variants or directly on SK_ChoralSheep slots for preview")

try:
    main()
except Exception as e:
    import traceback; traceback.print_exc(); print(f"[batch] error: {e}")
