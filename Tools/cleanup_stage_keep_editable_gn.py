# -*- coding: utf-8 -*-
"""Purge old ornament review meshes; keep only editable GN collections.

*** DO NOT RUN ON LIVE STAGE WITHOUT ARTIST CONSENT ***
  Deletes review collections / ornament meshes.
  Honors Saved/Audit/MELUSINA_SHADER_AGENT_STOP.
  Never save Melodia_Portfolio_Stage_*.blend unless MELODIA_ALLOW_STAGE_SAVE=1.

Collections kept (rebuilt):
  OrnamentGN_Editable  — gothic fix-list (_edit_SM_Orn_*)
  MusicalGN_Editable   — full musical kitbash (_edit_SM_Orn_*)

Removed:
  MusicalOrnaments_Review / OrnamentFix_Review objects + empty collections
  Non-editable SM_Orn_* / _regen_* / review-prefixed ornament meshes
  _ref_* HandRemake overlays

Does NOT overwrite KitbashExport FBX.

Blender (preferred — live stage):
  exec(open(r'G:\\EnvironmentPortfolio\\BS_GodFile\\Tools\\cleanup_stage_keep_editable_gn.py').read())

Headless:
  blender KitbashExport/Melodia_Portfolio_Stage_v4.blend -b -P Tools/cleanup_stage_keep_editable_gn.py
"""
from __future__ import annotations

import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path

import bpy

