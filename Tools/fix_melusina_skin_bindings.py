#!/usr/bin/env python3
"""Re-bind Melusina's geometry off root-parented bones onto the correctly parented ones.

THE DEFECT
----------
Two groups of geometry are skinned to bones that are NOT descendants of the pelvis
(`root_x`), so they only move when an animation explicitly keys them:

  eyes       -> MCH-eyes_parent -> root      (100-vert cornea section)
  c_index2_l -> root                         (finger phalanges 2 and 3, 20 bones)

In Blender these follow the body through CONSTRAINTS (`MCH-eyes_parent` has a
COPY_TRANSFORMS to `ORG-face`). Constraints do not survive FBX export, and
`Tools/bind_melusina_v2_pieces.py::apply_canonical_hierarchy` then re-parents every
bone verbatim from `specs/anim_presets/melusina_contract_hierarchy.json`, which
records 69 bones parented to `root` -- because that map was harvested from the
already-broken live UE skeleton. The export faithfully reproduces the defect.

At the reference pose everything is coincident, so static captures look perfect. The
moment a clip animates `head_x` the head moves and the corneas stay behind. Old V1
mocap masked this for months because it was baked in Blender with constraints
evaluated and therefore keys all 465 bones; a fresh retarget keys only the 19 chained
deform bones.

WHY RE-BIND RATHER THAN RE-PARENT
---------------------------------
Correcting `parent_map` would change each bone's parent space, which would break every
existing V1 clip keyed against the current hierarchy. Re-binding the geometry to bones
that are ALREADY correctly parented changes no skeleton at all, so V1 clips keep
working. This also reproduces the scheme of the original `SK_Melusina` body, whose
iris meshes are weighted to `DEF_eye.L`/`DEF_eye.R` and which animates correctly today.

THE MAPPING
-----------
  eyes            -> DEF_eye.L / DEF_eye.R     (split by the faceit side groups)
  c_<finger><N>.<s> -> <finger><N>_ref.<s>     (20 bones)

Every pair was verified coincident to < 0.01 cm before this script was written, and the
check is re-run at runtime. `*_ref` bones are what `bone_map` renames into Unreal's
correctly-chained deform family (`index2_ref_l -> index2_l -> index1_l -> hand_l`).

SAFETY
------
Dry-run by default. Refuses on any precondition failure rather than guessing. Writes a
per-mesh weight backup before mutating. Never saves over the input; use `--save-as`.
Runs headless deliberately -- driving this through the GUI bridge OOM'd Blender at 35 GB
because touching the active object rebuilds the depsgraph on an 879-object scene.

USAGE
-----
    blender --background <stage>.blend --python Tools/fix_melusina_skin_bindings.py
    blender --background <stage>.blend --python Tools/fix_melusina_skin_bindings.py -- \
        --apply --save-as G:/path/out.blend
"""

from __future__ import annotations

import json
import os
import sys

import bpy

RIG = "character_rig"

# Body only: the cornea section lives on the V2 body mesh.
EYE_MESH = "simply_coll"
EYE_SRC = "eyes"
EYE_SIDES = {"DEF_eye.L": "faceit_left_eyes_other", "DEF_eye.R": "faceit_right_eyes_other"}
EYE_EXPECTED = 100

# The V2 export set only. `Melusina.001` is the original body -- it is NOT part of the
# V2 export and is the known-good animation reference, so it is deliberately excluded.
FINGER_MESHES = ("simply_coll", "Melusina_Gloves", "Melusina_Sleeve")
FINGERS = [f"c_{f}{n}.{s}"
           for f in ("index", "middle", "ring", "pinky", "thumb")
           for n in (2, 3) for s in ("l", "r")]
FINGER_MAP = {b: b[2:].replace(".", "_ref.") for b in FINGERS}
COINCIDENT_TOL_CM = 0.01


def args() -> list[str]:
    return sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []


def opt(name: str, default=None):
    a = args()
    return a[a.index(name) + 1] if name in a and a.index(name) + 1 < len(a) else default


def read_groups(ob, wanted: set[str]) -> dict[str, dict[int, float]]:
    """Single pass. Re-walking a mesh per group is what made the interactive attempt hang."""
    name_of = {g.index: g.name for g in ob.vertex_groups}
    out: dict[str, dict[int, float]] = {n: {} for n in wanted}
    for v in ob.data.vertices:
        for g in v.groups:
            n = name_of.get(g.group)
            if n in out and g.weight > 1e-6:
                out[n][v.index] = g.weight
    return out


def backup(payload: dict, tag: str) -> str:
    path = os.path.join(bpy.path.abspath("//") or os.getcwd(), f"melusina_bind_backup_{tag}.json")
    with open(path, "w", encoding="utf-8") as fh:
        json.dump(payload, fh)
    return path


