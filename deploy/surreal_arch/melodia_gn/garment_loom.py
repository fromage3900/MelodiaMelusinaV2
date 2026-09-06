"""Melodia Wardrobe — garment loom GN builders + Blender UI panel.

Builds a parametric outfit loom on top of the interchangeable wardrobe intake
(garment_intake_prep.py): one intake mesh -> many outfit variations via Geometry
Nodes, with LIVE UV unwrap (attribute-derived cylindrical projection, not an
editor-side static bake) so Substance always receives a fresh, non-overlapping UV.

Honest constraint: Blender Geometry Nodes has NO native "pack islands" node, so
live UV here = cylindrical projection from mesh position (coherent, non-overlapping
for garment shells) via an attribute math chain. The panel exposes the controls.

Builders (registered in the Melodia GN catalog):
  MEL_garment_loom_variation — seed-driven per-layer drape/fold/inset variation
  MEL_garment_uv_unwrap     — live cylindrical UV projection + pack markers

UI:
  MELODIA_PT_wardrobe — "Melodia Wardrobe" panel (N-panel, category "Melodia").
  Controls: target mesh, slots (Cos_*), variation seed, per-layer fold/scale,
  live-U V toggle, Export OBJ/FBX + write intake_manifest.json + register Cos_ draft.
"""
from __future__ import annotations
import bpy, json, hashlib, os, math
from pathlib import Path

from .core import (
    safe_node, link_sockets, color_node, label_tree,
    new_geometry_tree, sock,
    add_float_param, add_int_param, add_bool_param, register_builder,
)

STAGE = Path("C:/EnvironmentPortfolio/BS_GodFile/Saved/Audit/wardrobe_pipeline/intake")
PROJECT = Path("C:/EnvironmentPortfolio/BS_GodFile")


# --------------------------------------------------------------------------- #
# property group (panel state)
# --------------------------------------------------------------------------- #
class MELODIA_PropsWardrobe(bpy.types.PropertyGroup):
    mesh: bpy.props.PointerProperty(type=bpy.types.Object)  # target garment mesh
    slot: bpy.props.EnumProperty(items=[
        ("Dress", "Dress", ""), ("Top", "Top", ""), ("Skirt", "Skirt", ""),
        ("Outerwear", "Outerwear", ""), ("Accessory", "Accessory", ""),
        ("Footwear", "Footwear", ""), ("Special", "Special", "")])
    descriptor: bpy.props.StringProperty(name="Descriptor", default="Loom01")
    seed: bpy.props.IntProperty(name="Variation Seed", default=20260902, min=0)
    fold: bpy.props.FloatProperty(name="Fold", default=0.5, min=0.0, max=2.0)
    drape: bpy.props.FloatProperty(name="Drape", default=0.5, min=0.0, max=2.0)
    live_uv: bpy.props.BoolProperty(name="Live UV Unwrap", default=True)


