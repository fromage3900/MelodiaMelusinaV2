"""magicians_mesh_finish.py — build LODs and simple collision for the kit.

The 2026-10-21 audit found every Magician's Library mesh at LODCount=1 with
0 simple collision primitives and CTF_USE_COMPLEX_AS_SIMPLE (triangle mesh as
collision) — expensive for a prop kit and unusable for fast-moving queries.

For each mesh:
  * 3 extra LODs (LOD1..LOD3) via StaticMeshEditorSubsystem.set_lods
  * screen sizes 1.0 / 0.55 / 0.30 / 0.12
  * simple BOX collision
  * collision complexity back to UseDefault so the simple hull is used
  * save

Mode: MAGICIANS_MODE=apply (default plan)
Slice: MAGICIANS_SLICE="start:end" over the sorted mesh list
Writes Saved/Audit/magicians_mesh_finish.json
"""
from __future__ import annotations

import json
import os
import sys
import time
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

import unreal

PROJECT_ROOT = Path(__file__).resolve().parents[2]
REPORT = PROJECT_ROOT / "Saved" / "Audit" / "magicians_mesh_finish.json"

TREES = {
    "canonical_migrated": "/Game/EnvSandbox/Library/Migrated/MagiciansLibrary",
    "pack_native": "/Game/MagicianLabatory/Source",
}
LOD_SCREEN_SIZES = [1.0, 0.55, 0.30, 0.12, 0.05]
N_LODS = 4


def _p(o):
    try:
        return o.get_path_name()
    except Exception:
        return ""


def reduction_settings():
    """A single StaticMeshReductionOptions carrying N MeshReductionSettings.

    EditorStaticMeshLibrary.SetLods takes ONE StaticMeshReductionOptions
    (not an array) and it holds a `reduction_settings` array.
    """
    rs = []
    settings_cls = getattr(unreal, "StaticMeshReductionSettings", None) or \
        getattr(unreal, "MeshReductionSettings", None)
    for i in range(N_LODS):
        s = settings_cls()
        for prop, val in (("percent_triangles", 50.0), ("min_triangles", 10),
                          ("lossy_quality", 0.5), ("bpreserve_symmetry", True),
                          ("bcheck_mirrored", True)):
            try:
                s.set_editor_property(prop, val)
            except Exception:
                pass
        rs.append(s)
    opts = unreal.StaticMeshReductionOptions()
    try:
        opts.set_editor_property("reduction_settings", rs)
    except Exception:
        pass
    try:
        opts.set_editor_property("auto_compute_lod_screen_size", False)
    except Exception:
        pass
    return opts


def collision_counts(sm):
    """(simple, convex) primitive counts, read from the body setup."""
    try:
        bs = sm.get_editor_property("body_setup")
        geom = bs.get_editor_property("agg_geom")
        simple = len(list(geom.get_editor_property("simple_collision_shape") or []))
        convex = len(list(geom.get_editor_property("convex_collision_shape") or []))
        return simple, convex
    except Exception:
        return None, None


def main() -> int:
    mode = (os.environ.get("MAGICIANS_MODE") or
            (sys.argv[1].strip().lower() if len(sys.argv) > 1 else "plan"))
    if mode not in ("plan", "apply"):
        mode = "plan"
    lo, hi = 0, 10 ** 9
    sl = os.environ.get("MAGICIANS_SLICE") or ""
    if ":" in sl:
        try:
            a, b = sl.split(":")
            lo, hi = int(a), int(b)
        except ValueError:
            lo, hi = 0, 10 ** 9

    # StaticMeshEditorSubsystem is an EDITOR subsystem: it only exists in a
    # full editor. In a commandlet it is None and the deprecated
    # EditorStaticMeshLibrary LOD/collision calls are no-op stubs (return -1).
    sme = None
    try:
        sme = unreal.get_editor_subsystem(unreal.StaticMeshEditorSubsystem)
    except Exception:
        sme = None
    def set_lods(sm):
        if sme is not None:
            return sme.set_lods(sm, reduction_settings())
        return unreal.EditorStaticMeshLibrary.set_lods(sm, reduction_settings())

    def set_screen_sizes(sm):
        if sme is not None:
            return sme.set_lod_screen_sizes(sm, LOD_SCREEN_SIZES)
        return None

    def add_collision(sm):
        if sme is not None:
            return sme.add_simple_collisions(sm, unreal.ScriptingCollisionShapeType.BOX)
        return unreal.EditorStaticMeshLibrary.add_simple_collisions(
            sm, unreal.ScriptingCollisionShapeType.BOX)

    targets = []
    for key, root in TREES.items():
        if not unreal.EditorAssetLibrary.does_directory_exist(root):
            continue
        for p in unreal.EditorAssetLibrary.list_assets(root, recursive=True, include_folder=False):
            name = p.rsplit("/", 1)[-1].rsplit(".", 1)[0]
            if not (name.startswith("SM_") or name.startswith("candle1_L")
                    or name.startswith("SM_Candle1_L")):
                continue
            targets.append((key, p))
    targets.sort(key=lambda t: t[1])
    total = len(targets)
    targets = targets[lo:hi]

    rows = []
    counters = Counter()
    t0 = time.time()
    for key, p in targets:
        sm = unreal.load_asset(p)
        row = {"tree": key, "mesh": p}
        if not isinstance(sm, unreal.StaticMesh):
            row["result"] = "load_failed"
            counters["load_failed"] += 1
            rows.append(row)
            continue
        row["lod_before"] = sm.get_num_lods()
        row["collision_before"] = collision_counts(sm)
        if mode == "plan":
            row["result"] = "planned"
            counters["planned"] += 1
            rows.append(row)
            continue
        try:
            n = set_lods(sm)
            row["set_lods_return"] = n
            if n == -1:
                row["set_lods_error"] = "degenerate API (no-op) - needs the editor subsystem"
                counters["set_lods_failed"] += 1
        except Exception as ex:
            row["set_lods_error"] = str(ex)[:220]
            counters["set_lods_failed"] += 1
        try:
            set_screen_sizes(sm)
        except Exception as ex:
            row["screen_sizes_error"] = str(ex)[:120]
        try:
            add_collision(sm)
        except Exception as ex:
            row["collision_error"] = str(ex)[:180]
            counters["collision_failed"] += 1
        try:
            sm.set_editor_property("collision_complexity",
                                   unreal.CollisionTraceFlag.CTF_USE_DEFAULT)
        except Exception:
            pass
        try:
            unreal.EditorAssetLibrary.save_loaded_asset(sm, only_if_is_dirty=False)
            row["result"] = "ok"
            counters["ok"] += 1
        except Exception as ex:
            row["result"] = "save_failed: " + str(ex)[:150]
            counters["save_failed"] += 1
        row["lod_after"] = sm.get_num_lods()
        row["collision_after"] = collision_counts(sm)
        rows.append(row)

    out = {
        "generated": datetime.now(timezone.utc).isoformat(),
        "mode": mode, "slice": "%d:%d" % (lo, hi), "total_meshes": total,
        "processed": len(targets), "counters": dict(counters),
        "subsystem_available": sme is not None,
        "seconds": round(time.time() - t0, 1),
        "rows": rows,
    }
    REPORT.parent.mkdir(parents=True, exist_ok=True)
    REPORT.write_text(json.dumps(out, indent=2), encoding="utf-8")
    print("MESHFINISH|%s|slice=%d:%d/%d|counters=%s|%.1fs" % (
        mode, lo, hi, total, json.dumps(dict(counters)), out["seconds"]))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
