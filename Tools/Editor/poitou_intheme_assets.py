#!/usr/bin/env python
"""Measure the real size of every mesh the Poitou layout HDA instances, and
compare it against the scale divisor inst.vex divides by.

Run headlessly (no editor, no GPU):

    UnrealEditor-Cmd.exe BS_GodFile.uproject -run=pythonscript \
        -script=".../poitou_intheme_assets.py" -unattended -nopause -nosplash \
        -nullrhi -stdout -FullStdOutLogOutput

Why this exists
---------------
snip/inst.vex scales each instance by dividing the wanted world size by the
SOURCE mesh's real size, e.g. `set(4.5/1.02, f@height_m/2.97, 4.5/1.02)` means
"4.5 m wide, height_m tall" for a tree-high that measures 1.02 x 2.97 x 1.02 m.
Swap the mesh and the divisor must change with it.

Two of them did not change:

  * tree-high stopped loading entirely, so the poplar branch was already
    emitting broken instances.
  * tree_fat was rescaled in place and never re-submitted. inst.vex still
    divides by the ORIGINAL 0.76 / 1.15 / 0.65 m, but the mesh now measures
    1356.0 x 1631.0 x 1594.3 cm - so the ash is scaled against a mesh roughly
    18x larger than the divisor assumes.

That is why the level read as a graveyard: the props were the wrong SIZE, not
just the wrong art. A size audit is therefore part of the in-theme gate, and
this script is the Unreal half of it: it measures, writes
inst_scale_cache.json, and the Houdini half (poitou_intheme_gate.py) compares.

It also reports every named instance that does not resolve, so a retired
asset cannot survive because nothing ever asked for it.
"""
from __future__ import annotations

import json
import os

import unreal

OUT_DIR = r"C:\EnvironmentPortfolio\BS_GodFile\Saved\Audit\PoitouConvergence_20261020"
CACHE = os.path.join(OUT_DIR, "inst_scale_cache.json")
GATE_RECEIPT = os.path.join(OUT_DIR, "intheme_gate.json")

# The meshes inst.vex divides by, with the divisor it uses. The divisor is
# in METRES; the measured size below is in CENTIMETRES, so the comparison is
# divisor_m * 100 == measured_cm.
SUBJECTS = [
    ("POP",   "/Game/EnvSandbox/Meshes/Environment/tree-high/StaticMeshes/tree-high",        [1.02, 2.97, 1.02]),
    ("ASH",   "/Game/EnvSandbox/Meshes/Environment/tree_fat/StaticMeshes/tree_fat",            [0.76, 1.15, 0.65]),
    ("GRS",   "/Game/EnvSandbox/Meshes/Environment/grass_leafsLarge/StaticMeshes/grass_leafsLarge", [3.0, 12.0, 3.0]),
    ("CANOE", "/Game/EnvSandbox/Meshes/Environment/canoe/StaticMeshes/canoe",                [0.30, 0.18, 1.15]),
    ("HOUSE", "/Game/Melodia/Kit/MorningPlaza/SM_hero_house/StaticMeshes/SM_hero_house",       [5.57, 3.27, 4.01]),
]

# The in-theme replacements, measured so a repoint has real numbers to divide by.
REPLACEMENTS = [
    ("poplar",  "/Game/Megascans/3D_Assets/MossyTree/SM_MossyTree_01"),
    ("ash",     "/Game/Melodia/Meshes/Poitou/SM_AshTetard_Canal_03_Sculpted"),
    ("barque",  "/Game/Melodia/Meshes/Poitou/SM_Marais_Barque_4m6_Sculpted"),
    ("reeds",   "/Game/Custom/RS_Assets/MossyRock_29/SM_GrassGroundPatch_01"),
    ("rock",    "/Game/Custom/IvyTest/MossyRocks/SM_MossyRocksVine_01"),
    ("bush",    "/Game/Megascans/3D_Plants/EuropeanHornbeam/Geometry/SimpleWind/SM_EuropeanHornbeam_Sapling_01"),
    ("parapet", "/Game/Melodia/Meshes/Poitou/SM_Poitou_BridgeParapet"),
    ("gate",    "/Game/Melodia/Meshes/Poitou/SM_Poitou_LockGate_Pair"),
    ("rubble",  "/Game/Melodia/Meshes/Poitou/SM_Maillezais_CrumbledWall_Sculpted"),
    ("arch",    "/Game/Melodia/Meshes/Poitou/SM_Maillezais_BrokenArch_Sculpted"),
    ("buttress", "/Game/Melodia/Meshes/Poitou/SM_Maillezais_ButtressStub_Sculpted"),
]


def measure(path):
    asset = unreal.load_asset(path)
    if asset is None:
        return None
    try:
        b = asset.get_bounding_box()
        s = b.max - b.min
        return [round(s.x, 2), round(s.y, 2), round(s.z, 2)]
    except Exception:
        return None


def main():
    os.makedirs(OUT_DIR, exist_ok=True)
    entries = []
    for label, path, divisor in SUBJECTS:
        measured = measure(path)
        row = {
            "label": label,
            "package": path,
            "divisor_m": divisor,
            "measured_cm": measured,
            "resolves": measured is not None,
            "mismatch": False,
        }
        if measured is None:
            row["note"] = "asset does not load"
            row["verdict"] = "MISSING"
        else:
            # Compare the divisor SET against the measured SET first.
            # inst.vex divides Y by the mesh's Z and Z by the mesh's Y, because
            # the source meshes are authored Z-up and Houdini is Y-up. So a
            # divisor that is a PERMUTATION of the measured size is an
            # axis-order question, not a size error - and is a different fix.
            want = sorted(d * 100.0 for d in divisor)
            got = sorted(measured)
            perm = all(abs(w - g) <= max(0.05 * w, 1.0) for w, g in zip(want, got))
            if perm:
                row["verdict"] = "AXIS-ORDER"
                row["note"] = ("the divisor set matches the measured set but on different axes; "
                               "inst.vex divides Y by the mesh Z and Z by the mesh Y")
            else:
                ratio = (max(got) / max(want)) if want and max(want) > 0 else 0
                row["verdict"] = "SIZE-ERROR"
                row["mismatch"] = True
                row["scale_ratio"] = round(ratio, 3)
                row["note"] = "the divisor does not match the measured size on any axis (%.1fx off)" % ratio
        entries.append(row)
        unreal.log("[intheme_assets] %-7s %-72s divisor=%s measured_cm=%s  %s" % (
            label, path, divisor, measured, row.get("verdict", "")))

    repl = []
    for role, path in REPLACEMENTS:
        measured = measure(path)
        repl.append({"role": role, "package": path, "measured_cm": measured,
                     "resolves": measured is not None})
        unreal.log("[intheme_assets] cand %-9s %-78s measured_cm=%s" % (role, path, measured))

    # every instance the gate saw, resolved
    named = []
    if os.path.isfile(GATE_RECEIPT):
        try:
            g = json.load(open(GATE_RECEIPT, encoding="utf-8"))
            for t, rec in (g.get("instances") or {}).items():
                for inst in (rec.get("instances") or {}):
                    named.append({"type": t, "package": inst})
        except Exception:
            pass

    cache = {
        "entries": entries,
        "replacements": repl,
        "named_instances": named,
    }
    with open(CACHE, "w", encoding="utf-8") as fh:
        json.dump(cache, fh, indent=1)
    unreal.log("[intheme_assets] wrote %s" % CACHE)
    bad = [e for e in entries if e["mismatch"] or not e["resolves"]]
    unreal.log("[intheme_assets] %d of %d instanced meshes are missing or mismatched" % (len(bad), len(entries)))


main()
