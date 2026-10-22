"""magicians_repoint_duplicates.py â€” move live references off the duplicate tree.

The 2026-09-01 purge spec wanted /Game/Library/Migrated/MagiciansLibrary deleted
as a duplicate of the canonical
/Game/EnvSandbox/Library/Migrated/MagiciansLibrary, but it was never executed
and, as it stands, is unsafe: 22 assets outside the tree still reference it
(4 PCG graphs + 18 material instances that use its T_Microscope_Normal).

This script re-points those references at the canonical assets, then the tree
can be archived without breaking anything.

Modes: MAGICIANS_MODE=plan (default) | apply
Writes Saved/Audit/magicians_repoint_duplicates.json
"""
from __future__ import annotations

import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path

import unreal

PROJECT_ROOT = Path(__file__).resolve().parents[2]
REPORT = PROJECT_ROOT / "Saved" / "Audit" / "magicians_repoint_duplicates.json"

DUP = "/Game/Library/Migrated/MagiciansLibrary"
CANON = "/Game/EnvSandbox/Library/Migrated/MagiciansLibrary"
ARCHIVE = "/Game/Library/_Archive/MagiciansLibrary_20261021"

# duplicate asset name -> canonical asset path
MESH_MAP = {
    "SM_Box": CANON + "/Box/SM_Box",
    "SM_Carpet": CANON + "/Carpet/SM_Carpet",
    "SM_Deco1": CANON + "/Deco1/SM_Kit_Ornament_A",
    "SM_Deco2": CANON + "/Deco2/SM_Kit_Ornament_B",
    "SM_Deco3": CANON + "/Deco3/SM_Kit_Ornament_C",
    "SM_Deco4": CANON + "/Deco4/SM_Deco4",
    "SM_Deco5": CANON + "/Deco5/SM_Deco5",
    "SM_Deco6": CANON + "/Deco6/SM_Deco6",
    "SM_Deco7": CANON + "/Deco7/SM_Deco7",
    "SM_Lantern": CANON + "/Lantern/SM_Lantern",
    "SM_GlassBottle_Object1715": CANON + "/GlassBottle/SM_GlassBottle_Object1715",
}
TEX_MAP = {
    "T_Microscope_Normal": CANON + "/Microscope/T_Microscope_Normal",
}

# duplicate package path -> canonical package path
def canonical_for(dup_pkg_path: str):
    """dup_pkg_path like /Game/Library/Migrated/MagiciansLibrary/Box/SM_Box.SM_Box"""
    if not dup_pkg_path.startswith(DUP):
        return None
    name = dup_pkg_path.rsplit("/", 1)[-1].rsplit(".", 1)[0]
    rel = dup_pkg_path[len(DUP) + 1:].rsplit(".", 1)[0]  # folder/name
    if name in MESH_MAP:
        return MESH_MAP[name]
    if name in TEX_MAP:
        return TEX_MAP[name]
    folder = rel.rsplit("/", 1)[0] if "/" in rel else ""
    if folder:
        cand = "%s/%s/%s" % (CANON, folder, name)
        if unreal.EditorAssetLibrary.does_asset_exist(cand):
            return cand
    cand = "%s/%s" % (CANON, name)
    if unreal.EditorAssetLibrary.does_asset_exist(cand):
        return cand
    return None


def _p(o):
    try:
        return o.get_path_name()
    except Exception:
        return ""


def _ref_path(o):
    """Path of a hard object OR a soft object path (PCG stores TSoftObjectPtr)."""
    if o is None:
        return ""
    p = _p(o)
    if p:
        return p
    for attr in ("get_asset_path_name", "get_asset_name", "to_string"):
        fn = getattr(o, attr, None)
        if fn is None:
            continue
        try:
            v = fn()
            s = str(v)
            if s and s != "None":
                return s
        except Exception:
            continue
    try:
        s = str(o)
        if "/" in s:
            return s
    except Exception:
        pass
    return ""


