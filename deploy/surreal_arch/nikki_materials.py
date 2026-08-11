"""Infinity Nikki-inspired prop material helpers for SurrealArch.

This module is deliberately environment/prop scoped. It never edits existing
Melusina materials and only assigns fresh Melodia-owned material instances to
selected mesh objects.
"""

from __future__ import annotations

import json
import os
from pathlib import Path

import bpy
from bpy.props import BoolProperty, EnumProperty


KOMIKAZE_BLEND_PATH = (
    r"G:\programs\BlenderPlugins\plugins\Komikaze v2 (UNZIP ME) vfxmed\Komikaze v2.blend"
)
KOMIKAZE_LINEAR_HALFTONE = "Linear Gradient (Halftone)"
KOMIKAZE_TILER = "NTTiler [Komp]"

WRAP_LINEAR_HALFTONE = "MEL_NPR_LinearHalftone"
WRAP_TILER = "MEL_NPR_Tiler"
WRAP_SURFACE = "MEL_Mat_NikkiSurface"

NIKKI_VARIANTS = {
    "SUBTLE": {
        "label": "Subtle",
        "base": (0.86, 0.78, 0.92, 1.0),
        "accent": (0.55, 0.72, 0.98, 1.0),
        "mix": 0.42,
        "roughness": 0.62,
    },
    "DREAM": {
        "label": "Dream",
        "base": (0.92, 0.70, 0.86, 1.0),
        "accent": (0.72, 0.90, 1.0, 1.0),
        "mix": 0.52,
        "roughness": 0.48,
    },
    "HERO": {
        "label": "Hero",
        "base": (0.98, 0.82, 0.96, 1.0),
        "accent": (0.55, 0.94, 1.0, 1.0),
        "mix": 0.58,
        "roughness": 0.34,
    },
}

SKIP_NAME_TOKENS = ("melusina", "sk_melusina", "hair")


def _is_melusina_or_hair(obj: bpy.types.Object) -> bool:
    haystack = " ".join(
        str(part).lower()
        for part in (
            obj.name,
            getattr(obj.data, "name", ""),
            getattr(obj.parent, "name", "") if obj.parent else "",
        )
    )
    return any(token in haystack for token in SKIP_NAME_TOKENS)


def _append_node_group(name: str):
    existing = bpy.data.node_groups.get(name)
    if existing is not None:
        return existing
    if not os.path.exists(KOMIKAZE_BLEND_PATH):
        return None
    try:
        with bpy.data.libraries.load(KOMIKAZE_BLEND_PATH, link=False) as (src, dst):
            if name not in src.node_groups:
                return None
            dst.node_groups = [name]
    except Exception:
        return None
    return bpy.data.node_groups.get(name)


def _new_socket(group, name: str, in_out: str, socket_type: str):
    interface = getattr(group, "interface", None)
    if interface is not None and hasattr(interface, "new_socket"):
        try:
            return interface.new_socket(name=name, in_out=in_out, socket_type=socket_type)
        except TypeError:
            return interface.new_socket(name, in_out=in_out, socket_type=socket_type)
    sockets = group.inputs if in_out == "INPUT" else group.outputs
    return sockets.new(socket_type, name)


def _ensure_passthrough_group(name: str, *, inner_name: str | None = None):
    group = bpy.data.node_groups.get(name)
    if group is not None:
        return group

    group = bpy.data.node_groups.new(name, "ShaderNodeTree")
    group["melodia_role"] = "Nikki prototype wrapper"
    if inner_name:
        group["komikaze_source"] = inner_name
    _new_socket(group, "Color", "INPUT", "NodeSocketColor")
    _new_socket(group, "Fac", "INPUT", "NodeSocketFloat")
    _new_socket(group, "Color", "OUTPUT", "NodeSocketColor")

    nodes = group.nodes
    links = group.links
    inp = nodes.new("NodeGroupInput")
    inp.location = (-420, 0)
    out = nodes.new("NodeGroupOutput")
    out.location = (360, 0)
    reroute = nodes.new("NodeReroute")
    reroute.location = (0, 0)
    try:
        links.new(inp.outputs["Color"], reroute.inputs[0])
        links.new(reroute.outputs[0], out.inputs["Color"])
    except Exception:
        pass

    if inner_name:
        inner = _append_node_group(inner_name)
        if inner is not None:
            node = nodes.new("ShaderNodeGroup")
            node.node_tree = inner
            node.location = (-40, -220)
            node.label = f"Source: {inner_name}"
    return group


