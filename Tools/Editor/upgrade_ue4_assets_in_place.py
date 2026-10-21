"""
Upgrade a folder of UE4-sourced packages to UE 5.8 in place, one asset at a time.

Why this exists: the Enchanted Interiors pack (Kitbash3D, UE4.26+) ships packages
with no engine version stamp ("Asset has been saved with empty engine version"),
so UE5 re-runs the upgrade path and rebuilds mesh data on every load. Doing that
for 1,696 meshes inside the editor exhausted the Windows commit limit
("Ran out of memory allocating 532.8 MiB ... The paging file is too small",
stack UnrealEditor_QuadricMeshReduction) and crash-looped the editor three times
on 2026-10-21. Two single meshes (KB3D_ECI_IntNecromancersLair_A_NicheA/_NicheC)
each need 7,691 MB to build.

This script does the same work headlessly, one asset at a time, so peak memory is
bounded by the largest single asset rather than the whole pack:

  * assets are processed in ASCENDING file size, so the cheap ones are stamped
    first and the monsters are reached last (a monster that still OOMs costs
    only itself, not the batch)
  * assets above --skip-mb are skipped and reported for a separate decision
  * each asset is loaded, re-saved (which writes a UE 5.8 package and populates
    the Nanite/DDC data), then released

Run:
    UnrealEditor-Cmd <proj> -run=pythonscript -script=<this file> -unattended -nullrhi
Optionally set ECV_FOLDER (default /Game/EnchantedInteriors) and ECV_SKIP_MB (default 300).
Writes Saved/Audit/ue4_asset_upgrade.json
"""

from __future__ import annotations

import json
import os
from pathlib import Path

import unreal

# ECV_PROJECT_ROOT lets the same script run against the scratch project
# (C:\EnvironmentPortfolio\Staging\ECI_scratch) so the upgrade does not have to
# run inside the live project folder.
ROOT = Path(os.environ.get("ECV_PROJECT_ROOT", str(Path(__file__).resolve().parents[2])))
OUT = Path(os.environ.get("ECV_OUT", str(ROOT / "Saved" / "Audit" / "ue4_asset_upgrade.json")))

FOLDER = os.environ.get("ECV_FOLDER", "/Game/EnchantedInteriors")
SKIP_MB = float(os.environ.get("ECV_SKIP_MB", "300"))
SKIP_DIRS = [d for d in os.environ.get("ECV_SKIP_DIRS", "Materials").split(",") if d]

LINES = []


def log(m):
    LINES.append(str(m))
    unreal.log("[UPG] " + str(m))
    try:
        OUT.parent.mkdir(parents=True, exist_ok=True)
        OUT.write_text("\n".join(LINES), encoding="utf-8")
    except Exception:
        pass


def _local_size(package_path: str) -> int:
    rel = package_path.replace("/Game/", "")
    p = ROOT / "Content" / Path(rel)
    try:
        return p.stat().st_size
    except Exception:
        return 0


def _size_map():
    """Map /Game/... package path -> bytes on disk.

    AssetData carries no file size in Python, so the local Content tree is walked
    once. (The earlier attempt read the size through AssetData and always got 0,
    which silently disabled the --skip-mb guard.)
    """
    content = ROOT / "Content"
    out = {}
    if not content.exists():
        return out
    for p in content.rglob("*.uasset"):
        rel = "/" + p.relative_to(content).as_posix()[:-len(".uasset")]
        out[rel] = p.stat().st_size
    for p in content.rglob("*.umap"):
        rel = "/" + p.relative_to(content).as_posix()[:-len(".umap")]
        out[rel] = p.stat().st_size
    return out


def main():
    report = {"generated": "2026-10-21", "folder": FOLDER, "skip_mb": SKIP_MB,
              "root": str(ROOT), "processed": [], "skipped": [], "failed": []}
    ar = unreal.AssetRegistryHelpers.get_asset_registry()
    sizes = _size_map()
    log(f"size map: {len(sizes)} packages on disk under {ROOT / 'Content'}")

    assets = []
    for a in ar.get_assets_by_path(FOLDER, recursive=True):
        pkg = str(a.package_name)
        if any(f"/{d}/" in pkg for d in SKIP_DIRS):
            continue
        size = sizes.get(pkg, 0)
        assets.append((size, pkg, str(a.asset_name), str(a.asset_class_path.asset_name)))
    log(f"packages to process: {len(assets)} (skipping dirs: {SKIP_DIRS})")

    assets.sort(key=lambda t: t[0])          # ascending: cheap first, monsters last
    total_bytes = sum(a[0] for a in assets)
    log(f"total on disk: {total_bytes/1024/1024:.0f} MB")

    for size, pkg, name, cls in assets:
        if size / 1024 / 1024 > SKIP_MB:
            report["skipped"].append({"package": pkg, "mb": round(size / 1024 / 1024, 1),
                                      "reason": f"above --skip-mb ({SKIP_MB})"})
            log(f"SKIP {name} ({size/1024/1024:.0f} MB > {SKIP_MB} MB)")
            continue
        try:
            obj = unreal.EditorAssetLibrary.load_asset(pkg)
            if obj is None:
                report["failed"].append({"package": pkg, "error": "load returned None"})
                log(f"FAIL load {name}")
                continue
            saved = unreal.EditorAssetLibrary.save_asset(pkg, only_if_is_dirty=False)
            report["processed"].append({"package": pkg, "mb": round(size / 1024 / 1024, 1),
                                        "saved": bool(saved), "class": cls})
            if len(report["processed"]) % 25 == 0:
                log(f"progress: {len(report['processed'])} saved, "
                    f"{len(report['skipped'])} skipped, {len(report['failed'])} failed")
        except Exception as exc:
            report["failed"].append({"package": pkg, "error": f"{type(exc).__name__}: {exc}"})
            log(f"FAIL {name}: {exc}")
        try:
            unreal.SystemLibrary.collect_garbage()
        except Exception:
            pass

    report["summary"] = {
        "processed": len(report["processed"]),
        "skipped": len(report["skipped"]),
        "failed": len(report["failed"]),
        "bytes_processed_mb": round(sum(p["mb"] for p in report["processed"]), 1),
    }
    OUT.write_text(json.dumps(report, indent=2, default=str), encoding="utf-8")
    log(f"DONE {report['summary']} -> {OUT}")
    return 0


if __name__ == "__main__":
    main()
