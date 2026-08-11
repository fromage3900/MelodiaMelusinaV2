"""Create safe NikkiHero mapping copies for the integrated Universal family.

Existing NikkiHero instances and their scratch/canonical parents remain
untouched.  The copies preserve only overrides that exist on the integrated
master, translate the legacy iridescence/sheen names into the new chain's
explicit controls, and record every skipped field for human review.
"""
from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

import unreal


PARENT = "/Game/EnvSandbox/Materials/Masters/M_Master_Toon_Universal_NikkiChainIntegratedV1"
SOURCE_DIR = "/Game/EnvSandbox/Materials/Instances/NikkiHero"
TARGET_DIR = "/Game/EnvSandbox/Materials/Instances/NikkiIntegrated/Mapped"
REPORT = Path(unreal.Paths.project_saved_dir()) / "Audit" / "nikki_integrated_mapped_family.json"
NAMES = (
    "MI_NikkiHero_BioGrotto",
    "MI_NikkiHero_SakuraDream",
    "MI_NikkiHero_CosmicOrrery",
    "MI_NikkiHero_SpaceCathedral",
    "MI_NikkiHero_BaroqueCastle",
)
TRANSLATIONS = {
    "Iridescence": "NikkiIridescence",
    "IridescencePower": "NikkiIridescencePower",
    "FabricSheen": "NikkiFabricSheen",
    "SheenTint": "NikkiSheenTint",
}
SPARKLE_INTENSITIES = {
    "MI_NikkiHero_BioGrotto": 0.38,
    "MI_NikkiHero_SakuraDream": 0.55,
    "MI_NikkiHero_CosmicOrrery": 0.72,
    "MI_NikkiHero_SpaceCathedral": 0.64,
    "MI_NikkiHero_BaroqueCastle": 0.25,
}
RIM_COLORS = {
    "MI_NikkiHero_BioGrotto": (0.34, 0.95, 0.78, 1.0),
    "MI_NikkiHero_SakuraDream": (1.0, 0.68, 0.88, 1.0),
    "MI_NikkiHero_CosmicOrrery": (0.62, 0.48, 1.0, 1.0),
    "MI_NikkiHero_SpaceCathedral": (0.52, 0.80, 1.0, 1.0),
    "MI_NikkiHero_BaroqueCastle": (1.0, 0.70, 0.34, 1.0),
}


def _path(asset) -> str:
    if not asset:
        return ""
    try:
        return asset.get_path_name().split(".", 1)[0]
    except Exception:
        return ""


def _parameter_names(material):
    names = {"scalar": set(), "vector": set(), "texture": set()}
    for expression in unreal.MaterialEditingLibrary.get_material_expressions(material) or []:
        class_name = expression.get_class().get_name()
        try:
            parameter_name = str(expression.get_editor_property("parameter_name"))
        except Exception:
            continue
        if class_name == "MaterialExpressionScalarParameter":
            names["scalar"].add(parameter_name)
        elif class_name == "MaterialExpressionVectorParameter":
            names["vector"].add(parameter_name)
        elif "Texture" in class_name and "Parameter" in class_name:
            names["texture"].add(parameter_name)
    return names


def _source_overrides(instance):
    result = {"scalar": {}, "vector": {}, "texture": {}}
    for entry in instance.get_editor_property("scalar_parameter_values") or []:
        info = entry.get_editor_property("parameter_info")
        result["scalar"][str(info.get_editor_property("name"))] = float(
            entry.get_editor_property("parameter_value")
        )
    for entry in instance.get_editor_property("vector_parameter_values") or []:
        info = entry.get_editor_property("parameter_info")
        result["vector"][str(info.get_editor_property("name"))] = entry.get_editor_property(
            "parameter_value"
        )
    for entry in instance.get_editor_property("texture_parameter_values") or []:
        info = entry.get_editor_property("parameter_info")
        result["texture"][str(info.get_editor_property("name"))] = entry.get_editor_property(
            "parameter_value"
        )
    return result


