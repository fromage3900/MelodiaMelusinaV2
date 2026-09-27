"""regalia_v4_build.py -- opens regalia_v3_final.blend (never saved over) and REBUILDS the circlet and tiara as
head-conforming pieces: band paths sampled on Melusina's skull (and, for the hair variant, on her water-hair surface),
offset outward, slim swept gold profile + rails, filigree loops projected ON the surface, a front-centre collet stone
(circlet) and a front-centre spire (tiara). Earrings/necklace untouched. Saves regalia_v4<tag>.blend (NEW file).
blender -b --factory-startup regalia_v3_final.blend --python regalia_v4_build.py -- --tag _it0"""
import bpy, bmesh, math, json, os, sys
from mathutils import Vector, Matrix
from mathutils.bvhtree import BVHTree
W = r"C:\EnvironmentPortfolio\_lookdev_work\regalia_v2"
A = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
def arg(k, d): return type(d)(A[A.index(k) + 1]) if k in A else d
TAG = arg("--tag", "")
OUTBLEND = W + r"\regalia_v4%s.blend" % TAG; RECEIPT = W + r"\regalia_v4%s_build_receipt.json" % TAG
assert not os.path.exists(OUTBLEND), "refusing to overwrite " + OUTBLEND
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
def circlet_path(bv, hair_mode, N=240):
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

def tiara_path(bv, hair_mode, N=160):
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

