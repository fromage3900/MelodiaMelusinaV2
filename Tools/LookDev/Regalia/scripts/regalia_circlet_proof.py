"""REGALIA PHASE B PROOF — circlet, gates measured against the live head.

Run inside the live session via MCP. Builds MEL_melusina_circlet, stages it on
Melusina_Base, and measures it against the real head surface.

Gate design note (learned 2026-09-25): a BOUNDING BOX cannot prove placement. An
earlier version asserted "no circlet vert lies inside the head's x/y extent" and
that read 91% INSIDE for a correctly-wrapped band, because the head is an egg and
a box around an egg contains its whole silhouette. The honest gate is radial:
for each circlet vert, is there a head vert within 12 mm in the XY plane at the
same height? A wrapping band touches a small fraction of that; a band pushed
through the skull touches nearly all of it.
"""

import bpy
import json
import math
import os
import sys

_HERE = os.path.dirname(os.path.abspath(__file__))
_OUT = os.path.join(_HERE, "circlet_integrity.json")

# ---- measured head landmarks (Melusina_Base, 18891 v, z -0.187..1.836) -------
HEAD_Z = (1.54, 1.58)          # the brow slice
HEAD_W = 0.4084                # measured
HEAD_D = 0.4594                # measured
BROW_Z = 1.560


def _pts(obj):
    bpy.context.view_layer.update()
    bpy.context.scene.update_tag()
    dg = bpy.context.evaluated_depsgraph_get()
    oe = obj.evaluated_get(dg)
    me = oe.to_mesh()
    P = [oe.matrix_world @ v.co for v in me.vertices]
    oe.to_mesh_clear()
    return P


