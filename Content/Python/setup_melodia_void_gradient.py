"""Create M_MelodiaVoidGradient + MI_Show_MelodiaVoidGradient.

Unlit radial void → iri magenta/cyan/gold falloff matching site tokens
(--void #0d1224, --iri-magenta, --iri-cyan, --iri-gold). Used as the
default MI preview studio backdrop so plates never read as UE headquarters sky.

Run in-editor:
  py Content/Python/setup_melodia_void_gradient.py
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import material_lib as lib
import mi_preview_studio as studio

MASTER_DIR = "/Game/EnvSandbox/Materials/Masters"
SHOWCASE_DIR = "/Game/EnvSandbox/Materials/Instances/Showcase"
MASTER_NAME = "M_MelodiaVoidGradient"
MI_NAME = "MI_Show_MelodiaVoidGradient"
REPORT = studio.PROJECT_ROOT / "Saved" / "Audit" / "melodia_void_gradient.json"

# Site token linear RGB approximations (sRGB-ish for unlit emissive)
VOID = (0.051, 0.071, 0.141, 1.0)  # #0d1224
MAGENTA = (1.0, 0.431, 0.706, 1.0)  # #ff6eb4
CYAN = (0.4, 0.851, 1.0, 1.0)  # #66d9ff
GOLD = (1.0, 0.902, 0.4, 1.0)  # #ffe666
PEARL = (0.941, 0.863, 0.941, 1.0)  # #f0dcf0


def build_master(*, force: bool = False) -> str:
    import unreal

    lib.ensure_directory(MASTER_DIR)
    path = f"{MASTER_DIR}/{MASTER_NAME}.{MASTER_NAME}"
    material = None
    if unreal.EditorAssetLibrary.does_asset_exist(path):
        material = unreal.load_asset(path)
        if material and not force:
            unreal.log(f"[VoidGradient] reusing {path}")
            return path
        if material and force:
            lib.clear_material_graph(material)

    if not material:
        asset_tools = unreal.AssetToolsHelpers.get_asset_tools()
        material = asset_tools.create_asset(
            MASTER_NAME, MASTER_DIR, unreal.Material, unreal.MaterialFactoryNew()
        )
    if not material:
        raise RuntimeError(f"Failed to create {MASTER_NAME}")

    material.set_editor_property("material_domain", unreal.MaterialDomain.MD_SURFACE)
    material.set_editor_property("blend_mode", unreal.BlendMode.BLEND_OPAQUE)
    material.set_editor_property("shading_model", unreal.MaterialShadingModel.MSM_UNLIT)
    material.set_editor_property("two_sided", True)

    # Camera-facing radial: PixelNormalWS · CameraVectorWS → fresnel-ish rim
    # Prefer UV radial from center for cyclorama sphere (inside-out).
    texcoord = lib.create_expression(material, unreal.MaterialExpressionTextureCoordinate, -1200, 0)
    sub = lib.create_expression(material, unreal.MaterialExpressionSubtract, -980, 0)
    half = lib.create_expression(material, unreal.MaterialExpressionConstant, -1200, 120)
    half.set_editor_property("r", 0.5)
    lib.connect(texcoord, "", sub, "A")
    lib.connect(half, "", sub, "B")

    len2 = lib.create_expression(material, unreal.MaterialExpressionSquareRoot, -760, 0)
    # Length via Dot(V,V) then sqrt
    dot = lib.create_expression(material, unreal.MaterialExpressionDotProduct, -880, 0)
    lib.connect(sub, "", dot, "A")
    lib.connect(sub, "", dot, "B")
    lib.connect(dot, "", len2, "")

    radius = lib.scalar_param(material, "GradientRadius", "Void", 0.72, -760, 160)
    soft = lib.scalar_param(material, "GradientSoftness", "Void", 0.45, -760, 280)
    t = lib.create_expression(material, unreal.MaterialExpressionDivide, -540, 0)
    lib.connect(len2, "", t, "A")
    lib.connect(radius, "", t, "B")
    t_clamp = lib.create_expression(material, unreal.MaterialExpressionClamp, -360, 0)
    lib.connect(t, "", t_clamp, "")

    # Smoothstep-ish: saturate((x) / soft) powered
    soft_div = lib.create_expression(material, unreal.MaterialExpressionDivide, -360, 160)
    lib.connect(t_clamp, "", soft_div, "A")
    lib.connect(soft, "", soft_div, "B")
    soft_clamp = lib.create_expression(material, unreal.MaterialExpressionClamp, -180, 160)
    lib.connect(soft_div, "", soft_clamp, "")
    power = lib.create_expression(material, unreal.MaterialExpressionPower, -180, 0)
    two = lib.create_expression(material, unreal.MaterialExpressionConstant, -360, 280)
    two.set_editor_property("r", 1.6)
    lib.connect(soft_clamp, "", power, "Base")
    lib.connect(two, "", power, "Exp")

    void_c = lib.vector_param(material, "VoidColor", "Void", VOID, -1200, 400)
    mag_c = lib.vector_param(material, "IriMagenta", "Iri", MAGENTA, -1200, 560)
    cyan_c = lib.vector_param(material, "IriCyan", "Iri", CYAN, -1200, 720)
    gold_c = lib.vector_param(material, "IriGold", "Iri", GOLD, -1200, 880)
    pearl_c = lib.vector_param(material, "IriPearl", "Iri", PEARL, -1200, 1040)
    rim_strength = lib.scalar_param(material, "RimStrength", "Iri", 0.55, -760, 400)
    center_lift = lib.scalar_param(material, "CenterPearl", "Iri", 0.12, -760, 520)

    # Mid rim: lerp magenta → cyan by UV.x
    uv_x = lib.create_expression(material, unreal.MaterialExpressionComponentMask, -980, 560)
    uv_x.set_editor_property("r", True)
    uv_x.set_editor_property("g", False)
    uv_x.set_editor_property("b", False)
    uv_x.set_editor_property("a", False)
    lib.connect(texcoord, "", uv_x, "")
    mid_lerp = lib.create_expression(material, unreal.MaterialExpressionLinearInterpolate, -760, 640)
    lib.connect(mag_c, "", mid_lerp, "A")
    lib.connect(cyan_c, "", mid_lerp, "B")
    lib.connect(uv_x, "", mid_lerp, "Alpha")

    # Outer: blend mid with gold
    uv_y = lib.create_expression(material, unreal.MaterialExpressionComponentMask, -980, 720)
    uv_y.set_editor_property("r", False)
    uv_y.set_editor_property("g", True)
    uv_y.set_editor_property("b", False)
    uv_y.set_editor_property("a", False)
    lib.connect(texcoord, "", uv_y, "")
    outer = lib.create_expression(material, unreal.MaterialExpressionLinearInterpolate, -540, 720)
    lib.connect(mid_lerp, "", outer, "A")
    lib.connect(gold_c, "", outer, "B")
    lib.connect(uv_y, "", outer, "Alpha")

    rim_mul = lib.create_expression(material, unreal.MaterialExpressionMultiply, -180, 400)
    lib.connect(outer, "", rim_mul, "A")
    lib.connect(rim_strength, "", rim_mul, "B")

    # Center pearl lift on void
    pearl_mul = lib.create_expression(material, unreal.MaterialExpressionMultiply, -180, 560)
    lib.connect(pearl_c, "", pearl_mul, "A")
    lib.connect(center_lift, "", pearl_mul, "B")
    one_minus = lib.create_expression(material, unreal.MaterialExpressionOneMinus, 0, 0)
    lib.connect(power, "", one_minus, "")
    center = lib.create_expression(material, unreal.MaterialExpressionMultiply, 0, 160)
    lib.connect(pearl_mul, "", center, "A")
    lib.connect(one_minus, "", center, "B")

    void_base = lib.create_expression(material, unreal.MaterialExpressionAdd, 200, 80)
    lib.connect(void_c, "", void_base, "A")
    lib.connect(center, "", void_base, "B")

    rim_term = lib.create_expression(material, unreal.MaterialExpressionMultiply, 200, 280)
    lib.connect(rim_mul, "", rim_term, "A")
    lib.connect(power, "", rim_term, "B")

    emissive = lib.create_expression(material, unreal.MaterialExpressionAdd, 420, 160)
    lib.connect(void_base, "", emissive, "A")
    lib.connect(rim_term, "", emissive, "B")

    lib.connect(emissive, "", material, "EmissiveColor")
    unreal.MaterialEditingLibrary.recompile_material(material)
    unreal.EditorAssetLibrary.save_asset(path)
    unreal.log(f"[VoidGradient] built {path}")
    return path


def build_instance(master_path: str) -> str:
    import unreal

    lib.ensure_directory(SHOWCASE_DIR)
    mi = lib.create_material_instance(MI_NAME, SHOWCASE_DIR, master_path)
    if not mi:
        raise RuntimeError(f"Failed to create {MI_NAME}")
    mi_path = f"{SHOWCASE_DIR}/{MI_NAME}.{MI_NAME}"
    unreal.EditorAssetLibrary.save_asset(mi_path)
    return mi_path


# Soft channel bias on void params — real backdrop key differentiation
VOID_TINT_SPECS = {
    "MI_Show_MelodiaVoid_Sakura": {
        "VoidColor": (0.08, 0.05, 0.12, 1.0),
        "IriMagenta": (1.0, 0.55, 0.78, 1.0),
        "IriCyan": (0.55, 0.82, 1.0, 1.0),
        "IriGold": (1.0, 0.88, 0.55, 1.0),
        "CenterPearl": 0.18,
        "RimStrength": 0.62,
    },
    "MI_Show_MelodiaVoid_Cosmic": {
        "VoidColor": (0.02, 0.03, 0.12, 1.0),
        "IriMagenta": (0.65, 0.35, 1.0, 1.0),
        "IriCyan": (0.25, 0.75, 1.0, 1.0),
        "IriGold": (0.7, 0.55, 1.0, 1.0),
        "CenterPearl": 0.08,
        "RimStrength": 0.7,
    },
    "MI_Show_MelodiaVoid_Baroque": {
        "VoidColor": (0.08, 0.06, 0.05, 1.0),
        "IriMagenta": (0.95, 0.55, 0.45, 1.0),
        "IriCyan": (0.85, 0.75, 0.45, 1.0),
        "IriGold": (1.0, 0.85, 0.35, 1.0),
        "CenterPearl": 0.15,
        "RimStrength": 0.58,
    },
    "MI_Show_MelodiaVoid_Neutral": {
        "VoidColor": (0.05, 0.07, 0.11, 1.0),
        "IriMagenta": (0.85, 0.55, 0.75, 1.0),
        "IriCyan": (0.5, 0.8, 0.95, 1.0),
        "IriGold": (0.95, 0.88, 0.55, 1.0),
        "CenterPearl": 0.12,
        "RimStrength": 0.5,
    },
}


def build_tint_instances(master_path: str) -> dict[str, str]:
    import unreal

    out: dict[str, str] = {}
    for name, params in VOID_TINT_SPECS.items():
        mi = lib.create_material_instance(name, SHOWCASE_DIR, master_path)
        if not mi:
            continue
        for key, val in params.items():
            if isinstance(val, tuple):
                lib.set_instance_vector(mi, key, val)
            else:
                lib.set_instance_scalar(mi, key, float(val))
        mi_path = f"{SHOWCASE_DIR}/{name}.{name}"
        unreal.EditorAssetLibrary.save_asset(mi_path)
        out[name] = mi_path
        unreal.log(f"[VoidGradient] tint {mi_path}")
    return out


def main() -> int:
    force = "force" in sys.argv
    master = build_master(force=force)
    mi = build_instance(master)
    tints = build_tint_instances(master)
    report = {
        "master": master,
        "instance": mi,
        "tint_instances": tints,
        "default_backdrop_key": "Melodia_VoidGradient",
        "backdrop_keys": {
            "Melodia_VoidGradient": studio.MELODIA_VOID_MI,
            "Sakura_SoftVoid": studio.MELODIA_VOID_SAKURA,
            "Cosmic_DeepField": studio.MELODIA_VOID_COSMIC,
            "Baroque_WarmVault": studio.MELODIA_VOID_BAROQUE,
            "Studio_Neutral": studio.MELODIA_VOID_NEUTRAL,
        },
        "tokens": {
            "void": "#0d1224",
            "iri_magenta": "#ff6eb4",
            "iri_cyan": "#66d9ff",
            "iri_gold": "#ffe666",
        },
    }
    REPORT.parent.mkdir(parents=True, exist_ok=True)
    REPORT.write_text(json.dumps(report, indent=2), encoding="utf-8")
    if "json" in sys.argv:
        print(json.dumps(report, indent=2))
    else:
        print(report)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
