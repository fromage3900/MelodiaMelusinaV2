"""WaveHarp form contract gate - offline, no Unreal, no editor.

The rule this gate exists to enforce (Jev, 2026-10-22, source=jev-live):
assert the CONTRACT, and read the numbers from the bake manifest - never re-type
them. A number that exists in two places is a number that will drift.

Checks:
  1. the C++ socket defaults match the bake manifest exactly
  2. the blade stays a crescent (and never the shipped 42 m defect)
  3. CurrentForm has exactly one assignment site (the single-writer contract)
  4. the melee trace does not read the unit-path-unsafe skeleton sockets
  5. the form ring in the code matches the contract
  6. the Niagara systems the component references exist on disk (no new graphs)

Run: C:/Python314/python.exe Tools/waveharp/check_waveharp_form_contract.py
"""
from __future__ import annotations

import json
import math
import os
import re
import sys

REPO = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
HEADER = os.path.join(REPO, "Source", "BS_GodFile", "MelodiaIntegration",
                      "MelodiaWaveHarpCombatComponent.h")
SOURCE = os.path.join(REPO, "Source", "BS_GodFile", "MelodiaIntegration",
                       "MelodiaWaveHarpCombatComponent.cpp")
MANIFEST = os.path.join(REPO, "Saved", "Audit", "waveharp", "ue_ready",
                         "waveharp_wand_bake_manifest.json")

# The shipped defect D8: the skeletal sockets put the blade ~90-100x too far out.
MAX_SANE_BLADE_CM = 200.0


def fail(results, name, detail):
    results.append({"check": name, "ok": False, "detail": detail})


def ok(results, name, detail):
    results.append({"check": name, "ok": True, "detail": detail})


def parse_vector(text):
    nums = re.findall(r"-?\d+(?:\.\d+)?", text)
    return [float(n) for n in nums[:3]]


def cpp_vector_default(text):
    match = re.search(r"FVector\(([^)]*)\)", text)
    if not match:
        return None
    parts = [p.strip() for p in match.group(1).split(",")]
    out = []
    for p in parts:
        try:
            out.append(float(p))
        except ValueError:
            return None
    return out if len(out) == 3 else None


def main() -> int:
    results = []
    if not os.path.exists(MANIFEST):
        print("MISSING manifest:", MANIFEST)
        return 2
    manifest = json.load(open(MANIFEST, encoding="utf-8"))
    header = open(HEADER, encoding="utf-8").read()
    source = open(SOURCE, encoding="utf-8").read()

    forms = manifest.get("forms", [])
    melee = None
    caster = None
    for form in forms:
        sockets = form.get("sockets_local_cm", {})
        if "Scythe_BladeTip" in sockets:
            melee = sockets
        else:
            caster = sockets

    if not melee or not caster:
        fail(results, "manifest.forms", "the bake manifest has no caster/melee socket pair")
        return report(results)

    # 1. the C++ defaults must equal the manifest
    def cxx_default(field):
        match = re.search(r"FVector\s+%s\s*=\s*(FVector\([^)]*\))" % re.escape(field), header)
        if not match:
            return None
        return cpp_vector_default(match.group(1))

    pairs = [
        ("BowGrip", caster.get("SOCKET_Bow_Grip")),
        ("HeadSeat", None),
        ("CymaticProjection", caster.get("SOCKET_Cymatic_Projection")),
        ("BladeStart", melee.get("Scythe_BladeStart")),
        ("BladeMid", melee.get("Scythe_BladeMid")),
        ("BladeTip", melee.get("Scythe_BladeTip")),
    ]
    for field, manifest_value in pairs:
        cxx = cxx_default(field)
        if cxx is None:
            fail(results, "cxx.%s" % field, "no FVector default found in the header")
            continue
        if manifest_value is None:
            ok(results, "cxx.%s" % field, "cxx %s (head seat is a runtime seat, not a baked socket)" % cxx)
            continue
        if all(abs(a - b) < 1e-6 for a, b in zip(cxx, manifest_value)):
            ok(results, "cxx.%s" % field, "matches the manifest %s" % manifest_value)
        else:
            fail(results, "cxx.%s" % field,
                 "cxx %s != manifest %s" % (cxx, manifest_value))

    # 2. the crescent stays a crescent
    blade_start = melee["Scythe_BladeStart"]
    blade_mid = melee["Scythe_BladeMid"]
    blade_tip = melee["Scythe_BladeTip"]
    length = math.dist(blade_start, blade_tip)
    radius = max(abs(blade_start[0]), abs(blade_mid[0]), abs(blade_tip[0]))
    if length <= MAX_SANE_BLADE_CM:
        ok(results, "blade.length_cm", "%.2f cm" % length)
    else:
        fail(results, "blade.length_cm", "%.2f cm is beyond a crescent" % length)
    if radius <= MAX_SANE_BLADE_CM:
        ok(results, "blade.radius_cm", "%.2f cm" % radius)
    else:
        fail(results, "blade.radius_cm", "%.2f cm is beyond a crescent" % radius)
    if length < 4200.0:
        ok(results, "defect.D8", "the sweep is a crescent, not the shipped 42 m")
    else:
        fail(results, "defect.D8", "the sweep is back at the shipped 42 m")

    # 3. single writer: CurrentForm is assigned in exactly one place
    assignments = [m.start() for m in re.finditer(r"CurrentForm\s*=[^=]", source)]
    land = "CurrentForm = PendingForm;"
    if len(assignments) == 1 and land in source:
        ok(results, "single_writer", "one assignment site: the transition landing")
    else:
        fail(results, "single_writer",
             "%d assignment sites for CurrentForm (expected exactly 1: the landing)" % len(assignments))

    # 4. the melee trace must not read the broken skeleton sockets
    if "Instrument->GetSocketLocation(ScytheBlade" in source:
        fail(results, "defect.D8.trace",
             "the melee still reads the unit-path-unsafe skeleton sockets")
    else:
        ok(results, "defect.D8.trace", "the melee reads the measured offsets")

    # 5. the ring
    for name in ("Harp", "Bow", "CarillonMelee"):
        if name not in header:
            fail(results, "ring.%s" % name, "the form %s is missing" % name)
        else:
            ok(results, "ring.%s" % name, "present")
    if re.search(r"GetNextForm\s*\(", header) or re.search(r"GetNextForm\s*\(", source):
        ok(results, "ring.order", "the ring has one shared helper")
    else:
        fail(results, "ring.order", "no shared ring helper")

    # 6. the Niagara systems the component names must exist (no new graphs)
    for path in sorted(set(re.findall(r'"/Game/[^"]+\.uasset"', source))):
        asset = path.strip('"')
        disk = os.path.join(REPO, "Content", asset[len("/Game/"):].replace("/", os.sep))
        if os.path.exists(disk):
            ok(results, "asset%s" % asset, "exists")
        else:
            fail(results, "asset%s" % asset, "missing on disk")

    return report(results)


def report(results):
    bad = [r for r in results if not r["ok"]]
    for r in results:
        print("%-6s %-38s %s" % ("PASS" if r["ok"] else "FAIL", r["check"], r["detail"]))
    print("\n%d checks, %d failed" % (len(results), len(bad)))
    out = os.path.join(REPO, "Saved", "Audit", "waveharp", "waveharp_form_contract.json")
    os.makedirs(os.path.dirname(out), exist_ok=True)
    with open(out, "w", encoding="utf-8") as fh:
        json.dump({"schema": "melodia.waveharp.form_contract.v1",
                   "source": "offline gate (no editor)",
                   "checks": results}, fh, indent=2)
    print("receipt:", out)
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
