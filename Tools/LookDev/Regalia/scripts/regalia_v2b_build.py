"""regalia_v2_build.py -- non-destructive lookdev rebuild of Melusina's 4 regalia pieces.

Runs in a NEW headless Blender:  blender -b --factory-startup --python regalia_v2_build.py
Uses COPIES of the original scripts (./scripts) and of deploy/surreal_arch (../pkg).
Writes ONLY: ../regalia_v2.blend and ../regalia_v2_build_receipt.json

What it does, per piece
  circlet / tiara : original baroque builders (house GN, bevel-offset fix intact) ->
                    realize -> strip the 68-face house stone -> seat a real faceted
                    brilliant (bmesh) in a gold bezel at the same spot, on its OWN
                    object with the stone material on the OBJECT slot.
  earrings        : original builder's world placement (EAR_L/EAR_R) kept; the house
                    crystal_drop parts (degenerate 12-vert slivers + 1024-v loops that
                    float 1-4 cm ABOVE the lobe) are replaced with a linked assembly:
                    stud -> jump ring -> bezel stone -> jump ring -> capped pear drop.
  necklace        : original bead collar kept (34 beads); the stray 128-v cord shell,
                    16-v stub and floating 1024-v loop are removed; a new continuous
                    cord threads every bead and droops across the front gap; a bail
                    ring hangs ON the cord and a capped pear pendant hangs from it.
  dangles         : house dangle builders realized and their 1 m strand islands
                    clamped on Z only (receipt only; not used on the 4 pieces).
"""
import bpy, bmesh, sys, os, math, json
from mathutils import Vector, Matrix

W = r"C:\EnvironmentPortfolio\_lookdev_work\regalia_v2"
SCRIPTS = os.path.join(W, "scripts")
PKG = os.path.join(W, "pkg")
BLEND = os.path.join(W, "regalia_v2b.blend")
RECEIPT = {"pieces": {}, "notes": []}
ARGS = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
GEM_LEN = float(ARGS[0]) if ARGS else 0.016      # earring main drop length (m)

sys.path.insert(0, SCRIPTS)
import regalia_baroque_build as RB
RB.REPO_GN = PKG                  # our COPY of the house package
RB.APPDATA_GN = r"Z:\__none__"    # never the installed addon
RB._import_house()
import surreal_arch
RECEIPT["house_package"] = surreal_arch.__file__
import regalia_earring_build as RE
import regalia_necklace_build as RN

# ------------------------------------------------------------------ scene
bpy.ops.wm.read_factory_settings(use_empty=True)
scene = bpy.context.scene
ROOT = scene.collection

def coll(name, parent=None):
    c = bpy.data.collections.get(name) or bpy.data.collections.new(name)
    if c.name not in [x.name for x in (parent or ROOT).children]:
        (parent or ROOT).children.link(c)
    return c

# ------------------------------------------------------------------ materials
def _set(n, key, val):
    s = n.inputs.get(key)
    if s is None: return False
    try: s.default_value = val; return True
    except Exception: return False

def mat_gold():
    m = bpy.data.materials.get("V2_Gold") or bpy.data.materials.new("V2_Gold")
    m.use_nodes = True; nt = m.node_tree; nt.nodes.clear()
    out = nt.nodes.new("ShaderNodeOutputMaterial"); b = nt.nodes.new("ShaderNodeBsdfPrincipled")
    _set(b, "Base Color", (1.0, 0.72, 0.33, 1)); _set(b, "Metallic", 1.0)
    _set(b, "Specular Tint", (1.0, 0.86, 0.6, 1))
    tc = nt.nodes.new("ShaderNodeTexCoord"); nz = nt.nodes.new("ShaderNodeTexNoise")
    _set(nz, "Scale", 900.0); _set(nz, "Detail", 4.0)
    nt.links.new(tc.outputs["Object"], nz.inputs["Vector"])
    mr = nt.nodes.new("ShaderNodeMapRange")
    _set(mr, "To Min", 0.13); _set(mr, "To Max", 0.27)
    nt.links.new(nz.outputs["Fac"], mr.inputs["Value"]); nt.links.new(mr.outputs["Result"], b.inputs["Roughness"])
    nt.links.new(b.outputs["BSDF"], out.inputs["Surface"])
    return m

