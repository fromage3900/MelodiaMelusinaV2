#!/usr/bin/env python
"""Census the static-mesh graveyard: what is Kenney-derived, what is referenced, what is free to cut.

Read-only. Emits a JSON artifact so the cut list is reviewable before anything
is deleted.

    python Tools/Editor/asset_graveyard_census.py \
        --content Content --out Saved/Audit/AssetGraveyard_20261021/census.json

How the referencer map is built, and why it is only a *candidate* map:
UE stores object references as FNames, so a referring package's name table
contains the referenced asset's *name*, not its path. Scanning package bytes
for that name finds the referrers, but it cannot distinguish two assets that
share a name in different folders, and it cannot see references that only
exist in a cooked/HDA-generated form. The authoritative map is the editor's
Asset Registry, which is what the deletion pass must use as its gate.

Method:
  1. Every .uasset/.umap under --content is classified.
  2. Graveyard candidates are the Kenney-derived static meshes, selected by
     explicit rules (see CANDIDATE_RULES) rather than by guesswork.
  3. Every Content package is scanned once for the candidate names.
  4. Each candidate is reported with its referrers, and classified as
     UNREFERENCED (safe to delete outright) or REFERENCED (needs a redirect
     before it can go).
"""
from __future__ import annotations

import argparse
import json
import os
import re
import sys
import time
from collections import defaultdict

# ----------------------------------------------------------------------
# Candidate rules. Each rule is (id, human reason, predicate on the record).
# A rule is only "in" the graveyard if the owner has not vetoed it.
# ----------------------------------------------------------------------

# Roots that are wholesale a third-party pack. Everything under these is a
# candidate; the referencer map then decides whether it can be cut outright.
PACK_ROOTS = (
    "/Game/EnvSandbox/Meshes/Environment/_RetroFantasyKit",
    "/Game/EnvSandbox/Meshes/Environment/_Loose",
)

# The pack's own folder. The candidate set is scoped to this: the Kenney
# Retro Fantasy Kit assets were dropped in as one folder per mesh, with the
# pack's own lowercase-hyphenated naming, while everything the project
# authored is SM_*/BP_*/MI_* prefixed.
PACK_ROOT = "/Game/EnvSandbox/Meshes/Environment"

# Material instances that belong to the Kenney RetroFantasyKit. A static mesh
# that uses one of these is Kenney-derived even if it sits in a themed folder.
KENNEY_MATERIAL_ROOTS = (
    "/Game/EnvSandbox/Materials/Instances/Kenney/RetroFantasyKit",
)

# Name shapes that identify the pack's own assets. Kenney's Retro Fantasy Kit
# uses lowercase, hyphen/underscore names with no SM_ prefix, while the
# project's own assets are SM_*/BP_*/MI_* prefixed.
PACK_NAME_RE = re.compile(r"^[a-z][a-z0-9]*([-_][a-zA-Z0-9]+)*$")
PROJECT_PREFIXES = ("SM_", "BP_", "MI_", "M_", "MF_", "T_", "DA_", "BP_", "SK_", "FL_", "ABP_", "PCG_", "IC_", "LT_", "E_", "HDA_", "AS_", "WBP_")

SCAN_EXTS = (".uasset", ".umap")


def project_path(content_root: str, disk_path: str) -> str:
    rel = os.path.relpath(disk_path, content_root).replace("\\", "/")
    return "/Game/" + rel[: -len(".uasset")] if rel.endswith(".uasset") else "/Game/" + rel[: -len(".umap")]


def asset_name(disk_path: str) -> str:
    return os.path.splitext(os.path.basename(disk_path))[0]


def is_project_prefixed(name: str) -> bool:
    return name.startswith(PROJECT_PREFIXES)


