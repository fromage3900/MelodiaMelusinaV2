# -*- coding: utf-8 -*-
"""Populate the live stage's Review_Queue with the Cadence Cathedral kit.

Appends the kit pieces (with their live, editable melodia_gn modifier stacks)
from CadenceCathedral_Review_2026-08-11.blend into the Review_Queue collection
as one child collection per piece, plus the 126 m nave assembly as one queue
item — matching the Prev/Solo/Next cycle structure (child collections).

Run:
  MELODIA_ALLOW_STAGE_SAVE=1; blender "<stage>.blend" -b -P Tools/populate_cathedral_review_queue.py -- --save
Flags: --save (write blend) · --clear (remove prior RQ_Cathedral_* items first)
"""
from __future__ import annotations

import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path

import bpy

_TOOLS = Path(__file__).resolve().parent
ROOT = _TOOLS.parent
sys.path.insert(0, str(_TOOLS))
from melodia_stage_paths import stage_save_allowed  # noqa: E402

KIT_LIBRARY = ROOT / "KitbashExport" / "CadenceCathedral_Review_2026-08-11.blend"
RQ_NAME = "Review_Queue"
PREFIX = "RQ_Cathedral_"
NAVE_ITEM = "RQ_Cathedral_Nave_126m"
AUDIT = ROOT / "Saved" / "Audit" / "cathedral_review_queue_sync.json"
NAVE_PREFIXES = ("NAVE_", "PIER_", "BUTTRESS_", "FACADE_", "CROSSING_", "CORRIDOR_")


def log(msg: str) -> None:
    print(f"[cathedral-rq] {msg}", flush=True)


def ensure_collection(name: str, parent=None) -> bpy.types.Collection:
    col = bpy.data.collections.get(name)
    if col is None:
        col = bpy.data.collections.new(name)
        (parent or bpy.context.scene.collection).children.link(col)
    return col


def clear_prior() -> None:
    rq = bpy.data.collections.get(RQ_NAME)
    if rq is None:
        return
    for child in list(rq.children):
        if child.name.startswith(PREFIX):
            for obj in list(child.objects):
                bpy.data.objects.remove(obj, do_unlink=True)
            bpy.data.collections.remove(child)


def append_kit_objects() -> dict[str, bpy.types.Object]:
    if not KIT_LIBRARY.is_file():
        raise FileNotFoundError(f"kit library missing: {KIT_LIBRARY}")
    with bpy.data.libraries.load(str(KIT_LIBRARY), link=False) as (from_, to):
        to.objects = [name for name in from_.objects
                      if name.startswith("SM_Cathedral_") or name.startswith(NAVE_PREFIXES)]
    return {o.name: o for o in bpy.data.objects
            if o.name.startswith("SM_Cathedral_") or o.name.startswith(NAVE_PREFIXES)}


def move_to(obj: bpy.types.Object, col: bpy.types.Collection) -> None:
    for c in list(obj.users_collection):
        if c is not col:
            c.objects.unlink(obj)
    if obj.name not in col.objects:
        col.objects.link(obj)


def run(*, save: bool = False, clear: bool = False) -> dict:
    if save and not stage_save_allowed():
        raise RuntimeError("stage save requires MELODIA_ALLOW_STAGE_SAVE=1")
    if clear:
        clear_prior()

    rq = ensure_collection(RQ_NAME)
    objs = append_kit_objects()
    if not objs:
        raise RuntimeError("no kit objects appended")

    placed, reused, skipped = [], [], []
    for name in sorted(objs):
        if name.startswith(NAVE_PREFIXES):
            continue
        col_name = PREFIX + name
        col = bpy.data.collections.get(col_name)
        if col is not None and any(o.type == "MESH" for o in col.objects):
            reused.append(col_name)
            continue
        col = ensure_collection(col_name, parent=rq)
        obj = objs[name]
        obj.hide_viewport = False
        obj.hide_render = False
        move_to(obj, col)
        placed.append(col_name)
        log(f"queued {col_name}")

    nave = bpy.data.collections.get(NAVE_ITEM)
    if nave is not None and any(o.type == "MESH" for o in nave.objects):
        reused.append(NAVE_ITEM)
    else:
        nave = ensure_collection(NAVE_ITEM, parent=rq)
        for name in sorted(objs):
            if name.startswith(NAVE_PREFIXES):
                obj = objs[name]
                obj.hide_viewport = False
                obj.hide_render = False
                move_to(obj, nave)
        placed.append(NAVE_ITEM)
        log(f"queued {NAVE_ITEM}")

    try:
        bpy.context.scene.surreal_arch_review_queue_index = 0
    except Exception:
        pass

    summary = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "stage": bpy.data.filepath,
        "library": str(KIT_LIBRARY),
        "placed": placed,
        "reused": reused,
        "skipped": skipped,
        "queue_total": len(placed) + len(reused),
    }
    AUDIT.parent.mkdir(parents=True, exist_ok=True)
    AUDIT.write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")
    log(f"audit → {AUDIT} placed={len(placed)} reused={len(reused)}")

    if save:
        bpy.ops.wm.save_mainfile()
        log("saved stage blend")
    return summary


def _parse_flags(argv: list[str]) -> dict:
    if "--" in argv:
        argv = argv[argv.index("--") + 1:]
    return {"save": "--save" in argv, "clear": "--clear" in argv}


if __name__ == "__main__":
    flags = _parse_flags(sys.argv)
    run(**flags)
