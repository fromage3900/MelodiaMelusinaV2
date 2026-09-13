# -*- coding: utf-8 -*-
"""Starskiff updated-bake texture import (2026-09-10/12 bakes).

One-shot contract: Saved/Audit/sea_above/skiff_MK3/STARSKIFF_BAKE_IMPORT_RUNBOOK_2026-09-10.md

Sources  : Saved/Audit/melusina_lookdev/houdini_variants/T_Starskiff_*.png (2048, seed 20260904)
Dest     : /Game/Melodia/SeaAbove/Textures   (PR #188 consolidated path -- NOT the 09-04 Clothes base)
Flags    : per-suffix table below, straight from the runbook.
Safety   : imports/refreshes textures only. No master material edits, no deletes.

Run via Monolith:
  python Tools/ue_run_python.py --file Saved/_tmp_starskiff_import.py --timeout 900
"""
from __future__ import annotations

import json
import os
import sys
import traceback

import unreal

PROJECT = "C:/EnvironmentPortfolio/BS_GodFile"
SRC_DIR = PROJECT + "/Saved/Audit/melusina_lookdev/houdini_variants"
DEST = "/Game/Melodia/SeaAbove/Textures"
RECEIPT = PROJECT + "/Saved/Audit/melusina_lookdev/starskiff_bake_import_2026-09-12.json"

# suffix -> (srgb, compression, lod_group)   runbook table, verbatim
FLAGS = [
    ("_BaseColor", True, "TC_Default", "World"),
    ("_Normal", False, "TC_Normalmap", "World"),
    ("_Roughness", False, "TC_Default", "World"),
    ("_Height", False, "TC_Default", "World"),
    ("_Emission", False, "TC_Masks", "Effects"),
    ("_Mask", False, "TC_Masks", "World"),
]

COMP = {
    "TC_Default": unreal.TextureCompressionSettings.TC_DEFAULT,
    "TC_Normalmap": unreal.TextureCompressionSettings.TC_NORMALMAP,
    "TC_Masks": unreal.TextureCompressionSettings.TC_MASKS,
}
GROUP = {
    "World": unreal.TextureGroup.TEXTUREGROUP_WORLD,
    "Effects": unreal.TextureGroup.TEXTUREGROUP_EFFECTS,
}


def flags_for(name: str):
    """Longest-suffix-first so _Hull_Regal_Normal beats nothing and _BaseColor beats _Color."""
    for suffix, srgb, comp, group in FLAGS:
        if name.endswith(suffix):
            return srgb, comp, group
    return None


def discover():
    """Exactly the files the two fresh manifests name -- not every T_Starskiff_*.png in the dir
    (older passes left others there; importing those would silently re-stamp stale art)."""
    manifests = [
        SRC_DIR + "/refined_starskiff_wood_manifest.json",
        SRC_DIR + "/refined_starskiff_regal_manifest.json",
    ]
    names = []
    for mf in manifests:
        with open(mf, encoding="utf-8") as fh:
            data = json.load(fh)
        for entry in data.get("files", []):
            names.append(entry["name"])

    out = []
    for name in names:
        path = SRC_DIR + "/" + name + ".png"
        if not os.path.isfile(path):
            print("MANIFEST FILE MISSING ON DISK: {}".format(path))
            continue
        f = flags_for(name)
        if f is None:
            print("UNCLASSIFIED (skipped): {}".format(name))
            continue
        srgb, comp, group = f
        out.append(
            {
                "name": name,
                "src": path,
                "mtime": os.path.getmtime(path),
                "srgb": srgb,
                "compression": comp,
                "group": group,
            }
        )
    return out


