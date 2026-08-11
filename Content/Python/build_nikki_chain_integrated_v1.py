"""Build an additive Nikki character-family proof from the live Universal master.

This script deliberately duplicates the current Universal material before adding
the repaired Nikki presentation chain.  It never edits M_Master_Toon_Universal,
the V9 water master, or the V10 water master.  The output is a compile/render
proof asset until its instance family has been reviewed by a human.
"""
from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

import unreal


SOURCE = "/Game/EnvSandbox/Materials/Masters/M_Master_Toon_Universal"
TARGET = "/Game/EnvSandbox/Materials/Masters/M_Master_Toon_Universal_NikkiChainIntegratedV1"
INSTANCE_DIR = "/Game/EnvSandbox/Materials/Instances/NikkiIntegrated"
FUNCTIONS = {
    "dream": "/Game/EnvSandbox/Materials/Functions/MF_NikkiDreamGrade",
    "rim": "/Game/EnvSandbox/Materials/Functions/MF_NikkiRimGlow",
    "sparkle": "/Game/EnvSandbox/Materials/Functions/MF_NikkiSparkle",
    "iridescence": "/Game/EnvSandbox/Materials/Functions/MF_NikkiIridescenceSheen",
}
SPARKLE_MASK = "/Game/Alphas_Sparkles/T_Spark_Twinkle8"
REPORT = Path(unreal.Paths.project_saved_dir()) / "Audit" / "nikki_chain_integrated_v1.json"


def _asset_path(asset) -> str:
    if not asset:
        return ""
    try:
        return str(asset.get_path_name()).split(".", 1)[0]
    except Exception:
        return ""


def _expressions(material):
    return list(unreal.MaterialEditingLibrary.get_material_expressions(material) or [])


def _find(material, name: str):
    for expr in _expressions(material):
        if expr.get_name() == name:
            return expr
    return None


def _find_param(material, parameter_name: str):
    for expr in _expressions(material):
        try:
            if expr.get_editor_property("parameter_name") == parameter_name:
                return expr
        except Exception:
            continue
    return None


def _function_calls(material) -> dict[str, object]:
    calls = {}
    for expr in _expressions(material):
        if expr.get_class().get_name() != "MaterialExpressionMaterialFunctionCall":
            continue
        fn = expr.get_editor_property("material_function")
        path = _asset_path(fn)
        for key, wanted in FUNCTIONS.items():
            if path == wanted:
                calls[key] = expr
    return calls


def _function_call_paths(material) -> dict[str, str]:
    calls = _function_calls(material)
    result = {}
    for key, expr in calls.items():
        try:
            result[key] = _asset_path(expr.get_editor_property("material_function"))
        except Exception:
            result[key] = ""
    return result


def _create_expr(material, cls, x: int, y: int):
    return unreal.MaterialEditingLibrary.create_material_expression(material, cls, x, y)


def _scalar(material, name: str, default: float, x: int, y: int):
    found = _find_param(material, name)
    if found:
        return found
    node = _create_expr(material, unreal.MaterialExpressionScalarParameter, x, y)
    node.set_editor_property("parameter_name", name)
    node.set_editor_property("group", "Nikki Hero")
    node.set_editor_property("default_value", default)
    return node


def _vector(material, name: str, rgba: tuple[float, float, float, float], x: int, y: int):
    found = _find_param(material, name)
    if found:
        return found
    node = _create_expr(material, unreal.MaterialExpressionVectorParameter, x, y)
    node.set_editor_property("parameter_name", name)
    node.set_editor_property("group", "Nikki Hero")
    node.set_editor_property("default_value", unreal.LinearColor(*rgba))
    return node


def _connect(source, source_pin: str, target, target_pin: str) -> None:
    if not unreal.MaterialEditingLibrary.connect_material_expressions(
        source, source_pin, target, target_pin
    ):
        raise RuntimeError(
            f"Could not connect {source.get_name()}:{source_pin} -> "
            f"{target.get_name()}:{target_pin}"
        )


def _function_call(material, path: str, x: int, y: int):
    node = _create_expr(material, unreal.MaterialExpressionMaterialFunctionCall, x, y)
    fn = unreal.load_asset(path)
    if not fn:
        raise RuntimeError(f"Missing Nikki function: {path}")
    node.set_editor_property("material_function", fn)
    return node


