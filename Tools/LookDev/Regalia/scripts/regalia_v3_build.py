"""regalia_v3_build.py -- opens regalia_v2d.blend, swaps the egg/neck/shoulder proxies for Melusina's baked bust
(melusina_bust_src_v3.blend, extracted read-only from ARP_R09_HotPass), fits the four pieces to her, saves regalia_v3.blend (NEW file).
blender -b --factory-startup regalia_v2d.blend --python regalia_v3_build.py"""
import bpy, bmesh, math, json, os, sys
from mathutils import Vector, Matrix
from mathutils.bvhtree import BVHTree
W = r"C:\EnvironmentPortfolio\_lookdev_work\regalia_v2"
SRC = W + r"\v3\melusina_bust_src_v3.blend"
_A = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
TAG = _A[_A.index("--tag") + 1] if "--tag" in _A else ""
OUTBLEND = W + r"\regalia_v3%s.blend" % TAG; RECEIPT = W + r"\regalia_v3%s_build_receipt.json" % TAG
assert not os.path.exists(OUTBLEND), "regalia_v3.blend exists -- refusing to overwrite"
R = {"notes": [], "fit": {}}
vl = bpy.context.view_layer
def upd(): vl.update()
O = bpy.data.objects
def mm(v): return round(v * 1000, 1)
def rnd(v): return [round(x, 4) for x in v]
def eval_pts(o, step=1):
    dg = bpy.context.evaluated_depsgraph_get(); oe = o.evaluated_get(dg); me = oe.to_mesh()
    pts = [o.matrix_world @ v.co for i, v in enumerate(me.vertices) if i % step == 0]; oe.to_mesh_clear(); return pts
def bb(pts): return (Vector([min(p[i] for p in pts) for i in range(3)]), Vector([max(p[i] for p in pts) for i in range(3)]))

# ------------------------------------------------ 1) stage: remove proxies (in this new file only), append Melusina
PC = bpy.data.collections["STAGE_proxies"]
for o in list(PC.objects): bpy.data.objects.remove(o)
with bpy.data.libraries.load(SRC, link=False) as (src, dst):
    dst.objects = [n for n in src.objects if n.startswith("MEL3_")]
MEL = {}
for o in dst.objects:
    if o is None: continue
    PC.objects.link(o); MEL[o["mel3_role"] + ("_" + o["mel3_src"] if o["mel3_role"] in ("eye", "brow") else "")] = o
R["appended"] = sorted(o.name for o in dst.objects if o)
body = [o for o in dst.objects if o and o["mel3_role"] == "body"][0]
# matte overrides (not her toon materials)
def matte(name, rgb, rough=0.6, sss=0.0, spec=0.35):
    m = bpy.data.materials.new(name); m.use_nodes = True; b = m.node_tree.nodes["Principled BSDF"]
    b.inputs["Base Color"].default_value = rgb + (1,); b.inputs["Roughness"].default_value = rough
    try: b.inputs["Specular IOR Level"].default_value = spec
    except Exception: pass
    if sss:
        try:
            b.inputs["Subsurface Weight"].default_value = sss; b.inputs["Subsurface Radius"].default_value = (0.012, 0.005, 0.003)
        except Exception: pass
    return m
SKIN = matte("V3_Skin_LightMatte", (0.80, 0.65, 0.57), 0.55, sss=0.08)
DARK = matte("V3_Brow_Lash", (0.10, 0.075, 0.065), 0.7)
SCLERA = matte("V3_Eye_White", (0.85, 0.84, 0.82), 0.3)
IRIS = matte("V3_Eye_Iris", (0.10, 0.12, 0.16), 0.15, spec=0.6)
HAIR = matte("V3_Hair_Clay", (0.42, 0.33, 0.28), 0.6)
for o in dst.objects:
    if o is None: continue
    role = o["mel3_role"]; src = o["mel3_src"]
    mat = {"body": SKIN, "brow": DARK, "lash": DARK, "eye": (SCLERA if src.endswith(".001") else IRIS)}.get(role, HAIR)
    o.data.materials.clear(); o.data.materials.append(mat)
    for p in o.data.polygons: p.use_smooth = True
    if role == "body":
        m = o.modifiers.new("smooth", "SUBSURF"); m.levels = 1; m.render_levels = 2
    if role.startswith("hair"):
        o.hide_render = True; o.hide_viewport = True   # water hair covers the crown (+51 mm above the scalp) and the brow
R["notes"].append("hair meshes appended but hidden (hair_main rises 51 mm above the scalp; bangs cover the forehead)")
R["materials"] = "matte overrides: skin (0.80,0.65,0.57) r0.55 sss0.08; brows/lashes dark; eye white/iris; her toon materials not used"
upd()