STONES = {  # tint, ior, thin film nm -- no emission (lookdev: no emissive noise)
    "Aquamarine Dream": ((0.72, 0.87, 1.0), 1.577, 0.0),
    "Void Orchid":      ((0.74, 0.44, 0.96), 1.76, 0.0),
    "Moon Opal":        ((0.80, 0.78, 0.95), 1.60, 380.0),
}
def mat_stone(key):
    name = "V2_Stone_" + key.replace(" ", "_")
    m = bpy.data.materials.get(name) or bpy.data.materials.new(name)
    m.use_nodes = True; nt = m.node_tree; nt.nodes.clear()
    tint, ior, film = STONES[key]
    out = nt.nodes.new("ShaderNodeOutputMaterial"); b = nt.nodes.new("ShaderNodeBsdfPrincipled")
    _set(b, "Base Color", tint + (1,)); _set(b, "Roughness", 0.0); _set(b, "IOR", ior)
    _set(b, "Transmission Weight", 1.0) or _set(b, "Transmission", 1.0)
    _set(b, "Dispersion", 0.35)
    if film: _set(b, "Thin Film Thickness", film); _set(b, "Thin Film IOR", 1.45)
    # absorption so the body colour deepens with thickness
    nt.links.new(b.outputs["BSDF"], out.inputs["Surface"])   # (v2a used Volume Absorption = complementary orange; removed)
    return m

def mat_matte(name, rgb, rough=0.62):
    m = bpy.data.materials.get(name) or bpy.data.materials.new(name)
    m.use_nodes = True; b = m.node_tree.nodes.get("Principled BSDF")
    _set(b, "Base Color", rgb + (1,)); _set(b, "Roughness", rough)
    return m

GOLD = mat_gold()

def put(ob, mat):
    """Material on the OBJECT slot (link='OBJECT'), so it cannot be lost by mesh re-evaluation."""
    ob.data.materials.clear(); ob.data.materials.append(mat)
    ob.material_slots[0].link = "OBJECT"; ob.material_slots[0].material = mat

# ------------------------------------------------------------------ geometry helpers
def new_obj(name, bm, c, smooth=False):
    me = bpy.data.meshes.new(name); bm.to_mesh(me); bm.free()
    for p in me.polygons: p.use_smooth = smooth
    ob = bpy.data.objects.new(name, me); c.objects.link(ob); return ob

def gem_bm(length, width, kind="pear", n=16, table=0.56, crown=0.16, pav=0.46, girdle=0.02):
    """A faceted brilliant built in XY (table up +Z), long axis +Y for 'pear'.
    length/width in metres. Flat shaded -> every facet reads."""
    bm = bmesh.new()
    def outline(t):  # t in [0,1)
        a = 2 * math.pi * t
        x, y = math.cos(a), math.sin(a)
        if kind == "pear":   # pointed toward +Y
            k = 0.5 * (1 + y); x *= (1 - 0.55 * k ** 2.2)
        return x * width * 0.5, y * length * 0.5
    size = max(length, width)
    zt = crown * size; zg = girdle * size * 0.5; zc = -pav * size
    ring_top = [bm.verts.new((*outline(i / n), zg)) for i in range(n)]
    ring_bot = [bm.verts.new((*outline(i / n), -zg)) for i in range(n)]
    tab = [bm.verts.new((outline((i + 0.5) / n)[0] * table, outline((i + 0.5) / n)[1] * table, zt)) for i in range(n)]
    # star facets between girdle and table
    for i in range(n):
        j = (i + 1) % n
        bm.faces.new((ring_bot[i], ring_bot[j], ring_top[j], ring_top[i]))       # girdle
        bm.faces.new((ring_top[i], ring_top[j], tab[i]))                         # upper girdle
        bm.faces.new((tab[i], ring_top[j], tab[j]))                              # star
    bm.faces.new(tab)                                                            # table
    cul = bm.verts.new((0, 0, zc))
    mid = [bm.verts.new((outline(i / n)[0] * 0.45, outline(i / n)[1] * 0.45, zc * 0.55)) for i in range(n)]
    for i in range(n):
        j = (i + 1) % n
        bm.faces.new((ring_bot[j], ring_bot[i], mid[i], mid[j])) if i % 2 == 0 else \
            bm.faces.new((ring_bot[j], ring_bot[i], mid[i], mid[j]))
        bm.faces.new((mid[j], mid[i], cul))
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    return bm

def torus_bm(R, r, seg=48, ring=16):
    bm = bmesh.new()
    bmesh.ops.create_circle  # noqa
    verts = []
    for i in range(seg):
        a = 2 * math.pi * i / seg
        row = []
        for j in range(ring):
            b = 2 * math.pi * j / ring
            p = Vector(((R + r * math.cos(b)) * math.cos(a), (R + r * math.cos(b)) * math.sin(a), r * math.sin(b)))
            row.append(bm.verts.new(p))
        verts.append(row)
    for i in range(seg):
        for j in range(ring):
            a, b = verts[i][j], verts[(i + 1) % seg][j]
            c, d = verts[(i + 1) % seg][(j + 1) % ring], verts[i][(j + 1) % ring]
            bm.faces.new((a, b, c, d))
    return bm

def sphere_bm(r, seg=48, rings=24):
    bm = bmesh.new(); bmesh.ops.create_uvsphere(bm, u_segments=seg, v_segments=rings, radius=r); return bm

