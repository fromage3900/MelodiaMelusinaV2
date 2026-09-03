"""Import the 424 KitBash3D Atlantis textures (PNG) into the game project.

Source: Imports/KitBash3D_Atlantis/Source/Textures 4K/*.png
Dest:   /Game/EnvSandbox/Textures/Atlantis/

Slot-aware sRGB (BlingVol3 proven pattern): basecolor/emissive = sRGB on;
normal/metallic/roughness/height/opacity/refraction = sRGB off. Never
overwrites an existing asset at the destination stem.

Run inside the live editor via Monolith run_python. Manifest:
Saved/Audit/atlantis_texture_import.json
"""
from __future__ import annotations

import json
import sys
from datetime import datetime, timezone
from pathlib import Path

import unreal

SRC = Path(__file__).resolve().parents[3] / "Imports" / "KitBash3D_Atlantis" / "Source" / "Textures 4K"
DEST = "/Game/EnvSandbox/Textures/Atlantis"
REPORT = Path(__file__).resolve().parents[2] / "Saved" / "Audit" / "atlantis_texture_import.json"

SRGB_ON = ("basecolor", "emissive")
SRGB_OFF = ("normal", "metallic", "roughness", "height", "opacity", "refraction")


def main() -> int:
    if not SRC.is_dir():
        print(f"ERROR: source dir missing: {SRC}")
        return 1
    pngs = sorted(SRC.glob("*.png"))
    unreal.log(f"[AtlantisTextures] found {len(pngs)} png in {SRC}")

    if not unreal.EditorAssetLibrary.does_directory_exist(DEST):
        unreal.EditorAssetLibrary.make_directory(DEST)

    imported, skipped, failed = [], [], []
    for png in pngs:
        safe_stem = png.stem.replace(".", "_")
        asset = f"{DEST}/{safe_stem}"
        if unreal.EditorAssetLibrary.does_asset_exist(asset):
            skipped.append(png.name)
            continue
        task = unreal.AssetImportTask()
        task.set_editor_property("automated", True)
        task.set_editor_property("filename", str(png))
        task.set_editor_property("destination_path", DEST)
        task.set_editor_property("replace_existing", False)
        task.set_editor_property("save", False)
        unreal.AssetToolsHelpers.get_asset_tools().import_asset_tasks([task])
        tex = unreal.EditorAssetLibrary.load_asset(asset)
        if tex:
            stem_lower = png.stem.lower()
            srgb_on = any(tag in stem_lower for tag in SRGB_ON) and not any(
                tag in stem_lower for tag in SRGB_OFF
            )
            tex.set_editor_property("srgb", srgb_on)
            imported.append(png.name)
        else:
            failed.append(png.name)

    unreal.log(
        f"[AtlantisTextures] imported: {len(imported)} | skipped-existing: {len(skipped)} | failed: {len(failed)}"
    )

    saved = 0
    for name in imported:
        try:
            safe_stem = name[:-4].replace(".", "_")
            if unreal.EditorAssetLibrary.save_asset(f"{DEST}/{safe_stem}"):
                saved += 1
        except Exception:
            pass
    unreal.log(f"[AtlantisTextures] saved: {saved}/{len(imported)}")

    report = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "source": str(SRC),
        "dest": DEST,
        "srgb_on_tags": list(SRGB_ON),
        "srgb_off_tags": list(SRGB_OFF),
        "found": len(pngs),
        "imported": imported,
        "skipped_existing": skipped,
        "failed": failed,
        "saved": saved,
        "ok": not failed,
    }
    REPORT.parent.mkdir(parents=True, exist_ok=True)
    REPORT.write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(json.dumps(report, indent=2))
    return 0 if not failed else 1


if __name__ == "__main__":
    raise SystemExit(main())