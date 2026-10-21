#!/usr/bin/env python
"""Restore the Poitou mesh material bindings to their pre-session state.

Run headlessly (no editor GUI, no GPU):

    UnrealEditor-Cmd.exe BS_GodFile.uproject -run=pythonscript \
        -script=".../poitou_restore_mesh_bindings.py" -unattended -nopause \
        -nosplash -nullrhi -stdout -FullStdOutLogOutput

Why this exists
---------------
On 2026-10-21 a session bound in-theme materials to 18 existing Poitou mesh
packages (and grew five of them to two static material slots) while the
level L_Poitou_v2 was live.  The level's Poitou_Layout_v6 Houdini cook then
finished "with errors" and the level produced nothing.

The pre-session state of those 18 meshes is not a matter of judgement: it
was MEASURED at 18:34, before any of the changes, and written to
Saved/Audit/PoitouConvergence_20261020/poitou_mesh_slots.json - every
mesh, its slot count, and its slot-0 material.  This script restores
exactly that record and nothing else:

  * slot 0 -> the recorded original material;
  * the static_materials array -> the recorded slot count.

It does NOT invent a binding, does NOT create a material, and does NOT
touch anything the snapshot does not name.  It is a restore, not a change.

Do not use `p4 revert` on these meshes: they are open for ADD in Perforce
(they were created locally on 2026-10-20 and never submitted), so a revert
would DELETE them.

Writes Saved/Audit/PoitouConvergence_20261020/mesh_binding_restore.json.
"""
from __future__ import annotations

import json
import os

import unreal

EAL = unreal.EditorAssetLibrary
REPO = os.environ.get("MELODIA_POITOU_REPO", r"C:\EnvironmentPortfolio\BS_GodFile")
OUT_DIR = os.path.join(REPO, "Saved", "Audit", "PoitouConvergence_20261020")
SNAPSHOT = os.path.join(OUT_DIR, "poitou_mesh_slots.json")
RECEIPT = os.path.join(OUT_DIR, "mesh_binding_restore.json")
CLAY = "/Game/EnvSandbox/Poitou/House/Clay/"


def resolve_material(recorded):
    """The recorded value is a full path for project assets and a bare name
    for the engine default."""
    cands = [recorded]
    if recorded.startswith("WorldGridMaterial"):
        cands = ["/Engine/BasicShapes/WorldGridMaterial.WorldGridMaterial",
                 "/Engine/EngineMaterials/WorldGridMaterial.WorldGridMaterial"]
    for c in cands:
        m = unreal.load_asset(c)
        if m is not None:
            return m, c
    return None, None


def main():
    if not os.path.isfile(SNAPSHOT):
        unreal.log_error("[restore] no snapshot at %s - refusing to guess" % SNAPSHOT)
        return 2
    snap = json.load(open(SNAPSHOT, encoding="utf-8"))
    rows = []
    for name, rec in snap.items():
        want_slots = len(rec["slots"])
        want_mat = rec["slots"][0]["material"] if rec["slots"] else None
        path = "/Game/Melodia/Meshes/Poitou/%s" % name
        if name == "SM_Melusina_ClayHouse_v07":
            path = CLAY + name
        mesh = unreal.load_asset(path)
        if mesh is None:
            rows.append({"mesh": name, "status": "MESH-MISSING"})
            unreal.log("[restore] %-42s MESH MISSING" % name)
            continue
        mat, used = resolve_material(want_mat or "")
        if mat is None:
            rows.append({"mesh": name, "status": "MATERIAL-MISSING", "wanted": want_mat})
            unreal.log("[restore] %-42s MATERIAL MISSING %s" % (name, want_mat))
            continue
        cur = list(mesh.get_editor_property("static_materials"))
        before = [s.get_editor_property("material_interface").get_path_name()
                  if s.get_editor_property("material_interface") else None for s in cur]
        keep = cur[0]
        keep.set_editor_property("material_interface", mat)
        # the exact recorded slot count: one slot for every mesh in this
        # snapshot, but honour the record rather than assuming it
        mesh.set_editor_property("static_materials", [keep][:want_slots])
        EAL.save_loaded_asset(mesh, only_if_is_dirty=False)
        after = [s.get_editor_property("material_interface").get_path_name()
                 if s.get_editor_property("material_interface") else None
                 for s in mesh.get_editor_property("static_materials")]
        ok = len(after) == want_slots and (not after or after[0] == used)
        rows.append({"mesh": name, "status": "RESTORED" if ok else "MISMATCH",
                     "before": before, "after": after, "wanted": want_mat})
        unreal.log("[restore] %-42s %s %s -> %s" % (name, "OK " if ok else "!! ", before, after))
    out = {"snapshot": SNAPSHOT, "rows": rows,
           "restored": sum(1 for r in rows if r["status"] == "RESTORED"),
           "failed": sum(1 for r in rows if r["status"] != "RESTORED")}
    os.makedirs(OUT_DIR, exist_ok=True)
    with open(RECEIPT, "w", encoding="utf-8") as fh:
        json.dump(out, fh, indent=1, default=str)
    unreal.log("[restore] %d restored, %d failed - receipt %s" % (out["restored"], out["failed"], RECEIPT))


main()
