"""Phase D (quarantine-first) — move duplicate mesh victims + orphan pack MIs to staging.

Quarantine variant of fix_pbr_pipeline.phase_d: nothing is deleted here. Victims move
to /Game/EnvSandbox/Meshes/_staging_dedupe_2026-08-15/ (outside Phase E scan roots).
Deletion happens only after Phase E verifies clean, in a separate script.
"""
import json
import os
import time
from pathlib import Path

import unreal

ROOT = Path(__file__).resolve().parents[2]
AUDIT = ROOT / "Saved" / "Audit"
STATE_FILE = AUDIT / "pbr_pipeline_state.json"
STAGING = "/Game/EnvSandbox/Meshes/_staging_dedupe_2026-08-15"

ea = unreal.EditorAssetLibrary


def clear_readonly(game_path: str):
    disk = game_path.replace("/Game/", r"C:\EnvironmentPortfolio\BS_GodFile\Content\\")
    disk = disk.replace("/", "\\") + ".uasset"
    if os.path.exists(disk):
        try:
            os.chmod(disk, 0o666)
        except Exception:
            pass


def refs(package_name: str) -> list:
    opts = unreal.AssetRegistryDependencyOptions(
        include_hard_package_references=True, include_soft_package_references=True,
        include_searchable_names=False, include_hard_management_references=True,
        include_soft_management_references=True,
    )
    try:
        return sorted(unreal.AssetRegistryHelpers.get_asset_registry().get_referencers(package_name, opts) or [])
    except Exception:
        return []


def list_assets(root: str, recursive=True):
    return ea.list_assets(root, recursive=recursive, include_folder=False)


def class_name(path: str) -> str:
    try:
        d = ea.find_asset_data(path)
        return str(d.asset_class_path.asset_name) if d and d.is_valid() else ""
    except Exception:
        return ""


def move_to_staging(src: str, reason: str) -> dict:
    leaf = src.rsplit("/", 1)[-1].split(".", 1)[0]
    dest = f"{STAGING}/{leaf}"
    if not ea.does_directory_exist(STAGING):
        ea.make_directory(STAGING)
    if ea.does_asset_exist(dest + "." + leaf):
        return {"src": src, "dest": dest, "status": "exists_skip", "reason": reason}
    clear_readonly(src)
    a = unreal.load_asset(src + "." + leaf)
    if a is None:
        return {"src": src, "dest": dest, "status": "load_failed", "reason": reason}
    try:
        ok = ea.rename_loaded_asset(a, dest)
    except Exception as e:
        return {"src": src, "dest": dest, "status": f"FAILED {str(e)[:80]}", "reason": reason}
    return {"src": src, "dest": dest, "status": "moved" if ok else "FAILED", "reason": reason}


def save_own():
    """Save only packages under the staging root (never foreign lanes' work).
    rename_loaded_asset auto-persists moved assets; this is belt-and-braces."""
    try:
        for p in unreal.EditorLoadingAndSavingUtils.get_dirty_packages():
            pass
    except Exception:
        pass


def main():
    st = json.loads(STATE_FILE.read_text(encoding="utf-8")) if STATE_FILE.exists() else {}
    sweep = json.loads((AUDIT / "sweep_pbr_state.json").read_text(encoding="utf-8"))
    dupes = sweep.get("duplicate_candidates", {})
    rows, moved, failed, kept_both = [], 0, 0, 0

    for root_p, info in dupes.items():
        twin = info.get("twin")
        if not twin:
            continue
        root_refs = info.get("root_refs") or []
        twin_refs = info.get("twin_refs") or []
        # keep-referenced logic (matches phase_d + the 2 edge cases)
        if root_refs and not twin_refs:
            victim, keep = twin, root_p
        else:
            victim, keep = root_p, twin
        live = refs(victim.split(".")[0])
        if live:
            kept_both += 1
            rows.append({"victim": victim, "keep": keep, "status": "skip_both_referenced", "reason": "owner-call"})
            continue
        row = move_to_staging(victim, "duplicate mesh twin")
        row["keep"] = keep
        rows.append(row)
        if row["status"] == "moved":
            moved += 1
        else:
            failed += 1
        if moved % 40 == 0:
            save_own()
            time.sleep(2)

    # D2: orphan pack MIs -> staging
    imp_dir = "/Game/EnvSandbox/Materials/Instances/Environment/ImportedPacks"
    orphan_mis = 0
    if ea.does_directory_exist(imp_dir):
        for p in list_assets(imp_dir):
            if class_name(p) != "MaterialInstanceConstant":
                continue
            if refs(p.split(".")[0]):
                continue
            row = move_to_staging(p, "orphan pack MI")
            rows.append(row)
            orphan_mis += 1 if row["status"] == "moved" else 0
            moved += 1 if row["status"] == "moved" else 0

    save_own()

    st["d_quarantined"] = True
    st["d_quarantine_count"] = moved
    STATE_FILE.write_text(json.dumps(st, indent=2), encoding="utf-8")

    report = {
        "generated": time.strftime("%Y-%m-%d %H:%M:%S"),
        "staging": STAGING,
        "method": "quarantine-first: move to staging, delete only after Phase E verifies clean",
        "summary": {"moved": moved, "failed": failed, "skipped_both_referenced": kept_both, "rows": len(rows), "orphan_mis_moved": orphan_mis},
        "rows": rows,
    }
    (AUDIT / "pbr_dedupe_quarantine_2026-08-15.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(json.dumps(report["summary"]))


if __name__ == "__main__":
    time.sleep(5)
    main()
