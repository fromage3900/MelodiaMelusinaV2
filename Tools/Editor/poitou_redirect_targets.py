#!/usr/bin/env python
"""Resolve the redirect targets for the Kenney assets that are genuinely referenced.

    UnrealEditor-Cmd.exe BS_GodFile.uproject -run=pythonscript -script=... -unattended -nullrhi -stdout

For each referenced Kenney asset, report its class, its bounds, and which other
assets in the project reference it. For the ones with an obvious in-theme
equivalent, report that mesh's bounds too, so the HDA scale divisors and the
level swaps can be derived from measurement rather than guesswork.
"""
from __future__ import annotations

import json
import os

import unreal

OUT = r"C:\EnvironmentPortfolio\BS_GodFile\Saved\Audit\AssetGraveyard_20261021\redirect_targets.json"

# Kenney assets that are genuinely referenced, and what they are used for.
REFERENCED = [
    ("/Game/EnvSandbox/Meshes/Environment/canoe/StaticMeshes/canoe", "barque on the canal"),
    ("/Game/EnvSandbox/Meshes/Environment/door/StaticMeshes/door", "114 doors in L_Poitou_v2"),
    ("/Game/EnvSandbox/Meshes/Environment/fence_simple/StaticMeshes/fence_simple", "canal fence"),
    ("/Game/EnvSandbox/Meshes/Environment/grass_leafsLarge/StaticMeshes/grass_leafsLarge", "reeds / undergrowth"),
    ("/Game/EnvSandbox/Meshes/Environment/violin", "Melusina's violin, on her own BP"),
    ("/Game/EnvSandbox/Meshes/Environment/Rock01_Art", "rocks (Morning ext actors)"),
    ("/Game/EnvSandbox/Meshes/Environment/Stone01_Art", "stones"),
    ("/Game/EnvSandbox/Meshes/Environment/Bush01_Art", "bushes"),
    ("/Game/EnvSandbox/Meshes/Environment/flower_redA", "lookdev flower"),
]

# In-theme candidates to measure, by role.
CANDIDATES = [
    ("barque", "/Game/Melodia/Meshes/Poitou/SM_Marais_Barque_4m6_Sculpted"),
    ("barque", "/Game/Melodia/Meshes/Poitou/SM_Poitou_Barque"),
    ("barque", "/Game/Melodia/Meshes/Poitou/SM_Poitou_Pigouille"),
    ("gate", "/Game/Melodia/Meshes/Poitou/SM_Poitou_LockGate_Pair"),
    ("gate", "/Game/Melodia/Meshes/Poitou/SM_Poitou_LockGate_Pair_Sculpted"),
    ("parapet", "/Game/Melodia/Meshes/Poitou/SM_Poitou_BridgeParapet"),
    ("parapet", "/Game/Melodia/Meshes/Poitou/SM_Poitou_BridgeParapet_Sculpted"),
    ("bench", "/Game/Melodia/Meshes/Poitou/SM_Poitou_StoneBench"),
    ("well", "/Game/Melodia/Meshes/Poitou/SM_Poitou_VillageWell"),
    ("ruin", "/Game/Melodia/Meshes/Poitou/SM_Maillezais_CrumbledWall_Sculpted"),
    ("ruin", "/Game/Melodia/Meshes/Poitou/SM_Maillezais_BrokenArch_Sculpted"),
    ("ash", "/Game/Melodia/Meshes/Poitou/SM_AshTetard_Canal_03_Sculpted"),
    ("poplar", "/Game/Megascans/3D_Assets/MossyTree/SM_MossyTree_01"),
    ("grass", "/Game/Melodia/Meshes/Poitou/SM_Poitou_Pigouille"),
]

# The door Blueprint that Poitou places 114 times.
DOOR_BPS = [
    "/Game/EnvSandbox/Meshes/Environment/door/StaticMeshes/door",
    "/Game/Melodia/Kit/MorningPlaza/SM_hero_house/StaticMeshes/SM_hero_house",
]


def describe(path):
    asset = unreal.load_asset(path)
    if asset is None:
        return None
    row = {"package": path, "class": str(asset.get_class().get_name())}
    try:
        box = asset.get_bounding_box()
        size = box.max - box.min
        row["size_cm"] = [round(size.x, 2), round(size.y, 2), round(size.z, 2)]
    except Exception:
        pass
    return row


def main():
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    out = {"referenced": [], "candidates": []}

    for path, use in REFERENCED:
        row = describe(path)
        if row is None:
            unreal.log("[redirect] MISSING %s" % path)
            out["referenced"].append({"package": path, "use": use, "missing": True})
            continue
        row["use"] = use
        # what is this asset made of / what references it
        try:
            mats = asset.get_editor_property("static_materials") if hasattr(asset, "get_editor_property") else []
            row["materials"] = [str(m.material_interface) for m in mats if m.material_interface]
        except Exception:
            pass
        unreal.log("[redirect] %-70s %s size_cm=%s mats=%s" % (
            path, row["class"], row.get("size_cm"), row.get("materials")))
        out["referenced"].append(row)

    for role, path in CANDIDATES:
        row = describe(path)
        if row is None:
            unreal.log("[redirect] MISSING %s" % path)
            out["candidates"].append({"role": role, "package": path, "missing": True})
            continue
        row["role"] = role
        unreal.log("[redirect] cand %-12s %-62s size_cm=%s" % (role, path, row.get("size_cm")))
        out["candidates"].append(row)

    # What mesh does the door Blueprint use?
    for bp_path in ("/Game/EnvSandbox/Meshes/Environment/door/StaticMeshes/door",):
        b = unreal.load_asset(bp_path)
        if b is None:
            continue
        try:
            comps = b.get_components_by_class(unreal.StaticMeshComponent)
            for c in comps:
                unreal.log("[redirect] door component %s -> static_mesh=%s" % (
                    c.get_name(), str(c.static_mesh) if c.static_mesh else None))
                out.setdefault("door_components", []).append({
                    "component": c.get_name(),
                    "static_mesh": str(c.static_mesh) if c.static_mesh else None,
                })
        except Exception as exc:
            unreal.log("[redirect] door component read failed: %s" % exc)

    with open(OUT, "w", encoding="utf-8") as fh:
        json.dump(out, fh, indent=1)
    unreal.log("[redirect] wrote %s" % OUT)


main()
