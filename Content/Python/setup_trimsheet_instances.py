"""ZenTrim + ClothTrim trimsheet material instances on M_Master_Toon_Universal.

Each MI assigns Layer A (Base4K) + Layer B (variation) 4K maps with height-aware LERP
(LayerBlendMode 1/2 via trim_layer_presets).

Run (editor or headless):
  py Content/Python/setup_trimsheet_instances.py

Headless:
  python Content/Python/setup_trimsheet_instances.py
"""
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
UE_CMD = Path(r"C:\Program Files\Epic Games\UE_5.8\Engine\Binaries\Win64\UnrealEditor-Cmd.exe")
UPROJECT = PROJECT_ROOT / "BS_GodFile.uproject"

MASTER = "/Game/EnvSandbox/Materials/Masters/M_Master_Toon_Universal.M_Master_Toon_Universal"
REPORT = PROJECT_ROOT / "Saved" / "Audit" / "trimsheet_instances.json"
FOLDER = "/Game/EnvSandbox/Materials/Instances/Environment/Stylized"
CLOTH_FOLDER = "/Game/EnvSandbox/Materials/Instances/Character/Cloth"

# layer_a / layer_b → zen_trim_textures.ZEN_TRIM_VARIANTS
# Height-aware LERP applied via trim_layer_presets.zen_layer_preset(layer_b)
TRIMSHEET_INSTANCES: list[dict] = [
    {
        "name": "MI_Trimsheet_VariationCracks",
        "layer_a": "Base4K",
        "layer_b": "CrackedToHell",
        "profile": "TP_Stone",
        "vectors": {"BaseTint": (1.0, 1.0, 1.0, 1.0)},
        "scalars": {
            "TextureWeight": 1.0,
            "LayerBlend": 0.42,
            "LayerA_TextureWeight": 1.0,
            "LayerB_TextureWeight": 0.9,
            "ParallaxStrength": 0.62,
            "ParallaxScale": 0.055,
            "ParallaxSteps": 12.0,
            "ParallaxMode": 2.0,
            "ParallaxHeight": 0.9,
            "NormalStrength": 1.2,
            "LayerA_ParallaxScale": 1.0,
            "LayerB_ParallaxScale": 1.35,
            "MacroVariationStrength": 0.28,
            "MacroScale": 0.0012,
            "Roughness": 0.68,
            "Metallic": 0.04,
        },
    },
    {
        "name": "MI_Trimsheet_ParallaxPOM",
        "layer_a": "Base4K",
        "layer_b": "CrackedToHell",
        "profile": "TP_Stone",
        "lerp": "pom",
        "vectors": {"BaseTint": (1.0, 1.0, 1.0, 1.0)},
        "scalars": {
            "TextureWeight": 1.0,
            "LayerBlend": 0.35,
            "LayerA_TextureWeight": 1.0,
            "LayerB_TextureWeight": 0.85,
            "ParallaxStrength": 0.7,
            "ParallaxScale": 0.06,
            "ParallaxSteps": 16.0,
            "ParallaxMode": 2.0,
            "ParallaxHeight": 0.9,
            "NormalStrength": 1.35,
            "LayerA_ParallaxScale": 1.0,
            "LayerB_ParallaxScale": 1.5,
            "MacroVariationStrength": 0.2,
            "MacroScale": 0.001,
            "Roughness": 0.7,
        },
    },
    {
        "name": "MI_Universal_TrimsheetBlend",
        "layer_a": "Base4K",
        "layer_b": "ColourShift",
        "profile": "TP_Default",
        "vectors": {"BaseTint": (1.0, 1.0, 1.0, 1.0)},
        "scalars": {
            "TextureWeight": 1.0,
            "LayerBlend": 0.25,
            "LayerA_TextureWeight": 1.0,
            "LayerB_TextureWeight": 0.75,
            "ParallaxStrength": 0.45,
            "ParallaxScale": 0.04,
            "ParallaxSteps": 10.0,
            "ParallaxMode": 1.0,
            "NormalStrength": 1.1,
            "MacroVariationStrength": 0.15,
            "MacroScale": 0.0009,
            "Roughness": 0.72,
        },
    },
    {
        "name": "MI_Trimsheet_HeavyWear",
        "layer_a": "Base4K",
        "layer_b": "CrackedToHell",
        "profile": "TP_Stone",
        "heavy": True,
        "vectors": {"BaseTint": (0.95, 0.92, 0.88, 1.0)},
        "scalars": {
            "TextureWeight": 1.0,
            "LayerBlend": 0.68,
            "LayerB_TextureWeight": 1.0,
            "ParallaxStrength": 0.75,
            "ParallaxScale": 0.065,
            "ParallaxSteps": 14.0,
            "ParallaxMode": 2.0,
            "ParallaxHeight": 0.82,
            "NormalStrength": 1.25,
            "LayerB_ParallaxScale": 1.6,
            "MacroVariationStrength": 0.42,
            "MacroScale": 0.0015,
            "Roughness": 0.78,
        },
    },
    {
        "name": "MI_ZenTrim_Wet",
        "layer_a": "Base4K",
        "layer_b": "Wet",
        "profile": "TP_Stone",
        "vectors": {"BaseTint": (1.0, 1.0, 1.0, 1.0)},
        "scalars": {
            "TextureWeight": 1.0,
            "LayerBlend": 0.55,
            "LayerB_TextureWeight": 0.95,
            "ParallaxStrength": 0.5,
            "ParallaxScale": 0.045,
            "Roughness": 0.35,
            "Wetness": 0.65,
        },
    },
    {
        "name": "MI_ZenTrim_FlowersMid",
        "layer_a": "Base4K",
        "layer_b": "FlowersMid",
        "profile": "TP_Foliage",
        "vectors": {"BaseTint": (1.0, 1.0, 1.0, 1.0)},
        "scalars": {
            "TextureWeight": 1.0,
            "LayerBlend": 0.38,
            "LayerB_TextureWeight": 0.85,
            "ParallaxStrength": 0.4,
            "Roughness": 0.75,
        },
    },
    {
        "name": "MI_ZenTrim_FlowersLittle",
        "layer_a": "Base4K",
        "layer_b": "FlowersLIttleBit",
        "profile": "TP_Foliage",
        "vectors": {"BaseTint": (1.0, 1.0, 1.0, 1.0)},
        "scalars": {
            "TextureWeight": 1.0,
            "LayerBlend": 0.22,
            "LayerB_TextureWeight": 0.7,
            "ParallaxStrength": 0.35,
            "Roughness": 0.78,
        },
    },
    {
        "name": "MI_ZenTrim_FlowersLots",
        "layer_a": "Base4K",
        "layer_b": "FlowersLOTS",
        "profile": "TP_Foliage",
        "vectors": {"BaseTint": (1.0, 1.0, 1.0, 1.0)},
        "scalars": {
            "TextureWeight": 1.0,
            "LayerBlend": 0.52,
            "LayerB_TextureWeight": 0.92,
            "ParallaxStrength": 0.42,
            "Roughness": 0.72,
        },
    },
    {
        "name": "MI_ZenTrim_ColourShift",
        "layer_a": "Base4K",
        "layer_b": "ColourShift",
        "profile": "TP_Default",
        "vectors": {"BaseTint": (1.0, 1.0, 1.0, 1.0)},
        "scalars": {
            "TextureWeight": 1.0,
            "LayerBlend": 0.48,
            "LayerB_TextureWeight": 0.88,
            "ParallaxStrength": 0.38,
            "Roughness": 0.7,
        },
    },
]


