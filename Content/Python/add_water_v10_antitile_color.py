"""Add a V10-only smooth anti-tiling color veil over the preserved V9 result.

The V9 texture maps remain connected and auditable. This layer only reduces
their repeated visual contrast through a continuous macro color field; V9 is
not edited.
"""
from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

import unreal
import material_lib as lib


MASTER = "/Game/EnvSandbox/Materials/Masters/M_Water_Master_Grand_v10_Upgrade"
GROUP = "Water v10 | Native Additive"
REPORT = Path(unreal.Paths.project_saved_dir()) / "Audit" / "water_v10_antitile_color.json"


def expressions(material):
    return list(unreal.MaterialEditingLibrary.get_material_expressions(material) or [])


def find(material, name: str):
    return next((e for e in expressions(material) if e and e.get_name() == name), None)


def find_param(material, name: str):
    for e in expressions(material):
        if not e or "Parameter" not in type(e).__name__ or "Function" in type(e).__name__:
            continue
        try:
            if str(e.get_editor_property("parameter_name")) == name:
                return e
        except Exception:
            pass
    return None


def connect(source, output: str, target, pin: str) -> None:
    if not lib.connect(source, output, target, pin):
        raise RuntimeError(f"Failed to connect {source.get_name()}:{output} -> {target.get_name()}:{pin}")


def description(e) -> str:
    for prop in ("description", "desc"):
        try:
            return str(e.get_editor_property(prop))
        except Exception:
            continue
    return ""


def get_or_create_custom(material):
    for e in expressions(material):
        if description(e) == "V10 Smooth AntiTile Color Veil":
            return e, False
    node = lib.create_expression(material, unreal.MaterialExpressionCustom, 420, -750)
    node.set_editor_property("description", "V10 Smooth AntiTile Color Veil")
    node.set_editor_property(
        "code",
        "float m = saturate(MacroField); "
        "float3 smoothColor = lerp(DeepColor, MidColor, smoothstep(0.0, 0.62, m)); "
        "smoothColor = lerp(smoothColor, CrestColor, smoothstep(0.62, 1.0, m)); "
        "return lerp(ExistingColor, smoothColor, saturate(AntiTileStrength));",
    )
    node.set_editor_property("output_type", unreal.CustomMaterialOutputType.CMOT_FLOAT3)
    custom_inputs = []
    for name in ("ExistingColor", "MacroField", "AntiTileStrength", "DeepColor", "MidColor", "CrestColor"):
        item = unreal.CustomInput()
        item.set_editor_property("input_name", name)
        custom_inputs.append(item)
    node.set_editor_property("inputs", custom_inputs)
    return node, True


def main() -> dict:
    material = unreal.EditorAssetLibrary.load_asset(MASTER)
    if not material:
        raise RuntimeError(f"Missing material: {MASTER}")

    v9_color = find(material, "MaterialExpressionCustom_2")
    macro = find(material, "MaterialExpressionCustom_0")
    bsdf = find(material, "MaterialExpressionSubstrateSingleLayerWaterBSDF_0")
    deep = find_param(material, "RampDeepColor")
    mid = find_param(material, "RampMidColor")
    crest = find_param(material, "RampCrestColor")
    strength = find_param(material, "WaterV10AntiTileStrength")
    if not all((v9_color, macro, bsdf, deep, mid, crest)):
        raise RuntimeError("Missing V9 color/macro/BSDF nodes")
    if not strength:
        strength = lib.scalar_param(
            material,
            "WaterV10AntiTileStrength",
            GROUP,
            0.55,
            11200,
            2200,
            desc="V10 smooth veil over V9 texture layers; preserves PBR map connections.",
        )

    node, created = get_or_create_custom(material)
    connect(v9_color, "", node, "ExistingColor")
    connect(macro, "MacroField", node, "MacroField")
    connect(strength, "", node, "AntiTileStrength")
    connect(deep, "", node, "DeepColor")
    connect(mid, "", node, "MidColor")
    connect(crest, "", node, "CrestColor")
    connect(node, "", bsdf, "BaseColor")

    unreal.MaterialEditingLibrary.recompile_material(material)
    unreal.EditorAssetLibrary.save_loaded_asset(material, only_if_is_dirty=False)
    report = {
        "ok": True,
        "master": MASTER,
        "created": created,
        "v9_color_result_preserved_as_existing_color": True,
        "pbr_texture_maps_disconnected": False,
        "anti_tile_parameter": "WaterV10AntiTileStrength",
        "default_strength": 0.55,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }
    REPORT.parent.mkdir(parents=True, exist_ok=True)
    REPORT.write_text(json.dumps(report, indent=2), encoding="utf-8")
    unreal.log("[WaterV10] Added smooth anti-tile color veil: " + json.dumps(report))
    print(json.dumps(report, indent=2))
    return report


if __name__ == "__main__":
    main()
