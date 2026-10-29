"""Fresh-load verifier for proving-preset MI families.

Run INSIDE the Unreal editor via Monolith editor_query(run_python, mode=execute_file):
    run_python execute_file Tools/masters_spine_fresh_load_check.py M_Water_Oceanology_Melodia

Reads Saved/Audit/MastersSpine_20261028/receipt_proving_presets_<key>.json, unloads
each authored MI package, reloads it from disk, and verifies:
  - parent still resolves to the expected master
  - override census (scalar/vector/texture counts) matches the authored receipt
Writes Saved/Audit/MastersSpine_20261028/fresh_load_check_<key>.json.
Read-only beyond load/unload of the lane's own instances; saves nothing.
"""
import json
import os
import sys
import unreal

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
OUTDIR = os.path.join(ROOT, "Saved", "Audit", "MastersSpine_20261028")

ARR_KINDS = (
    ("scalar_parameter_values", "scalar"),
    ("vector_parameter_values", "vector"),
    ("texture_parameter_values", "texture"),
)


def main():
    key = sys.argv[1] if len(sys.argv) > 1 else "M_Master_Toon_Character"
    receipt_path = os.path.join(OUTDIR, "receipt_proving_presets_%s.json" % key)
    if not os.path.isfile(receipt_path):
        print("NO_RECEIPT", receipt_path)
        sys.exit(1)
    with open(receipt_path) as fh:
        receipt = json.load(fh)

    master_tail = receipt["master_path"].split("/")[-1]
    out = {"schema": "melodia.proving_fresh_load_check.v1", "when": "2026-10-28",
           "master": key, "master_path": receipt["master_path"], "checks": []}

    for preset in receipt.get("presets", []):
        path = preset.get("package")
        name = preset.get("name")
        row = {"name": name, "package": path}
        if not path:
            row["status"] = "NO_PACKAGE_IN_RECEIPT"
            out["checks"].append(row)
            continue
        try:
            unreal.EditorAssetLibrary.unload_asset(path)
        except Exception as exc:
            row["unload_note"] = str(exc)[:120]
        mi = unreal.load_asset(path)
        if mi is None:
            row["status"] = "RELOAD_FAILED"
            out["checks"].append(row)
            continue
        row["class"] = str(mi.get_class().get_name())
        parent = None
        try:
            parent = mi.get_editor_property("parent")
        except Exception:
            pass
        row["parent"] = str(parent) if parent else None
        row["parent_ok"] = bool(row["parent"]) and master_tail in row["parent"]
        expected = {"scalar": 0, "vector": 0, "texture": 0}
        for ov in preset.get("overrides", {}).values():
            if isinstance(ov, dict) and ov.get("kind") in expected:
                expected[ov["kind"]] += 1
        got = {}
        for arr_key, kind in ARR_KINDS:
            try:
                got[kind] = len(mi.get_editor_property(arr_key))
            except Exception:
                got[kind] = "get_failed"
        row["expected_counts"] = expected
        row["got_counts"] = got
        row["census_ok"] = all(got.get(k) == v for k, v in expected.items())
        row["status"] = "ok" if (row["parent_ok"] and row["census_ok"]) else "MISMATCH"
        out["checks"].append(row)
        print("FRESH", name, "|", row["status"], "| parent_ok", row["parent_ok"],
              "| census", row["census_ok"], got)

    os.makedirs(OUTDIR, exist_ok=True)
    out_path = os.path.join(OUTDIR, "fresh_load_check_%s.json" % key)
    with open(out_path, "w") as fh:
        json.dump(out, fh, indent=1)
    ok = all(c.get("status") == "ok" for c in out["checks"])
    print("FRESH_LOAD_ALL_OK", ok)
    print("FRESH_LOAD_RECEIPT", out_path)


main()
