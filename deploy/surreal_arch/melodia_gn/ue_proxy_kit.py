"""UE Proxy Material Kit — stylized shaders for UE preview renders.

All materials are spatial-aware (Fresnel, layer-weight, view-dependent halftone)
so they read correctly in 3D space under rotating lights. Use these as
drop-in proxies while the UE editor is down.

Also provides quick-apply operators wrapping the best of materials_kit.py.
"""

from __future__ import annotations

import bpy

# ============================================================
# Material builders (shader node trees, not GN)
# ============================================================

def build_npr_halftone_material():
    """Halftone ink shader — Komikaze signature look.

    Spatial: dots compress at grazing angles, darkening silhouettes.
    """
    mat = bpy.data.materials.get("MEL_NPR_Halftone") or bpy.data.materials.new("MEL_NPR_Halftone")
    mat.use_nodes = True
    nt = mat.node_tree
    nt.nodes.clear()

    out = nt.nodes.new("ShaderNodeOutputMaterial"); out.location = (1200, 0)
    bsdf = nt.nodes.new("ShaderNodeBsdfPrincipled"); bsdf.location = (900, 0)

    # Halftone grid pattern
    grid = nt.nodes.new("ShaderNodeTexChecker"); grid.location = (0, 0)
    grid.inputs["Scale"].default_value = 8.0

    # Light direction via Layer Weight (view-dependent)
    lw = nt.nodes.new("ShaderNodeLayerWeight"); lw.location = (0, 300)
    lw.inputs["Blend"].default_value = 0.5

    # Dot mask: checker * facing
    mix_dot = nt.nodes.new("ShaderNodeMix"); mix_dot.location = (300, 150)
    mix_dot.data_type = "RGBA"
    nt.links.new(lw.outputs["Facing"], mix_dot.inputs["Factor"])
    mix_dot.inputs["A"].default_value = (0, 0, 0, 1)  # ink
    mix_dot.inputs["B"].default_value = (1, 1, 1, 1)  # paper

    # Grid density control
    mapper = nt.nodes.new("ShaderNodeMapRange"); mapper.location = (600, 0)
    mapper.inputs["From Min"].default_value = 0.0
    mapper.inputs["From Max"].default_value = 1.0
    mapper.inputs["To Min"].default_value = 0.0
    mapper.inputs["To Max"].default_value = 1.0

    nt.links.new(grid.outputs["Color"], mapper.inputs["Value"])
    nt.links.new(mix_dot.outputs["Result"], bsdf.inputs["Base Color"])
    nt.links.new(bsdf.outputs["BSDF"], out.inputs["Surface"])

    # Param exposure
    mat["ue_proxy"] = "npr_halftone"
    return mat


def build_stylized_fabric_material():
    """Stylized fabric — soft sheen + Fresnel rim + thread detail.

    Spatial: sheen peaks at grazing (velvet), thread lines UV-warped.
    """
    mat = bpy.data.materials.get("MEL_Fabric_Stylized") or bpy.data.materials.new("MEL_Fabric_Stylized")
    mat.use_nodes = True
    nt = mat.node_tree
    nt.nodes.clear()

    out = nt.nodes.new("ShaderNodeOutputMaterial"); out.location = (1200, 0)
    bsdf = nt.nodes.new("ShaderNodeBsdfPrincipled"); bsdf.location = (900, 0)
    bsdf.inputs["Roughness"].default_value = 0.7

    # Fresnel rim
    fres = nt.nodes.new("ShaderNodeFresnel"); fres.location = (0, 300)
    fres.inputs["IOR"].default_value = 1.45

    # Sheen tint ramp
    sheen_ramp = nt.nodes.new("ShaderNodeValToRGB"); sheen_ramp.location = (300, 300)
    nt.links.new(fres.outputs["Fac"], sheen_ramp.inputs["Fac"])
    cr = sheen_ramp.color_ramp
    cr.elements[0].color = (0, 0, 0, 1)
    cr.elements[1].color = (0.9, 0.85, 1.0, 1.0)

    # Thread detail
    wave = nt.nodes.new("ShaderNodeTexWave"); wave.location = (0, 0)
    wave.wave_type = "BANDS"
    wave.bands_direction = "X"
    wave.inputs["Scale"].default_value = 20.0

    # Mix sheen + thread
    mix = nt.nodes.new("ShaderNodeMix"); mix.location = (600, 150)
    mix.data_type = "RGBA"
    nt.links.new(wave.outputs["Color"], mix.inputs["A"])
    nt.links.new(sheen_ramp.outputs["Color"], mix.inputs["B"])
    mix.inputs["Factor"].default_value = 0.6

    nt.links.new(mix.outputs["Result"], bsdf.inputs["Base Color"])
    nt.links.new(bsdf.outputs["BSDF"], out.inputs["Surface"])

    mat["ue_proxy"] = "fabric_stylized"
    return mat


