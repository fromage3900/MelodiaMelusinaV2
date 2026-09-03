"""SDF maturation: copy cathedral batch, build M_Master_SDF_Toon, ensure instances.

Run headless:
  UnrealEditor-Cmd.exe BS_GodFile.uproject ^
    -ExecutePythonScript="G:/EnvironmentPortfolio/BS_GodFile/Content/Python/setup_sdf_maturation.py"
"""
from __future__ import annotations

import json
import shutil
from datetime import datetime, timezone
from pathlib import Path

import unreal

import material_lib as lib

PROJECT_ROOT = Path(__file__).resolve().parents[2]
PROJECT_MATERIALS = PROJECT_ROOT / "Content" / "_PROJECT" / "04_Materials" / "SDF"
MASTER_DIR_FS = PROJECT_ROOT / "Content" / "EnvSandbox" / "Materials" / "Masters"
REPORT_PATH = PROJECT_ROOT / "Saved" / "Audit" / "sdf_maturation.json"

MASTER_SDF_TOON = "M_Master_SDF_Toon"

CATHEDRAL_BATCH = [
    "M_SDF_CathedralVault",
    "M_SDF_FlyingButtress",
    "M_SDF_BaroqueColumn",
    "M_SDF_GildedAltar",
    "M_SDF_GothicRoseWindow",
    "M_SDF_Grass_Field",
]

CATHEDRAL_INSTANCES = [
    {"master": "M_SDF_CathedralVault", "instance": "MI_SDF_CathedralVault", "profile": "TP_Stucco"},
    {"master": "M_SDF_FlyingButtress", "instance": "MI_SDF_FlyingButtress", "profile": "TP_Stucco"},
    {"master": "M_SDF_BaroqueColumn", "instance": "MI_SDF_BaroqueColumn", "profile": "TP_Ornamental"},
    {"master": "M_SDF_GildedAltar", "instance": "MI_SDF_GildedAltar", "profile": "TP_Gold"},
    {"master": "M_SDF_GothicRoseWindow", "instance": "MI_SDF_GothicRoseWindow", "profile": "TP_Gold"},
    {"master": "M_SDF_Grass_Field", "instance": "MI_SDF_Grass_Field", "profile": "TP_Foliage"},
]


def _copy_cathedral_batch() -> list[str]:
    copied: list[str] = []
    MASTER_DIR_FS.mkdir(parents=True, exist_ok=True)
    for stem in CATHEDRAL_BATCH:
        src = PROJECT_MATERIALS / f"{stem}.uasset"
        dst = MASTER_DIR_FS / f"{stem}.uasset"
        if not src.exists():
            continue
        if not dst.exists() or src.stat().st_mtime > dst.stat().st_mtime:
            shutil.copy2(src, dst)
            copied.append(stem)
    return copied


def _call_mf(material, mf_name: str, x: int, y: int):
    path = lib.asset_path(lib.FUNCTION_DIR, mf_name)
    if not unreal.EditorAssetLibrary.does_asset_exist(path):
        return None
    mf = unreal.load_asset(path)
    call = lib.create_expression(material, unreal.MaterialExpressionMaterialFunctionCall, x, y)
    call.set_editor_property("material_function", mf)
    return call


