"""Hydrate + import Bow HUD v4 Figma token exports for UE staging.

Source:
  pipeline/figma/bow_hud_v4_manifest.json

PNG is Git-LFS-managed in this repo. The connected GitHub API cannot upload LFS
backing objects, so exact PNG @2x bytes are stored as .png.b64 text payloads.
Hydration is lossless and writes only under Saved/Staging before import.
"""
from __future__ import annotations

import base64
import json
from pathlib import Path
import unreal

ROOT = Path(__file__).resolve().parents[2]
MANIFEST = ROOT / "pipeline" / "figma" / "bow_hud_v4_manifest.json"
STAGE_DIR = ROOT / "Saved" / "Staging" / "BowHUD_v4"


def _configure_ui_texture(game_path: str) -> bool:
    tex = unreal.EditorAssetLibrary.load_asset(game_path)
    if not tex or not isinstance(tex, unreal.Texture2D):
        unreal.log_error(f"[BowHUDv4] not a Texture2D: {game_path}")
        return False
    tex.set_editor_property("compression_settings", unreal.TextureCompressionSettings.TC_EDITOR_ICON)
    tex.set_editor_property("lod_group", unreal.TextureGroup.TEXTUREGROUP_UI)
    tex.set_editor_property("mip_gen_settings", unreal.TextureMipGenSettings.TMGS_NO_MIPMAPS)
    tex.set_editor_property("srgb", True)
    tex.set_editor_property("never_stream", True)
    tex.set_editor_property("preserve_border", True)
    tex.modify()
    tex.post_edit_change()
    unreal.EditorAssetLibrary.save_loaded_asset(tex)
    return True


def _hydrate(entry: dict) -> Path:
    payload = ROOT / entry["png_b64"]
    if not payload.is_file():
        raise FileNotFoundError(payload)
    STAGE_DIR.mkdir(parents=True, exist_ok=True)
    out = STAGE_DIR / entry["filename"]
    out.write_bytes(base64.b64decode(payload.read_text(encoding="ascii")))
    return out


def _import(src: Path, dest: str) -> str | None:
    stem = src.stem
    game_path = f"{dest}/{stem}.{stem}"
    if not unreal.EditorAssetLibrary.does_directory_exist(dest):
        unreal.EditorAssetLibrary.make_directory(dest)
    task = unreal.AssetImportTask()
    task.set_editor_property("filename", str(src))
    task.set_editor_property("destination_path", dest)
    task.set_editor_property("destination_name", stem)
    task.set_editor_property("automated", True)
    task.set_editor_property("save", True)
    task.set_editor_property("replace_existing", True)
    unreal.AssetToolsHelpers.get_asset_tools().import_asset_tasks([task])
    if unreal.EditorAssetLibrary.does_asset_exist(game_path) and _configure_ui_texture(game_path):
        unreal.log(f"[BowHUDv4] imported {game_path}")
        return game_path
    unreal.log_error(f"[BowHUDv4] failed {src} -> {dest}")
    return None


def main() -> list[str]:
    if not MANIFEST.is_file():
        unreal.log_error(f"[BowHUDv4] missing manifest: {MANIFEST}")
        return []
    data = json.loads(MANIFEST.read_text(encoding="utf-8"))
    imported: list[str] = []
    for entry in data.get("entries", []):
        try:
            src = _hydrate(entry)
        except Exception as exc:
            unreal.log_error(f"[BowHUDv4] hydrate failed for {entry.get('token')}: {exc}")
            continue
        path = _import(src, entry["ue_dest"])
        if path:
            imported.append(path)
    unreal.log(f"[BowHUDv4] imported {len(imported)}/{len(data.get('entries', []))} tokens")
    return imported


if __name__ == "__main__":
    main()
