#!/usr/bin/env python
"""Measure the real bounds of the meshes the Poitou HDA instances, and of their
in-theme replacements.

Run headlessly, so it never touches the owner's editor session:

    UnrealEditor-Cmd.exe BS_GodFile.uproject \
        -run=pythonscript -script=".../poitou_mesh_bounds.py" -unattended -nullrhi -stdout

Why the numbers matter: Tools/Poitou/snip/inst.vex scales each instance by
dividing the wanted world size by the SOURCE MESH's real size, e.g.
`set(4.5/1.02, f@height_m/2.97, 4.5/1.02)` means "4.5 m wide, height_m tall"
for a tree-high that is 1.02 x 2.97 x 1.02 m. Swap the source mesh and the
divisor must change with it, or the poplars come out 40 cm wide or 40 m tall.

This prints the measured bounds so the divisors can be re-derived from fact
rather than guessed. Read-only: it changes no asset.
"""
from __future__ import annotations

import json
import os

import unreal

OUT = r"C:\EnvironmentPortfolio\BS_GodFile\Saved\Audit\AssetGraveyard_20261021\mesh_bounds.json"

# (label, package path) for the meshes the HDA instances today, and the
# in-theme candidates they are being redirected to.
SUBJECTS = [
    # --- current, third-party ---
    ("CURRENT poplar",  "/Game/EnvSandbox/Meshes/Environment/tree-high/StaticMeshes/tree-high"),
    ("CURRENT ash",    "/Game/EnvSandbox/Meshes/Environment/tree_fat/StaticMeshes/tree_fat"),
    ("CURRENT reeds",  "/Game/EnvSandbox/Meshes/Environment/grass_leafsLarge/StaticMeshes/grass_leafsLarge"),
    ("CURRENT barque", "/Game/EnvSandbox/Meshes/Environment/canoe/StaticMeshes/canoe"),
    ("CURRENT house",  "/Game/Melodia/Kit/MorningPlaza/SM_hero_house/StaticMeshes/SM_hero_house"),
    # --- in-theme replacements ---
    ("CANDIDATE poplar A", "/Game/Megascans/3D_Assets/MossyTree/SM_MossyTree_01"),
    ("CANDIDATE poplar B", "/Game/EnvSandbox/Meshes/Tree/SM_BlackAlder_Forest_Simple"),
    ("CANDIDATE poplar C", "/Game/EnvSandbox/Meshes/IvyTest/SM_EuropeanHornbeam_01"),
    ("CANDIDATE poplar D", "/Game/EnvSandbox/Meshes/SimpleWind/SM_EuropeanHornbeam_05"),
    ("CANDIDATE ash A",    "/Game/Melodia/Meshes/Poitou/SM_AshTetard_Canal_03"),
    ("CANDIDATE ash B",    "/Game/Melodia/Meshes/Poitou/SM_AshTetard_Canal_03_Sculpted"),
    ("CANDIDATE ash C",    "/Game/Melodia/Meshes/Poitou/SM_AshTetard_Ancient_01"),
    ("CANDIDATE ash D",    "/Game/Melodia/Meshes/Poitou/SM_AshTetard_Twisted_02_Sculpted"),
    ("CANDIDATE reeds A",  "/Game/EnvSandbox/Meshes/MossyRock_29/SM_GrassGroundPatch_01"),
    ("CANDIDATE barque A", "/Game/Melodia/Meshes/Poitou/SM_Marais_Barque_4m6_Sculpted"),
    ("CANDIDATE barque B", "/Game/Melodia/Meshes/Poitou/SM_Poitou_Barque"),
]


def main():
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    rows = []
    for label, path in SUBJECTS:
        row = {"label": label, "package": path}
        asset = unreal.load_asset(path)
        if asset is None:
            row["missing"] = True
            unreal.log("[bounds] MISSING %s -> %s" % (label, path))
            rows.append(row)
            continue
        box = asset.get_bounding_box()
        size = box.max - box.min
        row["size_m"] = [round(size.x, 4), round(size.y, 4), round(size.z, 4)]
        row["min_m"] = [round(box.min.x, 4), round(box.min.y, 4), round(box.min.z, 4)]
        try:
            row["nanite"] = asset.get_editor_property("nanite_settings").enabled
        except Exception:
            row["nanite"] = None
        unreal.log("[bounds] %-22s %-62s size_m=%s nanite=%s" % (
            label, path, row["size_m"], row["nanite"]))
        rows.append(row)

    with open(OUT, "w", encoding="utf-8") as fh:
        json.dump({"rows": rows}, fh, indent=1)
    unreal.log("[bounds] wrote %s" % OUT)


main()