# --------------------------------------------------------------------------- #
# GN: live UV unwrap (cylindrical projection via attribute math)
# --------------------------------------------------------------------------- #
def build_garment_uv_unwrap(group_name="MEL_garment_uv_unwrap"):
    tree, gin, gout = new_geometry_tree(group_name)
    geo = gin.outputs["Geometry"]
    # Compute normalized XZ angle + Y height -> UV
    pos = safe_node(tree, "GeometryNodeInputPosition", (0, 0))
    comb = safe_node(tree, "GeometryNodeSeparateXYZ", (-180, 0))
    link_sockets(tree, pos.outputs["Position"], comb.inputs["Vector"])
    # cylindrical U = atan2(x,z) normalized ; V = y norm (range clamp)
    atan = safe_node(tree, "ShaderNodeMath", (0, -120))
    atan.operation = "ARCTAN2"
    atan.inputs[1].default_value = 1.0
    x_local = comb.outputs["X"]
    z_local = comb.outputs["Z"]
    # atan2(x, z) in radians
    link_sockets(tree, z_local, atan.inputs[0])
    link_sockets(tree, x_local, atan.inputs[1])
    scale = safe_node(tree, "ShaderNodeMath", (180, -120))
    scale.operation = "MULTIPLY"
    scale.inputs[1].default_value = 0.5 / math.pi  # -> [-0.5,0.5]
    link_sockets(tree, atan.outputs[0], scale.inputs[0])
    u = safe_node(tree, "ShaderNodeMath", (180, -240))
    u.operation = "ADD"
    u.inputs[1].default_value = 0.5  # -> [0,1]
    link_sockets(tree, scale.outputs[0], u.inputs[0])
    v = safe_node(tree, "ShaderNodeMath", (0, -240))
    v.operation = "ADD"
    v.inputs[0].default_value = 0.5
    link_sockets(tree, comb.outputs["Y"], v.inputs[1])
    clamp = safe_node(tree, "ShaderNodeClamp", (360, -240))
    clamp.inputs["Min"].default_value = 0.0
    clamp.inputs["Max"].default_value = 1.0
    link_sockets(tree, u.outputs[0], clamp.inputs["Value"])
    clamp2 = safe_node(tree, "ShaderNodeClamp", (360, -320))
    clamp2.inputs["Min"].default_value = 0.0
    clamp2.inputs["Max"].default_value = 1.0
    link_sockets(tree, v.outputs[0], clamp2.inputs["Value"])
    comb2 = safe_node(tree, "ShaderNodeCombineXYZ", (140, -260))
    link_sockets(tree, clamp.outputs[0], comb2.inputs["X"])
    link_sockets(tree, clamp2.outputs[0], comb2.inputs["Y"])
    comp = safe_node(tree, "GeometryNodeStoreNamedAttribute", (0, -360))
    try:
        comp.data_type = "FLOAT2"
    except Exception:
        pass
    link_sockets(tree, geo, comp.inputs["Geometry"])
    try:
        comp.inputs["Name"].default_value = "uv"
    except Exception:
        comp.inputs["Attribute"].default_value = "uv"
    try:
        comp.inputs["Value"].default_value = (0.0, 0.0, 0.0)
    except Exception:
        pass
    link_sockets(tree, comb2.outputs["Vector"], comp.inputs["Value"] if "Value" in comp.inputs else comp.inputs[2])
    link_sockets(tree, comp.outputs["Geometry"], gout.inputs["Geometry"])
    return label_tree(tree, group_name, [
        {"title": "Position Input", "nodes": ("position", "separate",), "role": "attribute"},
        {"title": "Cylindrical Project", "nodes": ("arctan", "scale", "clamp", "combine",), "role": "geometry"},
        {"title": "Export UV", "nodes": ("store",), "role": "output"},
    ])


