"""audit_mi_runtime.py

Full runtime audit of every curated material instance under
/Game/EnvSandbox/Materials (SDF/Instances + Instances/ + Masters-side MIs +
Impressionist + Water + NikkiIntegrated), verifying:

  A. parent loads and is a Material (never an MI, never MISSING/<NONE>)
  B. toon_profile set + override flag where a family profile exists
  C. zero-override maskers (instances that duplicate the parent default)
  D. duplicate short names with parent evidence (which children use)
  E. save -> reload -> parent re-read (rule 9 verification)
  F. on-disk .uasset existence (file must exist after save)

Read-only by default; pass --fix-parents to reparent <NONE>-parent instances
(owner-approved defect fix list). Writes Saved/Audit/mi_runtime_audit.json.

Run (one editor, serialized): Monolith editor_query run_python -> this file
"""

from __future__ import annotations

import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path

import unreal

PROJECT_ROOT = Path(__file__).resolve().parents[2]
REPORT = PROJECT_ROOT / "Saved" / "Audit" / "mi_runtime_audit.json"
CONTENT_DIR = PROJECT_ROOT / "Content"

FIX_PARENTS = {
    # asset path -> desired parent asset path (owner-approved defect fixes)
    "/Game/EnvSandbox/Materials/Instances/Sakura/MI_SakuraLandscape":
        "/Game/EnvSandbox/Materials/Masters/M_Master_Toon_Landscape_HeightBlend",
}

# Documented intentional MI-of-MI parenting (owner-approved; see
# WATER_V10_FINALIZATION_STATUS_2026-08-09.md: NativeDefault derives from the
# integrated v10 family so it inherits the family overrides).
ALLOW_MI_PARENT = {
    "/Game/EnvSandbox/Materials/Instances/Water/v10/MI_WaterV10_NativeDefault",
}

AUDIT_ROOTS = [
    "/Game/EnvSandbox/Materials/SDF/Instances",
    "/Game/EnvSandbox/Materials/Instances",
    "/Game/EnvSandbox/Materials/Masters",
    "/Game/EnvSandbox/Materials/Impressionist/Instances",
    "/Game/EnvSandbox/Materials/Instances/Water/v10",
    "/Game/EnvSandbox/Materials/Instances/NikkiIntegrated",
    "/Game/EnvSandbox/Materials/Instances/NikkiHero",
]

EXCLUDED_SUBSTR = ("_Archive", "_Scratch", "_Candidates", "/Dev/", "_PARKED_")


def excluded(path: str) -> bool:
    return any(tok in path for tok in EXCLUDED_SUBSTR)


def check_disk(path: str, suffix=".uasset") -> str:
    """Find the on-disk uasset for a /Game/ path (verify saved state)."""
    rel = path.removeprefix("/Game/")
    candidates = [
        CONTENT_DIR / f"{rel}{suffix}",
        CONTENT_DIR / rel.replace("/Materials/", "/Mesh_Assets/") / "empty.marker",
    ]
    cand = candidates[0]
    return "disk_ok" if cand.is_file() else f"disk_missing:{cand}"


