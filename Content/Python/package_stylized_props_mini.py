"""Package Melodia Stylized Props Mini lean buyer ZIP.

Copies game/low meshes + Brick01/02 bake maps from staging into
Products/StylizedPropsMini/, excluding multi-100MB highs.

Usage:
  python Content/Python/package_stylized_props_mini.py
  python Content/Python/package_stylized_props_mini.py --zip
"""
from __future__ import annotations

import json
import shutil
import zipfile
from datetime import datetime, timezone
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
STAGING = PROJECT_ROOT / "Products" / "_Staging" / "StylizedPropsMini"
PRODUCT = PROJECT_ROOT / "Products" / "StylizedPropsMini"
MANIFEST_PATH = PRODUCT / "product_manifest.json"

# Lean ship set — highs never included
LEAN_MESHES = [
    "Brick1.fbx",
    "stylizedmagicalwand.fbx",
    "sakurapetal.fbx",
    "wallbase.fbx",
    "MelodySlime1.fbx",
    "zenlantern.obj",  # prefer OBJ (~0.4 MB) over zenlantern.fbx (~163 MB)
]

ZIP_EXCLUDES = {
    "Brick1High.fbx",
    "Brick2High.fbx",
    "zenlanternhigh.fbx",
    "wand.obj",
    "zenlantern.fbx",
}


def _copy_lean() -> list[str]:
    fbx_dir = PRODUCT / "FBX"
    tex_dir = PRODUCT / "Textures"
    fbx_dir.mkdir(parents=True, exist_ok=True)
    tex_dir.mkdir(parents=True, exist_ok=True)

    copied: list[str] = []
    for name in LEAN_MESHES:
        src = STAGING / name
        if not src.is_file():
            print(f"[PropsMini] MISSING lean mesh: {name}")
            continue
        dest = fbx_dir / name
        shutil.copy2(src, dest)
        copied.append(name)
        print(f"[PropsMini] copied {name}")

    staging_tex = STAGING / "Textures"
    if staging_tex.is_dir():
        for png in sorted(staging_tex.glob("Brick0*.png")):
            shutil.copy2(png, tex_dir / png.name)
            copied.append(f"Textures/{png.name}")
            print(f"[PropsMini] copied Textures/{png.name}")

    return copied


def _update_manifest(mesh_count: int, zip_path: Path | None) -> None:
    data = json.loads(MANIFEST_PATH.read_text(encoding="utf-8-sig"))
    data["mesh_count"] = mesh_count
    data["store_live"] = False
    data["artstation_live"] = False
    data["zip_excludes_highs"] = True
    data["export_status"] = {
        "status": "lean_packaged" if zip_path else "lean_staged",
        "exported": mesh_count,
        "total": mesh_count,
        "note": "Highs excluded; zenlantern ships as .obj",
    }
    data["generated_at"] = datetime.now(timezone.utc).isoformat()
    if zip_path:
        data["release_zip"] = str(zip_path.relative_to(PROJECT_ROOT)).replace("\\", "/")
    MANIFEST_PATH.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")


def _write_zip() -> Path:
    releases = PRODUCT / "releases"
    releases.mkdir(parents=True, exist_ok=True)
    zip_path = releases / "melodia-stylized-props-mini-v1.zip"
    if zip_path.exists():
        zip_path.unlink()

    with zipfile.ZipFile(zip_path, "w", compression=zipfile.ZIP_DEFLATED) as zf:
        for folder, arc_prefix in (
            (PRODUCT / "FBX", "FBX"),
            (PRODUCT / "Textures", "Textures"),
            (PRODUCT / "Docs", "Docs"),
        ):
            if not folder.is_dir():
                continue
            for path in folder.rglob("*"):
                if path.is_file():
                    if path.name in ZIP_EXCLUDES:
                        continue
                    arc = f"{arc_prefix}/{path.relative_to(folder).as_posix()}"
                    zf.write(path, arcname=arc)
    return zip_path


def main() -> int:
    import sys

    do_zip = "--zip" in sys.argv
    if not STAGING.is_dir():
        print(f"[PropsMini] staging missing: {STAGING}")
        return 1

    copied = _copy_lean()
    mesh_copied = [c for c in copied if not c.startswith("Textures/")]
    mesh_count = len(mesh_copied)

    zip_path = None
    if do_zip:
        zip_path = _write_zip()
        size_mb = zip_path.stat().st_size / (1024 * 1024)
        print(f"[PropsMini] ZIP -> {zip_path} ({size_mb:.1f} MB)")

    _update_manifest(mesh_count, zip_path)
    print(f"[PropsMini] lean meshes={mesh_count} store_live=false")
    return 0 if mesh_count == len(LEAN_MESHES) else 2


if __name__ == "__main__":
    raise SystemExit(main())
