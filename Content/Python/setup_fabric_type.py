"""Add FabricType system to M_Master_Toon_Universal.

FabricType scalar (0-7), FabricAnisoLevel, FabricWeaveScale, FabricWeaveStrength
parameters in group "10 | Nikki Iridescence & Sheen", plus a FabricWeaveNormal
Custom HLSL node for procedural fabric weave normal perturbation.

Run (editor Output Log):
  py "G:/EnvironmentPortfolio/BS_GodFile/Content/Python/setup_fabric_type.py"
"""
from __future__ import annotations

import unreal
import material_lib as lib

MASTER_PATH = "/Game/EnvSandbox/Materials/Masters/M_Master_Toon_Universal"
GROUP = "10 | Nikki Iridescence & Sheen"

FABRIC_WEAVE_HLSL = """float2 wUV = UV * WeaveScale;
float warp = 0.5 + 0.5 * sin(wUV.x * 6.28318);
float weft = 0.5 + 0.5 * sin(wUV.y * 6.28318);
float pattern = warp * weft;
float3 n;
n.xy = float2(ddx(pattern), ddy(pattern)) * WeaveStrength;
n.z = 1.0;
return normalize(n);
"""


def _existing_param_names(m) -> set[str]:
    names: set[str] = set()
    for expr in unreal.MaterialEditingLibrary.get_material_expressions(m) or []:
        for prop in ("parameter_name", "ParameterName"):
            try:
                raw = expr.get_editor_property(prop)
                if raw:
                    names.add(str(raw))
                    break
            except Exception:
                continue
    return names


def _existing_custom_names(m) -> set[str]:
    names: set[str] = set()
    for expr in unreal.MaterialEditingLibrary.get_material_expressions(m) or []:
        if type(expr).__name__ == "MaterialExpressionCustom":
            try:
                n = expr.get_editor_property("name")
                if n:
                    names.add(str(n))
            except Exception:
                continue
    return names


def _create_scalar(m, name: str, default: float, x: int, y: int,
                   min_v: float, max_v: float, *,
                   desc: str | None = None) -> None:
    param = lib.scalar_param(m, name, GROUP, default, x, y, desc=desc)
    param.set_editor_property("slider_min", min_v)
    param.set_editor_property("slider_max", max_v)


def main():
    if not unreal.EditorAssetLibrary.does_asset_exist(MASTER_PATH):
        unreal.log_error(f"[FabricType] Material not found: {MASTER_PATH}")
        return

    m = unreal.load_asset(MASTER_PATH)
    if not m:
        unreal.log_error("[FabricType] Failed to load material")
        return

    unreal.log(f"[FabricType] Loaded {MASTER_PATH}")

    existing = _existing_param_names(m)
    existing_custom = _existing_custom_names(m)
    created = []

    # FabricType — 0=Default 1=Cotton 2=Silk 3=Satin 4=Velvet 5=Wool 6=Chiffon 7=Sequins
    if "FabricType" not in existing:
        _create_scalar(m, "FabricType", 0.0, 100, 100, 0.0, 7.0,
                       desc="0=Default 1=Cotton 2=Silk 3=Satin 4=Velvet 5=Wool 6=Chiffon 7=Sequins")
        created.append("FabricType")
        unreal.log("  Created FabricType")
    else:
        unreal.log("  Skipped FabricType — already exists")

    # FabricAnisoLevel
    if "FabricAnisoLevel" not in existing:
        _create_scalar(m, "FabricAnisoLevel", 0.0, 260, 100, -1.0, 1.0)
        created.append("FabricAnisoLevel")
        unreal.log("  Created FabricAnisoLevel")
    else:
        unreal.log("  Skipped FabricAnisoLevel — already exists")

    # FabricWeaveScale
    if "FabricWeaveScale" not in existing:
        _create_scalar(m, "FabricWeaveScale", 48.0, 420, 100, 1.0, 128.0)
        created.append("FabricWeaveScale")
        unreal.log("  Created FabricWeaveScale")
    else:
        unreal.log("  Skipped FabricWeaveScale — already exists")

    # FabricWeaveStrength
    if "FabricWeaveStrength" not in existing:
        _create_scalar(m, "FabricWeaveStrength", 0.0, 580, 100, 0.0, 2.0)
        created.append("FabricWeaveStrength")
        unreal.log("  Created FabricWeaveStrength")
    else:
        unreal.log("  Skipped FabricWeaveStrength — already exists")

    # FabricWeaveNormal Custom HLSL node
    if "FabricWeaveNormal" in existing_custom:
        unreal.log("  Skipped FabricWeaveNormal HLSL node — already exists")
    else:
        hlsl = unreal.MaterialEditingLibrary.create_material_expression(
            m, unreal.MaterialExpressionCustom, 740, 100
        )
        hlsl.set_editor_property("name", "FabricWeaveNormal")
        hlsl.set_editor_property("code", FABRIC_WEAVE_HLSL)
        hlsl.set_editor_property("output_type", unreal.CustomMaterialOutputType.CMOT_FLOAT3)
        hlsl.set_editor_property("description", "Procedural fabric weave normal perturbation")

        uv_in = unreal.CustomInput()
        uv_in.set_editor_property("input_name", "UV")
        uv_in.set_editor_property("input", unreal.MaterialExpressionInput())
        ws_in = unreal.CustomInput()
        ws_in.set_editor_property("input_name", "WeaveScale")
        ws_in.set_editor_property("input", unreal.MaterialExpressionInput())
        wstr_in = unreal.CustomInput()
        wstr_in.set_editor_property("input_name", "WeaveStrength")
        wstr_in.set_editor_property("input", unreal.MaterialExpressionInput())

        hlsl.set_editor_property("inputs", [uv_in, ws_in, wstr_in])
        created.append("FabricWeaveNormal")
        unreal.log("  Created FabricWeaveNormal HLSL node")

    if created:
        unreal.log(f"[FabricType] Created: {', '.join(created)}")
    else:
        unreal.log("[FabricType] All items already exist — nothing new created")

    unreal.MaterialEditingLibrary.rebuild_material_editing_data(m)
    unreal.EditorAssetLibrary.save_loaded_asset(m, only_if_is_dirty=False)
    unreal.log("[FabricType] Material saved")


if __name__ == "__main__":
    main()