def ensure_nikki_wrapper_groups() -> dict[str, object]:
    """Append Komikaze sources and create Melodia-owned wrapper groups."""
    linear_source = _append_node_group(KOMIKAZE_LINEAR_HALFTONE)
    tiler_source = _append_node_group(KOMIKAZE_TILER)
    linear = _ensure_passthrough_group(WRAP_LINEAR_HALFTONE, inner_name=KOMIKAZE_LINEAR_HALFTONE)
    tiler = _ensure_passthrough_group(WRAP_TILER, inner_name=KOMIKAZE_TILER)
    surface = _ensure_passthrough_group(WRAP_SURFACE)
    return {
        "linear_source": linear_source,
        "tiler_source": tiler_source,
        "linear": linear,
        "tiler": tiler,
        "surface": surface,
    }


def _safe_node(tree, node_type: str, location: tuple[int, int]):
    node = tree.nodes.new(node_type)
    node.location = location
    return node


def build_nikki_surface_material(variant: str = "DREAM") -> bpy.types.Material:
    """Create or refresh the shared Nikki prototype material for a variant."""
    variant = variant if variant in NIKKI_VARIANTS else "DREAM"
    cfg = NIKKI_VARIANTS[variant]
    ensure_nikki_wrapper_groups()

    mat_name = f"{WRAP_SURFACE}_{cfg['label']}"
    mat = bpy.data.materials.get(mat_name) or bpy.data.materials.new(mat_name)
    mat.use_nodes = True
    mat["melodia_lane"] = "prop_env_only"
    mat["melodia_nikki_variant"] = variant
    mat["melodia_skip"] = "Melusina and hair objects are intentionally excluded"

    tree = mat.node_tree
    tree.nodes.clear()

    out = _safe_node(tree, "ShaderNodeOutputMaterial", (820, 0))
    bsdf = _safe_node(tree, "ShaderNodeBsdfPrincipled", (560, 0))
    ramp = _safe_node(tree, "ShaderNodeValToRGB", (300, 80))
    noise = _safe_node(tree, "ShaderNodeTexNoise", (40, 120))
    checker = _safe_node(tree, "ShaderNodeTexChecker", (40, -110))
    mix = _safe_node(tree, "ShaderNodeMix", (300, -110))

    try:
        noise.inputs["Scale"].default_value = 18.0
        noise.inputs["Detail"].default_value = 10.0
        noise.inputs["Roughness"].default_value = 0.58
    except Exception:
        pass
    try:
        checker.inputs["Scale"].default_value = 7.0
    except Exception:
        pass
    try:
        ramp.color_ramp.elements[0].position = 0.32
        ramp.color_ramp.elements[0].color = cfg["base"]
        ramp.color_ramp.elements[1].position = 1.0
        ramp.color_ramp.elements[1].color = cfg["accent"]
    except Exception:
        pass
    try:
        mix.data_type = "RGBA"
        mix.factor_mode = "UNIFORM"
        mix.inputs["Factor"].default_value = cfg["mix"]
    except Exception:
        pass
    try:
        bsdf.inputs["Roughness"].default_value = cfg["roughness"]
        bsdf.inputs["Metallic"].default_value = 0.0
    except Exception:
        pass

    linear_wrap = bpy.data.node_groups.get(WRAP_LINEAR_HALFTONE)
    tiler_wrap = bpy.data.node_groups.get(WRAP_TILER)
    for group, loc, label in (
        (tiler_wrap, (-260, -260), "MEL_NPR_Tiler"),
        (linear_wrap, (560, -260), "MEL_NPR_LinearHalftone"),
    ):
        if group is None:
            continue
        node = _safe_node(tree, "ShaderNodeGroup", loc)
        node.node_tree = group
        node.label = label

    links = tree.links
    try:
        links.new(noise.outputs["Fac"], ramp.inputs["Fac"])
        links.new(ramp.outputs["Color"], mix.inputs[6])
        links.new(checker.outputs["Color"], mix.inputs[7])
        links.new(mix.outputs[2], bsdf.inputs["Base Color"])
        links.new(bsdf.outputs["BSDF"], out.inputs["Surface"])
    except Exception:
        try:
            links.new(ramp.outputs["Color"], bsdf.inputs["Base Color"])
            links.new(bsdf.outputs["BSDF"], out.inputs["Surface"])
        except Exception:
            pass

    return mat