ROOT = os.path.normpath(os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
STOP = Path(ROOT) / "Saved" / "Audit" / "MELUSINA_SHADER_AGENT_STOP"
AUDIT = os.path.join(ROOT, "Saved", "Audit", "cleanup_keep_editable_gn.json")
TOOLS = os.path.dirname(os.path.abspath(__file__))

KEEP_COLLECTIONS = ("OrnamentGN_Editable", "MusicalGN_Editable")
DELETE_COLLECTIONS = (
    "MusicalOrnaments_Review",
    "OrnamentFix_Review",
    "OrnamentSculptReview",
    "Ornament_Review",
    "Musical_Review",
)

# Object-name prefixes / exact stems that are old review / baked ornaments
REVIEW_PREFIXES = (
    "SM_Orn_",
    "_regen_",
    "_tmp_SM_Orn_",
    "_ref_SM_Orn_",
    "torus_knot_SM_Orn_",
    "filigree_ring_SM_Orn_",
    "crown_molding_SM_Orn_",
    "rose_window_SM_Orn_",
    "vault_ribs_SM_Orn_",
    "oculus_frame_SM_Orn_",
    "spiral_stair_SM_Orn_",
)


def log(msg: str) -> None:
    print(f"[keep-editable-gn] {msg}", flush=True)


def _in_keep_collection(obj: bpy.types.Object) -> bool:
    return any(c.name in KEEP_COLLECTIONS for c in obj.users_collection)


def _is_review_ornament(obj: bpy.types.Object) -> bool:
    if obj.name.startswith("_edit_SM_Orn_"):
        return False
    name = obj.name
    if name.startswith(REVIEW_PREFIXES):
        return True
    if "MelodyToken" in name and not name.startswith("_edit_"):
        return True
    return False


def delete_object(obj: bpy.types.Object) -> None:
    try:
        bpy.data.objects.remove(obj, do_unlink=True)
    except Exception as e:
        log(f"warn remove {obj.name}: {e}")


def purge_review_meshes() -> dict:
    deleted_objs: list[str] = []
    deleted_cols: list[str] = []

    # 1) Wipe known review collections (objects first)
    for cname in DELETE_COLLECTIONS:
        col = bpy.data.collections.get(cname)
        if col is None:
            continue
        for obj in list(col.objects):
            deleted_objs.append(obj.name)
            delete_object(obj)
        # Unlink from parents then remove collection
        for parent in list(bpy.data.collections):
            if col.name in parent.children:
                try:
                    parent.children.unlink(col)
                except Exception:
                    pass
        try:
            if col.name in bpy.context.scene.collection.children:
                bpy.context.scene.collection.children.unlink(col)
        except Exception:
            pass
        try:
            bpy.data.collections.remove(col)
            deleted_cols.append(cname)
        except Exception as e:
            log(f"warn remove col {cname}: {e}")

    # 2) Sweep scene for leftover non-editable ornament meshes
    for obj in list(bpy.data.objects):
        if not _is_review_ornament(obj):
            continue
        if _in_keep_collection(obj) and obj.name.startswith("_edit_"):
            continue
        deleted_objs.append(obj.name)
        delete_object(obj)

    # 3) Clear prior editable spawns (will be rebuilt)
    for obj in list(bpy.data.objects):
        if obj.name.startswith("_edit_SM_Orn_") or obj.name.startswith("_ref_SM_Orn_"):
            deleted_objs.append(obj.name)
            delete_object(obj)

    for cname in KEEP_COLLECTIONS:
        col = bpy.data.collections.get(cname)
        if col is None:
            continue
        for obj in list(col.objects):
            deleted_objs.append(obj.name)
            delete_object(obj)

    return {
        "deleted_objects": sorted(set(deleted_objs)),
        "deleted_collections": deleted_cols,
        "deleted_object_count": len(set(deleted_objs)),
    }


def isolate_editable_collections() -> list[str]:
    """DISABLED — isolation hid collections and made meshes untoggleable.

    Previously: hide_viewport/hide_render on non-essentials + sculpt_monetization preset.
    Do not re-enable without an explicit user request and a matching restore path.
    """
    log("isolate_editable_collections: skipped (disabled)")
    return []


def spawn_editable() -> dict:
    spawn_path = os.path.join(TOOLS, "spawn_editable_ornament_gn.py")
    if TOOLS not in sys.path:
        sys.path.insert(0, TOOLS)
    import importlib.util

    spec = importlib.util.spec_from_file_location("spawn_editable_ornament_gn", spawn_path)
    mod = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(mod)
    return mod.main()


def main(*, save: bool = True) -> dict:
    if STOP.is_file():
        msg = f"ABORT: {STOP} present — cleanup deletes review collections; blocked."
        log(msg)
        return {"ok": False, "error": "MELUSINA_SHADER_AGENT_STOP"}

    purge = purge_review_meshes()
    log(f"purged objects={purge['deleted_object_count']} cols={purge['deleted_collections']}")

    spawn = spawn_editable()
    # Do NOT isolate collections — that locked viewport toggles on the stage.
    shown = isolate_editable_collections()

    payload = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "filepath": bpy.data.filepath,
        "purge": purge,
        "spawn": {
            "ok_count": spawn.get("ok_count"),
            "fail_count": spawn.get("fail_count"),
            "collections": spawn.get("collections"),
        },
        "shown_collections": shown,
        "policy": "purge review + spawn editable GN; no collection isolation",
        "isolate_disabled": True,
    }
    os.makedirs(os.path.dirname(AUDIT), exist_ok=True)
    with open(AUDIT, "w", encoding="utf-8") as f:
        json.dump(payload, f, indent=2)

    fp = (bpy.data.filepath or "").replace("\\", "/").lower()
    is_stage = "melodia_portfolio_stage_" in fp and fp.endswith(".blend")
    allow = os.environ.get("MELODIA_ALLOW_STAGE_SAVE", "").strip() == "1"
    if save and bpy.data.filepath:
        if is_stage and not allow:
            payload["saved"] = None
            payload["save_refused"] = (
                "REFUSED stage save — set MELODIA_ALLOW_STAGE_SAVE=1 with artist consent"
            )
            log(payload["save_refused"])
        else:
            try:
                bpy.ops.wm.save_mainfile()
                payload["saved"] = bpy.data.filepath
                log(f"saved {bpy.data.filepath}")
            except Exception as e:
                alt = bpy.data.filepath.replace(".blend", "_EditableGN_Only.blend")
                try:
                    bpy.ops.wm.save_as_mainfile(filepath=alt, copy=True)
                    payload["saved"] = alt
                    log(f"saved copy {alt}")
                except Exception as e2:
                    payload["save_error"] = f"{e} / {e2}"
                    log(f"save failed: {e2}")

    log(json.dumps({"ok": spawn.get("ok_count"), "fail": spawn.get("fail_count"), "purged": purge["deleted_object_count"]}))
    return payload


if __name__ == "__main__":
    # Headless default: save=True but stage path still refused without MELODIA_ALLOW_STAGE_SAVE=1
    main(save=True)