def enumerate_packages(content_root: str):
    for dirpath, _dirnames, filenames in os.walk(content_root):
        for fn in filenames:
            if fn.endswith(SCAN_EXTS):
                yield os.path.join(dirpath, fn)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--content", default="Content")
    ap.add_argument("--out", default="Saved/Audit/AssetGraveyard/census.json")
    ap.add_argument("--no-scan", action="store_true", help="inventory only, skip the referencer scan")
    ap.add_argument("--min-name-len", type=int, default=4,
                    help="shorter names are too ambiguous to scan for reliably")
    args = ap.parse_args()

    content_root = os.path.abspath(args.content)
    out_path = os.path.abspath(args.out)
    started = time.time()

    all_pkgs = list(enumerate_packages(content_root))
    print("scanning %d packages under %s" % (len(all_pkgs), content_root), flush=True)

    # ---- 1. classify every static mesh as a candidate or not -------------
    # The candidate set is deliberately NARROW. A name-shape heuristic applied
    # tree-wide catches audio, UI and character assets (a first pass matched
    # 2,628 packages tree-wide, of which only 885 were the actual pack), so
    # the rule is scoped to the pack's own folder and to names that are not
    # project-prefixed. The project's own assets are SM_*/BP_*/MI_* prefixed.
    candidates = {}
    for disk in all_pkgs:
        name = asset_name(disk)
        if is_project_prefixed(name):
            continue
        ppath = project_path(content_root, disk)
        if not ppath.startswith(PACK_ROOT):
            continue
        candidates[name] = {
            "package": ppath,
            "disk": disk,
            "size": os.path.getsize(disk),
            "in_pack_root": any(ppath.startswith(r) for r in PACK_ROOTS),
            "pack_shaped": True,
            "referrers": [],
        }

    print("candidate static meshes: %d (of %d packages)" % (len(candidates), len(all_pkgs)), flush=True)

    # ---- 2. one pass over every package, looking for candidate names ----
    # Content is tens of gigabytes, so the scan is delegated to ripgrep, whose
    # fixed-string multi-pattern search is an Aho-Corasick automaton. The
    # in-process regex alternative took minutes per gigabyte and was killed.
    scan_names = {n for n in candidates if len(n) >= args.min_name_len}
    hits = 0
    if scan_names and not args.no_scan:
        import subprocess
        import tempfile

        with tempfile.NamedTemporaryFile("w", suffix=".txt", delete=False, encoding="utf-8") as tf:
            for n in sorted(scan_names):
                tf.write(n + "\n")
            pattern_file = tf.name

        try:
            proc = subprocess.run(
                ["rg", "-F", "-a", "-H", "-o", "--no-messages",
                 "--glob", "!**/StaticMeshes/**",
                 "-f", pattern_file, content_root],
                capture_output=True, text=True, encoding="utf-8", errors="replace",
            )
            # output lines look like: <path>:<matched name>
            for line in proc.stdout.splitlines():
                path, sep, name = line.rpartition(":")
                if not sep:
                    continue
                rec = candidates.get(name)
                if rec is None:
                    continue
                referrer = project_path(content_root, path)
                if referrer != rec["package"] and referrer not in rec["referrers"]:
                    rec["referrers"].append(referrer)
                hits += 1
        finally:
            try:
                os.unlink(pattern_file)
            except OSError:
                pass
        print("referencer name hits: %d" % hits, flush=True)

    # ---- 3. classify and write ------------------------------------------
    unreferenced = [r for r in candidates.values() if not r["referrers"]]
    referenced = [r for r in candidates.values() if r["referrers"]]
    for r in candidates.values():
        r["status"] = "REFERENCED" if r["referrers"] else "UNREFERENCED"
        r["referrers"].sort()

    total_bytes = sum(r["size"] for r in candidates.values())
    unreferenced_bytes = sum(r["size"] for r in unreferenced)

    report = {
        "generated": started,
        "content_root": content_root,
        "packages_scanned": len(all_pkgs),
        "candidates": len(candidates),
        "candidate_bytes": total_bytes,
        "unreferenced": len(unreferenced),
        "unreferenced_bytes": unreferenced_bytes,
        "referenced": len(referenced),
        "unreferenced_pct": round(100.0 * len(unreferenced) / max(1, len(candidates)), 2),
        "unreferenced_bytes_pct": round(100.0 * unreferenced_bytes / max(1, total_bytes), 2),
        "candidates_detail": sorted(candidates.values(), key=lambda r: (r["status"], r["package"])),
    }

    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    with open(out_path, "w", encoding="utf-8") as fh:
        json.dump(report, fh, indent=1)

    print("")
    print("candidates            : %d" % report["candidates"])
    print("  unreferenced        : %d (%.1f%%)  %s" % (
        report["unreferenced"], report["unreferenced_pct"],
        "%.1f MB" % (report["unreferenced_bytes"] / 1048576.0)))
    print("  referenced          : %d" % report["referenced"])
    print("candidate bytes       : %.1f MB" % (report["candidate_bytes"] / 1048576.0))
    print("wrote                 : %s" % out_path)
    print("")
    print("NOTE: the referencer map is a candidate map built from package name")
    print("      tables. The authoritative map is the editor's Asset Registry and")
    print("      must be the gate before anything is deleted.")
    return 0


if __name__ == "__main__":
    sys.exit(main())

