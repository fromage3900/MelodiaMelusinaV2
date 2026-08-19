"""Import the BlingVol3 rhinestone texture set (90 jpg, 6-slot x 15 materials).

Source: Imports/SubstanceSource/BlingVol3/rhinestoneTextures/*.jpg
Dest:   /Game/EnvSandbox/Textures/BlingVol3/

Slot-aware sRGB: basecolor = sRGB on; normal/metallic/roughness/height/ao = sRGB off.
The 15 .sbsar Substance archives are NOT importable by UE; they stay in Imports as
source. Never overwrites: an existing asset at the destination stem is skipped.
"""
from __future__ import annotations

import sys
import time
from pathlib import Path

import unreal

SRC = Path(__file__).resolve().parents[2] / "Imports" / "SubstanceSource" / "BlingVol3" / "rhinestoneTextures"
DEST = "/Game/EnvSandbox/Textures/BlingVol3"

SRGB_OFF = ("normal", "metallic", "roughness", "height", "ambientocclusion")


def main() -> int:
    jpgs = sorted(SRC.glob("*.jpg"))
    unreal.log(f"[bling] found {len(jpgs)} jpg in {SRC}")
    imported, skipped, failed = [], [], []
    for jpg in jpgs:
        asset = f"{DEST}/{jpg.stem}"
        if unreal.EditorAssetLibrary.does_asset_exist(asset):
            skipped.append(jpg.name)
            continue
        task = unreal.AssetImportTask()
        task.set_editor_property("automated", True)
        task.set_editor_property("filename", str(jpg))
        task.set_editor_property("destination_path", DEST)
        task.set_editor_property("replace_existing", False)
        task.set_editor_property("save", False)
        unreal.AssetToolsHelpers.get_asset_tools().import_asset_tasks([task])
        tex = unreal.EditorAssetLibrary.load_asset(asset)
        if tex:
            is_srgb = not any(tag in jpg.stem for tag in SRGB_OFF)
            tex.set_editor_property("srgb", is_srgb)
            imported.append(jpg.name)
        else:
            failed.append(jpg.name)

    unreal.log(f"[bling] imported: {len(imported)} | skipped-existing: {len(skipped)} | failed: {len(failed)}")

    saved = 0
    for name in imported:
        try:
            if unreal.EditorAssetLibrary.save_asset(f"{DEST}/{name[:-4]}"):
                saved += 1
        except Exception:
            pass
    unreal.log(f"[bling] saved: {saved}/{len(imported)}")

    manifest = {
        "generated": "2026-08-13",
        "source": str(SRC),
        "dest": DEST,
        "imported": imported,
        "skipped_existing": skipped,
        "failed": failed,
    }
    out = Path(__file__).resolve().parents[2] / "Saved" / "Audit" / "blingvol3_import.json"
    out.write_text(__import__("json").dumps(manifest, indent=2), encoding="utf-8")
    return 0 if not failed else 1


if __name__ == "__main__":
    time.sleep(5)
    sys.exit(main())
