"""Sync Grease Pencil brushes + materials into durable Asset Libraries.

Targets:
  1) User Library:  C:\\Users\\froma\\OneDrive\\Documents\\Blender\\Assets\\GreasePencil\\
  2) Project SSOT:  G:\\EnvironmentPortfolio\\BS_GodFile\\Assets\\GreasePencil\\

Copies Blender 5.1 Essentials GP brush blends (already asset-marked),
ensures key GP materials are asset-marked in a cataloged library blend,
and writes an inventory JSON.

Safe to run headless:
  blender --factory-startup -b -P Tools/sync_grease_pencil_asset_library.py
"""
from __future__ import annotations

import json
import shutil
import uuid
from datetime import datetime, timezone
from pathlib import Path

import bpy

USER_LIB = Path(r"C:\Users\froma\OneDrive\Documents\Blender\Assets")
PROJECT_LIB = Path(r"G:\EnvironmentPortfolio\BS_GodFile\Assets\GreasePencil")
ESSENTIALS_SRC = Path(
    r"C:\Program Files\Blender Foundation\Blender 5.1\5.1\datafiles\assets\brushes"
)
AUDIT = Path(
    r"G:\EnvironmentPortfolio\BS_GodFile\Saved\Audit\grease_pencil_asset_inventory.json"
)

GP_BLENDS = [
    "essentials_brushes-gp_draw.blend",
    "essentials_brushes-gp_sculpt.blend",
    "essentials_brushes-gp_vertex.blend",
    "essentials_brushes-gp_weight.blend",
]

# Stable catalog UUIDs (do not change once published)
CATALOGS = [
    ("a1b2c3d4-e5f6-7890-ab12-gp0000000001", "GreasePencil/Draw", "GP Draw"),
    ("a1b2c3d4-e5f6-7890-ab12-gp0000000002", "GreasePencil/Sculpt", "GP Sculpt"),
    ("a1b2c3d4-e5f6-7890-ab12-gp0000000003", "GreasePencil/Vertex", "GP Vertex"),
    ("a1b2c3d4-e5f6-7890-ab12-gp0000000004", "GreasePencil/Weight", "GP Weight"),
    ("a1b2c3d4-e5f6-7890-ab12-gp0000000005", "GreasePencil/Materials", "GP Materials"),
    ("a1b2c3d4-e5f6-7890-ab12-gp0000000006", "GreasePencil/Custom", "GP Custom"),
]

DRAW_CAT = CATALOGS[0][0]
SCULPT_CAT = CATALOGS[1][0]
VERTEX_CAT = CATALOGS[2][0]
WEIGHT_CAT = CATALOGS[3][0]
MAT_CAT = CATALOGS[4][0]
CUSTOM_CAT = CATALOGS[5][0]


def _log(msg: str) -> None:
    print(f"[gp-assets] {msg}", flush=True)


def _ensure_dirs() -> dict[str, Path]:
    paths = {
        "user_root": USER_LIB / "GreasePencil",
        "user_essentials": USER_LIB / "GreasePencil" / "Essentials",
        "user_custom": USER_LIB / "GreasePencil" / "Custom",
        "user_library_blend_dir": USER_LIB / "GreasePencil" / "Library",
        "project_root": PROJECT_LIB,
        "project_essentials": PROJECT_LIB / "Essentials",
        "project_custom": PROJECT_LIB / "Custom",
        "project_library": PROJECT_LIB / "Library",
    }
    for p in paths.values():
        p.mkdir(parents=True, exist_ok=True)
    return paths


def _update_cats_txt(cats_path: Path) -> None:
    existing = cats_path.read_text(encoding="utf-8") if cats_path.exists() else "VERSION 1\n"
    lines = existing.splitlines()
    # Keep header + unrelated catalogs; replace GreasePencil:* block
    kept = []
    for line in lines:
        if ":GreasePencil/" in line or line.strip().endswith(":GP Draw") or ":GP " in line:
            continue
        kept.append(line)
    if not any(l.strip() == "VERSION 1" for l in kept):
        kept.insert(0, "VERSION 1")
    # Ensure blank line before catalogs
    body = [l for l in kept if l.strip()]
    out = ["# This is an Asset Catalog Definition file for Blender.", "#", "VERSION 1", ""]
    # Preserve non-GP catalogs from body
    for l in body:
        if l.startswith("VERSION"):
            continue
        if l.startswith("#"):
            continue
        out.append(l)
    out.append("")
    for uid, path, name in CATALOGS:
        out.append(f"{uid}:{path}:{name}")
    cats_path.write_text("\n".join(out) + "\n", encoding="utf-8")
    _log(f"Updated catalogs {cats_path}")


def _copy_essentials(dest_essentials: Path) -> list[dict]:
    copied = []
    for name in GP_BLENDS:
        src = ESSENTIALS_SRC / name
        if not src.exists():
            copied.append({"file": name, "status": "missing_src"})
            continue
        dst = dest_essentials / name
        shutil.copy2(src, dst)
        copied.append({"file": name, "status": "copied", "bytes": dst.stat().st_size})
        _log(f"Copied {name} -> {dst}")
    return copied


