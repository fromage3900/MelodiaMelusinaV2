"""regalia_v2_render.py -- studio renders of regalia_v2.blend (never saves the blend).
blender -b regalia_v2.blend --python regalia_v2_render.py -- [shot ...] [--samples N] [--res N]
Writes PNGs to C:\\Users\\froma\\Documents\\lookdev_regalia_v2\\
"""
import bpy, sys, os, math
from mathutils import Vector, Matrix
OUT = r"C:\Users\froma\Documents\lookdev_regalia_v2"
os.makedirs(OUT, exist_ok=True)
A = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
SAMPLES = int(A[A.index("--samples") + 1]) if "--samples" in A else 256
RES = int(A[A.index("--res") + 1]) if "--res" in A else 1600
SHOTS = [a for a in A if not a.startswith("--") and not a.isdigit()]
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
nt.links.new(mix.outputs[0], out.inputs[0])

# ---------------- lights (3-point, area, re-aimed per shot)
LC = bpy.data.collections.new("STAGE_lights"); sc.collection.children.link(LC)
def area(name, energy, size, col):
    L = bpy.data.lights.new(name, "AREA"); L.energy = energy; L.size = size; L.color = col; L.shape = "DISK"
    o = bpy.data.objects.new(name, L); LC.objects.link(o); return o
KEY = area("Key", 1, 1, (1.0, 0.93, 0.84)); FILL = area("Fill", 1, 1, (0.86, 0.9, 1.0)); RIM = area("Rim", 1, 1, (1.0, 0.97, 0.94))
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

def shoot(tag, show, target, radius, azim, elev, lens=85, fstop=None, focus=None, res=(RES, RES), light_scale=1.0):
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
    sc.render.filepath = os.path.join(OUT, tag + ".png")
    print("V2-SHOT", tag, "dist %.3f" % dist); bpy.ops.render.render(write_still=True)

def gem_of(coll):
    for o in bpy.data.collections[coll].objects:
        if "stone" in o.name or "pendant" in o.name: return o
def ctr_of(o):
    pts = [o.matrix_world @ Vector(b) for b in o.bound_box]; return sum(pts, Vector()) / 8, max((p - pts[0]).length for p in pts)

def headpiece_shots(p):
    C = "REG_" + p; mn, mx = objs_bbox([C]); c = (mn + mx) * 0.5; r = max(mx - mn) * 0.5
    show = [C, "STAGE_proxies"]
    # hide bust objects for head shots
    for o in bpy.data.collections["STAGE_proxies"].objects: o.hide_render = not o.name.startswith("PROXY_head")
    band = mn.z + (mx.z - mn.z) * 0.5
    if p == "circlet":
        tgt = Vector((c.x, c.y, band + 0.02)); k = 0.66; e1, e2 = 6, 12
    else:
        tgt = Vector((c.x, c.y, band + r * 0.18)); k = 0.85; e1, e2 = 10, 20
    shoot(p + "_front", show, tgt, r * k, 0, e1)
    shoot(p + "_threequarter", show, tgt, r * k, 38, e2)
    g = gem_of(C); gc, gs = ctr_of(g)
    shoot(p + "_gem_macro", show, gc, max(gs * 1.1, 0.02), 22, 14, lens=100, fstop=22, light_scale=4.0)

def earring_shots():
    C = "REG_earrings"
    L = [o for o in bpy.data.collections[C].objects if o.name.startswith("earL")]
    pts = [o.matrix_world @ Vector(b) for o in L for b in o.bound_box]
    mn = Vector([min(p[i] for p in pts) for i in range(3)]); mx = Vector([max(p[i] for p in pts) for i in range(3)])
    c = (mn + mx) * 0.5; r = max(mx - mn) * 0.5
    for o in bpy.data.collections[C].objects: o.hide_render = not o.name.startswith("earL")
    shoot("earrings_front", [C], c, r * 1.25, 0, 5, light_scale=6.0)
    shoot("earrings_threequarter", [C], c, r * 1.25, 40, 15, light_scale=6.0)
    g = [o for o in L if o.name.endswith("stone_drop")][0]; gc, gs = ctr_of(g)
    shoot("earrings_gem_macro", [C], gc, gs * 0.75, 20, 10, lens=100, fstop=22, light_scale=12.0)
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

todo = SHOTS or ["circlet", "tiara", "earrings", "necklace", "lineup"]
for t in todo:
    if t in ("circlet", "tiara"): headpiece_shots(t)
    elif t == "earrings": earring_shots()
    elif t == "necklace": necklace_shots()
    elif t == "lineup": lineup()
print("V2-RENDER-DONE")
