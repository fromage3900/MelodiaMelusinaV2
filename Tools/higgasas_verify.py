"""Higgsas capability probe. Run inside Blender 5.2:

    "C:/Program Files/Blender Foundation/Blender 5.2/blender.exe" \\
        --background --factory-startup --python Tools/higgasas_verify.py

    options: --json OUT.json   write the probe report (default Saved/Audit/higgsas_probe.json)
             --require         treat a missing library as FAIL instead of SKIP

Why this exists: the library is gitignored and machine-local
(RawArt/BlenderLibraries/Higgsas/*), so a fresh clone has no Higgsas and the NATIVE
FALLBACK is what actually runs. That means the normal gates - which all run
--factory-startup - exercise the fallback, and a Higgsas path can be silently broken
for months while every gate stays green. This probe is the one place the real path is
exercised, reported, and written down.

RawArt/BlenderLibraries/README.md has promised `higgsas_verify.py` since 2026-09-23;
that file did not exist until this. The only prior artifacts were an ad-hoc
Saved/Audit/higgas_scan.py plus two text dumps.

Exit codes:
    0  all required checks pass, OR library absent and --require not given (SKIP)
    1  a check failed
    2  invoked without bpy (plain `python Tools/higgasas_verify.py`)
"""

from __future__ import annotations

import argparse
import json
import os
import sys

try:
    import bpy
except ImportError:
    sys.stderr.write(
        "\n[higgasas_verify] bpy not available - this probe must run inside Blender.\n"
        "  Correct invocation:\n"
        '    "C:/Program Files/Blender Foundation/Blender 5.2/blender.exe"'
        " --background --factory-startup --python Tools/higgasas_verify.py\n\n"
    )
    raise SystemExit(2)

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DEPLOY = os.path.join(REPO, "deploy")
APPDATA_ADDONS = os.path.join(
    os.environ.get("APPDATA", ""), "Blender Foundation", "Blender", "5.2",
    "scripts", "addons")
# Checkout wins so the probe audits uncommitted work (house rule); live addon is the
# fallback so it still runs against an installed copy.
sys.path.insert(0, DEPLOY)
if APPDATA_ADDONS not in sys.path:
    sys.path.append(APPDATA_ADDONS)

results = []
notes = []


def check(name, ok, detail="", tier="FAIL"):
    """Record one assertion. tier='SKIP' reports without failing the run."""
    status = "SKIP" if tier == "SKIP" else ("PASS" if ok else "FAIL")
    results.append((name, status, detail))
    print("PROBE %-5s %-24s %s" % (status, name, detail))
    return ok


