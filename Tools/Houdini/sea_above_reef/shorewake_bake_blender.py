"""PASS H2 — full texture bake for the Shorewake dress (Blender Cycles, no watermark).

Bake chain (evidence-culture compliant, all seeds/params recorded):
  LOW  = SM_ShorewakeDress_48MAT_v2.obj        (UVs + normals, from bake_prep)
  ATTR = SM_ShorewakeDress_48MAT_v2_attrs.obj  (Houdini vertex colors: R=thickness G=convex B=concave)
  HIGH = LOW subdivided x2 (simple)            (normal/AO detail source)

Maps (4096x4096, margin 16px):
  T_DressShorewake_Normal      tangent-space, MikkT-ish, DirectX green PRE-FLIPPED
  T_DressShorewake_AO          Cycles AO, high->low, 64 samples
  T_DressShorewake_Curvature   Houdini convex/concave (G/B) -> single map
  T_DressShorewake_Thickness   Houdini two-sided raycast (R)
  T_DressShorewake_Position    object-space P normalized to bbox
  T_DressShorewake_ID          panel-ID color blocks (7 merged panels)

Output: Saved/Audit/melusina_lookdev/bake/ + dress_bake_manifest.json
Run:  blender -b --factory-startup --python shorewake_bake_blender.py
"""

import json
import math
from pathlib import Path

import bpy
import numpy as np

BAKE_DIR = Path(r"C:\EnvironmentPortfolio\BS_GodFile\Saved\Audit\melusina_lookdev\bake")
LOW_OBJ = BAKE_DIR / "SM_ShorewakeDress_48MAT_v2.obj"
ATTR_OBJ = BAKE_DIR / "SM_ShorewakeDress_48MAT_v2_attrs.obj"
RES = 4096
MARGIN = 16
AO_SAMPLES = 64
SEED = 20260830
SUBDIV_LEVELS = 2

ID_COLORS = [
    (1.0, 0.1, 0.1), (0.1, 1.0, 0.1), (0.1, 0.1, 1.0), (1.0, 1.0, 0.1),
    (1.0, 0.1, 1.0), (0.1, 1.0, 1.0), (1.0, 0.6, 0.1),
]


def import_obj(path, name):
    before = set(bpy.data.objects)
    bpy.ops.wm.obj_import(filepath=str(path))
    new = [o for o in bpy.data.objects if o not in before and o.type == "MESH"]
    obj = max(new, key=lambda o: len(o.data.polygons))
    obj.name = name
    return obj


