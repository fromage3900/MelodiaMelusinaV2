from __future__ import annotations
import json
from datetime import datetime, timezone
from pathlib import Path
import unreal

PROJECT_ROOT = Path(__file__).resolve().parents[2]
REPORT_DIR = PROJECT_ROOT / "Saved" / "Audit"

MATERIALS_ROOT = "/Game/EnvSandbox/Materials"
SDF_INST_DIR = f"{MATERIALS_ROOT}/SDF/Instances"
PARENT = f"{MATERIALS_ROOT}/Masters/M_Toon_SDF.M_Toon_SDF"

STYLIZED = [
    {
        "name": "MI_SDF_CelestialVinyl",
        "tint": (0.82, 0.71, 0.35, 1.0),
        "accent": (0.12, 0.08, 0.22, 1.0),
        "band_scale": 0.045,
        "band_strength": 0.3,
        "style": "celestial gold + dark vinyl bands",
        "tags": ["magical", "baroque", "henshin"]
    },
    {
        "name": "MI_SDF_TealCeramic",
        "tint": (0.25, 0.48, 0.52, 1.0),
        "accent": (0.85, 0.88, 0.92, 1.0),
        "band_scale": 0.06,
        "band_strength": 0.18,
        "style": "teal ceramic + white band relief",
        "tags": ["architectural", "clean", "modern"]
    },
    {
        "name": "MI_SDF_RosyQuartz",
        "tint": (0.95, 0.72, 0.78, 1.0),
        "accent": (0.82, 0.48, 0.55, 1.0),
        "band_scale": 0.04,
        "band_strength": 0.15,
        "style": "rosy pink quartz + cherry blossom shimmer",
        "tags": ["sakura", "warm", "translucent"]
    },
    {
        "name": "MI_SDF_MossyCopper",
        "tint": (0.42, 0.55, 0.38, 1.0),
        "accent": (0.72, 0.45, 0.22, 1.0),
        "band_scale": 0.055,
        "band_strength": 0.28,
        "style": "aged copper + moss patina",
        "tags": ["nature", "aged", "ornament"]
    },
    {
        "name": "MI_SDF_VoidStarlight",
        "tint": (0.06, 0.04, 0.12, 1.0),
        "accent": (0.18, 0.22, 0.95, 1.0),
        "band_scale": 0.08,
        "band_strength": 0.42,
        "style": "void black + starlight blue",
        "tags": ["celestial", "cosmic", "deep"]
    },
    {
        "name": "MI_SDF_IvoryScrollwork",
        "tint": (0.92, 0.88, 0.78, 1.0),
        "accent": (0.75, 0.62, 0.32, 1.0),
        "band_scale": 0.035,
        "band_strength": 0.25,
        "style": "ivory parchment + gold filigree",
        "tags": ["manuscript", "warm", "ornate"]
    }
]

def _ensure_directory(path: str) -> None:
    if not unreal.EditorAssetLibrary.does_directory_exist(path):
        unreal.EditorAssetLibrary.make_directory(path)

def build_stylized_instances() -> list[dict]:
    results = []
    parent = unreal.load_asset(PARENT)
    asset_tools = unreal.AssetToolsHelpers.get_asset_tools()
    factory = unreal.MaterialInstanceConstantFactoryNew()
    for spec in STYLIZED:
        path = f"{SDF_INST_DIR}/{spec['name']}"
        full = f"{path}.{spec['name']}"
        if unreal.EditorAssetLibrary.does_asset_exist(full):
            continue
        inst = asset_tools.create_asset(spec['name'], SDF_INST_DIR, unreal.MaterialInstanceConstant, factory)
        unreal.MaterialEditingLibrary.set_material_instance_parent(inst, parent)
        unreal.MaterialEditingLibrary.set_material_instance_vector_parameter_value(
            inst, "BaseTint", unreal.LinearColor(*spec['tint']))
        unreal.MaterialEditingLibrary.set_material_instance_vector_parameter_value(
            inst, "AccentTint", unreal.LinearColor(*spec['accent']))
        unreal.MaterialEditingLibrary.set_material_instance_scalar_parameter_value(
            inst, "SDF_BandScale", spec['band_scale'])
        unreal.MaterialEditingLibrary.set_material_instance_scalar_parameter_value(
            inst, "SDF_BandStrength", spec['band_strength'])
        unreal.EditorAssetLibrary.save_loaded_asset(inst, only_if_is_dirty=False)
        results.append(spec)
    return results

def build_all() -> int:
    results = build_stylized_instances()
    unreal.EditorLoadingAndSavingUtils.save_dirty_packages(True, True)
    return 0

if __name__ == '__main__':
    raise SystemExit(build_all())