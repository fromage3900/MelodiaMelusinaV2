"""Create the canonical meadow landscape instance without rebuilding the family."""
from __future__ import annotations

import json
from pathlib import Path

ASSET = "/Game/EnvSandbox/Materials/Instances/Landscape/MI_Landscape_Meadow"
PARENT = "/Game/EnvSandbox/Materials/Masters/M_Master_Toon_Landscape_HeightBlend"
REPORT = Path(__file__).resolve().parents[2] / "Saved" / "Audit" / "landscape_meadow_instance.json"


def _set_vector(instance, name: str, value: tuple[float, float, float, float]) -> None:
    import unreal

    unreal.MaterialEditingLibrary.set_material_instance_vector_parameter_value(
        instance, name, unreal.LinearColor(*value)
    )


def _set_scalar(instance, name: str, value: float) -> None:
    import unreal

    unreal.MaterialEditingLibrary.set_material_instance_scalar_parameter_value(
        instance, name, value
    )


def main() -> dict:
    import unreal

    created = unreal.EditorAssetLibrary.does_asset_exist(ASSET)
    if created:
        instance = unreal.load_asset(ASSET)
        if not instance:
            raise RuntimeError(f"Could not load {ASSET}")
        parent = unreal.load_asset(PARENT)
        instance.set_editor_property("parent", parent)
    else:
        tools = unreal.AssetToolsHelpers.get_asset_tools()
        factory = unreal.MaterialInstanceConstantFactoryNew()
        instance = tools.create_asset("MI_Landscape_Meadow", "/Game/EnvSandbox/Materials/Instances/Landscape", unreal.MaterialInstanceConstant, factory)
        if not instance:
            raise RuntimeError(f"Could not create {ASSET}")
        parent = unreal.load_asset(PARENT)
        if not parent:
            raise RuntimeError(f"Could not load {PARENT}")
        instance.set_editor_property("parent", parent)
    for name, value in {
            "RockTint": (0.50, 0.46, 0.40, 1.0),
            "GrassTint": (0.38, 0.58, 0.24, 1.0),
            "MudTint": (0.34, 0.26, 0.18, 1.0),
    }.items():
        _set_vector(instance, name, value)
    for name, value in {
            "SlopeSharpness": 2.2,
            "HeightBlendStrength": 1.8,
            "GrassAmount": 0.85,
            "MudAmount": 0.15,
            "MacroStrength": 0.35,
            "TriplanarTiling": 220.0,
    }.items():
        _set_scalar(instance, name, value)
    unreal.MaterialEditingLibrary.update_material_instance(instance)
    saved = unreal.EditorAssetLibrary.save_loaded_asset(instance)
    result = {"asset": ASSET, "created": not created, "exists": True, "saved": bool(saved), "ok": bool(saved)}
    REPORT.parent.mkdir(parents=True, exist_ok=True)
    REPORT.write_text(json.dumps(result, indent=2), encoding="utf-8")
    unreal.log("Landscape meadow instance: " + json.dumps(result, sort_keys=True))
    return result


if __name__ == "__main__":
    main()
