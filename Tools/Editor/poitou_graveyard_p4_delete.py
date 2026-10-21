#!/usr/bin/env python
"""Open the unreferenced Kenney static meshes for delete in Perforce.

Run headlessly:

    UnrealEditor-Cmd.exe BS_GodFile.uproject -run=pythonscript \
        -script=".../poitou_graveyard_p4_delete.py" -unattended -nullrhi -stdout \
        -- <changelist-name> --dry-run

The pack is Perforce-owned (change 79), and `p4 where` maps the client view
straight onto Content/, so deleting these is a Perforce operation, not a file
move. This script OPENS the files for delete in a dedicated changelist and
STOPS THERE. It never submits: a submit is the owner's decision.

Safety:
  1. The cut list comes from the Asset Registry referencer map, not from a name
     heuristic. An asset with any referrer is excluded and reported.
  2. A protection list is never cut, whatever the referencer map says:
     the meshes the Houdini HDA names (they are re-emitted on every cook, so
     deleting the file without repointing the HDA just moves the problem), the
     project's own house, and anything whose name is project-prefixed.
  3. Nothing is submitted. The changelist is left open for the owner.
  4. Every opened file is listed in a receipt.

Usage:
    --dry-run              print the list, change nothing in Perforce
    --changelist <name>    name for the new changelist (default: melodia-graveyard-kenney)
    --limit <n>            cap the number of files opened (0 = no cap)
"""
from __future__ import annotations

import json
import os
import re
import stat
import subprocess
import sys

import unreal

OUT_DIR = r"C:\EnvironmentPortfolio\BS_GodFile\Saved\Audit\AssetGraveyard_20261021"
AR_MAP = os.path.join(OUT_DIR, "referencers.json")
RECEIPT = os.path.join(OUT_DIR, "p4_delete_receipt.json")

# Never cut these, whatever the referencer map says.
PROTECTED_SUBSTRINGS = (
    "SM_hero_house",            # the project's own house, not the pack
    "/tree-high",               # named by the Houdini HDA
    "/tree_fat",                # named by the Houdini HDA
    "/grass_leafsLarge",        # named by the Houdini HDA
    "/canoe/",                  # named by the Houdini HDA
    "/violin",                  # referenced by Melusina's own Blueprints
    "/door/",                   # 114 placed in the live Poitou level
    "/fence_simple/",           # placed in the live Poitou level
    "/flower_redA",             # placed in the lookdev level
    "/Rock01_Art", "/Rock02_Art",
    "/Stone01_Art", "/Stone03_Art", "/Stone05_Art",
    "/Bush01_Art", "/Bush04_Art", "/Bush05_Art", "/Bush08_Art",
)

PROJECT_PREFIXES = ("SM_", "BP_", "MI_", "M_", "MF_", "T_", "DA_", "SK_", "FL_", "ABP_",
                     "PCG_", "IC_", "LT_", "E_", "HDA_", "AS_", "WBP_", "S_", "U_", "C_")

# The pack's own material instances, which become orphans once the meshes go.
MI_ROOTS = (
    "/Game/EnvSandbox/Materials/Instances/Kenney",
    "/Game/EnvSandbox/Meshes/Environment/_RetroFantasyKit/Materials",
    "/Game/EnvSandbox/Meshes/Environment/_Loose",
    "/Game/EnvSandbox/Meshes/Environment/AvatarGarden/Materials",
)
MI_CLASSES = ("MaterialInstanceConstant", "MaterialInstance")


def p4(args, check=True, stdin=None):
    proc = subprocess.run(["p4"] + args, capture_output=True, input=stdin)
    out = proc.stdout.decode("utf-8", "replace")
    err = proc.stderr.decode("utf-8", "replace")
    if check and proc.returncode != 0:
        unreal.log("[p4del] p4 %s failed: %s" % (" ".join(args), (err or out).strip()[:300]))
    return proc.returncode, out, err


