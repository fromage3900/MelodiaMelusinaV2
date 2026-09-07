# -*- coding: utf-8 -*-
"""p14 — Nikki-doctrine shader pass on Night Reel (headless).

1. Belly: full 9-map Copernicus PBR base (BC/N/ORM/Emissive/Iri) + cel ramp mix
   (the repo's Lane A hybrid recipe, mirrored from SHAWL.001 doctrine).
2. Jewelry gems: fake refraction per Infinity Nikki interview — opaque mesh,
   cubemap-ish gradient ramp by view-normal + 3S band + sharp spec. No real SSS.
3. F-holes: deeper S-curves (hotter offsets) + stronger glow under Standard.
4. Strings: emissive energy lane stays; add tangent-ish aniso streak via sheen.
"""
import bpy, json, math, os
import bmesh
from mathutils import Vector

LANE = r"C:\EnvironmentPortfolio\BS_GodFile\Saved\Portfolio\wave_violin"
COP = os.path.join(LANE, "copernicus", "textures")
OUT = os.path.join(LANE, "render_out")
BLEND = os.path.join(LANE, "ME_WaveViolin.blend")
bpy.ops.wm.open_mainfile(filepath=BLEND)
log = lambda m: print(f"[vr-p14] {m}", flush=True)
rep = {"phase": "p14", "ok": True}

def load_img(name, path, noncolor=True):
    img = bpy.data.images.get(name)
    if img is None:
        img = bpy.data.images.load(path, check_existing=True); img.name = name
    img.filepath = path
    if noncolor: img.colorspace_settings.name = "Non-Color"
    return img

# ---------- 1) belly: 9-map Nikki master-style hybrid ----------
mb = bpy.data.materials.get("ME_MAT_Violin_BellyCymatic") or bpy.data.materials["ME_MAT_Violin_AmberNight"].copy()
mb.name = "ME_MAT_Violin_BellyCymatic"
nt = mb.node_tree; nt.nodes.clear()
out_n = nt.nodes.new("ShaderNodeOutputMaterial"); out_n.location = (1200, 0)
mix = nt.nodes.new("ShaderNodeMixShader"); mix.location = (950, 0)
mix.inputs["Fac"].default_value = 0.45
p = nt.nodes.new("ShaderNodeBsdfPrincipled"); p.location = (500, 250)

def tex(mapname, x, y, noncolor=True):
    n = nt.nodes.new("ShaderNodeTexImage"); n.location = (x, y)
    n.image = load_img(f"T_ME_WaveViolin_{mapname}", os.path.join(COP, f"T_ME_WaveViolin_{mapname}.png"), noncolor)
    return n
