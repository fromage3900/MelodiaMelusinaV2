"""Apply the CANONICAL column scheme to all four Melodia masters.

Reads the scheme from master_column_scheme.py (single source of truth) and
assigns each parameter's Group + SortPriority so the material-instance editor
reads top-to-bottom by column. Metadata-only: does NOT touch graph topology.

Run in the UE editor (Monolith editor_query run_python):
  Content/Python/organize_masters.py
"""
from __future__ import annotations

import importlib
import json

import unreal

MASTERS = {
    "M_Master_Toon_Universal": "/Game/EnvSandbox/Materials/Masters/M_Master_Toon_Universal",
    "M_Master_Toon_Landscape_HeightBlend": "/Game/EnvSandbox/Materials/Masters/M_Master_Toon_Landscape_HeightBlend",
    "M_Master_Nikki": "/Game/EnvSandbox/Materials/Masters/M_Master_Nikki",
    "M_Master_Nikki_Landscape": "/Game/EnvSandbox/Materials/Masters/M_Master_Nikki_Landscape",
}


def organize_one(material_path: str, stem: str) -> dict:
    import master_column_scheme as scheme

    scheme = importlib.reload(scheme)
    meta = scheme.build_meta(scheme.groups_for(stem))

    if not unreal.EditorAssetLibrary.does_asset_exist(material_path):
        return {"asset": material_path, "error": "asset_missing"}
    material = unreal.load_asset(material_path)
    if material is None:
        return {"asset": material_path, "error": "load_failed"}

    seen: set[str] = set()
    set_count = 0
    unmapped: list[str] = []
    for expr in unreal.MaterialEditingLibrary.get_material_expressions(material) or []:
        pname = None
        for prop in ("parameter_name", "ParameterName"):
            try:
                raw = expr.get_editor_property(prop)
                if raw:
                    pname = str(raw)
                    break
            except Exception:
                continue
        if not pname:
            continue
        # Only parameter expressions participate in the instance editor. Skip
        # non-parameter nodes that happen to expose a name-like property
        # (LandscapeLayerSample reports its layer name, Custom nodes their
        # description, etc.) and MPC collection parameters (drive runtime
        # values, never instance-editable).
        cls = expr.get_class().get_name()
        if "Parameter" not in cls:
            continue
        if cls == "MaterialExpressionCollectionParameter":
            continue
        if pname == "None":
            continue
        seen.add(pname)
        entry = meta.get(pname)
        if not entry:
            unmapped.append(pname)
            continue
        group, prio = entry
        try:
            expr.set_editor_property("group", group)
            expr.set_editor_property("sort_priority", prio)
            set_count += 1
        except Exception as exc:
            unreal.log_warning(f"[organize_masters] {pname}: {exc}")

    unreal.MaterialEditingLibrary.recompile_material(material)
    unreal.EditorAssetLibrary.save_loaded_asset(material, only_if_is_dirty=False)
    mapped_missing = sorted(set(meta) - seen)
    unreal.log(f"[organize_masters] {stem}: grouped={set_count} unmapped={sorted(set(unmapped))} "
               f"mapped_but_absent={mapped_missing}")
    return {"asset": material_path, "grouped": set_count, "unmapped": sorted(set(unmapped)),
            "mapped_but_absent": mapped_missing}


def main() -> int:
    results = []
    for stem, path in MASTERS.items():
        try:
            results.append(organize_one(path, stem))
        except Exception as exc:  # noqa: BLE001
            unreal.log_error(f"[organize_masters] {stem}: {exc}")
            results.append({"asset": path, "error": str(exc)})
    print(f"ORGANIZE_MASTERS_RESULT {json.dumps(results, default=str)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
