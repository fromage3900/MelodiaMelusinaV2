"""regalia_v2d_build.py -- opens regalia_v2b.blend, rescales circlet/tiara/head to human size,
pear bezel for the tiara, deeper/clearer Void Orchid + baked aquamarine, saves regalia_v2d.blend (new file).
blender -b --factory-startup regalia_v2b.blend --python regalia_v2d_build.py"""
import bpy, bmesh, math, json
from mathutils import Vector, Matrix
from mathutils.bvhtree import BVHTree
W = r"C:\EnvironmentPortfolio\_lookdev_work\regalia_v2"
OUTBLEND = W + r"\regalia_v2d.blend"; RECEIPT = W + r"\regalia_v2d_build_receipt.json"
R = {"notes": []}
vl = bpy.context.view_layer
def upd(): vl.update()
O = bpy.data.objects
GOLD = bpy.data.materials["V2_Gold"]

def eval_pts(o, step=1):
    dg = bpy.context.evaluated_depsgraph_get(); oe = o.evaluated_get(dg); me = oe.to_mesh()
    pts = [o.matrix_world @ v.co for i, v in enumerate(me.vertices) if i % step == 0]; oe.to_mesh_clear(); return pts
def bb(pts):
    return (Vector([min(p[i] for p in pts) for i in range(3)]), Vector([max(p[i] for p in pts) for i in range(3)]))
def head_section(z, tol=0.004):
    allp = eval_pts(O["PROXY_head"]); pts = []
    while len(pts) < 8 and tol < 0.05:
        pts = [p for p in allp if abs(p.z - z) < tol]; tol *= 2
    if not pts: raise RuntimeError("head_section: no head verts near z=%.4f (head z %.4f..%.4f)" % (z, min(p.z for p in allp), max(p.z for p in allp)))
    mn, mx = bb(pts); return (mn + mx) * 0.5, mx.x - mn.x, mx.y - mn.y