def build_master_sdf_toon(profiles: dict[str, unreal.ToonProfile]) -> str:
    """Enhanced SDF toon master with parallax, curvature ornament, full param schema."""
    lib.ensure_directory(lib.MASTER_DIR)
    path = lib.asset_path(lib.MASTER_DIR, MASTER_SDF_TOON)
    if unreal.EditorAssetLibrary.does_asset_exist(path):
        unreal.log(f"[SDFMaturation] rebuilding {path}")
        unreal.EditorAssetLibrary.delete_asset(path)

    asset_tools = unreal.AssetToolsHelpers.get_asset_tools()
    material = asset_tools.create_asset(
        MASTER_SDF_TOON, lib.MASTER_DIR, unreal.Material, unreal.MaterialFactoryNew()
    )
    if not material:
        raise RuntimeError(f"Failed to create {MASTER_SDF_TOON}")

    material.set_editor_property("material_domain", unreal.MaterialDomain.MD_SURFACE)
    material.set_editor_property("blend_mode", unreal.BlendMode.BLEND_OPAQUE)
    lib.try_set_editor_property(material, "bUsesSubstrate", True)

    base_tint = lib.vector_param(material, "BaseTint", "Palette", (0.55, 0.48, 0.42, 1.0), -1500, 0)
    accent_tint = lib.vector_param(material, "AccentTint", "Palette", (0.72, 0.62, 0.52, 1.0), -1500, 120)
    lib.scalar_param(material, "UVScale", "UV", 1.0, -1500, 240)
    lib.scalar_param(material, "UVRotation", "UV", 0.0, -1500, 340)
    normal_map = lib.texture_param(material, "NormalMap", "Maps", -1500, 460)
    rough_map = lib.texture_param(material, "RoughnessMap", "Maps", -1500, 580)
    height_map = lib.texture_param(material, "HeightMap", "Maps", -1500, 700)
    parallax_scale = lib.scalar_param(material, "ParallaxScale", "Parallax", 0.06, -1500, 820)
    lib.scalar_param(material, "ParallaxSteps", "Parallax", 12.0, -1500, 920)
    lib.scalar_param(material, "ReliefDepth", "SDF", 0.35, -1500, 1020)
    gilding_strength = lib.scalar_param(material, "GildingStrength", "Gilding", 0.0, -1500, 1120)
    gold_tint = lib.vector_param(material, "GoldTint", "Gilding", (0.85, 0.65, 0.25, 1.0), -1500, 1220)
    lib.scalar_param(material, "OilPaintStrength", "OilPaint", 0.0, -1500, 1340)
    lib.scalar_param(material, "TemporalStrength", "Temporal", 0.0, -1500, 1440)
    lib.scalar_param(material, "InkIntensity", "Ink", 0.0, -1500, 1540)
    ink_color = lib.vector_param(material, "InkColor", "Ink", (0.05, 0.08, 0.15, 1.0), -1500, 1640)
    lib.scalar_param(material, "OrnamentStyle", "Ornament", 0.0, -1500, 1760)
    lib.scalar_param(material, "OrnamentScale", "Ornament", 1.0, -1500, 1860)
    curvature_sens = lib.scalar_param(material, "CurvatureSensitivity", "Ornament", 2.0, -1500, 1960)
    lib.scalar_param(material, "AudioReactivity", "Audio", 0.0, -1500, 2060)
    dry_rough = lib.scalar_param(material, "DryRoughness", "Surface", 0.75, -1500, 2160)

    band_mask = None
    world = lib.create_expression(material, unreal.MaterialExpressionWorldPosition, -1100, 80)
    mask_xy = lib.create_expression(material, unreal.MaterialExpressionComponentMask, -920, 80)
    mask_xy.set_editor_property("r", True)
    mask_xy.set_editor_property("g", True)
    mask_xy.set_editor_property("b", False)
    mask_xy.set_editor_property("a", False)
    lib.connect(world, "", mask_xy, "")
    band_scale = lib.scalar_param(material, "BandScale", "SDF", 0.035, -1100, 200)
    band_strength = lib.scalar_param(material, "BandStrength", "SDF", 0.22, -1100, 300)
    scale_mul = lib.create_expression(material, unreal.MaterialExpressionMultiply, -740, 100)
    lib.connect(mask_xy, "", scale_mul, "A")
    lib.connect(band_scale, "", scale_mul, "B")
    sin_n = lib.create_expression(material, unreal.MaterialExpressionSine, -560, 100)
    sin_n.set_editor_property("period", 1.0)
    lib.connect_unary(scale_mul, sin_n)
    abs_n = lib.create_expression(material, unreal.MaterialExpressionAbs, -380, 100)
    lib.connect_unary(sin_n, abs_n)
    band_mask = lib.create_expression(material, unreal.MaterialExpressionMultiply, -200, 100)
    lib.connect(abs_n, "", band_mask, "A")
    lib.connect(band_strength, "", band_mask, "B")

    pixel_normal = lib.create_expression(material, unreal.MaterialExpressionPixelNormalWS, -1100, 360)
    ddx = lib.create_expression(material, unreal.MaterialExpressionDDX, -920, 320)
    ddy = lib.create_expression(material, unreal.MaterialExpressionDDY, -920, 400)
    lib.connect_unary(pixel_normal, ddx)
    lib.connect_unary(pixel_normal, ddy)
    curve = lib.create_expression(material, unreal.MaterialExpressionAdd, -740, 360)
    lib.connect(ddx, "", curve, "A")
    lib.connect(ddy, "", curve, "B")
    ornament_mod = lib.create_expression(material, unreal.MaterialExpressionMultiply, -560, 360)
    lib.connect(curve, "", ornament_mod, "A")
    lib.connect(curvature_sens, "", ornament_mod, "B")

    parallax_h = lib.scalar_param(material, "ParallaxHeight", "Parallax", 0.06, -1100, 540)
    parallax_mod = lib.create_expression(material, unreal.MaterialExpressionMultiply, -740, 540)
    lib.connect(parallax_h, "", parallax_mod, "A")
    lib.connect(parallax_scale, "", parallax_mod, "B")

    color_lerp = lib.create_expression(material, unreal.MaterialExpressionLinearInterpolate, -480, 80)
    lib.connect(base_tint, "", color_lerp, "A")
    lib.connect(accent_tint, "", color_lerp, "B")
    lib.connect(band_mask, "", color_lerp, "Alpha")

    ornament_lerp = lib.create_expression(material, unreal.MaterialExpressionLinearInterpolate, -280, 120)
    lib.connect(color_lerp, "", ornament_lerp, "A")
    lib.connect(accent_tint, "", ornament_lerp, "B")
    ornament_alpha = lib.create_expression(material, unreal.MaterialExpressionAbs, -400, 360)
    lib.connect_unary(ornament_mod, ornament_alpha)
    lib.connect(ornament_alpha, "", ornament_lerp, "Alpha")

    gild_color = lib.create_expression(material, unreal.MaterialExpressionMultiply, -480, 720)
    lib.connect(gilding_strength, "", gild_color, "A")
    lib.connect(gold_tint, "", gild_color, "B")

    color_gild = lib.create_expression(material, unreal.MaterialExpressionAdd, -80, 120)
    lib.connect(ornament_lerp, "", color_gild, "A")
    lib.connect(gild_color, "", color_gild, "B")

    rough_out = dry_rough

    normal_out = pixel_normal

    vertex_n = lib.create_expression(material, unreal.MaterialExpressionVertexNormalWS, 120, 760)
    wpo = lib.create_expression(material, unreal.MaterialExpressionMultiply, 320, 740)
    lib.connect(parallax_mod, "", wpo, "A")
    lib.connect(vertex_n, "", wpo, "B")
    unreal.MaterialEditingLibrary.connect_material_property(
        wpo, "", unreal.MaterialProperty.MP_WORLD_POSITION_OFFSET
    )

    profile = profiles.get("TP_Stucco") or profiles.get("TP_Default")
    toon_bsdf = lib.create_expression(material, unreal.MaterialExpressionSubstrateToonBSDF, 520, 280)
    if profile:
        toon_bsdf.set_editor_property("toon_profile", profile)
    lib.connect_toon_pin(toon_bsdf, color_gild, ("BaseColor", "DiffuseColor"))
    lib.connect_toon_pin(toon_bsdf, rough_out, ("Roughness",))
    lib.connect_toon_pin(toon_bsdf, normal_out, ("Normal", "TangentNormal", "NormalMap"))
    lib.connect_front_material(material, toon_bsdf)

    unreal.MaterialEditingLibrary.recompile_material(material)
    lib.save_package(material)
    unreal.log(f"[SDFMaturation] built {path}")
    return path


