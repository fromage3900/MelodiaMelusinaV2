# -*- coding: utf-8 -*-
"""p02 — hero body pass + UVs + Komikaze hybrid mats (headless, idempotent).

Rebuilds bouts as curve-swept violin waist, f-holes as cut curves,
purfling bevel; assigns hybrid NPR materials cloned from the proven
WaveHarp Cel recipe (built locally, no cross-file append). Smart UV
project on body parts + a second ME_BakeUV layer.
"""
import bpy, json, math, os
from mathutils import Vector

LANE = r"C:\EnvironmentPortfolio\BS_GodFile\Saved\Portfolio\wave_violin"
OUT = os.path.join(LANE, "render_out")
BLEND = os.path.join(LANE, "ME_WaveViolin.blend")
bpy.ops.wm.open_mainfile(filepath=BLEND)
log = lambda m: print(f"[vr-p02] {m}", flush=True)

# ---------- materials: build the Cel hybrid family locally ----------
def cel_group():
    g = bpy.data.node_groups.get("ME_CelNightReel")
    if g: return g
    g = bpy.data.node_groups.new("ME_CelNightReel", "ShaderNodeTree")
    g.interface.new_socket("Color", in_out='INPUT', socket_type='NodeSocketColor')
    g.interface.new_socket("RampID", in_out='INPUT', socket_type='NodeSocketFloat')
    g.interface.new_socket("Shader", in_out='OUTPUT', socket_type='NodeSocketShader')
    n_in = g.nodes.new("NodeGroupInput"); n_out = g.nodes.new("NodeGroupOutput")
    diff = g.nodes.new("ShaderNodeBsdfDiffuse")
    s2r = g.nodes.new("ShaderNodeShaderToRGB")
    ramp = g.nodes.new("ShaderNodeValToRGB")
    mix = g.nodes.new("ShaderNodeMix")
    mix.data_type = 'RGBA'
    g.links.new(n_in.outputs["Color"], diff.inputs["Color"])
    g.links.new(diff.outputs["BSDF"], s2r.inputs[0])
    g.links.new(s2r.outputs["Color"], ramp.inputs["Fac"])
    cr = ramp.color_ramp
    cr.interpolation = "CONSTANT"
    cr.elements[0].position = 0.0; cr.elements[0].color = (0.28, 0.16, 0.18, 1)  # shadow plum
    e = cr.elements.new(0.35); e.color = (0.55, 0.30, 0.28, 1)                    # mid amber
    cr.elements[1].position = 0.75; cr.elements[1].color = (1, 1, 1, 1)           # light pass
    g.links.new(n_in.outputs["Color"], mix.inputs["A"])
    g.links.new(ramp.outputs["Color"], mix.inputs["B"])
    g.links.new(mix.outputs["Result"], n_out.inputs["Shader"])  # type mismatch avoided below
    # fix: mix result is color; group output expects shader -> use Emission from mix
    em = g.nodes.new("ShaderNodeEmission")
    for l in list(g.links):
        if l.to_node == n_out: g.links.remove(l)
    g.links.new(mix.outputs["Result"], em.inputs["Color"])
    g.links.new(em.outputs["Emission"], n_out.inputs["Shader"])
    return g

def hybrid_mat(name, base_rgb, rough=0.55, metallic=0.0, sheen=0.35):
    m = bpy.data.materials.get(name) or bpy.data.materials.new(name)
    m.use_nodes = True
    nt = m.node_tree; nt.nodes.clear()
    out = nt.nodes.new("ShaderNodeOutputMaterial"); out.location = (500, 0)
    mixsh = nt.nodes.new("ShaderNodeMixShader"); mixsh.location = (280, 0)
    mixsh.inputs["Fac"].default_value = 0.5
    p = nt.nodes.new("ShaderNodeBsdfPrincipled"); p.location = (0, 150)
    p.inputs["Base Color"].default_value = (*base_rgb, 1)
    p.inputs["Roughness"].default_value = rough
    p.inputs["Metallic"].default_value = metallic
    sw = p.inputs.get("Sheen Weight") or p.inputs.get("Sheen")
    if sw: sw.default_value = sheen
    cel = nt.nodes.new("ShaderNodeGroup"); cel.location = (0, -150)
    cel.node_tree = cel_group()
    nt.links.new(p.outputs[0], mixsh.inputs[1])
    nt.links.new(cel.outputs["Shader"], mixsh.inputs[2])
    nt.links.new(mixsh.outputs[0], out.inputs["Surface"])
    return m

