"""Ensure every portfolio master has at least one editable MaterialInstanceConstant.

Creates missing MI_* under SDF/Instances (or Impressionist/Instances) with
parent assignment, Toon Profile, and safe default scalar/vector overrides.

Run headless:
  UnrealEditor-Cmd.exe BS_GodFile.uproject ^
    -ExecutePythonScript="G:/EnvironmentPortfolio/BS_GodFile/Content/Python/ensure_portfolio_instances.py"
"""
from __future__ import annotations

import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path

import unreal

MATERIALS_ROOT = "/Game/EnvSandbox/Materials"
MASTER_DIR = f"{MATERIALS_ROOT}/Masters"
SDF_INST_DIR = f"{MATERIALS_ROOT}/SDF/Instances"
IMP_INST_DIR = f"{MATERIALS_ROOT}/Impressionist/Instances"
PROFILE_DIR = f"{MATERIALS_ROOT}/ToonProfiles"
REPORT_PATH = (
    Path(__file__).resolve().parents[2]
    / "Saved"
    / "Audit"
    / "ensure_portfolio_instances.json"
)

# One showcase instance per master that lacks a dedicated MI_* child.
MASTER_INSTANCES: list[dict] = [
    {
        "master": "M_SDF_Baroque",
        "instance": "MI_SDF_Baroque_Default",
        "profile": "TP_Stucco",
        "folder": SDF_INST_DIR,
        "vectors": {"BaseTint": (0.42, 0.32, 0.28, 1.0), "AccentTint": (0.62, 0.48, 0.38, 1.0)},
        "scalars": {"BandScale": 0.06, "BandStrength": 0.35},
    },
    {
        "master": "M_SDF_GildedStucco",
        "instance": "MI_SDF_GildedStucco_Wall",
        "profile": "TP_Stucco",
        "folder": SDF_INST_DIR,
        "vectors": {"BaseTint": (0.68, 0.58, 0.48, 1.0), "AccentTint": (0.82, 0.72, 0.55, 1.0)},
        "scalars": {"BandScale": 0.04, "BandStrength": 0.28},
    },
    {
        "master": "M_SDF_GothicArchitecture",
        "instance": "MI_SDF_GothicArchitecture_Stone",
        "profile": "TP_Stucco",
        "folder": SDF_INST_DIR,
        "vectors": {"BaseTint": (0.38, 0.36, 0.34, 1.0), "AccentTint": (0.52, 0.50, 0.48, 1.0)},
        "scalars": {"BandScale": 0.05, "BandStrength": 0.22},
    },
    {
        "master": "M_SDF_GothicArchitecture_Enhanced",
        "instance": "MI_SDF_GothicArchitecture_Enhanced_Detail",
        "profile": "TP_Stucco",
        "folder": SDF_INST_DIR,
        "vectors": {"BaseTint": (0.35, 0.33, 0.40, 1.0), "AccentTint": (0.55, 0.48, 0.62, 1.0)},
        "scalars": {"BandScale": 0.07, "BandStrength": 0.38},
    },
    {
        "master": "M_SDF_OrnamentLayer",
        "instance": "MI_SDF_OrnamentLayer_Classic",
        "profile": "TP_Ornamental",
        "folder": SDF_INST_DIR,
        "vectors": {"BaseTint": (0.72, 0.58, 0.38, 1.0), "AccentTint": (0.88, 0.72, 0.45, 1.0)},
        "scalars": {"BandScale": 0.065, "BandStrength": 0.42},
    },
    {
        "master": "M_SDF_OrnamentLayer_Enhanced",
        "instance": "MI_SDF_OrnamentLayer_Enhanced_Gold",
        "profile": "TP_Ornamental",
        "folder": SDF_INST_DIR,
        "vectors": {"BaseTint": (0.78, 0.62, 0.35, 1.0), "AccentTint": (0.92, 0.78, 0.42, 1.0)},
        "scalars": {"BandScale": 0.08, "BandStrength": 0.48},
    },
    {
        "master": "M_SDF_RayMarch_Gothic",
        "instance": "MI_SDF_RayMarch_Gothic_Deep",
        "profile": "TP_Stucco",
        "folder": SDF_INST_DIR,
        "vectors": {"BaseTint": (0.22, 0.18, 0.28, 1.0), "AccentTint": (0.38, 0.32, 0.48, 1.0)},
        "scalars": {"BandScale": 0.09, "BandStrength": 0.55},
    },
    {
        "master": "M_HybridStone_SDF",
        "instance": "MI_HybridStone_SDF_Moss",
        "profile": "TP_Default",
        "folder": SDF_INST_DIR,
        "vectors": {"StoneTint": (0.45, 0.42, 0.38, 1.0), "MossTint": (0.28, 0.38, 0.22, 1.0)},
        "scalars": {"WearAmount": 0.35, "StoneTiling": 1.2},
    },
    {
        "master": "M_SDF_TrueParallax",
        "instance": "MI_SDF_TrueParallax",
        "profile": "TP_Stucco",
        "folder": SDF_INST_DIR,
        "vectors": {"BaseTint": (0.72, 0.55, 0.85, 1.0), "AccentTint": (0.58, 0.42, 0.68, 1.0)},
        "scalars": {"BandScale": 0.035, "BandStrength": 0.22},
        "legacy_rename_from": "M_SDF_TrueParallax_Inst",
    },
    {
        "master": "M_Master_SDF_Toon",
        "instance": "MI_Master_SDF_Toon_Default",
        "profile": "TP_Stucco",
        "folder": SDF_INST_DIR,
        "vectors": {"BaseTint": (0.55, 0.48, 0.42, 1.0), "AccentTint": (0.72, 0.62, 0.52, 1.0)},
        "scalars": {"UVScale": 1.0, "ParallaxScale": 0.06, "BandScale": 0.035},
    },
    {
        "master": "M_Master_Toon_Unified",
        "instance": "MI_Master_Toon_Unified_Default",
        "profile": "TP_Default",
        "folder": f"{MATERIALS_ROOT}/Instances/Environment",
        "vectors": {"BaseTint": (0.55, 0.48, 0.42, 1.0), "AccentTint": (0.72, 0.62, 0.52, 1.0)},
        "scalars": {"UVScale": 1.0, "DryRoughness": 0.78},
    },
    {
        "master": "M_Master_Toon_Universal",
        "instance": "MI_Master_Toon_Universal_Default",
        "profile": "TP_Default",
        "folder": f"{MATERIALS_ROOT}/Instances/Environment",
        "vectors": {
            "BaseTint": (0.62, 0.58, 0.55, 1.0),
            "DreamTint": (1.0, 0.88, 0.94, 1.0),
            "RimColor": (0.70, 0.85, 1.0, 1.0),
            "GlowColor": (1.0, 0.92, 0.98, 1.0),
        },
        "scalars": {
            "TextureWeight": 1.0,
            "UVScale": 1.0,
            "Roughness": 0.65,
            "RimIntensity": 0.0,
            "GlowIntensity": 0.0,
            "PastelLift": 0.0,
            "BloomBoost": 0.0,
        },
    },
    # Aquatic / underwater SDF
    {
        "master": "M_SDF_AbyssalVent",
        "instance": "MI_SDF_AbyssalVent_Deep",
        "profile": "TP_Default",
        "folder": SDF_INST_DIR,
        "vectors": {"BaseTint": (0.08, 0.18, 0.32, 1.0), "AccentTint": (0.95, 0.42, 0.12, 1.0)},
        "scalars": {"BandScale": 0.05, "BandStrength": 0.45},
    },
    {
        "master": "M_SDF_Anemone",
        "instance": "MI_SDF_Anemone_Coral",
        "profile": "TP_Ornamental",
        "folder": SDF_INST_DIR,
        "vectors": {"BaseTint": (0.92, 0.38, 0.52, 1.0), "AccentTint": (0.98, 0.72, 0.78, 1.0)},
        "scalars": {"BandScale": 0.07, "BandStrength": 0.38},
    },
    {
        "master": "M_SDF_Bioluminescence",
        "instance": "MI_SDF_Bioluminescence_Glow",
        "profile": "TP_Ornamental",
        "folder": SDF_INST_DIR,
        "vectors": {"BaseTint": (0.05, 0.35, 0.48, 1.0), "AccentTint": (0.22, 0.95, 0.88, 1.0)},
        "scalars": {"BandScale": 0.04, "BandStrength": 0.62},
    },
    {
        "master": "M_SDF_BubbleColumn",
        "instance": "MI_SDF_BubbleColumn_Foam",
        "profile": "TP_Default",
        "folder": SDF_INST_DIR,
        "vectors": {"BaseTint": (0.55, 0.78, 0.92, 1.0), "AccentTint": (0.88, 0.95, 1.0, 1.0)},
        "scalars": {"BandScale": 0.03, "BandStrength": 0.28},
    },
    {
        "master": "M_SDF_Caustics_Underwater",
        "instance": "MI_SDF_Caustics_Underwater_Shallow",
        "profile": "TP_Default",
        "folder": SDF_INST_DIR,
        "vectors": {"BaseTint": (0.32, 0.58, 0.72, 1.0), "AccentTint": (0.78, 0.92, 0.98, 1.0)},
        "scalars": {"BandScale": 0.045, "BandStrength": 0.35},
    },
    {
        "master": "M_SDF_CoralBranching",
        "instance": "MI_SDF_CoralBranching_Reef",
        "profile": "TP_Ornamental",
        "folder": SDF_INST_DIR,
        "vectors": {"BaseTint": (0.88, 0.42, 0.28, 1.0), "AccentTint": (0.98, 0.62, 0.35, 1.0)},
        "scalars": {"BandScale": 0.06, "BandStrength": 0.42},
    },
    {
        "master": "M_SDF_FishSchool_Caustics",
        "instance": "MI_SDF_FishSchool_Caustics_Open",
        "profile": "TP_Default",
        "folder": SDF_INST_DIR,
        "vectors": {"BaseTint": (0.18, 0.38, 0.55, 1.0), "AccentTint": (0.72, 0.85, 0.95, 1.0)},
        "scalars": {"BandScale": 0.05, "BandStrength": 0.32},
    },
    {
        "master": "M_SDF_KelpCurtain",
        "instance": "MI_SDF_KelpCurtain_Forest",
        "profile": "TP_Foliage",
        "folder": SDF_INST_DIR,
        "vectors": {"BaseTint": (0.12, 0.28, 0.18, 1.0), "AccentTint": (0.35, 0.55, 0.28, 1.0)},
        "scalars": {"BandScale": 0.055, "BandStrength": 0.38},
    },
    {
        "master": "M_SDF_ThermalGlow",
        "instance": "MI_SDF_ThermalGlow_Vent",
        "profile": "TP_Ornamental",
        "folder": SDF_INST_DIR,
        "vectors": {"BaseTint": (0.15, 0.08, 0.12, 1.0), "AccentTint": (1.0, 0.45, 0.08, 1.0)},
        "scalars": {"BandScale": 0.05, "BandStrength": 0.55},
    },
]

