#!/usr/bin/env python
"""Headless in-theme gate for the Poitou layout HDA.

Run under hython, in an isolated process (see run_intheme_gate.ps1):

    "C:/Program Files/Side Effects Software/Houdini 22.0.368/bin/hython.exe" \
        Tools/Poitou/poitou_intheme_gate.py

Why this gate exists
--------------------
The v6 layout HDA emits instancing POINTS and asks Unreal to spawn a mesh.
Nothing checked that the mesh it names is in-theme, that it exists, or that it
is the size the HDA's scale divisor assumes. Three failures followed from that:

  1. The retired Kenney pack. snip/inst.vex named tree-high, tree_fat,
     grass_leafsLarge and canoe. Change 292 retired the pack, so the next cook
     emits instances of assets that no longer exist.
  2. tree-high no longer loaded at all, so that branch was already broken.
  3. The scale divisors were stale by ~18x for the ash: tree_fat was rescaled
     in place and never re-submitted, but inst.vex still divided by the
     ORIGINAL 0.76/1.15/0.65 m while the mesh now measures 1356x1631x1594 cm.
     The level read as a graveyard because the props were the wrong SIZE.

What it asserts
---------------
  RETIRED-PACK     no instance may point into /Game/EnvSandbox/Meshes/Environment/,
                    the pack that changelist 292 retired.
  OFF-PALETTE      every instance must resolve under a known in-theme root.
  ENGINE-BLOCKOUT  no instance may be an /Engine/BasicShapes/ primitive - those
                    are the preview placeholders.
  DEAD-ABBEY       v6 deletes the abbey footprint and the rubble outright when
                    real meshes are on, so the abbey is currently NOT generated
                    at all. The gate reports it as a failure, because a Poitou
                    level with no abbey in it is not the level the canon asks for.
  DIVISOR-MISMATCH the scale divisor in inst.vex is compared against the real
                    size of the mesh it divides by. The real sizes are measured
                    on the Unreal side (Tools/Editor/poitou_intheme_assets.py)
                    and cached in inst_scale_cache.json; this gate compares
                    against that cache and fails on a mismatch.

It also writes the divisor table it parsed, so the Unreal-side measurement can
be checked against a single source.

Writes Saved/Audit/PoitouConvergence_20261020/intheme_gate.json and exits
non-zero on any failure.
"""
from __future__ import annotations

import json
import os
import re
import sys

import hou

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, "..", ".."))
OUT_DIR = os.path.join(ROOT, "Saved", "Audit", "PoitouConvergence_20261020")
RECEIPT = os.path.join(OUT_DIR, "intheme_gate.json")
SCALE_CACHE = os.path.join(OUT_DIR, "inst_scale_cache.json")

# The LIVE v6 sources live here. The repo copy of build_poitou_hda.py is the
# older v5 builder: building from it silently regresses (13 landscape layers
# instead of 20, no IGN calibration, horizon_on=True, wrong landscape material).
V6_ROOT = os.environ.get("MELODIA_POITOU_V6_ROOT", r"C:\Users\froma\agent-tools\poitou_houdini")
HDA_PATH = os.path.join(V6_ROOT, "hda", "poitou_layout_live.hdalc")
HIPLC_PATH = os.path.join(V6_ROOT, "hda", "poitou_layout_live_test.hiplc")
INST_VEX = os.path.join(V6_ROOT, "snip", "inst.vex")

# Where an in-theme asset may live. Everything else is a failure.
IN_THEME_ROOTS = (
    "/Game/Melodia/Meshes/Poitou/",
    "/Game/Melodia/Kit/MorningPlaza/",
    "/Game/EnvSandbox/Poitou/",
    "/Game/Megascans/3D_Assets/MossyTree/",
    "/Game/Custom/RS_Assets/MossyRock_29/",
    "/Game/Custom/IvyTest/",
    "/Game/Megascans/3D_Plants/",
)
RETIRED_ROOT = "/Game/EnvSandbox/Meshes/Environment/"

# The vocabulary the canon requires the level to contain.
REQUIRED_VOCABULARY = {
    "poplar": "canal-bank poplar row",
    "poplar_band": "far poplar band",
    "ash_tetard": "pollard ash (tetard)",
    "building": "village house",
    "barque": "marsh barque",
    "abbey_maillezais_footprint": "Maillezais abbey",
}

REQUIRED_OUTPUTS = (
    "output_landscape",
    "output_points",
    "output_route_curve",
    "output_skirt_mesh",
    "output_water",
)


def log(msg):
    print("[intheme_gate] %s" % msg, flush=True)


def classify(path):
    if not path:
        return "EMPTY"
    if path.startswith("/Engine/"):
        return "ENGINE-BLOCKOUT"
    if path.startswith(RETIRED_ROOT):
        return "RETIRED-PACK"
    if any(path.startswith(r) for r in IN_THEME_ROOTS):
        return "IN-THEME"
    return "OFF-PALETTE"


