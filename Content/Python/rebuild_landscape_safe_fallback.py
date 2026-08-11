"""Rebuild the Zen Forest landscape master as a compile-safe painted material.

This is the recovery lane for a material graph that has invalid function pins.
It deliberately uses no project material functions, static switches, texture
object wiring, triplanar calls, or optional effects.  Those features can be
added back only after this base compiles on the target shader platform.

The existing Rock/Grass/Mud/Path layer names remain authoritative, so current
Landscape paint and LayerInfo assets continue to work.  Existing CC0 textures
are assigned directly to TextureSampleParameter2D defaults; authored PBR maps
will automatically win when they are imported at their documented paths.

Run with the Unreal Editor CLOSED:
  UnrealEditor-Cmd.exe BS_GodFile.uproject -ExecutePythonScript=.../rebuild_landscape_safe_fallback.py -nullrhi -unattended
"""
from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
MASTER_DIR = "/Game/EnvSandbox/Materials/Masters"
MASTER_NAME = "M_Master_Toon_Landscape_HeightBlend"
MASTER = f"{MASTER_DIR}/{MASTER_NAME}"
REPORT = PROJECT_ROOT / "Saved" / "Audit" / "landscape_safe_rebuild.json"
LAYERS = ("Rock", "Grass", "Mud", "Path")


def _object_path(path: str) -> str:
    package = path.split(".", 1)[0]
    return f"{package}.{package.rsplit('/', 1)[-1]}"


def _set_texture(sample, candidates: list[str]) -> str:
    import material_lib as lib

    resolved = lib.resolve_texture_path(candidates)
    if not resolved:
        raise RuntimeError(f"No texture found in fallback chain: {candidates}")
    texture = unreal.load_asset(_object_path(resolved))
    if not texture:
        raise RuntimeError(f"Could not load resolved texture: {resolved}")
    sample.set_editor_property("texture", texture)
    return resolved


def _layer_blend(material, x: int, y: int):
    blend = unreal.MaterialEditingLibrary.create_material_expression(
        material, unreal.MaterialExpressionLandscapeLayerBlend, x, y
    )
    inputs = []
    for name in LAYERS:
        entry = unreal.LayerBlendInput()
        entry.set_editor_property("layer_name", name)
        entry.set_editor_property(
            "blend_type", unreal.LandscapeLayerBlendType.LB_WEIGHT_BLEND
        )
        # Preview makes the master readable when opened without a Landscape;
        # runtime always receives the map's painted weights.
        entry.set_editor_property("preview_weight", 1.0 if name == "Rock" else 0.0)
        inputs.append(entry)
    blend.set_editor_property("layers", inputs)
    return blend


def _scalar(material, name: str, default: float, group: str, x: int, y: int):
    node = unreal.MaterialEditingLibrary.create_material_expression(
        material, unreal.MaterialExpressionScalarParameter, x, y
    )
    node.set_editor_property("parameter_name", name)
    node.set_editor_property("group", group)
    node.set_editor_property("default_value", default)
    node.set_editor_property("slider_min", 0.0)
    node.set_editor_property("slider_max", 1.0)
    return node


def _vector(material, name: str, default, group: str, x: int, y: int):
    node = unreal.MaterialEditingLibrary.create_material_expression(
        material, unreal.MaterialExpressionVectorParameter, x, y
    )
    node.set_editor_property("parameter_name", name)
    node.set_editor_property("group", group)
    node.set_editor_property("default_value", unreal.LinearColor(*default))
    return node


def _sample(material, name: str, group: str, candidates: list[str], x: int, y: int, *, normal=False):
    node = unreal.MaterialEditingLibrary.create_material_expression(
        material, unreal.MaterialExpressionTextureSampleParameter2D, x, y
    )
    node.set_editor_property("parameter_name", name)
    node.set_editor_property("group", group)
    if normal:
        node.set_editor_property("sampler_type", unreal.MaterialSamplerType.SAMPLERTYPE_NORMAL)
    chosen = _set_texture(node, candidates)
    return node, chosen


