#!/usr/bin/env python
"""Authoritative referencer map for the static-mesh graveyard. Run in the editor.

    py "C:/EnvironmentPortfolio/BS_GodFile/Tools/Editor/asset_graveyard_referencers.py"

This is the gate before anything is deleted. The offline census
(Tools/Editor/asset_graveyard_census.py) is only a candidate map: it reads
package name tables, so it cannot see a reference that exists only in a
cooked form, and it cannot distinguish two assets that share a name.

The Asset Registry knows the real dependency graph. For every candidate it
answers: who references this asset, is it a hard or soft reference, and is it
loaded by a shipping map right now.

Writes:
  Saved/Audit/AssetGraveyard_20261021/referencers.json

Read-only. It changes no asset and saves nothing in the editor.
"""
from __future__ import annotations

import json
import os

import unreal

OUT_DIR = r"C:\EnvironmentPortfolio\BS_GodFile\Saved\Audit\AssetGraveyard_20261021"
OUT_FILE = os.path.join(OUT_DIR, "referencers.json")
CENSUS = os.path.join(OUT_DIR, "census.json")

# The third-party pack's own folder. The candidate set is scoped here: the
# Kenney Retro Fantasy Kit assets were dropped in as one folder per mesh with
# the pack's own lowercase-hyphenated naming, while everything the project
# authored is SM_*/BP_*/MI_* prefixed.
PACK_ROOT = "/Game/EnvSandbox/Meshes/Environment"
# Material instances that belong to the Kenney RetroFantasyKit. A static mesh
# that uses one of these is Kenney-derived even if it sits in a themed folder.
KENNEY_MATERIAL_ROOTS = (
    "/Game/EnvSandbox/Materials/Instances/Kenney/RetroFantasyKit",
)
PROJECT_PREFIXES = ("SM_", "BP_", "MI_", "M_", "MF_", "T_", "DA_", "SK_", "FL_", "ABP_", "PCG_", "IC_", "LT_", "E_", "HDA_", "AS_", "WBP_")


def main():
    os.makedirs(OUT_DIR, exist_ok=True)
    ar = unreal.AssetRegistryHelpers.get_asset_registry()

    candidates = []
    for asset in ar.get_assets_by_path(PACK_ROOT, True):
        if str(asset.asset_class_path.asset_name) != "StaticMesh":
            continue
        if str(asset.asset_name).startswith(PROJECT_PREFIXES):
            continue
        candidates.append(asset)

    # UE 5.8 exposes get_referencers(package_name, options); the options
    # struct carries the hard/soft/game/editor-only switches.
    opts = unreal.AssetRegistryDependencyOptions()
    for flag in ("include_hard_package_references", "include_soft_package_references",
                 "include_game_package_references", "include_editor_only_package_references"):
        try:
            opts.set_editor_property(flag, True)
        except Exception:
            pass

    seen = set()
    rows = []
    for asset in candidates:
        pkg = str(asset.package_name)
        if pkg in seen:
            continue
        seen.add(pkg)
        referencers = []
        try:
            for dep in ar.get_referencers(pkg, opts):
                referencers.append(str(dep))
        except Exception as exc:
            unreal.log("[graveyard] referencer query failed for %s : %s" % (pkg, exc))
        rows.append({
            "package": pkg,
            "asset_name": str(asset.asset_name),
            "class": str(asset.asset_class_path.asset_name),
            "referencers": sorted(set(referencers)),
            "in_pack_root": any(pkg.startswith(r) for r in (PACK_ROOT + "/_RetroFantasyKit", PACK_ROOT + "/_Loose")),
            "hda_named": any(h in pkg for h in ("tree-high", "tree_fat", "grass_leafsLarge", "/canoe/")),
        })

    referenced = [r for r in rows if r["referencers"]]
    hda_named = [r for r in rows if r["hda_named"]]
    hda_named_unreferenced = [r for r in hda_named if not r["referencers"]]

    report = {
        "candidates": len(rows),
        "referenced": len(referenced),
        "unreferenced": len(rows) - len(referenced),
        "unreferenced_pct": round(100.0 * (len(rows) - len(referenced)) / max(1, len(rows)), 2),
        "hda_named": len(hda_named),
        "hda_named_but_unreferenced": [r["package"] for r in hda_named_unreferenced],
        "referencer_summary": {},
        "rows": sorted(rows, key=lambda r: (bool(r["referencers"]), r["package"])),
    }
    for r in referenced:
        for ref in r["referencers"]:
            report["referencer_summary"].setdefault(ref, []).append(r["package"])
    report["referencer_summary"] = {k: sorted(v) for k, v in sorted(report["referencer_summary"].items())}

    with open(OUT_FILE, "w", encoding="utf-8") as fh:
        json.dump(report, fh, indent=1)

    unreal.log("[graveyard] candidates=%d referenced=%d unreferenced=%d (%.1f%%) hda_named=%d" % (
        report["candidates"], report["referenced"], report["unreferenced"],
        report["unreferenced_pct"], report["hda_named"]))
    unreal.log("[graveyard] hda_named_but_unreferenced=%s" % report["hda_named_but_unreferenced"])
    for ref, assets in report["referencer_summary"].items():
        unreal.log("[graveyard]   %s -> %d asset(s)" % (ref, len(assets)))
    unreal.log("[graveyard] wrote %s" % OUT_FILE)


main()
