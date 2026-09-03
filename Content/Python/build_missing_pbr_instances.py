# build_missing_pbr_instances.py
# Editor-only. Creates M_Master_Toon_Universal instances for every complete
# PBR texture set on disk that doesn't yet have one. Schema-compliant params,
# healthy MI_<Family>_<Profile> labeling, neutral-default fallback chains.
#
# Runs in-editor via:
#   py Content/Python/build_missing_pbr_instances.py
# Headless:
#   UnrealEditor-Cmd.exe BS_GodFile.uproject
#     -ExecutePythonScript="Content/Python/build_missing_pbr_instances.py"
#     -unattended -nullrhi

from __future__ import annotations

import json
import re
import sys
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path

import unreal

PROJECT_ROOT = Path("C:/EnvironmentPortfolio/BS_GodFile")
REPORT = PROJECT_ROOT / "Saved" / "Audit" / "missing_pbr_instances.json"

# Master to instantiate
MASTER_PATH = "/Game/EnvSandbox/Materials/Masters/M_Master_Toon_Universal"
INSTANCE_DIR = "/Game/EnvSandbox/Materials/Instances/AutoBuilt"

# Texture suffix -> (param_name, is_normal_map)
SUFFIX_MAP = {
    "_BaseColor": ("Albedo", False),
    "_albedo": ("Albedo", False),
    "_diffuse": ("Albedo", False),
    "_Normal": ("NormalMap", True),
    "_normal": ("NormalMap", True),
    "_Nrm": ("NormalMap", True),
    "_ORM": ("ORM", False),
    "_orm": ("ORM", False),
    "_Height": ("HeightMap", False),
    "_height": ("HeightMap", False),
    "_Displace": ("HeightMap", False),
    "_displace": ("HeightMap", False),
    "_Roughness": ("RoughnessMap", False),
    "_roughness": ("RoughnessMap", False),
    "_Metallic": ("MetallicMap", False),
    "_metallic": ("MetallicMap", False),
    "_AO": ("ORM", False),
    "_ao": ("ORM", False),
}

# Parameter group per role (from portfolio_texture_catalog.TEXTURE_ROLE_HINTS + master schema)
PARAM_GROUPS = {
    "Albedo": "LayerA",
    "NormalMap": "LayerA",
    "ORM": "LayerA",
    "HeightMap": "LayerA",
    "RoughnessMap": "LayerA",
    "MetallicMap": "LayerA",
}

# Fallback chain per role (from portfolio_texture_catalog.py — first existing wins)
NEUTRAL_NORMAL = "/Game/EnvSandbox/Textures/Utility/T_Neutral_Normal"
NEUTRAL_ORM = "/Game/EnvSandbox/Textures/Utility/T_Neutral_ORM"
NEUTRAL_HEIGHT = "/Game/EnvSandbox/Textures/Utility/T_Neutral_Height"
NEUTRAL_ROUGHNESS = "/Game/EnvSandbox/Textures/Utility/T_Neutral_Roughness"
NEUTRAL_METALLIC = "/Game/EnvSandbox/Textures/Utility/T_Neutral_Metallic"

FALLBACKS = {
    "Albedo": None,           # must come from texture set, no generic fallback
    "NormalMap": NEUTRAL_NORMAL,
    "ORM": NEUTRAL_ORM,
    "HeightMap": NEUTRAL_HEIGHT,
    "RoughnessMap": NEUTRAL_ROUGHNESS,
    "MetallicMap": NEUTRAL_METALLIC,
}


