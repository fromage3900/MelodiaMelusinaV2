"""gen_flower_brooch_v10.py -- PETAL SYSTEM: parametric botanical surfaces (v8 gala kept): gems + settings + empty-socket reliquary + en-tremblant dangles.

v8 additions over v7 (all backward compatible: absent genome traits = v7 behaviour):
  * gems{}: faceted flat-shaded stones (icosphere), bezel ring on the plate band, centre stone
    prong-set with 4 claws -- or an EMPTY SOCKET (the reliquary idea from BROOCH_IDENTITY_RESEARCH).
    Element-gem materials created in-tree (MID_Gem_<Element>, colours from genome).
  * dangles{}: en-tremblant chains (hinge + N links + terminal drop) on the front arc only,
    each with its own phase; per-dangle sway = Sway * sin(TAU * frame*Rate/60 + phase).
    Sway = 0 is the still-pose control for photo captures.
  * new sockets: Gems On / Ring Count / Ring Gem Size / Gem Size / Dangles On / Dangle Sway /
    Dangle Rate. Chains ride MID_Petal WITHOUT the cast (voxels would eat 2.8 mm links).

v7 additions over v6:
  F1  Cast SDF finish (in-tree, Blender 5.0 grid chain): gold group -> MeshToSDFGrid ->
      SDFGridFillet -> GridToMesh -> re-shade, socket-gated ("Cast Finish",
      "Cast Voxel (mm)", "Cast Fillet Iters"). Pass A (nominal measure) runs it off.
  F2  Surface-sampled pave seating: beads + seat cups follow the REAL gold surface
      (SampleNearestSurface with Value=Position) so the ring never floats at plate->step.
  F3  Hardware v7: hinge tube end-collars + jaw pivot boss.
  F4  (companion) GN_Brooch_Sparkles_v7 -- built by Tools/gen_brooch_sparkles_v7.py.
  F5  Pad tightening (offset 0.24, ratio 0.62/0.74) for a softer inset read.
Everything from v6 kept: real-world sizing (1u = 10 cm), real-structure clasp,
seat cups + bezel, plate step + collar, bloom driver, Bevel_Detail stack position.

Run:  bridge --file Tools/gen_flower_brooch_v7.py   (live session; script does not save)
"""
import importlib.util
import json
import math
import os
import random
import sys
import time
import traceback

# ensure Tools/ is importable for the sparkle companion
_TOOLS_DIR = os.path.dirname(os.path.abspath(__file__))
if _TOOLS_DIR not in sys.path:
    sys.path.insert(0, _TOOLS_DIR)

import bpy

BACKUP_DIR = r"P:/MelodiaMelusinaV2-Laptop/Saved/Accessories/brooch_lab/backups"
GENOME_DIR = r"P:/MelodiaMelusinaV2-Laptop/Saved/Accessories/brooch_lab/genome"
HERO_ID = "melodia_brooch_v1"
OBJ_NAME = "FlowerBrooch"
R90 = math.radians(90.0)
REPORT_V10 = r"P:/MelodiaMelusinaV2-Laptop/Saved/Accessories/brooch_lab/BUILD_REPORT_V10.txt"

GENOMES = (
    ("melodia_brooch_v1", "GN_FlowerBrooch_v10"),
    ("melodia_brooch_mini_v1", "GN_FlowerBrooch_v10_mini"),
    ("melodia_brooch_halo_v1", "GN_FlowerBrooch_v10_halo"),
    ("melodia_brooch_comet_v1", "GN_FlowerBrooch_v10_comet"),
    ("melodia_brooch_nova_v1", "GN_FlowerBrooch_v10_nova"),
    ("melodia_gala_tide_v1", "GN_FlowerBrooch_gala_tide_v10"),
    ("melodia_gala_umbra_v1", "GN_FlowerBrooch_gala_umbra_v10"),
)


