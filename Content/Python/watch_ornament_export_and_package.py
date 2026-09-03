"""Watch for kitbash FBX export completion, then package ZIP (and optionally UE-import).

Run while Blender bake / UE export finishes:
  python Content/Python/watch_ornament_export_and_package.py
  python Content/Python/watch_ornament_export_and_package.py --once
  python Content/Python/watch_ornament_export_and_package.py --also-import
  python Content/Python/watch_ornament_export_and_package.py --also-import --prep

Chain (SSOT):
  Blender bake → KitbashExport → import_ornament_fbx → package ZIP
"""
from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
import time
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
MANIFEST = PROJECT_ROOT / "Saved" / "Audit" / "kitbash_export_manifest.json"
FBX_DIR = PROJECT_ROOT / "KitbashExport" / "OrnamentalMeshes"
EXPECTED = 15
UE_CMD = Path(r"C:\Program Files\Epic Games\UE_5.8\Engine\Binaries\Win64\UnrealEditor-Cmd.exe")
UPROJECT = PROJECT_ROOT / "BS_GodFile.uproject"
IMPORT_SCRIPT = PROJECT_ROOT / "Content" / "Python" / "import_ornament_fbx.py"


def _status() -> dict:
    fbx_count = len(list(FBX_DIR.glob("*.fbx"))) if FBX_DIR.is_dir() else 0
    manifest_ok = 0
    if MANIFEST.is_file():
        data = json.loads(MANIFEST.read_text(encoding="utf-8"))
        entries = data.get("meshes", [])
        manifest_ok = sum(1 for e in entries if e.get("fbx_exported"))
    return {
        "fbx_files": fbx_count,
        "manifest_exported": manifest_ok,
        "ready": fbx_count >= EXPECTED or manifest_ok >= EXPECTED,
    }


def _package() -> int:
    from package_ornament_kitbash import build_product_folder

    build_product_folder(make_zip=True)
    return 0


def _try_ue_import(*, prep: bool) -> int:
    """Kick UnrealEditor-Cmd to run import_ornament_fbx.py, or print manual line."""
    py_line = "py Content/Python/import_ornament_fbx.py"
    if prep:
        py_line += " --prep"

    if not IMPORT_SCRIPT.is_file():
        print(f"[watch] FATAL missing {IMPORT_SCRIPT}")
        return 2

    if not UE_CMD.is_file() or not UPROJECT.is_file():
        print("[watch] UE Cmd / uproject not found — run import manually in editor:")
        print(f"  {py_line}")
        return 0

    script = str(IMPORT_SCRIPT).replace("\\", "/")
    cmd = [
        str(UE_CMD),
        str(UPROJECT),
        f"-ExecutePythonScript={script}",
        "-stdout",
        "-unattended",
        "-nullrhi",
        "-DisablePlugins=Monolith",
    ]
    # Pass flags via env — import_ornament_fbx reads argv; Cmd may not forward --prep.
    # Write a tiny runner when prep is needed.
    if prep:
        runner = PROJECT_ROOT / "Saved" / "Audit" / "_run_ornament_import_prep.py"
        runner.parent.mkdir(parents=True, exist_ok=True)
        runner.write_text(
            "import import_ornament_fbx as m\n"
            "raise SystemExit(m.main(['--prep']))\n",
            encoding="utf-8",
        )
        cmd[2] = f"-ExecutePythonScript={str(runner).replace(chr(92), '/')}"

    print(f"[watch] UE import: {' '.join(cmd[:3])} ...")
    try:
        proc = subprocess.run(cmd, cwd=str(PROJECT_ROOT), check=False)
        if proc.returncode != 0:
            print(f"[watch] UE import exit={proc.returncode} — try in-editor:")
            print(f"  {py_line}")
            return proc.returncode
        print("[watch] UE import finished")
        return 0
    except OSError as exc:
        print(f"[watch] UE launch failed: {exc}")
        print(f"  Manual: {py_line}")
        return 0


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Watch ornament FBX export then package (+ optional UE import)"
    )
    parser.add_argument("--once", action="store_true", help="Check once and exit")
    parser.add_argument("--interval", type=int, default=45, help="Seconds between polls")
    parser.add_argument("--force", action="store_true", help="Package even if incomplete")
    parser.add_argument(
        "--also-import",
        action="store_true",
        help="After ready: import FBXs into /Game/EnvSandbox/Meshes/Ornament via UE Cmd",
    )
    parser.add_argument(
        "--prep",
        action="store_true",
        help="With --also-import: re-apply LODs/collision/Base+Trim after import",
    )
    args = parser.parse_args()

    print(f"[watch] Expecting {EXPECTED} FBX under {FBX_DIR}")
    print(f"[watch] Manifest: {MANIFEST}")
    print("[watch] Chain: Blender bake -> KitbashExport -> import_ornament_fbx -> package ZIP")

    while True:
        st = _status()
        print(
            f"[watch] FBX files={st['fbx_files']}/{EXPECTED} "
            f"manifest={st['manifest_exported']}/{EXPECTED} ready={st['ready']}"
        )
        if st["ready"] or args.force:
            if args.also_import:
                code = _try_ue_import(prep=args.prep)
                if code not in (0, None):
                    print(f"[watch] import warning code={code} — continuing to package")
            print("[watch] Packaging ZIP...")
            return _package()
        if args.once:
            print("[watch] Not ready yet. Re-run after Blender bake / UE export.")
            return 2
        time.sleep(max(5, args.interval))


if __name__ == "__main__":
    raise SystemExit(main())
