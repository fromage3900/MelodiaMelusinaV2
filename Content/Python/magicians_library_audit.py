"""magicians_library_audit.py — READ-ONLY audit of the Magician's Library mesh trees.

Answers the owner's four questions, per mesh:
  1. imported    — does the SM load, does it have material slots + assigned materials,
                    does it have collision, how many LODs
  2. organized   — SM_ prefix, folder-per-prop naming, stray "_Loose" subfolders,
                    leftover source suffixes (Object1715, candle1_L, ...)
  3. MI coverage — is there a proper material instance for the mesh, and is it assigned
  4. toon master — does the assigned material's parent chain resolve to the Universal
                    toon master (M_Master_Toon_Universal)?

MUTATES NOTHING. Writes Saved/Audit/magicians_library_audit.json only.

Run: Monolith editor_query run_python (execute_file) with this path.
"""
from __future__ import annotations

import json
import re
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path

import unreal

PROJECT_ROOT = Path(__file__).resolve().parents[2]
REPORT = PROJECT_ROOT / "Saved" / "Audit" / "magicians_library_audit.json"

ROOTS = {
    "envsandbox_canonical": "/Game/EnvSandbox/Library/Migrated/MagiciansLibrary",
    "library_duplicate": "/Game/Library/Migrated/MagiciansLibrary",
    "archive_source": "/Game/00_Archive/MagicianLabSource_2026-08-31",
}

# The Universal toon master, per Docs/Production/MATERIAL_MASTER_RECONCILIATION.md
UNIVERSAL_TOON = "/Game/EnvSandbox/Materials/Masters/M_Master_Toon_Universal"
TOON_MASTER_RE = re.compile(r"^/Game/.*/M_(Master_)?Toon")
NIKKI_PARAMS = {"BaseTint", "TintStrength"}


def _p(obj) -> str:
    try:
        return obj.get_path_name()
    except Exception:
        return ""


def parent_chain(mat, depth: int = 0):
    """Walk MaterialInstance -> parent chain. Returns list of object paths."""
    chain = []
    seen = set()
    cur = mat
    while cur is not None and depth < 16:
        p = _p(cur)
        if not p or p in seen:
            break
        seen.add(p)
        chain.append(p)
        if isinstance(cur, unreal.MaterialInstanceConstant):
            try:
                cur = cur.get_editor_property("parent")
            except Exception:
                cur = None
        else:
            cur = None
        depth += 1
    return chain


def classify_material(mat):
    """-> (kind, chain, resolves_to_universal, root_kind)"""
    if mat is None:
        return ("none", [], False, "none")
    chain = parent_chain(mat)
    root = chain[-1] if chain else ""
    if isinstance(mat, unreal.MaterialInstanceConstant):
        kind = "instance"
    elif isinstance(mat, unreal.Material):
        kind = "master"
    else:
        kind = "other:" + type(mat).__name__
    resolves = any(c.split(".")[0] == UNIVERSAL_TOON for c in chain)
    return (kind, chain, resolves, root)


def master_graph_shape(mat):
    """Is this master a flat standalone converted graph, or a re-parented master?"""
    info = {"expr_count": None, "has_toon_bsdf": None, "has_basecolor_param": None}
    try:
        mel = unreal.MaterialEditingLibrary
        exprs = list(mel.get_material_expressions(mat) or [])
        info["expr_count"] = len(exprs)
        names = []
        for e in exprs:
            try:
                n = e.get_editor_property("parameter_name")
                names.append(str(n))
            except Exception:
                pass
            if "SubstrateToonBSDF" in type(e).__name__:
                info["has_toon_bsdf"] = True
            if type(e).__name__ == "MaterialExpressionTextureSampleParameter2D":
                tex = ""
                try:
                    tex = str(e.get_editor_property("parameter_name"))
                except Exception:
                    pass
                if tex:
                    names.append(tex)
        info["has_basecolor_param"] = any("BaseColor" in n for n in names)
    except Exception as ex:
        info["error"] = str(ex)
    return info