def _ensure_chain(material):
    # Existing Universal graph contract.  We preserve Dream emissive and only
    # replace the color branch that already feeds the toon front material.
    dream = _find(material, "MaterialExpressionMaterialFunctionCall_0")
    color_mix = _find(material, "MaterialExpressionLinearInterpolate_2")
    normal_source = _find(material, "MaterialExpressionStaticSwitchParameter_12")
    if not dream or not color_mix or not normal_source:
        raise RuntimeError("Universal anchor nodes are missing; refusing graph mutation")

    calls = _function_calls(material)
    rim = calls.get("rim") or _function_call(material, FUNCTIONS["rim"], 12000, -950)
    sparkle = calls.get("sparkle") or _function_call(material, FUNCTIONS["sparkle"], 12400, -950)
    iridescence = calls.get("iridescence") or _function_call(
        material, FUNCTIONS["iridescence"], 12800, -950
    )

    rim_color = _vector(material, "NikkiRimColor", (0.44, 0.78, 1.0, 1.0), 11100, -1260)
    rim_intensity = _scalar(material, "NikkiRimIntensity", 1.15, 11100, -1160)
    rim_width = _scalar(material, "NikkiRimWidth", 0.48, 11100, -1060)
    rim_glow = _scalar(material, "NikkiRimGlowIntensity", 0.65, 11100, -960)
    bloom_boost = _scalar(material, "NikkiRimBloomBoost", 0.22, 11100, -860)

    sparkle_color = _vector(material, "NikkiSparkleColor", (0.75, 0.90, 1.0, 1.0), 11600, -1260)
    sparkle_intensity = _scalar(material, "NikkiSparkleIntensity", 0.55, 11600, -1160)
    sparkle_threshold = _scalar(material, "NikkiSparkleThreshold", 0.72, 11600, -1060)
    sparkle_uv = _create_expr(material, unreal.MaterialExpressionTextureCoordinate, 11600, -900)
    sparkle_mask = _find_param(material, "NikkiSparkleMask")
    if not sparkle_mask:
        sparkle_mask = _create_expr(
            material, unreal.MaterialExpressionTextureObjectParameter, 11600, -800
        )
        sparkle_mask.set_editor_property("parameter_name", "NikkiSparkleMask")
        sparkle_mask.set_editor_property("group", "Nikki Hero")
        texture = unreal.load_asset(SPARKLE_MASK)
        if texture:
            sparkle_mask.set_editor_property("texture", texture)

    irid_amount = _scalar(material, "NikkiIridescence", 0.28, 12200, -1260)
    irid_tint = _vector(material, "NikkiIridescenceTint", (0.48, 0.78, 1.0, 1.0), 12200, -1160)
    irid_power = _scalar(material, "NikkiIridescencePower", 4.0, 12200, -1060)
    fabric_sheen = _scalar(material, "NikkiFabricSheen", 0.18, 12200, -960)
    sheen_tint = _vector(material, "NikkiSheenTint", (0.78, 0.88, 1.0, 1.0), 12200, -860)

    # Dream-grade is the canonical base for the expanded chain.
    _connect(dream, "Color", rim, "BaseColor")
    _connect(normal_source, "", rim, "Normal")
    _connect(rim_color, "", rim, "RimColor")
    _connect(rim_intensity, "", rim, "RimIntensity")
    _connect(rim_width, "", rim, "RimWidth")
    _connect(rim_glow, "", rim, "GlowIntensity")
    _connect(bloom_boost, "", rim, "BloomBoost")

    _connect(rim, "Color", sparkle, "BaseColor")
    _connect(sparkle_uv, "", sparkle, "UV")
    _connect(sparkle_mask, "", sparkle, "SparkleMask")
    _connect(sparkle_intensity, "", sparkle, "SparkleIntensity")
    _connect(sparkle_threshold, "", sparkle, "SparkleThreshold")
    _connect(sparkle_color, "", sparkle, "SparkleColor")

    _connect(sparkle, "Color", iridescence, "BaseColor")
    _connect(normal_source, "", iridescence, "Normal")
    _connect(irid_amount, "", iridescence, "Iridescence")
    _connect(irid_tint, "", iridescence, "IridescenceTint")
    _connect(irid_power, "", iridescence, "IridescencePower")
    _connect(fabric_sheen, "", iridescence, "FabricSheen")
    _connect(sheen_tint, "", iridescence, "SheenTint")

    # The pre-existing color mix remains the canonical toon gate.  Only its B
    # input is replaced; all DreamGrade emissive and substrate routing survive.
    _connect(iridescence, "Color", color_mix, "B")
    return {
        "dream": dream.get_name(),
        "rim": rim.get_name(),
        "sparkle": sparkle.get_name(),
        "iridescence": iridescence.get_name(),
        "color_anchor": color_mix.get_name(),
        "normal_anchor": normal_source.get_name(),
    }