def cone_bm(r1, r2, h, seg=32):
    bm = bmesh.new(); bmesh.ops.create_cone(bm, cap_ends=True, segments=seg, radius1=r1, radius2=r2, depth=h); return bm

def xf(bm, M):
    bmesh.ops.transform(bm, matrix=M, verts=bm.verts); return bm

def look(frm_axis, to_vec):
    return frm_axis.rotation_difference(to_vec.normalized()).to_matrix().to_4x4()

def frame(z, yhint=Vector((0, 0, 1))):
    """Basis with local +Z -> z and local +Y as close to yhint as possible."""
    z = z.normalized(); y = (yhint - z * yhint.dot(z)).normalized(); x = y.cross(z)
    M = Matrix((x, y, z)).transposed(); return M.to_4x4()

def add_subsurf(ob, lv=2):
    m = ob.modifiers.new("smooth", "SUBSURF"); m.levels = lv; m.render_levels = lv; return m

# ------------------------------------------------------------------ realize a GN tree
def realize_tree(tree):
    if isinstance(tree, (tuple, list)): tree = tree[0]
    gout = [n for n in tree.nodes if n.bl_idname == "NodeGroupOutput"][0]
    s = gout.inputs["Geometry"]
    if s.is_linked:
        src = s.links[0].from_socket
        r = tree.nodes.new("GeometryNodeRealizeInstances")
        tree.links.new(src, r.inputs["Geometry"]); tree.links.new(r.outputs["Geometry"], s)
    return tree

SRC = coll("_GN_source_hidden")
def evaluate(name, tree):
    tree = realize_tree(tree)
    host = bpy.data.objects.new(name + "_GNhost", bpy.data.meshes.new(name + "_GNhost"))
    SRC.objects.link(host)
    md = host.modifiers.new("regalia", "NODES"); md.node_group = tree
    dg = bpy.context.evaluated_depsgraph_get()
    me = bpy.data.meshes.new_from_object(host.evaluated_get(dg))
    me.name = name + "_realized"
    host.hide_render = True; host.hide_viewport = True
    return me, tree

def islands(bm):
    bm.verts.ensure_lookup_table(); seen = set(); out = []
    for v in bm.verts:
        if v.index in seen: continue
        st = [v]; seen.add(v.index); comp = []
        while st:
            x = st.pop(); comp.append(x)
            for e in x.link_edges:
                o = e.other_vert(x)
                if o.index not in seen: seen.add(o.index); st.append(o)
        out.append(comp)
    return out

def bbox(vs):
    cs = [v.co if hasattr(v, "co") else v for v in vs]
    mn = Vector([min(c[i] for c in cs) for i in range(3)]); mx = Vector([max(c[i] for c in cs) for i in range(3)])
    return mn, mx

def bevel_offsets_report(tree, depth=0, seen=None):
    """Every Mesh Bevel node's Start/End Left/Right Offset values (must be 0, not 0.1)."""
    seen = seen or set(); rep = []
    if tree is None or tree.name in seen: return rep
    seen.add(tree.name)
    for n in tree.nodes:
        if n.bl_idname == "GeometryNodeGroup": rep += bevel_offsets_report(n.node_tree, depth + 1, seen)
        elif "Bevel" in n.bl_idname:
            vals = {k: round(n.inputs[k].default_value, 4) for k in ("Start Left Offset", "Start Right Offset", "End Left Offset", "End Right Offset") if n.inputs.get(k) is not None}
            if vals: rep.append((tree.name, n.name, vals))
    return rep

# ------------------------------------------------------------------ headpieces
TIARA_STONE_Z = 1.838      # stone lifted above the crown band, held by the spire

def taper_curve(name, c, pts, r0, r1, res=24):
    """A smooth gold curve through pts, radius tapering r0 -> r1 (point radius drives bevel)."""
    cu = bpy.data.curves.new(name, "CURVE"); cu.dimensions = "3D"
    cu.bevel_depth = 1.0; cu.bevel_resolution = 8; cu.resolution_u = res
    sp = cu.splines.new("NURBS"); sp.points.add(len(pts) - 1); sp.order_u = min(4, len(pts)); sp.use_endpoint_u = True
    for i, (p, q) in enumerate(zip(sp.points, pts)):
        t = i / (len(pts) - 1); p.co = (q.x, q.y, q.z, 1); p.radius = r0 + (r1 - r0) * t
    o = bpy.data.objects.new(name, cu); c.objects.link(o); cu.materials.append(GOLD); return o

