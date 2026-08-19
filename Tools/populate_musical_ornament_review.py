# -*- coding: utf-8 -*-
"""Import musical ornament FBXs into Melodia Portfolio Stage v4 for review.

Creates empty `MusicalOrnaments_Review` (Lane B — not Wardrobe_*) and places
the 7 SM_Orn_* meshes in a shrine-rail grid.

Run:
  blender KitbashExport/Melodia_Portfolio_Stage_v4.blend -b -P Tools/populate_musical_ornament_review.py -- --save
  blender ... -P Tools/populate_musical_ornament_review.py -- --save --clear
"""
from __future__ import annotations

import json
import math
import sys
from datetime import datetime, timezone
from pathlib import Path

import bpy

_TOOLS = Path(__file__).resolve().parent
ROOT = _TOOLS.parent
sys.path.insert(0, str(_TOOLS))
sys.path.insert(0, str(ROOT / "Content" / "Python"))

from melodia_stage_paths import resolve_stage_blend  # noqa: E402

try:
    from musical_ornament_kitbash_catalog import FBX_EXPORT_DIR, MESHES, mesh_names
except ImportError:
    FBX_EXPORT_DIR = ROOT / "KitbashExport" / "MusicalOrnamentalMeshes"
    MESHES = ()
    def mesh_names():
        return [p.stem for p in FBX_EXPORT_DIR.glob("SM_Orn_*.fbx")]

PARENT_NAME = "MusicalOrnaments_Review"
AUDIT = ROOT / "Saved" / "Audit" / "musical_ornament_stage_populate.json"
SPACING = 2.4


def log(msg: str) -> None:
    print(f"[musical-stage] {msg}", flush=True)


def ensure_collection(name: str) -> bpy.types.Collection:
    col = bpy.data.collections.get(name)
    if col is None:
        col = bpy.data.collections.new(name)
        bpy.context.scene.collection.children.link(col)
    return col


def ensure_parent() -> bpy.types.Object:
    obj = bpy.data.objects.get(PARENT_NAME)
    if obj is None:
        bpy.ops.object.empty_add(type="PLAIN_AXES", location=(0, 0, 0))
        obj = bpy.context.active_object
        obj.name = PARENT_NAME
        obj.empty_display_size = 0.5
    col = ensure_collection(PARENT_NAME)
    if obj.name not in col.objects:
        # unlink from other cols then link
        for c in list(obj.users_collection):
            c.objects.unlink(obj)
        col.objects.link(obj)
    return obj


def clear_children(parent: bpy.types.Object) -> None:
    for child in list(parent.children):
        bpy.data.objects.remove(child, do_unlink=True)
    # Also remove imported meshes that match our names under the collection
    col = bpy.data.collections.get(PARENT_NAME)
    if not col:
        return
    for o in list(col.objects):
        if o.name != PARENT_NAME and (o.name.startswith("SM_Orn_") or ".fbx" in o.name.lower()):
            bpy.data.objects.remove(o, do_unlink=True)


def import_fbx(path: Path) -> list[bpy.types.Object]:
    before = set(bpy.data.objects.keys())
    bpy.ops.import_scene.fbx(filepath=str(path), automatic_bone_orientation=True)
    after = set(bpy.data.objects.keys())
    new_names = after - before
    return [bpy.data.objects[n] for n in new_names if bpy.data.objects[n].type in {"MESH", "EMPTY"}]


def place_grid(parent: bpy.types.Object, objects: list[tuple[str, bpy.types.Object]]) -> None:
    n = max(len(objects), 1)
    cols = math.ceil(math.sqrt(n))
    col = ensure_collection(PARENT_NAME)
    for i, (stem, obj) in enumerate(objects):
        row, c = divmod(i, cols)
        obj.name = stem
        obj.parent = parent
        obj.location = (c * SPACING, -row * SPACING, 0.0)
        # Ensure in review collection
        for uc in list(obj.users_collection):
            uc.objects.unlink(obj)
        col.objects.link(obj)


def run(*, save: bool = False, clear: bool = False) -> dict:
    parent = ensure_parent()
    if clear:
        clear_children(parent)

    placed = []
    missing = []
    names = mesh_names() if callable(mesh_names) else list(mesh_names)
    if MESHES:
        names = [m.asset_name for m in MESHES]

    mesh_objs: list[tuple[str, bpy.types.Object]] = []
    for stem in names:
        fbx = FBX_EXPORT_DIR / f"{stem}.fbx"
        if not fbx.is_file():
            missing.append(stem)
            log(f"MISSING {fbx}")
            continue
        # Skip if already present as child
        existing = bpy.data.objects.get(stem)
        if existing and existing.parent == parent:
            mesh_objs.append((stem, existing))
            placed.append({"name": stem, "reused": True})
            continue
        imported = import_fbx(fbx)
        # Prefer mesh with most verts
        meshes = [o for o in imported if o.type == "MESH"]
        if not meshes:
            missing.append(stem)
            log(f"FAIL no mesh in {fbx.name}")
            continue
        meshes.sort(key=lambda o: len(o.data.vertices), reverse=True)
        main = meshes[0]
        # Remove extras
        for o in imported:
            if o != main:
                bpy.data.objects.remove(o, do_unlink=True)
        mesh_objs.append((stem, main))
        placed.append({"name": stem, "verts": len(main.data.vertices), "fbx": str(fbx)})
        log(f"OK {stem} verts={len(main.data.vertices)}")

    place_grid(parent, mesh_objs)

    summary = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "stage": str(resolve_stage_blend()),
        "parent": PARENT_NAME,
        "placed": placed,
        "missing": missing,
        "ok": len(missing) == 0 and len(placed) > 0,
        "subject_hint": "ornament:musical",
    }
    AUDIT.parent.mkdir(parents=True, exist_ok=True)
    AUDIT.write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")
    log(f"audit → {AUDIT} placed={len(placed)} missing={len(missing)}")

    if save:
        bpy.ops.wm.save_mainfile()
        log("saved blend")
    return summary


def _parse_flags(argv: list[str]) -> dict:
    # Support `blender ... -P script.py -- --save --clear`
    if "--" in argv:
        argv = argv[argv.index("--") + 1 :]
    return {
        "save": "--save" in argv or "--save-blend" in argv,
        "clear": "--clear" in argv,
    }


if __name__ == "__main__":
    flags = _parse_flags(sys.argv)
    run(**flags)