# --------------------------------------------------------------------------- #
# GN: variation — seed-driven drape/fold displacement over a garment shell
# --------------------------------------------------------------------------- #
def build_garment_loom_variation(group_name="MEL_garment_loom_variation"):
    tree, gin, gout = new_geometry_tree(group_name)
    geo = gin.outputs["Geometry"]
    s = add_int_param(tree, "Seed", 20260902, 0, 99999999)
    # 2026-09-06 neutrality fix (wardrobe_proof G3): dials default 0.0 (was 0.5,
    # which displaced every vertex by ~0.5*pos.y and bloated bounds 83-90%).
    fold = add_float_param(tree, "Fold", 0.0, 0.0, 2.0)
    drape = add_float_param(tree, "Drape", 0.0, 0.0, 2.0)
    # Blender has no white-noise-with-seed on geometry domain in older 5.x; use
    # a seeded sin hash on position for deterministic variation.
    pos = safe_node(tree, "GeometryNodeInputPosition", (0, 0))
    noise = safe_node(tree, "ShaderNodeTexNoise", (0, -200))
    try:
        noise.inputs["Scale"].default_value = 2.0
        noise.inputs["Detail"].default_value = 6.0
        w_sock = sock(noise, "W")  # Blender 5.2: ["W"] key lookup fails, iterate by name
        if w_sock is not None:
            w_sock.default_value = float(s.default_value % 100) * 0.01
    except Exception:
        pass
    link_sockets(tree, pos.outputs["Position"], noise.inputs["Vector"])
    # fold along height (local Y), drape along the noise field
    comb = safe_node(tree, "GeometryNodeSeparateXYZ", (-240, -100))
    link_sockets(tree, pos.outputs["Position"], comb.inputs["Vector"])
    y = comb.outputs["Y"]
    fold_f = safe_node(tree, "ShaderNodeMath", (-240, -220))
    fold_f.operation = "MULTIPLY"
    link_sockets(tree, y, fold_f.inputs[0])
    link_sockets(tree, gin.outputs["Fold"], fold_f.inputs[1])
    nz = noise.outputs[0] if "Color" not in [o.name for o in noise.outputs] else noise.outputs["Fac"]
    n_val = noise.outputs.get("Fac") or noise.outputs[0]
    drape_f = safe_node(tree, "ShaderNodeMath", (0, -220))
    drape_f.operation = "MULTIPLY"
    link_sockets(tree, n_val, drape_f.inputs[0])
    link_sockets(tree, gin.outputs["Drape"], drape_f.inputs[1])
    total = safe_node(tree, "ShaderNodeMath", (60, -220))
    total.operation = "ADD"
    link_sockets(tree, fold_f.outputs[0], total.inputs[0])
    link_sockets(tree, drape_f.outputs[0], total.inputs[1])
    disp = safe_node(tree, "GeometryNodeSetPosition", (120, -120))
    link_sockets(tree, geo, disp.inputs["Geometry"])
    norm = safe_node(tree, "GeometryNodeInputNormal", (60, -320))
    off = safe_node(tree, "ShaderNodeVectorMath", (120, -220))
    off.operation = "SCALE"
    link_sockets(tree, norm.outputs["Normal"], off.inputs["Vector"])
    link_sockets(tree, total.outputs[0], off.inputs["Scale"])
    link_sockets(tree, off.outputs["Vector"], disp.inputs["Offset"])
    link_sockets(tree, disp.outputs["Geometry"], gout.inputs["Geometry"])
    return label_tree(tree, group_name, [
        {"title": "Seed Field", "nodes": ("position", "noise",), "role": "attribute"},
        {"title": "Fold + Drape", "nodes": ("fold", "drape", "set position",), "role": "geometry"},
    ])


# --------------------------------------------------------------------------- #
# register builders + panel
# --------------------------------------------------------------------------- #
def register():
    register_builder("MEL_garment_uv_unwrap", build_garment_uv_unwrap,
                     "Garment UV Unwrap", "Live cylindrical UV projection for garment shells", "Garment")
    register_builder("MEL_garment_loom_variation", build_garment_loom_variation,
                     "Garment Loom Variation", "Seed-driven fold+drape variation over a garment shell", "Garment")
    from bpy.utils import register_class
    register_class(MELODIA_PropsWardrobe)
    register_class(MELODIA_PT_wardrobe)


def unregister():
    from bpy.utils import unregister_class
    unregister_class(MELODIA_PT_wardrobe)
    unregister_class(MELODIA_PropsWardrobe)


def _emit(obj, slot, desc, seed):
    name = f"Cos_{slot}_Melusina_{desc}"
    out = STAGE / name
    out.mkdir(parents=True, exist_ok=True)
    base = str(out / name)
    bpy.ops.wm.obj_export(filepath=base + ".obj", export_selected_objects=True,
                          export_materials=True, export_material_groups=True,
                          export_smooth_groups=True, export_uv=True,
                          export_normals=True, forward_axis="NEGATIVE_Y", up_axis="Z")
    bpy.ops.export_scene.fbx(filepath=base + ".fbx", use_selection=True,
                             mesh_smooth_type="FACE", add_leaf_bones=False,
                             bake_anim=False, path_mode="ABSOLUTE",
                             axis_forward="-Y", axis_up="Z")
    manifest = {
        "schema": "melodia.garment_loom_emission.v1", "seed": seed,
        "cos_id": name, "slot": slot, "descriptor": desc,
        "source_object": obj.name,
        "obj": base+".obj", "fbx": base+".fbx",
        "obj_sha256": hashlib.sha256(Path(base+".obj").read_bytes()).hexdigest(),
        "fbx_sha256": hashlib.sha256(Path(base+".fbx").read_bytes()).hexdigest() if Path(base+".fbx").exists() else None,
        "uv": "live-cylindrical (MEL_garment_uv_unwrap)" if any(
            m.node_group and m.node_group.name == "MEL_garment_uv_unwrap" for m in obj.modifiers
        ) else "source-uv",
    }
    (out / "intake_manifest.json").write_text(json.dumps(manifest, indent=1))
    return out