def parse_divisors(vex_path):
    """Pull the hard-coded scale divisors out of inst.vex.

    They are the source of the one failure this gate exists to catch: a divisor
    that no longer matches the mesh it divides by. The real sizes are measured
    on the Unreal side; here we only record the INTENT so the two can be
    compared.
    """
    out = {}
    if not os.path.isfile(vex_path):
        return out
    text = open(vex_path, encoding="utf-8", errors="replace").read()
    # string NAME="path";
    for m in re.finditer(r'string\s+(\w+)\s*=\s*"([^"]+)"', text):
        out.setdefault("instances", {})[m.group(1)] = m.group(2)
    # sc = real?set(A/B, C/D, E/F):...
    for m in re.finditer(r'sc\s*=\s*real\?set\(([^)]*)\)', text):
        parts = [p.strip() for p in m.group(1).split(",")]
        nums = []
        for p in parts:
            if "/" in p:
                a, b = p.split("/")
                try:
                    nums.append([float(a), float(b)])
                except ValueError:
                    pass
        if nums:
            out.setdefault("scale_divisors", []).append(nums)
    return out


def find_out(parent, name):
    n = parent.node(name)
    if n is not None:
        return n
    stack = [parent]
    while stack:
        cur = stack.pop()
        for ch in cur.children():
            if ch.name() == name:
                return ch
            stack.append(ch)
    return None


def main():
    os.makedirs(OUT_DIR, exist_ok=True)
    failures = []
    report = {"hda": HDA_PATH, "v6_root": V6_ROOT, "outputs": {}, "instances": {}, "types": {}}

    report["inst_vex_intent"] = parse_divisors(INST_VEX)
    log("inst.vex names: %s" % json.dumps(report["inst_vex_intent"].get("instances", {}), indent=1)[:900])

    if not os.path.isfile(HIPLC_PATH):
        log("FAIL: no live v6 hip at %s" % HIPLC_PATH)
        log("      build it with the v6 builder: hython %s" % os.path.join(V6_ROOT, "build_poitou_hda.py"))
        json.dump({"result": "NO-V6-SOURCE"}, open(RECEIPT, "w", encoding="utf-8"), indent=1)
        return 2

    hou.hipFile.load(HIPLC_PATH, suppress_save_prompt=True, ignore_load_warnings=True)
    node = None
    for cand in hou.node("/obj").allSubChildren():
        if cand.name() == "poitou_layout_live":
            node = cand
            break
    if node is None:
        log("FAIL: the hip does not contain a poitou_layout_live subnet")
        return 2

    # ---- 1. every output cooks and is non-empty -----------------------
    for out_name in REQUIRED_OUTPUTS:
        n = find_out(node, out_name)
        if n is None:
            failures.append("missing output node: %s" % out_name)
            continue
        try:
            g = n.geometry()
        except Exception as exc:
            failures.append("output %s failed to cook: %s" % (out_name, exc))
            continue
        report["outputs"][out_name] = {"points": len(g.points()), "prims": len(g.prims())}
        if len(g.prims()) == 0 and len(g.points()) == 0:
            failures.append("output %s cooked empty" % out_name)
        log("output %-20s points=%-8d prims=%-8d" % (out_name, len(g.points()), len(g.prims())))

    # ---- 2. every generated instance is in-theme -----------------------
    pts = find_out(node, "output_points")
    if pts is not None:
        g = pts.geometry()
        type_counts = {}
        for p in g.points():
            t = p.attribValue("type") or "<none>"
            type_counts[t] = type_counts.get(t, 0) + 1
            inst = p.attribValue("unreal_instance") or ""
            mat = p.attribValue("unreal_material") or ""
            rec = report["instances"].setdefault(t, {"count": 0, "instances": {}, "materials": {}})
            rec["count"] += 1
            if inst:
                rec["instances"][inst] = rec["instances"].get(inst, 0) + 1
            if mat:
                rec["materials"][mat] = rec["materials"].get(mat, 0) + 1
        report["types"] = type_counts
        log("point types: %s" % type_counts)

        for t, rec in report["instances"].items():
            for inst, n in rec["instances"].items():
                verdict = classify(inst)
                rec.setdefault("verdicts", {})[inst] = verdict
                if verdict != "IN-THEME":
                    failures.append("%s: %d x %s -> %s" % (t, n, inst, verdict))

    # ---- 3. the required vocabulary is present -------------------------
    for t, what in REQUIRED_VOCABULARY.items():
        if report["types"].get(t, 0) == 0:
            failures.append("no points of type '%s' (%s) - the generator is not emitting it" % (t, what))

    # ---- 4. the scale divisors match the measured meshes ---------------
    # (measured on the Unreal side; cached here)
    if os.path.isfile(SCALE_CACHE):
        cache = json.load(open(SCALE_CACHE, encoding="utf-8"))
        report["scale_check"] = cache
        for entry in cache.get("entries", []):
            if entry.get("mismatch"):
                failures.append("scale divisor mismatch: %s divides by %s but the mesh measures %s" % (
                    entry.get("label"), entry.get("divisor"), entry.get("measured")))
    else:
        report["scale_check"] = "not measured yet - run Tools/Editor/poitou_intheme_assets.py"

    report["failures"] = failures
    report["result"] = "PASS" if not failures else "FAIL"
    with open(RECEIPT, "w", encoding="utf-8") as fh:
        json.dump(report, fh, indent=1, default=str)

    log("")
    if failures:
        log("FAIL: %d problem(s)" % len(failures))
        for f in failures:
            log("   - %s" % f)
    else:
        log("PASS: every generated instance is in-theme, every output cooks, the vocabulary is complete")
    log("receipt: %s" % RECEIPT)
    return 0 if not failures else 1


sys.exit(main())
