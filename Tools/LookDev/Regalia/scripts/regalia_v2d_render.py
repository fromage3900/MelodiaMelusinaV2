"""regalia_v2_render.py -- studio renders of regalia_v2.blend (never saves the blend).
blender -b regalia_v2.blend --python regalia_v2_render.py -- [shot ...] [--samples N] [--res N]
Writes PNGs to C:\\Users\\froma\\Documents\\lookdev_regalia_v2\\
"""
import bpy, sys, os, math
from mathutils import Vector, Matrix
OUT = r"C:\Users\froma\Documents\lookdev_regalia_v2\v2d"
os.makedirs(OUT, exist_ok=True)
A = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
SAMPLES = int(A[A.index("--samples") + 1]) if "--samples" in A else 256
RES = int(A[A.index("--res") + 1]) if "--res" in A else 1600
_flagvals = {i + 1 for i, a in enumerate(A) if a.startswith("--")}
SHOTS = [a for i, a in enumerate(A) if not a.startswith("--") and i not in _flagvals]
sc = bpy.context.scene

# ---------------- render settings
sc.render.engine = "CYCLES"
cy = sc.cycles
try:
    pr = bpy.context.preferences.addons["cycles"].preferences
    for t in ("OPTIX", "CUDA", "HIP", "ONEAPI"):
        try:
            pr.compute_device_type = t; pr.get_devices()
            if any(d.type == t for d in pr.devices):
                for d in pr.devices: d.use = (d.type == t)
                cy.device = "GPU"; print("V2-DEVICE", t); break
        except Exception: pass
except Exception as e: print("V2-DEVICE cpu", e)
cy.samples = SAMPLES; cy.use_adaptive_sampling = True; cy.adaptive_threshold = 0.01
cy.use_denoising = True
try: cy.denoiser = "OPENIMAGEDENOISE"
except Exception: pass
cy.max_bounces = 16; cy.glossy_bounces = 10; cy.transmission_bounces = 16; cy.transparent_max_bounces = 16
cy.caustics_reflective = True; cy.caustics_refractive = True; cy.blur_glossy = 0.4
cy.sample_clamp_indirect = 8.0
sc.render.film_transparent = False
sc.view_settings.view_transform = "AgX"
try: sc.view_settings.look = "AgX - Medium High Contrast"
except Exception: pass
sc.render.image_settings.file_format = "PNG"

# ---------------- world: camera sees a dark neutral gradient; everything else sees a studio dome
w = bpy.data.worlds.new("V2_Studio"); sc.world = w; w.use_nodes = True; nt = w.node_tree; nt.nodes.clear()
out = nt.nodes.new("ShaderNodeOutputWorld")
tc = nt.nodes.new("ShaderNodeTexCoord"); lp = nt.nodes.new("ShaderNodeLightPath")
# camera gradient from window coords (radial vignette, dark neutral)
sep = nt.nodes.new("ShaderNodeSeparateXYZ"); nt.links.new(tc.outputs["Window"], sep.inputs[0])
def math_(op, a=None, b=None, va=0.0, vb=0.0):
    n = nt.nodes.new("ShaderNodeMath"); n.operation = op
    if a is not None: nt.links.new(a, n.inputs[0])
    else: n.inputs[0].default_value = va
    if b is not None: nt.links.new(b, n.inputs[1])
    else: n.inputs[1].default_value = vb
    return n.outputs[0]