def cloth_trim_instance_specs() -> list[dict]:
    """Auto-generate ClothTrim MIs from discovered /Game/Textures/ClothTrim_* assets."""
    import cloth_trim_textures as ct
    import trim_layer_presets as lp

    variants = ct.discover_variants()
    if not variants:
        return []

    layer_a = "Base4K" if "Base4K" in variants else variants[0]
    specs: list[dict] = []
    for variant in ct.overlay_variants():
        preset = lp.cloth_layer_preset(variant)
        specs.append({
            "name": f"MI_ClothTrim_{variant}",
            "folder": CLOTH_FOLDER,
            "trim_family": "cloth",
            "layer_a": layer_a,
            "layer_b": variant,
            "profile": "TP_Default",
            "vectors": {"BaseTint": (1.0, 1.0, 1.0, 1.0)},
            "scalars": lp.merge_scalars(
                {
                    "TextureWeight": 1.0,
                    "LayerBlend": 0.45,
                    "LayerA_TextureWeight": 1.0,
                    "LayerB_TextureWeight": 0.88,
                    "NormalStrength": 1.05,
                    "Roughness": 0.62,
                },
                preset,
            ),
        })
    return specs


def all_trimsheet_specs() -> list[dict]:
    zen = [{**s, "trim_family": "zen", "folder": FOLDER} for s in TRIMSHEET_INSTANCES]
    return zen + cloth_trim_instance_specs()