def inner_spans(o, zc, ctr, tol):
    """angular min radius of the piece around ctr in a z slab -> inner x / y spans"""
    bins = {}
    for p in eval_pts(o, 2):
        if abs(p.z - zc) > tol: continue
        d = p - ctr; a = int(((math.degrees(math.atan2(d.y, d.x)) + 360) % 360) // 5); r = math.hypot(d.x, d.y)
        bins[a] = min(bins.get(a, 9), r)
    g = lambda a: min(bins.get((a + k) % 72, 9) for k in (-1, 0, 1))
    rs = sorted(bins.values()); med = rs[len(rs) // 2] if rs else 0
    sp = lambda a, b: (g(a) + g(b)) if g(a) < 9 and g(b) < 9 else None
    return sp(0, 36), sp(18, 54), 2 * med, len(bins)
def mm(v): return round(v * 1000, 1)
def rnd(v): return [round(x, 4) for x in v]

# ------------------------------------------------ 0) measure old fit
H = O["PROXY_head"]; hp = eval_pts(H); hmn, hmx = bb(hp)
R["head_old_mm"] = [mm(v) for v in (hmx - hmn)]
old = {}
for piece, stone in (("circlet", "circlet_stone"), ("tiara", "tiara_stone")):
    g = O[piece + "_gold"]; gp = eval_pts(g); gmn, gmx = bb(gp)
    bz = (gmn.z + gmx.z) * 0.5 if piece == "circlet" else gmn.z + 0.006
    hc, hx, hy = head_section(bz)
    ix, iy, imean, nb = inner_spans(g, bz, Vector((hc.x, hc.y, bz)), (gmx.z - gmn.z) * 0.5 if piece == "circlet" else 0.006)
    old[piece] = dict(bz=bz, rel=(bz - hmn.z) / (hmx.z - hmn.z), hc=hc, hx=hx, hy=hy, ix=ix, iy=(iy or (2 * imean - ix)), W=gmx.x - gmn.x, D=gmx.y - gmn.y, gmn=gmn, gmx=gmx)
    R[piece + "_old"] = {"outer_mm": [mm(gmx.x - gmn.x), mm(gmx.y - gmn.y)], "inner_x_y_mm": [ix and mm(ix), iy and mm(iy)], "inner_mean_diam_mm": mm(imean), "angle_bins": nb,
                         "head_section_mm": [mm(hx), mm(hy)], "band_rel_height": round(old[piece]["rel"], 3)}

# ------------------------------------------------ 1) pear bezel for the tiara (built in old coords, before scaling)
st = O["tiara_stone"]; sme = st.data
tab = max(sme.polygons, key=lambda p: len(p.vertices))          # 16-gon table
out = (st.matrix_world.to_3x3() @ tab.normal).normalized()
tabc = st.matrix_world @ tab.center
L = 0.028; Wd = L * 0.78; crown = 0.16
ctr = tabc - out * (crown * L)
def frame(z, yhint=Vector((0, 0, 1))):
    z = z.normalized(); y = (yhint - z * yhint.dot(z)).normalized(); x = y.cross(z)
    return Matrix((x, y, z)).transposed().to_4x4()
M = Matrix.Translation(ctr) @ frame(out)
def outline(t, width, length):
    a = 2 * math.pi * t; x, y = math.cos(a), math.sin(a)
    k = 0.5 * (1 + y); x *= (1 - 0.55 * k ** 2.2); return Vector((x * width * 0.5, y * length * 0.5, 0))
n = 128; rt = 0.0009; ring = 12
wid, lng = Wd + 2 * rt * 0.9, L + 2 * rt * 0.9
P = [outline(i / n, wid, lng) for i in range(n)]
bm = bmesh.new(); rows = []
for i in range(n):
    tng = (P[(i + 1) % n] - P[i - 1]).normalized(); nrm = tng.cross(Vector((0, 0, 1))).normalized()
    if nrm.dot(P[i]) < 0: nrm = -nrm
    rows.append([bm.verts.new(M @ (P[i] + (nrm * math.cos(2 * math.pi * j / ring) + Vector((0, 0, 1)) * math.sin(2 * math.pi * j / ring) * 1.25) * rt)) for j in range(ring)])
for i in range(n):
    for j in range(ring):
        bm.faces.new((rows[i][j], rows[(i + 1) % n][j], rows[(i + 1) % n][(j + 1) % ring], rows[i][(j + 1) % ring]))
bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
me = bpy.data.meshes.new("tiara_bezel_pear"); bm.to_mesh(me); bm.free()
for p in me.polygons: p.use_smooth = True
old_bez = O["tiara_bezel"]; col = old_bez.users_collection[0]
pb = bpy.data.objects.new("tiara_bezel_pear", me); col.objects.link(pb)
pb.data.materials.append(GOLD); pb.material_slots[0].link = "OBJECT"; pb.material_slots[0].material = GOLD
# 3 small claw prongs at the tip and the two shoulders
for t in (0.25, 0.62, 0.88):
    p0 = outline(t, wid, lng)
    cb = bmesh.new(); bmesh.ops.create_uvsphere(cb, u_segments=16, v_segments=8, radius=0.0011)
    bmesh.ops.scale(cb, vec=(1, 1, 0.7), verts=cb.verts)
    bmesh.ops.transform(cb, matrix=M @ Matrix.Translation(p0 * 0.97 + Vector((0, 0, 0.0009))), verts=cb.verts)
    pm = bpy.data.meshes.new("tiara_prong"); cb.to_mesh(pm); cb.free()
    for q in pm.polygons: q.use_smooth = True
    po = bpy.data.objects.new("tiara_bezel_prong", pm); col.objects.link(po)
    pm.materials.append(GOLD); po.material_slots[0].link = "OBJECT"; po.material_slots[0].material = GOLD
bpy.data.objects.remove(old_bez)
R["tiara_bezel"] = {"type": "pear tube ring r=%.1f mm + 3 claw prongs (pre-scale)" % (rt * 1000), "replaced": "tiara_bezel (oval torus)"}

# ------------------------------------------------ 2) head -> adult size (15 w, 20 d, 22.5 h cm), sat on the neck
NECK = O["PROXY_neck"]; nmn, nmx = bb(eval_pts(NECK))
TW, TD, TH = 0.150, 0.200, 0.225
S_h = Vector(((TW) / (hmx.x - hmn.x), TD / (hmx.y - hmn.y), TH / (hmx.z - hmn.z)))
anchor_old = Vector(((hmn.x + hmx.x) * 0.5, (hmn.y + hmx.y) * 0.5, hmn.z))
anchor_new = Vector(((nmn.x + nmx.x) * 0.5, (nmn.y + nmx.y) * 0.5 - 0.02, 1.405))
MH = Matrix.Translation(anchor_new) @ Matrix.Diagonal((*S_h, 1)) @ Matrix.Translation(-anchor_old)
H.matrix_world = MH @ H.matrix_world; upd()
nhp = eval_pts(H); nhmn, nhmx = bb(nhp)
R["head_new_mm"] = [mm(v) for v in (nhmx - nhmn)]; R["head_new_min_max"] = [rnd(nhmn), rnd(nhmx)]

bvh = None
def build_bvh():
    global bvh
    global HINV
    dg = bpy.context.evaluated_depsgraph_get(); bvh = BVHTree.FromObject(H, dg); HINV = H.matrix_world.inverted()   # BVH is in head-local space
def inside_count(objs, step=3):
    c = 0; dg = bpy.context.evaluated_depsgraph_get()
    for o in objs:
        if o.type != "MESH": continue
        oe = o.evaluated_get(dg); me_ = oe.to_mesh()
        for i_, v in enumerate(me_.vertices):
            if i_ % step: continue
            p = HINV @ (o.matrix_world @ v.co); hit = bvh.find_nearest(p)
            if hit[0] is not None and (p - hit[0]).dot(hit[1]) < 0: c += 1
        oe.to_mesh_clear()
    return c
def move(objs, dz):
    for o in objs: o.matrix_world = Matrix.Translation((0, 0, dz)) @ o.matrix_world

# ------------------------------------------------ 3) circlet & tiara -> human size, fitted to the new head
CLR = 0.002
def refit(piece, uniform_names, pivot_old, stone_name, target_outer_w=None):
    o = old[piece]; col = bpy.data.collections["REG_" + piece]
    z_new = nhmn.z + o["rel"] * (nhmx.z - nhmn.z)
    hc_n, hx_n, hy_n = head_section(z_new)
    c_old = Vector((o["hc"].x, o["hc"].y, o["bz"])); c_new = Vector((hc_n.x, hc_n.y, z_new))
    if target_outer_w is None:
        # keep the band's original fit to the head (same mapping as the head), then a uniform XY
        # factor so the inner mean diameter is ~180 mm (≈57 cm inner circumference)
        # (the v2b band actually cut ~35 mm into the oversized egg, so the old fit is not reused)
        # inner band = head cross-section + 3 mm clearance per side -> inner mean ~ 176-180 mm
        sx = (hx_n + 0.006) / o["ix"]; sy = (hy_n + 0.006) / o["iy"]
        R[piece + "_fit"] = {"old_inner_x_y_mm": [mm(o["ix"]), mm(o["iy"])], "target_inner_x_y_mm": [mm(hx_n + 0.006), mm(hy_n + 0.006)]}
    else:
        sx = target_outer_w / o["W"]; sy = sx * (hy_n / hx_n) / (o["hy"] / o["hx"])
    sz = (sx + sy) * 0.5; su = sz
    MP = Matrix.Translation(c_new) @ Matrix.Diagonal((sx, sy, sz, 1)) @ Matrix.Translation(-c_old)
    # stone size guard (circlet stone 12-18 mm)
    s_len_old = max(bb(eval_pts(O[stone_name]))[1] - bb(eval_pts(O[stone_name]))[0])
    if piece == "circlet":
        su = min(max(su, 0.012 / s_len_old), 0.018 / s_len_old)
    piv_new = MP @ pivot_old
    MU = Matrix.Translation(piv_new) @ Matrix.Scale(su, 4) @ Matrix.Translation(-pivot_old)
    objs = list(col.objects)
    for ob in objs:
        ob.matrix_world = (MU if ob.name in uniform_names or ob.name.startswith(tuple(uniform_names)) else MP) @ ob.matrix_world
    upd(); build_bvh()
    # settle: lower from 30 mm above until the band touches the head, then back off 0.5 mm
    meshes = [ob for ob in objs if ob.type == "MESH"]
    dz_total = 0.0; steps = 0
    if inside_count(meshes) > 0:          # penetrating at the fitted height -> raise until clear (max 40 mm)
        while inside_count(meshes) > 0 and steps < 40:
            move(objs, 0.001); upd(); dz_total += 0.001; steps += 1
        move(objs, 0.0005); upd(); dz_total += 0.0005
    else:                                 # clear -> lower until contact (max 30 mm), then back off
        while inside_count(meshes) == 0 and steps < 30:
            move(objs, -0.001); upd(); dz_total -= 0.001; steps += 1
        if steps >= 30: move(objs, 0.03); upd(); dz_total = 0.0; R["notes"].append(piece + ": no contact within 30 mm below fit, kept fitted height")
        else: move(objs, 0.0015); upd(); dz_total += 0.0015
    print("V2D-SETTLE", piece, "steps", steps, "dz_mm", round(dz_total * 1000, 1), "z_new", round(z_new, 4), "sx sy", round(sx, 4), round(sy, 4))
    pen = inside_count(meshes, 1)
    gp = eval_pts(O[piece + "_gold"]); gmn, gmx = bb(gp)
    bzn = (gmn.z + gmx.z) * 0.5 if piece == "circlet" else gmn.z + 0.006 * sz
    hc2, hx2, hy2 = head_section(bzn)
    ix, iy, imean, nb = inner_spans(O[piece + "_gold"], bzn, Vector((hc2.x, hc2.y, bzn)), (gmx.z - gmn.z) * 0.5 if piece == "circlet" else 0.006 * sz)
    smn, smx = bb(eval_pts(O[stone_name]))
    R[piece + "_new"] = {"scale_xyz": [round(sx, 4), round(sy, 4), round(sz, 4)], "stone_scale": round(su, 4),
        "outer_mm": [mm(gmx.x - gmn.x), mm(gmx.y - gmn.y), mm(gmx.z - gmn.z)], "inner_x_y_mm": [ix and mm(ix), iy and mm(iy)], "inner_mean_diam_mm": mm(imean),
        "head_section_mm": [mm(hx2), mm(hy2)], "settle_dz_from_fit_mm": mm(dz_total - 0.0), "head_penetrating_verts": pen,
        "band_rel_height": round((bzn - nhmn.z) / (nhmx.z - nhmn.z), 3), "stone_bbox_mm": [mm(v) for v in (smx - smn)], "stone_len_mm": mm(max(smx - smn))}

cs = O["circlet_stone"]; cmn, cmx = bb(eval_pts(cs))
refit("circlet", {"circlet_stone", "circlet_bezel"}, (cmn + cmx) * 0.5, "circlet_stone")
tmn, tmx = bb(eval_pts(O["tiara_stone"]))
foot = Vector(((tmn.x + tmx.x) * 0.5, (tmn.y + tmx.y) * 0.5, old["tiara"]["gmx"].z))
refit("tiara", {"tiara_stone", "tiara_bezel", "tiara_spire", "tiara_prong"}, foot, "tiara_stone", target_outer_w=0.155)

# ------------------------------------------------ 4) earrings: same size, moved to the new ear positions
ec = Vector(((nhmn.x + nhmx.x) * 0.5, (nhmn.y + nhmx.y) * 0.5, nhmn.z + 0.42 * (nhmx.z - nhmn.z)))
for side, sgn in (("earL", 1), ("earR", -1)):
    stud = O[side + "_stud"]; sc_old = stud.matrix_world.translation.copy()
    hc_e, hx_e, hy_e = head_section(ec.z)
    tgt = Vector((hc_e.x + sgn * (hx_e * 0.5 + 0.004), hc_e.y + 0.01, ec.z))
    d = tgt - sc_old
    for ob in bpy.data.collections["REG_earrings"].objects:
        if ob.name.startswith(side): ob.matrix_world = Matrix.Translation(d) @ ob.matrix_world
    R[side + "_moved_mm"] = [mm(v) for v in d]
R["notes"].append("earrings/necklace unchanged in size; earrings translated to the new ears")

# ------------------------------------------------ 5) materials baked: aquamarine (v2b render-time fix) + deeper Void Orchid
def gem_mat(name, base, absorb_col, dens, disp):
    m = bpy.data.materials[name]; nt = m.node_tree
    b = [x for x in nt.nodes if x.type == "BSDF_PRINCIPLED"][0]; out = [x for x in nt.nodes if x.type == "OUTPUT_MATERIAL"][0]
    b.inputs["Base Color"].default_value = base + (1,)
    try: b.inputs["Dispersion"].default_value = disp
    except Exception: pass
    for x in [x for x in nt.nodes if x.type == "VOLUME_ABSORPTION"]: nt.nodes.remove(x)
    va = nt.nodes.new("ShaderNodeVolumeAbsorption"); va.inputs["Color"].default_value = absorb_col + (1,); va.inputs["Density"].default_value = dens
    nt.links.new(va.outputs[0], out.inputs["Volume"])
    R.setdefault("materials", {})[name] = {"base": base, "absorb": absorb_col, "density_per_m": dens, "dispersion": disp}
gem_mat("V2_Stone_Aquamarine_Dream", (0.52, 0.78, 1.0), (0.52, 0.78, 1.0), 14.0, 0.15)
gem_mat("V2_Stone_Void_Orchid", (0.72, 0.42, 0.92), (0.74, 0.36, 0.86), 70.0, 0.08)   # it1 (0.60,0.34,0.92)/(0.52,0.22,0.90)x55 read indigo

# ------------------------------------------------ 6) cap the open tube ends of the house gold (orange inter-reflection specks)
for gname in ("circlet_gold", "tiara_gold"):
    g = O[gname]; g.data = g.data.copy(); g.data.name = gname + "_v2d_capped"
    bm_ = bmesh.new(); bm_.from_mesh(g.data)
    nb = sum(1 for e in bm_.edges if e.is_boundary)
    r_ = bmesh.ops.holes_fill(bm_, edges=[e for e in bm_.edges if e.is_boundary], sides=24)
    for f in r_["faces"]: f.smooth = True
    bm_.to_mesh(g.data); bm_.free()
    R.setdefault("tube_caps", {})[gname] = {"boundary_edges": nb, "caps": len(r_["faces"])}
R["notes"].append("stones scaled with pieces; tiara spire/stone/bezel scaled uniformly about the spire foot; gold scaled non-uniformly to fit the head")
bpy.ops.wm.save_as_mainfile(filepath=OUTBLEND, copy=True)
json.dump(R, open(RECEIPT, "w"), indent=1, default=str)
print("V2D-RECEIPT", json.dumps(R, default=str))
print("V2D-SAVED", OUTBLEND)
