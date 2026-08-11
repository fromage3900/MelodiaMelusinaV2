"""NPC Material Factory — creates MToon master material and per-archetype MPCs.

Integrates with existing MPC_SakuraDream for runtime parameter driving.
"""
from __future__ import annotations

import json
from dataclasses import asdict
from pathlib import Path
from typing import Any

try:
    import unreal
except ImportError:
    unreal = None


# ──────────────────────────────────────────────────────────────────────
# Material Paths & Constants
# ──────────────────────────────────────────────────────────────────────

MASTER_MATERIAL_PATH = "/Game/NPCs/Materials/MM_Melodia_NPC_MToon"
MPC_BASE_PATH = "/Game/NPCs/Materials/MPC"
MASTER_MATERIAL_INSTANCE_PATH = "/Game/NPCs/Materials/MI_Melodia_NPC_MToon_Base"

# MToon Parameter Names (match VRM4U MToon material)
MTOON_PARAMS = {
    # Base
    "BaseColor": "Color",
    "ShadeColor": "Color",
    "ShadeShift": "Scalar",
    "ShadeToony": "Scalar",
    "LightingInfluence": "Scalar",

    # MatCap
    "MatCapBlend": "Scalar",
    "MatCapColor": "Color",
    "MatCapTexture": "Texture",

    # Rim
    "RimColor": "Color",
    "RimFresnelPower": "Scalar",
    "RimLift": "Scalar",

    # Outline
    "OutlineWidth": "Scalar",
    "OutlineColor": "Color",
    "OutlineLightingMix": "Scalar",

    # Emission
    "EmissionColor": "Color",
    "EmissionStrength": "Scalar",

    # Subsurface
    "SubsurfaceColor": "Color",
    "SubsurfaceAmount": "Scalar",

    # NPC Custom (exposed to MPC)
    "NPC_DreamIntensity": "Scalar",
    "NPC_ColorShift_R": "Scalar",
    "NPC_ColorShift_G": "Scalar",
    "NPC_ColorShift_B": "Scalar",
    "NPC_ColorShift_A": "Scalar",
    "NPC_WindStrength": "Scalar",
    "NPC_GlowIntensity": "Scalar",
}


# ──────────────────────────────────────────────────────────────────────
# MPC Parameter Builders
# ──────────────────────────────────────────────────────────────────────

def build_archetype_mpc_params(archetype_name: str, palette_data: dict) -> dict[str, Any]:
    """Build MPC parameter dictionary for an archetype."""
    mtoon = palette_data.get("mtoon_params", {})

    # Ensure all NPC params have _r, _g, _b, _a suffixes for vector params
    params = {}
    for k, v in mtoon.items():
        if k.endswith(("_r", "_g", "_b", "_a")):
            # Already split
            params[k] = v
        elif isinstance(v, (list, tuple)) and len(v) == 4:
            # Split vector into components
            params[f"{k}_r"] = v[0]
            params[f"{k}_g"] = v[1]
            params[f"{k}_b"] = v[2]
            params[f"{k}_a"] = v[3]
        else:
            params[k] = v

    return params


def build_global_npc_mpc_params() -> dict[str, Any]:
    """Global NPC MPC params that all archetypes inherit (driven by MPC_SakuraDream)."""
    return {
        # Runtime-driven parameters (set by gameplay systems)
        "NPC_DreamIntensity": 1.0,
        "NPC_ColorShift_R": 0.0,
        "NPC_ColorShift_G": 0.0,
        "NPC_ColorShift_B": 0.0,
        "NPC_ColorShift_A": 0.0,
        "NPC_WindStrength": 1.0,
        "NPC_GlowIntensity": 0.0,
    }


# ──────────────────────────────────────────────────────────────────────
# Unreal Material Creation (run in Editor)
# ──────────────────────────────────────────────────────────────────────

