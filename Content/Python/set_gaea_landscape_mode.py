"""Set the Glacier landscape instance to a deliberate Gaea sampling mode.

``whole_map`` samples the exported Gaea maps once across the landscape using
the shared normalized world-XY UV.  ``triplanar_detail`` opts into the
existing Substance-Painter-style triplanar function for close-up detail.

The two switches are kept mutually exclusive so a full-landscape export can
never be routed through world-space triplanar sampling by accident.
"""

import json
import os

import unreal


INSTANCE_PATH = "/Game/Gaea/Glacier/Materials/MI_Glacier_Landscape_Layered"
REPORT_PATH = "C:/EnvironmentPortfolio/BS_GodFile/Saved/Audit/gaea_landscape_mode.json"


def set_mode(mode="whole_map", instance_path=INSTANCE_PATH):
    if mode not in ("whole_map", "triplanar_detail"):
        raise ValueError("mode must be 'whole_map' or 'triplanar_detail'")

    instance = unreal.load_asset(instance_path)
    if instance is None:
        raise RuntimeError("Missing Gaea landscape instance: %s" % instance_path)

    before = {
        "whole_map": bool(unreal.MaterialEditingLibrary.get_material_instance_static_switch_parameter_value(
            instance, "bGaeaWholeLandscapeColor"
        )),
        "triplanar_detail": bool(unreal.MaterialEditingLibrary.get_material_instance_static_switch_parameter_value(
            instance, "bTriplanarPro_Active"
        )),
    }

    whole_map = mode == "whole_map"
    unreal.MaterialEditingLibrary.set_material_instance_static_switch_parameter_value(
        instance, "bGaeaWholeLandscapeColor", whole_map
    )
    unreal.MaterialEditingLibrary.set_material_instance_static_switch_parameter_value(
        instance, "bTriplanarPro_Active", not whole_map
    )
    unreal.MaterialEditingLibrary.update_material_instance(instance)
    unreal.EditorAssetLibrary.save_loaded_asset(instance, False)

    after = {
        "whole_map": bool(unreal.MaterialEditingLibrary.get_material_instance_static_switch_parameter_value(
            instance, "bGaeaWholeLandscapeColor"
        )),
        "triplanar_detail": bool(unreal.MaterialEditingLibrary.get_material_instance_static_switch_parameter_value(
            instance, "bTriplanarPro_Active"
        )),
    }
    if after != {"whole_map": whole_map, "triplanar_detail": not whole_map}:
        raise RuntimeError("Gaea mode did not settle: %s" % after)

    report = {
        "instance_path": instance_path,
        "mode": mode,
        "before": before,
        "after": after,
        "contract": "whole_map uses normalized Gaea UV; triplanar_detail uses MF_Triplanar_LandscapePro",
    }
    os.makedirs(os.path.dirname(REPORT_PATH), exist_ok=True)
    with open(REPORT_PATH, "w", encoding="utf-8") as handle:
        json.dump(report, handle, indent=2)
    return report


if __name__ == "__main__":
    print(set_mode("whole_map"))
