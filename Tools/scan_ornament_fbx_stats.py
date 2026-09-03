# -*- coding: utf-8 -*-
"""Scan KitbashExport ornament FBXs for verts/tris and sync catalog + passports.

Run:
  blender --factory-startup -b -P Tools/scan_ornament_fbx_stats.py

Writes:
  Saved/Audit/ornament_fbx_stats.json
  my-site-clean/generated/ornament_kitbash_catalog.json  (vertices/triangles/fbx_bytes)
  my-site-clean/generated/passports/<slug>_passport.{json,html}
  Products/OrnamentKitbash/product_manifest.json         (if present)
"""
from __future__ import annotations

import json
import os
import sys
from datetime import datetime, timezone

import bpy

ROOT = os.path.normpath(os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
ORN_DIR = os.path.join(ROOT, "KitbashExport", "OrnamentalMeshes")
SITE = os.path.join(ROOT, "my-site-clean")
CATALOG = os.path.join(SITE, "generated", "ornament_kitbash_catalog.json")
MANIFEST = os.path.join(ROOT, "Products", "OrnamentKitbash", "product_manifest.json")
AUDIT = os.path.join(ROOT, "Saved", "Audit", "ornament_fbx_stats.json")
TOOLS = os.path.dirname(os.path.abspath(__file__))

# catalog asset_name -> passport / intake asset_id
ID_MAP = {
    "SM_Orn_RoseWindow_8Petal": "rose_window",
    "SM_Orn_SpiralStaircase": "spiral_stair",
    "SM_Orn_VaultRibs": "vault_ribs",
    "SM_Orn_OculusFrame": "oculus_frame",
    "SM_Orn_QuatrefoilArch": "quatrefoil",
    "SM_Orn_GothicTracery": "gothic_tracery",
    "SM_Orn_DoorArchway": "door_archway",
    "SM_Orn_ColumnCapital": "column_capital",
    "SM_Orn_RosetteMedallion": "rosette",
    "SM_Orn_FiligreeRing": "filigree_ring",
    "SM_Orn_PendantFinial": "pendant_finial",
    "SM_Orn_WovenRing": "woven_ring",
    "SM_Orn_CrownMolding": "crown_molding",
    "SM_Orn_CorbelBracket": "corbel",
    "SM_Orn_TorusKnot": "torus_knot",
}

TITLE_MAP = {
    "vault_ribs": "Vault Ribs",
    "corbel": "Corbel Bracket",
    "crown_molding": "Crown Molding",
    "torus_knot": "Torus Knot",
}


def log(msg: str) -> None:
    print(f"[orn-stats] {msg}", flush=True)


def clear() -> None:
    bpy.ops.object.select_all(action="SELECT")
    bpy.ops.object.delete(use_global=False)
    for block in (bpy.data.meshes, bpy.data.materials, bpy.data.images):
        for b in list(block):
            if b.users == 0:
                block.remove(b)


def count_fbx(path: str) -> dict:
    clear()
    before = {o.name for o in bpy.data.objects}
    bpy.ops.import_scene.fbx(filepath=path)
    meshes = [
        o
        for o in bpy.data.objects
        if o.name not in before and o.type == "MESH" and o.data
    ]
    verts = 0
    tris = 0
    for o in meshes:
        me = o.data
        verts += len(me.vertices)
        try:
            me.calc_loop_triangles()
            tris += len(me.loop_triangles)
        except Exception:
            tris += sum(max(0, len(p.vertices) - 2) for p in me.polygons)
    dims = [0.0, 0.0, 0.0]
    if meshes:
        # world AABB diagonal approx via object dimensions sum
        xs, ys, zs = [], [], []
        for o in meshes:
            for corner in o.bound_box:
                w = o.matrix_world @ __import__("mathutils").Vector(corner)
                xs.append(w.x)
                ys.append(w.y)
                zs.append(w.z)
        dims = [
            round(max(xs) - min(xs), 3),
            round(max(ys) - min(ys), 3),
            round(max(zs) - min(zs), 3),
        ]
    return {
        "vertices": verts,
        "triangles": tris,
        "meshes": len(meshes),
        "dimensions_m": dims,
        "fbx_bytes": os.path.getsize(path) if os.path.isfile(path) else 0,
    }


def write_passport(asset_id: str, title: str, stats: dict) -> dict:
    if TOOLS not in sys.path:
        sys.path.insert(0, TOOLS)
    try:
        from melodia_asset_passport import build_passport, write_passport_files
    except ImportError as exc:
        log(
            f"passport skip for {asset_id}: melodia_asset_passport module is missing "
            "(lost 2026-07-31, only .pyc + a known-bad reconstruction remain - see "
            f"_TASK_QUEUE.md): {exc}"
        )
        return {"paths": None}

    passport = build_passport(
        asset_id=asset_id,
        project=title,
        category="Prop / ornament",
        version="cute-gn",
        shader="SurrealArch GeoNodes - kitbash",
        capture="FBX scan",
        software="Blender - SurrealArch v2.134",
        engine="Geometry Nodes -> FBX",
        stats={
            "triangles": stats["triangles"],
            "meshes": stats["meshes"],
            "materials": 1,
            "textures": 0,
        },
        extra_rows=[
            ["Vertices", f"{stats['vertices']:,}"],
            ["FBX", f"{stats['fbx_bytes'] // 1024} KB"],
            ["Dims (m)", " × ".join(str(d) for d in stats["dimensions_m"])],
        ],
    )
    paths = write_passport_files(passport)
    passport["paths"] = paths
    return passport


def main() -> None:
    if not os.path.isdir(ORN_DIR):
        log(f"FATAL missing {ORN_DIR}")
        raise SystemExit(2)

    catalog = {}
    if os.path.isfile(CATALOG):
        with open(CATALOG, encoding="utf-8") as f:
            catalog = json.load(f)

    results = {}
    for asset_name, asset_id in ID_MAP.items():
        path = os.path.join(ORN_DIR, f"{asset_name}.fbx")
        if not os.path.isfile(path):
            log(f"SKIP missing {asset_name}")
            continue
        stats = count_fbx(path)
        title = TITLE_MAP.get(asset_id, asset_name.replace("SM_Orn_", "").replace("_", " "))
        passport = write_passport(asset_id, title, stats)
        results[asset_name] = {
            **stats,
            "asset_id": asset_id,
            "passport": passport.get("paths"),
        }
        log(
            f"{asset_name}: verts={stats['vertices']} tris={stats['triangles']} "
            f"dims={stats['dimensions_m']} bytes={stats['fbx_bytes']}"
        )

    # Patch catalog meshes
    by_name = {m["asset_name"]: m for m in catalog.get("meshes", [])}
    for asset_name, stats in results.items():
        m = by_name.get(asset_name)
        if not m:
            continue
        m["vertices"] = stats["vertices"]
        m["triangles"] = stats["triangles"]
        m["fbx_bytes"] = stats["fbx_bytes"]
        m["dimensions_m"] = stats["dimensions_m"]
        m["asset_id"] = stats["asset_id"]
        if stats.get("passport"):
            m["passport_json"] = stats["passport"].get("json")
            m["passport_html"] = stats["passport"].get("html")
        # Refresh cute descriptions for the four
        if asset_name == "SM_Orn_VaultRibs":
            m["description"] = (
                "Crossing Bezier gothic vault ribs with apex flower boss - kitbash hero cluster."
            )
        elif asset_name == "SM_Orn_CorbelBracket":
            m["description"] = (
                "S-curve vine corbel with wall plate, scroll, shelf pad, and tip jewel."
            )
        elif asset_name == "SM_Orn_CrownMolding":
            m["description"] = (
                "Ogee/cyma crown molding with front bead and scallop lip waves."
            )
        elif asset_name == "SM_Orn_TorusKnot":
            m["description"] = (
                "Soft (3,2) trefoil knot with petal pulse and center jewel."
            )

    catalog["stats_scanned_at"] = datetime.now(timezone.utc).isoformat()
    catalog["mesh_count"] = len(catalog.get("meshes", []))
    # Export status from on-disk FBXs
    present = sum(
        1
        for m in catalog.get("meshes", [])
        if os.path.isfile(os.path.join(ORN_DIR, m.get("fbx_name") or f"{m['asset_name']}.fbx"))
    )
    total = len(catalog.get("meshes", []))
    catalog["export_status"] = {
        "exported": present,
        "total": total,
        "status": "complete" if present == total and total else "partial",
        "note": "Cute GeoNodes rebuild for vault / corbel / crown / torus",
    }

    os.makedirs(os.path.dirname(CATALOG), exist_ok=True)
    with open(CATALOG, "w", encoding="utf-8") as f:
        json.dump(catalog, f, indent=2)
        f.write("\n")
    log(f"catalog -> {CATALOG}")

    if os.path.isfile(MANIFEST):
        with open(MANIFEST, encoding="utf-8") as f:
            man = json.load(f)
        man_meshes = {m.get("asset_name"): m for m in man.get("meshes", [])}
        for asset_name, stats in results.items():
            if asset_name in man_meshes:
                man_meshes[asset_name]["vertices"] = stats["vertices"]
                man_meshes[asset_name]["triangles"] = stats["triangles"]
                man_meshes[asset_name]["fbx_bytes"] = stats["fbx_bytes"]
        man["stats_scanned_at"] = catalog["stats_scanned_at"]
        with open(MANIFEST, "w", encoding="utf-8") as f:
            json.dump(man, f, indent=2)
            f.write("\n")
        log(f"manifest -> {MANIFEST}")

    os.makedirs(os.path.dirname(AUDIT), exist_ok=True)
    with open(AUDIT, "w", encoding="utf-8") as f:
        json.dump(
            {
                "scanned_at": catalog["stats_scanned_at"],
                "meshes": results,
            },
            f,
            indent=2,
        )
    log(f"audit -> {AUDIT} ({len(results)} meshes)")
    clear()


if __name__ == "__main__":
    main()
