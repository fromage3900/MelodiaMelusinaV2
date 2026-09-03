"""Convert the four Gaea world recipes into isolated Substrate terrain MIs.

The source graphs are Gaea references plus the recorded ASTER metric terrain;
this pass converts their terrain/material intent into the existing Melodia
Substrate landscape master. It deliberately targets Mesh Terrain rather than
classic Landscape: the MIs use the master's world-aligned triplanar lane,
procedural height/slope blending, shore response, and Nikki-grade polish.

Targets only /Game/_PROJECT/ResonantWorld/Offline/GaeaSetups/MI_Gaea_*.
It never edits the master material or production landscape instances.
"""

from __future__ import annotations

import json
from pathlib import Path

import unreal


PROJECT_ROOT = Path(r"C:\EnvironmentPortfolio\BS_GodFile")
OUT_PATH = PROJECT_ROOT / "Saved/Audit/gaea_substrate_material_apply.json"
PARENT_PATH = "/Game/EnvSandbox/Materials/Masters/M_Master_Toon_Landscape_HeightBlend"

COMMON_SCALARS = {
    "LandscapeUVScale": 1.0,
    "NormalStrength": 1.0,
    "bUseLandscapeUV": False,
    "bUsePaintedLayers": False,
    "bTriplanarPro_Active": True,
    "TriplanarPro_Sharpness": 4.0,
    "TriplanarPro_BlendStrength": 1.0,
    "TriplanarPro_BreakupStrength": 0.16,
    "TriplanarPro_BreakupScale": 1.0,
    "TriplanarPro_BreakupContrast": 1.2,
}

