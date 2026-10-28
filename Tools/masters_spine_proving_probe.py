"""Proving-preset probe for the masters spine - live evidence for the proving-preset MI thread.

Run INSIDE the Unreal editor via Monolith editor_query(run_python, mode=execute_file):

    run_python execute_file Tools/masters_spine_proving_probe.py M_Master_Toon_Character

Read-only: loads one spine master + the ToonProfiles preset folder; touches nothing.

Emits Saved/Audit/MastersSpine_20261028/proving_probe_<key>.json containing:
  - the master's live parameter rows (class, name, group, sort, defaults, slider range)
  - the ToonProfiles TP_* audit (class, parent chain, override counts) so preset
    authoring extends the existing lane instead of duplicating it.
"""
import json
import os
import sys
import unreal

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
OUTDIR = os.path.join(ROOT, "Saved", "Audit", "MastersSpine_20261028")

SPINE = {
    "M_Master_Nikki_Landscape": "/Game/EnvSandbox/Materials/Masters/M_Master_Nikki_Landscape",
    "M_Master_Nikki": "/Game/EnvSandbox/Materials/Masters/M_Master_Nikki",
    "M_Master_Toon_Universal": "/Game/EnvSandbox/Materials/Masters/M_Master_Toon_Universal",
    "M_Master_Toon_Character": "/Game/EnvSandbox/Materials/Masters/M_Master_Toon_Character",
    "M_Water_Oceanology_Melodia": "/Game/EnvSandbox/Materials/Masters/M_Water_Oceanology_Melodia",
    "M_Master_SDF_Toon": "/Game/EnvSandbox/Materials/Masters/SDF/M_Master_SDF_Toon",
}


def dump_master(path):
    asset = unreal.load_asset(path)
    if asset is None:
        return {"error": "load_failed", "path": path}
    exprs = unreal.MaterialEditingLibrary.get_material_expressions(asset)
    rows = []
    for e in exprs:
        cls = str(e.get_class().get_name())
        if "Parameter" not in cls:
            continue
        row = {"c": cls.replace("MaterialExpression", "")}
        for prop in ("parameter_name", "group", "sort_priority"):
            try:
                row[prop] = str(e.get_editor_property(prop))
            except Exception:
                pass
        if cls == "MaterialExpressionVectorParameter":
            try:
                v = e.get_editor_property("default_value")
                row["rgb"] = [round(v.r, 4), round(v.g, 4), round(v.b, 4), round(v.a, 4)]
            except Exception:
                pass
        elif cls in ("MaterialExpressionScalarParameter", "MaterialExpressionStaticSwitchParameter"):
            for prop in ("default_value", "slider_min", "slider_max"):
                try:
                    v = e.get_editor_property(prop)
                    if v is not None:
                        row[prop] = round(float(v), 4)
                except Exception:
                    pass
        elif "Texture" in cls:
            for prop in ("texture", "tmav"):
                try:
                    v = e.get_editor_property(prop)
                    if v is not None:
                        row["tex"] = str(v)
                        break
                except Exception:
                    pass
        rows.append(row)
    return {"path": path, "expr_count": len(exprs), "params": rows}


def dump_toon_profiles():
    ar = unreal.AssetRegistryHelpers.get_asset_registry()
    prof_dir = "/Game/EnvSandbox/Materials/ToonProfiles"
    assets = ar.get_assets_by_path(prof_dir, True, False)
    rows = []
    for a in assets:
        entry = {
            "name": str(a.asset_name),
            "class": str(a.asset_class_path.asset_name),
            "path": str(a.package_name),
        }
        obj = unreal.load_asset(str(a.package_name))
        if obj is not None and obj.get_class().get_name() == "MaterialInstanceConstant":
            try:
                parent = obj.get_editor_property("parent")
                entry["parent"] = str(parent) if parent else None
            except Exception:
                entry["parent"] = "get_failed"
            for arr_key, out_key in (
                ("scalar_parameter_values", "n_scalar"),
                ("vector_parameter_values", "n_vector"),
                ("texture_parameter_values", "n_texture"),
            ):
                try:
                    vals = obj.get_editor_property(arr_key)
                    entry[out_key] = len(vals)
                    if out_key == "n_scalar" and vals:
                        names = []
                        for x in vals:
                            try:
                                names.append(str(x.get_editor_property("parameter_name")))
                            except Exception:
                                names.append("?")
                        entry["scalar_names"] = names[:48]
                except Exception:
                    entry[out_key] = "get_failed"
        rows.append(entry)
    return sorted(rows, key=lambda r: r["name"])


def main():
    key = sys.argv[1] if len(sys.argv) > 1 else "M_Master_Toon_Character"
    out = {"probe": "masters_spine_proving_probe.v1", "master": key,
           "master_rows": dump_master(SPINE.get(key, key)),
           "toon_profiles": dump_toon_profiles()}
    os.makedirs(OUTDIR, exist_ok=True)
    with open(os.path.join(OUTDIR, "proving_probe_%s.json" % key), "w") as fh:
        json.dump(out, fh, indent=1)
    m = out["master_rows"]
    if m.get("error"):
        print("MASTER_ERROR", json.dumps(m))
    else:
        print("MASTER", m["path"], "exprs", m["expr_count"], "params", len(m["params"]))
        for r in m["params"]:
            print("  P", r.get("c"), "|", r.get("parameter_name"), "|", r.get("group"), "|",
                  r.get("rgb") or r.get("default_value") or "", r.get("tex")[:40] if r.get("tex") else "")
    print("TOON_PROFILES", len(out["toon_profiles"]))
    for r in out["toon_profiles"]:
        print("  TP", r["name"], "|", r["class"], "| parent:", r.get("parent"),
              "| ov s/v/t:", r.get("n_scalar"), r.get("n_vector"), r.get("n_texture"))


main()
