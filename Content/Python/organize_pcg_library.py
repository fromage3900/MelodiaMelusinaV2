"""Organize EnvSandbox PCG folder tree and emit inventory JSON.

  python Content/Python/organize_pcg_library.py
"""
from __future__ import annotations

import json
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

import pcg_portfolio_standards as std

PROJECT_ROOT = Path(__file__).resolve().parents[2]
REPORT = PROJECT_ROOT / "Saved" / "Audit" / "pcg_library_inventory.json"
README = PROJECT_ROOT / "Content" / "EnvSandbox" / "PCG" / "README.md"
UE_CMD = Path(r"C:\Program Files\Epic Games\UE_5.8\Engine\Binaries\Win64\UnrealEditor-Cmd.exe")
UPROJECT = PROJECT_ROOT / "BS_GodFile.uproject"


def organize(*, move_orphan: bool = True) -> dict:
    import unreal
    import pcg_graph_builder as gb

    gb.ensure_directories()

    moved: list[str] = []
    if move_orphan and unreal.EditorAssetLibrary.does_asset_exist(std.ORPHAN_MEADOW_SCATTER):
        if not unreal.EditorAssetLibrary.does_directory_exist(std.DIR_DEPRECATED):
            unreal.EditorAssetLibrary.make_directory(std.DIR_DEPRECATED)
        dest = std.DEPRECATED_MEADOW
        if unreal.EditorAssetLibrary.does_asset_exist(dest):
            if unreal.EditorAssetLibrary.delete_asset(std.ORPHAN_MEADOW_SCATTER):
                moved.append(f"deleted stale root orphan {std.ORPHAN_MEADOW_SCATTER}")
            else:
                moved.append(f"failed_delete_stale_orphan {std.ORPHAN_MEADOW_SCATTER}")
        else:
            ok = unreal.EditorAssetLibrary.rename_asset(std.ORPHAN_MEADOW_SCATTER, dest)
            if ok:
                moved.append(f"{std.ORPHAN_MEADOW_SCATTER} -> {dest}")

    if move_orphan and unreal.EditorAssetLibrary.does_asset_exist(std.ORPHAN_SAKURA_GROVE):
        sakura_dir = f"{std.DIR_STYLES}/Sakura"
        if not unreal.EditorAssetLibrary.does_directory_exist(sakura_dir):
            unreal.EditorAssetLibrary.make_directory(sakura_dir)
        dest = std.GRAPH_SAKURA_GROVE
        if unreal.EditorAssetLibrary.does_asset_exist(dest):
            if unreal.EditorAssetLibrary.delete_asset(std.ORPHAN_SAKURA_GROVE):
                moved.append(f"deleted stale root orphan {std.ORPHAN_SAKURA_GROVE}")
            else:
                moved.append(f"failed_delete_stale_orphan {std.ORPHAN_SAKURA_GROVE}")
        else:
            ok = unreal.EditorAssetLibrary.rename_asset(std.ORPHAN_SAKURA_GROVE, dest)
            if ok:
                moved.append(f"{std.ORPHAN_SAKURA_GROVE} -> {dest}")

    inventory: list[dict] = []
    ar = unreal.AssetRegistryHelpers.get_asset_registry()
    filt = unreal.ARFilter(package_paths=[std.PCG_ROOT], recursive_paths=True)
    for ad in ar.get_assets(filt) or []:
        path = str(ad.package_name)
        name = path.rsplit("/", 1)[-1]
        parent = path.rsplit("/", 1)[0]
        inventory.append({
            "path": path,
            "name": name,
            "parent": parent,
            "owner": std.PCG_PYTHON_OWNERS.get(path),
            "compliant": parent != std.PCG_ROOT or name in ("PCG", "README"),
        })

    README.parent.mkdir(parents=True, exist_ok=True)
    if not README.exists():
        README.write_text(
            "# EnvSandbox PCG\n\n"
            "Do not add graphs at this root. Use:\n"
            "- `Universal/` — portfolio graphs\n"
            "- `Greybox/` — blockout presets\n"
            "- `Collections/` — SMC_* kits\n"
            "- `Styles/<Style>/` — per-style kits\n"
            "- `_Deprecated/` — retired orphans\n\n"
            "`_PROJECT/PCG` is read-only Melodia reference.\n",
            encoding="utf-8",
        )

    report = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "directories": list(std.ALL_PORTFOLIO_DIRS),
        "moved": moved,
        "inventory": sorted(inventory, key=lambda x: x["path"]),
        "count": len(inventory),
        "non_compliant_root": [i for i in inventory if not i["compliant"]],
    }
    REPORT.parent.mkdir(parents=True, exist_ok=True)
    REPORT.write_text(json.dumps(report, indent=2), encoding="utf-8")
    unreal.log(f"[PCGOrganize] inventory={report['count']} moved={len(moved)} -> {REPORT}")
    return report


def main() -> int:
    try:
        import unreal  # noqa: F401
        organize()
        print(f"ORGANIZE_PCG_OK -> {REPORT}")
        return 0
    except ImportError:
        if not UE_CMD.exists():
            print(f"ERROR: {UE_CMD}")
            return 1
        cmd = [
            str(UE_CMD), str(UPROJECT),
            f"-ExecutePythonScript={(PROJECT_ROOT / 'Content/Python/organize_pcg_library.py').as_posix()}",
            "-stdout", "-unattended", "-nullrhi", "-DisablePlugins=Monolith",
        ]
        return subprocess.run(cmd, cwd=str(PROJECT_ROOT)).returncode


if __name__ == "__main__":
    raise SystemExit(main())