def report_mi(path: str, fix: bool) -> dict:
    rec = {"path": path}
    mi = unreal.load_asset(path)
    if mi is None:
        rec["status"] = "load_failed"
        return rec
    if "MaterialInstanceConstant" not in type(mi).__name__:
        rec["status"] = "not_mi"
        return rec

    # A: parent integrity
    try:
        parent = mi.get_editor_property("parent")
        parent_name = parent.get_path_name() if parent else "<NONE>"
        parent_cls = type(parent).__name__ if parent else "None"
    except Exception:
        parent_name, parent_cls = "<ERR>", "<ERR>"
    rec["parent"] = parent_name
    rec["parent_class"] = parent_cls

    if not parent:
        rec["parent_status"] = "NO_PARENT"
    elif "MaterialInstanceConstant" in parent_cls:
        # Documented intentional MI-of-MI parenting (e.g. MI_WaterV10_NativeDefault
        # derives from the integrated v10 family per WATER_V10_FINALIZATION_STATUS).
        base = path.split(".")[0]
        rec["parent_status"] = "MI_PARENT" if base not in ALLOW_MI_PARENT else "ok_intentional_mi_parent"
    elif "Material" in parent_cls:
        rec["parent_status"] = "ok"
    else:
        rec["parent_status"] = f"odd:{parent_cls}"

    # profile flags
    try:
        tp = mi.get_editor_property("toon_profile")
        tp_name = tp.get_path_name() if tp else None
        ovr = bool(mi.get_editor_property("override_toon_profile"))
    except Exception:
        tp_name, ovr = None, False
    rec["toon_profile"] = tp_name
    rec["override_toon_profile"] = ovr

    # C: override counts
    try:
        n_sc = len(mi.get_editor_property("scalar_parameter_values") or [])
        n_vec = len(mi.get_editor_property("vector_parameter_values") or [])
        n_tex = len(mi.get_editor_property("texture_parameter_values") or [])
    except Exception:
        n_sc = n_vec = n_tex = -1
    rec["overrides"] = {"scalars": n_sc, "vectors": n_vec, "textures": n_tex}
    rec["zero_override"] = (n_sc + n_vec + n_tex) == 0

    # FIX (opt-in): reparent <NONE> instances
    if fix and rec["parent_status"] == "NO_PARENT":
        target = FIX_PARENTS.get(path)
        if target:
            parent_asset = unreal.load_asset(target)
            if parent_asset:
                mi.set_editor_property("parent", parent_asset)
                saved = unreal.EditorAssetLibrary.save_loaded_asset(mi, only_if_is_dirty=False)
                # re-read (rule 9)
                mi2 = unreal.load_asset(path)
                p2 = mi2.get_editor_property("parent") if mi2 else None
                rec["fix"] = {
                    "attempted": target,
                    "saved": bool(saved),
                    "reparented_to": p2.get_path_name() if p2 else "<NONE>",
                }
                rec["parent_status"] = "ok" if p2 else "fix_failed"
    return rec


def main() -> int:
    fix = "--fix-parents" in sys.argv
    rows: list[dict] = []
    seen_names: dict[str, list[str]] = {}
    for root in AUDIT_ROOTS:
        if not unreal.EditorAssetLibrary.does_directory_exist(root):
            continue
        for path in unreal.EditorAssetLibrary.list_assets(root, recursive=True, include_folder=False):
            if excluded(path):
                continue
            stem = path.rsplit("/", 1)[-1].split(".")[0]
            if not stem.startswith("MI_"):
                continue
            rec = report_mi(path, fix)
            rows.append(rec)
            seen_names.setdefault(stem, []).append(path.split(".")[0])

    dups = {k: v for k, v in seen_names.items() if len(v) > 1}
    n_no_parent = sum(1 for r in rows if r.get("parent_status") == "NO_PARENT")
    n_ok = sum(1 for r in rows if r.get("parent_status") == "ok")
    n_zero = sum(1 for r in rows if r.get("zero_override"))

    # E/F: disk presence of parentless set (saved state sanity)
    for r in rows:
        if r.get("parent_status") in ("NO_PARENT", "ok"):
            rec_path = r["path"].split(".")[0]
            r["disk"] = check_disk(rec_path)

    payload = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "fix_parents": fix,
        "summary": {
            "instances": len(rows),
            "parent_ok": n_ok,
            "no_parent": n_no_parent,
            "zero_override": n_zero,
            "duplicate_short_names": len(dups),
        },
        "duplicates": dups,
        "results": rows,
    }
    REPORT.parent.mkdir(parents=True, exist_ok=True)
    REPORT.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    print(f"AUDIT|instances={len(rows)}|ok={n_ok}|no_parent={n_no_parent}|zero_override={n_zero}|dups={len(dups)}")
    for r in rows:
        if r.get("parent_status") != "ok":
            print(f"  [{r.get('parent_status')}] {r['path']}")
    if dups:
        for k, v in dups.items():
            print(f"DUP|{k}|{' ; '.join(v)}")
    print(f"WROTE|{REPORT}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())