def _create_or_load(name: str):
    path = f"{TARGET_DIR}/{name}"
    instance = unreal.load_asset(path)
    created = False
    if not instance:
        tools = unreal.AssetToolsHelpers.get_asset_tools()
        instance = tools.create_asset(
            name,
            TARGET_DIR,
            unreal.MaterialInstanceConstant,
            unreal.MaterialInstanceConstantFactoryNew(),
        )
        created = True
    if not instance:
        raise RuntimeError(f"Could not create mapped instance: {path}")
    return instance, created, path


def main() -> dict:
    parent = unreal.load_asset(PARENT)
    if not parent:
        raise RuntimeError(f"Missing integrated Nikki parent: {PARENT}")
    if not unreal.EditorAssetLibrary.does_directory_exist(TARGET_DIR):
        unreal.EditorAssetLibrary.make_directory(TARGET_DIR)
    available = _parameter_names(parent)
    rows = []

    for source_name in NAMES:
        source_path = f"{SOURCE_DIR}/{source_name}"
        source = unreal.load_asset(source_path)
        if not source:
            rows.append({"source": source_path, "status": "missing"})
            continue
        target_name = f"{source_name}_IntegratedV1"
        target, created, target_path = _create_or_load(target_name)
        unreal.MaterialEditingLibrary.set_material_instance_parent(target, parent)
        unreal.MaterialEditingLibrary.set_material_instance_static_switch_parameter_value(
            target, "bNikkiHero", True
        )
        source_values = _source_overrides(source)
        applied = {"scalar": [], "vector": [], "texture": []}
        skipped = {"scalar": [], "vector": [], "texture": []}

        for kind in ("scalar", "vector", "texture"):
            for source_parameter, value in source_values[kind].items():
                destination_parameter = TRANSLATIONS.get(source_parameter, source_parameter)
                if destination_parameter not in available[kind]:
                    skipped[kind].append(source_parameter)
                    continue
                if kind == "scalar":
                    unreal.MaterialEditingLibrary.set_material_instance_scalar_parameter_value(
                        target, destination_parameter, float(value)
                    )
                elif kind == "vector":
                    unreal.MaterialEditingLibrary.set_material_instance_vector_parameter_value(
                        target, destination_parameter, value
                    )
                else:
                    unreal.MaterialEditingLibrary.set_material_instance_texture_parameter_value(
                        target, destination_parameter, value
                    )
                applied[kind].append({"source": source_parameter, "destination": destination_parameter})

        if "NikkiSparkleIntensity" in available["scalar"]:
            unreal.MaterialEditingLibrary.set_material_instance_scalar_parameter_value(
                target, "NikkiSparkleIntensity", SPARKLE_INTENSITIES[source_name]
            )
            applied["scalar"].append({"source": "profile", "destination": "NikkiSparkleIntensity"})
        if "NikkiRimColor" in available["vector"]:
            unreal.MaterialEditingLibrary.set_material_instance_vector_parameter_value(
                target, "NikkiRimColor", unreal.LinearColor(*RIM_COLORS[source_name])
            )
            applied["vector"].append({"source": "profile", "destination": "NikkiRimColor"})
        unreal.EditorAssetLibrary.save_loaded_asset(target)
        rows.append(
            {
                "source": source_path,
                "target": target_path,
                "created_this_run": created,
                "parent": _path(target.get_editor_property("parent")),
                "applied": applied,
                "skipped": skipped,
            }
        )

    report = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "parent": PARENT,
        "source_dir": SOURCE_DIR,
        "target_dir": TARGET_DIR,
        "rows": rows,
        "existing_instances_reparented": False,
        "ok": bool(rows) and all(row.get("parent") == PARENT for row in rows if row.get("target")),
    }
    REPORT.parent.mkdir(parents=True, exist_ok=True)
    REPORT.write_text(json.dumps(report, indent=2, default=str), encoding="utf-8")
    unreal.log(f"[NikkiMappedFamily] {json.dumps(report, default=str)}")
    print(json.dumps(report, indent=2, default=str))
    return report


if __name__ == "__main__":
    main()