def run():
    R = {"gates": {}, "checks": {}}
    body = bpy.data.objects.get("Melusina_Base")
    if body is None:
        R["error"] = "Melusina_Base not in scene"
        _write(R)
        return R

    import importlib.util
    P = os.path.join(_HERE, "melusina_regalia_circlet.py")
    spec = importlib.util.spec_from_file_location("regalia_circlet", P)
    mod = importlib.util.module_from_spec(spec)
    sys.modules["regalia_circlet"] = mod
    spec.loader.exec_module(mod)
    tree = mod.build()
    R["tree"] = tree.name
    R["nodes"] = len(tree.nodes)
    R["links"] = len(tree.links)
    R["dials"] = [i.name for i in tree.interface.items_tree
                  if getattr(i, "item_type", "") == "SOCKET"
                  and getattr(i, "in_out", "") == "INPUT"]

    # ---- stage on the rig -------------------------------------------------
    coll = bpy.data.collections.get("REGALIA") or bpy.data.collections.new("REGALIA")
    if coll.name not in [c.name for c in bpy.context.scene.collection.children]:
        bpy.context.scene.collection.children.link(coll)
    ob = bpy.data.objects.get("Melusina_Circlet")
    if ob is None:
        ob = bpy.data.objects.new("Melusina_Circlet",
                                  bpy.data.meshes.new("Melusina_Circlet"))
    if ob.name not in coll.objects:
        coll.objects.link(ob)
    ob.hide_viewport = False
    ob.hide_render = False
    for m in list(ob.modifiers):
        if m.type == "NODES":
            ob.modifiers.remove(m)
    md = ob.modifiers.new("Circlet", "NODES")
    md.node_group = tree
    # write every captured dial explicitly -- a NODES modifier captures POSITIONALLY
    # and keeps the old values when the tree is replaced
    for it in tree.interface.items_tree:
        if getattr(it, "item_type", "") == "SOCKET" and getattr(it, "in_out", "") == "INPUT" \
                and hasattr(it, "default_value"):
            try:
                md.properties.inputs[it.identifier].update(value=it.default_value)
            except Exception:
                pass
    rig = bpy.data.objects.get("character_rig")
    if rig is not None:
        # OBJECT parenting, NOT bone: `c_head.x` carries a ~1.5 m offset that threw
        # the circlet to y=-1.72, 1.5 m off the skull. The tree bakes world space, so
        # object-parenting to the (identity-transform) rig both follows the rig and
        # preserves the authored position.
        ob.parent = rig
        ob.parent_type = "OBJECT"
        ob.matrix_parent_inverse.identity()
    ob.location = (0.0, 0.0, 0.0)
    ob.rotation_euler = (0.0, 0.0, 0.0)
    ob.scale = (1.0, 1.0, 1.0)

    # ---- measure ----------------------------------------------------------
    cir = _pts(ob)
    bp = _pts(body)
    if not cir:
        R["error"] = "circlet emitted 0 verts"
        _write(R)
        return R

    mn = [min(v[i] for v in cir) for i in range(3)]
    mx = [max(v[i] for v in cir) for i in range(3)]
    dims = [mx[i] - mn[i] for i in range(3)]
    hs = [p for p in bp if HEAD_Z[0] <= p.z < HEAD_Z[1]]
    hmn = [min(p[i] for p in hs) for i in range(3)]
    hmx = [max(p[i] for p in hs) for i in range(3)]
    hcx = (hmn[0] + hmx[0]) / 2.0
    hcy = (hmn[1] + hmx[1]) / 2.0
    ccx = (mn[0] + mx[0]) / 2.0
    ccy = (mn[1] + mx[1]) / 2.0

    # radial clearance: head vert within 12 mm in XY, same height band
    tol = 0.012
    hset = [(p.x, p.y) for p in hs]
    inside = sum(1 for v in cir
                 if any((v.x - a) ** 2 + (v.y - b) ** 2 < tol * tol for a, b in hset))
    ratio = inside / float(len(cir))

    R["measure"] = {
        "verts": len(cir),
        "min": [round(v, 4) for v in mn],
        "max": [round(v, 4) for v in mx],
        "dims": [round(v, 4) for v in dims],
        "head_slice_verts": len(hs),
        "head_width": round(hmx[0] - hmn[0], 4),
        "head_depth": round(hmx[1] - hmn[1], 4),
        "head_centre": [round(hcx, 4), round(hcy, 4)],
        "circlet_centre": [round(ccx, 4), round(ccy, 4)],
        "centre_err_mm": [round((ccx - hcx) * 1000, 1), round((ccy - hcy) * 1000, 1)],
        "radial_contact_ratio": round(ratio, 4),
    }

    G = R["gates"]
    G["tree_built"] = len(tree.nodes) > 20
    G["emits_geometry"] = len(cir) > 300
    G["dials_present"] = len(R["dials"]) >= 12
    # wraps the head: wider than 90% of the head's width, and near-circular in plan
    G["wraps_head_width"] = dims[0] >= HEAD_W * 0.90
    G["wraps_head_depth"] = dims[1] >= HEAD_D * 0.90
    G["band_height_plausible"] = 0.010 <= dims[2] <= 0.060
    # centred on the head's measured axis, within 15 mm
    G["centred_on_head"] = (abs(ccx - hcx) < 0.015 and abs(ccy - hcy) < 0.015)
    # seated at the brow
    G["at_brow_height"] = abs(((mn[2] + mx[2]) / 2.0) - BROW_Z) < 0.035
    # NOT buried in the skull: a wrapping band grazes a small fraction
    G["not_buried_in_head"] = ratio < 0.35
    # filigree present (band alone is ~192 verts of 64-pt x 3 profile)
    G["filigree_emits"] = len(cir) > 400
    # rigid-body hygiene for an armature child
    G["clean_local_transform"] = (max(abs(v) for v in ob.location) < 1e-6
                                  and max(abs(v) for v in ob.rotation_euler) < 1e-6
                                  and all(abs(v - 1.0) < 1e-6 for v in ob.scale))

    npass = sum(1 for v in G.values() if v)
    R["status"] = "PASS_CIRCLET" if npass == len(G) else "FAIL_CIRCLET"
    R["gates_passed"] = npass
    R["gates_total"] = len(G)
    R["failed"] = [k for k, v in G.items() if not v]
    _write(R)
    return R


def _write(R):
    with open(_OUT, "w", encoding="utf-8") as f:
        json.dump(R, f, indent=1)


if __name__ == "__main__":
    r = run()
    print("STATUS", r.get("status"), r.get("gates_passed"), "/", r.get("gates_total"))
    print("FAILED", r.get("failed"))