def _apply_lerp_preset(spec: dict) -> dict[str, float]:
    import trim_layer_presets as lp

    layer_b = spec.get("layer_b", "CrackedToHell")
    if spec.get("trim_family") == "cloth":
        preset = lp.cloth_layer_preset(layer_b)
    elif spec.get("lerp") == "pom":
        preset = dict(lp.LERP_HEIGHT_CRACK_POM)
    else:
        preset = lp.zen_layer_preset(layer_b, heavy=bool(spec.get("heavy")))
    return lp.merge_scalars(spec.get("scalars") or {}, preset)


def build() -> list[dict]:
    import cloth_trim_textures as ct
    import material_lib as lib
    import unreal
    import zen_trim_textures as zt

    if not unreal.EditorAssetLibrary.does_asset_exist(MASTER):
        raise RuntimeError(f"Missing master: {MASTER} — run setup_master_universal.py first")

    profiles = lib.create_toon_profiles(["TP_Default", "TP_Stone", "TP_Foliage"])
    results: list[dict] = []

    for spec in all_trimsheet_specs():
        folder = spec.get("folder", FOLDER)
        inst = lib.create_material_instance(spec["name"], folder, MASTER)
        profile = profiles.get(spec.get("profile", "TP_Default"))
        if profile:
            lib.set_instance_toon_profile(inst, profile)
        for pname, rgba in spec.get("vectors", {}).items():
            lib.set_instance_vector(inst, pname, rgba)

        scalars = _apply_lerp_preset(spec)
        for pname, value in scalars.items():
            lib.set_instance_scalar(inst, pname, value)

        layer_a = spec.get("layer_a", "Base4K")
        layer_b = spec.get("layer_b", "CrackedToHell")
        if spec.get("trim_family") == "cloth":
            wired = ct.apply_cloth_trim_layers(inst, layer_a, layer_b)
        else:
            wired = zt.apply_zen_trim_layers(inst, layer_a, layer_b)

        lib.save_package(inst)
        path = lib.asset_path(folder, spec["name"])
        results.append({
            "instance": spec["name"],
            "path": path,
            "trim_family": spec.get("trim_family", "zen"),
            "layer_a": layer_a,
            "layer_b": layer_b,
            "layer_blend_mode": scalars.get("LayerBlendMode"),
            "textures": wired,
            "status": "created_or_updated",
        })

    return results


def _in_ue() -> bool:
    try:
        import unreal  # noqa: F401
        return True
    except ImportError:
        return False


def main() -> int:
    if not _in_ue():
        if not UE_CMD.exists():
            print(f"ERROR: UE not found at {UE_CMD}")
            print("Run in-editor: py Content/Python/setup_trimsheet_instances.py")
            return 1
        log = PROJECT_ROOT / "Saved" / "Logs" / "trimsheet_instances.log"
        log.parent.mkdir(parents=True, exist_ok=True)
        cmd = [
            str(UE_CMD),
            str(UPROJECT),
            f"-ExecutePythonScript={(PROJECT_ROOT / 'Content/Python/setup_trimsheet_instances.py').as_posix()}",
            "-stdout",
            "-unattended",
            "-nosplash",
            "-nullrhi",
            "-DisablePlugins=Monolith",
            f"-log={log}",
        ]
        print(f"Trimsheet instances -> {log}")
        return subprocess.run(cmd, cwd=str(PROJECT_ROOT)).returncode

    results = build()
    cloth_count = sum(1 for r in results if r.get("trim_family") == "cloth")
    report = {
        "instances": results,
        "count": len(results),
        "zen_count": len(results) - cloth_count,
        "cloth_count": cloth_count,
        "folder": FOLDER,
        "cloth_folder": CLOTH_FOLDER,
        "texture_roots": ["/Game/Textures/ZenTrim_*", "/Game/Textures/ClothTrim_*"],
        "artist_guide": {
            "LayerA": "Base4K trimsheet → Albedo, NormalMap, ORM, HeightMap",
            "LayerB": "Variation overlay → LayerB_* (same channel mapping)",
            "LayerBlendMode": "1=height compete (cracks/flowers), 2=height+manual (wet/satin)",
            "LayerBlend": "Manual overlay strength; pairs with height compete for artist tuning",
            "instances_only": "Master graph unchanged — MI scalars + texture assignments",
            "zen_variants": list(__import__("zen_trim_textures").ZEN_TRIM_VARIANTS),
            "cloth_variants": list(__import__("cloth_trim_textures").discover_variants()),
        },
    }
    REPORT.parent.mkdir(parents=True, exist_ok=True)
    REPORT.write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(json.dumps(report, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