def find_refs(asset, want_pkgs):
    """Locate the properties holding references into the duplicate tree.

    Two storage shapes matter here:
      * MaterialInstanceConstant -> texture_parameter_values[]
        (each FTextureParameterValue has parameter_info / parameter_value)
      * PCGGraph -> nodes[] -> each node's own properties
    """
    hits = []
    cls = type(asset).__name__

    # --- material instance texture overrides
    if isinstance(asset, unreal.MaterialInstanceConstant):
        try:
            tvs = asset.get_editor_property("texture_parameter_values") or []
        except Exception:
            tvs = []
        for i, tv in enumerate(tvs):
            try:
                info = tv.get_editor_property("parameter_info")
                pname = str(info.get_editor_property("name"))
            except Exception:
                pname = "?"
            try:
                val = tv.get_editor_property("parameter_value")
            except Exception:
                val = None
            vp = _ref_path(val)
            if vp and _pkg(vp) in want_pkgs:
                hits.append({"prop": "texture_parameter_values[%d]" % i,
                             "param": pname, "value": vp, "kind": "mi_texture"})

    # --- PCG graph nodes (the mesh lives in each node's settings_interface)
    if cls == "PCGGraph":
        try:
            nodes = asset.get_editor_property("nodes") or []
        except Exception:
            nodes = []
        for ni, node in enumerate(nodes):
            for prop in [n for n in dir(node) if not n.startswith("_")]:
                try:
                    val = node.get_editor_property(prop)
                except Exception:
                    continue
                if val is None:
                    continue
                if isinstance(val, (list, tuple)):
                    for i, v in enumerate(val):
                        vp = _ref_path(v)
                        if vp and _pkg(vp) in want_pkgs:
                            hits.append({"prop": "nodes[%d].%s[%d]" % (ni, prop, i),
                                         "value": vp, "kind": "pcg_node_array",
                                         "node": node.get_name()})
                else:
                    vp = _ref_path(val)
                    if vp and _pkg(vp) in want_pkgs:
                        hits.append({"prop": "nodes[%d].%s" % (ni, prop),
                                     "value": vp, "kind": "pcg_node",
                                     "node": node.get_name()})
                    elif _is_object(val):
                        _descend(val, want_pkgs, "nodes[%d].%s" % (ni, prop), 1, hits)
    return hits


def _descend(val, want_pkgs, path, depth, hits, maxdepth=4):
    """Recursively look inside object-valued properties. PCG nests the mesh list
    two levels down: node -> settings_interface -> mesh_selector_parameters -> meshes."""
    if depth > maxdepth:
        return
    for sp in [n for n in dir(val) if not n.startswith("_")]:
        try:
            sv = val.get_editor_property(sp)
        except Exception:
            continue
        if sv is None:
            continue
        if isinstance(sv, (list, tuple)):
            for i, v in enumerate(sv):
                vp = _ref_path(v)
                if vp and _pkg(vp) in want_pkgs:
                    hits.append({"prop": "%s.%s[%d]" % (path, sp, i),
                                 "value": vp, "kind": "deep_array"})
                elif _is_object(v):
                    _descend(v, want_pkgs, "%s.%s[%d]" % (path, sp, i), depth + 1, hits)
        else:
            vp = _ref_path(sv)
            if vp and _pkg(vp) in want_pkgs:
                hits.append({"prop": "%s.%s" % (path, sp), "value": vp, "kind": "deep"})
            elif _is_object(sv):
                _descend(sv, want_pkgs, "%s.%s" % (path, sp), depth + 1, hits)


def _pkg(s):
    """Package path of an object path: '/a/b/C.C' -> '/a/b/C'."""
    if not s:
        return ""
    tail = s.rsplit("/", 1)[-1]
    if "." in tail:
        return s[: -(len(tail) - tail.index("."))]
    return s


def _is_object(v):
    """True for UObjects AND for UE struct wrappers (both expose get_editor_property)."""
    return hasattr(v, "get_editor_property")


def _node_at(graph, prop_path):
    """'nodes[3].mesh' -> the PCG node object at index 3."""
    try:
        ni = int(prop_path.split("[")[1].split("]")[0])
        nodes = graph.get_editor_property("nodes") or []
        return nodes[ni]
    except Exception:
        return None