def create_master_material() -> bool:
    """Create the master MToon material for NPCs.

    This creates a material that mimics VRM MToon shader using Unreal's Material Editor.
    Run once in Editor to establish the master material.
    """
    if unreal is None:
        return False

    # Check if already exists
    if unreal.EditorAssetLibrary.does_asset_exist(MASTER_MATERIAL_PATH):
        unreal.log(f"Master material already exists: {MASTER_MATERIAL_PATH}")
        return True

    try:
        # Create material
        mat_factory = unreal.MaterialFactoryNew()
        mat = unreal.AssetToolsHelpers.get_asset_tools().create_asset(
            "MM_Melodia_NPC_MToon",
            "/Game/NPCs/Materials",
            unreal.Material,
            mat_factory
        )

        if not mat:
            unreal.log_error("Failed to create master material")
            return False

        # Configure material
        mat.set_editor_property("shading_model", unreal.MaterialShadingModel.MSM_UNLIT)
        mat.set_editor_property("blend_mode", unreal.BlendMode.BLEND_OPAQUE)
        mat.set_editor_property("two_sided", True)
        mat.set_editor_property("use_emissive_for_dynamic_area_lighting", False)

        # Create material expressions
        editor_lib = unreal.MaterialEditingLibrary

        # Base Color Parameter
        base_color = editor_lib.create_material_expression(mat, unreal.MaterialExpressionVectorParameter, -400, -200)
        base_color.set_editor_property("parameter_name", "BaseColor")
        base_color.set_editor_property("default_value", unreal.LinearColor(1.0, 1.0, 1.0, 1.0))
        editor_lib.connect_material_property(base_color, "RGB", unreal.MaterialProperty.MP_BASE_COLOR)

        # Shade Color Parameter
        shade_color = editor_lib.create_material_expression(mat, unreal.MaterialExpressionVectorParameter, -400, 0)
        shade_color.set_editor_property("parameter_name", "ShadeColor")
        shade_color.set_editor_property("default_value", unreal.LinearColor(0.2, 0.15, 0.25, 1.0))
        editor_lib.connect_material_property(shade_color, "RGB", unreal.MaterialProperty.MP_EMISSIVE_COLOR)  # Simplified

        # Scalar Parameters
        scalar_params = {
            "ShadeShift": (0.0, -400, 200),
            "ShadeToony": (0.5, -400, 300),
            "LightingInfluence": (0.8, -400, 400),
            "MatCapBlend": (0.0, -400, 500),
            "RimFresnelPower": (0.5, -200, 0),
            "RimLift": (0.0, -200, 100),
            "OutlineWidth": (0.03, 0, -200),
            "OutlineLightingMix": (0.0, 0, -100),
            "EmissionStrength": (0.0, 200, -200),
            "SubsurfaceAmount": (0.0, 200, -100),
            "NPC_DreamIntensity": (1.0, 400, -200),
            "NPC_WindStrength": (1.0, 400, -100),
            "NPC_GlowIntensity": (0.0, 400, 0),
        }

        for name, (default, x, y) in scalar_params.items():
            expr = editor_lib.create_material_expression(mat, unreal.MaterialExpressionScalarParameter, x, y)
            expr.set_editor_property("parameter_name", name)
            expr.default_value = default

        # Vector Parameters for Color Shift
        color_shift = editor_lib.create_material_expression(mat, unreal.MaterialExpressionVectorParameter, 400, 100)
        color_shift.set_editor_property("parameter_name", "NPC_ColorShift")
        color_shift.set_editor_property("default_value", unreal.LinearColor(0.0, 0.0, 0.0, 0.0))

        # Save
        unreal.EditorAssetLibrary.save_asset(MASTER_MATERIAL_PATH)
        unreal.log(f"Created master material: {MASTER_MATERIAL_PATH}")
        return True

    except Exception as e:
        unreal.log_error(f"Failed to create master material: {e}")
        return False


def create_archetype_mpc(archetype_name: str, params: dict) -> bool:
    """Create Material Parameter Collection for an archetype."""
    if unreal is None:
        return False

    mpc_path = f"{MPC_BASE_PATH}/MPC_NPC_{archetype_name}"

    if unreal.EditorAssetLibrary.does_asset_exist(mpc_path):
        # Update existing
        mpc = unreal.EditorAssetLibrary.load_asset(mpc_path)
    else:
        # Create new
        mpc_factory = unreal.MaterialParameterCollectionFactoryNew()
        mpc = unreal.AssetToolsHelpers.get_asset_tools().create_asset(
            f"MPC_NPC_{archetype_name}",
            MPC_BASE_PATH,
            unreal.MaterialParameterCollection,
            mpc_factory
        )

    if not mpc:
        unreal.log_error(f"Failed to create/load MPC for {archetype_name}")
        return False

    # Add/update scalar parameters
    for param_name, value in params.items():
        if isinstance(value, (int, float)):
            _set_mpc_scalar(mpc, param_name, float(value))
        elif isinstance(value, (list, tuple)) and len(value) == 4:
            _set_mpc_vector(mpc, param_name, unreal.LinearColor(*value))

    unreal.EditorAssetLibrary.save_asset(mpc_path)
    unreal.log(f"Created/Updated MPC: {mpc_path}")
    return True