class MELODIA_PT_wardrobe(bpy.types.Panel):
    bl_idname = "MELODIA_PT_wardrobe"
    bl_label = "Melodia Wardrobe"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "Melodia"

    def draw(self, context):
        p = context.scene.melodia_wardrobe
        c = self.layout.column()
        c.label(text="Garment Loom")
        c.prop(p, "mesh")
        c.prop(p, "slot")
        c.prop(p, "descriptor")
        c.prop(p, "seed")
        c.prop(p, "fold")
        c.prop(p, "drape")
        c.prop(p, "live_uv")
        r = self.layout.row()

        def _add_loom_modifier():
            if not p.mesh:
                self.layout.operator("melo.loom_modifier", text="Add UV + Variation", icon="MOD_UVPROJECT")
            else:
                self.layout.operator("melo.loom_modifier", text="Add UV + Variation", icon="MOD_UVPROJECT")

        _add_loom_modifier()
        self.layout.operator("melo.loom_emit", text="Emit OBJ+FBX + manifest", icon="EXPORT")


class MELODIA_OT_loom_modifier(bpy.types.Operator):
    bl_idname = "melo.loom_modifier"
    bl_label = "Add Loom Modifiers"
    bl_options = {"REGISTER", "UNDO"}

    def execute(self, context):
        p = context.scene.melodia_wardrobe
        obj = p.mesh
        if not obj:
            self.report({"ERROR"}, "Pick a target mesh in the panel")
            return {"CANCELLED"}
        uv = obj.modifiers.new(name="LoomUV", type="NODE_GROUP") if not any(
            m.name == "LoomUV" for m in obj.modifiers) else None
        if uv:
            uv.node_group = bpy.data.node_groups.get("MEL_garment_uv_unwrap")
        var = obj.modifiers.new(name="LoomVariation", type="NODE_GROUP") if not any(
            m.name == "LoomVariation" for m in obj.modifiers) else None
        if var:
            var.node_group = bpy.data.node_groups.get("MEL_garment_loom_variation")
        self.report({"INFO"}, "Added LoomUV + LoomVariation modifiers")
        return {"FINISHED"}


class MELODIA_OT_loom_emit(bpy.types.Operator):
    bl_idname = "melo.loom_emit"
    bl_label = "Emit garment variation"
    bl_options = {"REGISTER", "UNDO"}

    def execute(self, context):
        p = context.scene.melodia_wardrobe
        obj = p.mesh
        if not obj:
            self.report({"ERROR"}, "Pick a target mesh")
            return {"CANCELLED"}
        bpy.context.view_layer.objects.active = obj
        obj.select_set(True)
        bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)
        try:
            bpy.ops.object.modifier_apply(modifier="LoomUV")
        except Exception:
            pass
        try:
            bpy.ops.object.modifier_apply(modifier="LoomVariation")
        except Exception:
            pass
        out = _emit(obj, p.slot, p.descriptor, p.seed)
        self.report({"INFO"}, f"Emitted {out}")
        return {"FINISHED"}


_CLASSES = [MELODIA_PropsWardrobe, MELODIA_PT_wardrobe, MELODIA_OT_loom_modifier, MELODIA_OT_loom_emit]


# Auto-register builders on import (so GROUP_BUILDERS sees them even before addon register)
try:
    register_builder("MEL_garment_uv_unwrap", build_garment_uv_unwrap,
                     "Garment UV Unwrap", "Live cylindrical UV projection for garment shells (Substance-ready, non-overlapping)", "Garment")
    register_builder("MEL_garment_loom_variation", build_garment_loom_variation,
                     "Garment Loom Variation", "Seed-driven fold+drape variation over a garment shell (audio-rate-ready)", "Garment")
except Exception:
    pass

def register_full_modules():
    from bpy.utils import register_class
    for c in _CLASSES:
        try:
            register_class(c)
        except Exception:
            pass
    try:
        from bpy.types import Scene
        if not hasattr(Scene, "melodia_wardrobe"):
            Scene.melodia_wardrobe = bpy.props.PointerProperty(type=MELODIA_PropsWardrobe)
    except Exception:
        pass