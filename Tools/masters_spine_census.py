"""Masters spine census - re-runnable canon evidence for the six production masters.

Run INSIDE the Unreal editor via Monolith editor_query(run_python, mode=execute_file):

    run_python execute_file Tools/masters_spine_census.py

Read-only: it loads the six spine masters and enumerates expressions; it touches nothing.

Emits (paths are repo-root-relative, recomputed from this script's location):
    Saved/Audit/MastersSpine_20261028/master_census.json
        full node census per master (class, position, parameter name/group/sort,
        texture defaults, comment text, collection-parameter sources)
    Saved/Audit/MastersSpine_20261028/group_allocation_source.json
        the grouping facts used by the layout/canon passes:
        ungrouped + non-numbered-group parameters, and the full numbered group -> names map

Anchors the canon spec specs/materials/master_spine_canon.v1.json.
"""
import gc
import json
import os
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

PROPS = (
    ("material_expression_editor_x", "x"),
    ("material_expression_editor_y", "y"),
    ("parameter_name", "p"),
    ("group", "g"),
    ("sort_priority", "sp"),
    ("desc", "d"),
)


def census(path):
    asset = unreal.load_asset(path)
    if asset is None:
        return {"error": "load_failed"}
    exprs = unreal.MaterialEditingLibrary.get_material_expressions(asset)
    rows = []
    for e in exprs:
        row = {"c": str(e.get_class().get_name()).replace("MaterialExpression", "")}
        for prop, key in PROPS:
            try:
                v = e.get_editor_property(prop)
                row[key] = str(v) if v is not None else None
            except Exception:
                pass
        try:
            t = e.get_editor_property("texture")
            row["tx"] = t.get_path_name() if t else None
        except Exception:
            pass
        if row["c"] == "Comment":
            try:
                row["t"] = str(e.get_editor_property("text"))
            except Exception:
                pass
        if row["c"] == "CollectionParameter":
            try:
                c = e.get_editor_property("collection")
                row["col"] = c.get_path_name() if c else None
            except Exception:
                pass
        rows.append(row)
    return {"expr_count": len(exprs), "rows": rows}


def main():
    mats = dict((k, census(v)) for k, v in SPINE.items())
    if not os.path.isdir(OUTDIR):
        os.makedirs(OUTDIR, exist_ok=True)
    with open(os.path.join(OUTDIR, "master_census.json"), "w") as f:
        json.dump(
            {"schema": "melodia.masters_spine_census.v1", "when": "2026-10-28", "mats": mats},
            f,
            indent=1,
        )
    alloc = {}
    for key, value in mats.items():
        if value.get("error"):
            alloc[key] = {"error": value["error"]}
            continue
        rows = value["rows"]
        ungrouped = [
            {k: r.get(k) for k in ("p", "g", "c", "d", "tx")}
            for r in rows
            if r.get("p") and r.get("g") in (None, "None")
        ]
        non_numbered = [
            {"p": r.get("p"), "g": str(r.get("g"))}
            for r in rows
            if r.get("p") and r.get("g") and "|" not in str(r.get("g"))
        ]
        numbered = {}
        for r in rows:
            g = str(r.get("g")) if r.get("g") else None
            if r.get("p") and g and "|" in g:
                numbered.setdefault(g, []).append(str(r.get("p")))
        alloc[key] = {
            "ungrouped": ungrouped,
            "non_numbered_groups": non_numbered,
            "numbered_groups": numbered,
        }
    with open(os.path.join(OUTDIR, "group_allocation_source.json"), "w") as f:
        json.dump(alloc, f, indent=1)
    for key, value in mats.items():
        print(" ", key, "->", value.get("expr_count", value.get("error")))
    print("WROTE master_census.json + group_allocation_source.json under", OUTDIR)
    del mats
    gc.collect()


main()