dx = math_("SUBTRACT", sep.outputs[0], vb=0.5); dy = math_("SUBTRACT", sep.outputs[1], vb=0.62)
r2 = math_("ADD", math_("MULTIPLY", dx, dx), math_("MULTIPLY", dy, dy))
v = math_("POWER", math_("SUBTRACT", va=1.0, b=math_("MINIMUM", math_("MULTIPLY", r2, vb=2.2), vb=1.0)), vb=1.6)
cr = nt.nodes.new("ShaderNodeValToRGB"); nt.links.new(v, cr.inputs[0])
cr.color_ramp.elements[0].color = (0.006, 0.006, 0.007, 1); cr.color_ramp.elements[1].color = (0.055, 0.054, 0.056, 1)
bgc = nt.nodes.new("ShaderNodeBackground"); nt.links.new(cr.outputs[0], bgc.inputs[0]); bgc.inputs[1].default_value = 1.0
# studio dome for lighting/reflections: dark floor, bright top, soft horizon
sepn = nt.nodes.new("ShaderNodeSeparateXYZ"); nt.links.new(tc.outputs["Generated"], sepn.inputs[0])
dome = nt.nodes.new("ShaderNodeValToRGB"); nt.links.new(sepn.outputs[2], dome.inputs[0])
e = dome.color_ramp.elements; e[0].position = 0.45; e[0].color = (0.01, 0.01, 0.01, 1)
e[1].position = 1.0; e[1].color = (0.55, 0.55, 0.57, 1)
m = e.new(0.56); m.color = (0.16, 0.16, 0.165, 1)
bgd = nt.nodes.new("ShaderNodeBackground"); nt.links.new(dome.outputs[0], bgd.inputs[0]); bgd.inputs[1].default_value = 0.6
mix = nt.nodes.new("ShaderNodeMixShader")
nt.links.new(lp.outputs["Is Camera Ray"], mix.inputs[0]); nt.links.new(bgd.outputs[0], mix.inputs[1]); nt.links.new(bgc.outputs[0], mix.inputs[2])
# v2b: rays leaving a stone see a brighter neutral-cool dome (a 'white card' behind the gems), so
# transparent stones read light instead of refracting the dark floor. Gold never transmits, so unaffected.
bgt = nt.nodes.new("ShaderNodeBackground"); bgt.inputs[0].default_value = (0.78, 0.82, 0.88, 1)   # flat neutral-cool card
bgt.inputs[1].default_value = float(A[A.index("--gemdome") + 1]) if "--gemdome" in A else 0.5
mix2 = nt.nodes.new("ShaderNodeMixShader")
nt.links.new(lp.outputs["Is Transmission Ray"], mix2.inputs[0]); nt.links.new(mix.outputs[0], mix2.inputs[1]); nt.links.new(bgt.outputs[0], mix2.inputs[2])
nt.links.new(mix2.outputs[0], out.inputs[0])

# ---------------- lights (3-point, area, re-aimed per shot)
LC = bpy.data.collections.new("STAGE_lights"); sc.collection.children.link(LC)
def area(name, energy, size, col):
    L = bpy.data.lights.new(name, "AREA"); L.energy = energy; L.size = size; L.color = col; L.shape = "DISK"
    o = bpy.data.objects.new(name, L); LC.objects.link(o); return o
KEY = area("Key", 1, 1, (1.0, 0.93, 0.84)); FILL = area("Fill", 1, 1, (0.86, 0.9, 1.0)); RIM = area("Rim", 1, 1, (1.0, 0.97, 0.94))
KICK = area("GemKicker", 0, 1, (1.0, 1.0, 1.0)); KICK.data.shape = "RECTANGLE"
# v2c: card lights the stones only through transmission/diffuse; never seen directly or in reflections
KICK.visible_camera = False; KICK.visible_glossy = False
print("V2-KICK vis cam/gloss/trans/diff", KICK.visible_camera, KICK.visible_glossy, KICK.visible_transmission, KICK.visible_diffuse)
def aim(o, target, pos):
    o.location = pos; d = (target - pos).normalized()
    o.rotation_euler = d.to_track_quat("-Z", "Y").to_euler()

cam_d = bpy.data.cameras.new("Cam"); CAM = bpy.data.objects.new("Cam", cam_d); sc.collection.objects.link(CAM); sc.camera = CAM
cam_d.sensor_width = 36

def colls_visible(names):
    for c in bpy.data.collections:
        if c.name.startswith(("REG_", "STAGE_proxies", "LINEUP")):
            c.hide_render = c.name not in names
    for c in bpy.data.collections:
        if c.name.startswith(("_GN_source", "_Dangles")): c.hide_render = True

def objs_bbox(names, only=None):
    pts = []
    for c in bpy.data.collections:
        if c.name in names:
            for o in c.all_objects:
                if o.type not in ("MESH", "CURVE") or (only and not only(o)): continue
                pts += [o.matrix_world @ Vector(b) for b in o.bound_box]
    mn = Vector([min(p[i] for p in pts) for i in range(3)]); mx = Vector([max(p[i] for p in pts) for i in range(3)])
    return mn, mx

