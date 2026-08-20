"""Set material-type-appropriate PBR scalars on the shared FlatColors MIs.

The 37 shared flat MIs carry only BaseTint + TextureWeight=0. This pass gives
each material type proper roughness/metallic so surfaces read correctly under
the toon master (wood satin, metal glint, glass clear, water wet, fabric soft).

Run in the UE editor (Monolith run_python): tune_flat_materials.main()
Writes: Saved/Audit/flat_mi_tuning.json
"""
from __future__ import annotations

import json
from pathlib import Path

import unreal

FLAT_DIR = "/Game/EnvSandbox/Materials/Instances/Environment/FlatColors"
OUT = Path(__file__).resolve().parents[2] / "Saved" / "Audit" / "flat_mi_tuning.json"

MEL = unreal.MaterialEditingLibrary

# default values per material-name substring (first match wins, case-insensitive)
RULES = [
    ("glass",      {"Roughness": 0.08, "Metallic": 0.0}),
    ("water",      {"Roughness": 0.15, "Metallic": 0.0}),
    ("metal",      {"Roughness": 0.38, "Metallic": 0.55}),
    ("gold",       {"Roughness": 0.25, "Metallic": 0.9}),
    ("lamp",       {"Roughness": 0.4,  "Metallic": 0.0, "GlowIntensity": 0.5}),
    ("plant",      {"Roughness": 0.85, "Metallic": 0.0}),
    ("leaf",       {"Roughness": 0.75, "Metallic": 0.0}),
    ("grass",      {"Roughness": 0.9,  "Metallic": 0.0}),
    ("carpet",     {"Roughness": 0.92, "Metallic": 0.0}),
    ("wood",       {"Roughness": 0.72, "Metallic": 0.0}),
    ("dirt",       {"Roughness": 0.88, "Metallic": 0.0}),
    ("stone",      {"Roughness": 0.65, "Metallic": 0.0}),
    ("corn",       {"Roughness": 0.6,  "Metallic": 0.0}),
    ("fur",        {"Roughness": 0.95, "Metallic": 0.0}),
    ("_default",   {"Roughness": 0.75, "Metallic": 0.0}),
    ("color",      {"Roughness": 0.7,  "Metallic": 0.0}),
]


def rule_for(name):
    n = name.lower()
    for token, vals in RULES:
        if token in n:
            return vals
    return None


def main():
    if not unreal.EditorAssetLibrary.does_directory_exist(FLAT_DIR):
        print("[flat_tune] no FlatColors dir")
        return {"scanned": 0}
    assets = unreal.EditorAssetLibrary.list_assets(FLAT_DIR, recursive=False)
    rows = []
    changed = 0
    for path in assets:
        mi = unreal.load_asset(path)
        if mi is None:
            continue
        name = path.rsplit("/", 1)[-1]
        vals = rule_for(name)
        if vals is None:
            continue
        parent = mi.get_editor_property("parent")
        params = set()
        for p in (MEL.get_scalar_parameter_names(parent) or []):
            params.add(str(p))
        applied = {}
        for pname, pval in vals.items():
            if pname in params:
                cur = MEL.get_material_instance_scalar_parameter_value(mi, pname)
                if cur is not None and abs(float(cur) - pval) > 1e-4:
                    MEL.set_material_instance_scalar_parameter_value(mi, pname, pval)
                    applied[pname] = {"old": float(cur), "new": pval}
                    changed += 1
        if applied:
            unreal.EditorAssetLibrary.save_loaded_asset(mi)
            rows.append({"path": path, "rule": rule_for.__name__, "applied": applied})
    payload = {"generated": "2026-08-14", "scanned": len(assets), "changed_params": changed, "rows": rows}
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    unreal.log(f"[flat_tune] scanned={len(assets)} changed={changed}")
    return payload


if __name__ == "__main__":
    main()
