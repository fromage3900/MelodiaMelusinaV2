"""regalia_v5_build.py (derived from v4: same conforming paths)
 -- opens regalia_v3_final.blend (never saved over) and REBUILDS the circlet and tiara as
head-conforming pieces: band paths sampled on Melusina's skull (and, for the hair variant, on her water-hair surface),
offset outward, slim swept gold profile + rails, filigree loops projected ON the surface, a front-centre collet stone
(circlet) and a front-centre spire (tiara). Earrings/necklace untouched. Saves regalia_v4<tag>.blend (NEW file).
blender -b --factory-startup regalia_v3_final.blend --python regalia_v4_build.py -- --tag _it0"""
import bpy, bmesh, math, json, os, sys
from mathutils import Vector, Matrix
from mathutils.bvhtree import BVHTree
W = os.environ.get("REGV5_W", r"C:\EnvironmentPortfolio\_lookdev_work\regalia_v2")
A = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
def arg(k, d): return type(d)(A[A.index(k) + 1]) if k in A else d
TAG = arg("--tag", "")
OUTBLEND = os.path.join(W, "regalia_v5%s.blend" % TAG); RECEIPT = os.path.join(W, "regalia_v5%s_build_receipt.json" % TAG)
STAB = "--stability" in A
assert STAB or not os.path.exists(OUTBLEND), "refusing to overwrite " + OUTBLEND
P = dict(  # tunables (metres, HER scale; k_head = 2.23 vs a 150 mm adult head)
    c_h=arg("--c_h", 0.015), c_th=arg("--c_th", 0.0026), c_rail=arg("--c_rail", 0.0013), c_clear=arg("--c_clear", 0.003),
    c_front_above_brow=arg("--c_fab", 0.010), c_tilt=arg("--c_tilt", 0.075), c_stone=arg("--c_stone", 0.030),
    t_h=arg("--t_h", 0.012), t_z0=arg("--t_z0", 1.600), t_tilt=arg("--t_tilt", 22.0), t_span=arg("--t_span", 96.0), t_stone=arg("--t_stone", 0.032),
    loop_h=arg("--loop_h", 0.016), loop_w=arg("--loop_w", 0.012), loop_r=arg("--loop_r", 0.0011), hair_into=arg("--hair_into", 0.004), hair_lift=arg("--hair_lift", 0.003),
    pinch_dmax=arg("--pinch_dmax", 0.06), pinch_fall=arg("--pinch_fall", 0.7), fil_len=arg("--fil_len", 0.013), fil_wf=arg("--fil_wf", 0.55))
R = {"params": P, "notes": []}
O = bpy.data.objects; vl = bpy.context.view_layer
def mm(v): return round(v * 1000, 1)
def rnd(v): return [round(x, 4) for x in v]
GOLD = bpy.data.materials["V2_Gold"]; AQUA = bpy.data.materials["V2_Stone_Aquamarine_Dream"]
def put(ob, mat):
    ob.data.materials.clear(); ob.data.materials.append(mat)
    if ob.type == "MESH": ob.material_slots[0].link = "OBJECT"; ob.material_slots[0].material = mat

# ------------------------------------------------ 0) remove the v3 ring headpieces (in this new file only)
for cn in ("REG_circlet", "REG_tiara"):
    c = bpy.data.collections[cn]
    for o in list(c.objects): bpy.data.objects.remove(o)
    bpy.data.collections.remove(c)
PC = bpy.data.collections["STAGE_proxies"]
body = [o for o in PC.objects if o.get("mel3_role") == "body"][0]
hair = [o for o in PC.objects if str(o.get("mel3_role", "")).startswith("hair")]
brows = [o for o in PC.objects if o.get("mel3_role") == "brow"]

def bvh_of(objs):
    bm = bmesh.new()
    for o in objs:
        me = o.data.copy(); me.transform(o.matrix_world); bm.from_mesh(me); bpy.data.meshes.remove(me)
    t = BVHTree.FromBMesh(bm); bm.free(); return t
BV_SKIN = bvh_of([body]); BV_HAIR = bvh_of([body] + hair)
BP = [body.matrix_world @ v.co for v in body.data.vertices]
def section(z, tol=0.004):
    s = [p for p in BP if abs(p.z - z) < tol]
    return Vector(((min(p.x for p in s) + max(p.x for p in s)) / 2, (min(p.y for p in s) + max(p.y for p in s)) / 2, z))
brow_top = max((o.matrix_world @ v.co).z for o in brows for v in o.data.vertices)
top = max(p.z for p in BP)
ear = [p for p in BP if abs(p.x) > 0.175 and 1.45 < p.z < 1.70 and p.y > -0.25]
ear_top = max(p.z for p in ear) if ear else 1.60
AX = section(brow_top + 0.04)
if "--t_z0" not in A: P["t_z0"] = round(max(1.60, ear_top + 0.012), 4)
R["her"] = {"brow_top": round(brow_top, 4), "top": round(top, 4), "ear_top_z": round(ear_top, 4), "axis": rnd(AX)}

def ray_in(bv, origin_axis, d, far=0.6):
    """first hit coming IN from outside along -d toward origin_axis"""
    o = origin_axis + d * far
    hit = bv.ray_cast(o, -d, far * 1.2)
    return hit  # (loc, normal, index, dist)
def circ_smooth(vals, sig, closed=True):
    n = len(vals); out = []
    w = [math.exp(-0.5 * (k / sig) ** 2) for k in range(-3 * int(sig) - 1, 3 * int(sig) + 2)]
    ks = list(range(-3 * int(sig) - 1, 3 * int(sig) + 2))
    for i in range(n):
        acc = 0; ws = 0
        for k, ww in zip(ks, w):
            j = i + k
            if closed: j %= n
            elif j < 0 or j >= n: continue
            acc = acc + vals[j] * ww; ws += ww
        out.append(acc / ws)
    return out