def shoot(tag, show, target, radius, azim, elev, lens=85, fstop=None, focus=None, res=(RES, RES), light_scale=1.0, kick=None):
    colls_visible(show)
    sc.render.resolution_x, sc.render.resolution_y = res; sc.render.resolution_percentage = 100
    cam_d.lens = lens
    fov = 2 * math.atan(18 / lens)          # sensor_fit AUTO: fov spans the LARGER image side
    dist = radius / math.tan(fov * 0.5) * 1.08
    a, e_ = math.radians(azim), math.radians(elev)
    dirv = Vector((math.sin(a) * math.cos(e_), -math.cos(a) * math.cos(e_), math.sin(e_)))   # azim 0 = front (-Y)
    CAM.location = target + dirv * dist
    CAM.rotation_euler = (target - CAM.location).to_track_quat("-Z", "Y").to_euler()
    cam_d.clip_start = dist * 0.02; cam_d.clip_end = dist * 50
    cam_d.dof.use_dof = fstop is not None
    if fstop: cam_d.dof.aperture_fstop = fstop; cam_d.dof.focus_distance = (focus or target - CAM.location).length if not isinstance(focus, float) else focus
    s = radius * light_scale
    def around(az, el, d):
        aa, ee = math.radians(azim + az), math.radians(el)
        return target + Vector((math.sin(aa) * math.cos(ee), -math.cos(aa) * math.cos(ee), math.sin(ee))) * d
    aim(KEY, target, around(-40, 35, s * 6)); KEY.data.size = s * 3.0; KEY.data.energy = 900 * s * s
    aim(FILL, target, around(55, 10, s * 7)); FILL.data.size = s * 6.0; FILL.data.energy = 250 * s * s
    aim(RIM, target, around(165, 40, s * 6)); RIM.data.size = s * 2.0; RIM.data.energy = 1100 * s * s
    KICK.data.energy = 0
    if kick is not None:   # (target, energy): a small card just under the lens, for the stones
        kt, ke = kick
        aim(KICK, kt, CAM.location + Vector((0, 0, -dist * 0.18)) + (kt - CAM.location).normalized() * dist * 0.45)
        KICK.data.size = radius * 0.9; KICK.data.size_y = radius * 0.45; KICK.data.energy = ke
    sc.render.filepath = os.path.join(OUT, tag + ".png")
    print("V2-SHOT", tag, "dist %.3f" % dist); bpy.ops.render.render(write_still=True)

def gem_of(coll):
    for o in bpy.data.collections[coll].objects:
        if "stone" in o.name or "pendant" in o.name: return o
def ctr_of(o):
    pts = [o.matrix_world @ Vector(b) for b in o.bound_box]; return sum(pts, Vector()) / 8, max((p - pts[0]).length for p in pts)

AQUA = tuple(float(v) for v in A[A.index("--aqua") + 1].split(",")) if "--aqua" in A else (0.52, 0.78, 1.0)
AQUA_ABS = float(A[A.index("--aquaabs") + 1]) if "--aquaabs" in A else 14.0
def aqua_fix():
    m = bpy.data.materials.get("V2_Stone_Aquamarine_Dream")
    if not m: print("V2-AQUA material missing"); return
    nt_ = m.node_tree; b = [n for n in nt_.nodes if n.type == "BSDF_PRINCIPLED"][0]
    b.inputs["Base Color"].default_value = AQUA + (1,)
    try: b.inputs["Dispersion"].default_value = 0.15
    except Exception: pass
    out_ = [n for n in nt_.nodes if n.type == "OUTPUT_MATERIAL"][0]
    va = nt_.nodes.new("ShaderNodeVolumeAbsorption")
    va.inputs["Color"].default_value = AQUA + (1,); va.inputs["Density"].default_value = AQUA_ABS
    nt_.links.new(va.outputs[0], out_.inputs["Volume"])
    print("V2-AQUA", AQUA, AQUA_ABS)
