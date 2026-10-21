"""magicians_library_deep.py — READ-ONLY deep pass on the Magician's Library trees.

Answers the questions the first audit raised:
  A. Is every per-prop material instance actually BINDING that prop's textures
     (T_<Prop>_Base / _Normal / _AO) to the Universal toon master's texture params?
  B. Which M_ masters / MI_ instances in each tree are ORPHANS (nobody points at them)?
  C. What exactly is wrong with SM_Bookshelf (it carries a master, not an instance)?
  D. Collision + LOD reality per mesh.
  E. Cross-tree leakage: does a mesh in /Game/Library point at an MI that lives in
     /Game/EnvSandbox (and vice versa)?

MUTATES NOTHING. Writes Saved/Audit/magicians_library_deep.json.
"""
from __future__ import annotations

import json
import re
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path

import unreal

PROJECT_ROOT = Path(__file__).resolve().parents[2]
REPORT = PROJECT_ROOT / "Saved" / "Audit" / "magicians_library_deep.json"

ROOTS = {
    "envsandbox_canonical": "/Game/EnvSandbox/Library/Migrated/MagiciansLibrary",
    "library_duplicate": "/Game/Library/Migrated/MagiciansLibrary",
    "archive_source": "/Game/00_Archive/MagicianLabSource_2026-08-31",
}
UNIVERSAL_TOON = "/Game/EnvSandbox/Materials/Masters/M_Master_Toon_Universal"

TEXTURE_PARAM_HINTS = ("base", "albedo", "diffuse", "normal", "orm", "ao",
                       "rough", "metal", "height", "emissive")


def _p(obj):
    try:
        return obj.get_path_name()
    except Exception:
        return ""


def parent_of(mi):
    try:
        p = mi.get_editor_property("parent")
        return _p(p) if p else None
    except Exception:
        return None


def mi_texture_overrides(mi):
    """Texture parameter overrides on the instance -> [(param_name, texture_path)]"""
    out = []
    try:
        for tv in mi.get_editor_property("texture_parameter_values") or []:
            try:
                name = str(tv.get_editor_property("parameter_name"))
            except Exception:
                name = "?"
            try:
                tex = tv.get_editor_property("texture")
                out.append((name, _p(tex) if tex else None))
            except Exception:
                out.append((name, None))
    except Exception as ex:
        return out, "ERR:" + str(ex)
    return out, None


def material_graph_shape(mat):
    info = {"expr_count": 0, "has_toon_bsdf": False, "params": []}
    try:
        exprs = list(unreal.MaterialEditingLibrary.get_material_expressions(mat) or [])
        info["expr_count"] = len(exprs)
        for e in exprs:
            cn = type(e).__name__
            if "ToonBSDF" in cn or "SubstrateToon" in cn:
                info["has_toon_bsdf"] = True
            if "Parameter" in cn:
                try:
                    info["params"].append(str(e.get_editor_property("parameter_name")))
                except Exception:
                    pass
    except Exception as ex:
        info["error"] = str(ex)
    info["params"] = sorted(set(info["params"]))
    return info


def mesh_collision(sm):
    out = {}
    esml = unreal.EditorStaticMeshLibrary
    for fn, key in (("get_simple_collision_count_for_mesh", "simple_collision"),
                    ("get_convex_collision_count_for_mesh", "convex_collision")):
        try:
            out[key] = getattr(esml, fn)(sm)
        except Exception as ex:
            out[key] = "ERR:" + str(ex)
    try:
        out["collision_complexity"] = str(sm.get_editor_property("collision_complexity"))
    except Exception:
        pass
    return out


