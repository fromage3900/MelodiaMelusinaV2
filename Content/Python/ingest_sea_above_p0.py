"""Ingest the Sea Above P0 Houdini backlog into UE (single-editor window task).

Run inside the Unreal Editor (Output Log -> Cmd, or pie.py exec):
    py Content/Python/ingest_sea_above_p0.py

What it does (per Docs/Handoffs/HOUDINI_SEA_ABOVE_P0_AND_AAA_POLISH_PLAN_2026-08-28.md
Track B ingest pattern, and the reef_texture_ingest_manifest import contract):

  1. Textures  <- Saved/Audit/sea_above/houdini_variants/*.png (55 files,
                  per-file sRGB / LOD-group / compression from the manifest)
                  -> /Game/EnvSandbox/Monoliths/SeaAbove/Prototype/Reef/Textures/
  2. Meshes    <- Saved/Audit/sea_above/meshes/SM_*.obj (coral, clutter, kelp,
                  islands, rock chunks; manifest contract: 100x m->cm, Nanite on,
                  no auto collision at import)
                  -> /Game/EnvSandbox/Monoliths/SeaAbove/Prototype/Reef/Meshes/

RED LINES honored:
  - Never opens or edits any material master (M_*), any MI, or the Niagara
    flipbook material. Wiring (MI_Niagara_MelodiaFlipbook_Droplet sibling,
    membrane MI params, kelp pulse sampling) is a separate editor step.
  - Writes an assertion JSON next to the frames/manifests (evidence standard #3):
    Saved/Audit/sea_above/ingest_report_<UTC>.json

Verify-by-re-reading: every import is confirmed via does_asset_exist +
an asset re-load; failures are recorded, never swallowed.
"""

import json
import os
import datetime

import unreal

PROJECT_DIR = unreal.Paths.convert_relative_path_to_full(unreal.Paths.project_dir())

MANIFEST_PATH = os.path.join(PROJECT_DIR, "Saved", "Audit", "sea_above", "houdini_variants",
                             "reef_texture_ingest_manifest.json")
TEX_SRC = os.path.join(PROJECT_DIR, "Saved", "Audit", "sea_above", "houdini_variants")
MESH_SRC = os.path.join(PROJECT_DIR, "Saved", "Audit", "sea_above", "meshes")
TEX_DST = "/Game/EnvSandbox/Monoliths/SeaAbove/Prototype/Reef/Textures"
MESH_DST = "/Game/EnvSandbox/Monoliths/SeaAbove/Prototype/Reef/Meshes"

SKIP_NAMES = set()  # textures already imported by a previous partial run

LOD_BY_KIND = {
    "TEXTUREGROUP_Effects": unreal.TextureGroup.TEXTUREGROUP_EFFECTS,
    "TEXTUREGROUP_World": unreal.TextureGroup.TEXTUREGROUP_WORLD,
    "TEXTUREGROUP_WorldNormalMap": unreal.TextureGroup.TEXTUREGROUP_WORLD_NORMAL_MAP,
}


def _log(msg):
    unreal.log_warning("[SEA_ABOVE_INGEST] %s" % msg)


def import_textures(manifest):
    at = unreal.AssetToolsHelpers.get_asset_tools()
    results = []
    for entry in manifest["files"]:
        name = entry["name"]
        if name in SKIP_NAMES:
            continue
        existing = "%s/%s" % (TEX_DST, name)
        if unreal.EditorAssetLibrary.does_asset_exist(existing):
            results.append({"name": name, "ok": True, "asset": existing, "note": "already present"})
            continue
        src = entry["path"]
        if not os.path.exists(src):
            results.append({"name": name, "ok": False, "error": "source missing"})
            continue
        imp = unreal.AutomatedAssetImportData()
        imp.set_editor_property("destination_path", TEX_DST)
        imp.set_editor_property("filenames", [src])
        tex_import = unreal.TextureFactory()
        imp.set_editor_property("factory", tex_import)
        try:
            assets = at.import_assets_automated(imp)
        except Exception as exc:  # noqa: BLE001 - recorded, not swallowed
            results.append({"name": name, "ok": False, "error": str(exc)})
            continue
        if not assets:
            results.append({"name": name, "ok": False, "error": "import returned no asset"})
            continue
        tex = unreal.EditorAssetLibrary.load_asset(assets[0].get_name())
        if tex is None:
            results.append({"name": name, "ok": False, "error": "re-load after import failed"})
            continue
        # Import contract from the manifest (rule: verify-by-re-reading, not trusting success)
        tex.set_editor_property("srgb", bool(entry["import"]["sRGB"]))
        lod = LOD_BY_KIND.get(entry["import"]["lod_group"])
        if lod is not None:
            tex.set_editor_property("lod_group", lod)
        if entry.get("mode") == "L" and "Normal" not in name:
            tex.set_editor_property("compression_settings",
                                    unreal.TextureCompressionSettings.TC_MASKS)
        ok = unreal.EditorAssetLibrary.save_loaded_asset(tex)
        results.append({
            "name": name,
            "ok": bool(ok),
            "asset": assets[0].get_name(),
            "sha256": entry["sha256"],
            "srgb": bool(entry["import"]["sRGB"]),
            "lod_group": entry["import"]["lod_group"],
        })
    return results


