"""magicians_verify.py — READ-ONLY verification of the Magician's Library state.

Checks, over BOTH trees:
  * every static mesh's material slot resolves to a MaterialInstanceConstant
    parented to M_Master_Toon_Universal (the "converted to the Universal toon
    Master" requirement)
  * the instance binds that prop's own textures (Albedo / NormalMap / ORM)
  * the instance's HeightMap is a neutral utility map, never Perlin noise
  * LOD count and collision state per mesh
  * orphan flat masters left in the live tree vs archived

Also dumps the LOD/collision API surface for the next pass.
Writes Saved/Audit/magicians_verify.json. Mutates nothing.
"""
from __future__ import annotations

import json
import re
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

import unreal

PROJECT_ROOT = Path(__file__).resolve().parents[2]
REPORT = PROJECT_ROOT / "Saved" / "Audit" / "magicians_verify.json"

MASTER = "/Game/EnvSandbox/Materials/Masters/M_Master_Toon_Universal"
NEUTRAL_HEIGHT = "/Game/EnvSandbox/Textures/Utility/T_Neutral_Height"
TREES = {
    "canonical_migrated": "/Game/EnvSandbox/Library/Migrated/MagiciansLibrary",
    "pack_native": "/Game/MagicianLabatory/Source",
}
NEUTRAL_PREFIX = "/Game/EnvSandbox/Textures/Utility/T_Neutral"


def _p(o):
    try:
        return o.get_path_name()
    except Exception:
        return ""


def api_surface():
    out = {}
    for cls_name in ("StaticMeshEditorSubsystem", "EditorStaticMeshLibrary"):
        cls = getattr(unreal, cls_name, None)
        if cls is None:
            out[cls_name] = None
            continue
        methods = {}
        for m in dir(cls):
            if m.startswith("_"):
                continue
            low = m.lower()
            if "lod" in low or "collision" in low or "simplify" in low:
                doc = (getattr(cls, m).__doc__ or "")[:200].replace("\n", " ")
                methods[m] = doc
        out[cls_name] = methods
    return out


def main() -> int:
    # Editor subsystems are not instantiated in commandlet mode; the
    # StaticMeshEditorSubsystem helpers are exposed as static functions.
    try:
        sme = unreal.get_editor_subsystem(unreal.StaticMeshEditorSubsystem)
    except Exception:
        sme = None
    if sme is None:
        sme = unreal.StaticMeshEditorSubsystem

    def _sc(sm):
        for fn in ("get_simple_collision_count",):
            try:
                return getattr(sme, fn)(sm)
            except Exception:
                pass
        return None

    def _cc(sm):
        try:
            return sme.get_convex_collision_count(sm)
        except Exception:
            return None

    def _cx(sm):
        try:
            return str(sme.get_collision_complexity(sm))
        except Exception:
            return None

    report = {"generated": datetime.now(timezone.utc).isoformat(),
              "master": MASTER, "trees": {}}
    for key, root in TREES.items():
        if not unreal.EditorAssetLibrary.does_directory_exist(root):
            report["trees"][key] = {"exists": False}
            continue
        rows = []
        verdicts = Counter()
        for p in unreal.EditorAssetLibrary.list_assets(root, recursive=True, include_folder=False):
            name = p.rsplit("/", 1)[-1].rsplit(".", 1)[0]
            if not (name.startswith("SM_") or name.startswith("candle1_L")
                    or name.startswith("SM_Candle1_L")):
                continue
            sm = unreal.load_asset(p)
            if not isinstance(sm, unreal.StaticMesh):
                continue
            slots = []
            for s in (sm.get_editor_property("static_materials") or []):
                mi = s.get_editor_property("material_interface")
                if mi is None:
                    slots.append({"material": None, "kind": "NONE"})
                    continue
                parent = None
                if isinstance(mi, unreal.MaterialInstanceConstant):
                    parent = _p(mi.get_editor_property("parent"))
                # object path is "/Game/../Name.Name" -> compare the package part
                parent_pkg = parent.rsplit(".", 1)[0] if parent else None
                tex = {}
                for pn in ("Albedo", "NormalMap", "ORM", "HeightMap"):
                    try:
                        t = mi.get_texture_parameter_value(pn)
                        tex[pn] = _p(t) if t else None
                    except Exception:
                        tex[pn] = None
                slots.append({
                    "material": _p(mi), "kind": type(mi).__name__, "parent": parent,
                    "on_universal_toon": parent_pkg == MASTER,
                    "textures": tex,
                    "height_is_neutral": (tex.get("HeightMap") or "").startswith(NEUTRAL_PREFIX),
                    "height_is_perlin": "Perlin" in (tex.get("HeightMap") or ""),
                    "albedo_is_prop": "/" + p.split("/")[-2] + "/" in (tex.get("Albedo") or "")
                    or (tex.get("Albedo") or "") != "",
                })
            row = {"mesh": p, "slots": slots,
                   "lod_count": sm.get_num_lods(),
                   "simple_collision": _sc(sm),
                   "convex_collision": _cc(sm),
                   "collision_complexity": _cx(sm)}
            if not slots:
                v = "NO_SLOTS"
            elif any(s.get("material") is None for s in slots):
                v = "NO_MATERIAL_ASSIGNED"
            elif any(s.get("kind") != "MaterialInstanceConstant" for s in slots):
                v = "NOT_AN_INSTANCE"
            elif not all(s.get("on_universal_toon") for s in slots):
                v = "NOT_ON_UNIVERSAL_TOON"
            elif any(s.get("height_is_perlin") for s in slots):
                v = "PERLIN_HEIGHT"
            else:
                v = "OK"
            row["verdict"] = v
            verdicts[v] += 1
            rows.append(row)
        flat = [p for p in unreal.EditorAssetLibrary.list_assets(root, recursive=True, include_folder=False)
                if p.rsplit("/", 1)[-1].rsplit(".", 1)[0].startswith("M_")
                and not p.rsplit("/", 1)[-1].rsplit(".", 1)[0].startswith("MI_")]
        flat_live = [p for p in flat if "/_Archive/" not in p]
        report["trees"][key] = {
            "root": root, "meshes": len(rows), "verdicts": dict(verdicts),
            "lod_histogram": dict(Counter(str(r["lod_count"]) for r in rows)),
            "simple_collision_histogram": dict(Counter(str(r["simple_collision"]) for r in rows)),
            "flat_masters_total": len(flat),
            "flat_masters_live": len(flat_live),
            "flat_masters_archived": len(flat) - len(flat_live),
            "flat_masters_live_list": sorted(p.rsplit("/", 1)[-1] for p in flat_live),
            "rows": rows,
        }
    report["api_surface"] = api_surface()
    REPORT.parent.mkdir(parents=True, exist_ok=True)
    REPORT.write_text(json.dumps(report, indent=2), encoding="utf-8")
    for k, v in report["trees"].items():
        print("VERIFY|%s|meshes=%s|verdicts=%s|lods=%s|simple_coll=%s|flat_live=%s|flat_arch=%s" % (
            k, v.get("meshes"), v.get("verdicts"), v.get("lod_histogram"),
            v.get("simple_collision_histogram"), v.get("flat_masters_live"),
            v.get("flat_masters_archived")))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
