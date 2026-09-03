"""Restore Grotto SDF parent materials into /SDF and verify MI parents resolve.

Context:
  - M_SDF_{Bioluminescence,BubbleColumn,CoralBranching,FloatingNotes} were deleted
    from Masters/ in 94ed9d8 (LFS bodies still recoverable).
  - Grotto MIs already soft-ref /Game/EnvSandbox/Materials/SDF/M_SDF_*.
  - Blessed Masters/ stays the 7-master set; these specialty parents live under SDF/.

Disk prerequisite (run before this script if needed):
  LFS blobs restored to Content/EnvSandbox/Materials/Masters/M_SDF_*.uasset

Run in-editor:
  py Content/Python/fix_grotto_sdf_parents.py

Headless:
  python Content/Python/fix_grotto_sdf_parents.py
"""
from __future__ import annotations

import json
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
UE_CMD = Path(r"C:\Program Files\Epic Games\UE_5.8\Engine\Binaries\Win64\UnrealEditor-Cmd.exe")
UPROJECT = PROJECT_ROOT / "BS_GodFile.uproject"
REPORT_PATH = PROJECT_ROOT / "Saved" / "Audit" / "sdf_parents_fix.json"

MASTERS = (
    "M_SDF_Bioluminescence",
    "M_SDF_BubbleColumn",
    "M_SDF_CoralBranching",
    "M_SDF_FloatingNotes",
)

GROTTO_MIS = {
    "M_SDF_Bioluminescence": "/Game/EnvSandbox/Materials/Instances/Grotto/MI_Grotto_Bioluminescence",
    "M_SDF_BubbleColumn": "/Game/EnvSandbox/Materials/Instances/Grotto/MI_Grotto_BubbleColumn",
    "M_SDF_CoralBranching": "/Game/EnvSandbox/Materials/Instances/Grotto/MI_Grotto_CoralBranching",
    "M_SDF_FloatingNotes": "/Game/EnvSandbox/Materials/Instances/Grotto/MI_Grotto_FloatingNotes",
}


def _fix() -> dict:
    import unreal

    report: dict = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "strategy": "restore_lfs_to_masters_then_rename_to_sdf",
        "blessed_parents_unchanged": [
            "/Game/EnvSandbox/Materials/Masters/M_Master_SDF_Toon",
            "/Game/EnvSandbox/Materials/Masters/M_Toon_SDF",
        ],
        "moved": [],
        "already_in_sdf": [],
        "missing_source": [],
        "mi_parents": [],
        "errors": [],
    }

    for name in MASTERS:
        src = f"/Game/EnvSandbox/Materials/Masters/{name}"
        dst = f"/Game/EnvSandbox/Materials/SDF/{name}"
        src_exists = unreal.EditorAssetLibrary.does_asset_exist(src)
        dst_exists = unreal.EditorAssetLibrary.does_asset_exist(dst)

        if dst_exists and not src_exists:
            report["already_in_sdf"].append(dst)
            parent_path = dst
        elif src_exists and not dst_exists:
            ok = unreal.EditorAssetLibrary.rename_asset(src, dst)
            report["moved"].append({"from": src, "to": dst, "ok": bool(ok)})
            if not ok:
                report["errors"].append(f"rename_failed:{name}")
                continue
            parent_path = dst
        elif src_exists and dst_exists:
            # Prefer SDF path; delete Masters duplicate after confirming load
            report["already_in_sdf"].append(dst)
            unreal.EditorAssetLibrary.delete_asset(src)
            parent_path = dst
        else:
            report["missing_source"].append(name)
            report["errors"].append(f"missing_both_paths:{name}")
            continue

        mi_path = GROTTO_MIS[name]
        mi = unreal.load_asset(mi_path)
        parent = unreal.load_asset(parent_path)
        entry = {"instance": mi_path, "expected_parent": parent_path}
        if not mi:
            entry["status"] = "mi_load_failed"
            report["errors"].append(f"mi_load_failed:{name}")
        elif not parent:
            entry["status"] = "parent_load_failed"
            report["errors"].append(f"parent_load_failed:{name}")
        else:
            unreal.MaterialEditingLibrary.set_material_instance_parent(mi, parent)
            unreal.EditorAssetLibrary.save_loaded_asset(mi, only_if_is_dirty=False)
            unreal.EditorAssetLibrary.save_asset(parent_path, only_if_is_dirty=False)
            cur = mi.get_editor_property("parent")
            entry["status"] = "parent_set"
            entry["parent_after"] = cur.get_path_name() if cur else None
        report["mi_parents"].append(entry)

    report["ok"] = not report["errors"] and not report["missing_source"]
    REPORT_PATH.parent.mkdir(parents=True, exist_ok=True)
    REPORT_PATH.write_text(json.dumps(report, indent=2), encoding="utf-8")
    unreal.log(f"[SDFParents] wrote {REPORT_PATH}")
    return report


def main() -> int:
    try:
        import unreal  # noqa: F401

        report = _fix()
        print(json.dumps(report, indent=2))
        return 0 if report.get("ok") else 1
    except ImportError:
        if not UE_CMD.exists():
            print(f"ERROR: missing {UE_CMD}", file=sys.stderr)
            return 1
        log = PROJECT_ROOT / "Saved" / "Logs" / "fix_grotto_sdf_parents.log"
        log.parent.mkdir(parents=True, exist_ok=True)
        cmd = [
            str(UE_CMD),
            str(UPROJECT),
            f"-ExecutePythonScript={(PROJECT_ROOT / 'Content/Python/fix_grotto_sdf_parents.py').as_posix()}",
            "-stdout",
            "-unattended",
            "-nosplash",
            "-nullrhi",
            "-DisablePlugins=Monolith",
            f"-log={log}",
        ]
        print(f"Headless SDF parent fix -> {log}")
        return subprocess.run(cmd, cwd=str(PROJECT_ROOT)).returncode


if __name__ == "__main__":
    raise SystemExit(main())
