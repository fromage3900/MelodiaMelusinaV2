#!/usr/bin/env python
"""Measure the real size of every mesh the Poitou layout HDA instances, and
check the scale divisor inst.vex uses against it.

Run headlessly (no editor, no GPU):

    UnrealEditor-Cmd.exe BS_GodFile.uproject -run=pythonscript \
        -script=".../poitou_intheme_assets.py" -unattended -nopause -nosplash \
        -nullrhi -stdout -FullStdOutLogOutput

Why this exists
---------------
snip/inst.vex scales each instance by dividing a wanted world size by the
SOURCE mesh's real size, e.g. `set(4.5/1.02, f@height_m/2.97, 4.5/1.02)`.
Swap the mesh and the divisor must change with it.  Three things went wrong
before this script existed:

  * the retired Kenney pack was still named (changelist 292 removed it);
  * tree_fat was rescaled in place and never re-submitted, so the divisor
    still said 0.76/1.15/0.65 m while the mesh measured 13.56/16.31/15.94 m
    - the ash was 18x the wrong size and the level read as a graveyard;
  * the divisors were written in the wrong AXIS ORDER for the in-theme pack.

The axis rule this script enforces
----------------------------------
Every in-theme asset is Z-up with its pivot at the base, so the mesh's Z
size IS its height.  Houdini is Y-up and the Houdini Engine maps
UE X->Houdini X, UE Z->Houdini Y (up), UE Y->Houdini Z.  So the divisor
triple written into set(scale.x, scale.y, scale.z) must be

    (srcX, srcZ, srcY)

which means: the SECOND divisor (the up slot) must equal the mesh's measured
Z size.  A divisor whose up slot matches some other axis is an axis-order
error, which produces a mesh that is the right size in one direction and
grossly wrong in the others - the failure that is hardest to see and
easiest to ship.

The (mesh, divisor) pairs are PARSED OUT OF inst.vex, not hand-listed here,
so the check cannot drift from the file it is checking.
"""
from __future__ import annotations

import hashlib
import json
import os
import re

import unreal

REPO = os.environ.get("MELODIA_POITOU_REPO", r"C:\EnvironmentPortfolio\BS_GodFile")
OUT_DIR = os.path.join(REPO, "Saved", "Audit", "PoitouConvergence_20261020")
CACHE = os.path.join(OUT_DIR, "inst_scale_cache.json")
INST_VEX = os.path.join(REPO, "Tools", "Poitou", "snip", "inst.vex")

# tolerance on "this divisor is this mesh's size"
TOL = 0.01

# set(...) groups whose arguments are not a literal/literal division are
# preview placeholders and are ignored.
_NUM = re.compile(r"^-?\d+(?:\.\d+)?$")


def _divisors(group):
    """Pull the denominator of each `want/size` term out of one set(...) group."""
    out = []
    for part in group.split(","):
        part = part.strip()
        if "/" not in part:
            return None  # not a divisor form (absolute scale) -> skip the group
        den = part.rsplit("/", 1)[1].strip()
        if not _NUM.match(den):
            return None
        out.append(float(den))
    return out or None


def parse_inst_vex(path):
    """Walk inst.vex and pair each scale divisor group with the mesh it scales.

    The file is written branch by branch, and each branch names its mesh
    first (`s@unreal_instance=real?KEY:"..."`) and its scale second
    (`sc=real?set(...)`), so a line-ordered scan recovers the pairing.
    """
    if not os.path.isfile(path):
        return [], None
    raw = open(path, "rb").read()
    text = raw.decode("utf-8", errors="replace")

    meshes = {}
    for m in re.finditer(r'string\s+(\w+)\s*=\s*"(/Game/[^"]+)"', text):
        meshes[m.group(1)] = m.group(2)

    pairs = []
    current = None
    for line in text.splitlines():
        for m in re.finditer(r's@unreal_instance\s*=\s*(?:real\?(\w+)|(\w+))', line):
            current = m.group(1) or m.group(2)
        for m in re.finditer(r'sc\s*=\s*(?:real\?)?set\(([^)]*)\)', line):
            divs = _divisors(m.group(1))
            if divs is None or current is None:
                continue
            path_m = meshes.get(current)
            if not path_m:
                continue
            pairs.append({"key": current, "package": path_m, "divisor_m": divs})
            break  # one divisor group per branch
    return pairs, hashlib.sha256(raw).hexdigest()


def measure(path):
    asset = unreal.load_asset(path)
    if asset is None:
        return None
    try:
        b = asset.get_bounding_box()
        s = b.max - b.min
        return [round(s.x / 100.0, 4), round(s.y / 100.0, 4), round(s.z / 100.0, 4)]
    except Exception:
        return None


def main():
    os.makedirs(OUT_DIR, exist_ok=True)
    pairs, vex_hash = parse_inst_vex(INST_VEX)
    unreal.log("[intheme_assets] inst.vex: %s" % INST_VEX)
    unreal.log("[intheme_assets] %d mesh/divisor pair(s) parsed, sha256=%s" % (len(pairs), (vex_hash or "")[:16]))
    if not pairs:
        unreal.log("[intheme_assets] FAIL: no mesh/divisor pairs parsed - check INST_VEX path")
        json.dump({"entries": [], "inst_vex_sha256": vex_hash, "error": "no pairs parsed"},
                  open(CACHE, "w", encoding="utf-8"), indent=1)
        return

    entries = []
    seen = set()
    for p in pairs:
        ident = (p["package"], tuple(p["divisor_m"]))
        if ident in seen:
            continue
        seen.add(ident)
        measured = measure(p["package"])
        row = {
            "key": p["key"],
            "package": p["package"],
            "divisor_m": p["divisor_m"],
            "measured_m": measured,
            "resolves": measured is not None,
            "mismatch": False,
        }
        if measured is None:
            row["verdict"] = "MISSING"
            row["note"] = "asset does not resolve"
            row["mismatch"] = True
        else:
            # the up slot (.y) must divide by the mesh's Z size - the height
            up = p["divisor_m"][1]
            mz = measured[2]
            if abs(up - mz) > max(TOL * mz, 0.005):
                row["verdict"] = "AXIS-ORDER"
                row["mismatch"] = True
                row["note"] = ("up slot divides by %.4f m but the mesh is %.4f m tall on Z "
                               "(UE Z -> Houdini Y); the height is wrong" % (up, mz))
            else:
                stray = [d for d in p["divisor_m"]
                         if not any(abs(d - m) <= max(TOL * m, 0.005) for m in measured)]
                if stray:
                    row["verdict"] = "SIZE-ERROR"
                    row["mismatch"] = True
                    row["note"] = "divisor(s) %s match no axis of the mesh %s" % (stray, measured)
                else:
                    row["verdict"] = "OK"
                    row["note"] = "divisor triple matches the mesh on every axis"
        entries.append(row)
        unreal.log("[intheme_assets] %-9s %-78s divisor=%s measured=%s -> %s" % (
            row["key"], row["package"], row["divisor_m"], measured, row["verdict"]))

    cache = {
        "inst_vex": INST_VEX,
        "inst_vex_sha256": vex_hash,
        "entries": entries,
    }
    with open(CACHE, "w", encoding="utf-8") as fh:
        json.dump(cache, fh, indent=1)
    unreal.log("[intheme_assets] wrote %s" % CACHE)
    bad = [e for e in entries if e["mismatch"]]
    unreal.log("[intheme_assets] %d of %d instanced meshes are missing or mismatched" % (len(bad), len(entries)))


main()
