# -*- coding: utf-8 -*-
"""Melusina rig prep - FinalUERig43 (canonical).

Task 1: repair the 53 invalid shape-key drivers (FaceitControlRig was dropped
       from this rig; its c_* controls are the driver targets).
Task 2: weight audit + normalize + zero-weight group cleanup (no hand-painting).
Saves AS a new file (never overwrites the original). No FBX export.

Run:
  blender 5.2 --factory-startup -b -P Tools/melusina_rig_prep.py
"""
from __future__ import annotations

import json
import os
import sys
import traceback
from collections import Counter
from datetime import datetime, timezone

import bpy

ROOT = os.path.normpath(os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
AUDIT_DIR = os.path.join(ROOT, "Saved", "Audit")
RIG = r"G:\MelodiaMelusina\MelusinaFinalRig\FinalUERig43.blend"
REF = r"G:\MelodiaMelusina\MelusinaFinalRig\MelusinarigWithFaceUntextured.blend"
OUT = r"G:\MelodiaMelusina\MelusinaFinalRig\FinalUERig43_prep.blend"


def log(msg: str) -> None:
    print(f"[melusina-prep] {msg}", flush=True)


def write_json(name: str, payload: dict) -> str:
    path = os.path.join(AUDIT_DIR, name)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(payload, f, indent=2)
        f.write("\n")
    return path


def append_object(blend_path: str, obj_name: str):
    with bpy.data.libraries.load(blend_path, link=False) as (from_, to):
        to.objects = [obj_name]
    obj = bpy.data.objects.get(obj_name)
    if obj is None:
        raise RuntimeError(f"append failed: {obj_name} not present after load")
    return obj


def repoint_drivers(mesh_name: str, target_obj) -> dict:
    mesh = bpy.data.objects.get(mesh_name)
    if mesh is None or not mesh.data.shape_keys:
        return {"mesh": mesh_name, "error": "mesh or shape_keys missing"}
    sk = mesh.data.shape_keys
    fcurves = list(sk.animation_data.drivers) if sk.animation_data and sk.animation_data.drivers else []
    fixed = 0
    already = 0
    broken_bones = []
    for fcu in fcurves:
        if "key_blocks" not in fcu.data_path:
            continue
        drv = fcu.driver
        for v in drv.variables:
            for t in v.targets:
                if t.id is None:
                    t.id = target_obj
                    t.id_type = "OBJECT"
                    fixed += 1
                else:
                    already += 1
                if getattr(t, "bone_target", None):
                    if t.id and t.id.type == "ARMATURE":
                        if t.bone_target not in t.id.data.bones:
                            broken_bones.append(t.bone_target)
    valid_after = sum(1 for f in fcurves if getattr(f.driver, "is_valid", False))
    return {
        "mesh": mesh_name,
        "driver_fcurves": len(fcurves),
        "targets_repointed": fixed,
        "targets_already_set": already,
        "drivers_valid_after": valid_after,
        "missing_bones_still": sorted(set(broken_bones)),
    }


def weight_audit(mesh_name: str) -> dict:
    mesh = bpy.data.objects.get(mesh_name)
    me = mesh.data
    sums = Counter()
    over4 = 0
    group_stats = {}
    for v in me.vertices:
        n = len(v.groups)
        s = 0.0
        for g in v.groups:
            try:
                s += g.weight
            except Exception:
                pass
        if s == 0:
            sums["zero"] += 1
        elif s < 1:
            sums["under"] += 1
        elif s > 1:
            sums["over"] += 1
        else:
            sums["one"] += 1
        if n > 4:
            over4 += 1
    for vg in me.vertex_groups:
        cnt = 0
        for v in me.vertices:
            if vg.index in [g.group for g in v.groups] and any(
                abs(g.weight) > 1e-6 for g in v.groups if g.group == vg.index
            ):
                cnt += 1
        group_stats[vg.name] = cnt
    return {
        "mesh": mesh_name,
        "verts": len(me.vertices),
        "group_count": len(me.vertex_groups),
        "sum_histogram": dict(sums),
        "verts_over_4_influences": over4,
        "empty_groups": [k for k, v in group_stats.items() if v == 0],
        "def_group_coverage": {k: v for k, v in group_stats.items() if k.startswith("DEF") or k.startswith("def")},
    }


def normalize_weights(mesh_name: str) -> int:
    mesh = bpy.data.objects.get(mesh_name)
    me = mesh.data
    changed = 0
    for v in me.vertices:
        total = sum(g.weight for g in v.groups)
        if abs(total - 1.0) > 1e-4 and total > 0:
            for g in v.groups:
                g.weight = g.weight / total
            changed += 1
    return changed


def remove_empty_groups(mesh_name: str) -> int:
    mesh = bpy.data.objects.get(mesh_name)
    me = mesh.data
    removed = 0
    for vg in list(me.vertex_groups):
        used = False
        for v in me.vertices:
            if vg.index in [g.group for g in v.groups] and any(
                abs(g.weight) > 1e-6 for g in v.groups if g.group == vg.index
            ):
                used = True
                break
        if not used:
            me.vertex_groups.remove(vg)
            removed += 1
    return removed


def main() -> int:
    report = {"generated_at": datetime.now(timezone.utc).isoformat(), "source": RIG}
    bpy.ops.wm.open_mainfile(filepath=RIG)
    log("opened rig")

    faceit = None
    try:
        faceit = append_object(REF, "FaceitControlRig")
        log(f"FaceitControlRig appended: {len(faceit.data.bones)} bones, {len(faceit.keys())} props")
        report["faceit_append"] = {"ok": True, "bones": len(faceit.data.bones),
                                   "props": len(faceit.keys()),
                                   "has_eyelid_ctrl": "c_eyelid_upper.L" in faceit.data.bones}
    except Exception as exc:
        log(f"FaceitControlRig append FAILED: {exc}")
        report["faceit_append"] = {"ok": False, "error": str(exc)}

    if faceit is not None:
        try:
            report["driver_repair"] = repoint_drivers("Melusina", faceit)
            log(f"drivers repaired: {report['driver_repair']}")
        except Exception as exc:
            log(f"driver repair FAILED: {exc}")
            report["driver_repair"] = {"ok": False, "error": str(exc)}

    try:
        report["weight_before"] = weight_audit("Melusina")
        norm = normalize_weights("Melusina")
        removed = remove_empty_groups("Melusina")
        report["weight_after"] = weight_audit("Melusina")
        report["normalize"] = {"verts_changed": norm, "empty_groups_removed": removed}
        log(f"weights normalized ({norm} verts), {removed} empty groups removed")
    except Exception as exc:
        log(f"weight pass FAILED: {exc}")
        report["weight_pass_error"] = str(exc)

    try:
        bpy.ops.wm.save_as_mainfile(filepath=OUT, copy=True)
        report["saved_as"] = OUT
        log(f"saved {OUT}")
    except Exception as exc:
        log(f"save FAILED: {exc}")
        report["save_error"] = str(exc)

    path = write_json("melusina_rig_prep_report.json", report)
    log(f"report -> {path}")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception:
        log(traceback.format_exc())
        raise