def tiara_spire(c, ctr, out, L, Wd, band_top):
    """Replaces the ribbed crest: two tapered arms rise from the band, sweep around the stone
    as a teardrop frame and meet in a finial above it -- the stone is HELD, not perched."""
    z_ax = out; side = Vector((1, 0, 0)); up = Vector((0, 0, 1))
    base_y = ctr - out * 0.0015
    gw = Wd * 0.5 + 0.0022; gl = L * 0.5 + 0.0022
    arms = []
    for sgn in (-1, 1):
        pts = [Vector((ctr.x + sgn * 0.014, base_y.y, band_top - 0.002)),
               Vector((ctr.x + sgn * 0.011, base_y.y, band_top + 0.006)),
               Vector((ctr.x + sgn * gw * 1.05, base_y.y, ctr.z - gl * 0.55)),
               Vector((ctr.x + sgn * gw * 1.08, base_y.y, ctr.z + gl * 0.15)),
               Vector((ctr.x + sgn * gw * 0.55, base_y.y, ctr.z + gl * 0.85)),
               Vector((ctr.x + sgn * 0.0012, base_y.y, ctr.z + gl * 1.25)),
               Vector((ctr.x, base_y.y, ctr.z + gl * 1.55))]
        arms.append(taper_curve("tiara_spire_arm_%s" % ("L" if sgn < 0 else "R"), c, pts, 0.0019, 0.0007))
    tip = ctr.z + gl * 1.55
    # finial: small bead + a fine tapered spike
    b = sphere_bm(0.0024, 32, 16); xf(b, Matrix.Translation((ctr.x, base_y.y, tip + 0.0018)))
    fin = new_obj("tiara_spire_finial", b, c, smooth=True); put(fin, GOLD)
    taper_curve("tiara_spire_tip", c, [Vector((ctr.x, base_y.y, tip + 0.003)), Vector((ctr.x, base_y.y, tip + 0.012)),
                                       Vector((ctr.x, base_y.y, tip + 0.022))], 0.0011, 0.0002)
    # two small scroll curls at the foot, echoing the band filigree
    for sgn in (-1, 1):
        pts = [Vector((ctr.x + sgn * 0.012, base_y.y, band_top)), Vector((ctr.x + sgn * 0.026, base_y.y, band_top + 0.004)),
               Vector((ctr.x + sgn * 0.034, base_y.y, band_top + 0.012)), Vector((ctr.x + sgn * 0.028, base_y.y, band_top + 0.017)),
               Vector((ctr.x + sgn * 0.023, base_y.y, band_top + 0.012))]
        taper_curve("tiara_spire_curl_%s" % ("L" if sgn < 0 else "R"), c, pts, 0.0014, 0.0006)
    return {"type": "teardrop frame + finial", "tip_z": round(tip + 0.022, 4), "stone_z": round(ctr.z, 4)}