def _ensure_instances(parent) -> list[dict]:
    """Create review-only Nikki family instances; never reparent existing heroes."""
    if not unreal.EditorAssetLibrary.does_directory_exist(INSTANCE_DIR):
        unreal.EditorAssetLibrary.make_directory(INSTANCE_DIR)
    specs = {
        "MI_NikkiIntegrated_Dream": {
            "NikkiRimIntensity": 0.95,
            "NikkiSparkleIntensity": 0.32,
            "NikkiIridescence": 0.16,
            "NikkiRimColor": (0.46, 0.78, 1.0, 1.0),
        },
        "MI_NikkiIntegrated_Moonlit": {
            "NikkiRimIntensity": 1.25,
            "NikkiSparkleIntensity": 0.58,
            "NikkiIridescence": 0.30,
            "NikkiRimColor": (0.68, 0.56, 1.0, 1.0),
        },
        "MI_NikkiIntegrated_Bloom": {
            "NikkiRimIntensity": 1.42,
            "NikkiSparkleIntensity": 0.78,
            "NikkiIridescence": 0.42,
            "NikkiRimColor": (1.0, 0.72, 0.48, 1.0),
        },
    }
    tools = unreal.AssetToolsHelpers.get_asset_tools()
    result = []
    for name, values in specs.items():
        path = f"{INSTANCE_DIR}/{name}"
        instance = unreal.load_asset(path)
        created = False
        if not instance:
            instance = tools.create_asset(
                name,
                INSTANCE_DIR,
                unreal.MaterialInstanceConstant,
                unreal.MaterialInstanceConstantFactoryNew(),
            )
            created = True
        if not instance:
            raise RuntimeError(f"Could not create Nikki instance: {path}")
        unreal.MaterialEditingLibrary.set_material_instance_parent(instance, parent)
        # The canonical Universal graph gates its toon character branch behind
        # this static switch.  Enable it only on the new proof-family assets;
        # existing Nikki instances remain untouched.
        unreal.MaterialEditingLibrary.set_material_instance_static_switch_parameter_value(
            instance, "bNikkiHero", True
        )
        for key, value in values.items():
            if isinstance(value, tuple):
                unreal.MaterialEditingLibrary.set_material_instance_vector_parameter_value(
                    instance, key, unreal.LinearColor(*value)
                )
            else:
                unreal.MaterialEditingLibrary.set_material_instance_scalar_parameter_value(
                    instance, key, float(value)
                )
        unreal.EditorAssetLibrary.save_loaded_asset(instance)
        result.append({"path": path, "created_this_run": created, "parent": TARGET})
    return result


def main() -> dict:
    if not unreal.EditorAssetLibrary.does_asset_exist(SOURCE):
        raise RuntimeError(f"Source Universal master missing: {SOURCE}")

    target = unreal.EditorAssetLibrary.load_asset(TARGET)
    created = False
    if not target:
        if not unreal.EditorAssetLibrary.duplicate_asset(SOURCE, TARGET):
            raise RuntimeError(f"Could not duplicate Universal master to {TARGET}")
        target = unreal.load_asset(TARGET)
        created = True
    if not target:
        raise RuntimeError(f"Target Nikki chain master did not load: {TARGET}")

    anchors = _ensure_chain(target)
    unreal.MaterialEditingLibrary.recompile_material(target)
    unreal.EditorAssetLibrary.save_loaded_asset(target)
    instances = _ensure_instances(target)

    calls = _function_calls(target)
    report = {
        "ok": all(key in calls for key in ("dream", "rim", "sparkle", "iridescence")),
        "source": SOURCE,
        "target": TARGET,
        "created_this_run": created,
        "function_calls": _function_call_paths(target),
        "anchors": anchors,
        "instances": instances,
        "source_untouched": True,
        "v9_untouched": True,
        "v10_untouched": True,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }
    REPORT.parent.mkdir(parents=True, exist_ok=True)
    REPORT.write_text(json.dumps(report, indent=2), encoding="utf-8")
    unreal.log(f"[NikkiIntegratedV1] {json.dumps(report)}")
    print(json.dumps(report, indent=2))
    return report


if __name__ == "__main__":
    main()
