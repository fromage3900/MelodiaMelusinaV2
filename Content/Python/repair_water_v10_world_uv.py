"""Add a V10-only blended world-UV domain for all layered water PBR samples.

V9 is intentionally untouched.  The V10 custom UV/POM node remains the
authoritative path, but its layer UVs can now blend from mesh UVs to absolute
world-space UVs.  That removes per-primitive tiling seams on authored and
non-World-Partition levels while retaining a rollback-safe mesh-UV fallback.
"""
from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

import unreal
import material_lib as lib


MASTER = "/Game/EnvSandbox/Materials/Masters/M_Water_Master_Grand_v10_Upgrade"
GROUP = "Water v10 | Native Additive"
REPORT = Path(unreal.Paths.project_saved_dir()) / "Audit" / "water_v10_world_uv.json"


def _expressions(material):
    return list(unreal.MaterialEditingLibrary.get_material_expressions(material) or [])


def _find(material, name):
    return next((e for e in _expressions(material) if e and e.get_name() == name), None)


def _find_param(material, name):
    for expr in _expressions(material):
        if not expr or "Parameter" not in expr.get_class().get_name():
            continue
        try:
            if str(expr.get_editor_property("parameter_name")) == name:
                return expr
        except Exception:
            continue
    return None


def _connect(source, output, target, pin):
    if not unreal.MaterialEditingLibrary.connect_material_expressions(
        source, output, target, pin
    ):
        raise RuntimeError(f"Failed to connect {source.get_name()} -> {target.get_name()}:{pin}")


def _ensure_input(custom, name):
    inputs = list(custom.get_editor_property("inputs") or [])
    for item in inputs:
        try:
            if str(item.get_editor_property("input_name")) == name:
                return False
        except Exception:
            pass
    item = unreal.CustomInput()
    item.set_editor_property("input_name", name)
    inputs.append(item)
    custom.set_editor_property("inputs", inputs)
    return True


def main():
    material = unreal.EditorAssetLibrary.load_asset(MASTER)
    if not material:
        raise RuntimeError(f"Missing material: {MASTER}")
    custom = _find(material, "MaterialExpressionCustom_0")
    if not custom:
        raise RuntimeError("Missing V10 custom POM/UV node")

    world_scale = _find_param(material, "WaterV10WorldTextureScale")
    if not world_scale:
        world_scale = lib.scalar_param(
            material,
            "WaterV10WorldTextureScale",
            GROUP,
            0.0008,
            -2350,
            -720,
            desc="Absolute-world UV scale for V10 layered water PBR maps.",
        )
    world_blend = _find_param(material, "WaterV10WorldUVBlend")
    if not world_blend:
        world_blend = lib.scalar_param(
            material,
            "WaterV10WorldUVBlend",
            GROUP,
            0.78,
            -2200,
            -720,
            desc="Blend from mesh UVs to world UVs; 0 keeps authored UV behavior.",
        )

    added_scale = _ensure_input(custom, "WorldTextureScale")
    added_blend = _ensure_input(custom, "WorldUVBlend")
    code = str(custom.get_editor_property("code"))
    marker = "float2 macroP = WorldPosition.xy * max(MacroScale, 0.000001);"
    replacement = (
        "float2 worldUV = WorldPosition.xy * max(WorldTextureScale, 0.000001);\n"
        "float2 uvBase = lerp(UV, worldUV, saturate(WorldUVBlend));\n"
        "float2 macroP = WorldPosition.xy * max(MacroScale, 0.000001);"
    )
    if marker in code and "float2 uvBase =" not in code:
        code = code.replace(marker, replacement, 1)
    code = code.replace("float2 buv0 = UV * BaseTiling + baseFlow + textureWarp;", "float2 buv0 = uvBase * BaseTiling + baseFlow + textureWarp;")
    code = code.replace("float2 muv0 = UV * MidTiling + midFlow + textureWarp * 0.73;", "float2 muv0 = uvBase * MidTiling + midFlow + textureWarp * 0.73;")
    code = code.replace("Layer2UV = UV * Layer2Tiling +", "Layer2UV = uvBase * Layer2Tiling +")
    code = code.replace("HighlightUV = UV * HighlightTiling +", "HighlightUV = uvBase * HighlightTiling +")
    custom.set_editor_property("code", code)
    _connect(world_scale, "", custom, "WorldTextureScale")
    _connect(world_blend, "", custom, "WorldUVBlend")

    unreal.MaterialEditingLibrary.recompile_material(material)
    unreal.EditorAssetLibrary.save_loaded_asset(material, only_if_is_dirty=False)
    report = {
        "ok": True,
        "master": MASTER,
        "v9_touched": False,
        "world_uv_inputs_added": ["WorldTextureScale", "WorldUVBlend"],
        "parameters": {
            "WaterV10WorldTextureScale": 0.0008,
            "WaterV10WorldUVBlend": 0.78,
        },
        "mesh_uv_rollback": "WaterV10WorldUVBlend=0",
        "pbr_texture_sample_uv_path": "MaterialExpressionCustom_0 blended absolute-world UV",
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }
    REPORT.parent.mkdir(parents=True, exist_ok=True)
    REPORT.write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(json.dumps(report, indent=2))
    return report


if __name__ == "__main__":
    main()