def build() -> dict:
    global unreal
    import unreal
    import material_lib as lib
    import portfolio_landscape_textures as textures

    asset_tools = unreal.AssetToolsHelpers.get_asset_tools()
    master_object = _object_path(MASTER)
    exists = unreal.EditorAssetLibrary.does_asset_exist(master_object)
    backup = ""
    if exists:
        stamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
        backup = f"{MASTER_DIR}/{MASTER_NAME}_PRE_SAFE_{stamp}"
        if not unreal.EditorAssetLibrary.duplicate_asset(MASTER, backup):
            raise RuntimeError(f"Unable to create recovery backup: {backup}")
        material = unreal.load_asset(master_object)
        lib.clear_material_graph(material)
    else:
        material = asset_tools.create_asset(
            MASTER_NAME, MASTER_DIR, unreal.Material, unreal.MaterialFactoryNew()
        )
    if not material:
        raise RuntimeError("Unable to create/load landscape master")

    # Set only properties needed for a normal opaque Landscape material.
    material.set_editor_property("material_domain", unreal.MaterialDomain.MD_SURFACE)
    material.set_editor_property("blend_mode", unreal.BlendMode.BLEND_OPAQUE)
    lib.try_set_editor_property(material, "bUsesSubstrate", True)
    lib.try_set_editor_property(material, "bUsedWithLandscape", True)

    color_blend = _layer_blend(material, 450, -250)
    normal_blend = _layer_blend(material, 450, 50)
    rough_blend = _layer_blend(material, 450, 350)
    textures_used: dict[str, dict[str, str]] = {}

    palette = {
        "Rock": (0.78, 0.76, 0.78, 1.0),
        "Grass": (0.78, 0.92, 0.72, 1.0),
        "Mud": (0.82, 0.72, 0.60, 1.0),
        "Path": (0.92, 0.84, 0.70, 1.0),
    }
    roughness = {"Rock": 0.82, "Grass": 0.86, "Mud": 0.92, "Path": 0.78}
    for index, layer in enumerate(LAYERS):
        y = -700 + index * 420
        candidates = textures.resolve_layer_textures(layer)
        albedo, albedo_path = _sample(
            material, f"{layer}_Albedo", "Textures", candidates["Albedo"], -1750, y
        )
        normal, normal_path = _sample(
            material, f"{layer}_Normal", "Textures", candidates["Normal"], -1750, y + 100, normal=True
        )
        tint = _vector(material, f"{layer}Tint", palette[layer], "Palette", -1450, y)
        tint_mul = unreal.MaterialEditingLibrary.create_material_expression(
            material, unreal.MaterialExpressionMultiply, -1150, y
        )
        unreal.MaterialEditingLibrary.connect_material_expressions(albedo, "RGB", tint_mul, "A")
        unreal.MaterialEditingLibrary.connect_material_expressions(tint, "", tint_mul, "B")
        layer_roughness = _scalar(material, f"{layer}Roughness", roughness[layer], "Surface", -1450, y + 180)
        unreal.MaterialEditingLibrary.connect_material_expressions(tint_mul, "", color_blend, f"Layer {layer}")
        unreal.MaterialEditingLibrary.connect_material_expressions(normal, "RGB", normal_blend, f"Layer {layer}")
        unreal.MaterialEditingLibrary.connect_material_expressions(layer_roughness, "", rough_blend, f"Layer {layer}")
        textures_used[layer] = {"Albedo": albedo_path, "Normal": normal_path}

    bsdf = unreal.MaterialEditingLibrary.create_material_expression(
        material, unreal.MaterialExpressionSubstrateToonBSDF, 850, 0
    )
    unreal.MaterialEditingLibrary.connect_material_expressions(color_blend, "", bsdf, "BaseColor")
    unreal.MaterialEditingLibrary.connect_material_expressions(normal_blend, "", bsdf, "Normal")
    unreal.MaterialEditingLibrary.connect_material_expressions(rough_blend, "", bsdf, "Roughness")
    unreal.MaterialEditingLibrary.connect_material_property(
        bsdf, "", unreal.MaterialProperty.MP_FRONT_MATERIAL
    )
    unreal.MaterialEditingLibrary.recompile_material(material)
    if not unreal.EditorAssetLibrary.save_asset(MASTER, only_if_is_dirty=False):
        raise RuntimeError(f"Unable to save {MASTER}")
    return {"master": MASTER, "backup": backup, "textures": textures_used, "layers": list(LAYERS)}


def main() -> int:
    result = build()
    REPORT.parent.mkdir(parents=True, exist_ok=True)
    REPORT.write_text(json.dumps(result, indent=2), encoding="utf-8")
    print(f"LANDSCAPE_SAFE_REBUILD_OK master={result['master']} backup={result['backup']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
