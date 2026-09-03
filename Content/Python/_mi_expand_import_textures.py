"""Import Copernicus cymatic PNGs from Saved/Audit/copernicus_cymatic/ into
Content/EnvSandbox/Textures/Copernicus/. Covers all 30 variants (static +
animated channels).

Per-variant, per-channel sRGB tagging (matches existing import_atlantis_textures.py):
  sRGB ON:  BaseColor, Emissive, Iridescence
  sRGB OFF: Normal, ORM, Roughness, Metallic, Height, Opacity

Destination path convention (matches existing MIs):
  /Game/EnvSandbox/Textures/Copernicus/<Variant>/T_Cymatic_<Variant>_<Channel>

Run in-editor:
  UnrealEditor-Cmd.exe BS_GodFile.uproject
    -ExecutePythonScript="Content/Python/_mi_expand_import_textures.py"
    -unattended -nullrhi

Manifest: Saved/Audit/copernicus_mi_import.json
"""
from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

import unreal

PROJECT_ROOT = Path("C:/EnvironmentPortfolio/BS_GodFile")
SRC_ROOT = PROJECT_ROOT / "Saved" / "Audit" / "copernicus_cymatic"
DEST_ROOT = "/Game/EnvSandbox/Textures/Copernicus"
REPORT = PROJECT_ROOT / "Saved" / "Audit" / "copernicus_mi_import.json"

SRGB_ON = {"basecolor", "emissive", "iridescence"}
SRGB_OFF = {"normal", "orm", "roughness", "metallic", "height", "opacity"}

# Channel suffix detection on PNG stem T_Cymatic_<Variant>_<Channel>
CHANNEL_SUFFIXES = [
    "BaseColor", "Emissive", "Height", "Iridescence",
    "Metallic", "Normal", "ORM", "Opacity", "Roughness",
]


def channel_from_stem(variant: str, stem: str) -> str | None:
    """Return channel tag from PNG stem, or None if not a channel file."""
    prefix = f"T_Cymatic_{variant}_"
    if not stem.startswith(prefix):
        return None
    tail = stem[len(prefix):]
    # Strip animated frame suffix (.1, .2, ...) to get base channel
    base = tail.split(".")[0] if "." in tail else tail
    if base in CHANNEL_SUFFIXES:
        return base
    return None


def srgb_for_channel(channel: str) -> bool:
    return channel.lower() in SRGB_ON and channel.lower() not in SRGB_OFF


def main() -> int:
    if not SRC_ROOT.is_dir():
        print(f"[IMPORT] ERROR source missing: {SRC_ROOT}")
        return 1

    variants = sorted(
        d.name for d in SRC_ROOT.iterdir()
        if d.is_dir() and not d.name.startswith("_")
    )
    print(f"[IMPORT] found {len(variants)} variants on disk")

    if not unreal.EditorAssetLibrary.does_directory_exist(DEST_ROOT):
        unreal.EditorAssetLibrary.make_directory(DEST_ROOT)

    total_imported = 0
    total_skipped = 0
    total_failed = 0
    variant_rows = []

    for variant in variants:
        src_dir = SRC_ROOT / variant
        dest_dir = f"{DEST_ROOT}/{variant}"
        if not unreal.EditorAssetLibrary.does_directory_exist(dest_dir):
            unreal.EditorAssetLibrary.make_directory(dest_dir)

        pngs = sorted(src_dir.glob("*.png"))
        imported, skipped, failed = [], [], []
        for png in pngs:
            stem = png.stem
            channel = channel_from_stem(variant, stem)
            if channel is None:
                continue
            asset = f"{dest_dir}/{stem}"
            if unreal.EditorAssetLibrary.does_asset_exist(asset):
                skipped.append(stem)
                continue
            task = unreal.AssetImportTask()
            task.set_editor_property("automated", True)
            task.set_editor_property("filename", str(png))
            task.set_editor_property("destination_path", dest_dir)
            task.set_editor_property("replace_existing", False)
            task.set_editor_property("save", False)
            unreal.AssetToolsHelpers.get_asset_tools().import_asset_tasks([task])
            tex = unreal.EditorAssetLibrary.load_asset(asset)
            if tex is not None:
                tex.set_editor_property("srgb", srgb_for_channel(channel))
                imported.append(stem)
            else:
                failed.append(stem)

        # Save newly imported textures
        saved = 0
        for stem in imported:
            try:
                if unreal.EditorAssetLibrary.save_asset(f"{dest_dir}/{stem}"):
                    saved += 1
            except Exception:
                pass

        total_imported += len(imported)
        total_skipped += len(skipped)
        total_failed += len(failed)
        variant_rows.append({
            "variant": variant, "imported": len(imported),
            "skipped": len(skipped), "failed": len(failed), "saved": saved,
        })
        print(f"[IMPORT] {variant}: +{len(imported)} import, {len(skipped)} skip, "
              f"{len(failed)} fail, {saved} saved")

    report = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "source": str(SRC_ROOT),
        "dest": DEST_ROOT,
        "variants": variant_rows,
        "total_imported": total_imported,
        "total_skipped": total_skipped,
        "total_failed": total_failed,
        "ok": total_failed == 0,
    }
    REPORT.parent.mkdir(parents=True, exist_ok=True)
    REPORT.write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(f"[IMPORT] === report -> {REPORT} ===")
    print(json.dumps({k: v for k, v in report.items() if k != "variants"}, indent=2))
    return 0 if total_failed == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())