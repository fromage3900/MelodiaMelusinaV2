"""Import or reimport generated Melodia UI atoms with alpha-safe UMG settings.

Run after ``generate_ui_textures.py`` from Unreal's Python console:

    import import_generated_ui_atoms as atoms; atoms.main()

The source PNGs remain canonical. This script intentionally updates only textures
under /Game/Melodia/UI/Textures/Generated and never edits Widget Blueprints.
"""
from __future__ import annotations

from pathlib import Path

import unreal

PROJECT_ROOT = Path(__file__).resolve().parents[2]
SOURCE_DIR = PROJECT_ROOT / "Content" / "Melodia" / "UI" / "Textures" / "Generated"
DESTINATION = "/Game/Melodia/UI/Textures/Generated"


def _configure(texture: unreal.Texture2D) -> None:
    """Use color-UI compression while retaining the PNG alpha channel."""
    texture.set_editor_property("compression_settings", unreal.TextureCompressionSettings.TC_EDITOR_ICON)
    texture.set_editor_property("lod_group", unreal.TextureGroup.TEXTUREGROUP_UI)
    texture.set_editor_property("mip_gen_settings", unreal.TextureMipGenSettings.TMGS_NO_MIPMAPS)
    texture.set_editor_property("srgb", True)
    texture.set_editor_property("never_stream", True)
    texture.set_editor_property("preserve_border", True)
    texture.modify()
    texture.post_edit_change()
    unreal.EditorAssetLibrary.save_loaded_asset(texture)


def _import_or_reimport(source: Path) -> str | None:
    stem = source.stem
    object_path = f"{DESTINATION}/{stem}.{stem}"

    if not unreal.EditorAssetLibrary.does_directory_exist(DESTINATION):
        unreal.EditorAssetLibrary.make_directory(DESTINATION)

    task = unreal.AssetImportTask()
    task.set_editor_property("filename", str(source))
    task.set_editor_property("destination_path", DESTINATION)
    task.set_editor_property("destination_name", stem)
    task.set_editor_property("automated", True)
    task.set_editor_property("replace_existing", True)
    task.set_editor_property("save", False)
    unreal.AssetToolsHelpers.get_asset_tools().import_asset_tasks([task])

    texture = unreal.EditorAssetLibrary.load_asset(object_path)
    if not texture or not isinstance(texture, unreal.Texture2D):
        unreal.log_error(f"[MelodiaUIAtoms] import failed: {source} -> {object_path}")
        return None

    _configure(texture)
    alpha_state = "opaque" if stem == "T_ParchmentNoise" else "transparent"
    unreal.log(f"[MelodiaUIAtoms] {alpha_state} UI texture ready: {object_path}")
    return object_path


def main() -> list[str]:
    if not SOURCE_DIR.is_dir():
        unreal.log_error(f"[MelodiaUIAtoms] source directory missing: {SOURCE_DIR}")
        return []

    imported = [
        path
        for source in sorted(SOURCE_DIR.glob("*.png"))
        if (path := _import_or_reimport(source)) is not None
    ]
    unreal.log(f"[MelodiaUIAtoms] configured {len(imported)} atom textures")
    return imported


if __name__ == "__main__":
    main()
