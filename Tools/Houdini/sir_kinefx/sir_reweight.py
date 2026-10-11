"""Sir Melodious body reweight (staging only, no Content/ write, no reimport).

Root cause found 2026-10-07: the tail IS rigged in the source blend — ARP
spline chain `c_spline_root.x -> spline_01/02/03.x -> spline_stretch.x ->
c_spline_tip.x` plus ARP B-bones `bbones_01..04.x` (weighted in
`sirmelodious_BézierCurve.002`). But in the v5 UE export every spline/bbone is
non-deform and absent from the 66-bone set, so the tail has no deforming bone
in UE. Separately, 654 body verts are weighted ONLY to `c_root_bend.x`
(an ARP bend helper that also does not export), so they ship with zero
weights and freeze at bind pose.

This script fixes the second defect (the unweighted verts) by binding each
unweighted vertex to the weights of its nearest already-weighted neighbours,
top-4 clamped and renormalised. It does NOT delete anything, does NOT touch
Content/, and does NOT reimport a mesh. Outputs a staged fixed copy + a
per-vertex weight delta JSON + a manifest for owner review.

  blender --background --python Tools/Houdini/sir_kinefx/sir_reweight.py
"""
import bpy
import json
import math

from mathutils import Vector

SRC_BLEND = r"G:\EnvironmentPortfolio\BS_GodFile\Saved\Audit\SirMelodious_FlightUnit_20261003\arp\SirMelodious_ARP_CrestTie_v5.blend"
EXP_FBX = r"C:\EnvironmentPortfolio\BS_GodFile\Saved\Audit\SirMelodious_FlightUnit_20261003\exports\ue_arp\SKM_SirMelodious_ARP_CrestTie_v5.fbx"
OUT_DIR = r"C:\EnvironmentPortfolio\BS_GodFile\Saved\Audit\sirmelodious_kinefx_doctor\reweight"
MAX_INFLUENCES = 4

# Source ARP helper/bend groups that do NOT survive the v5 export, mapped to
# their nearest exported deform equivalent. Verified 2026-10-07: the body's
# tail/rear verts are weighted ONLY to c_root_bend.x (+ unit groups), and
# c_root_bend.x is absent from the 66-bone export, so they ship unweighted.
# root.x is the exported root (spike centroid sits 0.174 from root.x head).
HELPER_MAP = {
    "c_root_bend.x": "root.x",
    "c_spine_01_bend.x": "spine_01.x",
    "c_spine_02_bend.x": "spine_02.x",
    "c_waist_bend.x": "spine_01.x",
}
UNIT_GROUPS = {"Group", "Group.001", "featherdirectionj"}

import os
os.makedirs(OUT_DIR, exist_ok=True)

# --- pass 1: source blend, gather per-vertex SOURCE weights -------------------
bpy.ops.wm.open_mainfile(filepath=SRC_BLEND)
src = bpy.data.objects["SirMelodiousBody"]
src_weights = {}
for v in src.data.vertices:
    co = src.matrix_world @ v.co
    src_weights[v.index] = (co.copy(),
                            {src.vertex_groups[g.group].name: g.weight for g in v.groups})

# --- pass 2: export FBX, find the exported bone set + unweighted verts --------
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.fbx(filepath=EXP_FBX)
rig = next(o for o in bpy.context.scene.objects if o.type == "ARMATURE")
exported_bones = set(b.name for b in rig.data.bones)
body = bpy.data.objects["SirMelodiousBody"]

weighted, unweighted = [], []
for v in body.data.vertices:
    co = body.matrix_world @ v.co
    groups = {body.vertex_groups[g.group].name: g.weight for g in v.groups}
    if groups:
        weighted.append((v.index, co.copy(), groups))
    else:
        unweighted.append((v.index, co.copy()))

# --- pass 3: for each unweighted vert, prefer source intent, else neighbours --
fixed = {}
for idx, co in unweighted:
    src_match = None
    # source intent: drop helper/non-exported names, keep real bones
    best = None
    for s_idx, (s_co, s_groups) in src_weights.items():
        d = (s_co - co).length_squared
        if best is None or d < best[0]:
            best = (d, s_groups)
    if best is not None and best[0] < 1e-6:
        src_match = best[1]
    if src_match:
        # source intent: keep real bones, remap ARP helpers, drop unit groups
        resolved = {}
        for k, w in src_match.items():
            if k in UNIT_GROUPS:
                continue
            target = k if k in exported_bones else HELPER_MAP.get(k)
            if target and target in exported_bones:
                resolved[target] = resolved.get(target, 0.0) + w
        if resolved:
            top = sorted(resolved.items(), key=lambda kv: -kv[1])[:MAX_INFLUENCES]
            s = sum(w for _, w in top) or 1.0
            fixed[idx] = {k: round(w / s, 4) for k, w in top}
            continue
    # fallback: nearest weighted neighbour (spatial), top-4
    nbrs = sorted(weighted, key=lambda w: (w[1] - co).length_squared)[:6]
    acc = {}
    for _, _, g in nbrs:
        for k, w in g.items():
            acc[k] = acc.get(k, 0.0) + w
    top = sorted(acc.items(), key=lambda kv: -kv[1])[:MAX_INFLUENCES]
    s = sum(w for _, w in top) or 1.0
    fixed[idx] = {k: round(w / s, 4) for k, w in top}

# --- pass 4: apply to the staged mesh, write delta + manifest -----------------
for idx, groups in fixed.items():
    v = body.data.vertices[idx]
    for name, w in groups.items():
        vg = body.vertex_groups.get(name) or body.vertex_groups.new(name=name)
        vg.add([idx], w, "REPLACE")

still = sum(1 for v in body.data.vertices if not v.groups)
maxinf = max((len(v.groups) for v in body.data.vertices), default=0)
print("FIXED", len(fixed), "STILL_UNWEIGHTED", still, "MAX_INFLUENCES", maxinf)

json.dump({"fixed_verts": {str(k): v for k, v in fixed.items()},
           "fixed_count": len(fixed), "still_unweighted": still,
           "max_influences": maxinf, "exported_bones": sorted(exported_bones)},
          open(OUT_DIR + r"\body_reweight_delta.json", "w"), indent=1)

bpy.ops.wm.save_as_mainfile(filepath=OUT_DIR + r"\SirMelodiousBody_reweighted_20261007.blend")
print("wrote", OUT_DIR + r"\body_reweight_delta.json")
