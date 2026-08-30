import json
import os
import unreal

PROJECT_DIR = unreal.Paths.convert_relative_path_to_full(unreal.Paths.project_dir())
MANIFEST_PATH = os.path.join(PROJECT_DIR, "Saved", "Audit", "sea_above", "houdini_variants",
                             "reef_texture_ingest_manifest.json")
BASE = "/Game/EnvSandbox/Monoliths/SeaAbove/Prototype/Reef/Textures/"
LOD_BY_KIND = {
    "TEXTUREGROUP_Effects": unreal.TextureGroup.TEXTUREGROUP_EFFECTS,
    "TEXTUREGROUP_World": unreal.TextureGroup.TEXTUREGROUP_WORLD,
    "TEXTUREGROUP_WorldNormalMap": unreal.TextureGroup.TEXTUREGROUP_WORLD_NORMAL_MAP,
}
NO_ALPHA = set()  # manifest may or may not carry alpha flags; report only

with open(MANIFEST_PATH, "r", encoding="utf-8") as fh:
    manifest = json.load(fh)

fixed, mismatches = [], []
for entry in manifest["files"]:
    name = entry["name"]
    tex = unreal.EditorAssetLibrary.load_asset(BASE + name)
    if tex is None:
        mismatches.append({"name": name, "error": "asset missing"})
        continue
    want_srgb = bool(entry["import"]["sRGB"])
    want_lod = LOD_BY_KIND.get(entry["import"]["lod_group"])
    got_srgb = tex.get_editor_property("srgb")
    got_lod = tex.get_editor_property("lod_group")
    if got_srgb != want_srgb or (want_lod is not None and got_lod != want_lod):
        tex.set_editor_property("srgb", want_srgb)
        if want_lod is not None:
            tex.set_editor_property("lod_group", want_lod)
        if entry.get("mode") == "L" and "Normal" not in name:
            tex.set_editor_property("compression_settings",
                                    unreal.TextureCompressionSettings.TC_MASKS)
        ok = unreal.EditorAssetLibrary.save_loaded_asset(tex, only_if_is_dirty=False)
        fixed.append({"name": name, "was": [str(got_srgb), str(got_lod)], "saved": bool(ok)})

print("FIXED_COUNT", len(fixed))
for f in fixed:
    print("FIXED", f["name"], f["was"])
print("MISMATCH_ERRORS", mismatches if mismatches else "none")
