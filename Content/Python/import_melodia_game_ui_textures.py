"""Import Melodia game UI PNGs into EnvSandbox alphas and textures.

Run in Unreal Editor after export_melodia_game_ui_assets.py:

  python Content/Python/import_melodia_game_ui_textures.py

Or from the Python console:
  import import_melodia_game_ui_textures as m; m.main()
"""
from __future__ import annotations

import json
from pathlib import Path

import unreal

from paths import ALPHAS_MELODIA, MELODIA_GAME_UI_TEXTURES

PROJECT_ROOT = Path(__file__).resolve().parents[2]
MANIFEST = PROJECT_ROOT / "pipeline" / "figma" / "figma_game_ui_manifest.json"
SOURCE = PROJECT_ROOT / "Content" / "EnvSandbox" / "Textures" / "Source" / "MelodiaGameUI"
LIBRARY = Path(r"G:\EnvironmentPortfolio\_AssetLibrary") / "MelodiaGameUI"


def _resolve_src(filename: str) -> Path | None:
    for root in (SOURCE, LIBRARY):
        p = root / filename
        if p.is_file():
            return p
    return None


def _configure_ui_texture(game_path: str) -> bool:
    """Apply deterministic UMG-safe settings while preserving source alpha."""
    texture = unreal.EditorAssetLibrary.load_asset(game_path)
    if not texture or not isinstance(texture, unreal.Texture2D):
        unreal.log_error(f"[MelodiaGameUI] not a Texture2D: {game_path}")
        return False

    texture.set_editor_property("compression_settings", unreal.TextureCompressionSettings.TC_EDITOR_ICON)
    texture.set_editor_property("lod_group", unreal.TextureGroup.TEXTUREGROUP_UI)
    texture.set_editor_property("mip_gen_settings", unreal.TextureMipGenSettings.TMGS_NO_MIPMAPS)
    texture.set_editor_property("srgb", True)
    texture.set_editor_property("never_stream", True)
    texture.set_editor_property("preserve_border", True)
    texture.modify()
    texture.post_edit_change()
    unreal.EditorAssetLibrary.save_loaded_asset(texture)
    return True


def _import_png(src: Path, dest: str, stem: str) -> str | None:
    game_path = f"{dest}/{stem}.{stem}"
    if not unreal.EditorAssetLibrary.does_directory_exist(dest):
        unreal.EditorAssetLibrary.make_directory(dest)
    tools = unreal.AssetToolsHelpers.get_asset_tools()
    task = unreal.AssetImportTask()
    task.set_editor_property("filename", str(src))
    task.set_editor_property("destination_path", dest)
    task.set_editor_property("destination_name", stem)
    task.set_editor_property("automated", True)
    task.set_editor_property("save", True)
    task.set_editor_property("replace_existing", True)
    tools.import_asset_tasks([task])
    if unreal.EditorAssetLibrary.does_asset_exist(game_path):
        if not _configure_ui_texture(game_path):
            return None
        unreal.log(f"[MelodiaGameUI] imported/configured {game_path}")
        return game_path
    unreal.log_error(f"[MelodiaGameUI] failed {src} -> {dest}")
    return None


def main() -> list[str]:
    if not MANIFEST.is_file():
        unreal.log_error(f"[MelodiaGameUI] missing manifest: {MANIFEST}")
        return []

    data = json.loads(MANIFEST.read_text(encoding="utf-8"))
    imported: list[str] = []
    for entry in data.get("entries", []):
        filename = entry["filename"]
        src = _resolve_src(filename)
        if not src:
            unreal.log_warning(f"[MelodiaGameUI] missing source: {filename}")
            continue
        dest = entry.get("ue_dest") or (
            ALPHAS_MELODIA if entry.get("kind") == "alpha" else MELODIA_GAME_UI_TEXTURES
        )
        stem = Path(filename).stem
        path = _import_png(src, dest, stem)
        if path:
            imported.append(path)
    unreal.log(f"[MelodiaGameUI] imported {len(imported)} textures")
    return imported


if __name__ == "__main__":
    main()