def main() -> int:
    report = {"generated": datetime.now(timezone.utc).isoformat(),
              "universal_toon_master": UNIVERSAL_TOON, "roots": {}}
    for key, root in ROOTS.items():
        if not unreal.EditorAssetLibrary.does_directory_exist(root):
            report["roots"][key] = {"exists": False}
            continue
        paths = unreal.EditorAssetLibrary.list_assets(root, recursive=True, include_folder=False)
        r = {"root": root, "asset_count": len(paths),
             "materials": [], "meshes": [], "textures": []}
        for p in paths:
            base = p.rsplit("/", 1)[-1].rsplit(".", 1)[0]
            folder = "/".join(p.split("/")[:-1])
            try:
                a = unreal.load_asset(p)
            except Exception:
                a = None
            if a is None:
                continue
            if isinstance(a, unreal.MaterialInstanceConstant):
                tex, err = mi_texture_overrides(a)
                r["materials"].append({
                    "name": base, "path": p, "folder": folder, "kind": "instance",
                    "parent": parent_of(a),
                    "texture_overrides": tex, "texture_override_error": err,
                    "shape": None,
                })
            elif isinstance(a, unreal.Material):
                r["materials"].append({
                    "name": base, "path": p, "folder": folder, "kind": "master",
                    "parent": None, "texture_overrides": [], "texture_override_error": None,
                    "shape": material_graph_shape(a),
                })
            elif isinstance(a, unreal.StaticMesh):
                coll = mesh_collision(a)
                slots = []
                for s in (a.get_editor_property("static_materials") or []):
                    try:
                        mi = s.get_editor_property("material_interface")
                    except Exception:
                        mi = None
                    slots.append({"slot": str(s.get_editor_property("material_slot_name")),
                                  "material": _p(mi) if mi else None})
                r["meshes"].append({"name": base, "path": p, "folder": folder, "slots": slots,
                                    "lod_count": a.get_num_lods(), "collision": coll})
            elif isinstance(a, unreal.Texture2D):
                r["textures"].append({"name": base, "path": p, "folder": folder})

        # ---- who references each material (within this project)
        for m in r["materials"]:
            try:
                refs = unreal.EditorAssetLibrary.find_package_referencers_for_asset(m["path"], False)
                m["referenced_by"] = sorted(x for x in (refs or []) if "/Temp" not in x)
            except Exception:
                m["referenced_by"] = None

        # ---- A. texture binding check per MI
        texture_names = {t["name"] for t in r["textures"]}
        binding = []
        for m in r["materials"]:
            if m["kind"] != "instance":
                continue
            bound = [t for _, t in m["texture_overrides"] if t]
            bound_names = [t.rsplit("/", 1)[-1].rsplit(".", 1)[0] for t in bound]
            prop_stem = m["name"]
            for pref in ("MI_M_", "MI_SM_", "MI_"):
                if prop_stem.startswith(pref):
                    prop_stem = prop_stem[len(pref):]
                    break
            stem_variants = {prop_stem, prop_stem.replace("_", "")}
            matched = [n for n in bound_names
                       if any(n.startswith(sv) or sv in n for sv in stem_variants if sv)]
            binding.append({
                "mi": m["name"], "parent": m["parent"],
                "n_texture_overrides": len(bound),
                "bound": bound_names,
                "binds_own_prop_textures": bool(matched),
                "matched": matched,
                "referenced_by_count": (len(m["referenced_by"]) if m["referenced_by"] is not None else None),
            })
        r["mi_texture_binding"] = binding

        # ---- B. orphan materials (not referenced by anything outside their own tree)
        orphan_mats = []
        for m in r["materials"]:
            refs = m["referenced_by"] or []
            outside = [x for x in refs if "MagiciansLibrary" not in x]
            internal = [x for x in refs if "MagiciansLibrary" in x]
            m["external_referencers"] = outside
            m["internal_referencers"] = internal
            if not outside:
                orphan_mats.append({"name": m["name"], "kind": m["kind"],
                                    "folder": m["folder"].split("MagiciansLibrary/")[-1],
                                    "parent": m["parent"],
                                    "internal_refs": len(internal)})
        r["orphan_materials"] = orphan_mats

        # ---- E. cross-tree leakage on mesh slot assignments
        leak = []
        for m in r["meshes"]:
            for s in m["slots"]:
                if not s["material"]:
                    continue
                mp = s["material"].rsplit(".", 1)[0]
                if not mp.startswith("/Game/" + root.lstrip("/Game/")):
                    other = "envsandbox" if "/EnvSandbox/" in mp else ("library" if "/Library/" in mp else "other")
                    leak.append({"mesh": m["name"], "mesh_tree": key,
                                 "slot_material": mp, "material_lives_in": other})
        r["cross_tree_assignments"] = leak

        # ---- D. mesh collision/LOD summary
        r["lod_histogram"] = dict(Counter(str(m["lod_count"]) for m in r["meshes"]))
        r["collision_summary"] = dict(Counter(
            str(m["collision"].get("simple_collision")) for m in r["meshes"]))
        report["roots"][key] = r

    REPORT.parent.mkdir(parents=True, exist_ok=True)
    REPORT.write_text(json.dumps(report, indent=2), encoding="utf-8")
    print("MAGICIANS_DEEP|wrote=%s" % REPORT)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