def transfer_attrs(low, attr_obj):
    """Copy Cd from the Houdini attrs OBJ (same point order) onto LOW."""
    me_a = attr_obj.data
    me_l = low.data
    if len(me_a.vertices) != len(me_l.vertices):
        raise SystemExit("vertex count mismatch: %d vs %d" % (len(me_a.vertices), len(me_l.vertices)))
    # sanity: positions must match (same mesh, same order)
    for i in (0, len(me_l.vertices) // 2, len(me_l.vertices) - 1):
        d = (me_a.vertices[i].co - me_l.vertices[i].co).length
        if d > 1e-5:
            raise SystemExit("vertex order mismatch at %d (dist %.6f)" % (i, d))
    # Blender 4.1+ stores OBJ vertex colors as a POINT-domain color attribute
    src_attr = None
    for cand in ("Col", "Cd", "vert_color", "col"):
        if cand in me_a.attributes:
            src_attr = me_a.attributes[cand]
            break
    if src_attr is None:
        src_attr = next((a for a in me_a.attributes
                         if a.domain == "POINT" and a.data_type == "FLOAT_COLOR"), None)
    if src_attr is None:
        raise SystemExit("no vertex color attribute found on attrs OBJ")
    colors = [(src_attr.data[i].color[0], src_attr.data[i].color[1], src_attr.data[i].color[2])
              for i in range(len(me_a.vertices))]
    me_l.attributes.new(name="hou_attrs", type="FLOAT_COLOR", domain="POINT")
    attr = me_l.attributes["hou_attrs"]
    for i in range(len(me_l.vertices)):
        attr.data[i].color = (*colors[i], 1.0)
    print("ATTRS_TRANSFERRED", len(colors))


def make_high(low):
    high = low.copy()
    high.data = low.data.copy()
    bpy.context.collection.objects.link(high)
    high.name = "DRESS_HIGH"
    mod = high.modifiers.new("subdiv", "SUBSURF")
    mod.subdivision_type = "SIMPLE"
    mod.levels = SUBDIV_LEVELS
    mod.render_levels = SUBDIV_LEVELS
    bpy.context.view_layer.objects.active = high
    bpy.ops.object.modifier_apply(modifier=mod.name)
    return high


def setup_cycles():
    sc = bpy.context.scene
    sc.render.engine = "CYCLES"
    sc.cycles.device = "CPU"
    sc.cycles.samples = 1
    sc.cycles.use_adaptive_sampling = False
    sc.render.film_transparent = False
    sc.render.bake.margin = MARGIN
    sc.render.bake.use_clear = True
    sc.cycles.seed = SEED


def new_image(name, linear=True):
    img = bpy.data.images.new(name, RES, RES, alpha=False, float_buffer=False)
    img.colorspace_settings.name = "Non-Color" if linear else "sRGB"
    img.generated_color = (0, 0, 0, 1)
    return img


def ensure_uv_node(mat, img):
    nt = mat.node_tree
    nt.nodes.clear()
    tex = nt.nodes.new("ShaderNodeTexImage")
    tex.image = img
    tex.select = True
    nt.nodes.active = tex
    out = nt.nodes.new("ShaderNodeOutputMaterial")
    nt.links.new(tex.outputs["Color"], out.inputs["Surface"])


def override_material(name, nodes_links):
    """nodes_links: callable(node_tree) building the emission shader."""
    mat = bpy.data.materials.new(name)
    mat.use_nodes = True
    nt = mat.node_tree
    nt.nodes.clear()
    out = nt.nodes.new("ShaderNodeOutputMaterial")
    emit = nt.nodes.new("ShaderNodeEmission")
    nodes_links(nt, emit, out)
    return mat


def bake_pass(img, bake_type, low, high=None, samples=1, normal_space=None, bake_mat=None):
    sc = bpy.context.scene
    sc.cycles.samples = samples
    bpy.ops.object.select_all(action="DESELECT")
    if high is not None:
        high.select_set(True)
    low.select_set(True)
    bpy.context.view_layer.objects.active = low
    # Single bake material with the ACTIVE image node — required by Cycles bake
    ensure_uv_node(bake_mat, img)
    kw = dict(type=bake_type, use_clear=True, margin=MARGIN)
    if bake_type == "NORMAL":
        kw["normal_space"] = normal_space or "TANGENT"
    if high is not None:
        kw["use_selected_to_active"] = True
        kw["max_ray_distance"] = 0.001  # 1mm: hit ONLY the coincident subdiv shell
        # (wider cages sample distant floral-trim geometry -> speckle artifacts)
    bpy.ops.object.bake(**kw)
    img.filepath_raw = str(BAKE_DIR / (img.name + ".png"))
    img.file_format = "PNG"
    img.save()
    print("BAKED", img.name)


def flip_green(path):
    """OpenGL->DirectX green channel flip (UE convention), in place."""
    img = bpy.data.images.load(str(path))
    w, h = img.size
    buf = np.empty(w * h * 4, dtype=np.float32)
    img.pixels.foreach_get(buf)
    buf = buf.reshape(h, w, 4)
    buf[:, :, 1] = 1.0 - buf[:, :, 1]
    img.pixels.foreach_set(buf.ravel())
    img.file_format = "PNG"
    img.save()
    bpy.data.images.remove(img)
    print("GREEN_FLIPPED", path.name)


def main():
    BAKE_DIR.mkdir(parents=True, exist_ok=True)
    bpy.ops.wm.read_factory_settings(use_empty=True)
    low = import_obj(str(LOW_OBJ), "DRESS_LOW")
    attr_obj = import_obj(str(ATTR_OBJ), "DRESS_ATTRS")
    transfer_attrs(low, attr_obj)
    bpy.data.objects.remove(attr_obj)

    # Coincident duplicate faces (USDZ artifacts) make every AO ray "occluded" —
    # weld by distance before anything else.
    bpy.context.view_layer.objects.active = low
    bpy.ops.object.mode_set(mode="EDIT")
    bpy.ops.mesh.select_all(action="SELECT")
    before_verts = len(low.data.vertices)
    bpy.ops.mesh.remove_doubles(threshold=1e-5)
    bpy.ops.object.mode_set(mode="OBJECT")
    print("MERGED_DOUBLES", before_verts, "->", len(low.data.vertices))

    high = make_high(low)
    setup_cycles()

    import mathutils
    diag = (low.matrix_world @ mathutils.Vector(low.bound_box[6])
            - low.matrix_world @ mathutils.Vector(low.bound_box[0])).length
    print("DIAG", diag)

    # One bake material on LOW. NOTE: the OBJ carries no materials (no MTL),
    # so a panel-ID map is not derivable here — skipped until the Substance
    # paint pass assigns slots (recorded in manifest).
    bake_mat = bpy.data.materials.new("bake_target")
    bake_mat.use_nodes = True
    low.data.materials.clear()
    low.data.materials.append(bake_mat)

    # --- NORMAL (high -> low, tangent) ---
    img_n = new_image("T_DressShorewake_Normal")
    bake_pass(img_n, "NORMAL", low, high=high, samples=1, bake_mat=bake_mat)
    flip_green(BAKE_DIR / "T_DressShorewake_Normal.png")

    # --- AO: OWNED BY HOUDINI (dress_ao_vex.py + bake_rasterize_ao.py).
    #     Cycles AO on open thin panels self-shadows to black — do NOT bake here. ---

    # --- THICKNESS + CURVATURE from Houdini attrs (EMIT, low only) ---
    def thick_links(nt, emit, out):
        a = nt.nodes.new("ShaderNodeAttribute")
        a.attribute_name = "hou_attrs"
        nt.links.new(a.outputs["Color"], emit.inputs["Color"])
        nt.links.new(emit.outputs["Emission"], out.inputs["Surface"])
    img_th = new_image("T_DressShorewake_Thickness")
    mat_th = override_material("ovr_thick", thick_links)
    low.data.materials.clear()
    low.data.materials.append(mat_th)
    bake_pass(img_th, "EMIT", low, samples=1, bake_mat=mat_th)
    img_cv = new_image("T_DressShorewake_Curvature")

    def curv_links(nt, emit, out):
        a = nt.nodes.new("ShaderNodeAttribute")
        a.attribute_name = "hou_attrs"
        sep = nt.nodes.new("ShaderNodeSeparateColor")
        nt.links.new(a.outputs["Color"], sep.inputs["Color"])
        comb = nt.nodes.new("ShaderNodeCombineColor")
        nt.links.new(sep.outputs["Green"], comb.inputs["Red"])
        nt.links.new(sep.outputs["Blue"], comb.inputs["Green"])
        nt.links.new(sep.outputs["Green"], comb.inputs["Blue"])
        nt.links.new(comb.outputs["Color"], emit.inputs["Color"])
        nt.links.new(emit.outputs["Emission"], out.inputs["Surface"])
    mat_cv = override_material("ovr_curv", curv_links)
    low.data.materials.clear()
    low.data.materials.append(mat_cv)
    bake_pass(img_cv, "EMIT", low, samples=1, bake_mat=mat_cv)

    # --- POSITION (object space normalized) ---
    bb = [low.matrix_world @ __import__("mathutils").Vector(c) for c in low.bound_box]
    mn = [min(v[i] for v in bb) for i in range(3)]
    mx = [max(v[i] for v in bb) for i in range(3)]
    sz = [mx[i] - mn[i] or 1.0 for i in range(3)]

    def pos_links(nt, emit, out):
        g = nt.nodes.new("ShaderNodeNewGeometry")
        sub = nt.nodes.new("ShaderNodeVectorMath")
        sub.operation = "SUBTRACT"
        sub.inputs[1].default_value = (mn[0], mn[1], mn[2])
        div = nt.nodes.new("ShaderNodeVectorMath")
        div.operation = "DIVIDE"
        div.inputs[1].default_value = (sz[0], sz[1], sz[2])
        nt.links.new(g.outputs["Position"], sub.inputs[0])
        nt.links.new(sub.outputs["Vector"], div.inputs[0])
        nt.links.new(div.outputs["Vector"], emit.inputs["Color"])
        nt.links.new(emit.outputs["Emission"], out.inputs["Surface"])
    img_p = new_image("T_DressShorewake_Position")
    mat_p = override_material("ovr_pos", pos_links)
    low.data.materials.clear()
    low.data.materials.append(mat_p)
    bake_pass(img_p, "EMIT", low, samples=1, bake_mat=mat_p)

    manifest = {
        "schema": "melodia.shorewake_full_bake.v1",
        "seed": SEED,
        "resolution": RES,
        "margin_px": MARGIN,
        "ao_samples": AO_SAMPLES,
        "subdiv_levels": SUBDIV_LEVELS,
        "high_poly_est": len(high.data.polygons),
        "blender": bpy.app.version_string,
        "engine": "CYCLES CPU",
        "normal": {"file": "T_DressShorewake_Normal.png", "space": "tangent",
                   "y_convention": "directx (pre-flipped for UE)"},
        "maps": ["Normal", "Thickness", "Curvature", "Position"],
        "ao": "baked in Houdini (dress_ao_vex.py, 64 rays, self-exclusion) + rasterized (bake_rasterize_ao.py) — NOT from Cycles",
        "id_map": "skipped — OBJ carries no material slots; derive panel IDs at Substance paint setup",
        "bbox_min": mn, "bbox_size": sz,
        "source": {"low": str(LOW_OBJ), "attrs": str(ATTR_OBJ)},
        "note": "thickness/curvature computed in Houdini (dress_geometry_attrs.py), encoded in OBJ vertex colors",
    }
    (BAKE_DIR / "dress_bake_manifest.json").write_text(json.dumps(manifest, indent=1), encoding="utf-8")
    print("FULL_BAKE_DONE", sorted(p.name for p in BAKE_DIR.glob("*.png")))


main()