# Extend INSTANCE_PROFILE_BY_STEM in convert_masters_to_substrate_toon.py
NEW_PROFILE_STEMS = {
    "MI_SDF_Baroque_Default": "TP_Stucco",
    "MI_SDF_GildedStucco_Wall": "TP_Stucco",
    "MI_SDF_GothicArchitecture_Stone": "TP_Stucco",
    "MI_SDF_GothicArchitecture_Enhanced_Detail": "TP_Stucco",
    "MI_SDF_OrnamentLayer_Classic": "TP_Ornamental",
    "MI_SDF_OrnamentLayer_Enhanced_Gold": "TP_Ornamental",
    "MI_SDF_RayMarch_Gothic_Deep": "TP_Stucco",
    "MI_HybridStone_SDF_Moss": "TP_Default",
    "MI_SDF_TrueParallax": "TP_Stucco",
    "MI_SDF_AbyssalVent_Deep": "TP_Default",
    "MI_SDF_Anemone_Coral": "TP_Ornamental",
    "MI_SDF_Bioluminescence_Glow": "TP_Ornamental",
    "MI_SDF_BubbleColumn_Foam": "TP_Default",
    "MI_SDF_Caustics_Underwater_Shallow": "TP_Default",
    "MI_SDF_CoralBranching_Reef": "TP_Ornamental",
    "MI_SDF_FishSchool_Caustics_Open": "TP_Default",
    "MI_SDF_KelpCurtain_Forest": "TP_Foliage",
    "MI_SDF_ThermalGlow_Vent": "TP_Ornamental",
}


