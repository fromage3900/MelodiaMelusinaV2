"""
Apply sculpted normal maps to Choral Sheep 12 chromatic MIs.

Reads Saved/Audit/choral_sheep/sculpted_normals/normal_ingest_manifest.json
produced by Tools/Houdini/ingest_sheep_normals.py, imports textures (if not
already in Content) and assigns to MI_ChoralSheep_Coat_PC* Normal slots.

Run inside UE Editor Python:
    exec(open(r"C:/EnvironmentPortfolio/BS_GodFile/Content/Python/apply_choral_sheep_normals.py", encoding="utf-8").read())

Idempotent — rerun after you drop new sculpts keeps existing MIs.
"""
import json
from pathlib import Path
import unreal

INGEST_MANIFEST = Path(r"C:/EnvironmentPortfolio/BS_GodFile/Saved/Audit/choral_sheep/sculpted_normals/normal_ingest_manifest.json")
ALT_MANIFEST = Path(r"C:/EnvironmentPortfolio/BS_GodFile/Saved/Audit/choral_sheep/houdini_variants/normal_ingest_manifest.json")
UE_MATERIAL_DIR = "/Game/Melodia/Companions/ChoralSheep/Materials/"
UE_TEXTURE_DIR = "/Game/Melodia/Companions/ChoralSheep/Textures/"
LABELS = ["C","Cs","D","Ds","E","F","Fs","G","Gs","A","As","B"]

def _load_manifest():
    for p in (INGEST_MANIFEST, ALT_MANIFEST):
        if p.is_file():
            return json.loads(p.read_text(encoding="utf-8")), p
    raise FileNotFoundError(f"no manifest at {INGEST_MANIFEST} or {ALT_MANIFEST} — run ingest_sheep_normals.py first")

def _ensure_texture_import(src_png: Path, ue_name: str):
    # Use Interchange / AssetTools import if available; otherwise report
    dest_pkg = UE_TEXTURE_DIR + ue_name
    if unreal.EditorAssetLibrary.does_asset_exist(dest_pkg):
        print(f"[normals] texture exists: {dest_pkg}")
        return dest_pkg
    # try auto-import via AssetTools
    try:
        task = unreal.AssetImportTask()
        task.filename = str(src_png)
        task.destination_path = UE_TEXTURE_DIR.rstrip("/")
        task.destination_name = ue_name
        task.automated = True
        task.save = True
        task.replace_existing = False
        unreal.AssetToolsHelpers.get_asset_tools().import_asset_tasks([task])
        # configure as normal map
        tex = unreal.EditorAssetLibrary.load_asset(dest_pkg)
        if tex:
            try:
                tex.set_editor_property("compression_settings", unreal.TextureCompressionSettings.TC_NORMALMAP)
                tex.set_editor_property("srgb", False)
                unreal.EditorAssetLibrary.save_asset(dest_pkg)
            except Exception as e:
                print(f"[normals] warn normal settings: {e}")
        print(f"[normals] imported {src_png.name} -> {dest_pkg}")
        return dest_pkg
    except Exception as e:
        print(f"[normals] import failed for {src_png} -> {dest_pkg}: {e}")
        print(f"         manual import: drag {src_png} into Content Browser {UE_TEXTURE_DIR} and set Compression=Normalmap, sRGB=False")
        return None

def main():
    manifest, src = _load_manifest()
    print(f"[normals] manifest {src}: {json.dumps(manifest, indent=2)}")
    ar = unreal.AssetRegistryHelpers.get_asset_registry()
    # map label -> texture pkg
    label_to_tex = {}
    if manifest.get("shared"):
        src_png = Path(manifest["shared"])
        if src_png.is_file():
            tex_pkg = _ensure_texture_import(src_png, "T_ChoralSheep_Normal")
            for lab in LABELS:
                label_to_tex[lab] = tex_pkg
    for lab, tex_path in manifest.get("per_pc", {}).items():
        src_png = Path(tex_path)
        if src_png.is_file():
            tex_pkg = _ensure_texture_import(src_png, f"T_ChoralSheep_Normal_PC{lab}")
            label_to_tex[lab] = tex_pkg

    if not label_to_tex:
        print("[normals] no textures to wire — check manifest")
        return

    for lab in LABELS:
        mi_path = UE_MATERIAL_DIR + f"MI_ChoralSheep_Coat_PC{lab}"
        if not unreal.EditorAssetLibrary.does_asset_exist(mi_path):
            print(f"[normals] MI missing (create with generate): {mi_path}")
            continue
        tex_pkg = label_to_tex.get(lab)
        if not tex_pkg or not unreal.EditorAssetLibrary.does_asset_exist(tex_pkg):
            print(f"[normals] no texture for PC {lab}, skipping {mi_path}")
            continue
        mi = unreal.EditorAssetLibrary.load_asset(mi_path)
        tex = unreal.EditorAssetLibrary.load_asset(tex_pkg)
        try:
            # Material Instance: set Normal texture parameter (common name: Normal, NormalMap, NormalTexture)
            # Try common param names
            for param in ("Normal", "NormalMap", "NormalTexture", "Normal Map"):
                try:
                    unreal.MaterialEditingLibrary.set_material_instance_texture_parameter_value(mi, param, tex)
                    print(f"[normals] {mi_path} .{param} = {tex_pkg}")
                    break
                except Exception:
                    continue
            else:
                print(f"[normals] {mi_path}: no Normal param found — check M_Master_ChoralWool param name")
            unreal.EditorAssetLibrary.save_asset(mi_path)
        except Exception as e:
            print(f"[normals] failed {mi_path}: {e}")

    print("[normals] done — check Choral Sheep in viewport with normals. Re-run after new sculpts.")

if __name__ == "__main__":
    # when exec()-ed in Editor Python, run immediately
    try:
        main()
    except Exception as e:
        print(f"[normals] error: {e}")
        import traceback; traceback.print_exc()