def headpiece(piece, stone_key):
    c = coll("REG_" + piece)
    me, tree = evaluate(piece, RB.build_piece("MEL_regalia_" + piece))
    bev = bevel_offsets_report(tree)
    stone_idx = [i for i, m in enumerate(me.materials) if m and m.name.startswith("REGALIA_STONE")]
    bm = bmesh.new(); bm.from_mesh(me)
    sf = [f for f in bm.faces if f.material_index in stone_idx]
    sv = {v for f in sf for v in f.verts}
    mn, mx = bbox(sv) if sv else (None, None)
    bmesh.ops.delete(bm, geom=sf, context="FACES")
    loose = [v for v in bm.verts if not v.link_faces]
    bmesh.ops.delete(bm, geom=loose, context="VERTS")
    for f in bm.faces: f.material_index = 0; f.smooth = True
    seated = []
    isl_all = islands(bm)
    main = max(isl_all, key=len); bmn, bmx = bbox(main)
    for isl_ in isl_all:
        if isl_ is main: continue
        mn_, mx_ = bbox(isl_)
        gap = mn_.z - bmx.z
        if len(isl_) < 400 and gap > 0.002:
            # House fan-spire rods/tips hover 6-57 mm above the band with nothing under them
            # (v1 read them as floating stubs). Seating them read worse (dots on the scalp), so
            # they are REMOVED rather than faked.
            seated.append((len(isl_), round(gap * 1000, 1)))
            bmesh.ops.delete(bm, geom=list(isl_), context="VERTS")
    crest_removed = []
    if piece == "tiara":
        for isl_ in islands(bm):
            if isl_ is main or not isl_[0].is_valid: continue
            mn_, mx_ = bbox(isl_)
            if mx_.z - bmx.z > 0.015:
                crest_removed.append((len(isl_), round((mx_.z - bmx.z) * 1000, 1)))
                bmesh.ops.delete(bm, geom=list(isl_), context="VERTS")
    ob = bpy.data.objects.new(piece + "_gold", bpy.data.meshes.new(piece + "_gold")); c.objects.link(ob)
    bm.to_mesh(ob.data); bm.free()
    ob.data.set_sharp_from_angle(angle=math.radians(50))
    put(ob, GOLD)
    add_subsurf(ob, 2)           # kills the tube faceting/banding seen in v1 macros
    info = {"gold_verts": len(ob.data.vertices), "house_stone_faces_removed": len(sf), "bevel_offsets": bev,
            "floating_finials_removed_(verts,gap_mm)": seated, "crest_islands_removed_(verts,rise_mm)": crest_removed}
    if mn is not None:
        ctr = (mn + mx) * 0.5; size = max(mx - mn)
        # The house nikki crystal is a tall double-terminated spike (bbox %.0f mm), which is why
        # v1 read as a cone standing on the band. Seat a real stone ON the band face instead.
        band_z = {"circlet": 1.566, "tiara": 1.812}[piece]
        ctr = Vector((ctr.x, ctr.y, band_z))
        info_house_bbox_mm = [round(v * 1000, 1) for v in (mx - mn)]
        # face outward from the head centre, tilted slightly up
        head_c = Vector((RB.BROW_CX, RB.BROW_CY, ctr.z))
        out = (ctr - head_c); out.z = 0; out.normalize(); out = (out + Vector((0, 0, 0.25))).normalized()
        L = 0.036 if piece == "circlet" else 0.028; Wd = L * 0.78
        if piece == "tiara":
            ctr = Vector((ctr.x, ctr.y, TIARA_STONE_Z))
        # push the girdle plane just proud of the band's frontmost gold at this height
        me_g = ob.data
        near = [ (ob.matrix_world @ v.co) for v in me_g.vertices
                 if abs(v.co.x - ctr.x) < L * 0.5 and abs(v.co.z - ctr.z) < L * 0.5 ]
        if near:
            front = max(p_.dot(out) for p_ in near)
            ctr = ctr + out * (front - ctr.dot(out) + 0.0015)
        info_front_offset_mm = round((front - ctr.dot(out)) * 1000, 2) if near else None
        g = gem_bm(L, Wd, kind="oval" if piece == "circlet" else "pear")
        M = Matrix.Translation(ctr) @ frame(out)
        # pear tip should point UP the face of the tiara
        xf(g, M)
        gem = new_obj(piece + "_stone", g, c); put(gem, mat_stone(stone_key))
        # bezel: gold ring around the girdle + 4 prongs, same frame
        bz = torus_bm(1.0, 0.07, 64, 12)
        xf(bz, M @ Matrix.Diagonal((Wd * 0.5 * 1.04, L * 0.5 * 1.04, Wd * 0.5, 1.0)))
        bez = new_obj(piece + "_bezel", bz, c, smooth=True); put(bez, GOLD)
        info.update({"stone": stone_key, "stone_center": [round(v, 4) for v in ctr], "stone_len_mm": round(L * 1000, 1), "house_stone_bbox_mm": info_house_bbox_mm,
                     "stone_object_slot": gem.material_slots[0].material.name, "stone_slot_link": gem.material_slots[0].link,
                     "stone_proud_of_band_mm": 1.5})
        if piece == "tiara":
            info["spire"] = tiara_spire(c, ctr, out, L, Wd, bmx.z)
    RECEIPT["pieces"][piece] = info
    return c

# ------------------------------------------------------------------ earrings
def gem_on_axis(name, c, length, width, top, kind, key, facing=Vector((0, -1, 0))):
    """Gem hanging DOWN from `top`, table facing `facing`, long axis -Z (tip down)."""
    g = gem_bm(length, width, kind=kind)
    # gem local: long axis +Y (pear tip at +Y), table +Z.  want tip -> -Z, table -> facing
    R = Matrix(((1, 0, 0), (0, 0, 1), (0, -1, 0))).to_4x4()   # +Y -> -Z , +Z -> +Y
    if facing.y < 0: R = Matrix.Rotation(math.pi, 4, "Z") @ R  # table toward -Y
    ctr = top - Vector((0, 0, length * 0.5))
    xf(g, Matrix.Translation(ctr) @ R)
    ob = new_obj(name, g, c); put(ob, mat_stone(key)); return ob, ctr

def cap(name, c, top, r, h):
    """Gold cup over the top of a drop; touches the bail above and the gem below."""
    b = cone_bm(r * 0.35, r, h, 32); xf(b, Matrix.Translation(top - Vector((0, 0, h * 0.5))) @ Matrix.Rotation(math.pi, 4, "X"))
    ob = new_obj(name, b, c, smooth=True); put(ob, GOLD); add_subsurf(ob, 1); return ob

def ring(name, c, ctr, R, r, axis):
    b = torus_bm(R, r); rot = look(Vector((0, 0, 1)), axis)
    xf(b, Matrix.Translation(ctr) @ rot); ob = new_obj(name, b, c, smooth=True); put(ob, GOLD); return ob