def mesh_info(sm):
    info = {"slots": [], "lod_count": None, "has_collision": None, "collision_flag": None}
    try:
        slots = list(sm.get_editor_property("static_materials") or [])
        for i, s in enumerate(slots):
            try:
                mi = s.get_editor_property("material_interface")
            except Exception:
                mi = None
            try:
                slot_name = str(s.get_editor_property("material_slot_name"))
            except Exception:
                slot_name = "slot%d" % i
            kind, chain, resolves, root = classify_material(mi)
            info["slots"].append({
                "i": i,
                "slot_name": slot_name,
                "material": _p(mi) if mi else None,
                "material_kind": kind,
                "chain": chain,
                "resolves_to_universal_toon": resolves,
                "root": root,
            })
    except Exception as ex:
        info["slots_error"] = str(ex)
    try:
        info["lod_count"] = sm.get_num_lods()
    except Exception:
        try:
            info["lod_count"] = len(sm.get_editor_property("lod_for_render") or [])
        except Exception:
            pass
    try:
        bs = sm.get_editor_property("body_setup")
        info["has_collision"] = bs is not None
        if bs is not None:
            try:
                agg = bs.get_editor_property("agg_geom")
                info["collision_flag"] = str(agg.get_editor_property("collision_trace_flag"))
                info["collision_prims"] = len(list(agg.get_editor_property("simple_collision_shape") or []))
            except Exception:
                pass
    except Exception:
        info["has_collision"] = None
    return info


def mi_info(mi):
    info = {}
    try:
        parent = mi.get_editor_property("parent")
        info["parent"] = _p(parent) if parent else None
    except Exception:
        info["parent"] = None
    for prop, key in (("toon_profile", "toon_profile"),
                      ("override_toon_profile", "override_toon_profile")):
        try:
            v = mi.get_editor_property(prop)
            info[key] = _p(v) if hasattr(v, "get_path_name") else v
        except Exception:
            info[key] = None
    vec = []
    scl = []
    try:
        for p in mi.get_editor_property("vector_parameter_values") or []:
            vec.append(str(p.get_editor_property("parameter_name")))
    except Exception:
        pass
    try:
        for p in mi.get_editor_property("scalar_parameter_values") or []:
            scl.append(str(p.get_editor_property("parameter_name")))
    except Exception:
        pass
    info["vector_params"] = sorted(vec)
    info["scalar_params"] = sorted(scl)
    info["nikki_params"] = sorted(set(vec) & NIKKI_PARAMS) + sorted(set(scl) & NIKKI_PARAMS)
    return info


def referenced_by(path):
    try:
        refs = unreal.EditorAssetLibrary.find_package_referencers_for_asset(path, False)
        return sorted(r for r in (refs or []) if not r.startswith("/Temp") and "MagiciansLibrary" not in r)
    except Exception:
        return None