def main(argv):
    ap = argparse.ArgumentParser(description="Higgsas capability probe")
    ap.add_argument("--json", dest="json_out", default=None)
    ap.add_argument("--require", action="store_true",
                    help="fail instead of skip when the library is absent")
    args = ap.parse_args(argv)

    from surreal_arch.melodia_gn import higgsas_pipeline as hp
    # NOTE: it is melodia_gn.higgsas_pipeline, not surreal_arch.higgsas_pipeline -
    # importing the subpackage also runs the full builder registration, so a broken
    # package init fails here loudly instead of being missed by this probe.

    rep = hp.status()
    lib_absent = not rep["library_exists"]
    # Library-dependent checks hard-fail when the library is here (or --require);
    # otherwise they report SKIP and the run still proves the fallback path.
    tier = "FAIL" if (args.require or not lib_absent) else "SKIP"

    # ---- C1: the library resolves ------------------------------------------------
    check("C1_library_path", rep["library_exists"],
          rep["library_path"] or "<unresolved>",
          tier="FAIL" if args.require else ("SKIP" if lib_absent else "FAIL"))
    if lib_absent:
        notes.append("library is gitignored/machine-local - Higgsas paths use their "
                     "native fallback on this machine (by design)")

    # ---- C2: what is actually inside the library --------------------------------
    lib_count = 0
    if rep["library_exists"]:
        try:
            with bpy.data.libraries.load(rep["library_path"], link=False) as (src, dst):
                lib_count = len(list(src.node_groups))
        except Exception as exc:
            lib_count = -1
            notes.append("library read failed: %s: %s" % (type(exc).__name__, exc))
    check("C2_library_inventory", lib_count >= 200,
          "node_groups_in_library=%d" % lib_count, tier=tier)

    # ---- C3: every pipeline group loads -----------------------------------------
    missing = [k for k, v in rep["groups"].items() if v == "missing"]
    check("C3_pipeline_load", rep["missing"] == 0,
          "%d/%d loaded, %d missing%s" % (
              rep["loaded"], rep["requested"], rep["missing"],
              ("" if not missing else " e.g." + str(missing[:6]))),
          tier=tier)

    # ---- C4: no .001 twins -------------------------------------------------------
    dupes = [g.name for g in bpy.data.node_groups if ".001" in g.name]
    check("C4_no_duplicates", not dupes, "duplicates=%s" % (dupes[:6] or "none"))

    # ---- C5: both spellings resolve to ONE group --------------------------------
    a = hp.load("Bricks Grid")
    b = hp.load("NTBricks Grid")
    check("C5_canonical_equivalence", a is not None and a is b,
          "bare is NT: %s (identity=%s)" % (a is not None, a is b), tier=tier)

    # ---- C6: the legacy loaders still agree with this one (back-compat) ----------
    try:
        from surreal_arch import higgsas_bridge as hb
        legacy = hb.load_node("NTSpin")
        ours = hp.load("Spin")
        check("C6_legacy_loader_agrees",
              legacy is ours or (legacy is None and ours is None),
              "bridge==pipeline on NTSpin: %s" % (legacy is ours), tier=tier)
    except Exception as exc:
        check("C6_legacy_loader_agrees", False,
              "bridge import failed: %s" % exc, tier="FAIL")

    # ---- C7/C8: fallback path vs real path --------------------------------------
    tree = bpy.data.node_groups.new("__higgas_probe__", "GeometryNodeTree")
    try:
        n, used = hp.stage(tree, "NT___definitely_not_a_real_group___", 0, 0,
                           fallback_type="GeometryNodeMeshCube")
        check("C7_fallback_path", n is not None and used is True,
              "node=%s used_fallback=%s" % (n is not None, used))
        m, used_m = hp.stage(tree, "Bricks Grid", 320, 0,
                             fallback_type="GeometryNodeMeshCube")
        check("C8_real_group_path", m is not None,
              "node=%s used_fallback=%s (expected fallback=%s here)"
              % (m is not None, used_m, lib_absent), tier=tier)
    finally:
        try:
            bpy.data.node_groups.remove(tree)
        except Exception:
            pass

    # ---- C9: repeated loads must not grow the session ---------------------------
    before = len(bpy.data.node_groups)
    for _ in range(3):
        hp.load("Bricks Grid")
        hp.load("NTBricks Grid")
    after = len(bpy.data.node_groups)
    check("C9_idempotent_load", after == before,
          "node_groups %d -> %d" % (before, after))

    report = {
        "stamp": __import__("datetime").date.today().isoformat(),
        "library_path": rep["library_path"],
        "library_exists": rep["library_exists"],
        "library_node_groups": lib_count,
        "requested": rep["requested"],
        "loaded": rep["loaded"],
        "missing": rep["missing"],
        "groups": rep["groups"],
        "checks": [{"name": n, "status": s, "detail": d} for n, s, d in results],
        "notes": notes,
    }
    out = args.json_out or os.path.join(REPO, "Saved", "Audit", "higgsas_probe.json")
    try:
        os.makedirs(os.path.dirname(out), exist_ok=True)
        with open(out, "w", encoding="utf-8") as fh:
            json.dump(report, fh, indent=1)
        print("PROBE json written: %s" % out)
    except Exception as exc:
        print("PROBE json FAILED: %s" % exc)

    for note in notes:
        print("PROBE NOTE  %s" % note)

    failed = [n for n, s, _ in results if s == "FAIL"]
    print("HIGGSAS PROBE RESULT: %s  (%d checks, %d failed)"
          % ("FAIL" if failed else "PASS", len(results), len(failed)))
    if failed:
        print("  failed: %s" % failed)
    if lib_absent and not args.require:
        print("HIGGSAS PROBE MODE: SKIP (library not on this machine; "
              "pass --require to hard-fail)")
    return 1 if failed else 0


if __name__ == "__main__":
    argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
    raise SystemExit(main(argv))

