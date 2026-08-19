#!/usr/bin/env python3
"""Prepare Melusina's V2 meshes as a clean base for hand weight painting.

WHAT THIS IS FOR
----------------
Hand painting on top of an un-normalised, over-influenced mesh means fighting
artifacts that were never the painter's fault. This does the mechanical part so the
art pass starts from a defensible base, and leaves every judgement call to a human.

WHAT IT DOES
------------
1. **Limit total influences to 4 per vertex.** Unreal supports 8, but 4 is the
   practical ceiling: it is what LODs and mobile paths assume, and going over it
   silently changes deformation between LOD0 and LOD1. Blender's Limit Total keeps
   the 4 heaviest influences and drops the rest.
2. **Normalize All.** After limiting, each vertex's remaining weights are rescaled to
   sum to 1.0. Skipping this is what produces the classic "limb shrinks slightly when
   posed" artifact, because the missing weight is treated as zero-transform.
3. **Report, before and after.** Max influences, vertices over the cap, and any vertex
   that would end up unweighted.

WHAT IT DELIBERATELY DOES NOT DO
--------------------------------
- **No smoothing.** Corrective smoothing is a deformation decision; `voxel_skinning`'s
  Corrective Smooth Baker is the right tool and it belongs in a human's hands.
- **No mirroring.** The left and right sides of this mesh were authored independently
  and a blind X-mirror would overwrite real asymmetry.
- **No auto-weighting.** Nothing here re-solves weights; it only constrains what is
  already authored.

The intent is that this is *reversible in spirit*: it removes influence noise, it does
not invent influence.

SAFETY
------
Dry-run by default. Never saves over the input. Aborts if any vertex would be left
with no influence at all.

USAGE
-----
    blender --background --factory-startup <stage>.blend \
        --python Tools/prep_melusina_weight_paint_base.py
    blender --background --factory-startup <stage>.blend \
        --python Tools/prep_melusina_weight_paint_base.py -- --apply --save-as <out>.blend
"""

from __future__ import annotations

import sys

import bpy

# The V2 export set. Melusina.001 is the original body and is not touched.
MESHES = ("simply_coll", "Melusina_Gloves", "Melusina_Sleeve", "newshirt",
          "Melusina_Skirt", "Melusina_SkirtPanel", "Melusina_Bow",
          "Melusina_FrontPanel", "Melusina_Shawl",
          "Retopo_boot 2.001", "Retopo_boot 2.002")
MAX_INFLUENCES = 4


def args() -> list[str]:
    return sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []


def opt(name, default=None):
    a = args()
    return a[a.index(name) + 1] if name in a and a.index(name) + 1 < len(a) else default


def survey(ob) -> dict:
    """Influence stats. Counts only meaningful weights."""
    over = 0
    unweighted = 0
    peak = 0
    for v in ob.data.vertices:
        n = sum(1 for g in v.groups if g.weight > 1e-6)
        peak = max(peak, n)
        if n > MAX_INFLUENCES:
            over += 1
        if n == 0:
            unweighted += 1
    return {"verts": len(ob.data.vertices), "peak": peak,
            "over": over, "unweighted": unweighted}


def main() -> int:
    apply = "--apply" in args()
    save_as = opt("--save-as")

    targets = []
    missing = []
    for name in MESHES:
        ob = bpy.data.objects.get(name)
        if ob and ob.type == "MESH" and ob.vertex_groups:
            targets.append(ob)
        else:
            missing.append(name)

    if missing:
        print(f"note: not found / not skinned, skipped: {missing}")
    if not targets:
        print("ABORT: no target meshes found")
        return 1

    print(f"\n{'mesh':<22}{'verts':>8}{'peak':>6}{'>%d' % MAX_INFLUENCES:>7}{'unweighted':>12}")
    before = {}
    for ob in targets:
        s = survey(ob)
        before[ob.name] = s
        print(f"{ob.name:<22}{s['verts']:>8}{s['peak']:>6}{s['over']:>7}{s['unweighted']:>12}")

    total_over = sum(s["over"] for s in before.values())
    print(f"\nvertices above {MAX_INFLUENCES} influences: {total_over}")

    pre_unweighted = sum(s["unweighted"] for s in before.values())
    if pre_unweighted:
        print(f"ABORT: {pre_unweighted} vertices already carry no influence — fix binding first")
        return 1

    if not apply:
        print("\nDRY RUN. Nothing written. Re-run with '-- --apply' to limit + normalize.")
        return 0

    # Direct data API, not bpy.ops. The operator versions need an active object,
    # which rebuilds the depsgraph on this 879-object scene and OOM'd the process
    # (exit 137). Working on the mesh data straight is both lighter and exact.
    for ob in targets:
        by_index = {g.index: g for g in ob.vertex_groups}
        trimmed = 0
        for v in ob.data.vertices:
            live = [(g.group, g.weight) for g in v.groups if g.weight > 1e-6]
            if not live:
                continue
            live.sort(key=lambda gw: gw[1], reverse=True)
            keep, drop = live[:MAX_INFLUENCES], live[MAX_INFLUENCES:]
            for gi, _ in drop:
                by_index[gi].remove([v.index])
                trimmed += 1
            total = sum(w for _, w in keep)
            if total <= 0.0:
                continue
            # Normalize the survivors so the vertex sums to 1.0. Without this the
            # dropped weight reads as zero-transform and the limb visibly shrinks.
            for gi, w in keep:
                by_index[gi].add([v.index], w / total, "REPLACE")
        print(f"  {ob.name}: dropped {trimmed} surplus influences")

    print(f"\n{'mesh':<22}{'peak':>6}{'>%d' % MAX_INFLUENCES:>7}{'unweighted':>12}")
    broke = 0
    for ob in targets:
        s = survey(ob)
        broke += s["unweighted"]
        print(f"{ob.name:<22}{s['peak']:>6}{s['over']:>7}{s['unweighted']:>12}")

    if broke:
        print(f"\nWARNING: {broke} vertices ended with no influence. NOT saving.")
        return 1

    if save_as:
        bpy.ops.wm.save_as_mainfile(filepath=save_as, copy=True, compress=False)
        print(f"\nsaved: {save_as}")
    else:
        print("\nNOT saved. Pass '--save-as <path>'.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