def _starters_only_requested() -> bool:
    """When set, only rebuild MI_Show_* starters (skip SDF portfolio ensure pass)."""
    if os.environ.get("BS_STARTERS_ONLY", "").strip().lower() in ("1", "true", "yes", "on"):
        return True
    return any(str(a).lower() in ("--starters-only", "--starters") for a in sys.argv)


def _run_starters_only() -> int:
    import apply_starter_instances as starters
    import portfolio_texture_catalog as catalog

    unreal.log("=== Ensure portfolio instances (starters only) ===")
    results = starters.build_starter_instances()
    texture_pass = catalog.refresh_starter_instance_textures()
    report = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "mode": "starters_only",
        "starter_count": len(results),
        "instances": results,
        "texture_refresh": texture_pass,
    }
    REPORT_PATH.parent.mkdir(parents=True, exist_ok=True)
    REPORT_PATH.write_text(json.dumps(report, indent=2), encoding="utf-8")
    unreal.log(f"[EnsureInstances] starters={len(results)} -> {REPORT_PATH}")
    try:
        unreal.EditorLoadingAndSavingUtils.save_dirty_packages(True, True)
    except Exception:
        pass
    return 0


def _asset_path(folder: str, name: str) -> str:
    return f"{folder}/{name}.{name}"