# ------------------------------------------------ helpers against HER body
dgx = bpy.context.evaluated_depsgraph_get()
BVH = BVHTree.FromObject(body, dgx); BINV = body.matrix_world.inverted()
BP = eval_pts(body)
def section(z, tol=0.004):
    s = [p for p in BP if abs(p.z - z) < tol]
    mn, mx = bb(s); return (mn + mx) * 0.5, mx.x - mn.x, mx.y - mn.y
def inside_count(objs, step=3):
    c = 0; dg = bpy.context.evaluated_depsgraph_get()
    for o in objs:
        if o.type != "MESH": continue
        oe = o.evaluated_get(dg); me_ = oe.to_mesh()
        for i_, v in enumerate(me_.vertices):
            if i_ % step: continue
            p = BINV @ (o.matrix_world @ v.co); hit = BVH.find_nearest(p)
            if hit[0] is not None and (p - hit[0]).dot(hit[1]) < 0: c += 1
        oe.to_mesh_clear()
    return c
def inner_spans(o, zc, ctr, tol):
    bins = {}
    for p in eval_pts(o, 2):
        if abs(p.z - zc) > tol: continue
        d = p - ctr; a = int(((math.degrees(math.atan2(d.y, d.x)) + 360) % 360) // 5); r = math.hypot(d.x, d.y)
        bins[a] = min(bins.get(a, 9), r)
    g = lambda a: min(bins.get((a + k) % 72, 9) for k in (-1, 0, 1))
    rs = sorted(bins.values()); med = rs[len(rs) // 2]
    sp = lambda a, b: (g(a) + g(b)) if g(a) < 9 and g(b) < 9 else None
    return sp(0, 36), sp(18, 54), 2 * med
def xform(objs, M):
    for o in objs: o.matrix_world = M @ o.matrix_world
def piece_objs(p): return list(bpy.data.collections["REG_" + p].objects)

# head reference numbers
top = max(p.z for p in BP)
brow_z = max(p.z for p in eval_pts([o for o in dst.objects if o and o["mel3_role"] == "brow"][0]))
R["her_head"] = {"top_z": round(top, 4), "brow_top_z": round(brow_z, 4)}
hc_b, hx_b, hy_b = section(brow_z + 0.04)
R["her_head"]["section_at_brow+40mm_mm"] = [mm(hx_b), mm(hy_b)]
K_HEAD = hx_b / 0.150       # her head width vs the 150 mm adult head the v2d pieces were sized for
R["her_head"]["k_head_vs_150mm_adult"] = round(K_HEAD, 3)

# ------------------------------------------------ 2) circlet: on the brow (front edge ~12 mm above the brows), fitted, grown until clear
def fit_ring(p, z_band, clr, uniform_prefixes, pivot_fn, stone, grow=True):
    objs = piece_objs(p); g = O[p + "_gold"]
    gp = eval_pts(g); gmn, gmx = bb(gp); bz = (gmn.z + gmx.z) * 0.5
    c0 = Vector(((gmn.x + gmx.x) * 0.5, (gmn.y + gmx.y) * 0.5, bz))
    # centre of the band's inner opening (angular bins around the gold bbox centre)
    ix, iy, imean = inner_spans(g, bz, c0, (gmx.z - gmn.z) * 0.5)
    iy = iy or (2 * imean - ix)
    hc, hx, hy = section(z_band)
    sx = (hx + 2 * clr) / ix; sy = (hy + 2 * clr) / iy; sz = (sx + sy) * 0.5
    piv0 = pivot_fn()
    def apply(sx, sy, dy=0.0):
        M = Matrix.Translation(Vector((hc.x, hc.y + dy, z_band))) @ Matrix.Diagonal((sx, sy, K_HEAD, 1)) @ Matrix.Translation(-c0)
        su = K_HEAD; pn = M @ piv0
        MU = Matrix.Translation(pn) @ Matrix.Scale(su, 4) @ Matrix.Translation(-piv0)
        for o in objs:
            o.matrix_world = (MU if o.name.startswith(uniform_prefixes) else M) @ MW0[o.name]
        upd()
    MW0 = {o.name: o.matrix_world.copy() for o in objs}
    meshes = [o for o in objs if o.type == "MESH"]
    tries = 0; best = None
    for tries in range(0, 14):
        f = 1.02 ** tries
        for dy in (0.0, -0.008, 0.008, -0.016, 0.016, -0.024, 0.024, -0.032, 0.032):
            apply(sx * f, sy * f, dy); pen = inside_count(meshes)
            if pen == 0: best = (f, dy); break
        if best: break
    if best is None: best = (1.02 ** 13, 0.0)
    sx *= best[0]; sy *= best[0]; apply(sx, sy, best[1]); pen = inside_count(meshes, 1)
    smn, smx = bb(eval_pts(O[stone])); gmn2, gmx2 = bb(eval_pts(g))
    R["fit"][p] = {"extra_scale_vs_v2d_xyz": [round(sx, 3), round(sy, 3), round((sx + sy) / 2, 3)], "band_z": round(z_band, 4),
                   "her_section_mm": [mm(hx), mm(hy)], "v2d_inner_mm": [mm(ix), mm(iy)], "grow_steps_2pct": tries, "dy_mm": mm(best[1]), "penetrating_verts": pen, "z_and_stone_scale": round(K_HEAD, 3),
                   "outer_mm": [mm(v) for v in (gmx2 - gmn2)], "stone_len_mm": mm(max(smx - smn))}
    return sx, sy

def pivot_of(name):
    def f():
        a, b = bb(eval_pts(O[name])); return (a + b) * 0.5
    return f
fit_ring("circlet", brow_z + 0.030, 0.003, ("circlet_stone", "circlet_bezel"), pivot_of("circlet_stone"), "circlet_stone")
# ------------------------------------------------ 3) tiara: on the crown -- section ~45 mm below the top
tz = top - 0.030
def tiara_foot():
    a, b = bb(eval_pts(O["tiara_stone"])); g0, g1 = bb(eval_pts(O["tiara_gold"]))
    return Vector(((a.x + b.x) * 0.5, (a.y + b.y) * 0.5, g1.z))
fit_ring("tiara", tz, 0.002, ("tiara_stone", "tiara_bezel", "tiara_spire", "tiara_prong"), tiara_foot, "tiara_stone")
# settle the tiara down onto the crown
tobjs = piece_objs("tiara"); tm = [o for o in tobjs if o.type == "MESH"]; dz = 0.0; st = 0
if inside_count(tm) == 0:
    while inside_count(tm) == 0 and st < 40:
        xform(tobjs, Matrix.Translation((0, 0, -0.001))); upd(); dz -= 0.001; st += 1
    xform(tobjs, Matrix.Translation((0, 0, 0.0015))); upd(); dz += 0.0015
else:
    while inside_count(tm) > 0 and st < 40:
        xform(tobjs, Matrix.Translation((0, 0, 0.001))); upd(); dz += 0.001; st += 1
R["fit"]["tiara"]["settle_dz_mm"] = mm(dz); R["fit"]["tiara"]["penetrating_after_settle"] = inside_count(tm, 1)

# ------------------------------------------------ 3b) pull the flat outward loops in (radial compression beyond the band)
def compress_overhang(p, D, f):
    g = O[p + "_gold"]; gp = eval_pts(g); gmn, gmx = bb(gp)
    c = Vector(((gmn.x + gmx.x) * 0.5, (gmn.y + gmx.y) * 0.5, 0))
    # inner radius per 5 deg bin, from the head section is not needed: take the gold's own inner edge
    me = g.data; Mw = g.matrix_world; Mi = Mw.inverted()
    P = [Mw @ v.co for v in me.vertices]
    bins = {}
    for q in P:
        d = q - c; a = int(((math.degrees(math.atan2(d.y, d.x)) + 360) % 360) // 5); r = math.hypot(d.x, d.y)
        bins[a] = min(bins.get(a, 9), r)
    vals = sorted(bins.values()); med = vals[len(vals) // 2]
    rin = {}
    for a in range(72):
        near = [bins[(a + k) % 72] for k in range(-2, 3) if (a + k) % 72 in bins]
        rin[a] = (sum(near) / len(near)) if near else med
    def mapq(q):
        d = q - c; a = int((math.degrees(math.atan2(d.y, d.x)) % 360) // 5); r = math.hypot(d.x, d.y)
        dr = r - rin[a]
        if dr <= D: return q, 0.0
        r2 = rin[a] + D + (dr - D) * f; k = r2 / r
        return Vector((c.x + d.x * k, c.y + d.y * k, q.z)), r - r2
    moved = 0; maxpull = 0.0
    for v, q in zip(me.vertices, P):
        nq, pull = mapq(q)
        if pull > 0: v.co = Mi @ nq; moved += 1; maxpull = max(maxpull, pull)
    me.update(); upd()
    # carry the stone / bezel / spire / prongs rigidly with the band (same map applied to their centres)
    a_, b_ = bb(eval_pts(O[p + "_stone"])); ctr = (a_ + b_) * 0.5; nq, pull = mapq(ctr)
    carried = {"displacement_mm": mm(pull), "objects": []}
    if pull > 0:
        for o in piece_objs(p):
            if o is g: continue
            o.matrix_world = Matrix.Translation(nq - ctr) @ o.matrix_world; carried["objects"].append(o.name)
    upd()
    a2, b2 = bb(eval_pts(g))
    R["fit"][p]["overhang_compression"] = {"band_keep_mm": mm(D), "factor": f, "verts_moved": moved, "max_pull_mm": mm(maxpull), "carried_mm": carried, "outer_after_mm": [mm(v) for v in (b2 - a2)]}
O["circlet_gold"].data = O["circlet_gold"].data.copy(); O["tiara_gold"].data = O["tiara_gold"].data.copy()
compress_overhang("circlet", 0.034, 0.45)
compress_overhang("tiara", 0.028, 0.5)
R["fit"]["circlet"]["penetrating_after_compress"] = inside_count([o for o in piece_objs("circlet") if o.type == "MESH"], 1)
R["fit"]["tiara"]["penetrating_after_compress"] = inside_count([o for o in piece_objs("tiara") if o.type == "MESH"], 1)

# ------------------------------------------------ 4) earrings: at her lobes, scaled by her head factor
ear = [p for p in BP if abs(p.x) > 0.18 and 1.47 < p.z < 1.62]
ER = {}
for side, sgn in (("earL", 1), ("earR", -1)):
    pts = [p for p in ear if p.x * sgn > 0]
    lobe = min(pts, key=lambda p: p.z)
    stud = O[side + "_stud"]; s0 = stud.matrix_world.translation.copy()
    objs = [o for o in bpy.data.collections["REG_earrings"].objects if o.name.startswith(side)]
    tgt = Vector((lobe.x + sgn * 0.003, lobe.y - 0.002, lobe.z + 0.004 * K_HEAD))
    M = Matrix.Translation(tgt) @ Matrix.Scale(K_HEAD, 4) @ Matrix.Translation(-s0)
    xform(objs, M)
    ER[side] = {"lobe": rnd(lobe), "stud_at": rnd(tgt)}
upd()
R["fit"]["earrings"] = {"scale": round(K_HEAD, 3), "sides": ER, "ear_verts_found": len(ear)}

# ------------------------------------------------ 5) necklace: scale to her neck, then settle onto the neck base / shoulders
nobjs = list(bpy.data.collections["REG_necklace"].objects)
beads = O["necklace_beads"]; bp_ = eval_pts(beads); bmn, bmx = bb(bp_); nz = (bmn.z + bmx.z) * 0.5
c0 = Vector(((bmn.x + bmx.x) * 0.5, (bmn.y + bmx.y) * 0.5, nz))
_, _, nimean = inner_spans(beads, nz, c0, (bmx.z - bmn.z) * 0.5 + 0.01)
neck_z = 1.335   # below the jaw (1.40 slice caught the chin)
nhc, nhx, nhy = section(neck_z)
kn = ((nhx + nhy) * 0.5 + 0.030) / nimean
M = Matrix.Translation(Vector((nhc.x, nhc.y, neck_z))) @ Matrix.Scale(kn, 4) @ Matrix.Translation(-c0)
xform(nobjs, M); upd()
nm = [o for o in nobjs if o.type == "MESH" and o.name == "necklace_beads"]; st = 0; dz = 0.0
while inside_count(nm) == 0 and st < 160:
    xform(nobjs, Matrix.Translation((0, 0, -0.001))); upd(); dz -= 0.001; st += 1
xform(nobjs, Matrix.Translation((0, 0, 0.002))); upd(); dz += 0.002
pn_a, pn_b = bb(eval_pts(O["necklace_pendant"]))
R["fit"]["necklace"] = {"scale": round(kn, 3), "neck_section_at_1.40_mm": [mm(nhx), mm(nhy)], "v2d_inner_mean_mm": mm(nimean),
                        "settle_dz_mm": mm(dz), "hit_limit": st >= 160, "pendant_len_mm": mm(pn_b.z - pn_a.z), "pendant_centre": rnd((pn_a + pn_b) * 0.5)}

bpy.ops.wm.save_as_mainfile(filepath=OUTBLEND, copy=True)
json.dump(R, open(RECEIPT, "w"), indent=1, default=str)
print("V3B-RECEIPT", json.dumps(R, default=str))
print("V3B-SAVED", OUTBLEND)
