"""Create and assign Melusina's dedicated water-hair material path."""
from __future__ import annotations
import json
from datetime import datetime, timezone
from pathlib import Path

PROJECT = Path(__file__).resolve().parents[2]
REPORT = PROJECT / "Saved/Audit/melusina_water_hair.json"
MASTER = "/Game/EnvSandbox/Materials/Masters/M_Water_Master_Grand_v6"
INSTANCE = "/Game/EnvSandbox/Materials/Instances/Melusina/MI_Melusina_WaterHair"
MESH = "/Game/Melodia/Characters/Melusina/Hair/SK_MelusinaHair"

def main() -> dict:
    import unreal
    asset_tools = unreal.AssetToolsHelpers.get_asset_tools()
    parent = unreal.EditorAssetLibrary.load_asset(MASTER)
    if not parent:
        raise RuntimeError(f"Missing parent material: {MASTER}")
    folder, name = INSTANCE.rsplit("/", 1)
    mi = unreal.EditorAssetLibrary.load_asset(INSTANCE)
    if not mi:
        mi = asset_tools.create_asset(name, folder, unreal.MaterialInstanceConstant,
                                      unreal.MaterialInstanceConstantFactoryNew())
    if not mi:
        raise RuntimeError(f"Could not create {INSTANCE}")
    unreal.MaterialEditingLibrary.set_material_instance_parent(mi, parent)
    # Hair-safe defaults: retain color/reactivity, remove surface-water behavior.
    values = {
        "GerstnerScale": 0.0,
        "WaveSpeed": 0.0,
        "RefractionStrength": 0.0,
        "ShorelineWidth": 0.0,
        "ShorelineFoam": 0.0,
        "DepthFadeDistance": 0.0,
        "Opacity": 0.92,
        "WaterRoughness": 0.22,
        "MagicalIntensity": 0.18,
        "CausticIntensity": 0.12,
    }
    for param, value in values.items():
        try:
            unreal.MaterialEditingLibrary.set_material_instance_scalar_parameter_value(mi, param, value)
        except Exception:
            pass
    unreal.EditorAssetLibrary.save_loaded_asset(mi, only_if_is_dirty=False)

    mesh = unreal.EditorAssetLibrary.load_asset(MESH)
    assigned_slots = []
    if mesh:
        try:
            materials = list(mesh.get_editor_property("materials") or [])
            new_materials = []
            for index, slot in enumerate(materials):
                new_materials.append(unreal.SkeletalMaterial(
                    material_interface=mi,
                    material_slot_name=slot.get_editor_property("material_slot_name"),
                    uv_channel_data=slot.get_editor_property("uv_channel_data"),
                ))
                assigned_slots.append(index)
            mesh.set_editor_property("materials", new_materials)
            unreal.EditorAssetLibrary.save_loaded_asset(mesh, only_if_is_dirty=False)
        except Exception as exc:
            assigned_slots = []
            assignment_error = str(exc)
    result = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "ok": bool(mi and mesh and assigned_slots),
        "parent": MASTER,
        "instance": INSTANCE,
        "mesh": MESH,
        "assigned_slots": assigned_slots,
        "surface_features_disabled": ["gerstner_wpo", "screen_refraction", "shoreline_foam", "world_depth_fade"],
    }
    if "assignment_error" in locals():
        result["assignment_error"] = assignment_error
    REPORT.parent.mkdir(parents=True, exist_ok=True)
    REPORT.write_text(json.dumps(result, indent=2), encoding="utf-8")
    unreal.log("Melusina water hair setup: " + json.dumps(result, sort_keys=True))
    return result

if __name__ == "__main__":
    main()
