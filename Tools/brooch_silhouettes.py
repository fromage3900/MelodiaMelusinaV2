# brooch_silhouettes.py — canonical home for brooch silhouette variant builders (v11.3).
# Ported 2026-09-19 from Saved/Audit/v11_variant_spike.py (spike = historical record; the
# construction is proven there: citadel + veil rendered clean on the repaired base).
#
# Consumers:
#   - Tools/gen_flower_brooch_v10.py builds the genome-selected preset after the standard parts.
#   - Saved/Audit/render_sil_icons.py builds each preset runtime-only for the icon contact sheet.
#
# Ownership: variants are ADDITIVE objects (like dangles/sparkles), never in-place swaps of the
# flower crown. "flower" (default) = no extra object. Trees are GN_BroochSil_*; objects are
# FlowerBrooch_Sil*. Scale-to-plate and placement are object-level (no tree interface changes).
#
# Nothing here executes at import time.
import math
import os
import sys

import bpy
from mathutils import Vector


# ------------------------------------------------------------ node helpers ----
def mk(tree, t, name, loc):
    n = tree.nodes.new(t)
    n.name = name
    n.location = loc
    return n


def L(a, sa, b, sb):
    return a.id_data.links.new(a.outputs[sa], b.inputs[sb])


def dn(n, k, v):
    try:
        n.inputs[k].default_value = v
    except Exception as exc:
        print("  warn dn %s.%s (%r)" % (n.name, k, exc))


def mth(tree, name, op, loc, a=None, b=None):
    n = mk(tree, 'ShaderNodeMath', name, loc)
    n.operation = op
    if a is not None:
        n.inputs[0].default_value = a
    if b is not None:
        n.inputs[1].default_value = b
    return n


def tree_new(name):
    t = bpy.data.node_groups.new(name, 'GeometryNodeTree')
    t.interface.new_socket("Geometry", in_out='INPUT', socket_type='NodeSocketGeometry')
    t.interface.new_socket("Geometry", in_out='OUTPUT', socket_type='NodeSocketGeometry')
    gi = mk(t, 'NodeGroupInput', "in", (0, 0))
    go = mk(t, 'NodeGroupOutput', "out", (0, -400))
    return t, gi, go


def obj_new(name, tree):
    me = bpy.data.meshes.new(name)
    ob = bpy.data.objects.new(name, me)
    bpy.context.scene.collection.objects.link(ob)
    mod = ob.modifiers.new("GN", 'NODES')
    mod.node_group = tree
    return ob


def mat_simple(name, color, metallic=0.0, rough=0.5, emission=None, strength=0.0,
               specular=None):
    m = bpy.data.materials.get(name)
    if m is None:
        m = bpy.data.materials.new(name)
    m.use_nodes = True
    for n in m.node_tree.nodes:
        if n.type == 'BSDF_PRINCIPLED':
            n.inputs['Base Color'].default_value = (*color, 1)
            n.inputs['Metallic'].default_value = metallic
            n.inputs['Roughness'].default_value = rough
            if specular is not None:
                for key in ('Specular IOR Level', 'Specular'):
                    try:
                        n.inputs[key].default_value = specular
                        break
                    except Exception:
                        continue
            if emission:
                n.inputs['Emission Color'].default_value = (*emission, 1)
                n.inputs['Emission Strength'].default_value = strength
    return m


def add_set_material(tree, mat):
    go = next(n for n in tree.nodes if n.type == 'GROUP_OUTPUT')
    links = list(go.inputs['Geometry'].links)
    if not links:
        return
    src = links[0].from_socket
    for l in links:
        tree.links.remove(l)
    sm = tree.nodes.new('GeometryNodeSetMaterial')
    sm.name = "set material"
    sm.location = (go.location.x - 220, go.location.y + 60)
    sm.inputs['Material'].default_value = mat
    tree.links.new(src, sm.inputs['Geometry'])
    tree.links.new(sm.outputs['Geometry'], go.inputs['Geometry'])


