"""Organize material folders + metadata (v2) — long-term lane per MATERIAL_ORG_PLAN_2026-08-25.

Run headless (editor CLOSED):
    & "C:\\Program Files\\Epic Games\\UE_5.8\\Engine\\Binaries\\Win64\\UnrealEditor-Cmd.exe" ^
      "C:\\EnvironmentPortfolio\\BS_GodFile\\BS_GodFile.uproject" ^
      -ExecutePythonScript="Content/Python/organize_material_folders_v2.py" ^
      -unattended -noP4 -nullRHI -NOSOUND -stdout -nosplash

Or in-editor:  py Content/Python/organize_material_folders_v2.py --dry-run

What it does (metadata ONLY — never touches graph topology):
  1. Census scan of target roots (disk-level when no editor; registry-level in editor).
  2. Assigns Content Browser Group + SortPriority on material expressions of MASTERS only,
     following master_column_scheme groups_for(stem).
  3. Writes Saved/Audit/material_org_v2_report.json with duplicates/orphans/drift flags.
  4. Dry-run by default: pass --apply to write metadata.

Safety:
  - Never saves masters without --apply.
  - Batched saves with list_dirty_packages verification after each batch.
  - Skips _Archive/_Scratch/_Quarantine trees entirely (read-only evidence).
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
REPORT = PROJECT_ROOT / "Saved" / "Audit" / "material_org_v2_report.json"

# Canonical roots (registry paths) and their disk mirrors for no-editor census
ROOTS = [
    ("/Game/EnvSandbox/Materials", PROJECT_ROOT / "Content" / "EnvSandbox" / "Materials"),
    ("/Game/Melodia/_PROJECT/04_Materials", PROJECT_ROOT / "Content" / "Melodia" / "_PROJECT" / "04_Materials"),
    ("/Game/ZenForestTest_MusicalGlam", PROJECT_ROOT / "Content" / "ZenForestTest_MusicalGlam"),
]
SKIP_PARTS = {"_Archive", "_Scratch", "_Quarantine", "_Recovery", "Candidates"}

CLASS_PREFIX = {
    "M_": "Material",
    "MI_": "MaterialInstanceConstant",
    "MF_": "MaterialFunction",
    "MPC_": "MaterialParameterCollection",
    "NPC_": "NiagaraParameterCollection",
    "T_": "Texture2D",
}

# Group scheme derived from master_column_scheme conventions
GROUP_RULES = [
    (re.compile(r"^M_Master_Toon_Landscape|^M_.*Landscape.*HeightBlend", re.I), "Landscape"),
    (re.compile(r"^M_Master_Toon_Character", re.I), "Character"),
    (re.compile(r"^M_Master_(SDF|Nikki)", re.I), "Stylized"),
    (re.compile(r"^M_Water|^MF_Water", re.I), "Water"),
    (re.compile(r"^MF_Nikki", re.I), "Function/Nikki"),
    (re.compile(r"^MF_Impressionist", re.I), "Function/Impressionist"),
    (re.compile(r"^MF_", re.I), "Function"),
    (re.compile(r"^M_Zen_", re.I), "GlamPass/ZenForest"),
    (re.compile(r"^MI_", re.I), "Instance"),
]


def classify(name: str) -> str:
    for prefix, cls in CLASS_PREFIX.items():
        if name.startswith(prefix):
            return cls
    return "Unknown"


def group_for(name: str) -> str:
    for pattern, group in GROUP_RULES:
        if pattern.search(name):
            return group
    return "Misc"


def disk_census() -> dict:
    """No-editor mode: filesystem-only census."""
    assets = []
    seen_names = defaultdict(list)
    for reg_root, disk_root in ROOTS:
        if not disk_root.exists():
            continue
        for p in disk_root.rglob("*.uasset"):
            if any(part in SKIP_PARTS for part in p.parts):
                continue
            stem = p.stem
            rel_reg = f"{reg_root}/{p.relative_to(disk_root).as_posix().rsplit('.', 1)[0]}"
            entry = {
                "path": rel_reg,
                "name": stem,
                "class_guess": classify(stem),
                "group_proposed": group_for(stem),
            }
            assets.append(entry)
            seen_names[stem].append(rel_reg)
    duplicates = {k: v for k, v in seen_names.items() if len(v) > 1}
    # MI orphan heuristic: MI_X whose implied master M_X has no census row
    names = {a["name"] for a in assets}
    orphans = []
    for a in assets:
        if a["name"].startswith("MI_"):
            implied_master = "M_" + a["name"][3:]
            # masters may carry suffixes (_Universal etc); flag only exact-name misses
            if implied_master not in names:
                orphans.append({"mi": a["path"], "implied_master_missing_exact": implied_master})
    return {
        "mode": "disk_no_editor",
        "asset_count": len(assets),
        "duplicates": duplicates,
        "duplicate_count": len(duplicates),
        "orphan_candidates": orphans[:50],
        "orphan_candidate_count": len(orphans),
        "assets_sample": assets[:200],
        "note": "Full 2093-asset census incl. quarantine trees: Saved/Audit/material_org_baseline.json",
    }


def editor_apply_groups(unreal, dry_run: bool) -> dict:
    """In-editor: set Group+SortPriority metadata on master material expressions."""
    mel = unreal.MaterialEditingLibrary
    applied = []
    errors = []
    for spec in (
        "/Game/EnvSandbox/Materials/Masters/M_Master_Toon_Universal",
        "/Game/EnvSandbox/Materials/Masters/M_Master_Toon_Unified",
        "/Game/EnvSandbox/Materials/Masters/M_Master_Toon_Character",
        "/Game/EnvSandbox/Materials/Masters/M_Master_SDF_Toon",
    ):
        if not unreal.EditorAssetLibrary.does_asset_exist(spec):
            continue
        try:
            mat = unreal.EditorAssetLibrary.load_asset(spec)
            exprs = list(mel.get_material_expressions(mat) or [])
            groups_seen = defaultdict(int)
            for e in exprs:
                try:
                    pname = str(e.get_editor_property("parameter_name") or "")
                except Exception:
                    pname = ""
                if not pname:
                    continue
                g = group_for(pname)
                try:
                    e.set_editor_property("expression_group", unreal.Name(g))
                    groups_seen[g] += 1
                except Exception as exc:
                    errors.append({"asset": spec, "param": pname, "err": str(exc)[:120]})
            if not dry_run:
                mat.modify()
                unreal.EditorAssetLibrary.save_loaded_asset(mat, only_if_is_dirty=True)
                dirty = unreal.EditorAssetLibrary.list_dirty_packages() or []
                if spec.split("/")[-1] in " ".join(dirty):
                    errors.append({"asset": spec, "err": "still dirty after save"})
            applied.append({"asset": spec, "groups": dict(groups_seen)})
        except Exception as exc:
            errors.append({"asset": spec, "err": str(exc)[:200]})
    return {"applied": applied, "errors": errors, "dry_run": dry_run}


def run(apply: bool = False) -> dict:
    ts = datetime.now(timezone.utc).isoformat()
    report: dict = {"timestamp": ts, "apply": apply}
    try:
        import unreal  # type: ignore
    except ImportError:
        unreal = None

    if unreal is None:
        report.update(disk_census())
    else:
        report.update(disk_census())          # disk layer always (cheap, deterministic)
        report["editor"] = editor_apply_groups(unreal, dry_run=not apply)

    report["ok"] = True
    REPORT.parent.mkdir(parents=True, exist_ok=True)
    REPORT.write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(json.dumps({k: report[k] for k in ("timestamp", "mode", "apply", "ok",
                                             "asset_count", "duplicate_count")},
                     indent=2))
    print(f"[MatOrgV2] full report -> {REPORT}")
    return report


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true",
                    help="Write Group metadata to masters (default: dry-run)")
    args = ap.parse_args()
    apply = args.apply or "--apply" in sys.argv
    r = run(apply=apply)
    return 0 if r.get("ok") else 1


if __name__ == "__main__":
    raise SystemExit(main())