def main() -> int:
    mode = (os.environ.get("MAGICIANS_MODE") or
            (sys.argv[1].strip().lower() if len(sys.argv) > 1 else "plan"))
    if mode not in ("plan", "apply"):
        mode = "plan"
    out = {"generated": datetime.now(timezone.utc).isoformat(), "mode": mode,
           "referencers": [], "unmapped": []}

    dup_assets = [str(p) for p in unreal.EditorAssetLibrary.list_assets(DUP, recursive=True, include_folder=False)]
    # package path -> canonical package path
    pkg_map = {}
    for p in dup_assets:
        pkg = p.rsplit(".", 1)[0]
        c = canonical_for(pkg)
        if c:
            pkg_map[pkg] = c
        else:
            out["unmapped"].append(pkg)

    # external referencers
    ext = {}
    for p in dup_assets:
        try:
            refs = unreal.EditorAssetLibrary.find_package_referencers_for_asset(p, False) or []
        except Exception:
            refs = []
        for r in refs:
            if r.startswith(DUP) or "/Temp" in r:
                continue
            ext.setdefault(r, set()).add(p)

    total_hits = 0
    for ref_path, dup_paths in sorted(ext.items()):
        asset = unreal.load_asset(ref_path)
        row = {"referencer": ref_path, "dup_refs": sorted(dup_paths), "hits": []}
        if asset is None:
            row["error"] = "referencer load failed"
            out["referencers"].append(row)
            continue
        want = set(_pkg(x) for x in dup_paths)
        hits = find_refs(asset, want)
        for h in hits:
            canon = canonical_for(h["value"].rsplit(".", 1)[0] + "." +
                                  h["value"].rsplit(".", 1)[-1])
            h["canonical"] = canon
            h["mapped"] = canon is not None
        row["hits"] = hits
        total_hits += len(hits)
        if mode == "apply":
            applied = 0
            for h in hits:
                if not h.get("canonical"):
                    continue
                new_obj = unreal.load_asset(h["canonical"])
                if new_obj is None:
                    continue
                try:
                    if h["kind"] == "mi_texture":
                        unreal.MaterialEditingLibrary.set_material_instance_texture_parameter_value(
                            asset, h["param"], new_obj)
                    elif h["kind"] == "pcg_node":
                        node = _node_at(asset, h["prop"])
                        if node is not None:
                            node.set_editor_property(h["prop"].split(".")[-1], new_obj)
                    elif h["kind"] == "pcg_node_array":
                        node = _node_at(asset, h["prop"])
                        if node is not None:
                            leaf = h["prop"].split(".")[-1]
                            idx = int(leaf.split("[")[1].rstrip("]"))
                            base = leaf.split("[")[0]
                            arr = list(node.get_editor_property(base))
                            arr[idx] = new_obj
                            node.set_editor_property(base, arr)
                    elif h["kind"] in ("pcg_settings", "pcg_settings_array"):
                        node = _node_at(asset, h["prop"])
                        if node is None:
                            continue
                        parts = h["prop"].split(".")
                        settings = node.get_editor_property(parts[2])
                        leaf = parts[-1]
                        if "[" in leaf:
                            base = leaf.split("[")[0]
                            idx = int(leaf.split("[")[1].rstrip("]"))
                            arr = list(settings.get_editor_property(base))
                            arr[idx] = new_obj
                            settings.set_editor_property(base, arr)
                        else:
                            settings.set_editor_property(leaf, new_obj)
                    applied += 1
                except Exception as ex:
                    h["apply_error"] = str(ex)[:140]
            row["applied"] = applied
            if applied:
                try:
                    unreal.EditorAssetLibrary.save_loaded_asset(asset, only_if_is_dirty=False)
                    row["saved"] = True
                except Exception as ex:
                    row["save_error"] = str(ex)[:140]
        out["referencers"].append(row)

    out["total_hits"] = total_hits
    out["n_referencers"] = len(out["referencers"])
    out["n_unmapped_dup_assets"] = len(out["unmapped"])

    # ---------- archive the duplicate tree (UE's own move, which fixes references)
    if mode == "apply" and os.environ.get("MAGICIANS_ARCHIVE") == "1":
        arch = {"from": DUP, "to": ARCHIVE}
        try:
            if unreal.EditorAssetLibrary.does_directory_exist(ARCHIVE):
                arch["result"] = "archive target already exists"
            else:
                unreal.EditorAssetLibrary.make_directory("/Game/Library/_Archive")
                ok = unreal.EditorAssetLibrary.rename_directory(DUP, ARCHIVE)
                arch["result"] = "moved" if ok else "rename_directory returned False"
        except Exception as ex:
            arch["result"] = "ERR " + str(ex)[:220]
        arch["dup_exists_after"] = unreal.EditorAssetLibrary.does_directory_exist(DUP)
        arch["archive_exists_after"] = unreal.EditorAssetLibrary.does_directory_exist(ARCHIVE)
        out["archive"] = arch

    REPORT.parent.mkdir(parents=True, exist_ok=True)
    REPORT.write_text(json.dumps(out, indent=2), encoding="utf-8")
    print("REPOINT|%s|referencers=%d|hits=%d|unmapped_dup_assets=%d" % (
        mode, out["n_referencers"], total_hits, out["n_unmapped_dup_assets"]))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())