def _selected_targets(context, apply_to_all_selected: bool) -> list[bpy.types.Object]:
    candidates = context.selected_objects if apply_to_all_selected else [context.active_object]
    targets = []
    for obj in candidates or []:
        if obj is None or obj.type != "MESH":
            continue
        if _is_melusina_or_hair(obj):
            continue
        targets.append(obj)
    return targets


def apply_nikki_material(context, *, variant: str = "DREAM", apply_to_all_selected: bool = True) -> dict[str, object]:
    mat = build_nikki_surface_material(variant)
    targets = _selected_targets(context, apply_to_all_selected)
    applied = []
    skipped = []
    for obj in context.selected_objects or [context.active_object]:
        if obj and obj.type == "MESH" and _is_melusina_or_hair(obj):
            skipped.append(obj.name)
    for obj in targets:
        if obj.data.materials:
            obj.data.materials[0] = mat
        else:
            obj.data.materials.append(mat)
        obj["melodia_material_recipe"] = "NikkiProto: MM nikki tiles + Higgsas grid + MEL_NPR_Tiler + LinearHalftone"
        applied.append(obj.name)
    return {"material": mat.name, "applied": applied, "skipped": skipped}


class SURREAL_ARCH_OT_nikki_mat_apply(bpy.types.Operator):
    bl_idname = "surreal_arch.nikki_mat_apply"
    bl_label = "Nikki Mat (props)"
    bl_description = "Apply the Melodia Nikki prototype material to selected prop meshes only"
    bl_options = {"REGISTER", "UNDO"}

    variant: EnumProperty(
        name="Variant",
        items=[
            ("SUBTLE", "Subtle", "Portfolio stills: soft halftone and gentle pastel lift"),
            ("DREAM", "Dream", "Default pastel tile and halftone balance"),
            ("HERO", "Hero", "Stronger rim/sparkle read for sendoff props"),
        ],
        default="DREAM",
    )
    apply_to_all_selected: BoolProperty(
        name="Apply to all selected",
        default=True,
        description="Apply to all selected mesh props; otherwise only the active mesh",
    )

    @classmethod
    def poll(cls, context):
        obj = context.active_object
        return obj is not None and obj.type == "MESH"

    def invoke(self, context, event):
        return context.window_manager.invoke_props_dialog(self, width=340)

    def execute(self, context):
        result = apply_nikki_material(
            context,
            variant=self.variant,
            apply_to_all_selected=self.apply_to_all_selected,
        )
        applied = result["applied"]
        skipped = result["skipped"]
        context.scene["surreal_arch_nikki_mat_apply_last"] = json.dumps(result, sort_keys=True)
        if not applied:
            self.report({"WARNING"}, "No eligible prop meshes selected; Melusina/hair are skipped")
            return {"CANCELLED"}
        suffix = f"; skipped {len(skipped)} protected object(s)" if skipped else ""
        self.report({"INFO"}, f"Nikki material {result['material']} applied to {len(applied)} prop mesh(es){suffix}")
        return {"FINISHED"}


NIKKI_MATERIAL_CLASSES = (SURREAL_ARCH_OT_nikki_mat_apply,)