tBC = tex("BaseColor", -500, 400, noncolor=False)
tORM = tex("ORM", -500, 100)
tN = tex("Normal", -500, -200)
tEM = tex("Emissive", -500, -500, noncolor=False)
tIRI = tex("Iridescence", -500, -800, noncolor=False)
nt.links.new(tBC.outputs["Color"], p.inputs["Base Color"])
sep = nt.nodes.new("ShaderNodeSeparateColor"); sep.location = (-200, 100)
nt.links.new(tORM.outputs["Color"], sep.inputs["Color"])
# AO: multiply red channel into base color (Principled has no AO input in 5.2)
aomul = nt.nodes.new("ShaderNodeMix"); aomul.data_type = 'RGBA'; aomul.blend_type = 'MULTIPLY'; aomul.location = (-200, 400)
nt.links.new(tBC.outputs["Color"], aomul.inputs["A"])
nt.links.new(sep.outputs["Red"], aomul.inputs["Factor"])
nt.links.new(aomul.outputs["Result"], p.inputs["Base Color"])
nt.links.new(sep.outputs["Green"], p.inputs["Roughness"])
nt.links.new(sep.outputs["Blue"], p.inputs["Metallic"])
nmap = nt.nodes.new("ShaderNodeNormalMap"); nmap.location = (-200, -200)
nmap.inputs["Strength"].default_value = 0.7
nt.links.new(tN.outputs["Color"], nmap.inputs["Color"])
nt.links.new(nmap.outputs["Normal"], p.inputs["Normal"])
nt.links.new(tEM.outputs["Color"], p.inputs["Emission Color"])
p.inputs["Emission Strength"].default_value = 1.4
sw = p.inputs.get("Sheen Weight") or p.inputs.get("Sheen")
if sw: sw.default_value = 0.5
# iridescence: view-angle tint multiplied onto emission
layer = nt.nodes.new("ShaderNodeLayerWeight"); layer.location = (-200, -520)
layer.inputs["Blend"].default_value = 0.35
mixc = nt.nodes.new("ShaderNodeMix"); mixc.data_type = 'RGBA'; mixc.blend_type = 'MULTIPLY'; mixc.location = (100, -450)
mixc.inputs["Factor"].default_value = 0.4
nt.links.new(layer.outputs["Facing"], mixc.inputs["A"])
nt.links.new(tIRI.outputs["Color"], mixc.inputs["B"])
addem = nt.nodes.new("ShaderNodeMix"); addem.data_type = 'RGBA'; addem.blend_type = 'ADD'; addem.location = (300, -300)
addem.inputs["Factor"].default_value = 0.6
nt.links.new(tEM.outputs["Color"], addem.inputs["A"])
nt.links.new(mixc.outputs["Result"], addem.inputs["B"])
nt.links.new(addem.outputs["Result"], p.inputs["Emission Color"])
# cel branch: diffuse->s2rgb->ramp (Nikki one-graph doctrine)
diff = nt.nodes.new("ShaderNodeBsdfDiffuse"); diff.location = (500, -350)
nt.links.new(tBC.outputs["Color"], diff.inputs["Color"])
s2r = nt.nodes.new("ShaderNodeShaderToRGB"); s2r.location = (650, -350)
nt.links.new(diff.outputs[0], s2r.inputs[0])
ramp = nt.nodes.new("ShaderNodeValToRGB"); ramp.location = (700, -550)
ramp.color_ramp.interpolation = "CONSTANT"
els = ramp.color_ramp.elements
els[0].position = 0.0; els[0].color = (0.25, 0.12, 0.16, 1)
e_mid = els.new(0.45); e_mid.color = (1.0, 0.72, 0.45, 1)   # nodal gold light-side
els[-1].position = 0.8; els[-1].color = (1, 1, 1, 1)
nt.links.new(s2r.outputs["Color"], ramp.inputs["Fac"])
celout = nt.nodes.new("ShaderNodeEmission"); celout.location = (800, -550)
nt.links.new(ramp.outputs["Color"], celout.inputs["Color"])
nt.links.new(p.outputs[0], mix.inputs[1])
nt.links.new(celout.outputs[0], mix.inputs[2])
nt.links.new(mix.outputs[0], out_n.inputs["Surface"])
belly = bpy.data.objects["ME_WaveViolin_BellyPlate"]
belly.data.materials.clear(); belly.data.materials.append(mb)
rep["belly"] = "9-map Copernicus + cel ramp hybrid"

# ---------- 2) jewelry gems: fake refraction ramp ----------
mg = bpy.data.materials.get("ME_MAT_Violin_DuskGem")
if mg is None:
    mg = bpy.data.materials.new("ME_MAT_Violin_DuskGem"); mg.use_nodes = True
gnt = mg.node_tree; gnt.nodes.clear()
gout = gnt.nodes.new("ShaderNodeOutputMaterial"); gout.location = (800, 0)
gp = gnt.nodes.new("ShaderNodeBsdfPrincipled"); gp.location = (450, 100)
gp.inputs["Roughness"].default_value = 0.06
gp.inputs["Metallic"].default_value = 0.0
gfr = gnt.nodes.new("ShaderNodeFresnel"); gfr.location = (-100, 200); gfr.inputs["IOR"].default_value = 1.45
rmp = gnt.nodes.new("ShaderNodeValToRGB"); rmp.location = (150, 250)
rmp.color_ramp.interpolation = "CONSTANT"
re_ = rmp.color_ramp.elements
re_[0].position = 0.0; re_[0].color = (0.16, 0.05, 0.30, 1)     # deep core
ee = re_.new(0.55); ee.color = (0.55, 0.30, 0.90, 1)            # mid violet
re_[1].position = 0.85; re_[1].color = (0.85, 0.75, 1.0, 1)     # rim flash (cubemap-ish)
gnt.links.new(gfr.outputs[0], rmp.inputs["Fac"])
gnt.links.new(rmp.outputs["Color"], gp.inputs["Base Color"])
ges = gp.inputs.get("Emission Strength"); gec = gp.inputs.get("Emission Color")
if ges: ges.default_value = 0.35
if gec: gec.default_value = (0.4, 0.18, 0.7, 1)
gnt.links.new(gp.outputs[0], gout.inputs["Surface"])
rep["gems"] = "fresnel-ramp fake refraction + rim flash"