def _find_texture_sets() -> dict[str, dict[str, str]]:
    """Walk Content/Textures and Content/_PROJECT, group by stem, return
    {stem: {param_name: /Game/absolute/path}}."""
    roots = [
        Path("C:/EnvironmentPortfolio/BS_GodFile/Content/Textures"),
        Path("C:/EnvironmentPortfolio/BS_GodFile/Content/_PROJECT/04_Materials/Textures"),
    ]
    # Also scan Characters/Melusina/Materials for any packed sets
    char = Path("C:/EnvironmentPortfolio/BS_GodFile/Content/Melodia/Characters/Melusina/Materials")
    if char.exists():
        roots.append(char)

    texture_files: list[Path] = []
    for root in roots:
        if not root.exists():
            continue
        for p in root.rglob("*.uasset"):
            texture_files.append(p)

    sets: dict[str, dict[str, str]] = defaultdict(dict)
    for p in texture_files:
        name = p.stem  # e.g. "HeartTilesBase_BaseColor"
        stem = None
        param_name = None
        for suffix, (pname, _is_nrm) in SUFFIX_MAP.items():
            if name.endswith(suffix):
                stem = name[: -len(suffix)]
                param_name = pname
                break
        if stem is None:
            continue
        # Build /Game path from absolute path (strip the Content/ prefix)
        try:
            rel = p.relative_to(PROJECT_ROOT / "Content")
            game_path = "/Game/" + str(rel).replace("\\", "/")
        except ValueError:
            continue
        sets[stem][param_name] = str(game_path)
    return dict(sets)


def _complete_sets(sets: dict[str, dict[str, str]]) -> dict[str, dict[str, str]]:
    """Only keep sets that have at least albedo + normal + (ORM or roughness+metallic)."""
    complete = {}
    for stem, maps in sets.items():
        if "Albedo" in maps and "NormalMap" in maps and (
            "ORM" in maps or ("RoughnessMap" in maps and "MetallicMap" in maps)
        ):
            complete[stem] = maps
    return complete


def _existing_instance_names() -> set[str]:
    """Query all existing MI names under Instances/ to avoid clobbering."""
    try:
        ar = unreal.AssetRegistryHelpers.get_asset_registry()
        f = unreal.ARFilter(
            class_names=["MaterialInstanceConstant"],
            recursive_classes=True,
            recursive_paths=True,
            package_paths=["/Game/EnvSandbox/Materials/Instances"],
        )
        out = set()
        for a in ar.get_assets(f):
            out.add(str(a.asset_name))
        # Also check the legacy _PROJECT folder
        f2 = unreal.ARFilter(
            class_names=["MaterialInstanceConstant"],
            recursive_classes=True,
            recursive_paths=True,
            package_paths=["/Game/_PROJECT/04_Materials"],
        )
        for a in ar.get_assets(f2):
            out.add(str(a.asset_name))
        return out
    except Exception:
        return set()