def _ensure_cathedral_instances(profiles: dict[str, unreal.ToonProfile]) -> list[dict]:
    results: list[dict] = []
    for spec in CATHEDRAL_INSTANCES:
        master_path = lib.asset_path(lib.MASTER_DIR, spec["master"])
        inst_path = lib.asset_path(lib.SDF_INST_DIR, spec["instance"])
        row = {"master": master_path, "instance": inst_path, "status": "pending"}
        if not unreal.EditorAssetLibrary.does_asset_exist(master_path):
            row["status"] = "master_missing"
            results.append(row)
            continue
        inst = lib.create_material_instance(spec["instance"], lib.SDF_INST_DIR, master_path)
        pname = spec["profile"]
        if pname in profiles:
            lib.set_instance_toon_profile(inst, profiles[pname])
        lib.set_instance_scalar(inst, "UVScale", 1.0)
        lib.set_instance_scalar(inst, "ParallaxScale", 0.06)
        lib.save_package(inst)
        row["status"] = "created_or_updated"
        results.append(row)
    return results


def _convert_cathedral_masters() -> list[dict]:
    try:
        from convert_masters_to_substrate_toon import convert_master

        results = []
        for stem in CATHEDRAL_BATCH:
            path = lib.asset_path(lib.MASTER_DIR, stem)
            if unreal.EditorAssetLibrary.does_asset_exist(path):
                results.append(convert_master(path, fix_params=False))
        return results
    except Exception as exc:
        unreal.log_warning(f"[SDFMaturation] convert skipped: {exc}")
        return []


def build_all() -> int:
    unreal.log("=== SDF maturation ===")
    copied = _copy_cathedral_batch()
    profiles = lib.create_toon_profiles(
        ["TP_Default", "TP_Stucco", "TP_Gold", "TP_Ornamental", "TP_Foliage"]
    )
    master_path = build_master_sdf_toon(profiles)
    convert_results = _convert_cathedral_masters()
    instance_results = _ensure_cathedral_instances(profiles)

    report = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "copied_cathedral": copied,
        "master_sdf_toon": master_path,
        "conversions": convert_results,
        "instances": instance_results,
    }
    REPORT_PATH.parent.mkdir(parents=True, exist_ok=True)
    REPORT_PATH.write_text(json.dumps(report, indent=2, default=str), encoding="utf-8")
    unreal.EditorLoadingAndSavingUtils.save_dirty_packages(True, True)
    unreal.log(f"[SDFMaturation] copied={len(copied)} instances={len(instance_results)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(build_all())