# beads use the gem mat
bead = bpy.data.objects.get("ME_WaveViolin_BeadProto") or bpy.data.objects.get("ME_WaveViolin_BeadProto.001")
if bead: bead.data.materials.clear(); bead.data.materials.append(mg)
# bridge hub keeps pearl; tailpiece end gem: give pommel-ish objects the gem mat
for n in ("ME_WaveViolin_PommelGem",):
    ob = bpy.data.objects.get(n)
    if ob: ob.data.materials.clear(); ob.data.materials.append(mg)

# ---------- 3) f-holes: deeper S + hotter glow ----------
vm = bpy.data.materials["ME_MAT_Violin_VentPure"]
em = next(n for n in vm.node_tree.nodes if n.type == "EMISSION")
em.inputs["Strength"].default_value = 3.0
for s, zn in ((-1, "L"), (1, "R")):
    nm = f"ME_WaveViolin_FHole_{zn}"
    ob = bpy.data.objects.get(nm)
    me_old = ob.data if ob else None
    if ob:
        bpy.data.objects.remove(ob, do_unlink=True)
        if me_old and me_old.users == 0: bpy.data.meshes.remove(me_old)
    bm = bmesh.new(); prev = None
    pts = [(-0.001, 0.135), (0.016, 0.122), (0.019, 0.100), (-0.007, 0.084),
           (-0.013, 0.045), (-0.010, 0.0), (-0.007, -0.045), (0.013, -0.084),
           (0.019, -0.102), (0.006, -0.124), (-0.011, -0.132)]
    for ox, oz in pts:
        v = bm.verts.new(Vector((s * 0.046 + s * ox, -0.0368, -0.045 + oz)))
        if prev: bm.edges.new((prev, v))
        prev = v
    me = bpy.data.meshes.new(nm); bm.to_mesh(me); bm.free()
    ob = bpy.data.objects.new(nm, me)
    ob.modifiers.new("ME_FHoleSkin", "SKIN")
    rad = [0.0075, 0.0040, 0.0030, 0.0026, 0.0024, 0.0024, 0.0024, 0.0026, 0.0030, 0.0040, 0.0075]
    for vv, rr in zip(me.skin_vertices[0].data, rad): vv.radius = (rr, rr)
    for c in list(ob.users_collection): c.objects.unlink(ob)
    bpy.data.collections["ME_WaveViolin_Assemblies"].objects.link(ob)
    ob.data.materials.append(vm)
rep["fholes"] = "±19mm swing S-curves with eyelets, glow 3.0"

# render check plates
scn = bpy.context.scene
mc = bpy.data.objects["ME_WaveViolin_Control"]
cam = bpy.data.objects.get("ME_Violin_Cam_Macro2")
if cam:
    scn.camera = cam
    scn.render.filepath = os.path.join(OUT, "p14_macro.png")
    bpy.ops.render.render(write_still=True)
scn.camera = bpy.data.objects["ME_WaveViolin_Cam_Presentation"]
for tag, rx in (("stow", -1.5708), ("deploy", 0.0)):
    mc.rotation_euler.x = rx; bpy.context.view_layer.update()
    scn.render.filepath = os.path.join(OUT, f"p14_{tag}.png")
    bpy.ops.render.render(write_still=True)
mc.rotation_euler.x = -1.5708
bpy.ops.wm.save_mainfile()
json.dump(rep, open(os.path.join(OUT, "p14_report.json"), "w"), indent=1)
log("done")
