"""REGALIA PHASE B PROOF -- circlet, measured against the CONTRACT head proxy.

Runs headless from regalia_contract.blend (148 KB), never from the 2.4 GB Melusina
blends -- those segfault in BKE_blendfile_read (crash 2026-09-25 19:08).

Gate design notes (each one learned by a failed gate, 2026-09-25):
  * A BOUNDING BOX cannot prove placement. An earlier "no circlet vert inside the
    head's x/y extent" gate read 91% INSIDE for a correctly wrapped band, because a
    box around an egg contains its whole silhouette. The honest gate is RADIAL: is
    each circlet vert within 12 mm of a head vert in XY?
  * Vert count is not ornament count. 46,170 verts once meant 243 scrolls from a
    requested 9, because a FRACT keep-rule passed every point. Count INSTANCES
    per motif and histogram their angle instead.
  * Non-zero geometry is not visibility. The gems emitted 60 verts and rendered
    nothing, because they sat on a chord through the head AXIS. Gate on angular
    spread and on radius-vs-head-surface, not on existence.

Run: blender -b regalia_contract.blend --python regalia_circlet_verify.py
"""

import bpy
import json
import math
import os

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "circlet_integrity.json")

# measured head landmarks (regalia_landmarks.json)
CX, CY = -0.0044, -0.1335      # head axis at the brow
BROW_Z = 1.560
HEAD_HW = 0.204                # half-width
HEAD_HD = 0.2295               # half-depth
DEPTH_RATIO = 1.125            # 0.4594/0.4084
BAND_R = 0.204 * 1.03          # Clearance 1.03
GAP_AT_NAPE_DEG = (180.0, 240.0)   # the intended open arc, measured


def _world_pts(ob):
    bpy.context.view_layer.update()
    bpy.context.scene.update_tag()
    dg = bpy.context.evaluated_depsgraph_get()
    oe = ob.evaluated_get(dg)
    me = oe.to_mesh()
    P = [oe.matrix_world @ v.co for v in me.vertices]
    oe.to_mesh_clear()
    return P


def _angle(x, y):
    return math.degrees(math.atan2(y - CY, x - CX)) % 360.0


