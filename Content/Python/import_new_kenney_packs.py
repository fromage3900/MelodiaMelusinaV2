"""Import the three new Kenney packs (2026-08-14).

Packs (staged under Imports/Environment/):
  1. KenneyRetroTexturesFantasy  - 119 albedo-style PNGs (door/floor/roof/wall/window/timber)
  2. KenneyRetroFantasyKit       - 105 meshes (GLB/FBX/OBJ) + 10 shared textures
                                   (barrel/cobblestone/cobblestoneAlternative/
                                    cobblestonePainted/details/fence/planks/roof/tree/water)
  3. KenneyPatternPackExtra      - 84 seamless patterns (Default) + Large variants

Textures go to /Game/EnvSandbox/Textures/PackTextures/<Pack>/ with slot-aware sRGB
(albedo/pattern sRGB ON). Meshes go to /Game/EnvSandbox/Meshes/Environment (flat,
matching the mass-GLB import convention), WITHOUT materials (intake contract), then
route_retro_materials.py assigns per-slot MIs using the pack's shared textures.

Run in the UE editor (Monolith run_python): import_new_kenney_packs.main()
Writes: Saved/Audit/kenney_new_import.json
"""
from __future__ import annotations

import json
import os
from pathlib import Path

import unreal

ROOT = Path(__file__).resolve().parents[2]
IMPORTS = ROOT / "Imports" / "Environment"
OUT = ROOT / "Saved" / "Audit" / "kenney_new_import.json"
TEX_BASE = "/Game/EnvSandbox/Textures/PackTextures"
MESH_DEST = "/Game/EnvSandbox/Meshes/Environment"

# texture name -> sRGB intent (default True = albedo/pattern)
NON_SRGB_TOKENS = ("normal", "bump", "ao", "ambientocclusion", "roughness",
                   "metallic", "displacement", "height", "specular", "cavity",
                   "gloss", "depth")


def tex_srgb(name: str) -> bool:
    n = name.lower()
    return not any(t in n for t in NON_SRGB_TOKENS)


def import_textures(src_dir: Path, dest_dir: str, pack: str) -> list[dict]:
    rows = []
    for f in sorted(src_dir.rglob("*")):
        if not f.is_file() or f.suffix.lower() not in (".png", ".jpg", ".jpeg", ".tif"):
            continue
        base = f.stem
        game = f"{dest_dir}/{base}"
        tex = unreal.EditorAssetLibrary.load_asset(game)
        if tex is None:
            task = unreal.AssetImportTask()
            task.set_editor_property("automated", True)
            task.set_editor_property("filename", str(f))
            task.set_editor_property("destination_path", dest_dir)
            task.set_editor_property("replace_existing", False)
            task.set_editor_property("save", False)
            unreal.AssetToolsHelpers.get_asset_tools().import_asset_tasks([task])
            tex = unreal.EditorAssetLibrary.load_asset(game)
        if tex is None:
            rows.append({"name": base, "status": "FAILED"})
            continue
        srgb = tex_srgb(base)
        try:
            tex.set_editor_property("srgb", srgb)
        except Exception:
            pass
        if "normal" in base.lower():
            try:
                tex.set_editor_property("compression_settings",
                                        unreal.TextureCompressionSettings.TC_NORMALMAP)
            except Exception:
                pass
        unreal.EditorAssetLibrary.save_loaded_asset(tex)
        rows.append({"name": base, "status": "ok", "srgb": srgb, "pack": pack})
    return rows


def import_meshes(src_dir: Path) -> list[dict]:
    glb_dir = src_dir / "Models" / "GLB format"
    rows = []
    for f in sorted(glb_dir.glob("*.glb")):
        stem = f.stem
        game = f"{MESH_DEST}/{stem}"
        if unreal.EditorAssetLibrary.does_asset_exist(game):
            rows.append({"name": stem, "status": "exists"})
            continue
        task = unreal.AssetImportTask()
        task.set_editor_property("automated", True)
        task.set_editor_property("filename", str(f))
        task.set_editor_property("destination_path", MESH_DEST)
        task.set_editor_property("replace_existing", False)
        task.set_editor_property("save", False)
        opts = unreal.FbxImportUI()
        opts.set_editor_property("import_materials", False)
        opts.set_editor_property("import_textures", False)
        opts.set_editor_property("import_as_skeletal", False)
        task.options = opts
        unreal.AssetToolsHelpers.get_asset_tools().import_asset_tasks([task])
        mesh = unreal.EditorAssetLibrary.load_asset(game)
        if mesh is None:
            rows.append({"name": stem, "status": "FAILED"})
            continue
        unreal.EditorAssetLibrary.save_loaded_asset(mesh)
        rows.append({"name": stem, "status": "imported"})
    return rows


def main():
    report = {"generated": "2026-08-14", "packs": {}}

    # 1. retro-textures-fantasy -> textures
    src1 = IMPORTS / "KenneyRetroTexturesFantasy" / "PNG"
    dest1 = f"{TEX_BASE}/RetroTexturesFantasy"
    if src1.exists():
        report["packs"]["retro_textures_fantasy"] = {
            "textures": import_textures(src1, dest1, "RetroTexturesFantasy")}

    # 2. retro-fantasy-kit -> meshes + textures
    src2 = IMPORTS / "KenneyRetroFantasyKit"
    glb_tex = src2 / "Models" / "GLB format" / "Textures"
    dest2 = f"{TEX_BASE}/RetroFantasyKit"
    meshes = import_meshes(src2) if (src2 / "Models" / "GLB format").exists() else []
    textures = import_textures(glb_tex, dest2, "RetroFantasyKit") if glb_tex.exists() else []
    report["packs"]["retro_fantasy_kit"] = {"meshes": meshes, "textures": textures}

    # 3. pattern-pack-extra -> textures (Default set; Large variants kept as-is)
    src3 = IMPORTS / "KenneyPatternPackExtra" / "PNG" / "Default"
    dest3 = f"{TEX_BASE}/PatternPackExtra"
    if src3.exists():
        report["packs"]["pattern_pack_extra"] = {
            "textures": import_textures(src3, dest3, "PatternPackExtra")}

    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(report, indent=2), encoding="utf-8")
    summary = {}
    for pack, data in report["packs"].items():
        for kind in ("textures", "meshes"):
            rows = data.get(kind) or []
            ok = sum(1 for r in rows if r["status"] in ("ok", "imported"))
            summary[f"{pack}.{kind}"] = f"{ok}/{len(rows)}"
    unreal.log(f"[kenney_new] {summary}")
    print(json.dumps(summary))
    return report


if __name__ == "__main__":
    main()