def move(ob, src_name: str, dst_name: str, weights: dict[int, float], mode: str) -> int:
    have = {g.name for g in ob.vertex_groups}
    if dst_name not in have:
        ob.vertex_groups.new(name=dst_name)
    tgt = ob.vertex_groups[dst_name]
    for vi, w in weights.items():
        tgt.add([vi], w, mode)
    ob.vertex_groups[src_name].remove(sorted(weights))
    return len(weights)


def main() -> int:
    apply = "--apply" in args()
    save_as = opt("--save-as")

    rig = bpy.data.objects.get(RIG)
    if not rig:
        print(f"ABORT: no armature '{RIG}'")
        return 2

    problems: list[str] = []

    # --- preconditions: every mapped pair must be coincident -----------------
    for s, d in FINGER_MAP.items():
        a, b = rig.data.bones.get(s), rig.data.bones.get(d)
        if not a or not b:
            problems.append(f"missing bone pair {s} -> {d}")
            continue
        cm = (a.head_local - b.head_local).length * 100.0
        if cm > COINCIDENT_TOL_CM:
            problems.append(f"{s} -> {d} is {cm:.3f} cm apart (> {COINCIDENT_TOL_CM})")
    for d in EYE_SIDES:
        if not rig.data.bones.get(d):
            problems.append(f"missing eye target bone {d}")

    # --- eyes -----------------------------------------------------------------
    eye_ob = bpy.data.objects.get(EYE_MESH)
    eye_w: dict[str, dict[int, float]] = {}
    if not eye_ob:
        problems.append(f"missing mesh '{EYE_MESH}'")
    else:
        eye_w = read_groups(eye_ob, {EYE_SRC, *EYE_SIDES.values()})
        src = eye_w[EYE_SRC]
        if src:
            left, right = set(eye_w[EYE_SIDES["DEF_eye.L"]]), set(eye_w[EYE_SIDES["DEF_eye.R"]])
            if set(src) != (left | right):
                problems.append("faceit side groups do not cover 'eyes' exactly")
            if left & right:
                problems.append(f"{len(left & right)} eye verts claimed by both sides")
            if len(src) != EYE_EXPECTED:
                problems.append(f"expected {EYE_EXPECTED} eye verts, found {len(src)}")

    # --- fingers --------------------------------------------------------------
    finger_w: dict[str, dict[str, dict[int, float]]] = {}
    for m in FINGER_MESHES:
        ob = bpy.data.objects.get(m)
        if not ob:
            problems.append(f"missing mesh '{m}'")
            continue
        finger_w[m] = read_groups(ob, set(FINGERS))

    eye_todo = len(eye_w.get(EYE_SRC, {}))
    fing_todo = {m: sum(len(v) for v in w.values()) for m, w in finger_w.items()}

    print(f"eyes on '{EYE_SRC}'      : {eye_todo} verts")
    for m, n in fing_todo.items():
        print(f"finger weights {m:<18}: {n}")

    if problems:
        print("\nABORT -- preconditions failed:")
        for p in problems:
            print(f"  - {p}")
        return 1

    if not (eye_todo or any(fing_todo.values())):
        print("\nNothing to do -- already re-bound.")
        return 0

    if not apply:
        print("\nDRY RUN. Nothing written. Re-run with '-- --apply' to perform the re-bind.")
        return 0

    # --- mutate ---------------------------------------------------------------
    if eye_todo:
        src = eye_w[EYE_SRC]
        backup({"mesh": EYE_MESH, "group": EYE_SRC,
                "weights": {str(k): v for k, v in src.items()}}, "eyes")
        for tgt, faceit in EYE_SIDES.items():
            side = {vi: src[vi] for vi in eye_w[faceit] if vi in src}
            print(f"  eyes -> {tgt}: {move(eye_ob, EYE_SRC, tgt, side, 'REPLACE')}")

    for m, groups in finger_w.items():
        ob = bpy.data.objects[m]
        payload = {k: {str(i): w for i, w in v.items()} for k, v in groups.items() if v}
        if not payload:
            continue
        backup({"mesh": m, "groups": payload}, f"fingers_{m}")
        moved = sum(move(ob, s, FINGER_MAP[s], w, "ADD") for s, w in groups.items() if w)
        print(f"  {m}: moved {moved} finger weights")

    # `*_ref` bones are non-deforming by default. Set the flag on the armature DATA
    # directly -- do NOT touch the active object, which rebuilds the depsgraph and
    # OOM'd an 8 GB interactive session.
    flagged = 0
    for d in set(FINGER_MAP.values()):
        b = rig.data.bones.get(d)
        if b and not b.use_deform:
            b.use_deform = True
            flagged += 1
    print(f"  set use_deform on {flagged} ref bones")

    if save_as:
        bpy.ops.wm.save_as_mainfile(filepath=save_as, copy=True, compress=False)
        print(f"\nsaved copy: {save_as}")
    else:
        print("\nNOT saved. Pass '--save-as <path>'.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