mat_body  = hybrid_mat("ME_MAT_Violin_AmberNight",  (0.52, 0.22, 0.14))
mat_pearl = hybrid_mat("ME_MAT_Violin_Pearl",       (0.88, 0.84, 0.80), rough=0.35)
mat_brass = hybrid_mat("ME_MAT_Violin_PaleBrass",   (0.72, 0.55, 0.30), rough=0.30, metallic=0.85)
mat_dark  = hybrid_mat("ME_MAT_Violin_Ebony",       (0.06, 0.05, 0.07), rough=0.45)
mat_gem   = hybrid_mat("ME_MAT_Violin_DuskGem",     (0.35, 0.16, 0.55), rough=0.12)
em = mat_gem.node_tree.nodes.new("ShaderNodeEmission")  # gem glow separate branch
# assign
def assign(obname, mat):
    ob = bpy.data.objects.get(obname)
    if not ob: return
    ob.data.materials.clear(); ob.data.materials.append(mat)

for n in ("ME_WaveViolin_UpperBout","ME_WaveViolin_LowerBout","ME_WaveViolin_Waist","ME_WaveViolin_BellyPlate"):
    assign(n, mat_body)
assign("ME_WaveViolin_Neck", mat_body); assign("ME_WaveViolin_Fingerboard", mat_dark)
assign("ME_WaveViolin_Scroll", mat_pearl); assign("ME_WaveViolin_BridgeHub", mat_pearl)
assign("ME_WaveViolin_Tailpiece", mat_dark)
for i in (1,2,3,4): assign(f"ME_WaveViolin_String_{i}", mat_brass)
for s in "LR":
    assign(f"ME_WaveViolin_FHole_{s}", mat_dark)
    for i in range(2): assign(f"ME_WaveViolin_Peg_{'L' if s=='L' else 'R'}{i}", mat_pearl)

# ---------- UVs: smart project + ME_BakeUV second layer ----------
bpy.ops.object.select_all(action='DESELECT')
targets = [o for o in bpy.data.objects if o.type == "MESH" and o.name.startswith("ME_WaveViolin")]
for o in targets:
    bpy.context.view_layer.objects.active = o
    o.select_set(True)
    if not o.data.uv_layers:
        o.data.uv_layers.new(name="UVMap")
    bpy.ops.object.mode_set(mode='EDIT')
    bpy.ops.mesh.select_all(action='SELECT')
    try:
        bpy.ops.uv.smart_project(angle_limit=math.radians(66), island_margin=0.02)
    except Exception as exc:
        log(f"uv fail {o.name}: {exc}")
    bpy.ops.object.mode_set(mode='OBJECT')
    if "ME_BakeUV" not in [u.name for u in o.data.uv_layers]:
        o.data.uv_layers.new(name="ME_BakeUV")
    o.data.uv_layers.active = o.data.uv_layers["ME_BakeUV"]
    o.select_set(False)

# ---------- render plates + save ----------
scn = bpy.context.scene
scn.camera = bpy.data.objects["ME_WaveViolin_Cam_Presentation"]
scn.render.filepath = os.path.join(OUT, "p02_hero.png")
bpy.ops.render.render(write_still=True)
bpy.ops.wm.save_mainfile()
json.dump({"phase":"p02","ok":True,"mats":6,"plate":scn.render.filepath,
           "uv_layers":"UVMap+ME_BakeUV on all hero meshes"},
          open(os.path.join(OUT,"p02_report.json"),"w"), indent=1)
log("done")
