#!/usr/bin/env python3
"""Re-bind Melusina's cornea section off the root-parented `eyes` bone.

THE DEFECT
----------
The 100-vertex eye/cornea section of the body mesh is skinned to the bone `eyes`:

    eyes -> MCH-eyes_parent -> (no parent)

`MCH-eyes_parent` is a Rigify eye-aim target that in Blender is driven by a CONSTRAINT
back to the head. Constraints do not survive FBX export, so in Unreal the bone is a
plain child of `root` -- a sibling of the whole spine:

    head_x -> neck_x -> spine_03_x -> spine_02_x -> spine_01_x -> root_x -> c_traj -> c_pos -> root
    eyes   -> MCH-eyes_parent -> root

At the reference pose everything is coincident, so a static capture looks perfect. As
soon as a clip animates `head_x`, the head moves and the eyes do not: the corneas
leave the skull. That is why the defect appears ONLY during animation, and why the
earlier iris material/UV remap did not fix it -- this was never a material bug.

Existing V1 mocap clips are immune because they were baked in Blender with constraints
evaluated and carry explicit keys on `eyes` (the audits measured 22 changing
deform/controller tracks on V1 vs 18 deform-only on a fresh retarget). Any newly
retargeted clip keys only the chained deform bones, so `eyes` is never written.

THE FIX
-------
Move those 100 vertices onto `DEF_eye.L` / `DEF_eye.R`, which already exist and are
already parented correctly into the head:

    DEF_eye.L -> MCH-eye.L -> master_eye.L -> ORG-face -> head.x -> c_head.x -> ...

This is a weight transfer only. It does not touch the skeleton, the retargeter, or any
animation, so V1 clips keep working -- and it makes the static-vs-animated discrepancy
structurally impossible rather than dependent on what a clip happens to key.

The left/right split is exact and is verified before anything is written: the mesh
carries `faceit_left_eyes_other` (50 verts) and `faceit_right_eyes_other` (50 verts),
whose union equals the `eyes` group with zero overlap. If that stops being true the
script refuses to run rather than guessing a midline.

USAGE
-----
    # inside Blender (Scripting tab), or headless:
    blender --background <stage>.blend --python Tools/fix_melusina_eye_weights.py
    blender --background <stage>.blend --python Tools/fix_melusina_eye_weights.py -- --apply

Dry-run by default: it reports what it would move and writes nothing.
`--apply` performs the transfer. The .blend is NEVER saved by this script -- saving
stays a human decision.
"""

from __future__ import annotations

import json
import os
import sys
from collections import defaultdict

import bpy

MESH = "simply_coll"
RIG = "character_rig"
SOURCE_GROUP = "eyes"
SIDE_GROUPS = {"DEF_eye.L": "faceit_left_eyes_other", "DEF_eye.R": "faceit_right_eyes_other"}
EXPECTED_VERTS = 100
BACKUP = "melusina_eye_weight_backup.json"


def argv_flag(name: str) -> bool:
    args = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
    return name in args


def bone_root(rig, name):
    """Top-most ancestor of a bone, or None when the bone is absent."""
    b = rig.data.bones.get(name)
    if not b:
        return None
    while b.parent:
        b = b.parent
    return b.name


def main() -> int:
    apply = argv_flag("--apply")

    ob = bpy.data.objects.get(MESH)
    rig = bpy.data.objects.get(RIG)
    if not ob or not rig:
        print(f"ABORT: need mesh '{MESH}' and armature '{RIG}' in the scene")
        return 2

    name_of = {g.index: g.name for g in ob.vertex_groups}
    wanted = {SOURCE_GROUP, *SIDE_GROUPS.values()}

    # ONE pass over the mesh. Re-walking 18891 verts per group is what wedged an
    # earlier interactive attempt.
    weights: dict[str, dict[int, float]] = defaultdict(dict)
    for v in ob.data.vertices:
        for g in v.groups:
            n = name_of.get(g.group)
            if n in wanted and g.weight > 1e-6:
                weights[n][v.index] = g.weight

    src = weights.get(SOURCE_GROUP, {})
    if not src:
        print(f"Nothing to do: '{SOURCE_GROUP}' carries no weight (already fixed?).")
        return 0

    sides = {tgt: set(weights.get(grp, {})) for tgt, grp in SIDE_GROUPS.items()}
    left, right = sides["DEF_eye.L"], sides["DEF_eye.R"]

    # Refuse to guess. An inexact split would silently bind half a cornea to the
    # wrong eye, which is harder to spot than the bug being fixed.
    problems = []
    if set(src) != (left | right):
        problems.append(f"side groups do not cover '{SOURCE_GROUP}' exactly "
                        f"({len(src)} verts vs {len(left | right)} covered)")
    if left & right:
        problems.append(f"{len(left & right)} verts claimed by BOTH sides")
    if len(src) != EXPECTED_VERTS:
        problems.append(f"expected {EXPECTED_VERTS} verts, found {len(src)}")
    for tgt in SIDE_GROUPS:
        if not rig.data.bones.get(tgt):
            problems.append(f"target bone '{tgt}' missing from '{RIG}'")

    print(f"mesh              : {MESH} ({len(ob.data.vertices)} verts)")
    print(f"source group      : {SOURCE_GROUP} -> {len(src)} verts, "
          f"root ancestor '{bone_root(rig, SOURCE_GROUP)}'")
    for tgt in SIDE_GROUPS:
        print(f"target            : {tgt} <- {len(sides[tgt])} verts, "
              f"root ancestor '{bone_root(rig, tgt)}'")

    if problems:
        print("\nABORT -- preconditions failed:")
        for p in problems:
            print(f"  - {p}")
        return 1

    if not apply:
        print("\nDRY RUN. Nothing written. Re-run with '-- --apply' to perform the transfer.")
        return 0

    path = os.path.join(bpy.path.abspath("//") or os.getcwd(), BACKUP)
    with open(path, "w", encoding="utf-8") as fh:
        json.dump({"mesh": MESH, "source_group": SOURCE_GROUP,
                   "weights": {str(k): v for k, v in src.items()},
                   "left": sorted(left), "right": sorted(right)}, fh, indent=1)
    print(f"\nbackup written    : {path}")

    vgs = ob.vertex_groups
    for tgt in SIDE_GROUPS:
        if tgt not in {g.name for g in vgs}:
            vgs.new(name=tgt)
    idx = {g.name: g for g in vgs}

    for tgt, verts in sides.items():
        grp = idx[tgt]
        for vi in sorted(verts):
            grp.add([vi], src[vi], "REPLACE")
    idx[SOURCE_GROUP].remove(sorted(src))

    print(f"moved             : {len(left)} verts -> DEF_eye.L, {len(right)} verts -> DEF_eye.R")
    print(f"cleared           : {SOURCE_GROUP}")

    # Write to a NEW file by default. The stage is routinely open in an interactive
    # Blender, and saving over it from a headless run would race that session.
    save_as = None
    args = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
    if "--save-as" in args:
        save_as = args[args.index("--save-as") + 1]
    if save_as:
        bpy.ops.wm.save_as_mainfile(filepath=save_as, copy=True)
        print(f"saved copy        : {save_as}")
    else:
        print("\nThe .blend was NOT saved. Pass '--save-as <path>' or save from the GUI, "
              "then re-export the body FBX and reimport.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
