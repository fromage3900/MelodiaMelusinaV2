"""Hydrate + import Storybook runtime atoms from the canonical native-Figma export.

Source:
  pipeline/figma/storybook_runtime_manifest.json

Small irregular atoms are stored losslessly as base64 PNG payload text because
GitHub connector writes cannot upload Git-LFS backing objects. Simple paper/card
geometry is NOT imported as texture: specs/ui/storybook_runtime_styles.v1.json
keeps those as native UMG/Slate styles. Radial rings remain material specs.

This script therefore imports only entries with runtime_type == "texture".
"""
from __future__ import annotations

import base64
import json
from pathlib import Path
import unreal

ROOT = Path(__file__).resolve().parents[2]
MANIFEST = ROOT / "pipeline" / "figma" / "storybook_runtime_manifest.json"
STAGE_DIR = ROOT / "Saved" / "Staging" / "StorybookRuntime"


def _configure_ui_texture(game_path: str, never_stream: bool = True) -> bool:
    tex = unreal.EditorAssetLibrary.load_asset(game_path)
    if not tex or not isinstance(tex, unreal.Texture2D):
        unreal.log_error(f"[StorybookUI] not a Texture2D: {game_path}")
        return False

    tex.set_editor_property(
        "compression_settings", unreal.TextureCompressionSettings.TC_EDITOR_ICON
    )
    tex.set_editor_property("lod_group", unreal.TextureGroup.TEXTUREGROUP_UI)
    tex.set_editor_property(
        "mip_gen_settings", unreal.TextureMipGenSettings.TMGS_NO_MIPMAPS
    )
    tex.set_editor_property("srgb", True)
    tex.set_editor_property("never_stream", bool(never_stream))
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
    encoded = payload.read_text(encoding="ascii").replace("\\n", "").replace("\\r", "")
    out.write_bytes(base64.b64decode(encoded, validate=True))
    return out


def _import(src: Path, dest: str, never_stream: bool) -> str | None:
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

    if unreal.EditorAssetLibrary.does_asset_exist(game_path):
        if _configure_ui_texture(game_path, never_stream):
            unreal.log(f"[StorybookUI] imported {game_path}")
            return game_path

    unreal.log_error(f"[StorybookUI] failed {src} -> {dest}")
    return None


def main() -> list[str]:
    if not MANIFEST.is_file():
        unreal.log_error(f"[StorybookUI] missing manifest: {MANIFEST}")
        return []

    data = json.loads(MANIFEST.read_text(encoding="utf-8"))
    default_dest = data["ue"]["texture_dest"]
    entries = [
        e for e in data.get("entries", [])
        if e.get("runtime_type") == "texture"
    ]

    imported: list[str] = []
    for entry in entries:
        try:
            src = _hydrate(entry)
        except Exception as exc:
            unreal.log_error(
                f"[StorybookUI] hydrate failed for {entry.get('id')}: {exc}"
            )
            continue

        path = _import(
            src,
            entry.get("ue_dest", default_dest),
            bool(entry.get("never_stream", True)),
        )
        if path:
            imported.append(path)

    unreal.log(f"[StorybookUI] imported {len(imported)}/{len(entries)} texture atoms")
    unreal.log(
        "[StorybookUI] material/umg_style entries remain declarative by design; "
        "see manifest + specs/ui/storybook_runtime_styles.v1.json"
    )
    return imported


if __name__ == "__main__":
    main()
