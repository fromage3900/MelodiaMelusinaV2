"""Choral Sheep flock batch import (run-once, NOT a startup hook).

Run at the next editor launch via RiderLink ue_execute_python (file mode) or
the editor Python console:
    <repo>/Content/Python/import_sheep_flock_batch.py

Reads the flock manifest + texture manifests, imports the 34 flock textures
idempotently (replace_existing), enforces per-type compression/sRGB, verifies
the 12 coat MIs, and writes a receipt + the per-variant assignment spec.
Never touches Content outside the flock texture folders; never saves other
packages; never hooks init_unreal (deliberate: imports stay explicit).

Phase 1: textures — 14 Chladni masks + 20 Copernicus wool maps.
Phase 2: coat MIs — verify all 12 exist, record parent + texture params, emit
  the assignment spec. No MI writes: parameter names are confirmed live first
  (one reflection pass), then assignment follows in a later run.
"""
import json
import os

import unreal

REPO = "C:/EnvironmentPortfolio/BS_GodFile"
LANE = "G:/BS_GodFile_Saved_Audit_20261009/choral_sheep/flock_20261010"
FLOCK = LANE + "/sheep_flock_20261010.json"
RECEIPT = LANE + "/sheep_flock_import_20261010.json"
TEX_WOOL = "/Game/Melodia/Companions/ChoralSheep/Textures/Flock/Wool"
TEX_CHLADNI = "/Game/Melodia/Companions/ChoralSheep/Textures/Flock/Chladni"
FLAT_SRC_DIR = "G:/BS_GodFile_Saved_Audit_20261009/choral_sheep/albedo_A_flat"
PC_VERIFY = ["/Game/Melodia/Companions/ChoralSheep/Textures/T_Chladni_C_ROOT"] + \
    ["/Game/Melodia/Companions/ChoralSheep/Textures/Chladni/T_Chladni_%s_ROOT" % s
     for s in ("CE", "CEG")] + \
    ["/Game/Melodia/Companions/ChoralSheep/Textures/Chladni/T_Chladni_PC_%s" % s
     for s in ("A", "As", "B", "C", "Cs", "D", "Ds", "E", "F", "Fs", "G", "Gs")]

MAP_SETTINGS = {
    "BaseColor": {"srgb": True, "compression": None},
    "Normal": {"srgb": False, "compression": "TC_Normalmap"},
    "ORM": {"srgb": False, "compression": "TC_Masks"},
    "Height": {"srgb": False, "compression": "TC_Masks"},
    "Mask": {"srgb": False, "compression": None},
}


def map_type_of(filename):
    for key in ("BaseColor", "Normal", "ORM", "Height"):
        if "_%s." % key in filename:
            return key
    if filename.endswith("_Mask.png"):
        return "Mask"
    if filename.startswith("ChoralWool_PC_"):
        return "BaseColor"
    return None


def import_texture(src_path, dest_dir, dest_name, map_type):
    rep = {"file": os.path.basename(src_path), "ok": False}
    try:
        task = unreal.AssetImportTask()
        task.filename = src_path
        task.destination_path = dest_dir
        task.destination_name = dest_name
        task.automated = True
        task.save = False
        task.replace_existing = True
        unreal.AssetToolsHelpers.get_asset_tools().import_asset_tasks([task])
        paths = task.imported_object_paths
        if not paths:
            rep["error"] = "import_returned_no_paths"
            return rep
        tex = unreal.load_asset(paths[0])
        if tex is None:
            rep["error"] = "load_failed"
            return rep
        st = MAP_SETTINGS[map_type]
        if st["compression"]:
            tex.set_editor_property(
                "compression_settings",
                getattr(unreal.TextureCompressionSettings, st["compression"]))
        tex.set_editor_property("srgb", st["srgb"])
        unreal.EditorAssetLibrary.save_loaded_asset(tex)
        rep["ok"] = True
        rep["asset"] = dest = "%s/%s" % (dest_dir, dest_name)
    except Exception as exc:
        rep["error"] = str(exc)[:300]
    return rep


def verify_assets(paths):
    out = []
    for p in paths:
        try:
            out.append({"asset": p, "exists": bool(
                unreal.EditorAssetLibrary.find_asset_data(p).is_valid())})
        except Exception as exc:
            out.append({"asset": p, "exists": "error",
                        "error": str(exc)[:200]})
    return out


