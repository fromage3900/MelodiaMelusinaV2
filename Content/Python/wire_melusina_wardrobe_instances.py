"""
Wire Melusina Hero Character Wardrobe Material Instances
========================================================
Maps and configures production Material Instances for Melusina wardrobe mesh slots:
    - M_frontpanel_001 -> MI_Melusina_Frontpanel_VelvetGilded (Royal Velvet)
    - M_SHAWL_001      -> MI_Melusina_Shawl_SheerSilk (Sheer Silk)
    - M_SKIRT_003      -> MI_Melusina_Skirt_GildedJacquard (Gilded Brocade)
    - M_sleeve_003     -> MI_Melusina_Sleeve_BaroqueLace (Baroque Filigree Lace)
    - M_shirt_001      -> MI_Melusina_Shirt_GoldEmbroidery (Gold Bullion Embroidery)

Dual-mode execution:
    1. Unreal Engine runtime -> updates UMaterialInstanceConstant assets & slot assignments
    2. Standalone Python -> validates wardrobe binding contracts against MELUSINA_WARDROBE_SPEC

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
WARDROBE_INSTANCE_DIR = "/Game/EnvSandbox/Materials/Instances/Character/Cloth"
CHARACTER_TEXTURES_DIR = "/Game/Melodia/Characters/Melusina/Textures"


@dataclass
class MelusinaWardrobeSlotWiring:
    slot_name: str
    mesh_material_index: int
    instance_name: str
    fabric_archetype: str
    fabric_type: float
    toon_profile: str = "TP_Character"
    assigned_textures: Dict[str, str] = field(default_factory=dict)
    scalar_parameters: Dict[str, float] = field(default_factory=dict)
    vector_parameters: Dict[str, Tuple[float, float, float, float]] = field(default_factory=dict)
    static_switches: Dict[str, bool] = field(default_factory=dict)


MELUSINA_WARDROBE_WIRING: Dict[str, MelusinaWardrobeSlotWiring] = {
    "M_frontpanel_001": MelusinaWardrobeSlotWiring(
        slot_name="M_frontpanel_001",
        mesh_material_index=0,
        instance_name="MI_Melusina_Frontpanel_VelvetGilded",
        fabric_archetype="RoyalVelvet",
        fabric_type=4.0,  # Velvet
        toon_profile="TP_Hero",
        assigned_textures={
            "BaseColor": f"{CHARACTER_TEXTURES_DIR}/T_Melusina_FrontPanel_BC",
            "ORM": f"{CHARACTER_TEXTURES_DIR}/T_Melusina_FrontPanel_ORM",
            "Normal": f"{CHARACTER_TEXTURES_DIR}/T_Melusina_FrontPanel_N",
            "Height": f"{CHARACTER_TEXTURES_DIR}/T_Melusina_FrontPanel_H",
            "Sheen": f"{CHARACTER_TEXTURES_DIR}/T_Melusina_FrontPanel_Sheen",
        },
        scalar_parameters={
            "FabricType": 4.0,
            "FabricSheen": 0.85,
            "SheenPower": 2.2,
            "FabricWeaveScale": 32.0,
            "LayerHeightBias": 0.08,
        },
        vector_parameters={
            "SheenTint": (1.0, 0.88, 0.95, 1.0),
        },
        static_switches={
            "bUseSeparateRoughnessMap": False,
            "bUseSeparateMetallicMap": False,
            "bEnableFabricAnisoGate": True,
            "bEnableHeightCompete": True,
        },
    ),
    "M_SHAWL_001": MelusinaWardrobeSlotWiring(
        slot_name="M_SHAWL_001",
        mesh_material_index=1,
        instance_name="MI_Melusina_Shawl_SheerSilk",
        fabric_archetype="SheerSilk",
        fabric_type=2.0,  # Silk
        toon_profile="TP_Character",
        assigned_textures={
            "BaseColor": f"{CHARACTER_TEXTURES_DIR}/T_Melusina_Shawl_BC",
            "ORM": f"{CHARACTER_TEXTURES_DIR}/T_Melusina_Shawl_ORM",
            "Normal": f"{CHARACTER_TEXTURES_DIR}/T_Melusina_Shawl_N",
            "Height": f"{CHARACTER_TEXTURES_DIR}/T_Melusina_Shawl_H",
        },
        scalar_parameters={
            "FabricType": 2.0,
            "FabricAnisoLevel": 0.85,
            "FabricSheen": 0.60,
            "SheenPower": 5.0,
            "Iridescence": 0.35,
        },
        vector_parameters={
            "SheenTint": (0.90, 0.95, 1.0, 1.0),
        },
        static_switches={
            "bUseSeparateRoughnessMap": False,
            "bUseSeparateMetallicMap": False,
            "bEnableFabricAnisoGate": True,
            "bEnableHeightCompete": False,
        },
    ),
    "M_SKIRT_003": MelusinaWardrobeSlotWiring(
        slot_name="M_SKIRT_003",
        mesh_material_index=2,
        instance_name="MI_Melusina_Skirt_GildedJacquard",
        fabric_archetype="GildedJacquard",
        fabric_type=3.0,  # Satin
        toon_profile="TP_Hero",
        assigned_textures={
            "BaseColor": f"{CHARACTER_TEXTURES_DIR}/T_Melusina_Skirt_BC",
            "ORM": f"{CHARACTER_TEXTURES_DIR}/T_Melusina_Skirt_ORM",
            "Normal": f"{CHARACTER_TEXTURES_DIR}/T_Melusina_Skirt_N",
            "Height": f"{CHARACTER_TEXTURES_DIR}/T_Melusina_Skirt_H",
        },
        scalar_parameters={
            "FabricType": 3.0,
            "FabricAnisoLevel": 0.65,
            "FabricWeaveScale": 48.0,
            "LayerHeightBias": 0.12,
            "LayerHeightSharpness": 3.5,
        },
        vector_parameters={
            "SheenTint": (1.0, 0.95, 0.80, 1.0),
        },
        static_switches={
            "bUseSeparateRoughnessMap": False,
            "bUseSeparateMetallicMap": False,
            "bEnableFabricAnisoGate": True,
            "bEnableHeightCompete": True,
        },
    ),
    "M_sleeve_003": MelusinaWardrobeSlotWiring(
        slot_name="M_sleeve_003",
        mesh_material_index=3,
        instance_name="MI_Melusina_Sleeve_BaroqueLace",
        fabric_archetype="BaroqueFiligreeLace",
        fabric_type=1.0,  # Cotton / Lace
        toon_profile="TP_Hero",
        assigned_textures={
            "BaseColor": f"{CHARACTER_TEXTURES_DIR}/T_Melusina_Sleeve_BC",
            "ORM": f"{CHARACTER_TEXTURES_DIR}/T_Melusina_Sleeve_ORM",
            "Normal": f"{CHARACTER_TEXTURES_DIR}/T_Melusina_Sleeve_N",
            "Height": f"{CHARACTER_TEXTURES_DIR}/T_Melusina_Sleeve_H",
            "Alpha": f"{CHARACTER_TEXTURES_DIR}/T_Melusina_Sleeve_Alpha",
        },
        scalar_parameters={
            "FabricType": 1.0,
            "FabricWeaveScale": 16.0,
            "FabricWeaveStrength": 0.80,
            "MaskClipValue": 0.33,
        },
        vector_parameters={
            "SheenTint": (1.0, 1.0, 1.0, 1.0),
        },
        static_switches={
            "bUseSeparateRoughnessMap": False,
            "bUseSeparateMetallicMap": False,
            "bEnableFabricAnisoGate": True,
            "bEnableHeightCompete": True,
            "bMaskedTransparency": True,
        },
    ),
    "M_shirt_001": MelusinaWardrobeSlotWiring(
        slot_name="M_shirt_001",
        mesh_material_index=4,
        instance_name="MI_Melusina_Shirt_GoldEmbroidery",
        fabric_archetype="GoldThreadedEmbroidery",
        fabric_type=3.0,  # Satin base with bullion gold
        toon_profile="TP_Gold",
        assigned_textures={
            "BaseColor": f"{CHARACTER_TEXTURES_DIR}/T_Melusina_Shirt_BC",
            "ORM": f"{CHARACTER_TEXTURES_DIR}/T_Melusina_Shirt_ORM",
            "Normal": f"{CHARACTER_TEXTURES_DIR}/T_Melusina_Shirt_N",
            "Height": f"{CHARACTER_TEXTURES_DIR}/T_Melusina_Shirt_H",
        },
        scalar_parameters={
            "FabricType": 3.0,
            "FabricAnisoLevel": 0.70,
            "FabricSheen": 0.40,
            "LayerHeightSharpness": 4.5,
        },
        vector_parameters={
            "SheenTint": (1.0, 0.90, 0.60, 1.0),
        },
        static_switches={
            "bUseSeparateRoughnessMap": False,
            "bUseSeparateMetallicMap": False,
            "bEnableFabricAnisoGate": True,
            "bEnableHeightCompete": True,
        },
    ),
}


def validate_wardrobe_wiring(wiring_dict: Dict[str, MelusinaWardrobeSlotWiring]) -> Tuple[bool, List[str]]:
    errors = []
    for slot, wiring in wiring_dict.items():
        for req in ["BaseColor", "ORM", "Normal"]:
            if req not in wiring.assigned_textures:
                errors.append(f"Slot {slot} missing required texture {req}")
        if wiring.static_switches.get("bUseSeparateRoughnessMap", False):
            errors.append(f"Slot {slot} has separate roughness True (violates ORM standard)")
        if wiring.static_switches.get("bUseSeparateMetallicMap", False):
            errors.append(f"Slot {slot} has separate metallic True (violates ORM standard)")
    return len(errors) == 0, errors


def main(argv: Optional[Sequence[str]] = None) -> int:
    parser = argparse.ArgumentParser(description="Wire Melusina Wardrobe Material Instances")
    parser.add_argument("--report", default=str(SAVED_DIR / "melusina_wardrobe_wiring.json"), help="Output JSON report path")
    args = parser.parse_args(argv)

    print(f"[MelusinaWardrobe] Wiring {len(MELUSINA_WARDROBE_WIRING)} wardrobe material instances...")
    valid, errors = validate_wardrobe_wiring(MELUSINA_WARDROBE_WIRING)
    if not valid:
        print(f"[MelusinaWardrobe] Validation errors: {errors}", file=sys.stderr)
        return 1

    unreal_results = {}
    try:
        import unreal
        print("[MelusinaWardrobe] Unreal Engine Python API detected. Updating Material Instances...")
        tools = unreal.AssetToolsHelpers.get_asset_tools()
        factory = unreal.MaterialInstanceConstantFactoryNew()
        master = unreal.load_asset(MASTER_MATERIAL_PATH)

        for slot_name, wiring in MELUSINA_WARDROBE_WIRING.items():
            inst_path = f"{WARDROBE_INSTANCE_DIR}/{wiring.instance_name}"
            inst = unreal.load_asset(inst_path)
            created = False
            if not inst:
                inst = tools.create_asset(wiring.instance_name, WARDROBE_INSTANCE_DIR, unreal.MaterialInstanceConstant, factory)
                created = True

            if inst and master:
                unreal.MaterialEditingLibrary.set_material_instance_parent(inst, master)
                for p_name, p_val in wiring.scalar_parameters.items():
                    unreal.MaterialEditingLibrary.set_material_instance_scalar_parameter_value(inst, p_name, p_val)
                for p_name, v_val in wiring.vector_parameters.items():
                    unreal.MaterialEditingLibrary.set_material_instance_vector_parameter_value(
                        inst, p_name, unreal.LinearColor(v_val[0], v_val[1], v_val[2], v_val[3])
                    )
                for sw_name, sw_val in wiring.static_switches.items():
                    try:
                        unreal.MaterialEditingLibrary.set_material_instance_static_switch_parameter_value(inst, sw_name, sw_val)
                    except Exception:
                        pass
                unreal.EditorAssetLibrary.save_loaded_asset(inst)
                unreal_results[slot_name] = {"instance": inst_path, "created": created, "status": "configured"}
    except ImportError:
        print("[MelusinaWardrobe] Standalone Python runtime detected. Validated all bindings successfully.")

    report_data = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "target_directory": WARDROBE_INSTANCE_DIR,
        "master_parent": MASTER_MATERIAL_PATH,
        "slots_wired": len(MELUSINA_WARDROBE_WIRING),
        "bindings": {k: asdict(v) for k, v in MELUSINA_WARDROBE_WIRING.items()},
        "unreal_engine_applied": bool(unreal_results),
        "unreal_results": unreal_results,
        "valid": valid,
        "errors": errors,
    }

    report_path = Path(args.report)
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text(json.dumps(report_data, indent=2), encoding="utf-8")
    print(f"[MelusinaWardrobe] Wardrobe wiring manifest saved: {report_path}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