# ---------------------------------------------------------------- citadel ----
def build_citadel():
    """8 pyramidal hard-surface rays + shoulder blocks + pylons + ring (flat facets)."""
    t, gi, go = tree_new("GN_BroochSil_Citadel")
    parts = []
    for i in range(8):
        th = math.radians(i * 45.0)
        el = math.radians(38.0)
        col = 200 * (i % 4)
        row = -160 * (i // 4)
        c = mk(t, 'GeometryNodeMeshCone', "ray %d" % i, (col, row))
        dn(c, "Vertices", 4)
        dn(c, "Radius Bottom", 0.050)
        dn(c, "Radius Top", 0.006)
        dn(c, "Depth", 0.34)
        tr = mk(t, 'GeometryNodeTransform', "ray %d xf" % i, (col + 160, row))
        L(c, "Mesh", tr, "Geometry")
        r0 = 0.150
        dn(tr, "Translation", (r0 * math.cos(th) * math.cos(el),
                               r0 * math.sin(th) * math.cos(el),
                               0.012 + 0.17 * math.sin(el)))
        dn(tr, "Rotation", (math.radians(90.0) - el, 0.0, th))
        parts.append((tr, "Geometry"))
        s = mk(t, 'GeometryNodeMeshCone', "shoulder %d" % i, (col, row - 160))
        dn(s, "Vertices", 4)
        dn(s, "Radius Bottom", 0.085)
        dn(s, "Radius Top", 0.052)
        dn(s, "Depth", 0.075)
        st = mk(t, 'GeometryNodeTransform', "shoulder %d xf" % i, (col + 160, row - 160))
        L(s, "Mesh", st, "Geometry")
        dn(st, "Translation", (0.135 * math.cos(th), 0.135 * math.sin(th), 0.010))
        dn(st, "Rotation", (math.radians(22.0), 0.0, th))
        parts.append((st, "Geometry"))
        p = mk(t, 'GeometryNodeMeshCone', "pylon %d" % i, (col, row - 320))
        dn(p, "Vertices", 4)
        dn(p, "Radius Bottom", 0.040)
        dn(p, "Radius Top", 0.006)
        dn(p, "Depth", 0.13)
        pt = mk(t, 'GeometryNodeTransform', "pylon %d xf" % i, (col + 160, row - 320))
        L(p, "Mesh", pt, "Geometry")
        pa = th + math.radians(22.5)
        dn(pt, "Translation", (0.165 * math.cos(pa), 0.165 * math.sin(pa), 0.055))
        dn(pt, "Rotation", (math.radians(14.0), 0.0, pa))
        parts.append((pt, "Geometry"))
    j = mk(t, 'GeometryNodeJoinGeometry', "join parts", (1400, -300))
    for src, ss in parts:
        L(src, ss, j, "Geometry")
    ring = mk(t, 'GeometryNodeCurvePrimitiveCircle', "ring path", (900, -600))
    dn(ring, "Radius", 0.150)
    dn(ring, "Resolution", 64)
    prof = mk(t, 'GeometryNodeCurvePrimitiveCircle', "ring prof", (900, -760))
    dn(prof, "Radius", 0.014)
    dn(prof, "Resolution", 8)
    c2m = mk(t, 'GeometryNodeCurveToMesh', "ring mesh", (1100, -680))
    L(ring, "Curve", c2m, "Curve")
    L(prof, "Curve", c2m, "Profile Curve")
    j2 = mk(t, 'GeometryNodeJoinGeometry', "join all", (1600, -300))
    L(j, "Geometry", j2, "Geometry")
    L(c2m, "Mesh", j2, "Geometry")
    # v11.4 elegant-mechanical: stepped rim band (concentric sweep, smaller
    # profile = assembled-metal read, no boolean) + twin guilloche groove rails.
    ring2 = mk(t, 'GeometryNodeCurvePrimitiveCircle', "v114 step path", (1750, -900))
    dn(ring2, "Radius", 0.150)
    dn(ring2, "Resolution", 64)
    prof2 = mk(t, 'GeometryNodeCurvePrimitiveCircle', "v114 step prof", (1750, -1060))
    dn(prof2, "Radius", 0.006)
    dn(prof2, "Resolution", 6)
    c2m2 = mk(t, 'GeometryNodeCurveToMesh', "v114 step mesh", (1950, -980))
    L(ring2, "Curve", c2m2, "Curve")
    L(prof2, "Curve", c2m2, "Profile Curve")
    L(c2m2, "Mesh", j2, "Geometry")
    for k, (rr, pr) in enumerate(((0.141, 0.0018), (0.159, 0.0018))):
        gp = mk(t, 'GeometryNodeCurvePrimitiveCircle', "v114 groove path %d" % k, (1750, -1200 - 160 * k))
        dn(gp, "Radius", rr)
        dn(gp, "Resolution", 96)
        gpr = mk(t, 'GeometryNodeCurvePrimitiveCircle', "v114 groove prof %d" % k, (1750, -1360 - 160 * k))
        dn(gpr, "Radius", pr)
        dn(gpr, "Resolution", 4)
        gm = mk(t, 'GeometryNodeCurveToMesh', "v114 groove mesh %d" % k, (1950, -1280 - 160 * k))
        L(gp, "Curve", gm, "Curve")
        L(gpr, "Curve", gm, "Profile Curve")
        L(gm, "Mesh", j2, "Geometry")
    # gothic-arch void markers: 8 small flat panels between the rays (negative-
    # space signature at icon scale; additive markers, never a plate boolean).
    arch_join = mk(t, 'GeometryNodeJoinGeometry', "v114 arch join", (2150, -700))
    for i in range(8):
        pa = math.radians(i * 45.0 + 22.5)
        cube = mk(t, 'GeometryNodeMeshCube', "v114 arch %d" % i, (1950, -500 - 120 * (i % 4)))
        dn(cube, "Size", (0.018, 0.010, 0.020))
        xf = mk(t, 'GeometryNodeTransform', "v114 arch xf %d" % i, (2150, -500 - 120 * (i % 4)))
        L(cube, "Mesh", xf, "Geometry")
        dn(xf, "Translation", (0.150 * math.cos(pa), 0.150 * math.sin(pa), 0.016))
        dn(xf, "Rotation", (0.0, 0.0, pa))
        L(xf, "Geometry", arch_join, "Geometry")
    L(arch_join, "Geometry", j2, "Geometry")
    # crisp facet shading for the crown.
    shade = mk(t, 'GeometryNodeSetShadeSmooth', "v114 facets flat", (2350, -300))
    try:
        shade.inputs["Shade Smooth"].default_value = False
    except Exception as exc:
        print("  warn v114 shade (%r)" % (exc,))
    L(j2, "Geometry", shade, "Geometry")
    L(shade, "Geometry", go, "Geometry")
    return t


# ------------------------------------------------------------------- veil ----
# Optional Higgsas path probe. The manual lissajous below is CANONICAL; Higgsas is an
# extra that is never required. This records state so a render report can state exactly
# which path produced the wire instead of printing a bare boolean that reads like a
# failure (2026-09-22: "VEIL: higgsas Lissajous Curve loaded: False" was mistaken for a
# build defect — nothing in the tree consumed the node).
HIGGSAS_STATUS = {}


def higgsas_lissajous_state():
    """Read-only capability record for the optional Higgsas 'Lissajous Curve' group."""
    st = {"bridge_import_ok": False, "bridge_file": None, "library_path": None,
          "library_exists": False, "lissajous_groups": [], "loaded": False, "error": None}
    try:
        from surreal_arch.capabilities import higgsas_library_path
        from surreal_arch.higgsas_bridge import load_node
    except Exception as exc:
        st["error"] = "import: %r" % (exc,)
        return st
    st["bridge_import_ok"] = True
    st["bridge_file"] = getattr(sys.modules.get("surreal_arch.higgsas_bridge"),
                                "__file__", None)
    try:
        path = higgsas_library_path()
        st["library_path"] = path
        st["library_exists"] = os.path.exists(path)
        if st["library_exists"]:
            with bpy.data.libraries.load(path, link=False) as (src, _dst):
                st["lissajous_groups"] = [n for n in src.node_groups
                                          if "lissajous" in n.lower()]
    except Exception as exc:
        st["error"] = "library: %r" % (exc,)
    # The bridge that answers above is the one Blender's addons dir provides, and
    # capabilities._REPO_ROOT is derived from that installed file's location — so on an
    # installed copy the repo-relative candidate becomes .../Blender/5.2/scripts/RawArt/...
    # and reports missing even though the library sits in the repo. Measured 2026-09-23:
    # addon-resolved=False while repo file = 20,565,027 bytes. Probe the repo candidate
    # directly so the record states both, without mutating sys.path (shadowing the addon
    # for the rest of the session would leak into the house GN lanes).
    try:
        repo = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        cand = os.path.join(repo, "RawArt", "BlenderLibraries", "Higgsas",
                            os.path.basename(path or ""))
        st["repo_root"] = repo
        st["repo_candidate"] = cand
        st["repo_candidate_exists"] = os.path.exists(cand)
    except Exception as exc:
        st["repo_candidate_error"] = repr(exc)
    # Bridge contract: call with the NT-prefixed name. v1.3 dropped the prefix and
    # higgsas_bridge.load_node resolves NT<Name> -> <Name>. The bare name is tried as a
    # documented fallback so an older library still resolves.
    for cand in ("NTLissajous Curve", "Lissajous Curve"):
        try:
            if load_node(cand) is not None:
                st["loaded"] = cand
                break
        except Exception as exc:
            st["error"] = "load(%s): %r" % (cand, exc)
    return st


def build_veil():
    """Three woven 3D lissajous wires (3:2:5) + beads at every 12th node + a base ring.

    The manual 3D lissajous is the deterministic path; the Higgsas 'Lissajous Curve'
    node is attempted via the bridge and skipped cleanly when unavailable.
    """
    t, gi, go = tree_new("GN_BroochSil_Veil")
    HIGGSAS_STATUS.clear()
    HIGGSAS_STATUS.update(higgsas_lissajous_state())
    print("VEIL: manual lissajous = canonical path (higgsas never required)")
    print("VEIL: higgsas probe bridge_import_ok=%s library_exists=%s lissajous_groups=%s "
          "loaded=%s" % (HIGGSAS_STATUS["bridge_import_ok"],
                         HIGGSAS_STATUS["library_exists"],
                         HIGGSAS_STATUS["lissajous_groups"],
                         HIGGSAS_STATUS["loaded"]))

    def manual_veil(i, delta, radius, z0, ampz, n=240):
        line = mk(t, 'GeometryNodeMeshLine', "m line %d" % i, (300, -200 - 300 * i))
        dn(line, "Count", n)
        dn(line, "Start Location", (0, 0, 0))
        dn(line, "Offset", (1, 0, 0))
        idx = mk(t, 'GeometryNodeInputIndex', "idx %d" % i, (300, -360 - 300 * i))
        tn = mth(t, "t %d" % i, 'DIVIDE', (480, -360 - 300 * i))
        L(idx, "Index", tn, 0)
        tn.inputs[1].default_value = float(n - 1)
        t2 = mth(t, "t*2pi %d" % i, 'MULTIPLY', (640, -360 - 300 * i), b=math.tau)
        L(tn, "Value", t2, 0)
        # x = radius*sin(3t+delta); y = radius*sin(2t); z = z0 + ampz*sin(5t+delta)
        xa = mth(t, "3t %d" % i, 'MULTIPLY', (800, -280 - 300 * i), b=3.0)
        L(t2, "Value", xa, 0)
        xb = mth(t, "3t+d %d" % i, 'ADD', (960, -280 - 300 * i), b=delta)
        L(xa, "Value", xb, 0)
        xs = mth(t, "sinx %d" % i, 'SINE', (1120, -280 - 300 * i))
        L(xb, "Value", xs, 0)
        xr = mth(t, "x %d" % i, 'MULTIPLY', (1280, -280 - 300 * i), b=radius)
        L(xs, "Value", xr, 0)
        ya = mth(t, "2t %d" % i, 'MULTIPLY', (800, -440 - 300 * i), b=2.0)
        L(t2, "Value", ya, 0)
        ys = mth(t, "siny %d" % i, 'SINE', (960, -440 - 300 * i))
        L(ya, "Value", ys, 0)
        yr = mth(t, "y %d" % i, 'MULTIPLY', (1120, -440 - 300 * i), b=radius)
        L(ys, "Value", yr, 0)
        za = mth(t, "5t %d" % i, 'MULTIPLY', (800, -600 - 300 * i), b=5.0)
        L(t2, "Value", za, 0)
        zb = mth(t, "5t+d %d" % i, 'ADD', (960, -600 - 300 * i), b=delta)
        L(za, "Value", zb, 0)
        zs = mth(t, "sinz %d" % i, 'SINE', (1120, -600 - 300 * i))
        L(zb, "Value", zs, 0)
        zr = mth(t, "z %d" % i, 'MULTIPLY', (1280, -600 - 300 * i), b=ampz)
        L(zs, "Value", zr, 0)
        zz = mth(t, "z0 %d" % i, 'ADD', (1440, -600 - 300 * i), b=z0)
        L(zr, "Value", zz, 0)
        comb = mk(t, 'ShaderNodeCombineXYZ', "pos %d" % i, (1600, -440 - 300 * i))
        L(xr, "Value", comb, "X")
        L(yr, "Value", comb, "Y")
        L(zz, "Value", comb, "Z")
        sp = mk(t, 'GeometryNodeSetPosition', "setpos %d" % i, (1780, -300 - 300 * i))
        L(line, "Mesh", sp, "Geometry")
        L(comb, "Vector", sp, "Position")
        return sp, idx

    veils = []
    for i, delta in enumerate((0.0, math.tau / 3.0, 2.0 * math.tau / 3.0)):
        sp, idx = manual_veil(i, delta, 0.165, 0.085, 0.055)
        c2c = mk(t, 'GeometryNodeMeshToCurve', "wire curve %d" % i, (2000, -300 - 300 * i))
        L(sp, "Geometry", c2c, "Mesh")
        prof = mk(t, 'GeometryNodeCurvePrimitiveCircle', "wire prof %d" % i, (2000, -440 - 300 * i))
        dn(prof, "Radius", 0.0045)
        dn(prof, "Resolution", 4)
        c2m = mk(t, 'GeometryNodeCurveToMesh', "wire mesh %d" % i, (2180, -360 - 300 * i))
        L(c2c, "Curve", c2m, "Curve")
        L(prof, "Curve", c2m, "Profile Curve")
        # v11.4: the wire path is an OPEN MeshLine -> MeshToCurve, so the sweep leaves two
        # uncapped tube ends per wire. Measured 2026-09-23: 3 wires x 2 ends x 4 profile
        # edges = the 24 boundary / 24 non-manifold edges the census gate caught. The
        # citadel's sweeps ride closed circle paths and were already 0/0. Close them where
        # they are made; the census check stays strict rather than being scoped down.
        try:
            c2m.inputs["Fill Caps"].default_value = True
        except Exception as exc:
            print("  warn wire fill caps %d (%r)" % (i, exc))
        veils.append((c2m, "Mesh"))
        bead = mk(t, 'GeometryNodeMeshUVSphere', "bead %d" % i, (2000, -620 - 300 * i))
        dn(bead, "Radius", 0.0085)
        dn(bead, "Segments", 12)
        dn(bead, "Rings", 8)
        every = mth(t, "mod %d" % i, 'MODULO', (2000, -760 - 300 * i))
        L(idx, "Index", every, 0)
        every.inputs[1].default_value = 12.0
        eq = mth(t, "eq %d" % i, 'COMPARE', (2160, -760 - 300 * i))
        L(every, "Value", eq, 0)
        eq.inputs[1].default_value = 0.0
        inst = mk(t, 'GeometryNodeInstanceOnPoints', "bead inst %d" % i, (2360, -560 - 300 * i))
        L(sp, "Geometry", inst, "Points")
        L(bead, "Mesh", inst, "Instance")
        L(eq, "Value", inst, "Selection")
        veils.append((inst, "Instances"))
    ring = mk(t, 'GeometryNodeCurvePrimitiveCircle', "veil ring", (2000, -1500))
    dn(ring, "Radius", 0.165)
    dn(ring, "Resolution", 64)
    rprof = mk(t, 'GeometryNodeCurvePrimitiveCircle', "veil ring prof", (2000, -1640))
    dn(rprof, "Radius", 0.012)
    dn(rprof, "Resolution", 8)
    rc2m = mk(t, 'GeometryNodeCurveToMesh', "veil ring mesh", (2180, -1560))
    L(ring, "Curve", rc2m, "Curve")
    L(rprof, "Curve", rc2m, "Profile Curve")
    j = mk(t, 'GeometryNodeJoinGeometry', "veil join", (2600, -600))
    for src, ss in veils:
        L(src, ss, j, "Geometry")
    L(rc2m, "Mesh", j, "Geometry")
    # v11.4 elegant-mechanical: hairline echo rail under the base ring.
    rp = mk(t, 'GeometryNodeCurvePrimitiveCircle', "v114 veil echo path", (2600, -1500))
    dn(rp, "Radius", 0.158)
    dn(rp, "Resolution", 96)
    rpr = mk(t, 'GeometryNodeCurvePrimitiveCircle', "v114 veil echo prof", (2600, -1640))
    dn(rpr, "Radius", 0.0022)
    dn(rpr, "Resolution", 4)
    rm = mk(t, 'GeometryNodeCurveToMesh', "v114 veil echo mesh", (2800, -1570))
    L(rp, "Curve", rm, "Curve")
    L(rpr, "Curve", rm, "Profile Curve")
    L(rm, "Mesh", j, "Geometry")
    L(j, "Geometry", go, "Geometry")
    return t


# ----------------------------------------------------------------- solving ----
PRESETS = {
    "star_citadel": build_citadel,
    "lissajous_veil": build_veil,
}

SIL_GOLD = "SIL_Gold"


def measured_bbox(objs):
    """World-space evaluated bbox across objs -> (lo, hi) Vectors."""
    dg = bpy.context.evaluated_depsgraph_get()
    lo = Vector((1e9, 1e9, 1e9))
    hi = Vector((-1e9, -1e9, -1e9))
    for ob in objs:
        if ob is None:
            continue
        ev = ob.evaluated_get(dg)
        for c in ev.bound_box:
            wv = ev.matrix_world @ Vector(c)
            lo = Vector((min(lo[i], wv[i]) for i in range(3)))
            hi = Vector((max(hi[i], wv[i]) for i in range(3)))
    return lo, hi


def plate_metrics(hero):
    """(center_xy, top_z, xy_span) of the hero brooch, evaluated."""
    lo, hi = measured_bbox([hero])
    ctr = ((lo.x + hi.x) * 0.5, (lo.y + hi.y) * 0.5)
    span = max(hi.x - lo.x, hi.y - lo.y)
    return ctr, hi.z, span


def build_silhouette(preset, hero=None, span_factor=1.15, sink=0.03):
    """Build the preset as an additive object, scale it to the plate, seat it on the flower.

    Returns a dict: {preset, tree, object, scale, span_before, span_after} or raises
    KeyError for an unknown preset. Object-level transform only (trees stay authored).
    """
    builder = PRESETS[preset]
    hero = hero or bpy.data.objects.get("FlowerBrooch")
    if hero is None:
        raise RuntimeError("hero FlowerBrooch not found; cannot solve silhouette")
    ctr, top_z, span = plate_metrics(hero)
    gold = mat_simple(SIL_GOLD, (1.0, 0.766, 0.336), metallic=1.0, rough=0.22)
    tree = builder()
    add_set_material(tree, gold)
    ob = obj_new("FlowerBrooch_Sil" + preset.split("_")[-1].title(), tree)
    ob.data.materials.append(gold)
    bpy.context.view_layer.update()
    lo, hi = measured_bbox([ob])
    span_before = max(hi.x - lo.x, hi.y - lo.y)
    k = (span * span_factor) / span_before if span_before > 1e-6 else 1.0
    ob.scale = (k, k, k)
    bpy.context.view_layer.update()
    lo, hi = measured_bbox([ob])
    bcx, bcy = (lo.x + hi.x) * 0.5, (lo.y + hi.y) * 0.5
    ob.location.x += ctr[0] - bcx
    ob.location.y += ctr[1] - bcy
    ob.location.z += (top_z - sink) - lo.z
    bpy.context.view_layer.update()
    lo, hi = measured_bbox([ob])
    span_after = max(hi.x - lo.x, hi.y - lo.y)
    print("[sil] preset=%s scale=%.4f span %.3f -> %.3f (plate %.3f, want %.3f)"
          % (preset, k, span_before, span_after, span, span * span_factor))
    return {"preset": preset, "tree": tree, "object": ob, "scale": k,
            "span_before": span_before, "span_after": span_after}


def active_preset(genome):
    """Read the genome's silhouette block -> preset name ('flower' = none)."""
    if not isinstance(genome, dict):
        return "flower"
    sil = genome.get("silhouette")
    if not isinstance(sil, dict):
        return "flower"
    a = sil.get("active", "flower")
    return a if a in PRESETS else "flower"


# ---------------------------------------------------------------- evidence ----
# Shared evidence emitters for the silhouette harnesses (v11.4). One definition, called
# by whichever harness renders, so a stage render and an sbs render emit the same report
# shape and neither drifts into its own dialect. Born 2026-09-22 from the pinned evidence
# standard: "frames without a report are not evidence" and "the committed harness must be
# the harness that ran". See AGENTS.md -> Evidence standard.
EVIDENCE_VERSION = "v11.4-1"


def mesh_census(ob):
    """Evaluated-mesh census for one object: counts + material ids.

    boundary_edges / non_manifold_edges are the two numbers the silhouette gate claims;
    materials is the list that proves the in-tree SetMaterial still resolves (a metals
    tree routes through SetMaterial, so editing Principled does nothing).
    """
    import bmesh
    dg = bpy.context.evaluated_depsgraph_get()
    ev = ob.evaluated_get(dg)
    me = ev.to_mesh()
    bm = bmesh.new()
    bm.from_mesh(me)
    out = {
        "verts": len(bm.verts),
        "edges": len(bm.edges),
        "faces": len(bm.faces),
        "boundary_edges": sum(1 for e in bm.edges if e.is_boundary),
        "non_manifold_edges": sum(1 for e in bm.edges if not e.is_manifold),
        "loose_verts": sum(1 for v in bm.verts if not v.link_edges),
        "loose_edges": sum(1 for e in bm.edges if not e.link_faces),
        "materials": [m.name if m is not None else None for m in ob.data.materials],
    }
    bm.free()
    ev.to_mesh_clear()
    return out


def ink_report(fname, polarity="dark", ink_max=0.02, bright_margin=0.10):
    """Read a rendered PNG back and measure the ink field.

    Polarity matters and is NOT guessable: the V11 flatten recipe rewires the in-tree
    SIL_Gold to a BLACK Emission node, so on that pass the objects are the dark minority
    against a bright backdrop — the opposite of a light-on-black mask. Measured
    2026-09-22 on v114_sbs_sil_*: backdrop modal 0.44, dark corners 0.196 (vignette),
    objects exactly 0.0. A blanket `pixel > 0.02` counts the whole backdrop as ink.

    Reports BOTH fractions plus the backdrop/corner readings, so the record states the
    raw evidence rather than only the interpretation. bbox / min_axis / gap are computed
    on the selected mask only. Only meaningful for passes where the subject is one flat
    value: on a lit beauty shot this describes the frame, not the object.

    numpy is bundled with Blender; the project's system python has neither numpy nor PIL.
    """
    import numpy as np
    img = bpy.data.images.load(fname, check_existing=False)
    try:
        w, h = img.size
        buf = np.empty(w * h * 4, dtype=np.float32)
        img.pixels.foreach_get(buf)
        g = buf.reshape(h, w, 4)[:, :, :3].max(axis=2)
        vals, counts = np.unique(np.round(g, 2), return_counts=True)
        modal = float(vals[int(np.argmax(counts))])
        corner = float(g[0, 0])
        mask = (g < ink_max) if polarity == "dark" else (g > modal + bright_margin)
        rec = {"file": fname, "px": [w, h], "polarity": polarity,
               "ink_max": ink_max, "bright_margin": bright_margin,
               "backdrop_modal": round(modal, 4), "corner": round(corner, 4),
               "frame_min": round(float(g.min()), 4),
               "frame_max": round(float(g.max()), 4),
               "frac_dark": round(float((g < ink_max).mean()), 4),
               "frac_bright": round(float((g > modal + bright_margin).mean()), 4),
               "ink_px": int(mask.sum()), "ink_pct": round(100.0 * float(mask.mean()), 3),
               "ink_bbox_px": None, "ink_w_px": 0, "ink_h_px": 0,
               "min_axis_px": 0, "max_column_gap_px": 0, "ink_col_runs": 0,
               # Framing: does the ink reach the frame border? A subject cropped by the
               # frame invalidates every bbox/legibility number below it. Sides are named
               # by buffer axis on purpose — Blender's pixel buffer is bottom-up, so
               # "row_min" is the bottom of the image and a top/bottom label would be a
               # guess. Added 2026-09-22 after the assertion read the key and died on
               # KeyError, which cost the whole report (frames, no report = not evidence).
               "touch_edge": False, "touch_edge_sides": []}
        if not mask.any():
            return rec
        cols = np.flatnonzero(mask.any(axis=0))
        rows = np.flatnonzero(mask.any(axis=1))
        x0, x1 = int(cols[0]), int(cols[-1])
        y0, y1 = int(rows[0]), int(rows[-1])
        gap = run = runs = 0
        for has_ink in mask[:, x0:x1 + 1].any(axis=0):
            if has_ink:
                gap = max(gap, run)
                if run:
                    runs += 1
                run = 0
            else:
                run += 1
        hits = []
        if x0 <= 0:
            hits.append("col_min")
        if x1 >= w - 1:
            hits.append("col_max")
        if y0 <= 0:
            hits.append("row_min")
        if y1 >= h - 1:
            hits.append("row_max")
        rec.update({"ink_bbox_px": [x0, y0, x1, y1],
                    "ink_w_px": x1 - x0 + 1, "ink_h_px": y1 - y0 + 1,
                    "min_axis_px": int(min(x1 - x0 + 1, y1 - y0 + 1)),
                    "max_column_gap_px": int(gap), "ink_col_runs": runs + 1,
                    "touch_edge": bool(hits), "touch_edge_sides": hits})
        return rec
    finally:
        bpy.data.images.remove(img)


def tree_detail_nodes(tree):
    """Report the v11.4 in-tree detail and the SetMaterial ids that actually resolve.

    A metals tree routes the surface through SetMaterial, so the node ids here — not
    `obj.data.materials` — are what proves the silhouette objects carry a material at all.
    """
    nodes = [n.name for n in tree.nodes]
    detail = sorted(n for n in nodes if n.lower().startswith("v114"))
    mats = []
    for n in tree.nodes:
        if n.bl_idname == 'GeometryNodeSetMaterial':
            m = n.inputs['Material'].default_value
            mats.append({"node": n.name, "material": m.name if m else None})
    return {"node_count": len(nodes), "detail_nodes": detail,
            "detail_count": len(detail), "set_material": mats}


def report_assert(payload, aid, ok, detail):
    """Append one assertion row to payload['assertions'] and return the boolean."""
    payload.setdefault("assertions", []).append(
        {"id": aid, "pass": bool(ok), "detail": detail})
    return bool(ok)


def write_report(path, payload):
    """Write the assertion report next to the frames (rule 3) as UTF-8 JSON."""
    import json
    with open(path, "w", encoding="utf-8") as fh:
        json.dump(payload, fh, indent=2, sort_keys=True)
        fh.write("\n")
    print("[report]", path)
    return path

