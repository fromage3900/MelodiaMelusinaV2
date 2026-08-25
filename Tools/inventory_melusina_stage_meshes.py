# -*- coding: utf-8 -*-
"""Inventory Melusina meshes on the Portfolio Stage (read-only classify + optional Wardrobe_* ensure).

Run:
  blender KitbashExport/Melodia_Portfolio_Stage_v4.blend -b -P Tools/inventory_melusina_stage_meshes.py
  blender ... -P Tools/inventory_melusina_stage_meshes.py -- --ensure-wardrobe --save
  blender ... -P Tools/inventory_melusina_stage_meshes.py -- --no-open

Writes Saved/Audit/melusina_stage_mesh_inventory.json
"""
from __future__ import annotations

import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path

import bpy

TOOLS = Path(__file__).resolve().parent
if str(TOOLS) not in sys.path:
    sys.path.insert(0, str(TOOLS))

from melodia_stage_paths import (  # noqa: E402
    AUDIT_INVENTORY,
    MELUSINA_RIG_BLEND,
    resolve_stage_blend,
)


def log(msg: str) -> None:
    print(f"[mel-inv] {msg}", flush=True)


def _argv() -> list[str]:
    if "--" in sys.argv:
        return sys.argv[sys.argv.index("--") + 1 :]
    return []


def ensure_coll(name: str, parent: bpy.types.Collection | None = None) -> bpy.types.Collection:
    coll = bpy.data.collections.get(name)
    if coll is None:
        coll = bpy.data.collections.new(name)
        if parent is not None:
            parent.children.link(coll)
        else:
            bpy.context.scene.collection.children.link(coll)
    elif parent is not None and coll.name not in {c.name for c in parent.children}:
        try:
            parent.children.link(coll)
        except Exception:
            pass
    return coll


def ensure_wardrobe_collections() -> dict[str, str]:
    """Create empty Wardrobe_* contract collections (non-destructive)."""
    review = ensure_coll("Review_Queue")
    review.hide_render = False
    created = {}
    for name, hide in (
        ("Wardrobe_Base", True),
        ("Wardrobe_Accessories", True),
    ):
        coll = ensure_coll(name, parent=review)
        coll.hide_render = hide
        coll.hide_viewport = False
        created[name] = coll.name
        log(f"ensure {name} hide_render={hide}")
    return created


def classify_mesh(obj: bpy.types.Object) -> str:
    low = obj.name.lower()
    mats = [
        (s.material.name if s.material else "")
        for s in (obj.material_slots or [])
    ]
    mat_blob = " ".join(mats).lower()
    if "water (advance)" in mat_blob or "hair" in low or "strand" in low:
        return "hair"
    if any(k in low for k in ("cloth", "dress", "skirt", "sleeve", "shawl", "bow", "glove", "outfit")):
        return "dress_or_cloth"
    if any(k in low for k in ("veil", "sparkle", "ribbon", "fx_", "jewelry")):
        return "fx"
    if any(k in low for k in ("body", "melusina", "face", "skin", "sbw")):
        return "body"
    if obj.find_armature():
        return "skinned_other"
    return "other"


def mesh_row(obj: bpy.types.Object) -> dict:
    arm = obj.find_armature()
    mats = []
    for s in obj.material_slots:
        mats.append(s.material.name if s.material else None)
    vg = len(obj.vertex_groups) if obj.vertex_groups else 0
    verts = len(obj.data.vertices) if obj.data else 0
    return {
        "name": obj.name,
        "vertices": verts,
        "vertex_groups": vg,
        "materials": mats,
        "armature": arm.name if arm else None,
        "parent": obj.parent.name if obj.parent else None,
        "collections": [c.name for c in obj.users_collection],
        "class": classify_mesh(obj),
        "hide_render": bool(obj.hide_render),
    }


def collect_from_collection(coll_name: str) -> list[dict]:
    coll = bpy.data.collections.get(coll_name)
    if not coll:
        return []
    rows = []
    for o in coll.all_objects:
        if o.type == "MESH" and o.data:
            rows.append(mesh_row(o))
    return rows


def main() -> int:
    args = _argv()
    no_open = "--no-open" in args
    ensure_w = "--ensure-wardrobe" in args

    stage = resolve_stage_blend()
    if not no_open:
        cur = Path(bpy.data.filepath or "")
        if cur.resolve() != stage.resolve():
            if not stage.is_file():
                log(f"FATAL missing stage {stage}")
                return 2
            log(f"opening {stage}")
            bpy.ops.wm.open_mainfile(filepath=str(stage))

    wardrobe_ensured = {}
    if ensure_w:
        wardrobe_ensured = ensure_wardrobe_collections()

    mel_rows = collect_from_collection("Asset_melusina")
    fx_rows = collect_from_collection("FX_Hero")
    wardrobe_rows = []
    for name in sorted(c.name for c in bpy.data.collections if c.name.startswith("Wardrobe_")):
        wardrobe_rows.extend(collect_from_collection(name))

    by_class: dict[str, int] = {}
    for r in mel_rows:
        by_class[r["class"]] = by_class.get(r["class"], 0) + 1

    audit = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "generated_by": "inventory_melusina_stage_meshes.py",
        "stage_blend": str(Path(bpy.data.filepath or stage)),
        "rig_source_pin": str(MELUSINA_RIG_BLEND),
        "rig_source_exists": MELUSINA_RIG_BLEND.is_file(),
        "wardrobe_ensured": wardrobe_ensured,
        "counts": {
            "Asset_melusina_meshes": len(mel_rows),
            "FX_Hero_meshes": len(fx_rows),
            "Wardrobe_meshes": len(wardrobe_rows),
            "by_class": by_class,
        },
        "note": (
            "Clothes on UE SK_Melusina are mostly slot-baked on body. "
            "New outfits go in Wardrobe_<OutfitId>; do not put wardrobe under FX_Hero."
        ),
        "Asset_melusina": mel_rows,
        "FX_Hero": fx_rows,
        "Wardrobe": wardrobe_rows,
    }

    AUDIT_INVENTORY.parent.mkdir(parents=True, exist_ok=True)
    AUDIT_INVENTORY.write_text(json.dumps(audit, indent=2) + "\n", encoding="utf-8")
    log(f"wrote {AUDIT_INVENTORY}")
    log(f"Asset_melusina meshes={len(mel_rows)} classes={by_class}")

    if ensure_w and "--save" in args:
        out = Path(bpy.data.filepath or stage)
        bpy.ops.wm.save_as_mainfile(filepath=str(out))
        log(f"SAVED wardrobe collections -> {out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