def earrings(stone_key="Void Orchid", main_len=GEM_LEN):
    c = coll("REG_earrings")
    me, tree = evaluate("earrings", RE.build_regalia_earring_pair())
    bm = bmesh.new(); bm.from_mesh(me); isl = islands(bm)
    removed = [len(i) for i in isl if len(i) != 200]
    studs = []
    for i in isl:
        if len(i) == 200:
            mn, mx = bbox(i); studs.append(((mn + mx) * 0.5, (mx - mn).x * 0.5))
    bm.free()
    parts = {}
    for tag, (sc, sr) in zip(("L", "R"), sorted(studs, key=lambda s: -s[0].x)):
        s = new_obj("ear%s_stud" % tag, sphere_bm(sr, 48, 24), c, smooth=True)
        s.location = sc; put(s, GOLD)
        rr, rt = 0.0022, 0.00055
        r1c = sc - Vector((0, 0, sr + rr - rt * 0.5))
        ring("ear%s_ring1" % tag, c, r1c, rr, rt, Vector((1, 0, 0)))          # ring plane YZ, hooks the stud
        # bezel-set round stone
        br = 0.0034
        bz_top = r1c - Vector((0, 0, rr - rt * 0.4))
        bctr = bz_top - Vector((0, 0, br + 0.0008))
        g = gem_bm(br * 2, br * 2, kind="round"); R = Matrix(((1, 0, 0), (0, 0, 1), (0, -1, 0))).to_4x4()
        xf(g, Matrix.Translation(bctr) @ Matrix.Rotation(math.pi, 4, "Z") @ R)
        gs = new_obj("ear%s_stone_round" % tag, g, c); put(gs, mat_stone(stone_key))
        ring("ear%s_bezel" % tag, c, bctr, br * 1.02, 0.0006, Vector((0, 1, 0)))
        ring("ear%s_loopTop" % tag, c, bctr + Vector((0, 0, br + 0.0008)), 0.0009, 0.00035, Vector((0, 1, 0)))
        lb = bctr - Vector((0, 0, br + 0.0008))
        ring("ear%s_loopBot" % tag, c, lb, 0.0009, 0.00035, Vector((0, 1, 0)))
        r2c = lb - Vector((0, 0, 0.0009 + 0.0016 - 0.0006))
        ring("ear%s_ring2" % tag, c, r2c, 0.0016, 0.0004, Vector((1, 0, 0)))
        ctop = r2c - Vector((0, 0, 0.0016 - 0.0003))
        cap("ear%s_cap" % tag, c, ctop, main_len * 0.62 * 0.5 * 0.55, 0.0028)
        gem_on_axis("ear%s_stone_drop" % tag, c, main_len, main_len * 0.62, ctop - Vector((0, 0, 0.0022)), "pear", stone_key)
        parts[tag] = [round(v, 4) for v in sc]
    RECEIPT["pieces"]["earrings"] = {"house_islands_removed_sizes": removed, "studs_kept": len(studs), "stud_centres": parts,
                                     "drop_len_mm": round(main_len * 1000, 1), "stone": stone_key}
    return c

