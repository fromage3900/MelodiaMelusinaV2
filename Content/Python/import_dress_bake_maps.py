import json
import os
import unreal

PROJECT_DIR = unreal.Paths.convert_relative_path_to_full(unreal.Paths.project_dir())
SRC = os.path.join(PROJECT_DIR, "Saved", "Audit", "melusina_lookdev", "bake")
DST = "/Game/Melodia/Characters/Melusina/Textures/Clothes"

MAPS = {
    "T_MelusinaC_DressShorewake_Normal_HB": ("T_DressShorewake_Normal.png", "normal"),
    "T_MelusinaC_DressShorewake_AO_HB": ("T_DressShorewake_AO.png", "mask"),
    "T_MelusinaC_DressShorewake_Curvature_HB": ("T_DressShorewake_Curvature.png", "mask"),
    "T_MelusinaC_DressShorewake_Thickness_HB": ("T_DressShorewake_Thickness.png", "mask"),
    "T_MelusinaC_DressShorewake_Position_HB": ("T_DressShorewake_Position.png", "color_data"),
}

LOD_BY_KIND = {
    "normal": unreal.TextureGroup.TEXTUREGROUP_CHARACTER_NORMAL_MAP,
    "mask": unreal.TextureGroup.TEXTUREGROUP_CHARACTER_SPECULAR,
    "color_data": unreal.TextureGroup.TEXTUREGROUP_CHARACTER_SPECULAR,
}

results = []
at = unreal.AssetToolsHelpers.get_asset_tools()
for name, (fname, kind) in MAPS.items():
    dst = "%s/%s" % (DST, name)
    if unreal.EditorAssetLibrary.does_asset_exist(dst):
        results.append({"name": name, "ok": True, "note": "already present"})
        continue
    src = os.path.join(SRC, fname)
    if not os.path.exists(src):
        results.append({"name": name, "ok": False, "error": "source missing"})
        continue
    task = unreal.AssetImportTask()
    task.filename = src
    task.destination_path = DST
    task.destination_name = name
    task.automated = True
    task.save = True
    task.options = None
    try:
        at.import_asset_tasks([task])
    except Exception as exc:  # noqa: BLE001
        results.append({"name": name, "ok": False, "error": str(exc)})
        continue
    if not unreal.EditorAssetLibrary.does_asset_exist(dst):
        results.append({"name": name, "ok": False, "error": "import/verify failed"})
        continue
    tex = unreal.EditorAssetLibrary.load_asset(dst)
    tex.set_editor_property("srgb", False)
    tex.set_editor_property("lod_group", LOD_BY_KIND[kind])
    if kind == "normal":
        tex.set_editor_property("compression_settings", unreal.TextureCompressionSettings.TC_NORMALMAP)
    elif kind == "mask":
        tex.set_editor_property("compression_settings", unreal.TextureCompressionSettings.TC_MASKS)
    else:
        tex.set_editor_property("compression_settings", unreal.TextureCompressionSettings.TC_DEFAULT)
    ok = unreal.EditorAssetLibrary.save_loaded_asset(tex, only_if_is_dirty=False)
    results.append({"name": name, "ok": bool(ok), "kind": kind})

print(json.dumps(results, indent=1))
