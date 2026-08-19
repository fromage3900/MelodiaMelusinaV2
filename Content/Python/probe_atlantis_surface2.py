"""Probe 2 (2026-08-17): expression-level parameter inventory of masters +
real instance override arrays as wiring templates.

Substrate masters do NOT populate material.texture_parameter_values (probe 1
showed empty arrays) — parameters are graph expressions. This probe reads them
from expressions and reads override arrays from live instances (which DO
populate them), giving exact slot names for Atlantis MI authoring.

Read-only. Manifest: Saved/Audit/atlantis_surface_probe2.json
"""
from __future__ import annotations

import json
from pathlib import Path

import unreal

REPORT = Path(__file__).resolve().parents[2] / "Saved" / "Audit" / "atlantis_surface_probe2.json"

MASTERS = {
    "toon_universal": "/Game/EnvSandbox/Materials/Masters/M_Master_Toon_Universal",
    "water_v10": "/Game/EnvSandbox/Materials/Masters/M_Water_Master_Grand_v10_Upgrade",
    "toon_foliage": "/Game/EnvSandbox/Materials/Masters/M_ToonFoliage",
}
INSTANCES = {
    "toon_sample": "/Game/EnvSandbox/Materials/Instances/Environment/MI_Show_Default",
    "water_v10_sample": "/Game/EnvSandbox/Materials/Instances/Water/v10/MI_WaterV10_Integrated_OceanDeep",
    "toon_foliage_sample": "/Game/EnvSandbox/Materials/Instances/Environment/MI_ExperimentalGrassCard",
}


def expression_params(mat: unreal.Material) -> dict:
    """{kind: {parameter_name: class}} from graph expressions."""
    out: dict = {"textures": {}, "scalars": {}, "switches": {}, "vectors": {}}
    try:
        for e in unreal.MaterialEditingLibrary.get_material_expressions(mat) or []:
            cls = type(e).__name__
            try:
                pname = str(e.get_editor_property("parameter_name"))
            except Exception:
                continue
            if not pname:
                continue
            if "Texture" in cls and "Parameter" in cls:
                out["textures"][pname] = cls
            elif "ScalarParameter" in cls:
                out["scalars"][pname] = cls
            elif "StaticSwitchParameter" in cls or "StaticBoolParameter" in cls:
                out["switches"][pname] = cls
            elif "VectorParameter" in cls:
                out["vectors"][pname] = cls
    except Exception as exc:
        out["error"] = str(exc)
    for kind in out:
        if isinstance(out[kind], dict):
            out[kind] = dict(sorted(out[kind].items()))
    return out


def instance_arrays(mi_path: str) -> dict:
    mi = unreal.EditorAssetLibrary.load_asset(mi_path)
    if not mi:
        return {"path": mi_path, "error": "load failed"}
    out = {"path": mi_path, "parent": str(mi.get_editor_property("parent"))}
    for prop, key in (
        ("texture_parameter_values", "textures"),
        ("scalar_parameter_values", "scalars"),
        ("static_switch_parameter_values", "switches"),
        ("vector_parameter_values", "vectors"),
    ):
        try:
            out[key] = sorted(str(p.get_editor_property("parameter_name"))
                              for p in mi.get_editor_property(prop) or [])
        except Exception as exc:
            out[key] = f"error: {exc}"
    return out


def main() -> int:
    report = {"masters": {}, "instances": {}}
    for key, path in MASTERS.items():
        mat = unreal.EditorAssetLibrary.load_asset(path)
        report["masters"][key] = {
            "path": path,
            "exists": bool(mat),
            "params": expression_params(mat) if mat else {},
        }
    for key, path in INSTANCES.items():
        report["instances"][key] = instance_arrays(path)
    REPORT.parent.mkdir(parents=True, exist_ok=True)
    REPORT.write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(json.dumps(report, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())