def median_f(vals, win, closed=True):
    n = len(vals); out = []
    for i in range(n):
        s = []
        for k in range(-win, win + 1):
            j = i + k
            if closed: j %= n
            elif j < 0 or j >= n: continue
            s.append(vals[j])
        s.sort(); out.append(s[len(s) // 2])
    return out

# ------------------------------------------------ path samplers
def circlet_path(bv, hair_mode, N=480):
    zf = brow_top + P["c_front_above_brow"] + P["c_h"] * 0.5
    D = P["c_tilt"]
    # keep the side (theta=90) band bottom above the ear tops
    zside = zf - D * 0.5
    if zside - P["c_h"] * 0.5 < ear_top + 0.004:
        D = 2 * (zf - (ear_top + 0.004 + P["c_h"] * 0.5)); R["notes"].append("circlet tilt reduced to clear ear tops: D=%.3f" % D)
    rs, nz, dirs, zs = [], [], [], []
    for i in range(N):
        th = 2 * math.pi * i / N
        d = Vector((math.sin(th), -math.cos(th), 0))
        z = zf - D * (1 - math.cos(th)) * 0.5
        a = Vector((AX.x, AX.y, z)); h = ray_in(bv, a, d)
        if h[0] is None: rs.append(None); nz.append(Vector((0, 0, 0))); dirs.append(d); zs.append(z); continue
        rs.append((h[0] - a).length); nz.append(h[1]); dirs.append(d); zs.append(z)
    good = [r for r in rs if r is not None]; med = sorted(good)[len(good) // 2]
    rs = [r if r is not None else med for r in rs]
    r1 = circ_smooth(rs, 3.0); r1 = [max(a, b) for a, b in zip(r1, rs)]; r1 = circ_smooth(r1, 2.0)
    r1 = [max(a, b) + P["c_clear"] + (P["hair_lift"] if hair_mode else 0.0) for a, b in zip(r1, rs)]
    pts = [Vector((AX.x, AX.y, zs[i])) + dirs[i] * r1[i] for i in range(N)]
    # outward normal: radial blended with the smoothed surface normal (follows the forehead slope)
    nrm = []
    for i in range(N):
        s = nz[i] if nz[i].length > 0.1 else dirs[i]
        nrm.append((dirs[i] * 0.45 + s.normalized() * 0.55).normalized())
    nx = circ_smooth([n.x for n in nrm], 4); ny = circ_smooth([n.y for n in nrm], 4); nzz = circ_smooth([n.z for n in nrm], 4)
    nrm = [Vector((a, b, c)).normalized() for a, b, c in zip(nx, ny, nzz)]
    return pts, nrm, True

def tiara_path(bv, hair_mode, N=320):
    al = math.radians(P["t_tilt"]); span = math.radians(P["t_span"])
    C = Vector((AX.x, AX.y + 0.02, P["t_z0"]))
    rs, nz, dirs = [], [], []
    for i in range(N):
        ph = -span + 2 * span * i / (N - 1)
        d = Vector((math.sin(ph), -math.sin(al) * math.cos(ph), math.cos(al) * math.cos(ph))).normalized()
        h = ray_in(bv, C, d)
        rs.append((h[0] - C).length if h[0] else None); nz.append(h[1] if h[0] else d); dirs.append(d)
    good = [r for r in rs if r is not None]; med = sorted(good)[len(good) // 2]; rs = [r if r is not None else med for r in rs]
    r1 = circ_smooth(rs, 3.0, False); r1 = [max(a, b) for a, b in zip(r1, rs)]; r1 = circ_smooth(r1, 2.0, False)
    r1 = [max(a, b) + P["c_clear"] + (P["hair_lift"] if hair_mode else 0.0) for a, b in zip(r1, rs)]
    pts = [C + dirs[i] * r1[i] for i in range(N)]
    nrm = [(dirs[i] * 0.4 + nz[i].normalized() * 0.6).normalized() for i in range(N)]
    nx = circ_smooth([n.x for n in nrm], 3, False); ny = circ_smooth([n.y for n in nrm], 3, False); nzz = circ_smooth([n.z for n in nrm], 3, False)
    nrm = [Vector((a, b, c)).normalized() for a, b, c in zip(nx, ny, nzz)]
    return pts, nrm, False

# ------------------------------------------------ sweep
def frames(pts, nrm, closed):
    n = len(pts); T, U, Nn = [], [], []
    for i in range(n):
        a = pts[(i - 1) % n] if (closed or i > 0) else pts[i]; b = pts[(i + 1) % n] if (closed or i < n - 1) else pts[i]
        t = (b - a).normalized(); nn = (nrm[i] - t * nrm[i].dot(t)).normalized(); u = t.cross(nn)
        T.append(t); U.append(u); Nn.append(nn)
    return T, U, Nn
def sweep(name, col, pts, T, U, Nn, prof, closed, off_n=0.0, off_u=0.0, cap=True):
    """prof: list of (a along N, b along U) closed polygon"""
    bm = bmesh.new(); rows = []
    for i in range(len(pts)):
        rows.append([bm.verts.new(pts[i] + Nn[i] * (a + off_n) + U[i] * (b + off_u)) for a, b in prof])
    m = len(prof); n = len(rows)
    for i in range(n if closed else n - 1):
        r0, r1 = rows[i], rows[(i + 1) % n]
        for j in range(m):
            bm.faces.new((r0[j], r1[j], r1[(j + 1) % m], r0[(j + 1) % m]))
    if not closed and cap:
        bm.faces.new(list(reversed(rows[0]))); bm.faces.new(rows[-1])
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    me = bpy.data.meshes.new(name); bm.to_mesh(me); bm.free()
    for p in me.polygons: p.use_smooth = True
    ob = bpy.data.objects.new(name, me); col.objects.link(ob); put(ob, GOLD); return ob
def band_profile(h, th, n=20):
    pr = []
    for k in range(n):
        t = 2 * math.pi * k / n; c, s = math.cos(t), math.sin(t)
        a = th * 0.5 + th * 0.5 * math.copysign(abs(c) ** 0.55, c); b = h * 0.5 * math.copysign(abs(s) ** 0.35, s)
        pr.append((a, b))
    return pr
def circle_profile(r, n=10): return [(r * math.cos(2 * math.pi * k / n), r * math.sin(2 * math.pi * k / n)) for k in range(n)]

def curve_obj(name, col, pts, r, cyclic=False, r1=None):
    cu = bpy.data.curves.new(name, "CURVE"); cu.dimensions = "3D"; cu.bevel_depth = 1.0; cu.bevel_resolution = 4; cu.resolution_u = 10
    sp = cu.splines.new("NURBS"); sp.points.add(len(pts) - 1); sp.order_u = min(4, len(pts)); sp.use_cyclic_u = cyclic; sp.use_endpoint_u = not cyclic
    for i, (p, q) in enumerate(zip(sp.points, pts)):
        t = i / max(1, len(pts) - 1); p.co = (q.x, q.y, q.z, 1); p.radius = r if r1 is None else r + (r1 - r) * t
    o = bpy.data.objects.new(name, cu); col.objects.link(o); cu.materials.append(GOLD); return o

def on_surface(bv, q, off):
    loc, nrm, idx, d = bv.find_nearest(q)
    if nrm is None: return q
    if (q - loc).dot(nrm) < 0 and nrm.dot(q - AX) < 0: nrm = -nrm
    return loc + nrm * off

def loops_along(name, col, bv, pts, T, U, Nn, idxs, side_sign, band_h, closed=True):
    n = len(pts); ds = sum((pts[(i + 1) % n] - pts[i]).length for i in range(n - 1)) / (n - 1)
    def at(f):
        if closed: f = f % n
        else: f = max(0.0, min(n - 1.0001, f))
        a = int(math.floor(f)); b = (a + 1) % n; t = f - a
        return pts[a].lerp(pts[b], t), Nn[a].lerp(Nn[b], t).normalized(), U[a].lerp(U[b], t).normalized()
    made = 0; off = P["c_th"] + P["loop_r"] * 0.85; L = P["fil_len"]; Wd = band_h * P["fil_wf"]
    for i in idxs:
        for s_ in (1, -1):
            lp = []
            for k in range(18):
                t = 2 * math.pi * k / 18
                y = (1 - math.cos(t)) * 0.5 * L                                        # along the band
                x = math.sin(t) * Wd * 0.5 * (0.30 + 0.70 * (1 - math.cos(t)) * 0.5)   # across the band
                p, nn, uu = at(i + s_ * y / ds)
                lp.append(p + nn * off + uu * x)
            curve_obj("%s_fil_%03d_%d" % (name, i, s_), col, lp, P["loop_r"], cyclic=True)
        made += 1
        p, nn, uu = at(i)
        b = bmesh.new(); bmesh.ops.create_uvsphere(b, u_segments=16, v_segments=8, radius=P["loop_r"] * 2.0)
        bmesh.ops.translate(b, vec=p + nn * (P["c_th"] + P["loop_r"] * 0.8), verts=b.verts)
        me = bpy.data.meshes.new(name + "_bead"); b.to_mesh(me); b.free()
        for pp in me.polygons: pp.use_smooth = True
        ob = bpy.data.objects.new("%s_bead_%03d" % (name, i), me); col.objects.link(ob); put(ob, GOLD)
    return made

# ------------------------------------------------ gems + settings (from the v2b/v2d builds)
def gem_bm(length, width, kind="pear", n=16, table=0.56, crown=0.16, pav=0.46, girdle=0.02):
    bm = bmesh.new()
    def outline(t):
        a = 2 * math.pi * t; x, y = math.cos(a), math.sin(a)
        if kind == "pear": k = 0.5 * (1 + y); x *= (1 - 0.55 * k ** 2.2)
        return x * width * 0.5, y * length * 0.5
    size = max(length, width); zt = crown * size; zg = girdle * size * 0.5; zc = -pav * size
    rt = [bm.verts.new((*outline(i / n), zg)) for i in range(n)]; rb = [bm.verts.new((*outline(i / n), -zg)) for i in range(n)]
    tab = [bm.verts.new((outline((i + 0.5) / n)[0] * table, outline((i + 0.5) / n)[1] * table, zt)) for i in range(n)]
    for i in range(n):
        j = (i + 1) % n
        bm.faces.new((rb[i], rb[j], rt[j], rt[i])); bm.faces.new((rt[i], rt[j], tab[i])); bm.faces.new((tab[i], rt[j], tab[j]))
    bm.faces.new(tab)
    cul = bm.verts.new((0, 0, zc)); mid = [bm.verts.new((outline(i / n)[0] * 0.45, outline(i / n)[1] * 0.45, zc * 0.55)) for i in range(n)]
    for i in range(n):
        j = (i + 1) % n; bm.faces.new((rb[j], rb[i], mid[i], mid[j])); bm.faces.new((mid[j], mid[i], cul))
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces); return bm, outline, zc
def frame(z, yhint):
    z = z.normalized(); y = (yhint - z * yhint.dot(z)).normalized(); x = y.cross(z)
    return Matrix((x, y, z)).transposed().to_4x4()
def mesh_obj(name, col, bm, mat, smooth=False):
    me = bpy.data.meshes.new(name); bm.to_mesh(me); bm.free()
    for p in me.polygons: p.use_smooth = smooth
    ob = bpy.data.objects.new(name, me); col.objects.link(ob); put(ob, mat); return ob
def outline_ring(name, col, outline_fn, M, scale, rt, z=0.0, n=96):
    Pp = [Vector((*outline_fn(i / n), 0)) * scale for i in range(n)]
    bm = bmesh.new(); rows = []; ring = 10
    for i in range(n):
        tng = (Pp[(i + 1) % n] - Pp[i - 1]).normalized(); nr = tng.cross(Vector((0, 0, 1))).normalized()
        if nr.dot(Pp[i]) < 0: nr = -nr
        rows.append([bm.verts.new(M @ (Pp[i] + Vector((0, 0, z)) + (nr * math.cos(2 * math.pi * j / ring) + Vector((0, 0, 1)) * math.sin(2 * math.pi * j / ring) * 1.2) * rt)) for j in range(ring)])
    for i in range(n):
        for j in range(ring):
            bm.faces.new((rows[i][j], rows[(i + 1) % n][j], rows[(i + 1) % n][(j + 1) % ring], rows[i][(j + 1) % ring]))
    return mesh_obj(name, col, bm, GOLD, True)
def collet_cup(name, col, outline_fn, M, depth, n=64):
    """closed-back cup from the girdle (scale 1.04) down to the band face (scale 0.8)"""
    bm = bmesh.new()
    top = [bm.verts.new(M @ Vector((*[c * 1.05 for c in outline_fn(i / n)], 0.0003))) for i in range(n)]
    bot = [bm.verts.new(M @ Vector((*[c * 0.80 for c in outline_fn(i / n)], -depth))) for i in range(n)]
    for i in range(n):
        j = (i + 1) % n; bm.faces.new((top[i], top[j], bot[j], bot[i]))
    bm.faces.new(bot)
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces); return mesh_obj(name, col, bm, GOLD, True)

# ===================================================================== v5: fixed-topology motif band
import hashlib
from mathutils.kdtree import KDTree
import mathutils.geometry as MG
_MOT = os.environ.get("REGV5_MOTIF", os.path.join(os.path.dirname(os.path.abspath(__file__)) if "__file__" in dir() else W, "motif2d.py"))
MOT = {}; exec(open(_MOT).read(), MOT)
L_NOM_C, L_NOM_T = 1240.0, 720.0
H_NOM_C, H_NOM_T = 15.0, 12.0
N_ROWS_C, N_ROWS_T = 300, 180
PLATE_A = 1.8
PROF_TOP = [(1.8, 0.0), (2.7, 0.55), (3.05, 1.4), (2.6, 2.35), (1.4, 2.8), (0.3, 2.45), (0.05, 1.8)]
N_BACK = 4
SUBSURF_RENDER = 1
R["v5"] = {"counts": {}, "checks": {}}

class PathMap:
    """arc-length parametrisation of a v4 path; Catmull-Rom positions, nlerp frames"""
    def __init__(self, pts, T, U, Nn, closed, s0_index=None):
        self.p, self.T, self.U, self.N, self.closed = pts, T, U, Nn, closed
        n = len(pts); self.n = n; L = [0.0]
        for i in range(1, n + (1 if closed else 0)): L.append(L[-1] + (pts[i % n] - pts[i - 1]).length)
        self.cum = L; self.L = L[-1]
        self.s_mid = 0.0 if closed else self.L * 0.5
    def _seg(self, s):
        if self.closed: s = s % self.L
        else: s = max(0.0, min(self.L - 1e-9, s))
        lo, hi = 0, len(self.cum) - 1
        while hi - lo > 1:
            m = (lo + hi) // 2
            if self.cum[m] <= s: lo = m
            else: hi = m
        t = (s - self.cum[lo]) / max(1e-12, self.cum[lo + 1] - self.cum[lo]); return lo, t
    def at(self, s_rel):
        s = s_rel + self.s_mid; i, t = self._seg(s); n = self.n
        def P(k):
            if self.closed: return self.p[k % n]
            return self.p[max(0, min(n - 1, k))]
        p0, p1, p2, p3 = P(i - 1), P(i), P(i + 1), P(i + 2)
        t2, t3 = t * t, t * t * t
        pos = 0.5 * ((2 * p1) + (-p0 + p2) * t + (2 * p0 - 5 * p1 + 4 * p2 - p3) * t2 + (-p0 + 3 * p1 - 3 * p2 + p3) * t3)
        j = (i + 1) % n if self.closed else min(n - 1, i + 1)
        T = self.T[i].lerp(self.T[j], t).normalized(); Nn = self.N[i].lerp(self.N[j], t).normalized()
        Nn = (Nn - T * Nn.dot(T)).normalized(); U = T.cross(Nn)
        if U.dot(self.U[i]) < 0: U = -U
        return pos, T, U, Nn

def build_motif_band(name, col, pm, closed, L_nom, h_nom, rim, n_rows, layout, ut, ub, h_world, conform_clear, bv_skin, peak_base=None):
    """ALL topology is decided here in nominal motif space (independent of fit); positions are mapped last."""
    ks = pm.L * 1000.0 / L_nom; ku = h_world * 1000.0 / h_nom; rs = rim / 2.8
    V = []          # (s_nom, u_nom, a_mm)
    F = []          # faces as lists of V indices
    def nv(s, u, a): V.append((s, u, a)); return len(V) - 1
    # ---- band rows (open profile: plate top edge -> top rim -> back -> bottom rim -> plate bottom edge)
    rows = []
    srow = [(-L_nom / 2 + L_nom * i / n_rows) if closed else (-L_nom / 2 + L_nom * i / (n_rows - 1)) for i in range(n_rows)]
    for s in srow:
        top, bot = ut(s), ub(s); r = []
        for a, db in PROF_TOP: r.append(nv(s, top + db * rs, a))
        for k in range(1, N_BACK + 1):
            u0, u1 = top + 1.8 * rs, bot - 1.8 * rs; r.append(nv(s, u0 + (u1 - u0) * k / (N_BACK + 1), 0.05))
        for a, db in reversed(PROF_TOP): r.append(nv(s, bot - db * rs, a))
        rows.append(r)
    m = len(rows[0])
    for i in range(n_rows if closed else n_rows - 1):
        r0, r1 = rows[i], rows[(i + 1) % n_rows]
        for j in range(m - 1): F.append([r0[j], r1[j], r1[j + 1], r0[j + 1]])
    if not closed:
        F.append(list(rows[0])); F.append(list(reversed(rows[-1])))
    # ---- motif elements: rows of verts; outline verts go to the CDT
    polys = []      # footprint polygons (lists of V indices), CCW
    def area2(ids): return sum(V[ids[k]][0] * V[ids[(k + 1) % len(ids)]][1] - V[ids[(k + 1) % len(ids)]][0] * V[ids[k]][1] for k in range(len(ids)))
    def ccw(ids): return ids if area2(ids) > 0 else list(reversed(ids))
    OFF = [(1.0, 0.0), (0.55, 0.835), (0.0, 1.0), (-0.55, 0.835), (-1.0, 0.0)]
    for e in layout:
        if e["kind"] == "bead":
            c, rr, hh = e["c"], e["r"], e["h"]; rings = []
            for fr, fz, cnt in ((1.0, 0.0, 16), (0.62, 0.785, 16), (0.3, 0.954, 16)):
                rings.append([nv(c[0] + rr * fr * math.cos(2 * math.pi * k / cnt), c[1] + rr * fr * math.sin(2 * math.pi * k / cnt), PLATE_A + hh * fz) for k in range(cnt)])
            apex = nv(c[0], c[1], PLATE_A + hh)
            for a_, b_ in zip(rings[:-1], rings[1:]):
                for k in range(16): F.append([a_[k], a_[(k + 1) % 16], b_[(k + 1) % 16], b_[k]])
            for k in range(16): F.append([rings[-1][k], rings[-1][(k + 1) % 16], apex])
            polys.append(ccw(rings[0])); continue
        P2 = e["pts"]; n = len(P2); hw = e["w"] / 2; hh = e["h"]; cl = e["closed"]
        tn = []
        for i in range(n):
            a_ = P2[i - 1] if (cl or i > 0) else P2[i]; b_ = P2[(i + 1) % n] if (cl or i < n - 1) else P2[i]
            tx, ty = b_[0] - a_[0], b_[1] - a_[1]; l = math.hypot(tx, ty) or 1.0; tn.append((tx / l, ty / l, -ty / l, tx / l))
        R5 = [[nv(P2[i][0] + tn[i][2] * hw * o, P2[i][1] + tn[i][3] * hw * o, PLATE_A + hh * z) for (o, z) in OFF] for i in range(n)]
        for i in range(n if cl else n - 1):
            a_, b_ = R5[i], R5[(i + 1) % n]
            for j in range(4): F.append([a_[j], b_[j], b_[j + 1], a_[j + 1]])
        if cl:
            polys.append(ccw([r[0] for r in R5])); polys.append(ccw([r[4] for r in R5]))
        else:
            caps = []
            for (i, sgn) in ((n - 1, 1.0), (0, -1.0)):
                c = P2[i]; tx, ty, nx, ny = tn[i]; outl, mid = [], []
                for phi in (45, 90, 135):
                    ph = math.radians(phi)
                    # end cap: from left(+n) through front(+t) to right(-n); start cap: from right(-n) through back(-t) to left(+n)
                    dx = (math.cos(ph) * nx + math.sin(ph) * tx) if sgn > 0 else (-math.cos(ph) * nx - math.sin(ph) * tx)
                    dy = (math.cos(ph) * ny + math.sin(ph) * ty) if sgn > 0 else (-math.cos(ph) * ny - math.sin(ph) * ty)
                    outl.append(nv(c[0] + dx * hw, c[1] + dy * hw, PLATE_A))
                    mid.append(nv(c[0] + dx * hw * 0.55, c[1] + dy * hw * 0.55, PLATE_A + hh * 0.835))
                r = R5[i]
                if sgn > 0: Lo, Lm, Cc, Rm, Ro = r[0], r[1], r[2], r[3], r[4]
                else: Lo, Lm, Cc, Rm, Ro = r[4], r[3], r[2], r[1], r[0]
                ring_o = [Lo] + outl + [Ro]; ring_m = [Lm] + mid + [Rm]
                for k in range(4): F.append([ring_o[k], ring_o[k + 1], ring_m[k + 1], ring_m[k]])
                for k in range(4): F.append([ring_m[k], ring_m[k + 1], Cc])
                caps.append(outl)
            poly = [r[0] for r in R5] + caps[0] + [r[4] for r in reversed(R5)] + caps[1]
            polys.append(ccw(poly))
    # ---- plate: CDT of the plate region with footprints as parity holes
    bot_e = [rows[i % n_rows][m - 1] for i in range(n_rows + (1 if closed else 0))]
    top_e = [rows[i % n_rows][0] for i in range(n_rows + (1 if closed else 0))]
    cin = []; cmap = []
    def add_in(vid, s_override=None):
        s, u, a = V[vid]; cin.append(Vector((s if s_override is None else s_override, u))); cmap.append(vid); return len(cin) - 1
    bl = [add_in(v, (L_nom / 2 if (closed and k == n_rows) else None)) for k, v in enumerate(bot_e)]
    tl = [add_in(v, (L_nom / 2 if (closed and k == n_rows) else None)) for k, v in enumerate(top_e)]
    plate_poly = bl + list(reversed(tl))
    faces_in = [plate_poly]
    for pl in polys: faces_in.append([add_in(v) for v in pl])
    vc, ed, fa, ov, oe, of = MG.delaunay_2d_cdt(cin, [], faces_in, 1, 1e-7)
    merged = sum(1 for o in ov if len(o) != 1); newv = sum(1 for o in ov if len(o) == 0)
    npl = 0
    for f, o in zip(fa, of):
        if 0 not in o: continue
        if (len(o) - 1) % 2: continue
        F.append([cmap[ov[k][0]] for k in f]); npl += 1
    # ---- map motif space -> world (positions only)
    world = []
    base_top = ut(L_nom / 2 * 0.999) if closed else ut(0.0)
    for (s, u, a) in V:
        p, T_, U_, N_ = pm.at(s * ks / 1000.0)
        q = p + U_ * (u * ku / 1000.0)
        if peak_base is not None and u > peak_base:
            w = min(1.0, (u - peak_base) / 6.0); w = w * w * (3 - 2 * w)
            hit = bv_skin.ray_cast(q + N_ * 0.06, -N_, 0.14)
            if hit[0] is not None:
                d = (hit[0] - q).dot(N_) + conform_clear
                q = q + N_ * (max(-0.012, min(0.004, d)) * w)
        world.append(q + N_ * (a / 1000.0))
    bm = bmesh.new(); bv_ = [bm.verts.new(x) for x in world]; bad = 0
    for f in F:
        try: bm.faces.new([bv_[k] for k in f])
        except ValueError: bad += 1
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    me = bpy.data.meshes.new(name); bm.to_mesh(me); bm.free()
    for pp in me.polygons: pp.use_smooth = True
    ob = bpy.data.objects.new(name, me); col.objects.link(ob); put(ob, GOLD)
    sub = ob.modifiers.new("render_subdiv", "SUBSURF"); sub.levels = 0; sub.render_levels = SUBSURF_RENDER
    info = {"verts": len(me.vertices), "faces": len(me.polygons), "tris": sum(len(p.vertices) - 2 for p in me.polygons),
            "quads": sum(1 for p in me.polygons if len(p.vertices) == 4), "plate_tris": npl, "cdt_merged": merged, "cdt_new_verts": newv, "face_build_fail": bad,
            "topo_hash": hashlib.sha1(json.dumps(F).encode()).hexdigest()[:16], "ks": round(ks, 4), "ku": round(ku, 4)}
    def mapper(s, u, a):
        p, T_, U_, N_ = pm.at(s * ks / 1000.0); q = p + U_ * (u * ku / 1000.0)
        if peak_base is not None and u > peak_base:
            w = min(1.0, (u - peak_base) / 6.0); w = w * w * (3 - 2 * w); hit = bv_skin.ray_cast(q + N_ * 0.06, -N_, 0.14)
            if hit[0] is not None: q = q + N_ * (max(-0.012, min(0.004, (hit[0] - q).dot(N_) + conform_clear)) * w)
        return q + N_ * (a / 1000.0)
    return ob, info, mapper, ks, ku

def mesh_checks(ob):
    bm = bmesh.new(); bm.from_mesh(ob.data)
    nm = sum(1 for e in bm.edges if not e.is_manifold); bd = sum(1 for e in bm.edges if e.is_boundary)
    za = sum(1 for f in bm.faces if f.calc_area() < 1e-12); loose = sum(1 for v in bm.verts if not v.link_faces)
    bm.faces.ensure_lookup_table()
    tree = BVHTree.FromBMesh(bm); pairs = tree.overlap(tree); si = 0
    for a, b in pairs:
        if a >= b: continue
        fa, fb = bm.faces[a], bm.faces[b]
        if set(v.index for v in fa.verts) & set(v.index for v in fb.verts): continue
        si += 1
    shells = 0; seen = set()
    for v in bm.verts:
        if v.index in seen: continue
        shells += 1; st = [v]; seen.add(v.index)
        while st:
            x = st.pop()
            for e in x.link_edges:
                y = e.other_vert(x)
                if y.index not in seen: seen.add(y.index); st.append(y)
    bm.free()
    return {"non_manifold_edges": nm, "boundary_edges": bd, "zero_area_faces": za, "loose_verts": loose, "self_intersect_pairs": si, "shells": shells}

def stone_on(name, col, mapper, s, u, sa_mm, sb_mm, ks, ku, pav=0.05, crown=0.15, lift_mm=0.15):
    L = 2 * sa_mm * ks / 1000.0; Wd = 2 * sb_mm * ku / 1000.0
    g, outl, zc = gem_bm(L, Wd, kind="oval", crown=crown, pav=pav, table=0.5)
    c = mapper(s, u, PLATE_A); nrm = (mapper(s + 0.5, u, PLATE_A) - mapper(s - 0.5, u, PLATE_A)).cross(mapper(s, u + 0.5, PLATE_A) - mapper(s, u - 0.5, PLATE_A)).normalized()
    ref = mapper(s, u, PLATE_A + 1.0) - c
    if nrm.dot(ref) < 0: nrm = -nrm
    tng = (mapper(s + 0.5, u, PLATE_A) - mapper(s - 0.5, u, PLATE_A)).normalized()
    M = Matrix.Translation(c + nrm * (-zc + lift_mm / 1000.0)) @ frame(nrm, tng)
    bmesh.ops.transform(g, matrix=M, verts=g.verts); return mesh_obj(name, col, g, AQUA), c, nrm

def build_circlet(var, bv, hair_mode):
    col = bpy.data.collections.new("REG_circlet_" + var); bpy.context.scene.collection.children.link(col)
    pts, nrm, closed = circlet_path(bv, hair_mode)
    T, U, Nn = frames(pts, nrm, closed)
    if U[0].z < 0: U = [-u for u in U]
    pm = PathMap(pts, T, U, Nn, True)
    E, ut, ub = MOT["circlet_layout"](L_NOM_C)
    clear = P["c_clear"] + (P["hair_lift"] if hair_mode else 0.0)
    ob, info, mapper, ks, ku = build_motif_band("circlet_%s_band" % var, col, pm, True, L_NOM_C, H_NOM_C, 2.8, N_ROWS_C, E, ut, ub, P["c_h"], clear, BV_SKIN, peak_base=4.7)
    st, c, n_ = stone_on("circlet_%s_stone" % var, col, mapper, 0.0, 9.5, 16.0, 12.0, ks, ku)
    ob["motifA_world"] = list(mapper(80.0, 0.0, PLATE_A)); ob["motifA_normal"] = list(pm.at(80.0 * ks / 1000)[3])
    info["checks"] = mesh_checks(ob); info["stone_centre"] = rnd(c); info["stone_normal"] = rnd(n_); info["axis_x"] = round(AX.x, 4)
    info["path_len_mm"] = round(pm.L * 1000, 1); info["stone_tris"] = sum(len(p.vertices) - 2 for p in st.data.polygons)
    info["export_tris_total"] = info["tris"] + info["stone_tris"]
    # per-path-sample band half heights (for the hair pinch), incl. the front peak
    htop, hbot = [], []
    for i in range(len(pts)):
        s_nom = (pm.cum[i] if pm.cum[i] <= pm.L / 2 else pm.cum[i] - pm.L) * 1000.0 / ks
        htop.append((ut(s_nom) + 2.8) * ku / 1000.0); hbot.append((-ub(s_nom) + 2.8) * ku / 1000.0)
    PATHS[("C", var)] = (pts, T, U, Nn, htop, hbot, True)
    R["v5"]["counts"]["circlet_" + var] = info
    return col

def build_tiara(var, bv, hair_mode):
    col = bpy.data.collections.new("REG_tiara_" + var); bpy.context.scene.collection.children.link(col)
    pts, nrm, closed = tiara_path(bv, hair_mode)
    T, U, Nn = frames(pts, nrm, closed)
    n = len(pts); mid = n // 2
    if U[mid].dot(Vector((0, -1, 0))) < 0: U = [-u for u in U]
    pm = PathMap(pts, T, U, Nn, False)
    E, ut, ub = MOT["tiara_layout"](L_NOM_T)
    clear = P["c_clear"] + (P["hair_lift"] if hair_mode else 0.0)
    ob, info, mapper, ks, ku = build_motif_band("tiara_%s_band" % var, col, pm, False, L_NOM_T, H_NOM_T, 2.24, N_ROWS_T, E, ut, ub, P["t_h"], clear, BV_SKIN, peak_base=None)
    # spire (v4 design, fixed curve resolution), rising from the top centre of the plate
    foot = mapper(0.0, 0.0, PLATE_A)
    L = P["t_stone"]; Wd = L * 0.78; k = L / 0.028
    up = Vector((0, 0, 1)); fwd = Vector((0, -1, 0)); side = Vector((1, 0, 0))
    gw = Wd * 0.5 + 0.0022 * k; gl = L * 0.5 + 0.0022 * k; ctr = foot + up * (0.012 * k + gl)
    def Pt(sx, sz): return foot + side * sx + up * sz
    parts = []
    for sgn in (-1, 1):
        pl = [Pt(sgn * 0.010 * k, -0.001 * k), Pt(sgn * 0.008 * k, 0.006 * k), Pt(sgn * gw * 1.05, (ctr - foot).z - gl * 0.55),
              Pt(sgn * gw * 1.08, (ctr - foot).z + gl * 0.15), Pt(sgn * gw * 0.55, (ctr - foot).z + gl * 0.85), Pt(sgn * 0.0012 * k, (ctr - foot).z + gl * 1.25), Pt(0, (ctr - foot).z + gl * 1.55)]
        parts.append(curve_obj("tiara_%s_spire_arm_%d" % (var, sgn), col, pl, 0.0019 * k, r1=0.0007 * k))
    tip = (ctr - foot).z + gl * 1.55
    b = bmesh.new(); bmesh.ops.create_uvsphere(b, u_segments=16, v_segments=8, radius=0.0024 * k)
    bmesh.ops.translate(b, vec=Pt(0, tip + 0.0018 * k), verts=b.verts); mesh_obj("tiara_%s_spire_finial" % var, col, b, GOLD, True)
    parts.append(curve_obj("tiara_%s_spire_tip" % var, col, [Pt(0, tip + 0.003 * k), Pt(0, tip + 0.012 * k), Pt(0, tip + 0.022 * k)], 0.0011 * k, r1=0.0002 * k))
    b = bmesh.new(); bmesh.ops.create_uvsphere(b, u_segments=16, v_segments=8, radius=0.006 * k)
    bmesh.ops.scale(b, vec=(1.6, 0.6, 0.7), verts=b.verts); bmesh.ops.translate(b, vec=foot, verts=b.verts); mesh_obj("tiara_%s_spire_foot" % var, col, b, GOLD, True)
    for c_ in parts: c_.data.bevel_resolution = 2; c_.data.resolution_u = 6
    g, outl, zc = gem_bm(L, Wd, kind="pear")
    face = (fwd + up * 0.12).normalized(); M = Matrix.Translation(ctr) @ frame(face, up)
    bmesh.ops.transform(g, matrix=M, verts=g.verts); mesh_obj("tiara_%s_stone" % var, col, g, AQUA)
    outline_ring("tiara_%s_bezel_pear" % var, col, outl, M, 1.05, 0.0009 * k, n=48)
    info["checks"] = mesh_checks(ob); info["path_len_mm"] = round(pm.L * 1000, 1); info["top_foot"] = rnd(foot)
    dg = bpy.context.evaluated_depsgraph_get(); tot = info["tris"]
    for o in col.objects:
        if o is ob: continue
        me = bpy.data.meshes.new_from_object(o.evaluated_get(dg)); tot += sum(len(p.vertices) - 2 for p in me.polygons); bpy.data.meshes.remove(me)
    info["export_tris_total"] = tot
    htop = [(ut(0) + 2.24) * ku / 1000.0] * len(pts); hbot = [(-ub(0) + 2.24) * ku / 1000.0] * len(pts)
    PATHS[("T", var)] = (pts, T, U, Nn, htop, hbot, False)
    R["v5"]["counts"]["tiara_" + var] = info
    return col

PATHS = {}

# ===================================================================== main
def pen_count(col, bv_skin=BV_SKIN, step=2):
    c = 0; tot = 0
    for o in col.objects:
        if o.type != "MESH" or "stone" in o.name: continue
        for i, v in enumerate(o.data.vertices):
            if i % step: continue
            p = o.matrix_world @ v.co; loc, nrm, idx, d = bv_skin.find_nearest(p); tot += 1
            if loc is not None and (p - loc).dot(nrm) < -0.0005: c += 1
    return c, tot
R["circlet"] = {}; R["tiara"] = {}
for var, bv, hm in (("bald", BV_SKIN, False), ("hair", BV_SKIN, True)):
    c1 = build_circlet(var, bv, hm); c2 = build_tiara(var, bv, hm)
    R["v5"]["counts"]["circlet_" + var]["skin_penetrating_verts"] = pen_count(c1)
    R["v5"]["counts"]["tiara_" + var]["skin_penetrating_verts"] = pen_count(c2)
    if STAB: break          # stability proof: one variant per fit is enough (both variants share the builder)

def fingerprint():
    out = {}
    for k, v in R["v5"]["counts"].items():
        out[k] = {x: v[x] for x in ("verts", "faces", "tris", "quads", "plate_tris", "cdt_merged", "cdt_new_verts", "face_build_fail", "topo_hash")}
        out[k]["checks"] = v["checks"]
    return out
R["v5"]["fingerprint"] = fingerprint()

if STAB:
    json.dump(R, open(RECEIPT, "w"), indent=1, default=str)
    print("V5-STAB", json.dumps(R["v5"]["fingerprint"]))
    print("V5-STAB-PARAMS", json.dumps(P))
else:
    from mathutils.kdtree import KDTree
    def smooth01(x): x = max(0.0, min(1.0, x)); return x * x * (3 - 2 * x)
    def path_kd(pts):
        kd = KDTree(len(pts))
        for i, p in enumerate(pts): kd.insert(p, i)
        kd.balance(); return kd
    def disp_of(p, paths):
        tot = Vector((0, 0, 0)); wmax = 0.0
        for (pts, T, U, Nn, htop, hbot, closed, kd) in paths:
            co, i, dist = kd.find(p)
            if dist > 0.2: continue
            d = p - pts[i]
            h_end = max(htop[i], hbot[i])
            if not closed and (i < 2 or i > len(pts) - 3) and abs(d.dot(T[i])) > h_end * 0.6: continue
            dn = d.dot(Nn[i]); du = d.dot(U[i])
            if dn <= -0.0012: continue
            fall = 0.010 + P["pinch_fall"] * min(dn, 0.08)
            a = (du - (htop[i] + 0.002)) if du >= 0 else (-du - (hbot[i] + 0.002))
            wu = 1.0 if a <= 0 else smooth01(1 - a / fall)
            wn = 1.0 if dn < P["pinch_dmax"] else max(0.0, 1 - (dn - P["pinch_dmax"]) / 0.04)
            w = wu * wn
            if w <= 0: continue
            tot += -Nn[i] * (dn + 0.0012) * w; wmax = max(wmax, w)
        return tot, wmax
    WATER = bpy.data.materials.new("V5_Hair_WaterClay"); WATER.use_nodes = True
    bsdf = WATER.node_tree.nodes.get("Principled BSDF")
    bsdf.inputs["Base Color"].default_value = (0.50, 0.63, 0.70, 1); bsdf.inputs["Roughness"].default_value = 0.42
    HC = PC; R["hair_pinch"] = {}
    for o in hair: o["mel3_role"] = "src_hair_untrimmed"; o.hide_render = True; o.hide_viewport = True
    for key, pieces in (("C", [("C", "hair")]), ("CT", [("C", "hair"), ("T", "hair")])):
        paths = [PATHS[k] + (path_kd(PATHS[k][0]),) for k in pieces]
        moved = 0; mx = 0.0; nv = 0
        for o in hair:
            bm = bmesh.new(); bm.from_mesh(o.data); bm.transform(o.matrix_world)
            for _ in range(2):
                ws = {v: disp_of(v.co, paths)[1] for v in bm.verts}
                ed = [e for e in bm.edges if (ws[e.verts[0]] > 0 or ws[e.verts[1]] > 0) and e.calc_length() > 0.005]
                if ed: bmesh.ops.subdivide_edges(bm, edges=ed, cuts=1, use_grid_fill=True)
            bm.verts.ensure_lookup_table()
            seen = set(); islands = []
            for v in bm.verts:
                if v in seen: continue
                st = [v]; isl = []; seen.add(v)
                while st:
                    x = st.pop(); isl.append(x)
                    for e in x.link_edges:
                        y = e.other_vert(x)
                        if y not in seen: seen.add(y); st.append(y)
                islands.append(isl)
            for isl in islands:
                mn = Vector((min(v.co.x for v in isl), min(v.co.y for v in isl), min(v.co.z for v in isl)))
                mxv = Vector((max(v.co.x for v in isl), max(v.co.y for v in isl), max(v.co.z for v in isl)))
                if (mxv - mn).length < 0.03:
                    dv, w = disp_of((mn + mxv) * 0.5, paths)
                    if w > 0:
                        for v in isl: v.co += dv
                        moved += len(isl); mx = max(mx, dv.length)
                else:
                    for v in isl:
                        dv, w = disp_of(v.co, paths)
                        if w > 0: v.co += dv; moved += 1; mx = max(mx, dv.length)
            nv += len(bm.verts)
            me = bpy.data.meshes.new(o.name + "_v5pinch" + key); bm.to_mesh(me); bm.free()
            for pp in me.polygons: pp.use_smooth = True
            ob = bpy.data.objects.new(o.name + "_v5pinch" + key, me); HC.objects.link(ob)
            ob["mel3_role"] = "hairv4_" + key; ob.data.materials.append(WATER)
        R["hair_pinch"][key] = {"verts": nv, "moved": moved, "max_disp_mm": mm(mx)}
    R["notes"].append("v5: circlet/tiara plate+wire filigree with topology fixed in nominal motif space; earrings/necklace unchanged from v3_final")
    bpy.ops.wm.save_as_mainfile(filepath=OUTBLEND, copy=True)
    json.dump(R, open(RECEIPT, "w"), indent=1, default=str)
    print("V5-FP", json.dumps(R["v5"]["fingerprint"]))
    print("V5-SAVED", OUTBLEND)