def _ensure_directory(path: str) -> None:
    if not unreal.EditorAssetLibrary.does_directory_exist(path):
        unreal.EditorAssetLibrary.make_directory(path)


def _try_set_editor_property(obj, name: str, value) -> None:
    try:
        if hasattr(obj, "has_editor_property") and obj.has_editor_property(name):
            obj.set_editor_property(name, value)
    except Exception:
        pass


def _set_instance_vector(instance, name: str, rgba: tuple[float, float, float, float]) -> None:
    color = unreal.LinearColor(*rgba)
    if hasattr(unreal.MaterialEditingLibrary, "set_material_instance_vector_parameter_value"):
        unreal.MaterialEditingLibrary.set_material_instance_vector_parameter_value(
            instance, name, color
        )
    else:
        instance.set_vector_parameter_value_editor_only(name, color)


def _set_instance_scalar(instance, name: str, value: float) -> None:
    if hasattr(unreal.MaterialEditingLibrary, "set_material_instance_scalar_parameter_value"):
        unreal.MaterialEditingLibrary.set_material_instance_scalar_parameter_value(
            instance, name, value
        )
    else:
        instance.set_scalar_parameter_value_editor_only(name, value)


def _set_instance_toon_profile(instance, profile_name: str) -> None:
    profile_path = _asset_path(PROFILE_DIR, profile_name)
    if not unreal.EditorAssetLibrary.does_asset_exist(profile_path):
        return
    profile = unreal.load_asset(profile_path)
    _try_set_editor_property(instance, "toon_profile", profile)
    _try_set_editor_property(instance, "override_toon_profile", True)


def _apply_params(instance, spec: dict) -> None:
    for name, rgba in spec.get("vectors", {}).items():
        _set_instance_vector(instance, name, rgba)
    for name, value in spec.get("scalars", {}).items():
        _set_instance_scalar(instance, name, value)


def _rename_legacy_instance(spec: dict) -> str | None:
    legacy = spec.get("legacy_rename_from")
    if not legacy:
        return None
    legacy_path = _asset_path(spec["folder"], legacy)
    target_path = _asset_path(spec["folder"], spec["instance"])
    if unreal.EditorAssetLibrary.does_asset_exist(target_path):
        return target_path
    if not unreal.EditorAssetLibrary.does_asset_exist(legacy_path):
        return None
    if unreal.EditorAssetLibrary.rename_asset(legacy_path, target_path):
        unreal.log(f"[EnsureInstances] renamed {legacy_path} -> {target_path}")
        return target_path
    return None


def _master_has_child_instance(master_stem: str, folder: str) -> bool:
    if not unreal.EditorAssetLibrary.does_directory_exist(folder):
        return False
    for path in unreal.EditorAssetLibrary.list_assets(folder, recursive=True, include_folder=False):
        inst = unreal.load_asset(path)
        if not isinstance(inst, unreal.MaterialInstanceConstant):
            continue
        parent = inst.get_editor_property("parent")
        if parent and parent.get_name() == master_stem:
            return True
    return False