# ---------------------------------------------------------------- helpers ----
def load_genome_module():
    path = os.path.join(GENOME_DIR, "brooch_genome.py")
    spec = importlib.util.spec_from_file_location("brooch_genome", path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def backup():
    os.makedirs(BACKUP_DIR, exist_ok=True)
    stamp = time.strftime("%Y%m%d_%H%M%S")
    dst = os.path.join(BACKUP_DIR, "FlowerBrooch_%s.blend" % stamp)
    try:
        bpy.ops.wm.save_as_mainfile(filepath=dst, copy=True)
        print("backup(ops copy):", dst)
        return dst
    except Exception as exc:
        print("backup: ops copy failed (%r), falling back to disk copy" % (exc,))
    src = bpy.data.filepath
    if src and os.path.exists(src):
        shutil.copy2(src, dst)
        print("backup(disk copy of last SAVED state):", dst)
        return dst
    print("backup: FAILED (no file on disk)")
    return None


def mk(tree, bl_id, name, loc):
    n = tree.nodes.new(bl_id)
    n.name = name
    n.location = loc
    return n


def d0(node, idx, value):
    try:
        node.inputs[idx].default_value = value
    except Exception as exc:
        print("  warn: could not set %s.inputs[%d] (%r)" % (node.name, idx, exc))
    return node


def dn(node, name, value):
    try:
        node.inputs[name].default_value = value
    except Exception as exc:
        print("  warn: could not set %s.inputs['%s'] (%r)" % (node.name, name, exc))
    return node


def L(tree, src, src_sock, dst, dst_sock):
    return tree.links.new(src.outputs[src_sock], dst.inputs[dst_sock])


def first_geo_out(node):
    for name in ("Geometry", "Mesh"):
        try:
            node.outputs[name]
            return name
        except Exception:
            pass
    return node.outputs[0].name


def mathx(tree, name, op, loc, a=None, b=None, c=None):
    n = mk(tree, 'ShaderNodeMath', name, loc)
    n.operation = op
    if a is not None:
        d0(n, 0, a)
    if b is not None:
        d0(n, 1, b)
    if c is not None:
        d0(n, 2, c)
    return n


def combine(tree, name, loc):
    return mk(tree, 'ShaderNodeCombineXYZ', name, loc)


def rnd(tree, name, loc):
    n = None
    for bl_id in ('FunctionNodeRandomValue', 'GeometryNodeRandomValue'):
        try:
            n = mk(tree, bl_id, name, loc)
            break
        except Exception:
            n = None
    if n is None:
        raise RuntimeError("no Random Value node class found")
    try:
        n.data_type = 'FLOAT'
    except Exception as exc:
        print("  warn: random data_type (%r)" % (exc,))
    return n


def rand_seed(node):
    for s in node.inputs:
        if s.name.lower() == 'seed' or s.identifier.lower().endswith('seed'):
            return s
    return None


def smooth_shade(tree, geo_node, geo_sock, loc, label):
    try:
        n = mk(tree, 'GeometryNodeSetShadeSmooth', label, loc)
        L(tree, geo_node, geo_sock, n, "Geometry")
        return n, "Geometry"
    except Exception as exc:
        print("warn: SetShadeSmooth %s (%r)" % (label, exc))
        return geo_node, geo_sock


def set_material(tree, geo_node, geo_sock, mat, loc, label):
    if mat is None:
        return geo_node, geo_sock
    try:
        n = mk(tree, 'GeometryNodeSetMaterial', label, loc)
        L(tree, geo_node, geo_sock, n, "Geometry")
        dn(n, "Material", mat)
        return n, "Geometry"
    except Exception as exc:
        print("warn: SetMaterial %s (%r)" % (label, exc))
        return geo_node, geo_sock


def cylinder(tree, name, loc, radius, depth, verts=16, rot=(0.0, 0.0, 0.0), trans=(0.0, 0.0, 0.0)):
    cyl = mk(tree, 'GeometryNodeMeshCylinder', name, loc)
    dn(cyl, "Radius", radius)
    dn(cyl, "Depth", depth)
    it = None
    for v in ("Vertices", "Vertices"):
        try:
            dn(cyl, v, verts)
            break
        except Exception:
            pass
    tr = mk(tree, 'GeometryNodeTransform', name + " xf", (loc[0], loc[1] + 120))
    L(tree, cyl, "Mesh", tr, "Geometry")
    dn(tr, "Rotation", rot)
    dn(tr, "Translation", trans)
    return tr


def box(tree, name, loc, size, rot=(0.0, 0.0, 0.0), trans=(0.0, 0.0, 0.0)):
    b = mk(tree, 'GeometryNodeMeshCube', name, loc)
    dn(b, "Size", size)
    tr = mk(tree, 'GeometryNodeTransform', name + " xf", (loc[0], loc[1] + 120))
    L(tree, b, "Mesh", tr, "Geometry")
    dn(tr, "Rotation", rot)
    dn(tr, "Translation", trans)
    return tr


def torus(tree, name, loc, major, minor, mseg=32, nseg=8, rot=(0.0, 0.0, 0.0), trans=(0.0, 0.0, 0.0)):
    # Blender 5.2 has no torus primitive node -> ring = curve circle + circle profile.
    # returns the Transform node; wire live radii into <name> path / <name> prof "Radius".
    path = mk(tree, 'GeometryNodeCurvePrimitiveCircle', name + " path", loc)
    try:
        dn(path, "Resolution", mseg)
    except Exception:
        pass
    try:
        dn(path, "Radius", major)
    except Exception as exc:
        print("  warn: torus path radius (%r)" % (exc,))
    prof = mk(tree, 'GeometryNodeCurvePrimitiveCircle', name + " prof",
              (loc[0] - 260, loc[1] - 160))
    try:
        dn(prof, "Resolution", nseg)
    except Exception:
        pass
    try:
        dn(prof, "Radius", minor)
    except Exception as exc:
        print("  warn: torus prof radius (%r)" % (exc,))
    c2m = mk(tree, 'GeometryNodeCurveToMesh', name, (loc[0], loc[1] + 80))
    L(tree, path, "Curve", c2m, "Curve")
    L(tree, prof, "Curve", c2m, "Profile Curve")
    tr = mk(tree, 'GeometryNodeTransform', name + " xf", (loc[0], loc[1] + 200))
    L(tree, c2m, "Mesh", tr, "Geometry")
    dn(tr, "Rotation", rot)
    dn(tr, "Translation", trans)
    return tr


def wire_radius(tree, node_name, value_node, indent=""):
    # link a live value into a curve circle's "Radius" socket (name churn safe)
    n = tree.nodes.get(node_name)
    if n is None:
        print("%swarn: node %r missing for radius wire" % (indent, node_name))
        return
    for sock in ("Radius", "radius"):
        try:
            tree.links.new(value_node.outputs["Value"], n.inputs[sock])
            return
        except Exception:
            continue
    try:
        tree.links.new(value_node.outputs["Value"], n.inputs[1])
        return
    except Exception as exc:
        print("%swarn: radius wire failed for %s (%r)" % (indent, node_name, exc))


def resolve_material(mats, key, fallback_key, fallback_mat):
    """Material-ID architecture (2026-09-17): per-part IDs for texture masks. Copy-on-first-use --
    a named ID missing from the file is created as a copy of the fallback material, so the look is
    unchanged until the presets differentiate it. Never overwrites an existing material."""
    want = mats.get(key) or mats.get(fallback_key)
    if not want:
        return fallback_mat
    m = bpy.data.materials.get(want)
    if m is None:
        if fallback_mat is None:
            print("  [mat-id] %s missing and no fallback" % want)
            return None
        m = fallback_mat.copy()
        m.name = want
        print("  [mat-id] created %s as a copy of %s" % (want, fallback_mat.name))
    return m


def make_gem_material(name, color, rough=0.05, ior=1.7, film=460.0):
    """Idempotent faceted-gem material: glossy dielectric + coat + thin film (element colours)."""
    m = bpy.data.materials.get(name)
    if m is None:
        m = bpy.data.materials.new(name)
    m.use_nodes = True
    nt = m.node_tree
    p = None
    for n in nt.nodes:
        if n.type == 'BSDF_PRINCIPLED':
            p = n
            break
    if p is None:
        for n in list(nt.nodes):
            nt.nodes.remove(n)
        out = nt.nodes.new('ShaderNodeOutputMaterial')
        p = nt.nodes.new('ShaderNodeBsdfPrincipled')
        nt.links.new(p.outputs["BSDF"], out.inputs["Surface"])
    for k, v in (("Base Color", tuple(color)[:3] + (1.0,)), ("Roughness", rough), ("IOR", ior),
                 ("Metallic", 0.0), ("Coat Weight", 1.0), ("Coat Roughness", 0.03),
                 ("Thin Film Thickness", film), ("Thin Film IOR", 1.55)):
        try:
            p.inputs[k].default_value = v
        except Exception:
            pass
    return m


def empty_geo(tree, name, loc):
    p = mk(tree, 'GeometryNodePoints', name, loc)
    dn(p, "Count", 0)
    return p


def geo_switch(tree, name, loc, cond_sock_parent, cond_sock, false_src, true_src):
    sw = mk(tree, 'GeometryNodeSwitch', name, loc)
    try:
        sw.input_type = 'GEOMETRY'
    except Exception as exc:
        print("  warn: switch input_type (%r)" % (exc,))
    try:
        tree.links.new(cond_sock_parent.outputs[cond_sock], sw.inputs["Switch"])
    except Exception as exc:
        print("  warn: switch cond link (%r)" % (exc,))
    L(tree, false_src[0], false_src[1], sw, "False")
    L(tree, true_src[0], true_src[1], sw, "True")
    return sw, first_geo_out(sw)


def gn_only(ob):
    """Temporarily hide every non-GN modifier so measurement sees the raw GN output."""
    saved = []
    for m in ob.modifiers:
        is_gn = (m.type == 'NODES' and m.node_group is not None
                 and (m.node_group.name.startswith("GN_FlowerBrooch")
                      or m.node_group.name.startswith("GN_BroochDangles")))
        if is_gn:
            continue
        saved.append((m, m.show_viewport))
        m.show_viewport = False
    return saved


def restore_mods(saved):
    for m, v in saved:
        try:
            m.show_viewport = v
        except Exception:
            pass


def gold_dims_from(per_mat):
    for name, dims in per_mat.items():
        if name and "Petal" in name:
            return dims
    return None


# ---------------------------------------------------------------- build ------
def petal_surface(tree, tag, loc, gin, base_w, tip_pow, bend0, recurve, cup, ridge,
                  wave_amp, wave_freq, thick, ripple=0.0, ripple_freq=2.5, waist=0.0,
                  grids=(11, 20), subd=2):
    """v10 petal surface, LOCAL units: x in [-1,1] margin, y in [-1,1] base->tip; the instance
    scale (W,L,T)*s squashes it later. Cage -> width profile, spine bend+recurve, cup, margin
    wave, midrib ridge -> dual sheet (+-t/2) -> weld (watertight pillow) -> SubdivisionSurface L2
    with a midrib edge crease. Rounded rim, continuous silhouette; no extruded knife edges."""
    PI = 3.141592653589793
    x0, y0 = loc

    def clamp01(name, at, src):
        mx = mathx(tree, name + " max0", 'MAXIMUM', at, b=0.0)
        L(tree, src, "Value", mx, 0)
        mn = mathx(tree, name + " min1", 'MINIMUM', (at[0] + 130, at[1]), b=1.0)
        L(tree, mx, "Value", mn, 0)
        return mn

    grid = mk(tree, 'GeometryNodeMeshGrid', "%s grid" % tag, (x0, y0))
    dn(grid, "Vertices X", int(grids[0]))
    dn(grid, "Vertices Y", int(grids[1]))
    dn(grid, "Size X", 2.0)
    dn(grid, "Size Y", 2.0)

    pos = mk(tree, 'GeometryNodeInputPosition', "%s pos" % tag, (x0 - 420, y0 + 80))
    xyz = mk(tree, 'ShaderNodeSeparateXYZ', "%s xyz" % tag, (x0 - 360, y0 + 80))
    L(tree, pos, "Position", xyz, "Vector")

    u = mathx(tree, "%s u" % tag, 'MULTIPLY_ADD', (x0 - 200, y0 + 160), b=0.5, c=0.5)
    L(tree, xyz, "Y", u, 0)

    tp = mathx(tree, "%s u^p" % tag, 'POWER', (x0 - 60, y0 + 200), b=tip_pow)
    L(tree, u, "Value", tp, 0)
    ang = mathx(tree, "%s *pi" % tag, 'MULTIPLY', (x0 + 60, y0 + 200), b=PI)
    L(tree, tp, "Value", ang, 0)
    sw = mathx(tree, "%s sin" % tag, 'SINE', (x0 + 180, y0 + 200))
    L(tree, ang, "Value", sw, 0)
    wc = mathx(tree, "%s w floor" % tag, 'MAXIMUM', (x0 + 300, y0 + 200), b=0.04)
    L(tree, sw, "Value", wc, 0)
    wsrc = wc
    if waist > 0.0:
        utw = mathx(tree, "%s waist 1-u" % tag, 'MULTIPLY_ADD', (x0 + 300, y0 + 320), b=-1.0, c=1.0)
        L(tree, u, "Value", utw, 0)
        uuw = mathx(tree, "%s waist u(1-u)" % tag, 'MULTIPLY', (x0 + 440, y0 + 320))
        L(tree, u, "Value", uuw, 0)
        L(tree, utw, "Value", uuw, 1)
        uu4w = mathx(tree, "%s waist *4" % tag, 'MULTIPLY', (x0 + 580, y0 + 320), b=4.0)
        L(tree, uuw, "Value", uu4w, 0)
        waw = mathx(tree, "%s *waist" % tag, 'MULTIPLY', (x0 + 720, y0 + 320), b=waist)
        L(tree, uu4w, "Value", waw, 0)
        wbw = mathx(tree, "%s 1-waist" % tag, 'SUBTRACT', (x0 + 860, y0 + 320), a=1.0)
        L(tree, waw, "Value", wbw, 1)
        wmw = mathx(tree, "%s w*(1-waist)" % tag, 'MULTIPLY', (x0 + 1000, y0 + 200))
        L(tree, wc, "Value", wmw, 0)
        L(tree, wbw, "Value", wmw, 1)
        wsrc = wmw
    # A1: super-ellipse margin exponent (continuous round→squarish→needle control)
    # drives the petal outline as a power of the base width profile
    w_base = mathx(tree, "%s w(u) base" % tag, 'MULTIPLY', (x0 + 450, y0 + 200), b=base_w)
    L(tree, wsrc, "Value", w_base, 0)
    w_exp = mathx(tree, "%s w(u) margin" % tag, 'POWER', (x0 + 600, y0 + 200))
    L(tree, w_base, "Value", w_exp, 0)
    L(tree, gin, "Margin Exp", w_exp, 1)
    w = w_exp
    if ripple > 0.0:
        rf = mathx(tree, "%s u*rf" % tag, 'MULTIPLY', (x0 + 180, y0 + 320), b=ripple_freq * 2.0 * PI)
        L(tree, u, "Value", rf, 0)
        rs = mathx(tree, "%s rip sin" % tag, 'SINE', (x0 + 320, y0 + 320))
        L(tree, rf, "Value", rs, 0)
        rsc = mathx(tree, "%s rip*amp" % tag, 'MULTIPLY', (x0 + 450, y0 + 320), b=ripple)
        L(tree, rs, "Value", rsc, 0)
        r1 = mathx(tree, "%s 1+rip" % tag, 'ADD', (x0 + 580, y0 + 320), b=1.0)
        L(tree, rsc, "Value", r1, 0)
        w_rip = mathx(tree, "%s w*rip" % tag, 'MULTIPLY', (x0 + 450, y0 + 200))
        L(tree, w, "Value", w_rip, 0)
        L(tree, r1, "Value", w_rip, 1)
        w = w_rip

    xnew = mathx(tree, "%s x*w" % tag, 'MULTIPLY', (x0 + 580, y0 + 120))
    L(tree, xyz, "X", xnew, 0)
    L(tree, w, "Value", xnew, 1)

    ax = mathx(tree, "%s |x|" % tag, 'ABSOLUTE', (x0 + 580, y0 - 40))
    L(tree, xyz, "X", ax, 0)
    e0 = mathx(tree, "%s 1-|x|" % tag, 'SUBTRACT', (x0 + 720, y0 - 40), a=1.0)
    L(tree, ax, "Value", e0, 1)
    ec = clamp01("%s edge clamp" % tag, (x0 + 850, y0 - 40), e0)
    e2 = mathx(tree, "%s edge^2" % tag, 'POWER', (x0 + 1110, y0 - 40), b=2.0)
    L(tree, ec, "Value", e2, 0)

    tu2 = mathx(tree, "%s u^2" % tag, 'POWER', (x0 - 60, y0 + 380), b=2.0)
    L(tree, u, "Value", tu2, 0)
    s1 = mathx(tree, "%s bend*u2" % tag, 'MULTIPLY', (x0 + 60, y0 + 380), b=bend0)
    L(tree, tu2, "Value", s1, 0)
    tu4 = mathx(tree, "%s u^4" % tag, 'POWER', (x0 + 60, y0 + 500), b=4.0)
    L(tree, u, "Value", tu4, 0)
    s2 = mathx(tree, "%s recurve*u4" % tag, 'MULTIPLY', (x0 + 180, y0 + 500), b=recurve)
    L(tree, tu4, "Value", s2, 0)
    spine = mathx(tree, "%s spine" % tag, 'ADD', (x0 + 300, y0 + 440))
    L(tree, s1, "Value", spine, 0)
    L(tree, s2, "Value", spine, 1)

    ur = mathx(tree, "%s 1-0.4u" % tag, 'MULTIPLY_ADD', (x0 + 580, y0 + 260), b=-0.4, c=1.0)
    L(tree, u, "Value", ur, 0)
    cupt = mathx(tree, "%s cup*e2" % tag, 'MULTIPLY', (x0 + 720, y0 + 260), b=cup)
    L(tree, e2, "Value", cupt, 0)
    cupf = mathx(tree, "%s cup relax" % tag, 'MULTIPLY', (x0 + 860, y0 + 260))
    L(tree, cupt, "Value", cupf, 0)
    L(tree, ur, "Value", cupf, 1)

    wf = mathx(tree, "%s u*flow" % tag, 'MULTIPLY', (x0 + 580, y0 + 560), b=wave_freq * 2.0 * PI)
    L(tree, u, "Value", wf, 0)
    wv = mathx(tree, "%s sin wave" % tag, 'SINE', (x0 + 720, y0 + 560))
    L(tree, wf, "Value", wv, 0)
    wam = mathx(tree, "%s wave*amp" % tag, 'MULTIPLY', (x0 + 860, y0 + 560), b=wave_amp)
    L(tree, wv, "Value", wam, 0)
    wae = mathx(tree, "%s wave*e2" % tag, 'MULTIPLY', (x0 + 1000, y0 + 560))
    L(tree, wam, "Value", wae, 0)
    L(tree, e2, "Value", wae, 1)

    rg = mathx(tree, "%s ridge*e" % tag, 'MULTIPLY', (x0 + 720, y0 - 180), b=ridge)
    L(tree, ec, "Value", rg, 0)

    zold = mathx(tree, "%s spine+cup" % tag, 'ADD', (x0 + 1000, y0 + 440))
    L(tree, spine, "Value", zold, 0)
    L(tree, cupf, "Value", zold, 1)
    z1 = mathx(tree, "%s +wave" % tag, 'ADD', (x0 + 1140, y0 + 440))
    L(tree, zold, "Value", z1, 0)
    L(tree, wae, "Value", z1, 1)
    zmid = mathx(tree, "%s +ridge" % tag, 'ADD', (x0 + 1280, y0 + 440))
    L(tree, z1, "Value", zmid, 0)
    L(tree, rg, "Value", zmid, 1)

    et = mathx(tree, "%s edge^0.8" % tag, 'POWER', (x0 + 720, y0 - 320), b=0.8)
    L(tree, ec, "Value", et, 0)
    ut = mathx(tree, "%s 1-u" % tag, 'MULTIPLY_ADD', (x0 + 580, y0 + 380), b=-1.0, c=1.0)
    L(tree, u, "Value", ut, 0)
    utm = mathx(tree, "%s u(1-u)" % tag, 'MULTIPLY', (x0 + 720, y0 + 380))
    L(tree, u, "Value", utm, 0)
    L(tree, ut, "Value", utm, 1)
    ut4 = mathx(tree, "%s *4" % tag, 'MULTIPLY', (x0 + 860, y0 + 380), b=4.0)
    L(tree, utm, "Value", ut4, 0)
    utc = clamp01("%s u clamp" % tag, (x0 + 990, y0 + 380), ut4)
    uts = mathx(tree, "%s sqrt" % tag, 'SQRT', (x0 + 1250, y0 + 380))
    L(tree, utc, "Value", uts, 0)
    tt = mathx(tree, "%s t_x" % tag, 'MULTIPLY', (x0 + 1390, y0 + 300))
    L(tree, et, "Value", tt, 0)
    L(tree, uts, "Value", tt, 1)
    tv = mathx(tree, "%s t_val" % tag, 'MULTIPLY', (x0 + 1530, y0 + 300), b=thick)
    L(tree, tt, "Value", tv, 0)
    half = mathx(tree, "%s t/2" % tag, 'MULTIPLY', (x0 + 1670, y0 + 300), b=0.5)
    L(tree, tv, "Value", half, 0)

    zt = mathx(tree, "%s z+t" % tag, 'ADD', (x0 + 1670, y0 + 460))
    L(tree, zmid, "Value", zt, 0)
    L(tree, half, "Value", zt, 1)
    top = mk(tree, 'GeometryNodeSetPosition', "%s top" % tag, (x0 + 1810, y0 + 120))
    L(tree, grid, "Mesh", top, "Geometry")
    pt = combine(tree, "%s pos top" % tag, (x0 + 1660, y0 + 40))
    L(tree, xnew, "Value", pt, "X")
    L(tree, xyz, "Y", pt, "Y")
    L(tree, zt, "Value", pt, "Z")
    L(tree, pt, "Vector", top, "Position")

    zb = mathx(tree, "%s z-t" % tag, 'SUBTRACT', (x0 + 1670, y0 - 20))
    L(tree, zmid, "Value", zb, 0)
    L(tree, half, "Value", zb, 1)
    bot = mk(tree, 'GeometryNodeSetPosition', "%s bot" % tag, (x0 + 1810, y0 - 200))
    L(tree, grid, "Mesh", bot, "Geometry")
    pb = combine(tree, "%s pos bot" % tag, (x0 + 1660, y0 - 280))
    L(tree, xnew, "Value", pb, "X")
    L(tree, xyz, "Y", pb, "Y")
    L(tree, zb, "Value", pb, "Z")
    L(tree, pb, "Vector", bot, "Position")

    jr = mk(tree, 'GeometryNodeJoinGeometry', "%s join" % tag, (x0 + 1960, y0 - 60))
    L(tree, top, "Geometry", jr, "Geometry")
    L(tree, bot, "Geometry", jr, "Geometry")
    mg = mk(tree, 'GeometryNodeMergeByDistance', "%s weld" % tag, (x0 + 2100, y0 - 60))
    L(tree, jr, "Geometry", mg, "Geometry")
    dn(mg, "Distance", 1.0e-5)

    p2 = mk(tree, 'GeometryNodeInputPosition', "%s pos2" % tag, (x0 + 1960, y0 - 360))
    x2 = mk(tree, 'ShaderNodeSeparateXYZ', "%s xyz2" % tag, (x0 + 2030, y0 - 360))
    L(tree, p2, "Position", x2, "Vector")
    ax2 = mathx(tree, "%s |x| post" % tag, 'ABSOLUTE', (x0 + 2100, y0 - 360))
    L(tree, x2, "X", ax2, 0)
    cr0 = mathx(tree, "%s 1-|x|/k" % tag, 'MULTIPLY_ADD', (x0 + 2240, y0 - 360), b=-1.0 / 0.30, c=1.0)
    L(tree, ax2, "Value", cr0, 0)
    crc = clamp01("%s crease clamp" % tag, (x0 + 2380, y0 - 360), cr0)

    sd = mk(tree, 'GeometryNodeSubdivisionSurface', "%s subd" % tag, (x0 + 2240, y0 - 60))
    L(tree, mg, "Geometry", sd, "Mesh")
    dn(sd, "Level", int(subd))
    try:
        L(tree, crc, "Value", sd, "Edge Crease")
    except Exception as exc:
        print("  warn: subd crease link (%r)" % (exc,))
    dn(sd, "Quality", 2)

    sh = mk(tree, 'GeometryNodeSetShadeSmooth', "%s smooth" % tag, (x0 + 2400, y0 - 60))
    L(tree, sd, "Mesh", sh, "Geometry")
    return sh, "Geometry"


def whorl_chain(tree, tag, gin, ix, loc):
    """One whorl's phyllotaxis placement (port of the v5 chain, index source = ix so a whorl
    can use a global-index offset). Adds a per-petal roll on the Y euler for variety."""
    x0, y0 = loc
    t_sub = mathx(tree, "%s n-1" % tag, 'SUBTRACT', (x0, y0), a=0.0)
    L(tree, gin, "Petal Count", t_sub, 0)
    d0(t_sub, 1, 1.0)
    t_max = mathx(tree, "%s max(n-1,1)" % tag, 'MAXIMUM', (x0 + 150, y0 - 80), b=1.0)
    L(tree, t_sub, "Value", t_max, 0)
    t_div = mathx(tree, "%s t=i/(n-1)" % tag, 'DIVIDE', (x0 + 300, y0 - 40))
    L(tree, ix, "Value", t_div, 0)
    L(tree, t_max, "Value", t_div, 1)
    r_a = rnd(tree, "%s randA" % tag, (x0, y0 - 300))
    seed_a = rand_seed(r_a)
    if seed_a is not None:
        L(tree, ix, "Value", r_a, seed_a.name)
    d0(r_a, 0, 0.0)
    d0(r_a, 1, 1.0)
    j0 = mathx(tree, "%s rA-0.5" % tag, 'SUBTRACT', (x0 + 150, y0 - 280), b=0.5)
    L(tree, r_a, "Value", j0, 0)
    j1 = mathx(tree, "%s *chaos" % tag, 'MULTIPLY', (x0 + 300, y0 - 320))
    L(tree, j0, "Value", j1, 0)
    L(tree, gin, "Chaos", j1, 1)
    j2 = mathx(tree, "%s jitter rad" % tag, 'MULTIPLY', (x0 + 450, y0 - 280), b=0.35)
    L(tree, j1, "Value", j2, 0)
    th0 = mathx(tree, "%s i*GA" % tag, 'MULTIPLY', (x0 + 300, y0 - 200))
    L(tree, ix, "Value", th0, 0)
    L(tree, gin, "Phyllotaxis Angle", th0, 1)
    th = mathx(tree, "%s theta" % tag, 'ADD', (x0 + 450, y0 - 200))
    L(tree, th0, "Value", th, 0)
    L(tree, j2, "Value", th, 1)
    sq = mathx(tree, "%s sqrt t" % tag, 'SQRT', (x0 + 450, y0 - 40))
    L(tree, t_div, "Value", sq, 0)
    rr = mathx(tree, "%s r" % tag, 'MULTIPLY', (x0 + 600, y0 - 40))
    L(tree, sq, "Value", rr, 0)
    L(tree, gin, "Spread", rr, 1)
    ct = mathx(tree, "%s cos" % tag, 'COSINE', (x0 + 600, y0 - 220))
    sn = mathx(tree, "%s sin" % tag, 'SINE', (x0 + 600, y0 - 320))
    L(tree, th, "Value", ct, 0)
    L(tree, th, "Value", sn, 0)
    px = mathx(tree, "%s px" % tag, 'MULTIPLY', (x0 + 750, y0 - 220))
    L(tree, ct, "Value", px, 0)
    L(tree, rr, "Value", px, 1)
    py = mathx(tree, "%s py" % tag, 'MULTIPLY', (x0 + 750, y0 - 320))
    L(tree, sn, "Value", py, 0)
    L(tree, rr, "Value", py, 1)
    omt = mathx(tree, "%s 1-t" % tag, 'SUBTRACT', (x0 + 600, y0 + 100), a=1.0)
    L(tree, t_div, "Value", omt, 1)
    pz = mathx(tree, "%s pz" % tag, 'MULTIPLY', (x0 + 750, y0 + 100))
    L(tree, omt, "Value", pz, 0)
    L(tree, gin, "Rise", pz, 1)
    vpos = combine(tree, "%s pos" % tag, (x0 + 900, y0 - 220))
    L(tree, px, "Value", vpos, "X")
    L(tree, py, "Value", vpos, "Y")
    L(tree, pz, "Value", vpos, "Z")
    seed_s = mathx(tree, "%s seedS" % tag, 'ADD', (x0 + 450, y0 - 450), b=1000.0)
    L(tree, ix, "Value", seed_s, 0)
    r_s = rnd(tree, "%s randS" % tag, (x0 + 600, y0 - 480))
    seed_sock = rand_seed(r_s)
    if seed_sock is not None:
        L(tree, seed_s, "Value", r_s, seed_sock.name)
    d0(r_s, 0, 0.0)
    d0(r_s, 1, 1.0)
    s0 = mathx(tree, "%s rS-0.5" % tag, 'SUBTRACT', (x0 + 750, y0 - 460), b=0.5)
    L(tree, r_s, "Value", s0, 0)
    s1n = mathx(tree, "%s *chaosS" % tag, 'MULTIPLY', (x0 + 900, y0 - 460))
    L(tree, s0, "Value", s1n, 0)
    L(tree, gin, "Chaos", s1n, 1)
    s2 = mathx(tree, "%s *0.5" % tag, 'MULTIPLY', (x0 + 1050, y0 - 460), b=0.5)
    L(tree, s1n, "Value", s2, 0)
    s3 = mathx(tree, "%s 1+jit" % tag, 'ADD', (x0 + 1200, y0 - 460), b=1.0)
    L(tree, s2, "Value", s3, 0)
    mr = mk(tree, 'ShaderNodeMapRange', "%s falloff" % tag, (x0 + 900, y0 - 330))
    dn(mr, "From Min", 0.0)
    dn(mr, "From Max", 1.0)
    L(tree, t_div, "Value", mr, "Value")
    L(tree, gin, "Inner Size", mr, "To Min")
    dn(mr, "To Max", 1.0)
    stot = mathx(tree, "%s s_tot" % tag, 'MULTIPLY', (x0 + 1050, y0 - 330))
    L(tree, mr, "Result", stot, 0)
    L(tree, s3, "Value", stot, 1)
    scw = mathx(tree, "%s W*s" % tag, 'MULTIPLY', (x0 + 1200, y0 - 330))
    L(tree, stot, "Value", scw, 0)
    L(tree, gin, "Petal Width", scw, 1)
    scl = mathx(tree, "%s L*s" % tag, 'MULTIPLY', (x0 + 1200, y0 - 230))
    L(tree, stot, "Value", scl, 0)
    L(tree, gin, "Petal Length", scl, 1)
    sct = mathx(tree, "%s T*s" % tag, 'MULTIPLY', (x0 + 1200, y0 - 130))
    L(tree, stot, "Value", sct, 0)
    L(tree, gin, "Petal Thickness", sct, 1)
    vsc = combine(tree, "%s scale" % tag, (x0 + 1350, y0 - 250))
    L(tree, scw, "Value", vsc, "X")
    L(tree, scl, "Value", vsc, "Y")
    L(tree, sct, "Value", vsc, "Z")
    cupt = mathx(tree, "%s cup(1-t)" % tag, 'MULTIPLY', (x0 + 900, y0 + 250))
    L(tree, omt, "Value", cupt, 0)
    L(tree, gin, "Cup", cupt, 1)
    tf = mathx(tree, "%s 1+cup" % tag, 'ADD', (x0 + 1050, y0 + 250), b=1.0)
    L(tree, cupt, "Value", tf, 0)
    tl = mathx(tree, "%s tilt_i" % tag, 'MULTIPLY', (x0 + 1200, y0 + 250))
    L(tree, tf, "Value", tl, 0)
    L(tree, gin, "Tilt", tl, 1)
    azn = mathx(tree, "%s theta+90" % tag, 'ADD', (x0 + 1050, y0 + 400), b=R90)
    L(tree, th, "Value", azn, 0)
    tl_n = mathx(tree, "%s -tilt" % tag, 'MULTIPLY', (x0 + 1350, y0 + 250), b=-1.0)
    L(tree, tl, "Value", tl_n, 0)
    roll = mathx(tree, "%s roll" % tag, 'MULTIPLY', (x0 + 300, y0 + 400), b=1.2)
    L(tree, j0, "Value", roll, 0)
    vrot = combine(tree, "%s rot" % tag, (x0 + 1500, y0 + 300))
    L(tree, tl_n, "Value", vrot, "X")
    L(tree, roll, "Value", vrot, "Y")
    L(tree, azn, "Value", vrot, "Z")
    return vpos, vrot, vsc


def petal_system(tree, gin, crown, phy, mat_metal_petal, flutter=False):
    """v10 petal block — extracted from build() for dual use: body tree (invisible sampler
    for accent snap, flutter=False) and petals object (visible + flutter, flutter=True).
    Returns (petal_out, petal_sock). Reads Petal Count/Phyllotaxis Angle/Spread/Petal
    Length/Width/Thickness/Inner Size/Tilt/Cup/Rise/Chaos/Bloom from gin; flutter reads
    Petal Amp + Petal Rate (must exist on the target tree's interface when flutter=True)."""
    ARCH = {
        "round":     ((0.92, 0.55, 1.05, -1.35, 0.55, 0.060, 0.030, 3.5, 1.00, 0.0, 0.0),
                      (0.60, 0.85, 0.90, -0.70, 0.90, 0.050, 0.020, 2.0, 0.80, 0.0, 0.0)),
        "acuminate": ((0.60, 0.95, 1.30, -1.20, 0.70, 0.080, 0.020, 2.0, 0.90, 0.0, 0.0),
                      (0.40, 1.10, 1.50, -0.50, 1.00, 0.065, 0.014, 1.6, 0.70, 0.0, 0.0)),
        "spatulate": ((0.95, 2.20, 0.95, -0.95, 0.50, 0.055, 0.025, 3.0, 1.00, 0.0, 0.12),
                      (0.62, 2.40, 0.85, -0.60, 0.75, 0.045, 0.018, 2.5, 0.80, 0.0, 0.10)),
        "cordate":   ((1.00, 2.60, 1.10, -1.60, 0.35, 0.070, 0.020, 2.5, 1.00, 0.0, 0.0),
                      (0.65, 2.80, 1.00, -1.00, 0.60, 0.055, 0.015, 2.0, 0.80, 0.0, 0.0)),
        "frilled":   ((0.85, 0.70, 0.90, -1.20, 0.45, 0.045, 0.040, 4.0, 0.95, 0.06, 0.0),
                      (0.55, 0.85, 0.80, -0.80, 0.70, 0.040, 0.030, 3.0, 0.75, 0.05, 0.0)),
        "reflexed":  ((0.88, 0.62, 1.25, -1.90, 0.70, 0.065, 0.020, 2.0, 1.00, 0.0, 0.0),
                      (0.58, 0.75, 1.35, -1.20, 0.95, 0.055, 0.015, 1.8, 0.80, 0.0, 0.0)),
        "cupped":    ((0.80, 0.75, 0.55, -0.60, 1.30, 0.080, 0.020, 2.0, 1.00, 0.0, 0.0),
                      (0.52, 0.85, 0.50, -0.40, 1.10, 0.060, 0.015, 1.8, 0.80, 0.0, 0.0)),
    }
    prof = str(crown.get("petal_profile", "round")).lower()
    arch_name = {"pointed": "acuminate"}.get(prof, prof)
    if arch_name not in ARCH:
        arch_name = "round"
    P_OUT, P_IN = ARCH[arch_name]

    ix = mk(tree, 'GeometryNodeInputIndex', "index i", (-6200, -500))
    t_sub = mathx(tree, "n-1", 'SUBTRACT', (-5800, -300), a=0.0)
    L(tree, gin, "Petal Count", t_sub, 0)
    d0(t_sub, 1, 1.0)
    t_max = mathx(tree, "max(n-1,1)", 'MAXIMUM', (-5600, -500), b=1.0)
    L(tree, t_sub, "Value", t_max, 0)
    t_div = mathx(tree, "t = i/(n-1)", 'DIVIDE', (-5400, -400))
    L(tree, ix, "Index", t_div, 0)
    L(tree, t_max, "Value", t_div, 1)

    r_a = rnd(tree, "rand A (angle)", (-6200, -900))
    seed_a = rand_seed(r_a)
    if seed_a is not None:
        L(tree, ix, "Index", r_a, seed_a.name)
    d0(r_a, 0, 0.0)
    d0(r_a, 1, 1.0)
    j_0 = mathx(tree, "randA-0.5", 'SUBTRACT', (-5900, -850), b=0.5)
    L(tree, r_a, "Value", j_0, 0)
    j_1 = mathx(tree, "*chaos", 'MULTIPLY', (-5700, -950))
    L(tree, j_0, "Value", j_1, 0)
    L(tree, gin, "Chaos", j_1, 1)
    j_2 = mathx(tree, "jitter rad", 'MULTIPLY', (-5500, -900), b=0.35)
    L(tree, j_1, "Value", j_2, 0)
    th_0 = mathx(tree, "i*GA", 'MULTIPLY', (-5800, -650))
    L(tree, ix, "Index", th_0, 0)
    L(tree, gin, "Phyllotaxis Angle", th_0, 1)
    th = mathx(tree, "theta", 'ADD', (-5300, -800))
    L(tree, th_0, "Value", th, 0)
    L(tree, j_2, "Value", th, 1)

    sq = mathx(tree, "sqrt(t)", 'SQRT', (-5400, -200))
    L(tree, t_div, "Value", sq, 0)
    rr = mathx(tree, "r = Spread*sqrt(t)", 'MULTIPLY', (-5200, -150))
    L(tree, sq, "Value", rr, 0)
    L(tree, gin, "Spread", rr, 1)
    cos_t = mathx(tree, "cos(theta)", 'COSINE', (-4900, -900))
    L(tree, th, "Value", cos_t, 0)
    sin_t = mathx(tree, "sin(theta)", 'SINE', (-4900, -700))
    L(tree, th, "Value", sin_t, 0)
    px = mathx(tree, "x = r*cos", 'MULTIPLY', (-4600, -950))
    L(tree, cos_t, "Value", px, 0)
    L(tree, rr, "Value", px, 1)
    py = mathx(tree, "y = r*sin", 'MULTIPLY', (-4600, -750))
    L(tree, sin_t, "Value", py, 0)
    L(tree, rr, "Value", py, 1)
    one_mt = mathx(tree, "1-t", 'SUBTRACT', (-5400, 100), a=1.0)
    L(tree, t_div, "Value", one_mt, 1)
    pz = mathx(tree, "z = Rise*(1-t)", 'MULTIPLY', (-4900, 100))
    L(tree, one_mt, "Value", pz, 0)
    L(tree, gin, "Rise", pz, 1)
    v_pos = combine(tree, "petal position", (-4200, -850))
    L(tree, px, "Value", v_pos, "X")
    L(tree, py, "Value", v_pos, "Y")
    L(tree, pz, "Value", v_pos, "Z")

    seed_s = mathx(tree, "seedS = i+1000", 'ADD', (-6200, -1300), b=1000.0)
    L(tree, ix, "Index", seed_s, 0)
    r_s = rnd(tree, "rand S (scale)", (-6000, -1500))
    seed_sock = rand_seed(r_s)
    if seed_sock is not None:
        L(tree, seed_s, "Value", r_s, seed_sock.name)
    d0(r_s, 0, 0.0)
    d0(r_s, 1, 1.0)
    s_0 = mathx(tree, "randS-0.5", 'SUBTRACT', (-5700, -1450), b=0.5)
    L(tree, r_s, "Value", s_0, 0)
    s_1 = mathx(tree, "*chaos", 'MULTIPLY', (-5500, -1550))
    L(tree, s_0, "Value", s_1, 0)
    L(tree, gin, "Chaos", s_1, 1)
    s_2 = mathx(tree, "scale jitter", 'MULTIPLY', (-5300, -1500), b=0.5)
    L(tree, s_1, "Value", s_2, 0)
    s_3 = mathx(tree, "1+jit", 'ADD', (-5100, -1400), b=1.0)
    L(tree, s_2, "Value", s_3, 0)
    mr = mk(tree, 'ShaderNodeMapRange', "falloff map", (-5100, -1150))
    dn(mr, "From Min", 0.0)
    dn(mr, "From Max", 1.0)
    L(tree, t_div, "Value", mr, "Value")
    L(tree, gin, "Inner Size", mr, "To Min")
    dn(mr, "To Max", 1.0)
    s_tot = mathx(tree, "s = falloff*jit", 'MULTIPLY', (-4800, -1250))
    L(tree, mr, "Result", s_tot, 0)
    L(tree, s_3, "Value", s_tot, 1)
    sc_w = mathx(tree, "W*s", 'MULTIPLY', (-4400, -1600))
    L(tree, s_tot, "Value", sc_w, 0)
    L(tree, gin, "Petal Width", sc_w, 1)
    sc_l = mathx(tree, "L*s", 'MULTIPLY', (-4400, -1300))
    L(tree, s_tot, "Value", sc_l, 0)
    L(tree, gin, "Petal Length", sc_l, 1)
    sc_t = mathx(tree, "T*s", 'MULTIPLY', (-4400, -1000))
    L(tree, s_tot, "Value", sc_t, 0)
    L(tree, gin, "Petal Thickness", sc_t, 1)
    v_scale = combine(tree, "petal scale", (-4100, -1300))
    L(tree, sc_w, "Value", v_scale, "X")
    L(tree, sc_l, "Value", v_scale, "Y")
    L(tree, sc_t, "Value", v_scale, "Z")

    cup_t = mathx(tree, "cup*(1-t)", 'MULTIPLY', (-4900, 400))
    L(tree, one_mt, "Value", cup_t, 0)
    L(tree, gin, "Cup", cup_t, 1)
    tf = mathx(tree, "1+cup", 'ADD', (-4700, 450), b=1.0)
    L(tree, cup_t, "Value", tf, 0)
    tilt = mathx(tree, "tilt_i", 'MULTIPLY', (-4500, 400))
    L(tree, tf, "Value", tilt, 0)
    L(tree, gin, "Tilt", tilt, 1)
    az = mathx(tree, "theta+90", 'ADD', (-4900, 600), b=R90)
    L(tree, th, "Value", az, 0)
    tilt_neg = mathx(tree, "tilt (outer tips up)", 'MULTIPLY', (-4300, 350), b=-1.0)
    L(tree, tilt, "Value", tilt_neg, 0)
    bloom_amt = mathx(tree, "1-bloom", 'SUBTRACT', (-4500, 250), a=1.0)
    L(tree, gin, "Bloom", bloom_amt, 1)
    bloom_closed = mathx(tree, "closed tilt delta", 'MULTIPLY', (-4300, 200), b=-1.15)
    L(tree, bloom_amt, "Value", bloom_closed, 0)
    tilt_fin = mathx(tree, "tilt + bloom", 'ADD', (-4100, 300))
    L(tree, tilt_neg, "Value", tilt_fin, 0)
    L(tree, bloom_closed, "Value", tilt_fin, 1)

    v_rot = combine(tree, "petal rotation", (-3900, 400))
    if flutter:
        fl_t = mk(tree, 'GeometryNodeInputSceneTime', "petal flutter time", (-6900, 1200))
        fl_r = mathx(tree, "flutter rate x", 'MULTIPLY', (-6700, 1200))
        L(tree, fl_t, "Frame", fl_r, 0)
        L(tree, gin, "Petal Rate", fl_r, 1)
        fl_ph = mathx(tree, "flutter phase", 'MULTIPLY', (-6500, 1200), b=0.55)
        L(tree, ix, "Index", fl_ph, 0)
        fl_ps = mathx(tree, "flutter phase sum", 'ADD', (-6300, 1200))
        L(tree, fl_r, "Value", fl_ps, 0)
        L(tree, fl_ph, "Value", fl_ps, 1)
        fl_sin = mathx(tree, "flutter sin", 'SINE', (-6100, 1200))
        L(tree, fl_ps, "Value", fl_sin, 0)
        fl_amp = mathx(tree, "flutter amp", 'MULTIPLY', (-5900, 1200))
        L(tree, fl_sin, "Value", fl_amp, 0)
        L(tree, gin, "Petal Amp", fl_amp, 1)
        fl_add = mathx(tree, "rot X + flutter", 'ADD', (-3700, 400))
        L(tree, tilt_fin, "Value", fl_add, 0)
        L(tree, fl_amp, "Value", fl_add, 1)
        L(tree, fl_add, "Value", v_rot, "X")
    else:
        L(tree, tilt_fin, "Value", v_rot, "X")
    d0(v_rot, 1, 0.0)
    L(tree, az, "Value", v_rot, "Z")

    inner_mul = mathx(tree, "n*0.38", 'MULTIPLY', (-6250, -1900), b=0.38)
    L(tree, gin, "Petal Count", inner_mul, 0)
    inner_n = mathx(tree, "inner_n = round(n*0.38)", 'ROUND', (-6100, -1750))
    L(tree, inner_mul, "Value", inner_n, 0)
    outer_n = mathx(tree, "outer_n = n - inner_n", 'SUBTRACT', (-5950, -1750))
    L(tree, gin, "Petal Count", outer_n, 0)
    L(tree, inner_n, "Value", outer_n, 1)

    proto_out, proto_out_sock = petal_surface(tree, "petal S outer", (-3200, -1400), gin, *P_OUT)
    proto_in, proto_in_sock = petal_surface(tree, "petal S inner", (-3200, -2700), gin, *P_IN)

    pts = mk(tree, 'GeometryNodePoints', "phyllotaxis points (outer)", (-3600, -700))
    L(tree, outer_n, "Value", pts, "Count")
    L(tree, v_pos, "Vector", pts, "Position")
    iop = mk(tree, 'GeometryNodeInstanceOnPoints', "instance petals (outer)", (-2900, -700))
    L(tree, pts, "Geometry", iop, "Points")
    L(tree, proto_out, proto_out_sock, iop, "Instance")
    L(tree, v_rot, "Vector", iop, "Rotation")
    L(tree, v_scale, "Vector", iop, "Scale")

    ix_b = mathx(tree, "inner index = i + outer_n", 'ADD', (-6200, -2100))
    L(tree, ix, "Index", ix_b, 0)
    L(tree, outer_n, "Value", ix_b, 1)
    vpos_b, vrot_b, vsc_b = whorl_chain(tree, "inner", gin, ix_b, (-6050, -2900))
    lb = vrot_b.inputs["X"].links[0]
    fin_b = mathx(tree, "inner tilt + bloom", 'ADD', (-3900, 620))
    L(tree, lb.from_socket.node, lb.from_socket.name, fin_b, 0)
    L(tree, bloom_closed, "Value", fin_b, 1)
    L(tree, fin_b, "Value", vrot_b, "X")
    pts_b = mk(tree, 'GeometryNodePoints', "phyllotaxis points (inner)", (-3600, -1900))
    L(tree, inner_n, "Value", pts_b, "Count")
    L(tree, vpos_b, "Vector", pts_b, "Position")
    iop_b = mk(tree, 'GeometryNodeInstanceOnPoints', "instance petals (inner)", (-2900, -1900))
    L(tree, pts_b, "Geometry", iop_b, "Points")
    L(tree, proto_in, proto_in_sock, iop_b, "Instance")
    L(tree, vrot_b, "Vector", iop_b, "Rotation")
    L(tree, vsc_b, "Vector", iop_b, "Scale")

    join_i = mk(tree, 'GeometryNodeJoinGeometry', "join petal whorls", (-2700, -1200))
    L(tree, iop, "Instances", join_i, "Geometry")
    L(tree, iop_b, "Instances", join_i, "Geometry")
    real = mk(tree, 'GeometryNodeRealizeInstances', "realize petals", (-2650, -700))
    L(tree, join_i, "Geometry", real, "Geometry")
    petal_out, petal_sock = smooth_shade(tree, real, "Geometry", (-2500, -700), "smooth petals")
    return petal_out, petal_sock, sc_l, rr, cos_t, sin_t, tilt, pz


def clone_interface(src_tree, dst_tree):
    """Clone all INPUT sockets from src_tree's interface to dst_tree (for parallel trees)."""
    for item in src_tree.interface.items_tree:
        if getattr(item, "in_out", "") != "INPUT":
            continue
        try:
            s = dst_tree.interface.new_socket(name=item.name, in_out='INPUT',
                                              socket_type=item.socket_type)
            s.default_value = item.default_value
            for attr in ("min_value", "max_value", "subtype"):
                if hasattr(item, attr):
                    try:
                        setattr(s, attr, getattr(item, attr))
                    except Exception:
                        pass
        except Exception as exc:
            print("  warn: clone socket %s (%r)" % (item.name, exc))


def build(genome_id, tree_name, bg, real_scale=1.0, cast_default=True, bloom=False):
    """Build one v7 tree from one genome. real_scale = final uniform scale (pass 2)."""
    S = float(real_scale) if real_scale else 1.0

    def mm(v):
        # real millimetres -> tree units BEFORE the final Real Scale is applied.
        # scene convention: 1 unit = 10 cm (scale_length 0.1), so 1 u = 100 mm.
        return (v / 100.0) / max(S, 1e-9)

    r = bg.resolve_genome(genome_id)
    t = r["traits"]
    crown, acc, pave, cbead, hw = t["crown"], t["accents"], t["pave"], t["center_bead"], t["hardware"]
    phy, mats = t["phyllotaxis"], t["materials"]
    prof0 = str(crown.get("petal_profile", "round")).lower()
    gspec = t.get("gems") or {}
    dspec = t.get("dangles") or {}
    # thin pointed blades erode under fine voxels + smoothing -> lighter cast settings
    vox_default = 0.35 if prof0 == "pointed" else 0.25
    mean_default = 0 if prof0 == "pointed" else 2
    size_blk = t.get("size") or {}
    target_mm = float(size_blk.get("real_mm", 0.0) or 0.0)

    ob = bpy.data.objects.get(OBJ_NAME)
    if ob is None:
        raise RuntimeError("object %r not found" % OBJ_NAME)

    mat_petal = bpy.data.materials.get(mats["petal"])
    mat_bead = bpy.data.materials.get(mats["bead"])
    mat_pin = bpy.data.materials.get(mats["pin"])
    if mat_petal is None and len(ob.material_slots):
        mat_petal = ob.material_slots[0].material
    # material-ID architecture: petals / dome / body / setting / chain / pearls / pave
    mat_metal_petal = resolve_material(mats, "metal_petal", "petal", mat_petal)
    mat_metal_dome = resolve_material(mats, "metal_dome", "petal", mat_petal)
    mat_metal_body = resolve_material(mats, "metal_body", "petal", mat_petal)
    mat_metal_setting = resolve_material(mats, "metal_setting", "petal", mat_petal)
    mat_bead_pearl = resolve_material(mats, "bead_pearl", "bead", mat_bead)
    mat_bead_pave = resolve_material(mats, "bead_pave", "bead", mat_bead)

    old = bpy.data.node_groups.get(tree_name)
    if old is not None:
        try:
            bpy.data.node_groups.remove(old)
            print("removed previous", tree_name)
        except Exception as exc:
            print("warn: could not remove old tree (%r)" % (exc,))

    tree = bpy.data.node_groups.new(tree_name, 'GeometryNodeTree')

    def iface(name, stype, default, mn=None, mx=None, subtype=None):
        s = tree.interface.new_socket(name=name, in_out='INPUT', socket_type=stype)
        s.default_value = default
        if mn is not None:
            try:
                s.min_value = mn
            except Exception:
                pass
        if mx is not None:
            try:
                s.max_value = mx
            except Exception:
                pass
        if subtype:
            try:
                s.subtype = subtype
            except Exception as exc:
                print("  warn: subtype %s (%r)" % (subtype, exc))
        return s

    iface("Petal Count", 'NodeSocketInt', int(crown["petal_count"]), 3, 64)
    iface("Phyllotaxis Angle", 'NodeSocketFloat', math.radians(phy["angle_deg"]), subtype='ANGLE')
    iface("Spread", 'NodeSocketFloat', float(phy["spread"]))
    iface("Petal Length", 'NodeSocketFloat', float(crown["petal_len"]))
    iface("Petal Width", 'NodeSocketFloat', float(crown["petal_wid"]))
    iface("Petal Thickness", 'NodeSocketFloat', float(crown["petal_thk"]))
    # A1 margin system: super-ellipse exponent driving the petal outline
    iface("Margin Exp", 'NodeSocketFloat', 1.0, 0.2, 4.0)
    iface("Inner Size", 'NodeSocketFloat', float(crown["inner_size"]))
    iface("Tilt", 'NodeSocketFloat', math.radians(crown["tilt_deg"]), subtype='ANGLE')
    iface("Cup", 'NodeSocketFloat', float(crown["cup"]))
    iface("Rise", 'NodeSocketFloat', float(crown["rise"]))
    iface("Chaos", 'NodeSocketFloat', float(crown["chaos"]))
    iface("Bead Radius", 'NodeSocketFloat', float(cbead["radius"]))
    iface("Accent Size", 'NodeSocketFloat', float(acc["size"]))
    iface("Accent Lift", 'NodeSocketFloat', float(acc["lift"]))
    iface("Pave Count", 'NodeSocketInt', int(pave["site_count"]), 0, 512)
    iface("Border Inner", 'NodeSocketFloat', float(pave["border_inner"]))
    iface("Border Outer", 'NodeSocketFloat', float(pave["border_outer"]))
    iface("Pave Bead Radius", 'NodeSocketFloat', float(pave["bead_radius"]))
    # 2026-09-17: the border row is a JEWELRY row -- machine-regular by default. Jitter is opt-in
    # per genome ("jitter" in the genome's pave block); 0.0 keeps the row exactly on its law.
    iface("Pave Jitter", 'NodeSocketFloat', float(pave.get("jitter", 0.0)), 0.0, 1.0)
    # 2026-09-17: EVEN row law (default ON): uniform angular step + staggered two-row radius.
    # Off = the legacy golden-angle phyllotaxis spiral (kept for comparison/designs).
    iface("Pave Even", 'NodeSocketBool', True)
    iface("Petal Inset", 'NodeSocketFloat', 1.0, 0.0, 1.0)
    # 2026-09-17 (v11 animation): Bloom = 1 authored open crown, 0 closed bud. Pure parameter --
    # NO SceneTime here (the body must stay time-free; live flutter belongs to the petal object).
    iface("Bloom", 'NodeSocketFloat', 1.0, 0.0, 1.0)
    # v11 polish: product/website shots hide the pin stem+tip (reads as a dead bar at 3/4 angles)
    iface("Show Pin", 'NodeSocketBool', True)
    iface("Bead Settings", 'NodeSocketBool', True)
    iface("Real Scale", 'NodeSocketFloat', float(S), 0.05, 5.0)
    iface("Cast Finish", 'NodeSocketBool', bool(cast_default))
    iface("Cast Voxel (mm)", 'NodeSocketFloat', vox_default, 0.05, 2.0)
    iface("Cast Fillet Iters", 'NodeSocketInt', 1, 0, 4)
    iface("Auto UV", 'NodeSocketBool', False)
    iface("Gems On", 'NodeSocketBool', True)
    iface("Ring Count", 'NodeSocketInt', int(gspec.get("ring_count", 0) or 0), 0, 64)
    iface("Ring Gem Size", 'NodeSocketFloat', float(gspec.get("ring_size", 0.0) or 0.0), 0.0, 0.3)
    iface("Gem Size", 'NodeSocketFloat', float(gspec.get("center_size", 0.0) or 0.0), 0.0, 0.4)
    # v11 milgrain + filigree (lace-like jewelry detail)
    iface("Milgrain On", 'NodeSocketBool', True)
    iface("Milgrain Size", 'NodeSocketFloat', 0.012, 0.003, 0.05)
    iface("Filigree On", 'NodeSocketBool', True)
    iface("Filigree Depth", 'NodeSocketFloat', 1, 0, 3)
    iface("Filigree Width", 'NodeSocketFloat', 0.008, 0.003, 0.03)
    tree.interface.new_socket(name="Geometry", in_out='OUTPUT', socket_type='NodeSocketGeometry')
    print("[%s] interface sockets: %d | target %s mm | S=%.5f" % (
        tree_name, len(tree.interface.items_tree), target_mm or "-", S))

    gin = mk(tree, 'NodeGroupInput', "Group Input", (-6200, 200))
    gout = mk(tree, 'NodeGroupOutput', "Group Output", (3400, 0))

    # ---------------- petals (extracted to petal_system) ---------------------
    petal_out, petal_sock, sc_l, rr, cos_t, sin_t, tilt, pz = petal_system(tree, gin, crown, phy, mat_metal_petal, flutter=False)

    # ---------------- pave field (v5 law) + v6 seats + v7 surface sampling ----
    # the pave section needs its own index counter (petal_system has its own internal ix)
    ix_pave = mk(tree, 'GeometryNodeInputIndex', "index i (pave)", (-6200, -2300))
    gold_surf = mk(tree, 'GeometryNodeJoinGeometry', "gold surface (for seating)", (-3450, -3080))
    pc_sub = mathx(tree, "pave n-1", 'SUBTRACT', (-5800, -2400), a=0.0)
    L(tree, gin, "Pave Count", pc_sub, 0)
    d0(pc_sub, 1, 1.0)
    pc_max = mathx(tree, "pave max(n-1,1)", 'MAXIMUM', (-5600, -2600), b=1.0)
    L(tree, pc_sub, "Value", pc_max, 0)
    pc_t = mathx(tree, "pt = i/(n-1)", 'DIVIDE', (-5400, -2500))
    L(tree, ix_pave, "Index", pc_t, 0)
    L(tree, pc_max, "Value", pc_t, 1)
    in2 = mathx(tree, "inner^2", 'MULTIPLY', (-5600, -3000))
    L(tree, gin, "Border Inner", in2, 0)
    L(tree, gin, "Border Inner", in2, 1)
    out2 = mathx(tree, "outer^2", 'MULTIPLY', (-5400, -3200))
    L(tree, gin, "Border Outer", out2, 0)
    L(tree, gin, "Border Outer", out2, 1)
    span2 = mathx(tree, "outer^2-inner^2", 'SUBTRACT', (-5200, -3100))
    L(tree, out2, "Value", span2, 0)
    L(tree, in2, "Value", span2, 1)
    fill2 = mathx(tree, "pt*span2", 'MULTIPLY', (-5000, -3000))
    L(tree, pc_t, "Value", fill2, 0)
    L(tree, span2, "Value", fill2, 1)
    r2sum = mathx(tree, "inner^2+fill", 'ADD', (-4800, -3000))
    L(tree, in2, "Value", r2sum, 0)
    L(tree, fill2, "Value", r2sum, 1)
    rp = mathx(tree, "rp = sqrt(...)", 'SQRT', (-4600, -3000))
    L(tree, r2sum, "Value", rp, 0)
    # 2026-09-17: EVEN row law (default). The phyllotaxis packing read uneven in stills
    # (angular-gap CV 0.311; crowded + merged pairs). A jewelry border row is machine-regular:
    # theta = i*(2pi/n) with the radius STAGGERED inner/outer by parity -> a two-row pave
    # (neighbor distance ~3.26 mm vs 2.58 mm bead diameter: uniform gaps, no merges).
    p_step = mathx(tree, "pave step = 2pi/n", 'DIVIDE', (-5400, -2750), a=2.0 * math.pi)
    L(tree, gin, "Pave Count", p_step, 1)
    p_the = mathx(tree, "i*step (pave)", 'MULTIPLY', (-5200, -2870))
    L(tree, ix_pave, "Index", p_the, 0)
    L(tree, p_step, "Value", p_the, 1)
    p_par = mathx(tree, "i mod 2 (stagger)", 'MODULO', (-5200, -2650))
    L(tree, ix_pave, "Index", p_par, 0)
    d0(p_par, 1, 2.0)
    p_ref = mathx(tree, "par*span2", 'MULTIPLY', (-5000, -2650))
    L(tree, p_par, "Value", p_ref, 0)
    L(tree, span2, "Value", p_ref, 1)
    p_res = mathx(tree, "inner^2+par*span2", 'ADD', (-4800, -2650))
    L(tree, in2, "Value", p_res, 0)
    L(tree, p_ref, "Value", p_res, 1)
    p_re = mathx(tree, "r_even = sqrt(...)", 'SQRT', (-4600, -2650))
    L(tree, p_res, "Value", p_re, 0)
    p_rnd = rnd(tree, "rand P (pave angle)", (-6000, -3400))
    p_seed = rand_seed(p_rnd)
    if p_seed is not None:
        seed_p = mathx(tree, "seedP = i+2000", 'ADD', (-6200, -3300), b=2000.0)
        L(tree, ix_pave, "Index", seed_p, 0)
        L(tree, seed_p, "Value", p_rnd, p_seed.name)
    d0(p_rnd, 0, 0.0)
    d0(p_rnd, 1, 1.0)
    p_j0 = mathx(tree, "randP-0.5", 'SUBTRACT', (-5800, -3400), b=0.5)
    L(tree, p_rnd, "Value", p_j0, 0)
    p_j1 = mathx(tree, "*chaos (pave)", 'MULTIPLY', (-5600, -3500))
    L(tree, p_j0, "Value", p_j1, 0)
    L(tree, gin, "Chaos", p_j1, 1)
    p_j2 = mathx(tree, "pave jitter rad", 'MULTIPLY', (-5400, -3450))
    L(tree, p_j1, "Value", p_j2, 0)
    L(tree, gin, "Pave Jitter", p_j2, 1)
    p_th0 = mathx(tree, "i*GA (pave)", 'MULTIPLY', (-5600, -3650))
    L(tree, ix_pave, "Index", p_th0, 0)
    L(tree, gin, "Phyllotaxis Angle", p_th0, 1)
    p_th_sw = mk(tree, 'GeometryNodeSwitch', "pave even switch (theta)", (-5150, -3820))
    L(tree, p_th0, "Value", p_th_sw, "False")
    L(tree, p_the, "Value", p_th_sw, "True")
    L(tree, gin, "Pave Even", p_th_sw, "Switch")
    p_th = mathx(tree, "theta_p", 'ADD', (-5100, -3550))
    tree.links.new(p_th_sw.outputs[0], p_th.inputs[0])  # float switch output name varies by build
    L(tree, p_j2, "Value", p_th, 1)
    p_cos = mathx(tree, "cos(theta_p)", 'COSINE', (-4900, -3800))
    L(tree, p_th, "Value", p_cos, 0)
    p_sin = mathx(tree, "sin(theta_p)", 'SINE', (-4900, -3600))
    L(tree, p_th, "Value", p_sin, 0)
    p_r_sw = mk(tree, 'GeometryNodeSwitch', "pave even switch (radius)", (-4450, -2870))
    L(tree, rp, "Value", p_r_sw, "False")
    L(tree, p_re, "Value", p_r_sw, "True")
    L(tree, gin, "Pave Even", p_r_sw, "Switch")
    p_x = mathx(tree, "xp", 'MULTIPLY', (-4400, -3850))
    L(tree, p_cos, "Value", p_x, 0)
    tree.links.new(p_r_sw.outputs[0], p_x.inputs[1])
    p_y = mathx(tree, "yp", 'MULTIPLY', (-4400, -3650))
    L(tree, p_sin, "Value", p_y, 0)
    tree.links.new(p_r_sw.outputs[0], p_y.inputs[1])
    dh = mathx(tree, "dome h = Rise*1.1", 'MULTIPLY', (-4600, -2900), b=1.1)
    L(tree, gin, "Rise", dh, 0)
    dzc = mathx(tree, "dome zc = Rise-h", 'SUBTRACT', (-4400, -2980))
    L(tree, gin, "Rise", dzc, 0)
    L(tree, dh, "Value", dzc, 1)
    # v7/v10 FIX 2026-09-17: beads + seats seat on the real plate/step surface via a DOWNWARD
    # RAYCAST. (The old SampleNearestSurface + Position-field route returned positions from the
    # wrong geometry context -- the ring rode a tilted phantom surface; measured z spread +-10 mm
    # across the row while the target cylinders are level.)
    p_hi = mathx(tree, "sample z (plate top + 6mm)", 'ADD', (-4000, -3350),
                 a=float(hw["plate_z"]) + float(hw["plate_depth"]) * 0.5, b=mm(6.0))
    p_sample_pos = combine(tree, "pave sample position", (-3600, -3450))
    L(tree, p_x, "Value", p_sample_pos, "X")
    L(tree, p_y, "Value", p_sample_pos, "Y")
    L(tree, p_hi, "Value", p_sample_pos, "Z")
    p_surf = mk(tree, 'GeometryNodeRaycast', "pave surface raycast", (-3400, -3350))
    L(tree, gold_surf, "Geometry", p_surf, "Target Geometry")
    L(tree, p_sample_pos, "Vector", p_surf, "Source Position")
    dn(p_surf, "Ray Direction", (0.0, 0.0, -1.0))
    dn(p_surf, "Ray Length", 0.2)
    p_hitz = mk(tree, 'ShaderNodeSeparateXYZ', "pave hit z", (-3300, -3520))
    L(tree, p_surf, "Hit Position", p_hitz, "Vector")
    p_bead_lift = mathx(tree, "bead lift = 0.38 r", 'MULTIPLY', (-3550, -3750), b=0.38)
    L(tree, gin, "Pave Bead Radius", p_bead_lift, 0)
    p_z = mathx(tree, "zp = surface + 0.38r", 'ADD', (-3200, -3300))
    L(tree, p_hitz, "Z", p_z, 0)
    L(tree, p_bead_lift, "Value", p_z, 1)
    p_pos = combine(tree, "pave position", (-3400, -3600))
    L(tree, p_x, "Value", p_pos, "X")
    L(tree, p_y, "Value", p_pos, "Y")
    L(tree, p_z, "Value", p_pos, "Z")
    p_pts = mk(tree, 'GeometryNodePoints', "pave points", (-3100, -3500))
    L(tree, gin, "Pave Count", p_pts, "Count")
    L(tree, p_pos, "Vector", p_pts, "Position")
    p_proto = mk(tree, 'GeometryNodeMeshUVSphere', "pave bead proto", (-3100, -4000))
    dn(p_proto, "Segments", 16)
    dn(p_proto, "Rings", 12)
    L(tree, gin, "Pave Bead Radius", p_proto, "Radius")
    p_iop = mk(tree, 'GeometryNodeInstanceOnPoints', "instance pave beads", (-2800, -3500))
    L(tree, p_pts, "Geometry", p_iop, "Points")
    L(tree, p_proto, "Mesh", p_iop, "Instance")
    p_real = mk(tree, 'GeometryNodeRealizeInstances', "realize pave beads", (-2500, -3500))
    L(tree, p_iop, "Instances", p_real, "Geometry")
    pave_out, pave_sock = smooth_shade(tree, p_real, "Geometry", (-2200, -3500), "smooth pave beads")

    # v6 seats: gold cup under every pavé bead (gated by "Bead Settings")
    seat_r = mathx(tree, "seat r = 1.35*bead", 'MULTIPLY', (-3100, -4400))
    L(tree, gin, "Pave Bead Radius", seat_r, 0)
    d0(seat_r, 1, 1.35)
    seat_proto = mk(tree, 'GeometryNodeMeshUVSphere', "seat proto", (-2950, -4500))
    dn(seat_proto, "Segments", 16)
    dn(seat_proto, "Rings", 10)
    L(tree, seat_r, "Value", seat_proto, "Radius")
    seat_sq = mk(tree, 'ShaderNodeCombineXYZ', "seat squash vec", (-2800, -4600))
    d0(seat_sq, 0, 1.0)
    d0(seat_sq, 1, 1.0)
    d0(seat_sq, 2, 0.5)
    seat_iop = mk(tree, 'GeometryNodeInstanceOnPoints', "instance seats", (-2950, -4100))
    L(tree, p_pts, "Geometry", seat_iop, "Points")
    L(tree, seat_proto, "Mesh", seat_iop, "Instance")
    L(tree, seat_sq, "Vector", seat_iop, "Scale")
    seat_real = mk(tree, 'GeometryNodeRealizeInstances', "realize seats", (-2700, -4100))
    L(tree, seat_iop, "Instances", seat_real, "Geometry")
    seat_off = mathx(tree, "seat offset = -0.45*bead", 'MULTIPLY', (-2950, -4300), b=-0.45)
    L(tree, gin, "Pave Bead Radius", seat_off, 0)
    seat_off_v = combine(tree, "seat offset vec", (-2800, -4250))
    d0(seat_off_v, 0, 0.0)
    d0(seat_off_v, 1, 0.0)
    L(tree, seat_off, "Value", seat_off_v, "Z")
    seat_tr = mk(tree, 'GeometryNodeTransform', "seat drop", (-2550, -4100))
    L(tree, seat_real, "Geometry", seat_tr, "Geometry")
    L(tree, seat_off_v, "Vector", seat_tr, "Translation")
    seat_smooth, seat_sock = smooth_shade(tree, seat_tr, "Geometry", (-2400, -4100), "smooth seats")
    seat_empty = empty_geo(tree, "no seats", (-2400, -4500))
    seat_sw, seat_sw_sock = geo_switch(tree, "seat switch", (-2250, -4200), gin, "Bead Settings",
                                       (seat_empty, "Geometry"), (seat_smooth, seat_sock))
    seats_out, seats_sock = seat_sw, seat_sw_sock

    # ---------------- dome (v5) + v6 collar ring ------------------------------
    dome = mk(tree, 'GeometryNodeMeshUVSphere', "dome proto", (-4900, -2300))
    dn(dome, "Segments", 48)
    dn(dome, "Rings", 24)
    L(tree, gin, "Spread", dome, "Radius")
    dome_sc = mk(tree, 'GeometryNodeTransform', "dome squash", (-4600, -2300))
    L(tree, dome, "Mesh", dome_sc, "Geometry")
    dome_sz = mathx(tree, "dome sz = h/Spread", 'DIVIDE', (-4850, -2600))
    L(tree, dh, "Value", dome_sz, 0)
    L(tree, gin, "Spread", dome_sz, 1)
    v_dsz = combine(tree, "dome scale vec", (-4650, -2650))
    d0(v_dsz, 0, 1.0)
    d0(v_dsz, 1, 1.0)
    L(tree, dome_sz, "Value", v_dsz, "Z")
    L(tree, v_dsz, "Vector", dome_sc, "Scale")
    v_dzc = combine(tree, "dome pos", (-4650, -2450))
    d0(v_dzc, 0, 0.0)
    d0(v_dzc, 1, 0.0)
    L(tree, dzc, "Value", v_dzc, "Z")
    L(tree, v_dzc, "Vector", dome_sc, "Translation")
    dome_out, dome_sock = smooth_shade(tree, dome_sc, "Geometry", (-4300, -2300), "smooth dome")

    # collar: ring where the dome meets the plate step (fillet-like transition)
    z_col = float(hw["plate_z"]) + float(hw["plate_depth"]) * 0.5 + mm(0.7)
    dz_col = mathx(tree, "dz = zc - z_collar", 'SUBTRACT', (-4300, -2700), b=z_col)
    L(tree, dzc, "Value", dz_col, 0)
    frac = mathx(tree, "frac = dz/h", 'DIVIDE', (-4150, -2650))
    L(tree, dz_col, "Value", frac, 0)
    L(tree, dh, "Value", frac, 1)
    fr2 = mathx(tree, "frac^2", 'MULTIPLY', (-4000, -2700))
    L(tree, frac, "Value", fr2, 0)
    L(tree, frac, "Value", fr2, 1)
    om = mathx(tree, "1-frac^2", 'SUBTRACT', (-3850, -2650), a=1.0)
    L(tree, fr2, "Value", om, 1)
    omc = mathx(tree, "clamp>=0", 'MAXIMUM', (-3700, -2650), b=0.0)
    L(tree, om, "Value", omc, 0)
    kk = mathx(tree, "k = sqrt(...)", 'SQRT', (-3550, -2650))
    L(tree, omc, "Value", kk, 0)
    rc = mathx(tree, "r_collar = Spread*k", 'MULTIPLY', (-3400, -2650))
    L(tree, kk, "Value", rc, 0)
    L(tree, gin, "Spread", rc, 1)
    collar_t = torus(tree, "collar torus", (-3400, -2300), 0.01, mm(0.85), 48, 8)
    collar_tr = tree.nodes["collar torus xf"]
    wire_radius(tree, "collar torus path", rc, "  ")
    coll_pos = combine(tree, "collar pos", (-3250, -2400))
    d0(coll_pos, 0, 0.0)
    d0(coll_pos, 1, 0.0)
    d0(coll_pos, 2, z_col)
    L(tree, coll_pos, "Vector", collar_tr, "Translation")
    collar_out, collar_sock = smooth_shade(tree, collar_tr, "Geometry", (-3200, -2300), "smooth collar")

    # ---------------- accents (v5, surface-snap kept) --------------------------
    reach = mathx(tree, "reach = L*s*0.55", 'MULTIPLY', (-4400, -1900), b=0.55)
    L(tree, sc_l, "Value", reach, 0)
    r2 = mathx(tree, "r+reach", 'ADD', (-4200, -2150))
    L(tree, rr, "Value", r2, 0)
    L(tree, reach, "Value", r2, 1)
    ax = mathx(tree, "ax", 'MULTIPLY', (-3950, -2350))
    L(tree, cos_t, "Value", ax, 0)
    L(tree, r2, "Value", ax, 1)
    ay = mathx(tree, "ay", 'MULTIPLY', (-3950, -2150))
    L(tree, sin_t, "Value", ay, 0)
    L(tree, r2, "Value", ay, 1)
    sin_t2 = mathx(tree, "sin(tilt)", 'SINE', (-4550, -1750))
    L(tree, tilt, "Value", sin_t2, 0)
    tip_lift = mathx(tree, "tip lift", 'MULTIPLY', (-4300, -1800))
    L(tree, sin_t2, "Value", tip_lift, 0)
    L(tree, reach, "Value", tip_lift, 1)
    z_tip = mathx(tree, "z_tip", 'ADD', (-4050, -1850))
    L(tree, pz, "Value", z_tip, 0)
    L(tree, tip_lift, "Value", z_tip, 1)
    az2 = mathx(tree, "z_tip + Accent Lift", 'ADD', (-3900, -1950))
    L(tree, z_tip, "Value", az2, 0)
    L(tree, gin, "Accent Lift", az2, 1)
    v_pos2 = combine(tree, "accent position", (-3700, -2250))
    L(tree, ax, "Value", v_pos2, "X")
    L(tree, ay, "Value", v_pos2, "Y")
    L(tree, az2, "Value", v_pos2, "Z")
    pts2 = mk(tree, 'GeometryNodePoints', "accent points", (-3450, -2100))
    L(tree, gin, "Petal Count", pts2, "Count")
    L(tree, v_pos2, "Vector", pts2, "Position")
    try:
        prox = mk(tree, 'GeometryNodeProximity', "accent snap point", (-3600, -1600))
        L(tree, petal_out, petal_sock, prox, "Target")
        L(tree, v_pos2, "Vector", prox, "Sample Position")
        nrm = mk(tree, 'GeometryNodeInputNormal', "petal normal field", (-4000, -1400))
        sns = mk(tree, 'GeometryNodeSampleNearestSurface', "accent snap normal", (-3420, -1500))
        L(tree, petal_out, petal_sock, sns, "Mesh")
        L(tree, nrm, "Normal", sns, "Value")
        L(tree, v_pos2, "Vector", sns, "Sample Position")
        vs = mk(tree, 'ShaderNodeVectorMath', "accent lift vector", (-3240, -1500))
        vs.operation = 'SCALE'
        L(tree, sns, "Value", vs, "Vector")
        L(tree, gin, "Accent Lift", vs, "Scale")
        va = mk(tree, 'ShaderNodeVectorMath', "accent seated position", (-3080, -1600))
        va.operation = 'ADD'
        L(tree, prox, "Position", va, "Vector")
        L(tree, vs, "Vector", va, 1)
        L(tree, va, "Vector", pts2, "Position")
        print("  [accent] surface snap wired (proximity + nearest-surface normal)")
    except Exception as exc:
        print("  [accent] snap skipped: %r" % exc)
    proto2 = mk(tree, 'GeometryNodeMeshUVSphere', "accent proto", (-3450, -2600))
    dn(proto2, "Segments", 16)
    dn(proto2, "Rings", 12)
    L(tree, gin, "Accent Size", proto2, "Radius")
    iop2 = mk(tree, 'GeometryNodeInstanceOnPoints', "instance accents", (-3100, -2100))
    L(tree, pts2, "Geometry", iop2, "Points")
    L(tree, proto2, "Mesh", iop2, "Instance")
    real2 = mk(tree, 'GeometryNodeRealizeInstances', "realize accents", (-2800, -2100))
    L(tree, iop2, "Instances", real2, "Geometry")
    acc_out, acc_sock = smooth_shade(tree, real2, "Geometry", (-2500, -2100), "smooth accents")

    # ---------------- center bead (v5) + v6 bezel ------------------------------
    bead = mk(tree, 'GeometryNodeMeshUVSphere', "bead proto", (-2200, -2600))
    dn(bead, "Segments", 24)
    dn(bead, "Rings", 12)
    L(tree, gin, "Bead Radius", bead, "Radius")
    bz = mathx(tree, "bead z", 'ADD', (-3200, -2900), b=0.005)
    L(tree, gin, "Rise", bz, 0)
    v_bpos = combine(tree, "bead position", (-2950, -2900))
    d0(v_bpos, 0, 0.0)
    d0(v_bpos, 1, 0.0)
    L(tree, bz, "Value", v_bpos, "Z")
    bead_tr = mk(tree, 'GeometryNodeTransform', "bead transform", (-1800, -2600))
    L(tree, bead, "Mesh", bead_tr, "Geometry")
    L(tree, v_bpos, "Vector", bead_tr, "Translation")
    dn(bead_tr, "Scale", (1.0, 1.0, float(cbead["z_squash"])))
    bead_out, bead_sock = smooth_shade(tree, bead_tr, "Geometry", (-1650, -2600), "smooth bead")
    bez_m = mathx(tree, "bezel major", 'MULTIPLY', (-2600, -2950), b=0.85)
    L(tree, gin, "Bead Radius", bez_m, 0)
    bez_n = mathx(tree, "bezel minor", 'MULTIPLY', (-2600, -3100), b=0.30)
    L(tree, gin, "Bead Radius", bez_n, 0)
    bez_off = mathx(tree, "bezel z = bead - 0.15r", 'MULTIPLY', (-2600, -3250), b=-0.15)
    L(tree, gin, "Bead Radius", bez_off, 0)
    bez_z = mathx(tree, "bezel z", 'ADD', (-2450, -3250))
    L(tree, bz, "Value", bez_z, 0)
    L(tree, bez_off, "Value", bez_z, 1)
    bez_t = torus(tree, "bezel torus", (-2400, -2700), 0.05, 0.02, 32, 8)
    bez_tr = tree.nodes["bezel torus xf"]
    wire_radius(tree, "bezel torus path", bez_m, "  ")
    wire_radius(tree, "bezel torus prof", bez_n, "  ")
    bpv = combine(tree, "bezel pos", (-2300, -2900))
    d0(bpv, 0, 0.0)
    d0(bpv, 1, 0.0)
    L(tree, bez_z, "Value", bpv, "Z")
    L(tree, bpv, "Vector", bez_tr, "Translation")
    bezel_out, bezel_sock = smooth_shade(tree, bez_tr, "Geometry", (-2150, -2700), "smooth bezel")

    # ---------------- plate: base + v6 step ------------------------------------
    cyl = mk(tree, 'GeometryNodeMeshCylinder', "pin plate", (-2200, 900))
    dn(cyl, "Radius", float(hw["plate_radius"]))
    dn(cyl, "Depth", float(hw["plate_depth"]))
    dn(cyl, "Vertices", 48)
    cyl_tr = mk(tree, 'GeometryNodeTransform', "pin transform", (-1800, 900))
    L(tree, cyl, "Mesh", cyl_tr, "Geometry")
    dn(cyl_tr, "Translation", (0.0, 0.0, float(hw["plate_z"])))
    plate_out, plate_sock = smooth_shade(tree, cyl_tr, "Geometry", (-1650, 900), "smooth plate")
    step_r = mathx(tree, "step r = 0.88*plate", 'MULTIPLY', (-2200, 700), b=0.88)
    d0(step_r, 0, float(hw["plate_radius"]))
    step = mk(tree, 'GeometryNodeMeshCylinder', "plate step", (-2000, 700))
    L(tree, step_r, "Value", step, "Radius")
    dn(step, "Depth", mm(0.7))
    dn(step, "Vertices", 64)
    step_z = float(hw["plate_z"]) + float(hw["plate_depth"]) * 0.5 + mm(0.7) * 0.5
    step_tr = mk(tree, 'GeometryNodeTransform', "step transform", (-1800, 700))
    L(tree, step, "Mesh", step_tr, "Geometry")
    dn(step_tr, "Translation", (0.0, 0.0, step_z))
    step_out, step_sock = smooth_shade(tree, step_tr, "Geometry", (-1650, 700), "smooth step")

    # ---------------- v11 base-plate redesign (silhouette audit 2026-09-17) ---------
    # Audit verdict: the plate was the weakest silhouette element ("smooth featureless arc").
    # Moves: scallop notches on the plate SKIRT (lower 70% of the depth only -- the top face stays
    # intact so the pave seating raycast cannot miss), one fine engraved ring on the plate's outer
    # annulus (outside the step, inside the rim), and a collar rail on the step top (the visible
    # band between the dome and the pave row). Radii respect the occupied zones: dome <= ~22 mm,
    # pave band 25.5-29.5 mm (local), step edge at 0.88*plate.
    # v11.1 (2026-09-17 late): the exact-boolean notches/grooves emitted 425 sentinel verts at
    # x ~ -7.7e31 (984 degenerate sliver faces -- the "thin line" artifact across renders;
    # proven by bypass test: without both booleans the sentinel count is 0). Replaced with
    # ADDITIVE details: a rim bead ring (scalloped edge read) + raised rails. No plate booleans.
    rim_sphere = mk(tree, 'GeometryNodeMeshUVSphere', "rim bead proto", (-2500, 320))
    dn(rim_sphere, "Segments", 10)
    dn(rim_sphere, "Rings", 8)
    dn(rim_sphere, "Radius", mm(0.55))
    rim_circ = mk(tree, 'GeometryNodeMeshCircle', "rim bead ring", (-2500, 180))
    dn(rim_circ, "Radius", float(hw["plate_radius"]) * 0.998)
    dn(rim_circ, "Vertices", 48)
    rim_pts = mk(tree, 'GeometryNodeMeshToPoints', "rim bead points", (-2300, 180))
    L(tree, rim_circ, "Mesh", rim_pts, "Mesh")
    rim_inst = mk(tree, 'GeometryNodeInstanceOnPoints', "rim bead instances", (-2100, 320))
    L(tree, rim_pts, "Points", rim_inst, "Points")
    L(tree, rim_sphere, "Mesh", rim_inst, "Instance")
    rim_real = mk(tree, 'GeometryNodeRealizeInstances', "rim bead realize", (-1900, 320))
    L(tree, rim_inst, "Instances", rim_real, "Geometry")
    rim_tr = mk(tree, 'GeometryNodeTransform', "rim bead z", (-1700, 320))
    L(tree, rim_real, "Geometry", rim_tr, "Geometry")
    dn(rim_tr, "Translation", (0.0, 0.0, float(hw["plate_z"])))
    rim_out, rim_sock = smooth_shade(tree, rim_tr, "Geometry", (-1500, 320), "smooth rim beads")

    grv = torus(tree, "plate rail a", (-2300, 20), float(hw["plate_radius"]) * 0.94, mm(0.25), 64, 6)
    dn(grv, "Translation", (0.0, 0.0, float(hw["plate_z"]) + float(hw["plate_depth"]) * 0.5))
    grv2 = torus(tree, "plate rail b", (-2300, -60), float(hw["plate_radius"]) * 0.86,
                 mm(0.22), 64, 6)
    dn(grv2, "Translation", (0.0, 0.0, float(hw["plate_z"]) + float(hw["plate_depth"]) * 0.5))
    grvj = mk(tree, 'GeometryNodeJoinGeometry', "plate rails join", (-2100, -40))
    L(tree, grv, "Geometry", grvj, "Geometry")
    L(tree, grv2, "Geometry", grvj, "Geometry")
    grvj_out, grvj_sock = smooth_shade(tree, grvj, "Geometry", (-1900, -40), "smooth plate rails")

    rail = torus(tree, "plate rail", (-2300, -140), float(hw["plate_radius"]) * 0.755, mm(0.32), 64, 8)
    dn(rail, "Translation", (0.0, 0.0, step_z + mm(0.7) * 0.5))
    rail_out, rail_sock = smooth_shade(tree, rail, "Geometry", (-2100, -140), "smooth plate rail")

    # milgrain row (v11 polish, "better detailing"): 48 micro-beads on the step top hugging the
    # rail -- classic jewelry grain; spheres need no per-point rotation.
    mg_sphere = mk(tree, 'GeometryNodeMeshUVSphere', "milgrain proto", (-2500, -300))
    dn(mg_sphere, "Segments", 8)
    dn(mg_sphere, "Rings", 6)
    mg_size = mk(tree, 'ShaderNodeMath', "milgrain size", (-2600, -350))
    mg_size.operation = 'MULTIPLY'
    L(tree, gin, "Milgrain Size", mg_size, 0)
    d0(mg_size, 1, 100.0)  # socket is in mm, convert to units (1u = 100mm)
    L(tree, mg_size, "Value", mg_sphere, "Radius")
    mg_circ = mk(tree, 'GeometryNodeMeshCircle', "milgrain ring", (-2500, -440))
    # v11.1: the row sat at 0.728*plate = ON the petal bases -> the beads interpenetrated the
    # petals and read as shattered shards (bypass-proven). Moved into the free slot between the
    # collar rail (0.755) and the pave band inner edge (~0.797): 0.772.
    dn(mg_circ, "Radius", float(hw["plate_radius"]) * 0.772)
    dn(mg_circ, "Vertices", 48)
    mg_pts = mk(tree, 'GeometryNodeMeshToPoints', "milgrain points", (-2300, -440))
    L(tree, mg_circ, "Mesh", mg_pts, "Mesh")
    mg_inst = mk(tree, 'GeometryNodeInstanceOnPoints', "milgrain instances", (-2100, -300))
    L(tree, mg_pts, "Points", mg_inst, "Points")
    L(tree, mg_sphere, "Mesh", mg_inst, "Instance")
    mg_real = mk(tree, 'GeometryNodeRealizeInstances', "milgrain realize", (-1900, -300))
    L(tree, mg_inst, "Instances", mg_real, "Geometry")
    mg_tr = mk(tree, 'GeometryNodeTransform', "milgrain z", (-1700, -300))
    L(tree, mg_real, "Geometry", mg_tr, "Geometry")
    dn(mg_tr, "Translation", (0.0, 0.0, step_z + mm(0.7) * 0.5 - mm(0.12)))
    mg_out, mg_sock = smooth_shade(tree, mg_tr, "Geometry", (-1500, -300), "smooth milgrain")

    # ---------------- v11 FILIGREE WIRE (lace-like jewelry detail) ----------------
    fg_join = None
    if True:
        fg_circ = mk(tree, 'GeometryNodeCurvePrimitiveCircle', "filigree rim curve",
                      (-2700, -600))
        dn(fg_circ, "Resolution", 64)
        fg_rim_r = mathx(tree, "filigree rim radius", 'MULTIPLY',
                          (-2800, -700), b=float(hw["plate_radius"]) * 0.94)
        dn(fg_circ, "Radius", 0.25)
        L(tree, fg_rim_r, "Value", fg_circ, "Radius")
        fg_prof = mk(tree, 'GeometryNodeCurvePrimitiveCircle',
                      "filigree wire profile", (-2500, -750))
        dn(fg_prof, "Resolution", 8)
        fg_width = mathx(tree, "filigree width", 'MULTIPLY',
                          (-2600, -850), b=0.012)
        L(tree, gin, "Filigree Width", fg_width, 1)
        dn(fg_prof, "Radius", 0.012)
        fg_sweep = mk(tree, 'GeometryNodeCurveToMesh', "filigree sweep",
                        (-2300, -600))
        L(tree, fg_circ, "Curve", fg_sweep, "Curve")
        L(tree, fg_prof, "Curve", fg_sweep, "Profile Curve")
        fg_z = mk(tree, 'GeometryNodeTransform', "filigree z place",
                    (-2100, -600))
        L(tree, fg_sweep, "Mesh", fg_z, "Geometry")
        dn(fg_z, "Translation", (0.0, 0.0, float(hw["plate_z"]) + float(hw["plate_depth"]) * 0.5))
        # v11 openwork: a second concentric wire + small pierced notches
        fg2_circ = mk(tree, 'GeometryNodeCurvePrimitiveCircle', "openwork rim curve",
                       (-2700, -900))
        dn(fg2_circ, "Resolution", 48)
        dn(fg2_circ, "Radius", 0.265)
        fg2_prof = mk(tree, 'GeometryNodeCurvePrimitiveCircle',
                       "openwork wire profile", (-2500, -1050))
        dn(fg2_prof, "Resolution", 6)
        dn(fg2_prof, "Radius", 0.006)
        fg2_sweep = mk(tree, 'GeometryNodeCurveToMesh', "openwork sweep",
                         (-2300, -900))
        L(tree, fg2_circ, "Curve", fg2_sweep, "Curve")
        L(tree, fg2_prof, "Curve", fg2_sweep, "Profile Curve")
        fg2_z = mk(tree, 'GeometryNodeTransform', "openwork z place",
                     (-2100, -900))
        L(tree, fg2_sweep, "Mesh", fg2_z, "Geometry")
        dn(fg2_z, "Translation", (0.0, 0.0, float(hw["plate_z"]) + float(hw["plate_depth"]) * 0.5 + 0.005))
        # join filigree + openwork
        fg_join_all = mk(tree, 'GeometryNodeJoinGeometry', "filigree join", (-1700, -750))
        L(tree, fg_z, "Geometry", fg_join_all, "Geometry")
        L(tree, fg2_z, "Geometry", fg_join_all, "Geometry")
        fg_mat = mk(tree, 'GeometryNodeSetMaterial', "filigree material", (-1500, -750))
        L(tree, fg_join_all, "Geometry", fg_mat, "Geometry")
        dn(fg_mat, "Material", mat_metal_setting)
        fg_join = fg_mat

    # v7: the seating sampler reads the real plate + step surfaces (multi-input join appends both).
    # NOTE 2026-09-17: an earlier reading of "only the step is linked" was an inspection artifact
    # (links[0] on a multi-input socket). The real seating defect was the SampleNearestSurface
    # Value-field semantics, fixed above with the raycast.
    L(tree, plate_out, plate_sock, gold_surf, "Geometry")
    L(tree, step_out, step_sock, gold_surf, "Geometry")

    # ---------------- v6 HARDWARE (real structure from research) ----------------
    plate_r = float(hw["plate_radius"])
    plate_z = float(hw["plate_z"])
    plate_d = float(hw["plate_depth"])
    HY = float(hw["stem_at"][1])
    back_z = plate_z - plate_d * 0.5
    pad_t = mm(0.6)
    hinge_x = -(plate_r - mm(4.0))
    catch_x = +(plate_r - mm(4.0))
    tip_x = catch_x + mm(3.5)
    pad_bot = back_z - pad_t
    pin_z = pad_bot - mm(0.9)
    print("  [hw] hinge_x=%.4f catch_x=%.4f pin_z=%.4f (units, pre-scale)" % (hinge_x, catch_x, pin_z))

    hw_parts = []
    # hinge pad + tubes + rod
    hw_parts.append(box(tree, "hinge pad", (-2300, 1400), (mm(8.0), mm(3.5), pad_t),
                        trans=(hinge_x, HY, back_z - pad_t * 0.5)))
    for i, (dx, ln) in enumerate(((-mm(1.8), mm(1.6)), (0.0, mm(2.0)), (mm(1.8), mm(1.6)))):
        hw_parts.append(cylinder(tree, "hinge tube %d" % i, (-2300, 1250 - i * 140),
                                 mm(0.9), ln, 16, rot=(0.0, R90, 0.0),
                                 trans=(hinge_x + dx, HY, pin_z)))
    for i_sgn, i_nm in ((-1, "hinge collar L"), (1, "hinge collar R")):
        hw_parts.append(cylinder(tree, i_nm, (-2300, 1080 + 70 * i_sgn),
                                 mm(1.1), mm(0.5), 14, rot=(0.0, R90, 0.0),
                                 trans=(hinge_x + i_sgn * mm(2.6), HY, pin_z)))
    hw_parts.append(cylinder(tree, "hinge rod", (-2300, 800), mm(0.4), mm(6.0), 12,
                             rot=(0.0, R90, 0.0), trans=(hinge_x, HY, pin_z)))
    # pin stem: tapered 1.0 -> 0.45 mm + rounded tip
    pin_len = tip_x - hinge_x
    pcone = mk(tree, 'GeometryNodeMeshCone', "pin stem", (-2300, 600))
    kn = {s.name for s in pcone.inputs}
    if "Radius1" in kn:
        dn(pcone, "Radius1", mm(0.5))
        dn(pcone, "Radius2", mm(0.225))
    else:
        dn(pcone, "Radius Bottom", mm(0.5))
        dn(pcone, "Radius Top", mm(0.225))
    dn(pcone, "Depth", pin_len)
    dn(pcone, "Vertices", 16)
    pin_tr = mk(tree, 'GeometryNodeTransform', "pin stem xf", (-2150, 600))
    L(tree, pcone, "Mesh", pin_tr, "Geometry")
    dn(pin_tr, "Rotation", (0.0, R90, 0.0))
    # 5.2 cone primitive is 0-BASED (z 0..depth) -- place base at the hinge so the
    # apex lands exactly on tip_x = hinge_x + pin_len (verified: prim_semantics_probe).
    dn(pin_tr, "Translation", (hinge_x, HY, pin_z))
    tip_s = mk(tree, 'GeometryNodeMeshUVSphere', "pin tip", (-2300, 400))
    dn(tip_s, "Segments", 12)
    dn(tip_s, "Rings", 8)
    dn(tip_s, "Radius", mm(0.225))
    tip_tr = mk(tree, 'GeometryNodeTransform', "pin tip xf", (-2150, 400))
    L(tree, tip_s, "Mesh", tip_tr, "Geometry")
    dn(tip_tr, "Translation", (tip_x, HY, pin_z))
    # v11 polish: "Show Pin" -- product/website shots hide the stem+tip (at 3/4 angles they read
    # as a dead bar across the piece); the catch hardware stays either way.
    # NOTE: two separate switches -- links.new() onto one multi-input join socket kept only the
    # last link here, so the stem silently stayed in the mesh. One switch per part, both on the
    # same socket, consumed by the (multi-part, proven) hw join.
    pin_empty = empty_geo(tree, "no pin", (-1950, 360))
    pin_sw, pin_sw_sock = geo_switch(tree, "pin switch", (-1800, 430), gin, "Show Pin",
                                     (pin_empty, "Geometry"), (pin_tr, "Geometry"))
    pin_empty2 = empty_geo(tree, "no pin tip", (-1950, 300))
    pin_sw2, pin_sw2_sock = geo_switch(tree, "pin tip switch", (-1800, 370), gin, "Show Pin",
                                       (pin_empty2, "Geometry"), (tip_tr, "Geometry"))
    hw_parts.append(pin_sw)
    hw_parts.append(pin_sw2)
    # catch: pad + riser + C torus (cut open) + safety jaw
    hw_parts.append(box(tree, "catch pad", (-2300, 200), (mm(7.0), mm(3.5), pad_t),
                        trans=(catch_x, HY, back_z - pad_t * 0.5)))
    hw_parts.append(cylinder(tree, "catch riser", (-2300, 40), mm(0.55), mm(0.9), 12,
                             trans=(catch_x, HY, pad_bot - mm(0.45))))
    c_tr = torus(tree, "c-catch torus", (-2300, -160), mm(1.3), mm(0.45), 28, 8,
                 trans=(catch_x, HY, pin_z))
    cut = mk(tree, 'GeometryNodeMeshCube', "c-cut box", (-2300, -320))
    dn(cut, "Size", (mm(1.7), mm(2.6), mm(2.4)))
    cut_tr = mk(tree, 'GeometryNodeTransform', "c-cut place", (-2150, -320))
    L(tree, cut, "Mesh", cut_tr, "Geometry")
    dn(cut_tr, "Translation", (catch_x - mm(1.15), HY, pin_z))
    booln = None
    try:
        booln = mk(tree, 'GeometryNodeMeshBoolean', "c-catch open", (-2000, -240))
        try:
            booln.operation = 'DIFFERENCE'
        except Exception:
            pass
        try:
            booln.solver = 'EXACT'
        except Exception:
            pass
        L(tree, c_tr, "Geometry", booln, 0)
        L(tree, cut_tr, "Geometry", booln, 1)
    except Exception as exc:
        print("  [hw] boolean unavailable (%r) -- using closed torus fallback" % (exc,))
        booln = c_tr
    hw_parts.append(booln)
    hw_parts.append(box(tree, "safety jaw", (-2300, -520), (mm(4.0), mm(1.8), mm(0.4)),
                        rot=(0.0, 0.0, math.radians(28.0)),
                        trans=(catch_x - mm(1.2), HY, pin_z + mm(1.35))))
    hw_parts.append(cylinder(tree, "jaw pivot boss", (-2300, -660), mm(0.45), mm(0.8), 10,
                             trans=(catch_x - mm(3.0), HY, pin_z + mm(1.35))))

    # ---------------- v8 gems: bezel ring + centre stone (prong) or EMPTY SOCKET ----------
    TAU = 6.283185307179586
    gmat_a = make_gem_material(gspec.get("material_a", "MID_Gem_Tide"),
                               gspec.get("color_a", (0.45, 0.72, 0.95)))
    gmat_b = make_gem_material(gspec.get("material_b", "MID_Gem_Radiant"),
                               gspec.get("color_b", (0.97, 0.92, 0.86)))
    ring_n = int(gspec.get("ring_count", 0) or 0)
    ring_r = float(gspec.get("ring_radius", 0.0) or 0.0)
    gem_parts = []
    if ring_n > 0 and ring_r > 0.0:
        gi = mk(tree, 'GeometryNodeInputIndex', "gem i", (-4050, -3350))
        gth = mathx(tree, "gem theta = i*(TAU/N)", 'MULTIPLY', (-3900, -3350), b=TAU / float(ring_n))
        L(tree, gi, "Index", gth, 0)
        gsn = mathx(tree, "gem sin", 'SINE', (-3750, -3450))
        gcs = mathx(tree, "gem cos", 'COSINE', (-3750, -3250))
        L(tree, gth, "Value", gsn, 0)
        L(tree, gth, "Value", gcs, 0)
        gx = mathx(tree, "gem x", 'MULTIPLY', (-3600, -3250), b=ring_r)
        gy = mathx(tree, "gem y", 'MULTIPLY', (-3600, -3450), b=ring_r)
        L(tree, gcs, "Value", gx, 0)
        L(tree, gsn, "Value", gy, 0)
        g_hi = mathx(tree, "gem sample z (plate top + 6mm)", 'ADD', (-4050, -3550),
                     a=float(hw["plate_z"]) + float(hw["plate_depth"]) * 0.5, b=mm(6.0))
        g_smp = mk(tree, 'GeometryNodeRaycast', "gem surface raycast", (-3900, -3700))
        L(tree, gold_surf, "Geometry", g_smp, "Target Geometry")
        g_sp = combine(tree, "gem sample position", (-3800, -3800))
        L(tree, gx, "Value", g_sp, "X")
        L(tree, gy, "Value", g_sp, "Y")
        L(tree, g_hi, "Value", g_sp, "Z")
        L(tree, g_sp, "Vector", g_smp, "Source Position")
        dn(g_smp, "Ray Direction", (0.0, 0.0, -1.0))
        dn(g_smp, "Ray Length", 0.2)
        g_hitz = mk(tree, 'ShaderNodeSeparateXYZ', "gem hit z", (-3860, -3850))
        L(tree, g_smp, "Hit Position", g_hitz, "Vector")
        g_lift_r = mathx(tree, "gem lift = 0.55 r", 'MULTIPLY', (-3700, -3900), b=0.55)
        L(tree, gin, "Ring Gem Size", g_lift_r, 0)
        g_lift = mathx(tree, "gem z = surface + 0.55r", 'ADD', (-3650, -3700))
        L(tree, g_hitz, "Z", g_lift, 0)
        L(tree, g_lift_r, "Value", g_lift, 1)
        g_pos = combine(tree, "gem position", (-3500, -3700))
        L(tree, gx, "Value", g_pos, "X")
        L(tree, gy, "Value", g_pos, "Y")
        L(tree, g_lift, "Value", g_pos, "Z")
        g_pts = mk(tree, 'GeometryNodePoints', "gem points", (-3350, -3600))
        L(tree, gin, "Ring Count", g_pts, "Count")
        L(tree, g_pos, "Vector", g_pts, "Position")
        g_ico = mk(tree, 'GeometryNodeMeshIcoSphere', "gem proto (faceted)", (-3350, -3950))
        dn(g_ico, "Subdivisions", 1)
        L(tree, gin, "Ring Gem Size", g_ico, "Radius")
        g_sq = mk(tree, 'GeometryNodeTransform', "gem squash", (-3150, -3950))
        L(tree, g_ico, "Mesh", g_sq, "Geometry")
        g_sqv = combine(tree, "gem squash vec", (-3250, -4100))
        d0(g_sqv, 0, 0.85)
        d0(g_sqv, 1, 0.85)
        d0(g_sqv, 2, 0.62)
        L(tree, g_sqv, "Vector", g_sq, "Scale")
        g_iop = mk(tree, 'GeometryNodeInstanceOnPoints', "instance gems", (-2950, -3700))
        L(tree, g_pts, "Geometry", g_iop, "Points")
        L(tree, g_sq, "Geometry", g_iop, "Instance")
        g_real = mk(tree, 'GeometryNodeRealizeInstances', "realize gems", (-2750, -3700))
        L(tree, g_iop, "Instances", g_real, "Geometry")
        gm, gm_s = set_material(tree, g_real, "Geometry", gmat_a, (-2600, -3700), "ring gem material")
        gem_parts.append((gm, gm_s))
        # bezel cup under every ring gem (gold, so the stones sit IN something)
        rs_baked = float(gspec.get("ring_size", 0.026) or 0.026)
        cup_g = torus(tree, "ring gem cup", (-3200, -4150), rs_baked * 0.92, rs_baked * 0.20)
        cup_tr = mk(tree, 'GeometryNodeTransform', "ring cup place", (-3000, -4150))
        L(tree, cup_g, "Geometry", cup_tr, "Geometry")
        cup_tv = combine(tree, "ring cup offset", (-3100, -4300))
        d0(cup_tv, 0, 0.0)
        d0(cup_tv, 1, 0.0)
        d0(cup_tv, 2, -rs_baked * 0.45)
        L(tree, cup_tv, "Vector", cup_tr, "Translation")
        cup_iop = mk(tree, 'GeometryNodeInstanceOnPoints', "instance ring cups", (-2800, -4150))
        L(tree, g_pts, "Geometry", cup_iop, "Points")
        L(tree, cup_tr, "Geometry", cup_iop, "Instance")
        cup_real = mk(tree, 'GeometryNodeRealizeInstances', "realize ring cups", (-2600, -4150))
        L(tree, cup_iop, "Instances", cup_real, "Geometry")
        cm2, cm2_s = set_material(tree, cup_real, "Geometry", mat_metal_setting, (-2450, -4150), "ring cup material")
        gem_parts.append((cm2, cm2_s))

    cs = float(gspec.get("center_size", 0.0) or 0.0)
    if cs > 0.0:
        c_lift = mathx(tree, "centre lift = 0.55 r", 'MULTIPLY', (-3900, -4400), b=0.55)
        L(tree, gin, "Gem Size", c_lift, 0)
        c_z = mathx(tree, "centre z = Rise + 0.55r", 'ADD', (-3750, -4400))
        L(tree, gin, "Rise", c_z, 0)
        L(tree, c_lift, "Value", c_z, 1)
        use_socket = bool(gspec.get("socket", False))
        if use_socket:
            s_rim = torus(tree, "socket rim", (-3700, -4750), cs * 1.02, cs * 0.14)
            s_tr = mk(tree, 'GeometryNodeTransform', "socket place", (-3400, -4750))
            L(tree, s_rim, "Geometry", s_tr, "Geometry")
            s_tv = combine(tree, "socket pos", (-3550, -4900))
            d0(s_tv, 0, 0.0)
            d0(s_tv, 1, 0.0)
            L(tree, c_z, "Value", s_tv, "Z")
            L(tree, s_tv, "Vector", s_tr, "Translation")
            sm, sm_s = set_material(tree, s_tr, "Geometry", mat_metal_setting, (-3250, -4750), "socket rim material")
            gem_parts.append((sm, sm_s))
            cup = mk(tree, 'GeometryNodeMeshUVSphere', "socket cup", (-3700, -5150))
            dn(cup, "Segments", 32)
            dn(cup, "Rings", 16)
            dn(cup, "Radius", cs * 0.82)
            cup_sc = mk(tree, 'GeometryNodeTransform', "socket cup squash", (-3450, -5150))
            L(tree, cup, "Mesh", cup_sc, "Geometry")
            cup_sv = combine(tree, "socket cup squash vec", (-3600, -5300))
            d0(cup_sv, 0, 1.0)
            d0(cup_sv, 1, 1.0)
            d0(cup_sv, 2, 0.42)
            L(tree, cup_sv, "Vector", cup_sc, "Scale")
            cup_tr = mk(tree, 'GeometryNodeTransform', "socket cup place", (-3200, -5150))
            L(tree, cup_sc, "Geometry", cup_tr, "Geometry")
            cup_tv = combine(tree, "socket cup pos", (-3350, -5300))
            d0(cup_tv, 0, 0.0)
            d0(cup_tv, 1, 0.0)
            cup_z = mathx(tree, "cup z = centre - 0.30 r", 'SUBTRACT', (-3600, -5050))
            L(tree, c_z, "Value", cup_z, 0)
            cup_k = mathx(tree, "cup drop = 0.30 r", 'MULTIPLY', (-3700, -5250), b=0.30)
            L(tree, gin, "Gem Size", cup_k, 0)
            L(tree, cup_k, "Value", cup_z, 1)
            L(tree, cup_z, "Value", cup_tv, "Z")
            L(tree, cup_tv, "Vector", cup_tr, "Translation")
            cm, cm_s = set_material(tree, cup_tr, "Geometry", mat_metal_setting, (-3050, -5150), "socket cup material")
            gem_parts.append((cm, cm_s))
            print("  [v10] centre = EMPTY SOCKET (reliquary) size %.3f" % cs)
        else:
            c_ico = mk(tree, 'GeometryNodeMeshIcoSphere', "centre gem proto", (-3700, -4400))
            dn(c_ico, "Subdivisions", 3)
            L(tree, gin, "Gem Size", c_ico, "Radius")
            c_sq = mk(tree, 'GeometryNodeTransform', "centre gem squash", (-3450, -4400))
            L(tree, c_ico, "Mesh", c_sq, "Geometry")
            c_sqv = combine(tree, "centre gem squash vec", (-3600, -4550))
            d0(c_sqv, 0, 0.92)
            d0(c_sqv, 1, 0.92)
            d0(c_sqv, 2, 0.7)
            L(tree, c_sqv, "Vector", c_sq, "Scale")
            c_tr = mk(tree, 'GeometryNodeTransform', "centre gem place", (-3200, -4400))
            L(tree, c_sq, "Geometry", c_tr, "Geometry")
            c_tv = combine(tree, "centre pos", (-3350, -4550))
            d0(c_tv, 0, 0.0)
            d0(c_tv, 1, 0.0)
            L(tree, c_z, "Value", c_tv, "Z")
            L(tree, c_tv, "Vector", c_tr, "Translation")
            cm, cm_s = set_material(tree, c_tr, "Geometry", gmat_b, (-3050, -4400), "centre gem material")
            gem_parts.append((cm, cm_s))
            for k in range(4):
                ang = math.radians(45.0 + 90.0 * k)
                claw = cylinder(tree, "claw %d" % k, (-3600 - 60 * k, -5750 + 40 * k),
                                cs * 0.10, cs * 1.15, 10,
                                rot=(math.radians(15.0), 0.0, ang),
                                trans=(math.cos(ang) * cs * 0.78, math.sin(ang) * cs * 0.78, 0.0))
                cl_tr = mk(tree, 'GeometryNodeTransform', "claw %d place" % k, (-3350 - 60 * k, -5750 + 40 * k))
                L(tree, claw, "Geometry", cl_tr, "Geometry")
                cl_tv = combine(tree, "claw %d pos" % k, (-3480 - 60 * k, -5900 + 40 * k))
                d0(cl_tv, 0, 0.0)
                d0(cl_tv, 1, 0.0)
                L(tree, c_z, "Value", cl_tv, "Z")
                L(tree, cl_tv, "Vector", cl_tr, "Translation")
                clm, clm_s = set_material(tree, cl_tr, "Geometry", mat_metal_setting, (-3150 - 60 * k, -5750 + 40 * k),
                                          "claw %d material" % k)
                gem_parts.append((clm, clm_s))
            print("  [v10] centre = prong-set gem size %.3f" % cs)

    if gem_parts:
        g_join = mk(tree, 'GeometryNodeJoinGeometry', "join gems", (-2600, -4300))
        for src, ss in gem_parts:
            L(tree, src, ss, g_join, "Geometry")
        gem_sw, gem_sw_sock = geo_switch(tree, "gems switch", (-2450, -4300), gin, "Gems On",
                                         (empty_geo(tree, "no gems", (-2700, -4600)), "Geometry"),
                                         (g_join, "Geometry"))
        print("  [v10] gems: ring=%d r=%.3f size=%.3f | centre=%.3f | parts=%d" % (
            ring_n, ring_r, float(gspec.get("ring_size", 0.0) or 0.0), cs, len(gem_parts)))
    else:
        gem_sw, gem_sw_sock = None, None

    # dangles live on their own object/tree (build_dangles) -- body stays time-free
    dang_sw, dang_sw_sock = None, None

    # ---------------- join / merge / real scale / output ------------------------
    j_gold = mk(tree, 'GeometryNodeJoinGeometry', "join gold", (-1200, -300))
    # per-part material IDs (texture masks): petals / dome / structural body / stone setting
    gold_parts = (
        (petal_out, petal_sock, mat_metal_petal, "petals"),
        (dome_out, dome_sock, mat_metal_dome, "dome"),
        (step_out, step_sock, mat_metal_body, "step"),
        (plate_out, plate_sock, mat_metal_body, "plate"),
        (rail_out, rail_sock, mat_metal_body, "rail"),
        (mg_out, mg_sock, mat_metal_body, "milgrain"),
        (rim_out, rim_sock, mat_metal_body, "rim beads"),
        (grvj_out, grvj_sock, mat_metal_body, "plate rails"),
        (seats_out, seats_sock, mat_metal_body, "seats"),
        (bezel_out, bezel_sock, mat_metal_setting, "bezel"),
        (collar_out, collar_sock, mat_metal_body, "collar"),
    )
    # v11 filigree (lace-like wire detail) — added to gold join when present
    if fg_join is not None:
        gold_parts = gold_parts + ((fg_join, "Geometry", mat_metal_setting, "filigree"),)
    for gi, (src, ss, gmat, gtag) in enumerate(gold_parts):
        if src is None:
            continue
        try:
            pm, pm_s = set_material(tree, src, ss, gmat, (-1240, -360 - 36 * gi),
                                    "gold %s material" % gtag)
            L(tree, pm, pm_s, j_gold, "Geometry")
        except Exception as exc:
            print("warn: gold join %s (%r)" % (gtag, exc))
    # v7 cast finish: optional in-tree SDF weld + fillet of the gold body (Blender 5.0 grid chain)
    vox_k = mathx(tree, "mm -> units", 'MULTIPLY', (-1180, -180))
    L(tree, gin, "Cast Voxel (mm)", vox_k, 0)
    d0(vox_k, 1, mm(1.0))
    m2s = mk(tree, 'GeometryNodeMeshToSDFGrid', "cast: mesh -> sdf", (-1150, -140))
    L(tree, j_gold, "Geometry", m2s, "Mesh")
    L(tree, vox_k, "Value", m2s, "Voxel Size")
    sdf_fil = mk(tree, 'GeometryNodeSDFGridFillet', "cast: fillet", (-1000, -140))
    L(tree, m2s, "SDF Grid", sdf_fil, "Grid")
    L(tree, gin, "Cast Fillet Iters", sdf_fil, "Iterations")
    mean = mk(tree, 'GeometryNodeSDFGridMean', "cast: mean smooth", (-925, -60))
    L(tree, sdf_fil, "Grid", mean, "Grid")
    dn(mean, "Iterations", mean_default)  # averaging pass: removes voxel stair-stepping
    g2m = mk(tree, 'GeometryNodeGridToMesh', "cast: sdf -> mesh", (-850, -140))
    L(tree, mean, "Grid", g2m, "Grid")
    dn(g2m, "Threshold", 0.0)
    cast_sh, cast_sh_sock = smooth_shade(tree, g2m, "Mesh", (-700, -140), "smooth cast")
    cast_mat, cast_mat_sock = set_material(tree, cast_sh, cast_sh_sock, mat_metal_petal, (-640, -40),
                                           "cast gold material (the weld collapses the per-part IDs)")
    cast_sw, cast_sw_sock = geo_switch(tree, "cast switch", (-560, -240), gin, "Cast Finish",
                                       (j_gold, "Geometry"), (cast_mat, cast_mat_sock))
    gold_out, gold_sock = cast_sw, cast_sw_sock
    j_bead = mk(tree, 'GeometryNodeJoinGeometry', "join beads", (-1200, -700))
    # per-part bead IDs: pave micro-beads vs pearls (centre + accents)
    pb, pb_s = set_material(tree, pave_out, pave_sock, mat_bead_pave, (-1240, -780), "pave beads material")
    L(tree, pb, pb_s, j_bead, "Geometry")
    for bsrc, bss, btag in ((acc_out, acc_sock, "accents"), (bead_out, bead_sock, "centre pearl")):
        bb, bb_s = set_material(tree, bsrc, bss, mat_bead_pearl, (-1240, -660), "%s material" % btag)
        L(tree, bb, bb_s, j_bead, "Geometry")
    bead_out2, bead_sock2 = j_bead, "Geometry"
    j_hw = mk(tree, 'GeometryNodeJoinGeometry', "join hardware", (-1200, 300))
    for src in hw_parts:
        try:
            L(tree, src, first_geo_out(src), j_hw, "Geometry")
        except Exception as exc:
            print("warn: hw join %s (%r)" % (getattr(src, "name", src), exc))
    hw_out, hw_sock = set_material(tree, j_hw, "Geometry", mat_pin, (-900, 300), "hardware material")
    j_all = mk(tree, 'GeometryNodeJoinGeometry', "join all", (-600, 0))
    L(tree, gold_out, gold_sock, j_all, "Geometry")
    L(tree, bead_out2, bead_sock2, j_all, "Geometry")
    L(tree, hw_out, hw_sock, j_all, "Geometry")
    if gem_sw is not None:
        L(tree, gem_sw, gem_sw_sock, j_all, "Geometry")
    merge = mk(tree, 'GeometryNodeMergeByDistance', "merge by distance", (-400, 0))
    L(tree, j_all, "Geometry", merge, "Geometry")
    dn(merge, "Distance", float(hw["merge_distance"]))
    rs = mk(tree, 'GeometryNodeTransform', "real scale", (-150, 0))
    L(tree, merge, "Geometry", rs, "Geometry")
    rs_v = combine(tree, "real scale vec", (-300, -150))
    L(tree, gin, "Real Scale", rs_v, "X")
    L(tree, gin, "Real Scale", rs_v, "Y")
    L(tree, gin, "Real Scale", rs_v, "Z")
    L(tree, rs_v, "Vector", rs, "Scale")
    # v7: auto UV (5.1 UV Unwrap node, SLIM method) — opt-in; slow on the cast body
    uv_u = mk(tree, 'GeometryNodeUVUnwrap', "auto uv (slim)", (-200, -420))
    try:
        ms = uv_u.inputs["Method"]
        for item in ms.enum_items:
            if "STRETCH" in item.identifier.upper():
                ms.default_value = item.identifier
                print("  uv method ->", item.identifier)
                break
    except Exception as exc:
        print("  uv method warn: %r" % (exc,))
    try:
        uv_u.inputs["Margin"].default_value = 0.001
    except Exception:
        pass
    uv_store = mk(tree, 'GeometryNodeStoreNamedAttribute', "store UVMap", (0, -420))
    L(tree, rs, "Geometry", uv_store, "Geometry")
    L(tree, uv_u, "UV", uv_store, "Value")
    try:
        uv_store.data_type = 'FLOAT2'
        uv_store.domain = 'CORNER'
    except Exception:
        pass
    try:
        uv_store.inputs["Name"].default_value = "UVMap"
    except Exception:
        pass
    uv_sw, uv_sw_sock = geo_switch(tree, "uv switch", (200, -160), gin, "Auto UV",
                                   (rs, "Geometry"), (uv_store, "Geometry"))
    L(tree, uv_sw, uv_sw_sock, gout, "Geometry")

    if bloom:
        try:
            add_bloom_driver(tree)
        except Exception as exc:
            print("  [bloom] driver skipped: %r" % (exc,))
    else:
        print("  [bloom] static body (bloom=False): the body tree carries no SceneTime by design")

    tree.use_fake_user = True
    print("[%s] built: %d nodes, %d links" % (tree_name, len(tree.nodes), len(tree.links)))
    return tree


def add_bloom_driver(tree, loop_frames=96):
    """In-tree Scene-Time bloom cycle (v5 behaviour kept)."""
    gin = None
    for n in tree.nodes:
        if n.type == 'GROUP_INPUT':
            gin = n
            break
    if gin is None:
        print("  [bloom] no group input node; skipped")
        return 0
    TAU = 6.283185307179586
    t = mk(tree, 'GeometryNodeInputSceneTime', "bloom time", (-6900, 800))
    m1 = mathx(tree, "bloom t-1", 'SUBTRACT', (-6700, 800), b=1.0)
    L(tree, t, "Frame", m1, 0)
    m2 = mathx(tree, "bloom phase", 'MULTIPLY', (-6550, 800), b=TAU / (loop_frames - 1))
    L(tree, m1, "Value", m2, 0)
    m3 = mathx(tree, "bloom cos", 'COSINE', (-6400, 800))
    L(tree, m2, "Value", m3, 0)
    m4 = mathx(tree, "bloom s a", 'MULTIPLY', (-6250, 800), b=0.5)
    L(tree, m3, "Value", m4, 0)
    m5 = mathx(tree, "bloom s", 'ADD', (-6100, 800), b=0.5)
    L(tree, m4, "Value", m5, 0)
    sh1 = mathx(tree, "bloom shrink a", 'MULTIPLY', (-5950, 950), b=0.65)
    L(tree, m5, "Value", sh1, 0)
    sh2 = mathx(tree, "bloom shrink", 'ADD', (-5800, 950), b=0.35)
    L(tree, sh1, "Value", sh2, 0)
    cl1 = mathx(tree, "bloom close a", 'MULTIPLY', (-5950, 650), b=-1.2)
    L(tree, m5, "Value", cl1, 0)
    cl2 = mathx(tree, "bloom close", 'ADD', (-5800, 650), b=2.2)
    L(tree, cl1, "Value", cl2, 0)
    total = 0
    splices = (("Spread", sh2), ("Rise", sh2), ("Chaos", sh2),
               ("Petal Length", sh2), ("Tilt", cl2))
    for i, (sock, factor) in enumerate(splices):
        try:
            gin.outputs[sock]
        except Exception:
            print("  [bloom] socket absent: %s" % sock)
            continue
        cons = [ln for ln in tree.links if ln.from_node == gin and ln.from_socket.name == sock]
        if not cons:
            print("  [bloom] no consumers: %s" % sock)
            continue
        mul = mathx(tree, "bloom x %s" % sock, 'MULTIPLY', (-5600, 500 - 90 * i))
        L(tree, gin, sock, mul, 0)
        L(tree, factor, "Value", mul, 1)
        for ln in cons:
            to_sock = ln.to_socket
            tree.links.remove(ln)
            tree.links.new(mul.outputs[0], to_sock)
        total += len(cons)
    print("  [bloom] driver spliced: %d sockets, %d consumers" % (len(splices), total))
    return total


def attach(ob, tree):
    mod = None
    for m in ob.modifiers:
        if m.type == 'NODES':
            mod = m
            break
    if mod is None:
        mod = ob.modifiers.new("GN_Brooch", 'NODES')
        print("created new modifier GN_Brooch")
    before = mod.node_group.name if mod.node_group else None
    mod.node_group = tree
    mod.show_viewport = True
    mod.show_render = True
    synced, total = 0, 0
    for item in tree.interface.items_tree:
        if getattr(item, "in_out", "") != "INPUT":
            continue
        total += 1
        val = item.default_value
        done = False
        try:
            mod.properties.inputs[item.identifier]["value"] = val
            done = True
        except Exception:
            try:
                mod[item.identifier] = val
                done = True
            except Exception:
                try:
                    mod[item.name] = val
                    done = True
                except Exception as exc:
                    print("  warn: could not set %s (%r)" % (item.name, exc))
        synced += 1 if done else 0
    print("modifier %r: node_group %s -> %s; inputs synced %d/%d" % (
        mod.name, before, tree.name, synced, total))
    return mod


def ensure_bevel(ob):
    mod = ob.modifiers.get("Bevel_Detail")
    if mod is None:
        mod = ob.modifiers.new("Bevel_Detail", 'BEVEL')
        print("created Bevel_Detail modifier")
    # stack position: directly after the GN modifier, BEFORE any outline pass
    try:
        gn_idx = 0
        for i, m in enumerate(ob.modifiers):
            if m.type == 'NODES' and m.node_group is not None and m.node_group.name.startswith("GN_FlowerBrooch"):
                gn_idx = i
        want = gn_idx + 1
        have = list(ob.modifiers).index(mod)
        if have != want:
            ob.modifiers.move(have, want)
            print("Bevel_Detail moved to index %d (after GN, before other passes)" % want)
    except Exception as exc:
        print("warn: could not reorder bevel (%r)" % (exc,))
    mod.width = 0.045
    mod.segments = 3
    try:
        mod.limit_method = 'ANGLE'
        mod.angle_limit = math.radians(35.0)
    except Exception as exc:
        print("warn: bevel angle setup (%r)" % (exc,))
    try:
        mod.use_clamp_overlap = True
    except Exception:
        pass
    try:
        mod.miter_outer = 'MITER_ARC'
    except Exception:
        pass
    print("Bevel_Detail: width=0.045 segments=3 angle=35 clamp=True")
    return mod


def measure(ob):
    bpy.context.view_layer.update()
    dg = bpy.context.evaluated_depsgraph_get()
    me = ob.evaluated_get(dg).data
    nv, nf = len(me.vertices), len(me.polygons)
    if not nv:
        return {"nv": 0, "nf": 0, "mm": None, "per_mat": {}, "bb": None, "per_mat_bb": {}}
    xs = [v.co.x for v in me.vertices]
    ys = [v.co.y for v in me.vertices]
    zs = [v.co.z for v in me.vertices]
    ext = [max(xs) - min(xs), max(ys) - min(ys), max(zs) - min(zs)]
    bb = [[min(xs), min(ys), min(zs)], [max(xs), max(ys), max(zs)]]
    per_mat = {}
    per_mat_bb = {}
    try:
        slot_names = [m.name if m else "slot%d" % i for i, m in enumerate(me.materials)]
        acc = {}
        for p in me.polygons:
            acc.setdefault(p.material_index, []).extend(
                [me.vertices[vi].co for vi in p.vertices])
        for mi, cos in acc.items():
            if not cos:
                continue
            ax = [c.x for c in cos]
            ay = [c.y for c in cos]
            az = [c.z for c in cos]
            key = slot_names[mi] if mi < len(slot_names) else "m%d" % mi
            per_mat[key] = [
                round((max(ax) - min(ax)) * 100.0, 2),
                round((max(ay) - min(ay)) * 100.0, 2),
                round((max(az) - min(az)) * 100.0, 2)]
            per_mat_bb[key] = ([min(ax), min(ay), min(az)], [max(ax), max(ay), max(az)])
    except Exception as exc:
        print("  warn: per-material measure (%r)" % (exc,))
    return {"nv": nv, "nf": nf, "mm": [round(e * 100.0, 2) for e in ext],
            "per_mat": per_mat, "bb": bb, "per_mat_bb": per_mat_bb}


def gold_bb_from(per_mat_bb):
    """Metal-part bbox: union over every slot whose name reads as metal (Petal/Metal IDs).
    Keeps the sizing law anchored on the metal extent now that the gold body is split into
    per-part IDs (MID_Metal_Petal / _Dome / _Body / _Setting). Pin/beads/gems excluded (as before)."""
    acc = None
    for name, bb in (per_mat_bb or {}).items():
        if name and ("Petal" in name or "Metal" in name):
            acc = bb_union(acc, bb)
    return acc


def bb_union(a, b):
    if a is None:
        return b
    if b is None:
        return a
    lo = [min(a[0][i], b[0][i]) for i in range(3)]
    hi = [max(a[1][i], b[1][i]) for i in range(3)]
    return (lo, hi)


def bb_dims_mm(bb):
    return [round((bb[1][i] - bb[0][i]) * 100.0, 2) for i in range(3)]


def union_gold_dims(m_body, m_dangle):
    """Sizing-law metric: gold-slot bbox dims (mm) unioned across body + dangles."""
    gb = gold_bb_from((m_body or {}).get("per_mat_bb"))
    if m_dangle:
        gb = bb_union(gb, gold_bb_from(m_dangle.get("per_mat_bb")))
    if gb is None:
        return None
    return bb_dims_mm(gb)


def dangle_tree_name(tname):
    return tname.replace("FlowerBrooch", "BroochDangles")


DANGLE_OBJ_NAME = "FlowerBrooch_Dangles"
PETAL_OBJ_NAME = "FlowerBrooch_Petals"


def dangle_block(tree, gin, dspec, hw, mat_petal, mat_bead):
    """v8 en-tremblant chains: eyelet + hinge + N links + terminal drop per dangle on the front
    arc, each with its own SceneTime sway. Standalone (no body geometry). Returns (switch, sock)."""
    TAU = 6.283185307179586
    dang_sw, dang_sw_sock = None, None
    d_count = int(dspec.get("count", 0) or 0)
    if d_count > 0:
        rim_r = float(hw["plate_radius"]) * float(dspec.get("rim_frac", 0.97))
        link_r = float(dspec.get("link_radius", 0.010))
        link_t = float(dspec.get("link_thick", 0.0028))
        n_links = int(dspec.get("links", 3))
        term_r = float(dspec.get("terminal_size", 0.015))
        hz = float(hw["plate_z"]) - float(hw["plate_depth"]) * 0.5 - link_t * 1.2
        arc = math.radians(float(dspec.get("arc_deg", 200.0)))
        a0 = math.radians(float(dspec.get("arc_center_deg", 270.0))) - arc * 0.5
        d_parts = []
        for i in range(d_count):
            th = a0 + (arc * i / float(max(1, d_count - 1)))
            hx = math.cos(th) * rim_r
            hy = math.sin(th) * rim_r
            left = -3900 - 46 * i
            top = 260 - 34 * i
            z = -link_r * 1.5
            fr = mk(tree, 'GeometryNodeInputSceneTime', "dangle %d time" % i, (left - 60, top + 460))
            sw1 = mathx(tree, "dangle %d sway a" % i, 'MULTIPLY', (left + 70, top + 460))
            L(tree, fr, "Frame", sw1, 0)
            L(tree, gin, "Dangle Rate", sw1, 1)
            sw2 = mathx(tree, "dangle %d sway w" % i, 'MULTIPLY', (left + 200, top + 460), b=TAU / 60.0)
            L(tree, sw1, "Value", sw2, 0)
            sw3 = mathx(tree, "dangle %d sway ph" % i, 'ADD', (left + 330, top + 460), b=float(i) * 0.55)
            L(tree, sw2, "Value", sw3, 0)
            sw4 = mathx(tree, "dangle %d sway sin" % i, 'SINE', (left + 460, top + 460))
            L(tree, sw3, "Value", sw4, 0)
            sw5 = mathx(tree, "dangle %d sway deg" % i, 'MULTIPLY', (left + 590, top + 460))
            L(tree, sw4, "Value", sw5, 0)
            L(tree, gin, "Dangle Sway", sw5, 1)
            swr = mathx(tree, "dangle %d sway rad" % i, 'MULTIPLY', (left + 720, top + 460), b=0.017453292519943295)
            L(tree, sw5, "Value", swr, 0)
            dj = mk(tree, 'GeometryNodeJoinGeometry', "dangle %d join" % i, (left + 40, top - 40))
            eyelet = torus(tree, "dangle %d eyelet" % i, (left, top), link_t * 1.5, link_t * 0.7,
                           rot=(R90, 0.0, 0.0), trans=(0.0, 0.0, link_t * 1.6))
            em, em_s = set_material(tree, eyelet, first_geo_out(eyelet), mat_petal,
                                    (left - 30, top + 40), "dangle %d eyelet mat" % i)
            L(tree, em, em_s, dj, "Geometry")
            hinge = torus(tree, "dangle %d hinge" % i, (left, top), link_r * 1.25, link_t * 1.1,
                           rot=(R90, 0.0, 0.0))
            hm, hm_s = set_material(tree, hinge, first_geo_out(hinge), mat_petal,
                                    (left - 30, top + 40 + 24), "dangle %d hinge mat" % i)
            L(tree, hm, hm_s, dj, "Geometry")
            for j in range(n_links):
                rot = (R90, 0.0, 0.0) if j % 2 == 0 else (0.0, R90, 0.0)
                lk = torus(tree, "dangle %d link %d" % (i, j), (left, top),
                           link_r, link_t, rot=rot, trans=(0.0, 0.0, z))
                lk_m, lk_s = set_material(tree, lk, first_geo_out(lk), mat_petal,
                                          (left - 30, top + 40 + 24 * j),
                                          "dangle %d chain mat %d" % (i, j))
                lag_mul = mathx(tree, "dangle %d link %d lag" % (i, j), 'MULTIPLY',
                                (left + 850, top + 320 + 30 * j), b=float(j + 1) * 0.15)
                L(tree, swr, "Value", lag_mul, 0)
                lk_rot = combine(tree, "dangle %d link %d rot" % (i, j),
                                 (left + 1000, top + 350 + 30 * j))
                d0(lk_rot, 0, 0.0)
                L(tree, lag_mul, "Value", lk_rot, "Y")
                d0(lk_rot, 2, th)
                lk_tr = mk(tree, 'GeometryNodeTransform', "dangle %d link %d lag_tr" % (i, j),
                            (left + 1150, top + 320 + 30 * j))
                L(tree, lk_m, lk_s, lk_tr, "Geometry")
                L(tree, lk_rot, "Vector", lk_tr, "Rotation")
                lk_pos = combine(tree, "dangle %d link %d pos" % (i, j),
                                 (left + 1000, top + 200 + 30 * j))
                d0(lk_pos, 0, 0.0)
                d0(lk_pos, 1, 0.0)
                lk_z = mathx(tree, "dangle %d link %d z" % (i, j), 'MULTIPLY',
                             (left + 850, top + 200 + 30 * j), b=float(j) * (link_r * 1.45))
                L(tree, lk_z, "Value", lk_pos, "Z")
                L(tree, lk_pos, "Vector", lk_tr, "Translation")
                L(tree, lk_tr, "Geometry", dj, "Geometry")
                z -= link_r * 1.45
            drop = mk(tree, 'GeometryNodeMeshUVSphere', "dangle %d drop" % i, (left, top))
            dn(drop, "Segments", 24)
            dn(drop, "Rings", 16)
            dn(drop, "Radius", term_r)
            d_sc = mk(tree, 'GeometryNodeTransform', "dangle %d drop squash" % i, (left, top - 60))
            L(tree, drop, "Mesh", d_sc, "Geometry")
            d_sv = combine(tree, "dangle %d squash vec" % i, (left - 90, top - 140))
            d0(d_sv, 0, 1.0)
            d0(d_sv, 1, 1.0)
            d0(d_sv, 2, 0.78)
            L(tree, d_sv, "Vector", d_sc, "Scale")
            d_tr = mk(tree, 'GeometryNodeTransform', "dangle %d drop place" % i, (left, top - 120))
            L(tree, d_sc, "Geometry", d_tr, "Geometry")
            d_tv = combine(tree, "dangle %d drop pos" % i, (left - 90, top - 200))
            d0(d_tv, 0, 0.0)
            d0(d_tv, 1, 0.0)
            d0(d_tv, 2, z - term_r * 0.9)
            L(tree, d_tv, "Vector", d_tr, "Translation")
            d_sh, d_sh_s = smooth_shade(tree, d_tr, "Geometry", (left, top - 180), "dangle %d drop smooth" % i)
            dm, dm_s = set_material(tree, d_sh, d_sh_s, mat_bead, (left - 30, top - 200),
                                    "dangle %d drop mat" % i)
            L(tree, dm, dm_s, dj, "Geometry")
            rot_v = combine(tree, "dangle %d euler" % i, (left + 850, top + 460))
            d0(rot_v, 0, 0.0)
            L(tree, swr, "Value", rot_v, "Y")
            d0(rot_v, 2, th)
            pos_v = combine(tree, "dangle %d place" % i, (left + 850, top + 320))
            d0(pos_v, 0, hx)
            d0(pos_v, 1, hy)
            d0(pos_v, 2, hz)
            sw_tr = mk(tree, 'GeometryNodeTransform', "dangle %d swing" % i, (left + 1000, top + 380))
            L(tree, dj, "Geometry", sw_tr, "Geometry")
            L(tree, rot_v, "Vector", sw_tr, "Rotation")
            L(tree, pos_v, "Vector", sw_tr, "Translation")
            d_parts.append((sw_tr, "Geometry"))
        d_join = mk(tree, 'GeometryNodeJoinGeometry', "join dangles", (-2350, 260))
        for src, ss in d_parts:
            L(tree, src, ss, d_join, "Geometry")
        dang_sw, dang_sw_sock = geo_switch(tree, "dangles switch", (-2200, 260), gin, "Dangles On",
                                           (empty_geo(tree, "no dangles", (-2500, 80)), "Geometry"),
                                           (d_join, "Geometry"))
        print("  [v10] dangles: %d | rim %.3f | links %d x %.3f | drop %.3f | sway %.1f deg @ %.2f" % (
            d_count, rim_r, n_links, link_r, term_r,
            float(dspec.get("sway_deg", 12.0) or 0.0), float(dspec.get("rate", 0.7) or 0.0)))
    return dang_sw, dang_sw_sock


def build_dangles(genome_id, tree_name, bg, real_scale=1.0):
    """Own-object dangles tree: same genome spec as the body, but chains only + their own
    SceneTime, so the body stays cached across frames while the chains animate (cheap re-cook)."""
    r = bg.resolve_genome(genome_id)
    t = r["traits"]
    hw = t["hardware"]
    dspec = t.get("dangles") or {}
    d_count = int(dspec.get("count", 0) or 0)
    if d_count <= 0:
        return None
    mats = t.get("materials") or {}
    mat_petal = bpy.data.materials.get(mats.get("petal", ""))
    mat_bead = bpy.data.materials.get(mats.get("bead", ""))
    if mat_petal is None or mat_bead is None:
        ob = bpy.data.objects.get(OBJ_NAME)
        if ob is not None and ob.material_slots:
            mat_petal = mat_petal or (ob.material_slots[0].material if ob.material_slots[0] else None)
    if mat_petal is None or mat_bead is None:
        print("  [dangles] materials missing; skipped")
        return None
    mat_chain = resolve_material(mats, "metal_chain", "petal", mat_petal)
    mat_pearl = resolve_material(mats, "bead_pearl", "bead", mat_bead)
    old = bpy.data.node_groups.get(tree_name)
    if old is not None:
        bpy.data.node_groups.remove(old)
    tree = bpy.data.node_groups.new(tree_name, 'GeometryNodeTree')

    def iface(name, stype, default, mn=None, mx=None):
        s = tree.interface.new_socket(name=name, in_out='INPUT', socket_type=stype)
        try:
            s.default_value = default
        except Exception:
            pass
        if mx is not None:
            try:
                s.max_value = mx
            except Exception:
                pass
        if mn is not None:
            try:
                s.min_value = mn
            except Exception:
                pass
        return s

    iface("Real Scale", 'NodeSocketFloat', float(real_scale), 0.05, 5.0)
    iface("Dangles On", 'NodeSocketBool', True)
    iface("Dangle Sway", 'NodeSocketFloat', float(dspec.get("sway_deg", 12.0) or 0.0), 0.0, 40.0)
    iface("Dangle Rate", 'NodeSocketFloat', float(dspec.get("rate", 0.7) or 0.0), 0.0, 3.0)
    tree.interface.new_socket(name="Geometry", in_out='OUTPUT', socket_type='NodeSocketGeometry')
    gin = mk(tree, 'NodeGroupInput', "Group Input", (-6200, 200))
    gout = mk(tree, 'NodeGroupOutput', "Group Output", (3400, 0))
    dang_sw, dang_sw_sock = dangle_block(tree, gin, dspec, hw, mat_chain, mat_pearl)
    src_node, src_sock = (dang_sw, dang_sw_sock)
    if src_node is None:
        src_node = empty_geo(tree, "no dangles (empty)", (0, 0))
        src_sock = first_geo_out(src_node)
    rs = mk(tree, 'GeometryNodeTransform', "dangles real scale", (1800, 0))
    L(tree, src_node, src_sock, rs, "Geometry")
    rs_v = combine(tree, "dangles scale vec", (1600, -150))
    L(tree, gin, "Real Scale", rs_v, "X")
    L(tree, gin, "Real Scale", rs_v, "Y")
    L(tree, gin, "Real Scale", rs_v, "Z")
    L(tree, rs_v, "Vector", rs, "Scale")
    L(tree, rs, "Geometry", gout, "Geometry")
    tree.use_fake_user = True
    print("[%s] dangles tree built: %d nodes | %d chains | sway %.1f deg @ %.2f"
          % (tree_name, len(tree.nodes), d_count,
             float(dspec.get("sway_deg", 12.0) or 0.0), float(dspec.get("rate", 0.7) or 0.0)))
    return tree


def ensure_dangle_object(tree):
    """Create/update FlowerBrooch_Dangles: parented to the hero (identity local), dangles tree
    attached, and the outline pass copied from the hero stack (same values)."""
    from mathutils import Matrix
    ob = bpy.data.objects.get(DANGLE_OBJ_NAME)
    if ob is None:
        me = bpy.data.meshes.new(DANGLE_OBJ_NAME)
        ob = bpy.data.objects.new(DANGLE_OBJ_NAME, me)
        bpy.context.scene.collection.objects.link(ob)
        print("created dangle object:", DANGLE_OBJ_NAME)
    hero = bpy.data.objects.get(OBJ_NAME)
    if hero is not None and ob.parent is None:
        ob.parent = hero
        ob.matrix_parent_inverse = Matrix.Identity(4)
        ob.location = (0.0, 0.0, 0.0)
        ob.rotation_euler = (0.0, 0.0, 0.0)
        ob.scale = (1.0, 1.0, 1.0)
        print("dangle object parented to", OBJ_NAME)
    mod = None
    for m in ob.modifiers:
        if m.type == 'NODES':
            mod = m
            break
    if mod is None:
        mod = ob.modifiers.new("GN_Dangles", 'NODES')
    before = mod.node_group.name if mod.node_group else None
    mod.node_group = tree
    mod.show_viewport = True
    mod.show_render = True
    for item in tree.interface.items_tree:
        if getattr(item, "in_out", "") != "INPUT":
            continue
        val = item.default_value
        try:
            mod.properties.inputs[item.identifier]["value"] = val
        except Exception:
            try:
                mod[item.identifier] = val
            except Exception:
                pass
    print("dangles modifier %r: node_group %s -> %s" % (mod.name, before, tree.name))
    # outline pass (same tree + same values as the hero's)
    hero = bpy.data.objects.get(OBJ_NAME)
    hero_outline = None
    if hero is not None:
        for m in hero.modifiers:
            if m.type == 'NODES' and m.node_group and m.node_group.name == "Outline [GeoNodes]":
                hero_outline = m
                break
    if hero_outline is not None:
        om = ob.modifiers.get("Outline [GeoNodes]")
        if om is None:
            om = ob.modifiers.new("Outline [GeoNodes]", 'NODES')
        om.node_group = hero_outline.node_group
        om.show_viewport = hero_outline.show_viewport
        om.show_render = hero_outline.show_render
        try:
            for item in hero_outline.node_group.interface.items_tree:
                if getattr(item, "in_out", "") != "INPUT":
                    continue
                try:
                    v = hero_outline.properties.inputs[item.identifier]["value"]
                    om.properties.inputs[item.identifier]["value"] = v
                except Exception:
                    pass
            print("dangle outline pass mirrored (values copied from the hero)")
        except Exception as exc:
            print("  warn: outline copy (%r)" % (exc,))
    return ob


def build_petals(genome_id, tree_name, bg, real_scale=1.0):
    """Own-object petals tree: the petal block extracted from the body, with flutter
    (SceneTime) enabled. The body stays time-free; the petals object re-cooks per frame
    (cheap — only the petal system, not the whole stack)."""
    r = bg.resolve_genome(genome_id)
    t = r["traits"]
    crown, phy, mats = t["crown"], t["phyllotaxis"], t["materials"]
    mat_petal = bpy.data.materials.get(mats.get("petal", ""))
    if mat_petal is None:
        ob = bpy.data.objects.get(OBJ_NAME)
        if ob is not None and ob.material_slots:
            mat_petal = ob.material_slots[0].material
    if mat_petal is None:
        print("  [petals] materials missing; skipped")
        return None
    mat_metal_petal = resolve_material(mats, "metal_petal", "petal", mat_petal)

    body_tree_name = tree_name
    body_tree = bpy.data.node_groups.get(body_tree_name)
    if body_tree is None:
        print("  [petals] body tree %r not found; skipped" % body_tree_name)
        return None

    pt_name = body_tree_name.replace("FlowerBrooch", "BroochPetals")
    old = bpy.data.node_groups.get(pt_name)
    if old is not None:
        try:
            bpy.data.node_groups.remove(old)
        except Exception:
            pass
    ptree = bpy.data.node_groups.new(pt_name, 'GeometryNodeTree')

    # clone the body's interface sockets (so the modifier panel shows the same dials)
    clone_interface(body_tree, ptree)

    # flutter-specific sockets (added on top of the cloned body interface)
    try:
        s = ptree.interface.new_socket(name="Petal Amp", in_out='INPUT', socket_type='NodeSocketFloat')
        s.default_value = 0.05
        s.min_value = 0.0
        s.max_value = 0.3
    except Exception:
        pass
    try:
        s = ptree.interface.new_socket(name="Petal Rate", in_out='INPUT', socket_type='NodeSocketFloat')
        s.default_value = 0.7
        s.min_value = 0.0
        s.max_value = 3.0
    except Exception:
        pass
    try:
        s = ptree.interface.new_socket(name="Real Scale", in_out='INPUT', socket_type='NodeSocketFloat')
        s.default_value = float(real_scale)
        s.min_value = 0.05
        s.max_value = 5.0
    except Exception:
        pass

    # add the output socket FIRST (before Group Output node, so its input auto-creates)
    ptree.interface.new_socket(name="Geometry", in_out='OUTPUT', socket_type='NodeSocketGeometry')
    pgin = mk(ptree, 'NodeGroupInput', "Group Input", (-6200, 200))
    pgout = mk(ptree, 'NodeGroupOutput', "Group Output", (3400, 0))

    petal_out, petal_sock, _, _, _, _, _, _ = petal_system(ptree, pgin, crown, phy, mat_metal_petal, flutter=True)

    # material + real scale + output
    pmat, pmat_s = set_material(ptree, petal_out, petal_sock, mat_metal_petal, (-2200, 0), "petals metal")
    rs = mk(ptree, 'GeometryNodeTransform', "petals real scale", (-1500, 0))
    L(ptree, pmat, pmat_s, rs, "Geometry")
    rs_v = combine(ptree, "petals scale vec", (-1700, -150))
    L(ptree, pgin, "Real Scale", rs_v, "X")
    L(ptree, pgin, "Real Scale", rs_v, "Y")
    L(ptree, pgin, "Real Scale", rs_v, "Z")
    L(ptree, rs_v, "Vector", rs, "Scale")
    L(ptree, rs, "Geometry", pgout, "Geometry")

    ptree.use_fake_user = True
    print("[%s] petals tree built: %d nodes | flutter amp=0.05 rate=0.7"
          % (pt_name, len(ptree.nodes)))
    return ptree


def ensure_petal_object(tree):
    """Create/update FlowerBrooch_Petals: parented to the hero (identity local), petals tree
    attached, and the outline pass copied from the hero stack (same values)."""
    from mathutils import Matrix
    ob = bpy.data.objects.get(PETAL_OBJ_NAME)
    if ob is None:
        me = bpy.data.meshes.new(PETAL_OBJ_NAME)
        ob = bpy.data.objects.new(PETAL_OBJ_NAME, me)
        bpy.context.scene.collection.objects.link(ob)
        print("created petal object:", PETAL_OBJ_NAME)
    hero = bpy.data.objects.get(OBJ_NAME)
    if hero is not None and ob.parent is None:
        ob.parent = hero
        ob.matrix_parent_inverse = Matrix.Identity(4)
        ob.location = (0.0, 0.0, 0.0)
        ob.rotation_euler = (0.0, 0.0, 0.0)
        ob.scale = (1.0, 1.0, 1.0)
        print("petal object parented to", OBJ_NAME)
    mod = None
    for m in ob.modifiers:
        if m.type == 'NODES':
            mod = m
            break
    if mod is None:
        mod = ob.modifiers.new("GN_Petals", 'NODES')
    before = mod.node_group.name if mod.node_group else None
    mod.node_group = tree
    mod.show_viewport = True
    mod.show_render = True
    for item in tree.interface.items_tree:
        if getattr(item, "in_out", "") != "INPUT":
            continue
        val = item.default_value
        try:
            mod.properties.inputs[item.identifier]["value"] = val
        except Exception:
            try:
                mod[item.identifier] = val
            except Exception:
                pass
    print("petals modifier %r: node_group %s -> %s" % (mod.name, before, tree.name))
    # outline pass (same tree + same values as the hero's)
    hero_outline = None
    if hero is not None:
        for m in hero.modifiers:
            if m.type == 'NODES' and m.node_group and m.node_group.name == "Outline [GeoNodes]":
                hero_outline = m
                break
    if hero_outline is not None:
        om = ob.modifiers.get("Outline [GeoNodes]")
        if om is None:
            om = ob.modifiers.new("Outline [GeoNodes]", 'NODES')
        om.node_group = hero_outline.node_group
        om.show_viewport = hero_outline.show_viewport
        om.show_render = hero_outline.show_render
        try:
            for item in hero_outline.node_group.interface.items_tree:
                if getattr(item, "in_out", "") != "INPUT":
                    continue
                try:
                    v = hero_outline.properties.inputs[item.identifier]["value"]
                    om.properties.inputs[item.identifier]["value"] = v
                except Exception:
                    pass
            print("petal outline pass mirrored (values copied from the hero)")
        except Exception as exc:
            print("  warn: outline copy (%r)" % (exc,))
    return ob


def ensure_sparkle_object():
    """Create/update FlowerBrooch_Sparkles: parented to the hero (identity local), sparkle tree
    attached (with twinkle). Stays on its own object so the body stays fully cached."""
    from mathutils import Matrix
    tree = bpy.data.node_groups.get("GN_Brooch_Sparkles_v7")
    if tree is None:
        return None
    ob = bpy.data.objects.get("FlowerBrooch_Sparkles")
    if ob is None:
        me = bpy.data.meshes.new("FlowerBrooch_Sparkles")
        ob = bpy.data.objects.new("FlowerBrooch_Sparkles", me)
        bpy.context.scene.collection.objects.link(ob)
        print("created sparkle object: FlowerBrooch_Sparkles")
    hero = bpy.data.objects.get(OBJ_NAME)
    if hero is not None and ob.parent is None:
        ob.parent = hero
        ob.matrix_parent_inverse = Matrix.Identity(4)
        ob.location = (0.0, 0.0, 0.0)
        print("sparkle object parented to", OBJ_NAME)
    mod = ob.modifiers.get("GN_Sparkles")
    if mod is None:
        mod = ob.modifiers.new("GN_Sparkles", 'NODES')
    mod.node_group = tree
    mod.show_viewport = True
    mod.show_render = True
    for item in tree.interface.items_tree:
        if getattr(item, "in_out", "") != "INPUT":
            continue
        try:
            val = item.default_value
        except AttributeError:
            continue  # geometry sockets have no default_value
        try:
            mod.properties.inputs[item.identifier]["value"] = val
        except Exception:
            try:
                mod[item.identifier] = val
            except Exception:
                pass
    print("sparkle modifier GN_Sparkles attached to FlowerBrooch_Sparkles")
    return ob


# ---------------------------------------------------------------- main -------
print("=== gen_flower_brooch_v7 (final refined: cast SDF finish + sampled seating + hardware v7) ===")
print("file:", bpy.data.filepath)
try:
    scn = bpy.context.scene
    scn.unit_settings.system = 'METRIC'
    scn.unit_settings.scale_length = 0.1
    scn.unit_settings.length_unit = 'MILLIMETERS'
    print("scene units: 1 unit = 10 cm (100 mm), display mm")
except Exception as exc:
    print("unit setup warn:", repr(exc))

try:
    bg = load_genome_module()
except Exception:
    print("GENOME MODULE RAISED:\n" + traceback.format_exc())
    bg = None

if bg is not None:
    ob = bpy.data.objects.get(OBJ_NAME)
    if ob is None:
        print("ERROR: object %r not found" % OBJ_NAME)
    else:
        try:
            backup()
        except Exception:
            print("BACKUP RAISED:\n" + traceback.format_exc())

        stats = {}
        frame0 = bpy.context.scene.frame_current
        try:
            bpy.context.scene.frame_set(1)
            print("frame pinned to 1 for measurement (scene was on frame %s; restored at end)" % frame0)
        except Exception as exc:
            print("frame pin warn:", repr(exc))
        for gid, tname in GENOMES:
            try:
                r = bg.resolve_genome(gid)
                tr = r["traits"]
                target = float((tr.get("size") or {}).get("real_mm", 0.0) or 0.0)
                print("--- genome %s (target %s mm) ---" % (gid, target or "-"))
                # pass A: nominal measured on the GOLD SLOT only (raw GN output, cast off)
                build(gid, tname, bg, real_scale=1.0, cast_default=False)
                attach(ob, bpy.data.node_groups[tname])
                d_tree = build_dangles(gid, dangle_tree_name(tname), bg, real_scale=1.0)
                d_ob = ensure_dangle_object(d_tree) if d_tree is not None else None
                p_tree = build_petals(gid, tname, bg, real_scale=1.0)
                p_ob = ensure_petal_object(p_tree) if p_tree is not None else None
                sv = gn_only(ob)
                m_a = measure(ob)
                restore_mods(sv)
                m_da = None
                if d_ob is not None:
                    sv_d = gn_only(d_ob)
                    m_da = measure(d_ob)
                    restore_mods(sv_d)
                gd = union_gold_dims(m_a, m_da)
                if gd:
                    nominal = max(gd[0], gd[1])
                elif m_a["mm"]:
                    nominal = max(m_a["mm"][0], m_a["mm"][1])
                    print("  warn: gold slot not found; nominal from full mesh")
                else:
                    nominal = 0.0
                S = (target / nominal) if (target and nominal) else 1.0
                print("[%s] pass A gold nominal %.2f mm -> Real Scale %.5f" % (tname, nominal, S))
                # pass B: real-scale build — CAST OFF by default (the SDF weld is a voxel remesh:
                # clean edge flow matters more than the cast look; cast is an opt-in finishing pass)
                build(gid, tname, bg, real_scale=S, cast_default=False)
                attach(ob, bpy.data.node_groups[tname])
                ensure_bevel(ob)
                d_tree = build_dangles(gid, dangle_tree_name(tname), bg, real_scale=S)
                d_ob = ensure_dangle_object(d_tree) if d_tree is not None else None
                p_tree = build_petals(gid, tname, bg, real_scale=S)
                p_ob = ensure_petal_object(p_tree) if p_tree is not None else None
                sv = gn_only(ob)
                m_b = measure(ob)
                restore_mods(sv)
                m_db = None
                if d_ob is not None:
                    sv_d = gn_only(d_ob)
                    m_db = measure(d_ob)
                    restore_mods(sv_d)
                gd_b = union_gold_dims(m_b, m_db)
                if target and gd_b:
                    err = abs(max(gd_b[0], gd_b[1]) - target) / max(target, 1e-9)
                    print("  gold dims %s mm (target %.1f, err %.1f%%)" % (
                        gd_b, target, err * 100.0))
                    # v10: re-solve iteration — the cast weld erodes the thin margin, so re-solve S
                    # from the CAST-ON measurement and rebuild (up to 2 times, until err <= 2%).
                    if err > 0.02:
                        S_used = S
                        for rsi in range(2):
                            measured = max(gd_b[0], gd_b[1]) if gd_b else 0.0
                            if measured <= 0.0:
                                break
                            S_used = S_used * (target / measured)
                            print("  re-solve %d: err %.1f%% -> Real Scale %.5f" % (
                                rsi + 1, err * 100.0, S_used))
                            build(gid, tname, bg, real_scale=S_used, cast_default=False)
                            attach(ob, bpy.data.node_groups[tname])
                            ensure_bevel(ob)
                            d_tree = build_dangles(gid, dangle_tree_name(tname), bg, real_scale=S_used)
                            d_ob = ensure_dangle_object(d_tree) if d_tree is not None else None
                            p_tree = build_petals(gid, tname, bg, real_scale=S_used)
                            p_ob = ensure_petal_object(p_tree) if p_tree is not None else None
                            sv = gn_only(ob)
                            m_b = measure(ob)
                            restore_mods(sv)
                            m_db = None
                            if d_ob is not None:
                                sv_d = gn_only(d_ob)
                                m_db = measure(d_ob)
                                restore_mods(sv_d)
                            gd_b = union_gold_dims(m_b, m_db)
                            if not gd_b:
                                break
                            err = abs(max(gd_b[0], gd_b[1]) - target) / max(target, 1e-9)
                            print("  gold dims %s mm (target %.1f, err %.1f%%) [re-solve %d]" % (
                                gd_b, target, err * 100.0, rsi + 1))
                            if err <= 0.02:
                                break
                        S = S_used
                stats[tname] = {
                    "genome": gid, "target_mm": target, "S": S,
                    "nominal_mm": round(nominal, 2), "final_mm": m_b["mm"],
                    "per_mat": m_b["per_mat"], "nv": m_b["nv"], "nf": m_b["nf"],
                    "pin_mm": None,
                }
                # pin dimensions (real mm, post scale)
                hw = tr["hardware"]
                plate_r = float(hw["plate_radius"])
                span = (2.0 * (plate_r - (0.04 / max(S, 1e-9)))) + (0.035 / max(S, 1e-9))
                stats[tname]["pin_mm"] = {
                    "hinge_to_catch_mm": round((2.0 * (plate_r - 0.04 / S)) * S * 100.0, 2),
                    "pin_len_mm": round(span * S * 100.0, 2)}
                print("[%s] final: verts=%d polys=%d dims(mm)=%s" % (
                    tname, m_b["nv"], m_b["nf"], m_b["mm"]))
            except Exception:
                print("BUILD %s RAISED:\n%s" % (gid, traceback.format_exc()))

        # land on hero
        try:
            hero_tree = (bpy.data.node_groups.get("GN_FlowerBrooch_v10")
                         or bpy.data.node_groups.get("GN_FlowerBrooch_gala_tide_v10")
                         or bpy.data.node_groups.get("GN_FlowerBrooch_v8"))
            if hero_tree is not None:
                used = hero_tree.name
                attach(ob, hero_tree)
                ensure_bevel(ob)
                sv = gn_only(ob)
                m_f = measure(ob)
                restore_mods(sv)
                if not m_f["nv"]:
                    print("v8 hero EMPTY -> falling back to gala tide then v7")
                    v5t = (bpy.data.node_groups.get("GN_FlowerBrooch_gala_tide_v10")
                           or bpy.data.node_groups.get("GN_FlowerBrooch_v8"))
                    if v5t is not None:
                        attach(ob, v5t)
                        used = v5t.name
                    sv = gn_only(ob)
                    m_f = measure(ob)
                    restore_mods(sv)
                print("FINAL attach -> %s: verts=%d polys=%d dims(mm)=%s per_mat=%s" % (
                    used, m_f["nv"], m_f["nf"], m_f["mm"], m_f["per_mat"]))
                if used in stats:
                    stats[used]["final_mm"] = m_f["mm"]
                    stats[used]["per_mat"] = m_f["per_mat"]
                # land the hero dangles on their own object
                hero_s = float(stats.get(used, {}).get("S", 1.0) or 1.0)
                hero_gid = stats.get(used, {}).get("genome", "melodia_brooch_v1")
                d_tree = build_dangles(hero_gid, dangle_tree_name(used), bg, real_scale=hero_s)
                d_ob = ensure_dangle_object(d_tree) if d_tree is not None else None
                p_tree = build_petals(hero_gid, used, bg, real_scale=hero_s)
                p_ob = ensure_petal_object(p_tree) if p_tree is not None else None
                # land the hero sparkles on their own object (twinkle restored)
                ensure_sparkle_object()
                if d_ob is not None:
                    sv_d = gn_only(d_ob)
                    m_d = measure(d_ob)
                    restore_mods(sv_d)
                    print("FINAL dangles -> %s: verts=%d polys=%d dims(mm)=%s per_mat=%s" % (
                        d_ob.name, m_d["nv"], m_d["nf"], m_d["mm"], m_d["per_mat"]))
                else:
                    print("FINAL dangles: none for genome %s" % hero_gid)
        except Exception:
            print("FINAL ATTACH RAISED:\n" + traceback.format_exc())

        # --- live-motion discipline: the body object must stay time-free, or every frame change
        # re-cooks its whole stack (measured 8-22 s/frame vs 0.33 s once time-free). The bloom is a
        # build-time option now; the Outline tree must not carry SceneTime nodes.
        # The sparkle tree is on its OWN object (FlowerBrooch_Sparkles), so its twinkle is allowed. ---
        try:
            for tname in ("Outline [GeoNodes]",):
                t = bpy.data.node_groups.get(tname)
                if t is None:
                    continue
                for n in [n for n in t.nodes if n.bl_idname == 'GeometryNodeInputSceneTime']:
                    nm = n.name
                    t.nodes.remove(n)
                    print("live discipline: removed SceneTime %r from %r" % (nm, tname))
            hero_ob = bpy.data.objects.get(OBJ_NAME)
            if hero_ob is not None:
                for m in hero_ob.modifiers:
                    if (m.type == 'NODES' and m.node_group is not None
                            and m.node_group.name == "Outline [GeoNodes]"):
                        for it in m.node_group.interface.items_tree:
                            if getattr(it, "in_out", "") == "INPUT" and it.name == "Freeze Frames":
                                m.properties.inputs[it.identifier]["value"] = 1
                                print("live discipline: outline Freeze Frames -> 1 (divide guard)")
                for m in [m for m in hero_ob.modifiers
                          if m.type == 'NODES' and m.node_group is None]:
                    nm = m.name
                    hero_ob.modifiers.remove(m)
                    print("live discipline: removed empty modifier %r" % nm)
                # remove the old sparkle modifier from the hero (it's now on its own object)
                sparkle_mod = hero_ob.modifiers.get("GN_Sparkles")
                if sparkle_mod is not None:
                    hero_ob.modifiers.remove(sparkle_mod)
                    print("live discipline: removed GN_Sparkles from hero (now on own object)")
        except Exception as exc:
            print("live discipline warn:", repr(exc))

        print("--- summary (real mm) ---")
        lines = []
        for name, st in stats.items():
            line = ("%s target=%smm S=%.4f nominal=%.2fmm final=%smm per_mat=%s pin=%s" % (
                name, st["target_mm"], st["S"], st["nominal_mm"], st["final_mm"],
                st["per_mat"], st["pin_mm"]))
            print("  " + line)
            lines.append(line)
        try:
            with open(REPORT_V10, "w", encoding="utf-8") as fh:
                fh.write("gen_flower_brooch_v10 BUILD_REPORT_V10  (all dims real mm)\n")
                fh.write("scene units: 1 unit = 10 cm (100 mm), display mm\n\n")
                for ln in lines:
                    fh.write(ln + "\n")
            print("wrote BUILD_REPORT_V10.txt")
        except Exception as exc:
            print("report write failed (%r)" % (exc,))
        print("trees in file:", sorted(
            g.name for g in bpy.data.node_groups
            if g.name.startswith("GN_FlowerBrooch") or g.name.startswith("GN_BroochDangles")))
        try:
            bpy.context.scene.frame_set(frame0)
            print("frame restored to %s" % frame0)
        except Exception as exc:
            print("frame restore warn:", repr(exc))

try:
    import os as _os
    import shutil
    import time as _time
    _bdir = r"P:/MelodiaMelusinaV2-Laptop/Saved/Accessories/brooch_lab/backups"
    _os.makedirs(_bdir, exist_ok=True)
    _stamp = _time.strftime("%Y%m%d_%H%M%S")
    shutil.copy2(bpy.data.filepath, _os.path.join(_bdir, "FlowerBrooch_preV10run_%s.blend" % _stamp))
    print("backup written: preV10run_%s" % _stamp)
except Exception as _exc:
    print("backup warn:", repr(_exc)[:90])
try:
    bpy.ops.wm.save_mainfile()
    print("SAVED", bpy.data.filepath)
except Exception as _exc:
    print("save warn:", repr(_exc)[:90])
print("=== done ===")