def _make_instance(stem: str, maps: dict[str, str], existing: set[str]) -> dict:
    """Create one MI for the texture set, using schema params + neutral fallbacks."""
    # Healthy label: MI_<Stem>  (PascalCase, no underscores where avoidable)
    safe = re.sub(r"[^A-Za-z0-9]", "_", stem).strip("_")
    name = f"MI_{safe}"
    if name in existing:
        return {"name": name, "status": "exists"}

    folder = INSTANCE_DIR
    try:
        unreal.EditorAssetLibrary.make_directory(folder)
    except Exception:
        pass

    inst = unreal.EditorAssetLibrary.create_asset(
        name, folder, unreal.MaterialInstanceConstant,
        unreal.MaterialInstanceConstantFactoryNew()
    )
    if not inst:
        return {"name": name, "status": "create_failed"}

    # Parent it
    parent = unreal.EditorAssetLibrary.load_asset(MASTER_PATH)
    if parent:
        inst.set_editor_property("parent", parent)

    # Wire textures: provided maps first, then neutral fallbacks for missing roles
    wired = {}
    for param, tex_path in maps.items():
        if unreal.EditorAssetLibrary.does_asset_exist(tex_path):
            try:
                unreal.MaterialEditingLibrary.set_material_instance_texture_parameter_value(
                    inst, param, unreal.load_asset(tex_path)
                )
                wired[param] = tex_path
            except Exception as exc:
                print(f"[PBR] wire fail {name}.{param}: {exc}")

    # Fill missing roles from neutral fallbacks
    for param, fallback_path in FALLBACKS.items():
        if param in wired or not fallback_path:
            continue
        if not unreal.EditorAssetLibrary.does_asset_exist(fallback_path):
            continue
        try:
            unreal.MaterialEditingLibrary.set_material_instance_texture_parameter_value(
                inst, param, unreal.load_asset(fallback_path)
            )
            wired[param] = fallback_path
        except Exception:
            pass

    # Schema-compliant scalar defaults (from starter_instances + master design)
    scalars = {
        "TextureWeight": 1.0,
        "UVScale": 1.0,
        "Roughness": 0.70,
        "Metallic": 0.0,
        "NormalStrength": 1.0,
        "NormalPower": 1.0,
        "TriplanarBlend": 0.0,          # UV projection default
        "TriplanarTiling": 256.0,
        "LayerA_TextureWeight": 1.0,
        "LayerA_ParallaxScale": 1.0,
        "LayerA_NormalStrength": 1.0,
    }
    for pname, val in scalars.items():
        try:
            unreal.MaterialEditingLibrary.set_material_instance_scalar_parameter_value(inst, pname, val)
        except Exception:
            pass

    # Neutral all Nikki/stylization drivers to 0 (master default)
    neutral_params = [
        "PastelLift", "DreamSaturation", "DreamContrast", "DreamShadowLift",
        "RimIntensity", "GlowIntensity", "SparkleIntensity", "Iridescence",
        "FabricSheen", "BloomBoost", "TemporalStrength",
    ]
    for pname in neutral_params:
        try:
            unreal.MaterialEditingLibrary.set_material_instance_scalar_parameter_value(inst, pname, 0.0)
        except Exception:
            pass

    # Save
    try:
        package = unreal.EditorAssetLibrary.get_package_for_object(inst)
        if package:
            unreal.EditorAssetLibrary.save_package(package, True)
    except Exception:
        try:
            unreal.EditorAssetLibrary.save_loaded_asset(inst, True)
        except Exception:
            pass

    return {"name": name, "folder": folder, "status": "created", "textures": wired}


def main() -> int:
    import material_lib as lib  # noqa: F411 — ensures lib loaded if needed
    print("[PBR] === scan PBR texture sets ===")
    all_sets = _find_texture_sets()
    complete = _complete_sets(all_sets)
    print(f"[PBR] total texture stems: {len(all_sets)}, complete PBR sets: {len(complete)}")

    existing = _existing_instance_names()
    print(f"[PBR] existing instances on disk: {len(existing)}")

    # Prioritize: P0 core levels first.  Heuristic: names likely used in
    # ZenForestTest, L_MelusinaMorning, L_KaleidoNave, L_FallenMoon.
    p0_keywords = ["Forest", "Wood", "Tree", "Grass", "Ground", "Soil", "Dirt",
                   "Path", "Stone", "Cliff", "Rock", "Mud", "Leaf", "Bark",
                   "Zen", "Garden", "Flower", "Brick", "Roof", "Tile"]
    prioritized = sorted(
        complete.items(),
        key=lambda kv: (0 if any(kw.lower() in kv[0].lower() for kw in p0_keywords) else 1, kv[0])
    )

    results = []
    for stem, maps in prioritized:
        r = _make_instance(stem, maps, existing)
        r["stem"] = stem
        r["maps"] = maps
        results.append(r)
        print(f"[PBR] {r['status']:12s} {r['name']}")

    report = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "master": MASTER_PATH,
        "instance_dir": INSTANCE_DIR,
        "complete_sets_found": len(complete),
        "results": results,
    }
    REPORT.parent.mkdir(parents=True, exist_ok=True)
    REPORT.write_text(json.dumps(report, indent=2, default=str), encoding="utf-8")
    print(f"[PBR] === report -> {REPORT} ===")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