def ensure_instance(spec: dict) -> dict:
    master_stem = spec["master"]
    inst_stem = spec["instance"]
    folder = spec["folder"]
    master_path = _asset_path(MASTER_DIR, master_stem)
    inst_path = _asset_path(folder, inst_stem)
    result = {"master": master_path, "instance": inst_path, "status": "pending"}

    if not unreal.EditorAssetLibrary.does_asset_exist(master_path):
        result["status"] = "master_missing"
        return result

    _ensure_directory(folder)

    renamed = _rename_legacy_instance(spec)
    if renamed:
        inst_path = renamed

    if unreal.EditorAssetLibrary.does_asset_exist(inst_path):
        inst = unreal.load_asset(inst_path)
        _set_instance_toon_profile(inst, spec["profile"])
        _apply_params(inst, spec)
        unreal.EditorAssetLibrary.save_loaded_asset(inst, only_if_is_dirty=False)
        result["status"] = "updated"
        return result

    if _master_has_child_instance(master_stem, folder):
        result["status"] = "skipped_has_child"
        return result

    parent = unreal.load_asset(master_path)
    factory = unreal.MaterialInstanceConstantFactoryNew()
    asset_tools = unreal.AssetToolsHelpers.get_asset_tools()
    instance = asset_tools.create_asset(
        inst_stem, folder, unreal.MaterialInstanceConstant, factory
    )
    if not instance:
        result["status"] = "create_failed"
        return result

    unreal.MaterialEditingLibrary.set_material_instance_parent(instance, parent)
    _set_instance_toon_profile(instance, spec["profile"])
    _apply_params(instance, spec)
    unreal.EditorAssetLibrary.save_loaded_asset(instance, only_if_is_dirty=False)
    result["status"] = "created"
    return result


def audit_coverage() -> dict:
    import material_lib as lib

    masters: list[dict] = []
    env_inst = f"{MATERIALS_ROOT}/Instances/Environment"
    if not unreal.EditorAssetLibrary.does_directory_exist(MASTER_DIR):
        return {"masters": masters, "uncovered": []}

    for path in unreal.EditorAssetLibrary.list_assets(MASTER_DIR, recursive=False, include_folder=False):
        stem = lib.list_path_stem(path)
        if not stem.startswith("M_"):
            continue
        asset = unreal.load_asset(path)
        if not isinstance(asset, unreal.Material):
            continue
        covered = _master_has_child_instance(stem, SDF_INST_DIR)
        if not covered and stem in ("M_Master_Toon_Unified", "M_Master_Toon_Universal"):
            covered = _master_has_child_instance(stem, env_inst)
        if not covered and stem.startswith("M_Master_Impressionist"):
            covered = _master_has_child_instance(stem, IMP_INST_DIR)
        if stem == "M_Toon_SDF":
            covered = _master_has_child_instance(stem, SDF_INST_DIR)
        masters.append({"path": path, "stem": stem, "has_instance": covered})

    uncovered = [m for m in masters if not m["has_instance"]]
    return {"masters": masters, "uncovered": uncovered}


def _default_instance_spec(master_stem: str) -> dict:
    """Fallback MI for any uncovered M_SDF_* master."""
    suffix = master_stem.replace("M_SDF_", "")
    return {
        "master": master_stem,
        "instance": f"MI_SDF_{suffix}_Default",
        "profile": "TP_Default",
        "folder": SDF_INST_DIR,
        "vectors": {"BaseTint": (0.45, 0.48, 0.52, 1.0), "AccentTint": (0.62, 0.65, 0.72, 1.0)},
        "scalars": {"BandScale": 0.05, "BandStrength": 0.3},
    }


def main() -> int:
    if _starters_only_requested():
        return _run_starters_only()

    unreal.log("=== Ensure portfolio material instances ===")
    results = [ensure_instance(spec) for spec in MASTER_INSTANCES]
    coverage = audit_coverage()
    for entry in coverage["uncovered"]:
        stem = entry["stem"]
        if not stem.startswith("M_SDF_"):
            continue
        results.append(ensure_instance(_default_instance_spec(stem)))
    coverage = audit_coverage()

    report = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "results": results,
        "coverage": coverage,
        "new_profile_stems": NEW_PROFILE_STEMS,
    }
    REPORT_PATH.parent.mkdir(parents=True, exist_ok=True)
    REPORT_PATH.write_text(json.dumps(report, indent=2), encoding="utf-8")

    created = sum(1 for r in results if r["status"] == "created")
    updated = sum(1 for r in results if r["status"] == "updated")
    uncovered = len(coverage["uncovered"])
    unreal.log(f"[EnsureInstances] created={created} updated={updated} uncovered_masters={uncovered}")
    unreal.log(f"[EnsureInstances] report: {REPORT_PATH}")

    unreal.EditorLoadingAndSavingUtils.save_dirty_packages(True, True)
    return 0 if uncovered == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