# ------------------------------------------------------------------ necklace
def necklace(stone_key="Void Orchid", pend_len=0.025):
    c = coll("REG_necklace")
    me, tree = evaluate("necklace", RN.build_regalia_necklace_group())
    bm = bmesh.new(); bm.from_mesh(me); isl = islands(bm)
    keep = [i for i in isl if len(i) == 222]
    drop = [i for i in isl if len(i) != 222]
    dropped = sorted(len(i) for i in drop)
    beads = []
    for i in keep:
        mn, mx = bbox(i); beads.append(((mn + mx) * 0.5, max(mx - mn) * 0.5))
    zs = [((bbox(i)[0] + bbox(i)[1]) * 0.5).z for i in keep]; zhi, zlo = max(zs), min(zs)
    for i in keep:   # house Droop sags at the arc MIDDLE = her back; mirror it so the front sits low
        zc_ = ((bbox(i)[0] + bbox(i)[1]) * 0.5).z; dz = (zhi + zlo - zc_) - zc_
        for v in i: v.co.z += dz
    for i in keep:   # house beads are 23 mm -- a fat torc. 0.45x -> ~10 mm beads with the cord visible between
        c_ = (bbox(i)[0] + bbox(i)[1]) * 0.5
        for v in i: v.co = c_ + (v.co - c_) * 0.45
    beads = [((bbox(i)[0] + bbox(i)[1]) * 0.5, max(bbox(i)[1] - bbox(i)[0]) * 0.5) for i in keep]
    kill = [v for i in drop for v in i]
    bmesh.ops.delete(bm, geom=kill, context="VERTS")
    for f in bm.faces: f.smooth = True; f.material_index = 0
    ob = bpy.data.objects.new("necklace_beads", bpy.data.meshes.new("necklace_beads")); c.objects.link(ob)
    bm.to_mesh(ob.data); bm.free(); put(ob, GOLD); add_subsurf(ob, 1)
    # order beads around the collar centre
    cc = Vector((0, -0.012, 0))
    def ang(p): v = p[0] - cc; return math.atan2(v.y, v.x) % (2 * math.pi)
    beads.sort(key=ang)
    angs = [ang(b) for b in beads]
    gaps = [((angs[(k + 1) % len(angs)] - angs[k]) % (2 * math.pi), k) for k in range(len(angs))]
    g, k = max(gaps)
    order = beads[k + 1:] + beads[:k + 1]          # starts after the gap, ends before it
    A, B = order[-1][0], order[0][0]               # the two ends that face the gap
    br = sum(b[1] for b in beads) / len(beads)
    mid = (A + B) * 0.5
    low = mid + Vector((0, -0.022, -0.026))        # droop across the throat, slightly forward
    pts = [b[0] for b in order]
    # front span: A -> low -> B, as a smooth curve
    span = []
    for t in [i / 12 for i in range(1, 12)]:
        p = (1 - t) ** 2 * A + 2 * (1 - t) * t * (low + (low - mid)) + t ** 2 * B  # quadratic bezier through ~low
        span.append(p)
    cu = bpy.data.curves.new("necklace_cord", "CURVE"); cu.dimensions = "3D"
    cu.bevel_depth = 0.0010; cu.bevel_resolution = 6; cu.resolution_u = 24
    sp = cu.splines.new("NURBS"); allp = pts + span
    sp.points.add(len(allp) - 1)
    for p, q in zip(sp.points, allp): p.co = (q.x, q.y, q.z, 1)
    sp.use_cyclic_u = True; sp.order_u = 4
    cord = bpy.data.objects.new("necklace_cord", cu); c.objects.link(cord)
    cord.data.materials.append(GOLD)
    # lowest point of the evaluated cord = where the bail hangs
    dg = bpy.context.evaluated_depsgraph_get()
    cme = cord.evaluated_get(dg).to_mesh(); lowv = min((v.co for v in cme.vertices if v.co.y < cc.y - 0.05 and abs(v.co.x) < 0.02), key=lambda v: v.z).copy()
    cord.evaluated_get(dg).to_mesh_clear()
    cord_low = lowv + Vector((0, 0, 0.0011))       # centreline
    bailR, bailr = 0.0034, 0.0008
    bail_c = cord_low - Vector((0, 0, bailR - 0.0011 - bailr * 0.2))
    ring("necklace_bail", c, bail_c, bailR, bailr, Vector((1, 0, 0)))   # cord passes THROUGH the ring
    ctop = bail_c - Vector((0, 0, bailR - bailr * 0.5))
    cap("necklace_cap", c, ctop, pend_len * 0.64 * 0.5 * 0.5, 0.0036)
    gem, gc = gem_on_axis("necklace_pendant", c, pend_len, pend_len * 0.64, ctop - Vector((0, 0, 0.003)), "pear", stone_key)
    RECEIPT["pieces"]["necklace"] = {"beads_kept": len(keep), "islands_removed_sizes": dropped,
                                     "cord": "continuous NURBS through all beads + front droop, r=1.1 mm",
                                     "bail_on_cord_gap_mm": round((bail_c.z + bailR - bailr) * 1000 - cord_low.z * 1000, 2),
                                     "pendant_len_mm": round(pend_len * 1000, 1), "stone": stone_key,
                                     "pendant_centre": [round(v, 4) for v in gc], "gap_deg": round(math.degrees(g), 1),
                                     "gap_ends": [[round(v, 4) for v in A], [round(v, 4) for v in B]]}
    return c

# ------------------------------------------------------------------ dangles: Z-only clamp
def dangles(target=0.03):
    c = coll("_Dangles_clamped_hidden"); rep = {}
    import importlib
    cd = importlib.import_module("surreal_arch.melodia_gn.cute_decor")
    for i, bn in enumerate(("build_star_dangl", "build_lace_dangl", "build_tassel_dangl")):
        f = getattr(cd, bn, None)
        if f is None: rep[bn] = "missing"; continue
        try:
            me, _ = evaluate(bn, f(bn))
        except Exception as e:
            rep[bn] = "error %s" % e; continue
        bm = bmesh.new(); bm.from_mesh(me)
        mn0, mx0 = bbox(bm.verts); fixed = 0
        for isl_ in islands(bm):
            mn, mx = bbox(isl_)
            if (mx.z - mn.z) > 0.2:        # the 1 m strand family
                s = target / (mx.z - mn.z); fixed += 1
                for v in isl_: v.co.z = mn.z + (v.co.z - mn.z) * s
        mn1, mx1 = bbox(bm.verts)
        ob = bpy.data.objects.new(bn + "_clamped", bpy.data.meshes.new(bn)); c.objects.link(ob)
        bm.to_mesh(ob.data); bm.free(); ob.location.x = i * 0.1; put(ob, GOLD)
        rep[bn] = {"before_mm": [round((mx0 - mn0)[k] * 1000, 1) for k in range(3)],
                   "after_mm": [round((mx1 - mn1)[k] * 1000, 1) for k in range(3)], "islands_clamped": fixed}
    c.hide_render = True
    for o in c.objects: o.hide_render = True
    RECEIPT["dangles_z_clamp"] = rep