PRESETS = {
    "sakura_terrace": {
        "mi": "/Game/_PROJECT/ResonantWorld/Offline/GaeaSetups/SakuraTerrace/MI_Gaea_SakuraTerrace_Substrate",
        "graph": "Directional Erosion.terrain",
        "recipe": "Ridge -> Directional Erosion -> ColorErosion -> FlowMap -> Weathering -> SatMap",
        "scalars": {
            "TriplanarTiling": 300.0,
            "SlopeSharpness": 3.2,
            "HeightBlendStrength": 2.4,
            "GrassAmount": 0.78,
            "MudAmount": 0.22,
            "MacroStrength": 0.34,
            "Wetness": 0.10,
            "WetRoughness": 0.38,
            "ShoreWetnessBoost": 0.46,
            "ShoreColorDarken": 0.16,
            "WaterPaletteAlign": 0.28,
            "PathWearStrength": 0.62,
            "PastelLift": 0.24,
            "DreamSaturation": 0.22,
            "DreamContrast": 0.04,
            "DreamShadowLift": 0.10,
            "ShadowFlowerStrength": 0.55,
            "ShadowFlowerScale": 7.0,
            "SparkleIntensity": 0.16,
            "RimIntensity": 0.08,
        },
        "vectors": {
            "RockTint": (0.46, 0.36, 0.30, 1.0),
            "GrassTint": (0.34, 0.54, 0.28, 1.0),
            "MudTint": (0.25, 0.20, 0.14, 1.0),
            "PathTint": (0.70, 0.55, 0.43, 1.0),
            "WaterAlignTint": (0.52, 0.75, 0.78, 1.0),
            "DreamTint": (1.0, 0.84, 0.91, 1.0),
            "ShadowFlowerColor": (0.92, 0.55, 0.72, 1.0),
        },
    },
    "liquid_cathedral": {
        "mi": "/Game/_PROJECT/ResonantWorld/Offline/GaeaSetups/LiquidCathedral/MI_Gaea_LiquidCathedral_Substrate",
        "graph": "Canyon River with Sea.terrain",
        "recipe": "Canyon -> Hydraulic Erosion -> HydroFix -> Sea -> SatMap -> WaveShine",
        "scalars": {
            "TriplanarTiling": 260.0,
            "SlopeSharpness": 3.8,
            "HeightBlendStrength": 2.8,
            "GrassAmount": 0.30,
            "MudAmount": 0.46,
            "MacroStrength": 0.52,
            "Wetness": 0.72,
            "WetRoughness": 0.24,
            "ShoreWetnessBoost": 0.88,
            "ShoreColorDarken": 0.30,
            "WaterPaletteAlign": 0.86,
            "PathWearStrength": 0.20,
            "PastelLift": 0.06,
            "DreamSaturation": 0.12,
            "DreamContrast": 0.10,
            "RimIntensity": 0.18,
            "SparkleIntensity": 0.28,
            "Iridescence": 0.12,
            "IridescencePower": 2.2,
        },
        "vectors": {
            "RockTint": (0.20, 0.30, 0.34, 1.0),
            "GrassTint": (0.20, 0.38, 0.30, 1.0),
            "MudTint": (0.10, 0.16, 0.17, 1.0),
            "PathTint": (0.42, 0.58, 0.62, 1.0),
            "WaterAlignTint": (0.10, 0.40, 0.50, 1.0),
            "DreamTint": (0.72, 0.86, 0.94, 1.0),
            "SparkleColor": (0.70, 0.92, 1.0, 1.0),
        },
    },
    "cadence_crystal_ridge": {
        "mi": "/Game/_PROJECT/ResonantWorld/Offline/GaeaSetups/CadenceCrystalRidge/MI_Gaea_CadenceCrystalRidge_Substrate",
        "graph": "Creative - Stylized Mountain.terrain",
        "recipe": "Radial Gradient -> restrained Erosion -> crystal dressing",
        "scalars": {
            "TriplanarTiling": 220.0,
            "SlopeSharpness": 4.2,
            "HeightBlendStrength": 2.2,
            "GrassAmount": 0.30,
            "MudAmount": 0.16,
            "MacroStrength": 0.28,
            "Wetness": 0.05,
            "WetRoughness": 0.34,
            "PastelLift": 0.10,
            "DreamSaturation": 0.14,
            "DreamContrast": 0.10,
            "DreamShadowLift": 0.08,
            "RimIntensity": 0.34,
            "GlowIntensity": 0.22,
            "BloomBoost": 0.18,
            "SparkleIntensity": 0.74,
            "SparkleThreshold": 0.40,
            "Iridescence": 0.68,
            "IridescencePower": 3.2,
        },
        "vectors": {
            "RockTint": (0.25, 0.28, 0.36, 1.0),
            "GrassTint": (0.20, 0.36, 0.34, 1.0),
            "MudTint": (0.14, 0.13, 0.18, 1.0),
            "PathTint": (0.45, 0.55, 0.68, 1.0),
            "WaterAlignTint": (0.35, 0.62, 0.76, 1.0),
            "DreamTint": (0.78, 0.76, 1.0, 1.0),
            "SparkleColor": (0.76, 0.92, 1.0, 1.0),
            "IridescenceTint": (0.62, 0.52, 1.0, 1.0),
            "RimColor": (0.60, 0.84, 1.0, 1.0),
        },
    },
    "fugue_grotto": {
        "mi": "/Game/_PROJECT/ResonantWorld/Offline/GaeaSetups/FugueGrotto/MI_Gaea_FugueGrotto_Substrate",
        "graph": "Collapsed Gullies.terrain",
        "recipe": "Cellular Gullies -> MountainSide -> Min Combine -> Erosion -> Erosion",
        "scalars": {
            "TriplanarTiling": 240.0,
            "SlopeSharpness": 4.6,
            "HeightBlendStrength": 2.8,
            "GrassAmount": 0.42,
            "MudAmount": 0.50,
            "MacroStrength": 0.56,
            "Wetness": 0.12,
            "WetRoughness": 0.40,
            "PathWearStrength": 0.72,
            "PastelLift": 0.02,
            "DreamSaturation": 0.08,
            "DreamContrast": 0.16,
            "DreamShadowLift": 0.02,
            "ShadowDreamStrength": 0.18,
            "ShadowContactBoost": 0.30,
            "IttoBlendAmount": 0.35,
            "IttoPatternScale": 4.0,
            "IttoCrackDepth": 0.28,
            "IttoWearAmount": 0.60,
            "IttoBreakupAmount": 0.35,
            "IttoErosionStrength": 0.45,
            "IttoWearDepth": 0.45,
            "IttoInkStrength": 0.25,
            "SparkleIntensity": 0.08,
            "RimIntensity": 0.12,
        },
        "vectors": {
            "RockTint": (0.22, 0.19, 0.17, 1.0),
            "GrassTint": (0.26, 0.32, 0.22, 1.0),
            "MudTint": (0.12, 0.10, 0.09, 1.0),
            "PathTint": (0.52, 0.42, 0.32, 1.0),
            "WaterAlignTint": (0.24, 0.40, 0.46, 1.0),
            "DreamTint": (0.54, 0.46, 0.68, 1.0),
            "IttoRampLow": (0.08, 0.06, 0.05, 1.0),
            "IttoRampHigh": (0.32, 0.25, 0.20, 1.0),
            "ShadowDreamTint": (0.38, 0.30, 0.52, 1.0),
        },
    },
}