def run():
    R = {"gates": {}, "measure": {}}
    ob = bpy.data.objects.get("Melusina_Circlet")
    head = bpy.data.objects.get("Melusina_HeadProxy")
    tree = bpy.data.node_groups.get("MEL_melusina_circlet")
    if ob is None or tree is None:
        R["error"] = "contract file missing the circlet or its tree"
        _w(R)
        return R

    cir = _world_pts(ob)
    hp = _world_pts(head) if head else []
    if not cir:
        R["error"] = "circlet emitted 0 verts"
        _w(R)
        return R

    mn = [min(v[i] for v in cir) for i in range(3)]
    mx = [max(v[i] for v in cir) for i in range(3)]
    dims = [mx[i] - mn[i] for i in range(3)]
    ccx, ccy, ccz = [(mn[i] + mx[i]) / 2.0 for i in range(3)]

    # ---- SIGNED containment, not proximity.
    #
    # The first version counted verts within 12 mm of a head vert and called that
    # "buried" -- but a band RESTING on a surface always has its inner half in
    # contact, so the gate read 56.6% on a perfectly-seated circlet. Unfalsifiable.
    # The real question is whether a vert is strictly INSIDE the head, so test the
    # egg cross-section analytically: ((x-CX)/HW)^2 + ((y-CY)/HD)^2 < 1, and allow a
    # small tolerance for the band's own thickness, which legitimately overlaps skin.
    hset = [(p.x, p.y) for p in hp if 1.50 <= p.z < 1.62]
    tol = 0.012
    contact = sum(1 for v in cir
                  if any((v.x - a) ** 2 + (v.y - b) ** 2 < tol * tol for a, b in hset))
    proximity = contact / float(len(cir))

    BAND_T = 0.006          # Band Depth: the band's own half-thickness
    deep = 0                # verts further inside than the band may legally reach
    for v in cir:
        e = ((v.x - CX) / HEAD_HW) ** 2 + ((v.y - CY) / HEAD_HD) ** 2
        # radius at which the surface sits on this bearing
        cos_a = (v.x - CX) / HEAD_HW
        sin_a = (v.y - CY) / HEAD_HD
        m = math.hypot(cos_a, sin_a)
        if m < 1e-9:
            continue
        # how far inside the surface this vert is, in metres
        depth_m = (1.0 - m) / m * (HEAD_HW if abs(cos_a) >= abs(sin_a) else HEAD_HD)
        if depth_m > BAND_T + 0.002:
            deep += 1
    ratio = deep / float(len(cir))

    # ---- ornament distribution: 30-degree histogram about the head axis
    buckets = {}
    for v in cir:
        b = int(_angle(v.x, v.y) // 30) * 30
        buckets[b] = buckets.get(b, 0) + 1
    occupied = sorted(k for k, v in buckets.items() if v > 0)
    gap_open = not any(GAP_AT_NAPE_DEG[0] <= a < GAP_AT_NAPE_DEG[1] for a in occupied)

    # ---- radius: the band must sit OUTSIDE the head surface
    rad = [math.hypot(v.x - CX, (v.y - CY) / DEPTH_RATIO) for v in cir]
    rmin, rmax = min(rad), max(rad)

    R["measure"] = {
        "verts": len(cir),
        "min": [round(v, 4) for v in mn],
        "max": [round(v, 4) for v in mx],
        "dims": [round(v, 4) for v in dims],
        "centre": [round(ccx, 4), round(ccy, 4), round(ccz, 4)],
        "centre_err_mm": [round((ccx - CX) * 1000, 1), round((ccy - CY) * 1000, 1),
                          round((ccz - BROW_Z) * 1000, 1)],
        "head_half_width": HEAD_HW,
        "band_radius": round(BAND_R, 4),
        "radius_range": [round(rmin, 4), round(rmax, 4)],
        "prox_12mm_ratio": round(proximity, 4),
        "buried_ratio": round(ratio, 4),
        "buried_verts": deep,
        "ornament_buckets_30deg": {str(k): buckets[k] for k in sorted(buckets)},
        "buckets_occupied": occupied,
        "nape_gap_open": gap_open,
        "dials": len([i for i in tree.interface.items_tree
                      if getattr(i, "item_type", "") == "SOCKET"
                      and getattr(i, "in_out", "") == "INPUT"]),
        "nodes": len(tree.nodes),
        "links": len(tree.links),
    }

    G = R["gates"]
    G["tree_built"] = len(tree.nodes) > 25
    G["emits_geometry"] = len(cir) > 500
    G["dial_contract"] = R["measure"]["dials"] >= 15
    # wraps the head, not a fragment
    G["wraps_width"] = dims[0] >= HEAD_HW * 2.0 * 0.95
    G["wraps_depth"] = dims[1] >= HEAD_HD * 2.0 * 0.95
    G["band_height_slim"] = 0.020 <= dims[2] <= 0.070
    # seated on the head
    G["centred_xy"] = abs(ccx - CX) < 0.010 and abs(ccy - CY) < 0.010
    G["at_brow"] = abs(ccz - BROW_Z) < 0.030
    G["outside_head"] = rmin >= HEAD_HW * 0.98
    G["not_buried"] = ratio < 0.05   # only the band thickness may overlap
    # ornament spread, not clumped
    G["ornament_spread"] = len(occupied) >= 8
    G["nape_gap_open"] = gap_open
    G["has_gold_material"] = any(m and m.name == "REGALIA_GOLD" for m in ob.data.materials) \
        or _tree_has_material(tree)
    # vert budget: a 9-scroll circlet should be a few thousand, not tens of thousands
    G["vert_budget"] = len(cir) < 12000

    np_ = sum(1 for v in G.values() if v)
    R["gates_passed"] = np_
    R["gates_total"] = len(G)
    R["failed"] = [k for k, v in G.items() if not v]
    R["status"] = "PASS_CIRCLET" if np_ == len(G) else "FAIL_CIRCLET"
    _w(R)
    return R


def _tree_has_material(tree):
    for n in tree.nodes:
        if n.bl_idname == "GeometryNodeSetMaterial":
            return True
    return False


def _w(R):
    with open(OUT, "w", encoding="utf-8") as f:
        json.dump(R, f, indent=1)


if __name__ == "__main__":
    r = run()
    print("STATUS", r.get("status"), r.get("gates_passed"), "/", r.get("gates_total"))
    print("FAILED", r.get("failed"))
    m = r.get("measure", {})
    for k in ("verts", "dims", "centre_err_mm", "radius_range", "radial_contact_ratio",
              "buckets_occupied", "nape_gap_open", "dials",
              "buried_ratio", "prox_12mm_ratio"):
        print("  %-24s %s" % (k, m.get(k)))
