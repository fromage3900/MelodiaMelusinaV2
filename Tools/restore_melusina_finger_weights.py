#!/usr/bin/env python3
"""Restore finger weights onto the ARP controller bones, undoing the *_ref remap.

WHY THIS EXISTS
---------------
`fix_melusina_skin_bindings.py` moved finger weights from `c_<finger>N.<s>` onto
`<finger>N_ref.<s>`. That was correct for the Unreal export -- the contract's
`bone_map` renames `index2_ref_l` into `index2_l`, which the retarget's LeftIndex
chain (`index1_l -> index3_l`) actually drives -- but it is WRONG for Blender.

`*_ref` bones are Auto-Rig Pro reference bones. They carry no constraints and do not
move when the rig is posed. Binding geometry to them means the fingers stop deforming
in Blender, which is exactly what the remap caused.

The two requirements genuinely conflict:
  Blender authoring needs the weights on `c_index2.l` (deform, constraint-driven).
  Unreal needs them on a bone that the retarget chain drives.

Weights cannot satisfy both. So the export-side problem is fixed on the export side --
by correcting the parent of `c_index2_l` in the contract hierarchy so it is no longer
orphaned to `root` -- and the stage keeps the weights ARP expects.

This script restores the stage. It does not touch the eye fix, which is safe in both
contexts: `DEF_eye.L/.R` are real deform bones already parented under `head.x`, so
they animate correctly in Blender and export correctly to Unreal.

USAGE
-----
    blender --background --factory-startup <stage>.blend \
        --python Tools/restore_melusina_finger_weights.py -- \
        --backup-dir G:/EnvironmentPortfolio/BS_GodFile --apply --save-as <out>.blend

Dry-run by default. Refuses if a backup is missing or a vertex would end up unweighted.
"""

from __future__ import annotations

import json
import os
import sys

import bpy

MESHES = ("simply_coll", "Melusina_Gloves", "Melusina_Sleeve")
FINGERS = [f"c_{f}{n}.{s}"
           for f in ("index", "middle", "ring", "pinky", "thumb")
           for n in (2, 3) for s in ("l", "r")]
REF_OF = {b: b[2:].replace(".", "_ref.") for b in FINGERS}


def args() -> list[str]:
    return sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []


def opt(name: str, default=None):
    a = args()
    return a[a.index(name) + 1] if name in a and a.index(name) + 1 < len(a) else default


def main() -> int:
    apply = "--apply" in args()
    bdir = opt("--backup-dir", os.path.dirname(bpy.data.filepath) or ".")
    save_as = opt("--save-as")

    plans = []
    problems = []

    for mesh in MESHES:
        ob = bpy.data.objects.get(mesh)
        if not ob:
            problems.append(f"missing mesh '{mesh}'")
            continue
        path = os.path.join(bdir, f"melusina_bind_backup_fingers_{mesh}.json")
        if not os.path.isfile(path):
            problems.append(f"missing backup {path}")
            continue
        groups = json.load(open(path, encoding="utf-8"))["groups"]
        plans.append((ob, {g: {int(i): w for i, w in v.items()} for g, v in groups.items()}))
        print(f"{mesh:<18} backup carries {len(groups)} groups / "
              f"{sum(len(v) for v in groups.values())} weights")

    if problems:
        print("\nABORT:")
        for p in problems:
            print(f"  - {p}")
        return 1

    if not apply:
        print("\nDRY RUN. Nothing written. Re-run with '-- --apply'.")
        return 0

    for ob, groups in plans:
        have = {g.name for g in ob.vertex_groups}
        restored = 0
        for src, weights in groups.items():
            if src not in have:
                ob.vertex_groups.new(name=src)
                have.add(src)
            tgt = ob.vertex_groups[src]
            for vi, w in weights.items():
                tgt.add([vi], w, "REPLACE")
            restored += len(weights)
            # strip whatever the remap put on the ref bone
            ref = REF_OF.get(src)
            if ref and ref in have:
                ob.vertex_groups[ref].remove(sorted(weights))
        print(f"  {ob.name}: restored {restored} weights onto c_* controllers")

    # Undo the deform flag the remap set; ARP reference bones must stay non-deforming.
    rig = bpy.data.objects.get("character_rig")
    cleared = 0
    if rig:
        for ref in set(REF_OF.values()):
            b = rig.data.bones.get(ref)
            if b and b.use_deform:
                b.use_deform = False
                cleared += 1
    print(f"  cleared use_deform on {cleared} ref bones")

    if save_as:
        bpy.ops.wm.save_as_mainfile(filepath=save_as, copy=True, compress=False)
        print(f"\nsaved: {save_as}")
    else:
        print("\nNOT saved. Pass '--save-as <path>'.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