def readback(asset_path):
    a = unreal.EditorAssetLibrary.load_asset(asset_path)
    if not a:
        return {"loaded": False}
    def get(prop, default=None):
        try:
            return a.get_editor_property(prop)
        except Exception:
            return default
    size = [None, None]
    try:
        size = [int(a.blueprint_get_size_x()), int(a.blueprint_get_size_y())]
    except Exception:
        pass
    return {
        "loaded": True,
        "srgb": bool(get("srgb", False)),
        "compression": str(get("compression_settings")),
        "lod_group": str(get("lod_group")),
        "size": size,
        "flip_green_channel": get("flip_green_channel"),
    }


def main(dry_run: bool = False) -> int:
    items = discover()
    print("discovered {} staged bakes in {}".format(len(items), SRC_DIR))

    if dry_run:
        for it in items:
            exists = unreal.EditorAssetLibrary.does_asset_exist(DEST + "/" + it["name"])
            print("  {:<38} srgb={:<5} {:<12} {:<7} exists={}".format(
                it["name"], str(it["srgb"]), it["compression"], it["group"], exists))
        return 0

    if not unreal.EditorAssetLibrary.does_directory_exist(DEST):
        unreal.EditorAssetLibrary.make_directory(DEST)

    tools = unreal.AssetToolsHelpers.get_asset_tools()
    report = {"schema": "melodia.starskiff_bake_import.v1", "dest": DEST, "results": []}

    for it in items:
        row = dict(it)
        row.pop("mtime", None)
        dest_path = DEST + "/" + it["name"]
        row["existed_before"] = unreal.EditorAssetLibrary.does_asset_exist(dest_path)
        try:
            task = unreal.AssetImportTask()
            task.filename = it["src"]
            task.destination_path = DEST
            task.destination_name = it["name"]
            task.replace_existing = True
            task.replace_existing_settings = True
            task.automated = True
            task.save = False          # saved below, after the texture properties are set
            task.factory = unreal.TextureFactory()
            # UE 5.8: AssetImportTask carries NO srgb/compression/lod_group fields
            # (the old import_starskiff_v2.py set them and raised AttributeError every time).
            # Texture properties are set on the asset itself, then saved.
            tools.import_asset_tasks([task])
            exists = unreal.EditorAssetLibrary.does_asset_exist(dest_path)
            row["import_ok"] = bool(exists)
            if exists:
                tex = unreal.EditorAssetLibrary.load_asset(dest_path)
                tex.set_editor_property("srgb", it["srgb"])
                tex.set_editor_property("compression_settings", COMP[it["compression"]])
                tex.set_editor_property("lod_group", GROUP[it["group"]])
                saved = unreal.EditorAssetLibrary.save_loaded_asset(tex, False)
                row["saved"] = bool(saved)
                row["readback"] = readback(dest_path)
            else:
                row["readback"] = {}
            rb = row["readback"]
            row["verified"] = bool(
                exists
                and rb.get("srgb") == it["srgb"]
                and it["compression"][3:].upper() in (rb.get("compression") or "").upper()
            )
        except Exception as exc:  # noqa: BLE001
            row["import_ok"] = False
            row["error"] = "{}: {}".format(type(exc).__name__, exc)
            traceback.print_exc()
        print("{} {:<40} ok={} verified={}".format(
            "REFRESH" if row["existed_before"] else "NEW    ",
            it["name"], row.get("import_ok"), row.get("verified")))
        report["results"].append(row)

    report["imported"] = sum(1 for r in report["results"] if r.get("import_ok"))
    report["verified"] = sum(1 for r in report["results"] if r.get("verified"))
    report["total"] = len(report["results"])
    with open(RECEIPT, "w", encoding="utf-8") as fh:
        json.dump(report, fh, indent=2)
    print("RECEIPT {} imported={}/{} verified={}".format(
        RECEIPT, report["imported"], report["total"], report["verified"]))

    dirty = unreal.EditorAssetLibrary.list_assets(DEST, recursive=False)
    print("dest asset count: {}".format(len(dirty)))
    return 0


if __name__ == "__main__":
    _dry = "--apply" not in sys.argv
    print("MODE {}".format("DRY-RUN" if _dry else "APPLY"))
    sys.exit(main(dry_run=_dry))
