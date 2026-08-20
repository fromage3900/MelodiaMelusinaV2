"""Move experimental SDF masters into Masters/SDF/ (redirector-safe reorg).

The 54 M_SDF_* / M_Master_SDF_* masters sit in the production Masters/ folder
alongside the 4 canonical families. Per MATERIAL_SYSTEM_REVIEW, separate the
experimental SDF family so production vs research is obvious. UE's
rename_asset creates redirectors so the 173 SDF instances keep resolving.

Also moves landscape quarantine/backup/work masters (M_Master_Toon_Landscape_HeightBlend_*_20260729,
_*_BACKUP_*, _*_QUARANTINE_*, _*_AUTHORED_RESTORED_*, _*_LIVE_RENDER_REPAIR_*,
_*_SAFE_FALLBACK_*, _*_TRIPLANAR_WORK_*, _*_LIVING_STORYBOOK_*) into _Scratch/.

Run in the UE editor (Monolith run_python): reorg_material_folders.main()
Writes: Saved/Audit/material_folder_reorg_2026-08-14.json
"""
from __future__ import annotations

import json
import os
from pathlib import Path

import unreal

MASTERS = "/Game/EnvSandbox/Materials/Masters"
SDF_DEST = f"{MASTERS}/SDF"
SCRATCH = "/Game/EnvSandbox/Materials/_Scratch"
OUT = Path(__file__).resolve().parents[2] / "Saved" / "Audit" / "material_folder_reorg_2026-08-14.json"

SDF_PREFIXES = ("M_SDF_", "M_Master_SDF_", "M_Toon_SDF", "M_HybridStone_SDF",
                "M_HybridLandscape_MooaToonSDF")
LANDSCAPE_QUARANTINE = ("_20260729", "_BACKUP_", "_QUARANTINE_", "_AUTHORED_RESTORED_",
                        "_LIVE_RENDER_REPAIR_", "_SAFE_FALLBACK_", "_TRIPLANAR_WORK_",
                        "_LIVING_STORYBOOK_")


def clear_readonly(game_path: str):
    """LFS checkout trap: package must be writable before rename."""
    disk = game_path.replace("/Game/", r"C:\EnvironmentPortfolio\BS_GodFile\Content\\")
    disk = disk.replace("/", "\\") + ".uasset"
    if os.path.exists(disk):
        try:
            os.chmod(disk, 0o666)
        except Exception:
            pass


def main():
    assets = unreal.EditorAssetLibrary.list_assets(MASTERS, recursive=False)
    rows = []
    moved = 0
    for p in assets:
        leaf = p.rsplit("/", 1)[-1].split(".", 1)[0]
        is_sdf = leaf.startswith(SDF_PREFIXES)
        is_lq = any(tok in leaf for tok in LANDSCAPE_QUARANTINE)
        if not (is_sdf or is_lq):
            continue
        dest_dir = SDF_DEST if is_sdf else SCRATCH
        if not unreal.EditorAssetLibrary.does_directory_exist(dest_dir):
            unreal.EditorAssetLibrary.make_directory(dest_dir)
        dest = f"{dest_dir}/{leaf}"
        if unreal.EditorAssetLibrary.does_asset_exist(dest):
            rows.append({"from": p, "to": dest, "status": "exists"})
            continue
        clear_readonly(p)
        a = unreal.load_asset(p)
        if a is None:
            rows.append({"from": p, "to": dest, "status": "load_failed"})
            continue
        ok = unreal.EditorAssetLibrary.rename_loaded_asset(a, dest)
        if ok:
            moved += 1
            rows.append({"from": p, "to": dest, "status": "moved"})
        else:
            rows.append({"from": p, "to": dest, "status": "FAILED"})
    payload = {
        "generated": "2026-08-14",
        "summary": {"moved": moved, "total": len(rows)},
        "rows": rows,
    }
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    unreal.log(f"[reorg] moved={moved} total={len(rows)}")
    print(json.dumps(payload["summary"]))
    return payload


if __name__ == "__main__":
    main()
