"""Read-only probe of the material surface for Atlantis MI authoring (2026-08-17).

Answers, for M_Master_Toon_Universal, M_Water_Master_Grand_v10_Upgrade,
M_ToonFoliage, and a sample of Atlantis meshes:
  - blend mode / two-sided / shading model
  - full texture-parameter, scalar-parameter, switch-parameter inventories
  - Substrate Toon BSDF node class + input-ish property names (opacity/alpha/blend)
  - what (if anything) feeds the material's Opacity / OpacityMask inputs
  - Atlantis mesh material slot names (for crosswalk matching)

Run inside the live editor via Monolith run_python. Read-only; saves nothing.
"""
from __future__ import annotations

import json
from pathlib import Path

import unreal

REPORT = Path(__file__).resolve().parents[2] / "Saved" / "Audit" / "atlantis_material_surface_probe.json"

MASTERS = {
    "toon_universal": "/Game/EnvSandbox/Materials/Masters/M_Master_Toon_Universal",
    "water_v10": "/Game/EnvSandbox/Materials/Masters/M_Water_Master_Grand_v10_Upgrade",
    "toon_foliage": "/Game/EnvSandbox/Materials/Masters/M_ToonFoliage",
}
MESH_ROOT = "/Game/EnvSandbox/Meshes/Atlantis"


def param_inventory(mat: unreal.Material) -> dict:
    out = {"textures": [], "scalars": [], "switches": [], "vectors": []}
    try:
        for pv in mat.get_editor_property("texture_parameter_values") or []:
            out["textures"].append(str(pv.get_editor_property("parameter_name")))
    except Exception:
        pass
    try:
        for pv in mat.get_editor_property("scalar_parameter_values") or []:
            out["scalars"].append(str(pv.get_editor_property("parameter_name")))
    except Exception:
        pass
    try:
        for pv in mat.get_editor_property("static_switch_parameter_values") or []:
            out["switches"].append(str(pv.get_editor_property("parameter_name")))
    except Exception:
        pass
    try:
        for pv in mat.get_editor_property("vector_parameter_values") or []:
            out["vectors"].append(str(pv.get_editor_property("parameter_name")))
    except Exception:
        pass
    for key in out:
        out[key].sort()
    return out


def bsdf_opacity_surface(mat: unreal.Material) -> dict:
    """Find SubstrateToonBSDF expressions and any opacity/alpha/blend-flavoured props."""
    found = []
    try:
        for e in unreal.MaterialEditingLibrary.get_material_expressions(mat) or []:
            cls = e.get_class().get_name()
            if "BSDF" not in cls and "Substrate" not in cls:
                continue
            props = []
            for name in dir(e):
                if any(t in name.lower() for t in ("opacity", "alpha", "blend", "surface")):
                    props.append(name)
            found.append({"class": cls, "name": e.get_name(), "interesting_props": sorted(props)})
    except Exception as exc:
        found.append({"error": str(exc)})
    return found


def opacity_input_state(mat: unreal.Material) -> dict:
    """What expression feeds MP_OPACITY / MP_OPACITY_MASK (by class + name)."""
    state = {}
    try:
        for prop, label in (
            (unreal.MaterialProperty.MP_OPACITY, "opacity"),
            (unreal.MaterialProperty.MP_OPACITY_MASK, "opacity_mask"),
        ):
            try:
                expr = unreal.MaterialEditingLibrary.get_material_property_input_node(mat, prop)
                state[label] = None if expr is None else {
                    "class": expr.get_class().get_name(), "name": expr.get_name(),
                }
            except Exception:
                state[label] = "unavailable"
    except Exception as exc:
        state["error"] = str(exc)
    return state


def mesh_slots_sample(count: int = 8) -> list[dict]:
    assets = unreal.EditorAssetLibrary.list_assets(MESH_ROOT)
    picked = assets[:count]
    rows = []
    for path in picked:
        sm = unreal.EditorAssetLibrary.load_asset(path)
        if not sm:
            rows.append({"mesh": path, "error": "load failed"})
            continue
        try:
            mats = [str(m.get_editor_property("material_slot_name")) for m in sm.get_editor_property("static_materials") or []]
            rows.append({"mesh": path, "slots": mats, "slot_count": len(mats)})
        except Exception as exc:
            rows.append({"mesh": path, "error": str(exc)})
    return rows


def main() -> int:
    report = {"masters": {}, "mesh_sample": []}
    for key, path in MASTERS.items():
        entry = {"path": path, "exists": unreal.EditorAssetLibrary.does_asset_exist(path)}
        if entry["exists"]:
            mat = unreal.EditorAssetLibrary.load_asset(path)
            if mat:
                entry.update({
                    "blend_mode": str(mat.get_editor_property("blend_mode")),
                    "two_sided": bool(mat.get_editor_property("two_sided")),
                    "shading_model": str(mat.get_editor_property("shading_model")),
                    "params": param_inventory(mat),
                    "bsdf": bsdf_opacity_surface(mat),
                    "opacity_inputs": opacity_input_state(mat),
                })
        report["masters"][key] = entry
    report["mesh_sample"] = mesh_slots_sample()
    REPORT.parent.mkdir(parents=True, exist_ok=True)
    REPORT.write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(json.dumps(report, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())