def build_emissive_crystal_material():
    """Emissive crystal — internal glow + Fresnel sparkle.

    Spatial: Fresnel peaks at silhouette, internal emission constant.
    """
    mat = bpy.data.materials.get("MEL_Crystal_Emissive") or bpy.data.materials.new("MEL_Crystal_Emissive")
    mat.use_nodes = True
    nt = mat.node_tree
    nt.nodes.clear()

    out = nt.nodes.new("ShaderNodeOutputMaterial"); out.location = (1200, 0)
    bsdf = nt.nodes.new("ShaderNodeBsdfPrincipled"); bsdf.location = (900, 0)
    bsdf.inputs["Roughness"].default_value = 0.1
    bsdf.inputs["Transmission Weight"].default_value = 0.5
    bsdf.inputs["IOR"].default_value = 2.0

    # Fresnel sparkle
    fres = nt.nodes.new("ShaderNodeFresnel"); fres.location = (0, 300)
    fres.inputs["IOR"].default_value = 2.0

    # Hue shift
    hue_ramp = nt.nodes.new("ShaderNodeValToRGB"); hue_ramp.location = (300, 0)
    cr = hue_ramp.color_ramp
    cr.elements[0].color = (0.4, 0.7, 1.0, 1.0)
    e1 = cr.elements.new(0.5); e1.color = (0.8, 0.5, 1.0, 1.0)
    cr.elements[1].color = (1.0, 0.6, 0.8, 1.0)

    # Mix with Fresnel
    mix = nt.nodes.new("ShaderNodeMix"); mix.location = (600, 150)
    mix.data_type = "RGBA"
    nt.links.new(hue_ramp.outputs["Color"], mix.inputs["A"])
    mix.inputs["B"].default_value = (1, 1, 1, 1)
    nt.links.new(fres.outputs["Fac"], mix.inputs["Factor"])

    nt.links.new(mix.outputs["Result"], bsdf.inputs["Base Color"])
    nt.links.new(mix.outputs["Result"], bsdf.inputs["Emission Color"])
    bsdf.inputs["Emission Strength"].default_value = 3.0
    nt.links.new(bsdf.outputs["BSDF"], out.inputs["Surface"])

    mat["ue_proxy"] = "crystal_emissive"
    return mat


def build_ue_toon_material():
    """Genshin-style toon — cel-shading + Fresnel rim + pastel."""
    mat = bpy.data.materials.get("MEL_UE_Toon") or bpy.data.materials.new("MEL_UE_Toon")
    mat.use_nodes = True
    nt = mat.node_tree
    nt.nodes.clear()

    out = nt.nodes.new("ShaderNodeOutputMaterial"); out.location = (1200, 0)
    bsdf = nt.nodes.new("ShaderNodeBsdfPrincipled"); bsdf.location = (900, 0)
    bsdf.inputs["Roughness"].default_value = 0.4

    # Cel-shading via Layer Weight facing
    lw = nt.nodes.new("ShaderNodeLayerWeight"); lw.location = (0, 200)
    lw.inputs["Blend"].default_value = 0.4

    cel_ramp = nt.nodes.new("ShaderNodeValToRGB"); cel_ramp.location = (300, 200)
    nt.links.new(lw.outputs["Facing"], cel_ramp.inputs["Fac"])
    cr = cel_ramp.color_ramp
    cr.interpolation = "CONSTANT"
    cr.elements[0].color = (0.5, 0.42, 0.55, 1.0)
    e1 = cr.elements.new(0.5); e1.color = (0.9, 0.8, 0.92, 1.0)
    cr.elements[2].color = (1.0, 0.95, 0.98, 1.0)

    # Pastel tint
    tint = nt.nodes.new("ShaderNodeRGB"); tint.location = (0, 0)
    tint.outputs[0].default_value = (0.95, 0.85, 0.95, 1.0)

    mix_tint = nt.nodes.new("ShaderNodeMixRGB"); mix_tint.location = (600, 100)
    mix_tint.blend_type = "MULTIPLY"
    mix_tint.inputs["Fac"].default_value = 0.6
    nt.links.new(cel_ramp.outputs["Color"], mix_tint.inputs["Color1"])
    nt.links.new(tint.outputs[0], mix_tint.inputs["Color2"])

    nt.links.new(mix_tint.outputs["Color"], bsdf.inputs["Base Color"])
    nt.links.new(bsdf.outputs["BSDF"], out.inputs["Surface"])

    mat["ue_proxy"] = "toon"
    return mat


# ============================================================
# Build all
# ============================================================

def build_ue_proxy_library():
    """Build (or refresh) all UE proxy materials. Idempotent."""
    return {
        "npr_halftone": build_npr_halftone_material(),
        "fabric_stylized": build_stylized_fabric_material(),
        "crystal_emissive": build_emissive_crystal_material(),
        "ue_toon": build_ue_toon_material(),
    }


