#!/usr/bin/env python
"""List the in-theme Poitou mesh set with measured bounds.

    UnrealEditor-Cmd.exe BS_GodFile.uproject -run=pythonscript -script=... -unattended -nullrhi -stdout

This is the replacement surface for the Kenney pack: what the project actually
authored for Poitou, and how big each piece really is. The bounds are what the
HDA's instance scale divisors have to be derived from.
"""
from __future__ import annotations

import json
import os

import unreal

OUT = r"C:\EnvironmentPortfolio\BS_GodFile\Saved\Audit\AssetGraveyard_20261021\intheme_meshes.json"
ROOTS = [
    "/Game/Melodia/Meshes/Poitou",
    "/Game/EnvSandbox/Meshes/Poitou",
    "/Game/EnvSandbox/Tree",
    "/Game/Megascans/3D_Assets/MossyTree",
]


def main():
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    ar = unreal.AssetRegistryHelpers.get_asset_registry()
    rows = []
    for root in ROOTS:
        for asset in ar.get_assets_by_path(root, True):
            if str(asset.asset_class_path.asset_name) != "StaticMesh":
                continue
            pkg = str(asset.package_name)
            if any(r["package"] == pkg for r in rows):
                continue
            row = {"package": pkg, "asset_name": str(asset.asset_name)}
            obj = unreal.load_asset(pkg)
            if obj is not None:
                try:
                    b = obj.get_bounding_box()
                    s = b.max - b.min
                    row["size_cm"] = [round(s.x, 2), round(s.y, 2), round(s.z, 2)]
                except Exception:
                    pass
                try:
                    mats = obj.get_editor_property("static_materials")
                    row["materials"] = [str(m.material_interface) for m in mats if m.material_interface]
                except Exception:
                    pass
            rows.append(row)
            unreal.log("[intheme] %-72s %s" % (pkg, row.get("size_cm")))

    with open(OUT, "w", encoding="utf-8") as fh:
        json.dump({"meshes": rows}, fh, indent=1)
    unreal.log("[intheme] %d in-theme meshes -> %s" % (len(rows), OUT))


main()