def house_crystal_sweep():
    """Evidence: what the house crystal_drop actually produces at Crystal Length 0.012-0.02."""
    import importlib
    cd = importlib.import_module("surreal_arch.melodia_gn.cute_decor"); out = {}
    for L in (0.012, 0.015, 0.02):
        t = cd.build_crystal_drop("sweep_%s" % L)
        if isinstance(t, (tuple, list)): t = t[0]
        g = bpy.data.node_groups.new("sweepwrap_%s" % L, "GeometryNodeTree")
        g.interface.new_socket("Geometry", in_out="OUTPUT", socket_type="NodeSocketGeometry")
        go = g.nodes.new("NodeGroupOutput"); n = g.nodes.new("GeometryNodeGroup"); n.node_tree = t
        for s in n.inputs:
            if s.name == "Crystal Length": s.default_value = L
            if s.name == "Crystal Width": s.default_value = L * 0.6
        g.links.new(n.outputs[0], go.inputs[0])
        me, _ = evaluate("sweep_%s" % L, g)
        bm = bmesh.new(); bm.from_mesh(me)
        out[str(L)] = sorted([(len(i), [round((bbox(i)[1] - bbox(i)[0])[k] * 1000, 1) for k in range(3)]) for i in islands(bm)], key=lambda x: -x[0])[:4]
        bm.free()
    RECEIPT["house_crystal_drop_sweep_(islands:verts,[mm])"] = out

# ------------------------------------------------------------------ stand-ins
def proxies():
    c = coll("STAGE_proxies")
    skin = mat_matte("V2_Proxy_WarmGrey", (0.30, 0.285, 0.27), 0.55)
    # head: egg fitted to the measured brow (z1.56, 0.408 x 0.459) and crown (z1.80, 0.2265) bands
    bm = sphere_bm(1.0, 96, 48)
    for v in bm.verts:
        x, y, z = v.co
        k = 1.0 if z > 0 else (1.0 - 0.28 * (-z) ** 1.5)          # jaw taper below the brow
        v.co = Vector((x * 0.199 * k, y * 0.223 * k, z * (0.29 if z > 0 else 0.215)))
    xf(bm, Matrix.Translation((RB.BROW_CX, RB.BROW_CY, 1.556)))
    head = new_obj("PROXY_head", bm, c, smooth=True); put(head, skin); add_subsurf(head, 1)
    # bust for the necklace: neck column + shoulders
    bm = bmesh.new(); bmesh.ops.create_cone(bm, cap_ends=False, segments=64, radius1=0.064, radius2=0.060, depth=0.30)
    xf(bm, Matrix.Translation((0, -0.012, 1.30)))
    neck = new_obj("PROXY_neck", bm, c, smooth=True); put(neck, skin); add_subsurf(neck, 1)
    bm = sphere_bm(1.0, 96, 48)
    for v in bm.verts: v.co = Vector((v.co.x * 0.24, v.co.y * 0.10, v.co.z * 0.10))
    xf(bm, Matrix.Translation((0, 0.0, 1.17)))
    sh = new_obj("PROXY_shoulders", bm, c, smooth=True); put(sh, skin); add_subsurf(sh, 1)
    return c

# ------------------------------------------------------------------ run
proxies()
headpiece("circlet", "Aquamarine Dream")
headpiece("tiara", "Aquamarine Dream")
earrings()
necklace()
try: dangles()
except Exception as e: RECEIPT["dangles_z_clamp"] = "error %s" % e
try: house_crystal_sweep()
except Exception as e: RECEIPT["house_crystal_drop_sweep"] = "error %s" % e
SRC.hide_render = True
for o in bpy.data.objects:
    is_gem = any(o.name.endswith(k) for k in ("_stone", "_stone_drop", "_stone_round", "pendant"))
    if not is_gem:
        o.visible_transmission = False     # gems refract the studio, not the gold / proxy
RECEIPT["notes"].append("v2b: all non-gem objects have visible_transmission=False (gold-bounce blocker for stones)")
# verify materials on object slots
RECEIPT["object_slots"] = {o.name: [(s.link, s.material.name if s.material else None) for s in o.material_slots]
                           for o in bpy.data.objects if o.name.endswith(("_stone", "_stone_drop", "_stone_round", "pendant"))}
bpy.ops.wm.save_as_mainfile(filepath=BLEND, compress=True)
with open(os.path.join(W, "regalia_v2b_build_receipt.json"), "w") as fh: json.dump(RECEIPT, fh, indent=1, default=str)
print("V2-RECEIPT", json.dumps(RECEIPT, default=str))