def _copy_custom_pencil(dest_custom: Path) -> dict | None:
    src = USER_LIB / "Saved" / "Brushes" / "Pencil.asset.blend"
    if not src.exists():
        return {"status": "missing", "src": str(src)}
    dst = dest_custom / "Pencil.asset.blend"
    shutil.copy2(src, dst)
    _log(f"Copied custom Pencil.asset.blend -> {dst}")
    return {"status": "copied", "src": str(src), "dst": str(dst), "bytes": dst.stat().st_size}


def _catalog_for_file(filename: str) -> str:
    if "gp_draw" in filename:
        return DRAW_CAT
    if "gp_sculpt" in filename:
        return SCULPT_CAT
    if "gp_vertex" in filename:
        return VERTEX_CAT
    if "gp_weight" in filename:
        return WEIGHT_CAT
    return DRAW_CAT


def _mark_asset(id_data, catalog_id: str, tags: list[str] | None = None) -> None:
    if not id_data.asset_data:
        id_data.asset_mark()
    ad = id_data.asset_data
    ad.catalog_id = catalog_id
    if tags:
        # clear then add
        while ad.tags:
            ad.tags.remove(ad.tags[0])
        for t in tags:
            ad.tags.new(t)


def build_marked_library(out_blend: Path, essentials_dir: Path, custom_dir: Path) -> dict:
    # Fresh empty file content (caller should run with --factory-startup ideally)
    bpy.ops.wm.read_homefile(use_empty=True)

    inventory = {
        "brushes": [],
        "materials": [],
        "sources": [],
    }

    # Append from essentials copies
    for name in GP_BLENDS:
        src = essentials_dir / name
        if not src.exists():
            continue
        cat = _catalog_for_file(name)
        with bpy.data.libraries.load(str(src), link=False) as (data_from, data_to):
            data_to.brushes = list(data_from.brushes or [])
            data_to.materials = list(data_from.materials or [])
        inventory["sources"].append(name)
        for b in data_to.brushes:
            # Avoid name collisions across packs
            if bpy.data.brushes.get(b.name) not in (None, b):
                b.name = f"{b.name} ({name.replace('essentials_brushes-', '').replace('.blend','')})"
            _mark_asset(b, cat, tags=["grease_pencil", "essentials"])
            inventory["brushes"].append({"name": b.name, "catalog": cat, "source": name})
        for m in data_to.materials:
            _mark_asset(m, MAT_CAT, tags=["grease_pencil", "material", "essentials"])
            inventory["materials"].append({"name": m.name, "catalog": MAT_CAT, "source": name})

    # Append custom pencil if present
    custom = custom_dir / "Pencil.asset.blend"
    if custom.exists():
        with bpy.data.libraries.load(str(custom), link=False) as (data_from, data_to):
            data_to.brushes = list(data_from.brushes or [])
            data_to.materials = list(data_from.materials or [])
        for b in data_to.brushes:
            if not b.name.endswith(" (Custom)"):
                b.name = f"{b.name} (Custom)"
            _mark_asset(b, CUSTOM_CAT, tags=["grease_pencil", "custom"])
            inventory["brushes"].append({"name": b.name, "catalog": CUSTOM_CAT, "source": "Pencil.asset.blend"})
        for m in data_to.materials:
            _mark_asset(m, MAT_CAT, tags=["grease_pencil", "material", "custom"])
            inventory["materials"].append({"name": m.name, "catalog": MAT_CAT, "source": "Pencil.asset.blend"})

    out_blend.parent.mkdir(parents=True, exist_ok=True)
    bpy.ops.wm.save_as_mainfile(filepath=str(out_blend))
    _log(f"Wrote library blend {out_blend}")
    inventory["library_blend"] = str(out_blend)
    inventory["brush_count"] = len(inventory["brushes"])
    inventory["material_count"] = len(inventory["materials"])
    return inventory


def main() -> dict:
    paths = _ensure_dirs()
    report: dict = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "user_library": str(USER_LIB),
        "project_library": str(PROJECT_LIB),
        "essentials_src": str(ESSENTIALS_SRC),
    }

    report["copied_user"] = _copy_essentials(paths["user_essentials"])
    report["copied_project"] = _copy_essentials(paths["project_essentials"])
    report["custom_user"] = _copy_custom_pencil(paths["user_custom"])
    # mirror custom into project
    if report["custom_user"] and report["custom_user"].get("status") == "copied":
        shutil.copy2(paths["user_custom"] / "Pencil.asset.blend", paths["project_custom"] / "Pencil.asset.blend")

    _update_cats_txt(USER_LIB / "blender_assets.cats.txt")
    # Project cats too
    _update_cats_txt(PROJECT_LIB / "blender_assets.cats.txt")

    user_lib_blend = paths["user_library_blend_dir"] / "Melodia_GreasePencil_Library.blend"
    inv = build_marked_library(user_lib_blend, paths["user_essentials"], paths["user_custom"])
    report["inventory"] = inv

    # Mirror library blend to project
    proj_lib_blend = paths["project_library"] / "Melodia_GreasePencil_Library.blend"
    shutil.copy2(user_lib_blend, proj_lib_blend)
    report["project_library_blend"] = str(proj_lib_blend)

    # Also mirror essentials + cats already done
    AUDIT.parent.mkdir(parents=True, exist_ok=True)
    AUDIT.write_text(json.dumps(report, indent=2), encoding="utf-8")
    report["audit"] = str(AUDIT)
    _log(f"Audit {AUDIT}")
    return report


if __name__ == "__main__":
    print(json.dumps(main(), indent=2))