PATHS = {}
# ------------------------------------------------ build a variant
def build_circlet(var, bv, hair_mode):
    col = bpy.data.collections.new("REG_circlet_" + var); bpy.context.scene.collection.children.link(col)
    pts, nrm, closed = circlet_path(bv, hair_mode)
    T, U, Nn = frames(pts, nrm, closed)
    if U[0].z < 0: U = [-u for u in U]
    h = P["c_h"]; th = P["c_th"]
    band = sweep("circlet_%s_band" % var, col, pts, T, U, Nn, band_profile(h, th), closed)
    for sgn in (1, -1):
        sweep("circlet_%s_rail_%s" % (var, "top" if sgn > 0 else "bot"), col, pts, T, U, Nn, circle_profile(P["c_rail"]), closed, off_n=th * 0.75, off_u=sgn * (h * 0.5 - P["c_rail"] * 0.6))
    n = len(pts)
    # filigree loops ON the surface above the band, every 24 deg, keeping the front 40 deg clear for the stone
    idxs = [i for i in range(0, n, n // 15) if min(i, n - i) > n * 20 / 360]
    nl = loops_along("circlet_%s" % var, col, bv, pts, T, U, Nn, idxs, 1, h)
    # front-centre collet stone, flush on the band face, facing forward
    L = P["c_stone"]; Wd = L * 0.76
    g, outl, zc = gem_bm(L, Wd, kind="oval", crown=0.14, pav=0.22)
    depth = -zc + 0.0008
    front = pts[0] + Nn[0] * th
    M = Matrix.Translation(front + Nn[0] * depth) @ frame(Nn[0], T[0])
    bmesh.ops.transform(g, matrix=M, verts=g.verts); stone = mesh_obj("circlet_%s_stone" % var, col, g, AQUA)
    outline_ring("circlet_%s_collet_rim" % var, col, outl, M, 1.035, 0.0011)
    collet_cup("circlet_%s_collet_cup" % var, col, outl, M, depth)
    for o in col.objects:
        if o.type == "MESH" and ("band" in o.name): o.modifiers.new("smooth", "SUBSURF").levels = 1
    PATHS[("C", var)] = (pts, T, U, Nn, h, th, True)
    R.setdefault("circlet", {})[var] = {"samples": n, "loops": nl, "front_centre": rnd(front), "front_normal": rnd(Nn[0]), "stone_len_mm": mm(L),
        "band_h_mm": mm(h), "band_th_mm": mm(th), "z_front": round(pts[0].z, 4), "z_back": round(pts[n // 2].z, 4), "z_side": round(pts[n // 4].z, 4),
        "path_len_mm": mm(sum((pts[(i + 1) % n] - pts[i]).length for i in range(n)))}
    return col

def build_tiara(var, bv, hair_mode):
    col = bpy.data.collections.new("REG_tiara_" + var); bpy.context.scene.collection.children.link(col)
    pts, nrm, closed = tiara_path(bv, hair_mode)
    T, U, Nn = frames(pts, nrm, closed)
    n = len(pts); mid = n // 2
    if U[mid].dot(Vector((0, -1, 0))) < 0: U = [-u for u in U]     # U points toward the face at the top
    h = P["t_h"]; th = P["c_th"]
    sweep("tiara_%s_band" % var, col, pts, T, U, Nn, band_profile(h, th), closed)
    for sgn in (1, -1):
        sweep("tiara_%s_rail_%d" % (var, sgn), col, pts, T, U, Nn, circle_profile(P["c_rail"]), closed, off_n=th * 0.75, off_u=sgn * (h * 0.5 - P["c_rail"] * 0.6))
    # end finials (small balls) at the ear ends
    for i in (0, n - 1):
        b = bmesh.new(); bmesh.ops.create_uvsphere(b, u_segments=20, v_segments=10, radius=h * 0.42)
        bmesh.ops.translate(b, vec=pts[i] + Nn[i] * th * 0.6, verts=b.verts); mesh_obj("tiara_%s_end_%d" % (var, i), col, b, GOLD, True)
    # loops toward the face, lying on the crown, avoiding the spire zone
    idxs = [i for i in range(12, n - 10, 13) if abs(i - mid) > 12]
    nl = loops_along("tiara_%s" % var, col, bv, pts, T, U, Nn, idxs, 1, h, closed=False)
    # spire: centred at the top of the arc, rising up; teardrop frame round a pear stone facing forward
    foot = pts[mid] + Nn[mid] * th
    L = P["t_stone"]; Wd = L * 0.78; k = L / 0.028
    up = Vector((0, 0, 1)); fwd = Vector((0, -1, 0)); side = Vector((1, 0, 0))
    gw = Wd * 0.5 + 0.0022 * k; gl = L * 0.5 + 0.0022 * k
    ctr = foot + up * (0.012 * k + gl)
    def Pt(sx, sz): return foot + side * sx + up * sz + fwd * 0.0
    for sgn in (-1, 1):
        pl = [Pt(sgn * 0.010 * k, -0.002 * k), Pt(sgn * 0.008 * k, 0.006 * k), Pt(sgn * gw * 1.05, (ctr - foot).z - gl * 0.55),
              Pt(sgn * gw * 1.08, (ctr - foot).z + gl * 0.15), Pt(sgn * gw * 0.55, (ctr - foot).z + gl * 0.85), Pt(sgn * 0.0012 * k, (ctr - foot).z + gl * 1.25),
              Pt(0, (ctr - foot).z + gl * 1.55)]
        curve_obj("tiara_%s_spire_arm_%d" % (var, sgn), col, pl, 0.0019 * k, r1=0.0007 * k)
        cl = [Pt(sgn * 0.009 * k, 0.0), Pt(sgn * 0.020 * k, 0.004 * k), Pt(sgn * 0.027 * k, 0.011 * k), Pt(sgn * 0.022 * k, 0.016 * k), Pt(sgn * 0.017 * k, 0.012 * k)]
        curve_obj("tiara_%s_spire_curl_%d" % (var, sgn), col, [on_surface(bv, q, 0.0016 * k) if q.z < foot.z + 0.004 * k else q for q in cl], 0.0014 * k, r1=0.0006 * k)
    tip = (ctr - foot).z + gl * 1.55
    b = bmesh.new(); bmesh.ops.create_uvsphere(b, u_segments=24, v_segments=12, radius=0.0024 * k)
    bmesh.ops.translate(b, vec=Pt(0, tip + 0.0018 * k), verts=b.verts); mesh_obj("tiara_%s_spire_finial" % var, col, b, GOLD, True)
    curve_obj("tiara_%s_spire_tip" % var, col, [Pt(0, tip + 0.003 * k), Pt(0, tip + 0.012 * k), Pt(0, tip + 0.022 * k)], 0.0011 * k, r1=0.0002 * k)
    # foot plate hugging the band
    b = bmesh.new(); bmesh.ops.create_uvsphere(b, u_segments=20, v_segments=10, radius=0.006 * k)
    bmesh.ops.scale(b, vec=(1.6, 0.6, 0.7), verts=b.verts); bmesh.ops.translate(b, vec=foot, verts=b.verts); mesh_obj("tiara_%s_spire_foot" % var, col, b, GOLD, True)
    g, outl, zc = gem_bm(L, Wd, kind="pear")
    face = (fwd + up * 0.12).normalized()
    M = Matrix.Translation(ctr) @ frame(face, up)
    bmesh.ops.transform(g, matrix=M, verts=g.verts); mesh_obj("tiara_%s_stone" % var, col, g, AQUA)
    outline_ring("tiara_%s_bezel_pear" % var, col, outl, M, 1.05, 0.0009 * k)
    for o in col.objects:
        if o.type == "MESH" and "band" in o.name: o.modifiers.new("smooth", "SUBSURF").levels = 1
    PATHS[("T", var)] = (pts, T, U, Nn, h, th, False)
    R.setdefault("tiara", {})[var] = {"samples": n, "loops": nl, "top_foot": rnd(foot), "stone_len_mm": mm(L), "spire_k": round(k, 3),
        "spire_tip_z": round(foot.z + tip + 0.022 * k, 4), "ends": [rnd(pts[0]), rnd(pts[-1])], "band_h_mm": mm(h)}
    return col

def pen_count(col, bv_skin=BV_SKIN, step=2):
    c = 0; tot = 0
    for o in col.objects:
        if o.type != "MESH" or "stone" in o.name: continue
        for i, v in enumerate(o.data.vertices):
            if i % step: continue
            p = o.matrix_world @ v.co; loc, nrm, idx, d = bv_skin.find_nearest(p); tot += 1
            if loc is not None and (p - loc).dot(nrm) < -0.0005: c += 1
    return c, tot

for var, bv, hm in (("bald", BV_SKIN, False), ("hair", BV_SKIN, True)):
    c1 = build_circlet(var, bv, hm); c2 = build_tiara(var, bv, hm)
    R["circlet"][var]["skin_penetrating_verts"] = pen_count(c1); R["tiara"][var]["skin_penetrating_verts"] = pen_count(c2)

# ------------------------------------------------ hair variant: copies of her water hair PINCHED under the bands
from mathutils.kdtree import KDTree
def smooth01(x): x = max(0.0, min(1.0, x)); return x * x * (3 - 2 * x)
def path_kd(pts):
    kd = KDTree(len(pts))
    for i, p in enumerate(pts): kd.insert(p, i)
    kd.balance(); return kd
def disp_of(p, paths):
    tot = Vector((0, 0, 0)); wmax = 0.0
    for (pts, T, U, Nn, h, th, closed, kd) in paths:
        co, i, dist = kd.find(p)
        if dist > 0.2: continue
        d = p - pts[i]
        if not closed and (i < 2 or i > len(pts) - 3) and abs(d.dot(T[i])) > h * 0.6: continue
        dn = d.dot(Nn[i]); du = d.dot(U[i])
        if dn <= -0.0012: continue
        fall = 0.010 + P["pinch_fall"] * min(dn, 0.08)
        a = abs(du) - (h * 0.5 + 0.002)
        wu = 1.0 if a <= 0 else smooth01(1 - a / fall)
        wn = 1.0 if dn < P["pinch_dmax"] else max(0.0, 1 - (dn - P["pinch_dmax"]) / 0.04)
        w = wu * wn
        if w <= 0: continue
        tot += -Nn[i] * (dn + 0.0012) * w; wmax = max(wmax, w)
    return tot, wmax
WATER = bpy.data.materials.new("V4_Hair_WaterClay"); WATER.use_nodes = True
bsdf = WATER.node_tree.nodes.get("Principled BSDF")
bsdf.inputs["Base Color"].default_value = (0.50, 0.63, 0.70, 1); bsdf.inputs["Roughness"].default_value = 0.42
HC = PC
R["hair_pinch"] = {}
for o in hair: o["mel3_role"] = "src_hair_untrimmed"; o.hide_render = True; o.hide_viewport = True
for key, pieces in (("C", [("C", "hair")]), ("CT", [("C", "hair"), ("T", "hair")])):
    paths = [PATHS[k] + (path_kd(PATHS[k][0]),) for k in pieces]
    moved = 0; mx = 0.0; nv = 0
    for o in hair:
        bm = bmesh.new(); bm.from_mesh(o.data); bm.transform(o.matrix_world)
        # refine edges inside the pinch zone so the groove is smooth
        for _ in range(2):
            ws = {v: disp_of(v.co, paths)[1] for v in bm.verts}
            ed = [e for e in bm.edges if (ws[e.verts[0]] > 0 or ws[e.verts[1]] > 0) and e.calc_length() > 0.005]
            if ed: bmesh.ops.subdivide_edges(bm, edges=ed, cuts=1, use_grid_fill=True)
        bm.verts.ensure_lookup_table()
        # islands: small ones (water droplets) move rigidly
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
                ds_ = [disp_of(v.co, paths) for v in isl]
                for v, (dv, w) in zip(isl, ds_):
                    if w > 0: v.co += dv; moved += 1; mx = max(mx, dv.length)
        nv += len(bm.verts)
        me = bpy.data.meshes.new(o.name + "_v4pinch" + key); bm.to_mesh(me); bm.free()
        for pp in me.polygons: pp.use_smooth = True
        ob = bpy.data.objects.new(o.name + "_v4pinch" + key, me); HC.objects.link(ob)
        ob["mel3_role"] = "hairv4_" + key; ob.data.materials.append(WATER)
    R["hair_pinch"][key] = {"verts": nv, "moved": moved, "max_disp_mm": mm(mx)}
R["notes"].append("hair variant: bands on skull + %d mm clearance + %d mm hair layer; hair copies pinched under the bands (originals hidden, untouched)" % (mm(P["c_clear"]), mm(P["hair_lift"])))
R["notes"].append("earrings/necklace unchanged from v3_final; v3 ring headpieces removed in this file")
bpy.ops.wm.save_as_mainfile(filepath=OUTBLEND, copy=True)
json.dump(R, open(RECEIPT, "w"), indent=1, default=str)
print("V4B-RECEIPT", json.dumps(R, default=str))
print("V4B-SAVED", OUTBLEND)
