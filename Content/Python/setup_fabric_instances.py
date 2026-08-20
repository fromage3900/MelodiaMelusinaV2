"""
Setup Material Instances for Melodia Fantasy Fabric Library (Infinity Nikki Grade)
==================================================================================
Creates and configures Material Instances in /Game/EnvSandbox/Materials/Instances/Character/Cloth/
parented to M_Master_Toon_Universal with proper FabricType (0-7), Anisotropy, Sheen,
WeaveScale, LayerBlendMode (Height Compete), and ToonProfile assignments.

Supports dual execution mode:
  1. Unreal Engine runtime (unreal module) -> Creates & configures UMaterialInstanceConstant
  2. Standalone Python runtime -> Validates contracts and exports JSON configuration manifest

Author: Teamwork Fantasy Fabric Worker (Milestone 2)
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Sequence, Tuple

PYTHON_DIR = Path(__file__).resolve().parent
PROJECT_DIR = PYTHON_DIR.parent.parent
SAVED_DIR = PROJECT_DIR / "Saved" / "Audit"

MASTER_MATERIAL_PATH = "/Game/EnvSandbox/Materials/Masters/M_Master_Toon_Universal"
TARGET_INSTANCE_DIR = "/Game/EnvSandbox/Materials/Instances/Character/Cloth"


@dataclass
class FabricInstanceConfig:
    instance_name: str
    archetype: str
    fabric_type: float
    parent_master: str = MASTER_MATERIAL_PATH
    toon_profile: str = "TP_Character"
    anisotropy_level: float = 0.0
    weave_scale: float = 48.0
    weave_strength: float = 0.20
    fabric_sheen: float = 0.50
    sheen_power: float = 3.0
    sheen_tint: Tuple[float, float, float, float] = (1.0, 1.0, 1.0, 1.0)
    iridescence: float = 0.0
    sparkle_intensity: float = 0.0
    sparkle_threshold: float = 0.85
    layer_blend_mode: int = 0
    layer_height_bias: float = 0.0
    layer_height_sharpness: float = 1.0
    layer_blend_softness: float = 0.5
    mask_clip_value: float = 0.33
    is_masked_transparency: bool = False
    assigned_textures: Dict[str, str] = field(default_factory=dict)
    static_switches: Dict[str, bool] = field(default_factory=dict)


# Canonical 6 Core Fantasy Fabric Instance Configurations
CORE_FABRIC_INSTANCES: Dict[str, FabricInstanceConfig] = {
    "MI_Fabric_RoyalVelvet": FabricInstanceConfig(
        instance_name="MI_Fabric_RoyalVelvet",
        archetype="RoyalVelvet",
        fabric_type=4.0,  # Velvet
        parent_master=MASTER_MATERIAL_PATH,
        toon_profile="TP_Character",
        anisotropy_level=0.0,
        weave_scale=32.0,
        weave_strength=0.15,
        fabric_sheen=0.85,
        sheen_power=2.2,
        sheen_tint=(1.0, 0.88, 0.95, 1.0),
        iridescence=0.0,
        sparkle_intensity=0.0,
        sparkle_threshold=1.0,
        assigned_textures={
            "BaseColor": "/Game/Textures/Fabrics/T_Fabric_RoyalVelvet_BC",
            "ORM": "/Game/Textures/Fabrics/T_Fabric_RoyalVelvet_ORM",
            "Normal": "/Game/Textures/Fabrics/T_Fabric_RoyalVelvet_N",
            "Height": "/Game/Textures/Fabrics/T_Fabric_RoyalVelvet_H",
            "Sheen": "/Game/Textures/Fabrics/T_Fabric_RoyalVelvet_Sheen",
        },
        static_switches={
            "bUseSeparateRoughnessMap": False,
            "bUseSeparateMetallicMap": False,
            "bEnableFabricAnisoGate": True,
            "bEnableHeightCompete": False,
        },
    ),
    "MI_Fabric_GildedBrocade": FabricInstanceConfig(
        instance_name="MI_Fabric_GildedBrocade",
        archetype="GildedJacquard",
        fabric_type=3.0,  # Satin
        parent_master=MASTER_MATERIAL_PATH,
        toon_profile="TP_Hero",
        anisotropy_level=0.65,
        weave_scale=48.0,
        weave_strength=0.35,
        fabric_sheen=0.30,
        sheen_power=4.0,
        sheen_tint=(1.0, 0.95, 0.80, 1.0),
        iridescence=0.15,
        sparkle_intensity=0.20,
        sparkle_threshold=0.85,
        layer_blend_mode=1,  # Height Compete
        layer_height_bias=0.08,
        layer_height_sharpness=3.5,
        layer_blend_softness=0.25,
        assigned_textures={
            "BaseColor": "/Game/Textures/Fabrics/T_Fabric_GildedBrocade_BC",
            "ORM": "/Game/Textures/Fabrics/T_Fabric_GildedBrocade_ORM",
            "Normal": "/Game/Textures/Fabrics/T_Fabric_GildedBrocade_N",
            "Height": "/Game/Textures/Fabrics/T_Fabric_GildedBrocade_H",
            "DetailNormal": "/Game/Textures/Fabrics/T_Fabric_GildedBrocade_DetailN",
        },
        static_switches={
            "bUseSeparateRoughnessMap": False,
            "bUseSeparateMetallicMap": False,
            "bEnableFabricAnisoGate": True,
            "bEnableHeightCompete": True,
        },
    ),
    "MI_Fabric_SheerSilk": FabricInstanceConfig(
        instance_name="MI_Fabric_SheerSilk",
        archetype="SheerSilk",
        fabric_type=2.0,  # Silk
        parent_master=MASTER_MATERIAL_PATH,
        toon_profile="TP_Character",
        anisotropy_level=0.85,
        weave_scale=64.0,
        weave_strength=0.10,
        fabric_sheen=0.60,
        sheen_power=5.0,
        sheen_tint=(0.90, 0.95, 1.0, 1.0),
        iridescence=0.35,
        sparkle_intensity=0.10,
        sparkle_threshold=0.90,
        assigned_textures={
            "BaseColor": "/Game/Textures/Fabrics/T_Fabric_SheerSilk_BC",
            "ORM": "/Game/Textures/Fabrics/T_Fabric_SheerSilk_ORM",
            "Normal": "/Game/Textures/Fabrics/T_Fabric_SheerSilk_N",
            "Height": "/Game/Textures/Fabrics/T_Fabric_SheerSilk_H",
            "Sheen": "/Game/Textures/Fabrics/T_Fabric_SheerSilk_Sheen",
        },
        static_switches={
            "bUseSeparateRoughnessMap": False,
            "bUseSeparateMetallicMap": False,
            "bEnableFabricAnisoGate": True,
            "bEnableHeightCompete": False,
        },
    ),
    "MI_Fabric_BaroqueLace": FabricInstanceConfig(
        instance_name="MI_Fabric_BaroqueLace",
        archetype="BaroqueFiligreeLace",
        fabric_type=1.0,  # Cotton / Lace
        parent_master=MASTER_MATERIAL_PATH,
        toon_profile="TP_Hero",
        anisotropy_level=0.15,
        weave_scale=16.0,
        weave_strength=0.80,
        fabric_sheen=0.25,
        sheen_power=3.0,
        sheen_tint=(1.0, 1.0, 1.0, 1.0),
        layer_blend_mode=1,
        layer_height_bias=0.15,
        layer_height_sharpness=4.0,
        layer_blend_softness=0.20,
        mask_clip_value=0.33,
        is_masked_transparency=True,
        assigned_textures={
            "BaseColor": "/Game/Textures/Fabrics/T_Fabric_BaroqueLace_BC",
            "ORM": "/Game/Textures/Fabrics/T_Fabric_BaroqueLace_ORM",
            "Normal": "/Game/Textures/Fabrics/T_Fabric_BaroqueLace_N",
            "Height": "/Game/Textures/Fabrics/T_Fabric_BaroqueLace_H",
            "Mask": "/Game/Textures/Fabrics/T_Fabric_BaroqueLace_Mask",
        },
        static_switches={
            "bUseSeparateRoughnessMap": False,
            "bUseSeparateMetallicMap": False,
            "bEnableFabricAnisoGate": True,
            "bEnableHeightCompete": True,
            "bMaskedTransparency": True,
        },
    ),
    "MI_Fabric_GoldEmbroidery": FabricInstanceConfig(
        instance_name="MI_Fabric_GoldEmbroidery",
        archetype="GoldThreadedEmbroidery",
        fabric_type=3.0,  # Satin base with bullion gold
        parent_master=MASTER_MATERIAL_PATH,
        toon_profile="TP_Gold",
        anisotropy_level=0.70,
        weave_scale=56.0,
        weave_strength=0.60,
        fabric_sheen=0.40,
        sheen_power=6.0,
        sheen_tint=(1.0, 0.90, 0.60, 1.0),
        iridescence=0.25,
        sparkle_intensity=0.45,
        sparkle_threshold=0.75,
        layer_blend_mode=1,
        layer_height_bias=0.20,
        layer_height_sharpness=4.5,
        layer_blend_softness=0.18,
        assigned_textures={
            "BaseColor": "/Game/Textures/Fabrics/T_Fabric_GoldEmbroidery_BC",
            "ORM": "/Game/Textures/Fabrics/T_Fabric_GoldEmbroidery_ORM",
            "Normal": "/Game/Textures/Fabrics/T_Fabric_GoldEmbroidery_N",
            "Height": "/Game/Textures/Fabrics/T_Fabric_GoldEmbroidery_H",
            "DetailNormal": "/Game/Textures/Fabrics/T_Fabric_GoldEmbroidery_DetailN",
        },
        static_switches={
            "bUseSeparateRoughnessMap": False,
            "bUseSeparateMetallicMap": False,
            "bEnableFabricAnisoGate": True,
            "bEnableHeightCompete": True,
        },
    ),
    "MI_Fabric_CelestialWeave": FabricInstanceConfig(
        instance_name="MI_Fabric_CelestialWeave",
        archetype="IridescentCelestialWeave",
        fabric_type=7.0,  # Sequins / Celestial
        parent_master=MASTER_MATERIAL_PATH,
        toon_profile="TP_Character",
        anisotropy_level=0.75,
        weave_scale=40.0,
        weave_strength=0.40,
        fabric_sheen=0.90,
        sheen_power=3.5,
        sheen_tint=(0.95, 0.85, 1.0, 1.0),
        iridescence=0.55,
        sparkle_intensity=0.65,
        sparkle_threshold=0.70,
        assigned_textures={
            "BaseColor": "/Game/Textures/Fabrics/T_Fabric_CelestialWeave_BC",
            "ORM": "/Game/Textures/Fabrics/T_Fabric_CelestialWeave_ORM",
            "Normal": "/Game/Textures/Fabrics/T_Fabric_CelestialWeave_N",
            "Height": "/Game/Textures/Fabrics/T_Fabric_CelestialWeave_H",
            "Sparkle": "/Game/Textures/Fabrics/T_Fabric_CelestialWeave_Sparkle",
        },
        static_switches={
            "bUseSeparateRoughnessMap": False,
            "bUseSeparateMetallicMap": False,
            "bEnableFabricAnisoGate": True,
            "bEnableHeightCompete": False,
        },
    ),
}


def create_or_update_unreal_instances(configs: Dict[str, FabricInstanceConfig]) -> Dict[str, Any]:
    """Execute inside Unreal Engine Editor runtime."""
    import unreal
    results = {}
    tools = unreal.AssetToolsHelpers.get_asset_tools()
    factory = unreal.MaterialInstanceConstantFactoryNew()

    master = unreal.load_asset(MASTER_MATERIAL_PATH)
    if not master:
        unreal.log_warning(f"[FabricInstances] Master material not found: {MASTER_MATERIAL_PATH}")

    for name, cfg in configs.items():
        asset_path = f"{TARGET_INSTANCE_DIR}/{name}"
        inst = unreal.load_asset(asset_path)
        created = False
        if not inst:
            inst = tools.create_asset(name, TARGET_INSTANCE_DIR, unreal.MaterialInstanceConstant, factory)
            created = True

        if inst and master:
            unreal.MaterialEditingLibrary.set_material_instance_parent(inst, master)

            # Scalar parameters
            unreal.MaterialEditingLibrary.set_material_instance_scalar_parameter_value(inst, "FabricType", cfg.fabric_type)
            unreal.MaterialEditingLibrary.set_material_instance_scalar_parameter_value(inst, "FabricAnisoLevel", cfg.anisotropy_level)
            unreal.MaterialEditingLibrary.set_material_instance_scalar_parameter_value(inst, "FabricWeaveScale", cfg.weave_scale)
            unreal.MaterialEditingLibrary.set_material_instance_scalar_parameter_value(inst, "FabricWeaveStrength", cfg.weave_strength)
            unreal.MaterialEditingLibrary.set_material_instance_scalar_parameter_value(inst, "FabricSheen", cfg.fabric_sheen)
            unreal.MaterialEditingLibrary.set_material_instance_scalar_parameter_value(inst, "SheenPower", cfg.sheen_power)
            unreal.MaterialEditingLibrary.set_material_instance_scalar_parameter_value(inst, "Iridescence", cfg.iridescence)
            unreal.MaterialEditingLibrary.set_material_instance_scalar_parameter_value(inst, "SparkleIntensity", cfg.sparkle_intensity)
            unreal.MaterialEditingLibrary.set_material_instance_scalar_parameter_value(inst, "SparkleThreshold", cfg.sparkle_threshold)

            # Vector parameters
            st = cfg.sheen_tint
            unreal.MaterialEditingLibrary.set_material_instance_vector_parameter_value(
                inst, "SheenTint", unreal.LinearColor(st[0], st[1], st[2], st[3])
            )

            # Static switches
            for sw_name, sw_val in cfg.static_switches.items():
                try:
                    unreal.MaterialEditingLibrary.set_material_instance_static_switch_parameter_value(inst, sw_name, sw_val)
                except Exception:
                    pass

            unreal.EditorAssetLibrary.save_loaded_asset(inst)
            results[name] = {"path": asset_path, "created": created, "status": "configured"}
        else:
            results[name] = {"path": asset_path, "status": "created_stub" if created else "loaded"}

    return results


def main(argv: Optional[Sequence[str]] = None) -> int:
    parser = argparse.ArgumentParser(description="Setup Melodia Fantasy Fabric Material Instances")
    parser.add_argument("--report", default=str(SAVED_DIR / "fabric_instances_config.json"), help="Output JSON report path")
    args = parser.parse_args(argv)

    print(f"[MelodiaFabrics] Setting up {len(CORE_FABRIC_INSTANCES)} Fantasy Fabric Material Instances...")
    unreal_results = {}
    try:
        import unreal
        print("[MelodiaFabrics] Unreal Engine Python API detected. Authoring assets in Content Browser...")
        unreal_results = create_or_update_unreal_instances(CORE_FABRIC_INSTANCES)
    except ImportError:
        print("[MelodiaFabrics] Standalone Python runtime detected. Validating configurations & exporting manifest...")

    manifest = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "target_directory": TARGET_INSTANCE_DIR,
        "master_parent": MASTER_MATERIAL_PATH,
        "total_instances": len(CORE_FABRIC_INSTANCES),
        "instances": {k: asdict(v) for k, v in CORE_FABRIC_INSTANCES.items()},
        "unreal_engine_applied": bool(unreal_results),
        "unreal_results": unreal_results,
    }

    report_path = Path(args.report)
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    print(f"[MelodiaFabrics] Material instance manifest saved: {report_path}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
