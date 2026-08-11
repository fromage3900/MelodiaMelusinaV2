"""Rename static meshes flagged by audit_static_mesh_inventory.py (editor required).

Uses EditorAssetLibrary.rename_asset — updates references when possible.

Run headless:
  python Content/Python/rename_static_meshes.py
  python Content/Python/rename_static_meshes.py --dry-run
"""
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
INVENTORY = PROJECT_ROOT / "Saved" / "Audit" / "static_mesh_inventory.json"
OUT = PROJECT_ROOT / "Saved" / "Audit" / "static_mesh_rename.json"
UE_CMD = Path(r"C:\Program Files\Epic Games\UE_5.8\Engine\Binaries\Win64\UnrealEditor-Cmd.exe")
UPROJECT = PROJECT_ROOT / "BS_GodFile.uproject"

# High-confidence renames (silhouette + naming heuristics)
CONFIDENT: dict[str, str] = {
    "SM_SM_Rock_1": "SM_Greybox_Rock_A",
    "SM_SM_Rock_2": "SM_Greybox_Rock_B",
    "SM_SM_Rock_3": "SM_Greybox_Rock_C",
    "SM_UMesh_PolySphere5": "SM_Sakura_PetalProxy_Sphere",
    "SM_Block_Cube_1": "SM_Greybox_Cube_1m",
    "SM_Block_Wall_4x3": "SM_Greybox_Wall_4x3",
    "SM_Block_Column_05": "SM_Greybox_Column_05",
    "SM_Deco1": "SM_Kit_Ornament_A",
    "SM_Deco2": "SM_Kit_Ornament_B",
    "SM_Deco3": "SM_Kit_Ornament_C",
    "SM_wallhi": "SM_Greybox_Wall_Tall",
    "SM_wallmid": "SM_Greybox_Wall_Mid",
    "SM_wallshort": "SM_Greybox_Wall_Short",
    "SM_wallwindow": "SM_Greybox_Wall_Window",
    "SM_SM_Torii": "SM_Greybox_Torii",
    "SM_SM_TeaHouse": "SM_Greybox_TeaHouse",
    "SM_SM_TeaBridge002": "SM_Greybox_TeaBridge",
    "SM_SM_BuildingBlock01": "SM_Greybox_BuildingBlock_A",
    "SM_SM_BuildingBlock02": "SM_Greybox_BuildingBlock_B",
    "SM_SM_BuildingBlock03": "SM_Greybox_BuildingBlock_C",
    "SM_SM_Gem": "SM_Greybox_Gem",
    "SM_SM_Heart": "SM_Greybox_Heart",
    "SM_SM_Star": "SM_Greybox_Star",
    "SM_SM_Pole": "SM_Greybox_Pole",
    "SM_SM_GreatDodec": "SM_Greybox_GreatDodecahedron",
    "SM_SM_Lissajous": "SM_Greybox_LissajousSculpture",
}


def _confident_rename(stem: str, folder: str) -> str | None:
    if stem in CONFIDENT:
        return CONFIDENT[stem]
    if stem.startswith("SM_wallhi_"):
        suffix = stem.removeprefix("SM_wallhi_").lstrip("_") or "00"
        return f"SM_Greybox_Wall_Tall_{suffix.zfill(2)}"
    if stem.startswith("SM_wallmid_"):
        suffix = stem.removeprefix("SM_wallmid_").lstrip("_") or "00"
        return f"SM_Greybox_Wall_Mid_{suffix.zfill(2)}"
    if stem.startswith("SM_wallshort_"):
        suffix = stem.removeprefix("SM_wallshort_").lstrip("_") or "00"
        return f"SM_Greybox_Wall_Short_{suffix.zfill(2)}"
    if stem.startswith("SM_SM_"):
        tail = stem.removeprefix("SM_SM_")
        return f"SM_Greybox_{tail}"
    if "Greybox_Kit" in folder and stem.startswith("SM_Block_"):
        return stem.replace("SM_Block_", "SM_Greybox_", 1)
    return None


RENAME_ROOTS = ("Greybox_Kit", "EnvSandbox/", "Library/Migrated/")


def _eligible_folder(folder: str) -> bool:
    return any(folder == r.rstrip("/") or folder.startswith(r) for r in RENAME_ROOTS)


def _run_in_ue(dry_run: bool) -> int:
    import unreal

    if not INVENTORY.is_file():
        unreal.log_error(f"Missing inventory: {INVENTORY}")
        return 1

    inv = json.loads(INVENTORY.read_text(encoding="utf-8"))
    report: dict = {"dry_run": dry_run, "renamed": [], "skipped": [], "errors": []}

    for item in inv.get("flagged", []):
        old_path = item["path"]
        stem = item["name"]
        folder = item.get("folder", "")
        if not _eligible_folder(folder):
            continue
        issues = item.get("issues", [])
        if "wallhi_placeholder" not in issues and stem not in CONFIDENT and not any(
            stem.startswith(p) for p in ("SM_wallhi_", "SM_wallmid_", "SM_wallshort_", "SM_SM_")
        ) and stem not in ("SM_UMesh_PolySphere5",) and not stem.startswith("SM_Block_") and not stem.startswith("SM_Deco"):
            continue
        new_stem = _confident_rename(stem, folder) or item.get("suggested_name")
        if not new_stem or new_stem == stem:
            report["skipped"].append({"path": old_path, "reason": "no confident suggestion"})
            continue
        parent = old_path.rsplit("/", 1)[0]
        new_path = f"{parent}/{new_stem}"
        if unreal.EditorAssetLibrary.does_asset_exist(new_path):
            report["skipped"].append({"path": old_path, "reason": f"target exists: {new_path}"})
            continue
        if dry_run:
            report["renamed"].append({"from": old_path, "to": new_path, "dry_run": True})
            continue
        ok = unreal.EditorAssetLibrary.rename_asset(old_path, new_path)
        if ok:
            report["renamed"].append({"from": old_path, "to": new_path})
            unreal.log(f"[SMRename] {old_path} -> {new_path}")
        else:
            report["errors"].append({"path": old_path, "to": new_path, "error": "rename_asset returned false"})

    if not dry_run:
        unreal.EditorLoadingAndSavingUtils.save_dirty_packages(True, True)
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(report, indent=2), encoding="utf-8")
    unreal.log(f"[SMRename] report -> {OUT}")
    print(json.dumps(report, indent=2))
    return 0 if not report["errors"] else 1


def main() -> int:
    dry_run = "--dry-run" in sys.argv
    try:
        import unreal  # noqa: F401
    except ImportError:
        if not UE_CMD.exists():
            print(f"ERROR: {UE_CMD}")
            return 1
        args = " --dry-run" if dry_run else ""
        script = f"{(PROJECT_ROOT / 'Content/Python/rename_static_meshes.py').as_posix()}{args}"
        log = PROJECT_ROOT / "Saved" / "Logs" / "static_mesh_rename.log"
        cmd = [
            str(UE_CMD),
            str(UPROJECT),
            f"-ExecutePythonScript={script}",
            "-stdout",
            "-unattended",
            "-nosplash",
            f"-log={log}",
        ]
        print(f"SM rename -> {log}")
        return subprocess.run(cmd, cwd=str(PROJECT_ROOT)).returncode
    return _run_in_ue(dry_run)


if __name__ == "__main__":
    raise SystemExit(main())