def _set_mpc_scalar(mpc, name: str, value: float):
    """Set scalar parameter in MPC."""
    params = mpc.get_editor_property("scalar_parameters") or []
    # Find existing
    for p in params:
        if p.get_editor_property("parameter_info").name == name:
            p.set_editor_property("parameter_value", value)
            mpc.set_editor_property("scalar_parameters", params)
            return
    # Add new
    new_param = unreal.ScalarParameterValue()
    param_info = unreal.MaterialParameterInfo()
    param_info.name = name
    new_param.set_editor_property("parameter_info", param_info)
    new_param.set_editor_property("parameter_value", value)
    params.append(new_param)
    mpc.set_editor_property("scalar_parameters", params)


def _set_mpc_vector(mpc, name: str, value: unreal.LinearColor):
    """Set vector parameter in MPC."""
    params = mpc.get_editor_property("vector_parameters") or []
    for p in params:
        if p.get_editor_property("parameter_info").name == name:
            p.set_editor_property("parameter_value", value)
            mpc.set_editor_property("vector_parameters", params)
            return
    new_param = unreal.VectorParameterValue()
    param_info = unreal.MaterialParameterInfo()
    param_info.name = name
    new_param.set_editor_property("parameter_info", param_info)
    new_param.set_editor_property("parameter_value", value)
    params.append(new_param)
    mpc.set_editor_property("vector_parameters", params)


def create_material_instance(archetype_name: str) -> str:
    """Create Material Instance for an archetype from master material."""
    if unreal is None:
        return ""

    mi_path = f"/Game/NPCs/Materials/MI_NPC_{archetype_name}"

    if unreal.EditorAssetLibrary.does_asset_exist(mi_path):
        return mi_path

    try:
        master = unreal.EditorAssetLibrary.load_asset(MASTER_MATERIAL_PATH)
        if not master:
            unreal.log_error(f"Master material not found: {MASTER_MATERIAL_PATH}")
            return ""

        mi_factory = unreal.MaterialInstanceConstantFactoryNew()
        mi = unreal.AssetToolsHelpers.get_asset_tools().create_asset(
            f"MI_NPC_{archetype_name}",
            "/Game/NPCs/Materials",
            unreal.MaterialInstanceConstant,
            mi_factory
        )

        if mi:
            mi.set_editor_property("parent", master)
            unreal.EditorAssetLibrary.save_asset(mi_path)
            unreal.log(f"Created material instance: {mi_path}")

        return mi_path
    except Exception as e:
        unreal.log_error(f"Failed to create material instance for {archetype_name}: {e}")
        return ""


def setup_all_materials(palette_json_path: Path = None) -> dict:
    """Full material setup pipeline for all archetypes."""
    if unreal is None:
        return {"error": "Not in Unreal environment"}

    if palette_json_path is None:
        palette_json_path = Path(__file__).parent / "archetype_palettes.json"

    if not palette_json_path.exists():
        return {"error": f"Palette file not found: {palette_json_path}"}

    with open(palette_json_path, "r", encoding="utf-8") as f:
        palettes = json.load(f)

    results = {}

    # 1. Create master material
    results["master_material"] = create_master_material()

    # 2. Create global NPC MPC (extends MPC_SakuraDream)
    global_params = build_global_npc_mpc_params()
    results["global_mpc"] = create_archetype_mpc("Global", global_params)

    # 3. Create per-archetype MPCs and material instances
    for arch_name, data in palettes.items():
        arch_params = build_archetype_mpc_params(arch_name, data)
        results[f"mpc_{arch_name}"] = create_archetype_mpc(arch_name, arch_params)
        results[f"mi_{arch_name}"] = create_material_instance(arch_name)

    return results


if __name__ == "__main__":
    if unreal:
        results = setup_all_materials()
        print(json.dumps(results, indent=2))
    else:
        print("NPC Material Factory - Run in Unreal Editor Python Console")
        print("Usage: import gmm.npc.material_factory as mf; mf.setup_all_materials()")