def verify_coats(variants):
    out = []
    for v in variants:
        path = v["coat_mi"]
        try:
            data = unreal.EditorAssetLibrary.find_asset_data(path)
            if not data.is_valid():
                out.append({"mi": path, "exists": False})
                continue
            mi = unreal.load_asset(path)
            parent = mi.get_editor_property("parent")
            entry = {
                "mi": path,
                "exists": True,
                "parent": (parent.get_path_name().split(".")[0]
                           if parent else None),
                "assign_weave": v["weave_files"],
                "assign_chladni": v["chladni"]["png"],
            }
            try:
                names = unreal.MaterialEditingLibrary.get_texture_parameter_names(mi)
                entry["texture_params"] = [str(n) for n in (names or [])]
            except Exception as exc:
                entry["texture_params_error"] = str(exc)[:200]
            out.append(entry)
        except Exception as exc:
            out.append({"mi": path, "exists": "error",
                        "error": str(exc)[:200]})
    return out


def main():
    flock = json.load(open(FLOCK, encoding="utf-8"))
    try:
        off = int(os.environ.get("FLOCK_OFFSET", "0") or 0)
    except Exception:
        off = 0
    try:
        lim = int(os.environ.get("FLOCK_LIMIT", "0") or 0)
    except Exception:
        lim = 0
    unreal.EditorAssetLibrary.make_directory(TEX_WOOL)
    unreal.EditorAssetLibrary.make_directory(TEX_CHLADNI)
    seen = set()
    jobs = []
    for v in flock["variants"]:
        for fn in v["weave_files"]:
            key = ("wool", fn)
            if key not in seen:
                seen.add(key)
                jobs.append((REPO + "/Saved/GeneratedTextures/Copernicus/" + fn,
                             TEX_WOOL, os.path.splitext(fn)[0]))
        fn = v["chladni"]["png"]
        key = ("chladni", fn)
        if key not in seen:
            seen.add(key)
            jobs.append((REPO + "/Saved/GeneratedTextures/Chladni/" + fn,
                         TEX_CHLADNI, os.path.splitext(fn)[0]))
        fn = v.get("pitch_albedo")
        if fn:
            key = ("flat", fn)
            if key not in seen:
                seen.add(key)
                jobs.append((FLAT_SRC_DIR + "/" + fn,
                             TEX_WOOL, os.path.splitext(fn)[0]))
    if lim:
        jobs = jobs[off:off + lim]
    elif off:
        jobs = jobs[off:]
    print("batch window offset=%d limit=%d jobs=%d" % (off, lim, len(jobs)),
          flush=True)
    results = []
    for src, dest_dir, dest_name in jobs:
        mt = map_type_of(os.path.basename(src))
        if mt is None or not os.path.isfile(src):
            results.append({"file": os.path.basename(src), "ok": False,
                            "error": "unknown_map_type_or_missing"})
            continue
        r = import_texture(src, dest_dir, dest_name, mt)
        results.append(r)
        print("  %s: %s" % (dest_name, "OK" if r["ok"] else r.get("error", "FAIL")),
              flush=True)
    coats = verify_coats(flock["variants"])
    pc = verify_assets(PC_VERIFY)
    payload = {"schema": "melodia.sheep_flock_import.v1",
               "textures_ok": sum(1 for r in results if r.get("ok")),
               "textures_total": len(results),
               "textures": results,
               "coats": coats,
               "pc_textures": pc,
               "not_proven": ("MI texture assignment needs one live reflection "
                              "pass over coat parent params; see assign_* spec above.")}
    with open(RECEIPT, "w", encoding="utf-8") as f:
        json.dump(payload, f, indent=1)
    print("__SHEEP_FLOCK_IMPORT__" + json.dumps(
        {"textures_ok": payload["textures_ok"],
         "textures_total": payload["textures_total"],
         "coats_found": sum(1 for c in coats if c.get("exists") is True),
         "pc_found": sum(1 for p in pc if p.get("exists") is True),
         "pc_total": len(pc)}))
    return payload


if __name__ == "__main__":
    main()