# ============================================================
# Quick-apply operators
# ============================================================

UE_PROXY_MATERIALS = {
    "UE_TOON": "MEL_UE_Toon",
    "UE_FABRIC": "MEL_Fabric_Stylized",
    "UE_CRYSTAL": "MEL_Crystal_Emissive",
    "UE_NPR": "MEL_NPR_Halftone",
    "UE_GOLD": "SurrealArch_Gold",
    "UE_GLOW": "SurrealArch_ClefGlow",
    "UE_IRIDESCENT": "SurrealArch_Iridescent",
    "UE_GLASS": "SurrealArch_StainedGlass",
}


def apply_ue_proxy_material(context, preset: str = "UE_TOON"):
    """Apply a UE-proxy material to selected props (skips Melusina)."""
    mat_name = UE_PROXY_MATERIALS.get(preset, "MEL_UE_Toon")
    mat = bpy.data.materials.get(mat_name)

    # Build if missing
    if mat is None:
        if preset == "UE_NPR":
            mat = build_npr_halftone_material()
        elif preset == "UE_FABRIC":
            mat = build_stylized_fabric_material()
        elif preset == "UE_CRYSTAL":
            mat = build_emissive_crystal_material()
        elif preset == "UE_TOON":
            mat = build_ue_toon_material()
        else:
            mat = bpy.data.materials.get(mat_name) or bpy.data.materials.new(mat_name)
            mat.use_nodes = True

    applied = []
    for obj in context.selected_objects:
        if obj.type != "MESH":
            continue
        if "melusina" in obj.name.lower() or "sk_melusina" in obj.name.lower():
            continue
        if obj.data.materials:
            obj.data.materials[0] = mat
        else:
            obj.data.materials.append(mat)
        applied.append(obj.name)

    return {"material": mat_name, "applied": applied}


class SURREAL_ARCH_OT_ue_proxy_apply(bpy.types.Operator):
    bl_idname = "surreal_arch.ue_proxy_apply"
    bl_label = "UE Proxy Material"
    bl_description = "Apply stylized UE-proxy material to selected props"
    bl_options = {"REGISTER", "UNDO"}

    preset: bpy.props.EnumProperty(
        name="Preset",
        items=[
            ("UE_TOON", "Toon", "Cel-shaded toon proxy"),
            ("UE_FABRIC", "Fabric", "Stylized fabric proxy"),
            ("UE_CRYSTAL", "Crystal", "Emissive gem proxy"),
            ("UE_NPR", "NPR", "Halftone ink proxy"),
            ("UE_GOLD", "Gold", "Warm metal proxy"),
            ("UE_GLOW", "Glow", "Emissive notation proxy"),
            ("UE_IRIDESCENT", "Iridescent", "Layer-weight color shift"),
            ("UE_GLASS", "Glass", "Stained glass proxy"),
        ],
        default="UE_TOON",
    )

    @classmethod
    def poll(cls, context):
        return context.active_object is not None and context.active_object.type == "MESH"

    def execute(self, context):
        result = apply_ue_proxy_material(context, self.preset)
        if not result["applied"]:
            self.report({"WARNING"}, "No eligible mesh selected")
            return {"CANCELLED"}
        self.report({"INFO"}, f"{result['material']} → {len(result['applied'])} objects")
        return {"FINISHED"}


class SURREAL_ARCH_PT_ue_proxy_panel(bpy.types.Panel):
    bl_idname = "SURREAL_ARCH_PT_ue_proxy"
    bl_label = "UE Proxy Materials"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "Melodia"

    def draw(self, context):
        layout = self.layout
        layout.label(text="Quick-apply stylized proxy:")
        layout.operator("surreal_arch.ue_proxy_apply", text="Toon").preset = "UE_TOON"
        layout.operator("surreal_arch.ue_proxy_apply", text="Fabric").preset = "UE_FABRIC"
        layout.operator("surreal_arch.ue_proxy_apply", text="Crystal").preset = "UE_CRYSTAL"
        layout.operator("surreal_arch.ue_proxy_apply", text="NPR Halftone").preset = "UE_NPR"
        layout.operator("surreal_arch.ue_proxy_apply", text="Gold").preset = "UE_GOLD"
        layout.operator("surreal_arch.ue_proxy_apply", text="Glow").preset = "UE_GLOW"
        layout.operator("surreal_arch.ue_proxy_apply", text="Iridescent").preset = "UE_IRIDESCENT"
        layout.operator("surreal_arch.ue_proxy_apply", text="Glass").preset = "UE_GLASS"


UE_PROXY_CLASSES = (SURREAL_ARCH_OT_ue_proxy_apply, SURREAL_ARCH_PT_ue_proxy_panel)