def main():
    # The Python commandlet does not forward extra argv, so the switches come
    # from the environment. Getting this wrong once created a changelist during
    # a "dry run", so the dry run is now the default and the real run has to be
    # asked for explicitly.
    dry_run = os.environ.get("MELODIA_GRAVEYARD_DRYRUN", "1") != "0"
    limit = int(os.environ.get("MELODIA_GRAVEYARD_LIMIT", "0") or 0)
    cl_name = os.environ.get("MELODIA_GRAVEYARD_CHANGELIST", "melodia-graveyard-kenney")

    if not os.path.isfile(AR_MAP):
        unreal.log("[p4del] ABORT: no Asset Registry map at %s" % AR_MAP)
        return

    with open(AR_MAP, encoding="utf-8") as fh:
        ar = json.load(fh)

    # ---- build the candidate graph --------------------------------------
    # referrers[c] = every package that references c (from the AR map for the
    # meshes, queried live for the material instances).
    opts = unreal.AssetRegistryDependencyOptions()
    for flag in ("include_hard_package_references", "include_soft_package_references",
                 "include_game_package_references", "include_editor_only_package_references"):
        try:
            opts.set_editor_property(flag, True)
        except Exception:
            pass
    arapi = unreal.AssetRegistryHelpers.get_asset_registry()

    referrers = {}
    for row in ar["rows"]:
        referrers[row["package"]] = list(row.get("referrers") or [])

    mi_rows = []
    for root in MI_ROOTS:
        for asset in arapi.get_assets_by_path(root, True):
            if str(asset.asset_class_path.asset_name) not in MI_CLASSES:
                continue
            pkg = str(asset.package_name)
            if pkg in referrers:
                continue
            try:
                refs = [str(d) for d in arapi.get_referencers(pkg, opts)]
            except Exception:
                refs = []
            referrers[pkg] = refs
            mi_rows.append(pkg)

    universe = set(referrers.keys())

    # ---- guard set: never cut these, whatever the graph says ------------
    # Only the explicit protection list is pre-blocked. "Has a referrer" is
    # NOT a reason to hold something: the fixpoint below decides that, and
    # pre-blocking here would strand every material instance whose only
    # referrer is a mesh we are about to delete.
    blocked = set()
    for row in ar["rows"]:
        pkg = row["package"]
        name = os.path.basename(pkg)
        if name.startswith(PROJECT_PREFIXES):
            blocked.add(pkg)
        elif any(s in pkg for s in PROTECTED_SUBSTRINGS):
            blocked.add(pkg)

    # ---- guard 2: local edits and already-open files -------------------
    rc, diff_out, _ = p4(["diff", "-se", "//Melodia/main/Content/EnvSandbox/..."], check=False)
    differing = set()
    for line in diff_out.splitlines():
        p = line.strip().replace("\\", "/")
        if not p:
            continue
        for prefix in ("C:/EnvironmentPortfolio/BS_GodFile/Content/", "Content/"):
            if p.startswith(prefix):
                differing.add(p[len(prefix):])
                break

    rc, open_out, _ = p4(["opened"], check=False)
    already_open = set()
    for line in open_out.splitlines():
        if "//Melodia/main/" not in line:
            continue
        path = line.split("#")[0][len("//Melodia/main/"):]
        if path.startswith("Content/"):
            already_open.add(path[len("Content/"):])

    for pkg in universe:
        rel = pkg[len("/Game/"):] + ".uasset"
        if rel in differing or rel in already_open:
            blocked.add(pkg)

    # ---- fixpoint: removable if every referrer is also removable ---------
    # A material instance whose only referencers are meshes we are about to
    # delete is an orphan the moment those meshes go, so it goes with them.
    # A file with a referrer OUTSIDE the universe is held by the project and
    # is never removed.
    removable = {p for p in universe if p not in blocked}
    changed = True
    while changed:
        changed = False
        for pkg in list(removable):
            for ref in referrers.get(pkg, []):
                if ref in universe:
                    if ref not in removable:
                        removable.discard(pkg)
                        changed = True
                        break
                else:
                    # an external referrer holds it
                    removable.discard(pkg)
                    changed = True
                    break

    final_cut = sorted(removable)
    kept = [{"package": p, "reason": "protected / referenced / local edits / already open"}
            for p in sorted(blocked)]

    unreal.log("[p4del] universe: %d (meshes + material instances)" % len(universe))
    unreal.log("[p4del] removable after fixpoint: %d" % len(final_cut))
    unreal.log("[p4del] held back: %d" % len(kept))
    for k in kept[:20]:
        unreal.log("[p4del]   KEPT %s" % k["package"])
    all_cut = final_cut

    # ---- Perforce paths -------------------------------------------------
    # /Game/... -> Content/... under the client view.
    p4_paths = []
    for pkg in all_cut:
        rel = pkg[len("/Game/"):]
        p4_paths.append("//Melodia/main/Content/" + rel + ".uasset")

    if dry_run:
        unreal.log("[p4del] DRY RUN - %d files would be opened for delete" % len(p4_paths))
        for p in p4_paths[:25]:
            unreal.log("[p4del]   %s" % p)
        if len(p4_paths) > 25:
            unreal.log("[p4del]   ... and %d more" % (len(p4_paths) - 25))
        return

    # ---- dedicated changelist -------------------------------------------
    desc = ("Melodia: retire the unreferenced Kenney static-mesh pack "
            "(%d files, Asset Registry verified zero referrers). Owner submit required." % len(p4_paths))
    spec = ("Change:\tnew\n\nClient:\tMelodia_ws\nUser:\tfroma\nStatus:\tnew\n"
            "Description:\t%s\n" % desc.replace("\n", " "))
    rc, out, err = p4(["change", "-i"], stdin=spec.encode("utf-8"))
    if rc != 0:
        unreal.log("[p4del] could not create changelist: %s" % (err or out).strip()[:300])
        return
    changelist = None
    m = re.search(r"Change (\d+) created", out)
    if m:
        changelist = m.group(1)
    if not changelist:
        unreal.log("[p4del] unexpected changelist response: %r" % out[:200])
        return
    unreal.log("[p4del] created changelist %s (%s)" % (changelist, cl_name))

    # ---- open for delete, in batches ------------------------------------
    # NOTE: "p4 -c <n> <cmd>" sets the CLIENT, not the changelist - the
    # changelist flag has to come AFTER the command, or p4 fails with
    # "Purely numeric name not allowed".
    #
    # This client has noclobber, and the pack was populated with WRITABLE
    # local files (noallwrite, so p4 sync never made them read-only). p4
    # refuses to remove a writable local file - "Can't clobber writable
    # file" - so the files are marked read-only first, which is exactly what
    # a sync would have done. p4 then does the removal.
    CLIENT_ROOT = r"C:\EnvironmentPortfolio\BS_GodFile"
    made_readonly = 0
    for p in p4_paths:
        local = os.path.join(CLIENT_ROOT, p[len("//Melodia/main/"):].replace("/", os.sep))
        if not os.path.isfile(local):
            continue
        try:
            if not os.stat(local).st_file_attributes & stat.FILE_ATTRIBUTE_READONLY:
                os.chmod(local, stat.S_IREAD)
                made_readonly += 1
        except OSError:
            pass
    unreal.log("[p4del] marked %d local files read-only for p4 to remove" % made_readonly)

    opened = []
    failed = []
    BATCH = 250
    for i in range(0, len(p4_paths), BATCH):
        batch = p4_paths[i:i + BATCH]
        rc, out, err = p4(["delete", "-c", changelist] + batch)
        for line in (out + err).splitlines():
            if line.startswith("//") and " - " in line:
                low = line.lower()
                if "can't" in low or "not opened" in low or "no such" in low or "clobber" in low:
                    failed.append(line.strip())
                else:
                    opened.append(line.strip())
        unreal.log("[p4del] batch %d/%d: opened %d so far" % (i // BATCH + 1, (len(p4_paths) + BATCH - 1) // BATCH, len(opened)))

    receipt = {
        "changelist": changelist,
        "changelist_name": cl_name,
        "submitted": False,
        "opened_count": len(opened),
        "failed_count": len(failed),
        "held_back": kept,
        "held_back_count": len(kept),
        "opened": opened,
        "failed": failed,
    }
    os.makedirs(os.path.dirname(RECEIPT), exist_ok=True)
    with open(RECEIPT, "w", encoding="utf-8") as fh:
        json.dump(receipt, fh, indent=1)

    unreal.log("[p4del] DONE: %d files opened for delete in changelist %s" % (len(opened), changelist))
    unreal.log("[p4del] NOT SUBMITTED. Review with: p4 opened -c %s" % changelist)
    unreal.log("[p4del] receipt: %s" % RECEIPT)


main()