def main() -> int:
    out = {
        "generated": datetime.now(timezone.utc).isoformat(),
        "universal_toon_master": UNIVERSAL_TOON,
        "roots": {},
    }
    summary = {}
    for key, root in ROOTS.items():
        if not unreal.EditorAssetLibrary.does_directory_exist(root):
            out["roots"][key] = {"exists": False}
            continue
        paths = unreal.EditorAssetLibrary.list_assets(root, recursive=True, include_folder=False)
        rows = {"exists": True, "root": root, "asset_count": len(paths), "meshes": [],
                "materials": [], "textures": [], "other": []}
        for p in paths:
            base = p.rsplit("/", 1)[-1].rsplit(".", 1)[0]
            folder = "/".join(p.split("/")[:-1])
            try:
                asset = unreal.load_asset(p)
            except Exception:
                asset = None
            if asset is None:
                rows["other"].append({"name": base, "path": p, "folder": folder, "load": "FAILED"})
                continue
            if isinstance(asset, unreal.StaticMesh):
                mi = mesh_info(asset)
                mi.update({"name": base, "path": p, "folder": folder,
                           "referenced_by": referenced_by(p)})
                rows["meshes"].append(mi)
            elif isinstance(asset, unreal.MaterialInstanceConstant):
                d = mi_info(asset)
                d.update({"name": base, "path": p, "folder": folder,
                          "referenced_by": referenced_by(p)})
                rows["materials"].append(d)
            elif isinstance(asset, unreal.Material):
                d = {"name": base, "path": p, "folder": folder,
                     "shape": master_graph_shape(asset), "referenced_by": referenced_by(p)}
                rows["materials"].append(d)
            elif isinstance(asset, unreal.Texture2D):
                rows["textures"].append({"name": base, "path": p, "folder": folder,
                                         "referenced_by": referenced_by(p)})
            else:
                rows["other"].append({"name": base, "path": p, "folder": folder,
                                      "class": type(asset).__name__})

        # ---- per-mesh verdicts
        verdicts = Counter()
        detail = []
        for m in rows["meshes"]:
            slots = m["slots"]
            assigned = [s for s in slots if s["material"]]
            mats = set(s["material"] for s in assigned)
            kinds = set(s["material_kind"] for s in assigned)
            uni = all(s["resolves_to_universal_toon"] for s in assigned) if assigned else False
            has_mi = any(s["material_kind"] == "instance" for s in assigned)
            naming_ok = bool(re.match(r"^SM_[A-Za-z0-9_]+$", m["name"]))
            loose = "_Loose" in m["folder"]
            if not slots:
                v = "NO_SLOTS"
            elif not assigned:
                v = "NO_MATERIAL_ASSIGNED"
            elif not has_mi:
                v = "NO_MATERIAL_INSTANCE"
            elif not uni:
                v = "INSTANCE_NOT_ON_UNIVERSAL_TOON"
            else:
                v = "OK"
            verdicts[v] += 1
            detail.append({
                "mesh": m["name"], "folder": m["folder"], "verdict": v,
                "naming_ok": naming_ok, "in_loose_folder": loose,
                "materials": sorted(mats), "material_kinds": sorted(kinds),
                "lod_count": m.get("lod_count"),
                "collision": m.get("collision_flag"), "collision_prims": m.get("collision_prims"),
                "referenced_by_count": (len(m["referenced_by"]) if m["referenced_by"] is not None else None),
                "referenced_by": m["referenced_by"],
            })
        rows["verdicts"] = dict(verdicts)
        rows["mesh_detail"] = detail

        # ---- folder / organization audit
        folders = defaultdict(lambda: {"assets": [], "kinds": Counter()})
        for coll in (rows["meshes"], rows["materials"], rows["textures"], rows["other"]):
            for a in coll:
                folders[a["folder"]]["assets"].append(a["name"])
                folders[a["folder"]]["kinds"][a["name"].split("_")[0] if "_" in a["name"] else "?"] += 1
        rows["folders"] = {
            f: {"count": len(v["assets"]), "names": sorted(v["assets"])}
            for f, v in sorted(folders.items())
        }
        rows["loose_folders"] = sorted(f for f in folders if "_Loose" in f)
        rows["naming_violations"] = sorted(
            m["name"] for m in rows["meshes"] if not re.match(r"^SM_[A-Za-z0-9_]+$", m["name"]))
        rows["orphan_meshes"] = sorted(
            m["name"] for m in rows["meshes"]
            if m["referenced_by"] is not None and len(m["referenced_by"]) == 0)

        summary[key] = {
            "assets": rows["asset_count"], "meshes": len(rows["meshes"]),
            "materials": len(rows["materials"]), "textures": len(rows["textures"]),
            "other": len(rows["other"]), "verdicts": rows["verdicts"],
            "loose_folder_count": len(rows["loose_folders"]),
            "naming_violations": rows["naming_violations"],
            "orphan_meshes": rows["orphan_meshes"],
        }
        out["roots"][key] = rows

    out["summary"] = summary
    REPORT.parent.mkdir(parents=True, exist_ok=True)
    REPORT.write_text(json.dumps(out, indent=2), encoding="utf-8")
    print("MAGICIANS_AUDIT|summary=%s" % json.dumps(summary))
    print("MAGICIANS_AUDIT|wrote=%s" % REPORT)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