# v2d: aquamarine/orchid materials are baked into regalia_v2d.blend (no render-time override)
RB_CY = -0.1335
PARTS = {"front", "threequarter", "top", "macro"}
KICK_E = float(A[A.index("--kick") + 1]) if "--kick" in A else 0.6
def headpiece_shots(p):
    C = "REG_" + p; mn, mx = objs_bbox([C]); c = (mn + mx) * 0.5; r = max(mx - mn) * 0.5
    show = [C, "STAGE_proxies"]
    # hide bust objects for head shots
    for o in bpy.data.collections["STAGE_proxies"].objects: o.hide_render = not o.name.startswith("PROXY_head")
    band = mn.z + (mx.z - mn.z) * 0.5
    if p == "circlet":
        # whole band in frame, head <= ~40% of pixels: pull back to a 0.62 m frame centred on the head
        hmn, hmx = objs_bbox(["STAGE_proxies"], lambda o: o.name.startswith("PROXY_head"))
        hc = (hmn + hmx) * 0.5; w = mx.x - mn.x
        tgt = Vector((hc.x, hc.y, hc.z)); rr = max(w * 0.62, (hmx.z - hmn.z) * 0.62)
        print("V2-CIRCLET frame r %.3f w %.3f head %.3f" % (rr, w, hmx.z - hmn.z))
        if "front" in PARTS: shoot("circlet_front", show, tgt, rr, 0, 8)
        if "threequarter" in PARTS: shoot("circlet_threequarter", show, tgt, rr, 35, 22)
        if "top" in PARTS: shoot("circlet_top", show, Vector((hc.x, hc.y, band)), max(w, mx.y - mn.y) * 0.62, 0, 89)
    else:
        tgt = Vector((c.x, c.y, band + r * 0.18)); k = 0.85
        # frame the new spire too
        sp = [o for o in bpy.data.collections[C].objects if "spire" in o.name]
        if sp:
            tgt = Vector((c.x, c.y, band + r * 0.21)); k = 1.12
        if "front" in PARTS: shoot(p + "_front", show, tgt, r * k, 0, 10)
        if "threequarter" in PARTS: shoot(p + "_threequarter", show, tgt, r * k, 38, 20)
    if "macro" not in PARTS: return
    g = gem_of(C); gc, gs = ctr_of(g)
    shoot(p + "_gem_macro", show, gc, max(gs * 1.1, 0.008), 22, 14, lens=100, fstop=22, light_scale=4.0, kick=(gc, KICK_E * 0.5))

def earring_shots():
    C = "REG_earrings"
    L = [o for o in bpy.data.collections[C].objects if o.name.startswith("earL")]
    pts = [o.matrix_world @ Vector(b) for o in L for b in o.bound_box]
    mn = Vector([min(p[i] for p in pts) for i in range(3)]); mx = Vector([max(p[i] for p in pts) for i in range(3)])
    c = (mn + mx) * 0.5; r = max(mx - mn) * 0.5
    for o in bpy.data.collections[C].objects: o.hide_render = not o.name.startswith("earL")
    gd = [o for o in L if o.name.endswith("stone_drop")][0]; gdc, _ = ctr_of(gd)
    shoot("earrings_front", [C], c, r * 1.25, 0, 5, light_scale=6.0, kick=(gdc, KICK_E))
    shoot("earrings_threequarter", [C], c, r * 1.25, 40, 15, light_scale=6.0, kick=(gdc, KICK_E))
    g = [o for o in L if o.name.endswith("stone_drop")][0]; gc, gs = ctr_of(g)
    if "--earmacro" in A: shoot("earrings_gem_macro", [C], gc, gs * 0.75, 20, 10, lens=100, fstop=22, light_scale=12.0)
    for o in bpy.data.collections[C].objects: o.hide_render = False

def necklace_shots():
    C = "REG_necklace"; show = [C, "STAGE_proxies"]
    for o in bpy.data.collections["STAGE_proxies"].objects: o.hide_render = o.name.startswith("PROXY_head")
    mn, mx = objs_bbox([C]); c = (mn + mx) * 0.5; r = max(mx - mn) * 0.5
    c = c + Vector((0, 0, -r * 0.15))
    shoot("necklace_front", show, c, r * 1.15, 0, 16)
    shoot("necklace_threequarter", show, c, r * 1.15, 38, 24)
    g = gem_of(C); gc, gs = ctr_of(g)
    shoot("necklace_gem_macro", show, gc + Vector((0, 0, gs * 0.15)), gs * 0.9, 15, 10, lens=100, fstop=22, light_scale=6.0)