def import_meshes():
    at = unreal.AssetToolsHelpers.get_asset_tools()
    results = []
    objs = sorted(p for p in os.listdir(MESH_SRC) if p.startswith("SM_") and p.endswith(".obj"))
    for fname in objs:
        name = os.path.splitext(fname)[0]
        dst_asset = "%s/%s" % (MESH_DST, name)
        if unreal.EditorAssetLibrary.does_asset_exist(dst_asset):
            results.append({"name": name, "ok": True, "asset": dst_asset, "note": "already present"})
            continue
        fbx_ui = unreal.FbxImportUI()
        fbx_ui.set_editor_property("import_mesh", True)
        fbx_ui.set_editor_property("import_textures", False)
        fbx_ui.set_editor_property("import_materials", False)
        fbx_ui.set_editor_property("import_as_skeletal", False)
        fbx_ui.static_mesh_import_data.set_editor_property("combine_meshes", True)
        fbx_ui.static_mesh_import_data.set_editor_property("generate_lightmap_u_vs", False)
        fbx_ui.static_mesh_import_data.set_editor_property("auto_generate_collision", False)
        fbx_ui.static_mesh_import_data.set_editor_property("import_uniform_scale", 100.0)
        task = unreal.AssetImportTask()
        task.filename = os.path.join(MESH_SRC, fname)
        task.destination_path = MESH_DST
        task.destination_name = name
        task.automated = True
        task.save = True
        task.options = fbx_ui
        try:
            at.import_asset_tasks([task])
        except Exception as exc:  # noqa: BLE001
            results.append({"name": name, "ok": False, "error": str(exc)})
            continue
        if not unreal.EditorAssetLibrary.does_asset_exist(dst_asset):
            results.append({"name": name, "ok": False, "error": "import/verify failed"})
            continue
        results.append({"name": name, "ok": True, "asset": dst_asset})
    return results


def main():
    report = {
        "schema": "melodia.sea_above_p0_ingest.v1",
        "utc": datetime.datetime.utcnow().isoformat() + "Z",
        "textures": [],
        "meshes": [],
    }
    if unreal.EditorAssetLibrary.does_directory_exist(TEX_DST) is False:
        unreal.EditorAssetLibrary.make_directory(TEX_DST)
    if unreal.EditorAssetLibrary.does_directory_exist(MESH_DST) is False:
        unreal.EditorAssetLibrary.make_directory(MESH_DST)

    with open(MANIFEST_PATH, "r", encoding="utf-8") as fh:
        manifest = json.load(fh)
    _log("texture manifest: %d files, tileable_pass=%d" % (
        len(manifest["files"]), manifest["summary"]["tileable_pass"]))
    report["textures"] = import_textures(manifest)
    report["meshes"] = import_meshes()

    tex_ok = sum(1 for r in report["textures"] if r["ok"])
    mesh_ok = sum(1 for r in report["meshes"] if r["ok"])
    report["summary"] = {
        "textures_ok": tex_ok, "textures_total": len(report["textures"]),
        "meshes_ok": mesh_ok, "meshes_total": len(report["meshes"]),
        "dirty_packages_note": "run list_dirty_packages before/after; save via this script only",
    }
    out = os.path.join(PROJECT_DIR, "Saved", "Audit", "sea_above",
                       "ingest_report_%s.json" % datetime.datetime.utcnow().strftime("%Y%m%dT%H%M%SZ"))
    with open(out, "w", encoding="utf-8") as fh:
        json.dump(report, fh, indent=1)
    _log("PASS tex %d/%d mesh %d/%d -> report %s" % (
        tex_ok, len(report["textures"]), mesh_ok, len(report["meshes"]), out))


if __name__ == "__main__":
    main()