MEL = unreal.MaterialEditingLibrary


def _parent_path(mi) -> str:
    parent = mi.get_editor_property("parent")
    return parent.get_path_name().split(".", 1)[0] if parent else ""


def _linear_color(value):
    return unreal.LinearColor(*value)


def _apply(mi, preset):
    parent = mi.get_editor_property("parent")
    scalar_names = {str(v) for v in (MEL.get_scalar_parameter_names(parent) or [])}
    vector_names = {str(v) for v in (MEL.get_vector_parameter_names(parent) or [])}
    switch_names = {str(v) for v in (MEL.get_static_switch_parameter_names(parent) or [])}
    applied = []
    missing = []

    for name, value in {**COMMON_SCALARS, **preset["scalars"]}.items():
        if name in switch_names:
            MEL.set_material_instance_static_switch_parameter_value(mi, name, bool(value))
            applied.append({"name": name, "type": "switch", "value": bool(value)})
        elif name in scalar_names:
            MEL.set_material_instance_scalar_parameter_value(mi, name, float(value))
            applied.append({"name": name, "type": "scalar", "value": float(value)})
        else:
            missing.append(name)

    for name, value in preset["vectors"].items():
        if name in vector_names:
            MEL.set_material_instance_vector_parameter_value(mi, name, _linear_color(value))
            applied.append({"name": name, "type": "vector", "value": list(value)})
        else:
            missing.append(name)

    MEL.update_material_instance(mi)
    path = mi.get_path_name().split(".", 1)[0]
    unreal.EditorAssetLibrary.save_asset(path, only_if_is_dirty=True)
    return applied, missing, scalar_names, vector_names, switch_names


def _verify(mi, applied):
    checks = []
    for item in applied:
        name = item["name"]
        try:
            if item["type"] == "scalar":
                actual = float(MEL.get_material_instance_scalar_parameter_value(mi, name))
                ok = abs(actual - float(item["value"])) < 1.0e-4
            elif item["type"] == "vector":
                actual = MEL.get_material_instance_vector_parameter_value(mi, name)
                expected = item["value"]
                got = [float(actual.r), float(actual.g), float(actual.b), float(actual.a)]
                ok = all(abs(a - b) < 1.0e-4 for a, b in zip(got, expected))
            else:
                actual = bool(MEL.get_material_instance_static_switch_parameter_value(mi, name))
                ok = actual == bool(item["value"])
            checks.append({"name": name, "ok": ok})
        except Exception as exc:
            checks.append({"name": name, "ok": False, "error": str(exc)})
    return checks


def main():
    results = []
    for setup_id, preset in PRESETS.items():
        path = preset["mi"]
        mi = unreal.load_asset(path)
        if mi is None:
            results.append({"setup_id": setup_id, "status": "MISSING", "path": path})
            continue
        parent = _parent_path(mi)
        if parent != PARENT_PATH:
            results.append({"setup_id": setup_id, "status": "WRONG_PARENT", "path": path, "parent": parent})
            continue
        applied, missing, scalar_names, vector_names, switch_names = _apply(mi, preset)
        reloaded = unreal.load_asset(path)
        checks = _verify(reloaded, applied)
        results.append(
            {
                "setup_id": setup_id,
                "status": "OK" if all(c["ok"] for c in checks) else "VERIFY_FAILED",
                "path": path,
                "parent": parent,
                "graph": preset["graph"],
                "recipe": preset["recipe"],
                "substrate_toon_bsdf_parent": True,
                "mesh_terrain_uv_mode": "world_aligned_triplanar",
                "applied": applied,
                "missing_parameters": sorted(set(missing)),
                "verification": checks,
                "parent_parameter_counts": {
                    "scalar": len(scalar_names),
                    "vector": len(vector_names),
                    "static_switch": len(switch_names),
                },
            }
        )

    payload = {
        "schema": "melodia.gaea_substrate_material_apply.v1",
        "parent_material": PARENT_PATH,
        "scope": "/Game/_PROJECT/ResonantWorld/Offline/GaeaSetups",
        "classic_landscape_used": False,
        "native_gaea_albedo_export": False,
        "note": "Gaea recipe intent is converted into the existing Substrate Toon landscape master; native SatMap/albedo export remains a separate gate.",
        "setups": results,
    }
    OUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    OUT_PATH.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    unreal.log("[GAEA_SUBSTRATE] report: " + str(OUT_PATH))
    return payload


if __name__ == "__main__":
    main()