def lineup():
    """All 4 pieces side by side, each normalised to the same display width (NOT to scale)."""
    L = bpy.data.collections.new("LINEUP"); sc.collection.children.link(L)
    items = [("REG_circlet", None), ("REG_tiara", None), ("REG_necklace", None), ("REG_earrings", lambda o: o.name.startswith("earL"))]
    x = 0.0; span = 0.30
    for name, flt in items:
        src = bpy.data.collections[name]
        mn, mx = objs_bbox([name], flt); c = (mn + mx) * 0.5; wdt = max(mx.x - mn.x, mx.z - mn.z, 1e-4)
        s = (span * 0.8) / wdt if name != "REG_earrings" else (span * 0.75) / (mx.z - mn.z)
        for o in src.objects:
            if flt and not flt(o): continue
            d = o.copy(); L.objects.link(d)
            d.matrix_world = Matrix.Translation((x, 0, 0)) @ Matrix.Scale(s, 4) @ Matrix.Translation(-c) @ o.matrix_world
        x += span
    for o in L.objects:
        pass
    mn, mx = objs_bbox(["LINEUP"]); c = (mn + mx) * 0.5; r = (mx.x - mn.x) * 0.5
    shoot("lineup_all4", ["LINEUP"], c, r * 1.1, 0, 12, lens=70, res=(int(RES * 1.6), int(RES * 0.8)), light_scale=0.6)

def lineup_real():
    """All 4 at TRUE relative size (one earring), with a 100 mm matte scale bar."""
    L = bpy.data.collections.new("LINEUP_REAL"); sc.collection.children.link(L)
    items = [("REG_circlet", None), ("REG_tiara", None), ("REG_necklace", None), ("REG_earrings", lambda o: o.name.startswith("earL"))]
    import bmesh
    x = 0.0; gap = 0.06
    for name, flt in items:
        mn, mx = objs_bbox([name], flt); c = (mn + mx) * 0.5; w = mx.x - mn.x
        x += w * 0.5
        for o in bpy.data.collections[name].objects:
            if flt and not flt(o): continue
            d = o.copy(); L.objects.link(d)
            mw = o.matrix_world.copy(); d.parent = None
            if d.type == "MESH" and name in ("REG_circlet", "REG_tiara") and d.name.startswith(("circlet_gold", "tiara_gold")):
                d.data = o.data.copy(); bm_ = bmesh.new(); bm_.from_mesh(d.data)
                nb = sum(1 for e in bm_.edges if e.is_boundary)
                r_ = bmesh.ops.holes_fill(bm_, edges=[e for e in bm_.edges if e.is_boundary], sides=24)
                bm_.to_mesh(d.data); bm_.free(); print("V2-CAP", d.name, "boundary edges", nb, "caps", len(r_["faces"]))
            d.matrix_world = Matrix.Translation(Vector((x - c.x, -c.y, -mn.z))) @ mw
        x += w * 0.5 + gap
    import bmesh
    bm = bmesh.new(); bmesh.ops.create_cube(bm, size=1.0)
    for v in bm.verts: v.co = Vector((v.co.x * 0.100, v.co.y * 0.004, v.co.z * 0.002))
    me = bpy.data.meshes.new("scalebar_100mm"); bm.to_mesh(me); bm.free()
    bar = bpy.data.objects.new("scalebar_100mm", me); L.objects.link(bar)
    bar.location = (x - gap - 0.05, -0.06, -0.012)
    m = bpy.data.materials.new("V2_ScaleBar"); m.use_nodes = True
    m.node_tree.nodes["Principled BSDF"].inputs["Base Color"].default_value = (0.35, 0.35, 0.36, 1)
    me.materials.append(m)
    cu = bpy.data.curves.new("scalebar_label", "FONT"); cu.body = "100 mm"; cu.size = 0.022; cu.extrude = 0.0006
    cu.align_x = "CENTER"; cu.align_y = "TOP"
    lab = bpy.data.objects.new("scalebar_label", cu); L.objects.link(lab)
    lab.location = (bar.location.x, bar.location.y, bar.location.z - 0.008); lab.rotation_euler = (math.radians(90), 0, 0)
    cu.materials.append(m)
    mn, mx = objs_bbox(["LINEUP_REAL"]); c = (mn + mx) * 0.5; r = (mx.x - mn.x) * 0.5
    print("V2-LREAL bbox", tuple(mn), tuple(mx))
    shoot("lineup_real_scale", ["LINEUP_REAL"], c, r * 1.02, 0, 12, lens=70, res=(int(RES * 1.6), int(RES * 0.8)), light_scale=0.6)

if "--parts" in A:
    PARTS = set(A[A.index("--parts") + 1].split(","))
todo = SHOTS or ["circlet", "tiara", "earrings", "necklace", "lineup"]
for t in todo:
    if t in ("circlet", "tiara"): headpiece_shots(t)
    elif t == "earrings": earring_shots()
    elif t == "necklace": necklace_shots()
    elif t == "lineup": lineup()
    elif t == "lineup_real": lineup_real()
print("V2-RENDER-DONE")
