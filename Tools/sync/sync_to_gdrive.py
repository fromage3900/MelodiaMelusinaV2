"""Sync the live project on C: to the portable copy on G: - ADDITIVELY, WITH BACKUPS.

The two copies have diverged (measured 2026-10-22): C: is 9 days ahead, and G: holds
119 files and 3,332 assets that C: does NOT have, plus a branch history that is on no
remote branch. So this is NOT a mirror operation and NOT a replace operation.

The rules this script obeys:
  * NOTHING on G: is ever deleted.
  * A file that exists only on G: is left alone and reported (it may be the only copy).
  * A file that exists on both is copied C: -> G: only after the G: version is backed
    up into G:/_sync_backup_20261022/<path>.
  * Every action is written to a receipt.

Run:  C:/Python314/python.exe Tools/sync/sync_to_gdrive.py            (dry run)
      C:/Python314/python.exe Tools/sync/sync_to_gdrive.py --apply    (do it)
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import shutil
import stat
import sys
import time

C = r"C:\EnvironmentPortfolio\BS_GodFile"
G = r"G:\EnvironmentPortfolio\BS_GodFile"
BACKUP = os.path.join(G, "_sync_backup_20261022")
RECEIPT = r"C:\EnvironmentPortfolio\BS_GodFile\Saved\Audit\gdrive_sync_20261022.json"

# The trees that carry the project. Content is the bulk; the rest is code and contracts.
TREES = ["Content", "Source", "specs", "Tools", "Docs", "Config", "Plugins",
         "deploy", "RawArt", "Reference", "Scripts", "Imports", "Assignment2",
         # The audit receipts: the evidence behind every claim the project makes.
         # 5.1 GB - the renders, the manifests and the wand FBX/OBJ sources.
         "Saved/Audit"]
# The root files that state the project's authority.
ROOT_FILES = ["CURRENT_STATE.md", "AGENTS.md", "CLAUDE.md", "SYSTEM_MAP.md",
              "DATA_FLOW.md", "_AGENT_WORKING_AGREEMENT.md", "BS_GodFile.uproject"]


def digest(path):
    h = hashlib.sha1()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


# The safety copy of G:'s own files lives on C: only - copying it back to G:
# would be pointless churn.
EXCLUDE = ["Saved/Audit/gdrive_only_20261022",
            # The sync receipt is inside the scope it syncs: without this, every
            # run flags its own output as changed.
            "Saved/Audit/gdrive_sync_20261022.json",
            "Saved/Audit/gdrive_sync_final_20261022.json",
            "Saved/Audit/gdrive_forcecopy_20261022.json"]


def walk_tree(root, tree):
    base = os.path.join(root, tree.replace('/', os.sep))
    out = {}
    if not os.path.isdir(base):
        return out
    for dirpath, dirs, files in os.walk(base):
        for f in files:
            full = os.path.join(dirpath, f)
            rel = os.path.relpath(full, root).replace("\\", "/")
            if any(rel.startswith(x) for x in EXCLUDE):
                continue
            try:
                out[rel] = os.path.getsize(full)
            except OSError:
                pass
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true", help="actually copy (default is a dry run)")
    args = ap.parse_args()

    if not os.path.isdir(G):
        print("G: is not mounted")
        return 2

    print("=" * 72)
    print("G: SYNC - %s -> %s   (%s)" % (C, G, "APPLY" if args.apply else "DRY RUN"))
    print("=" * 72)

    plan = {"source": C, "target": G, "apply": args.apply,
            "copied": [], "backed_up": [], "identical": [], "only_on_g": [],
            "errors": [], "bytes_copied": 0}

    index = {}
    for tree in TREES:
        index.update(walk_tree(C, tree))
    for name in ROOT_FILES:
        p = os.path.join(C, name)
        if os.path.isfile(p):
            index[name] = os.path.getsize(p)

    gindex = {}
    for tree in TREES:
        gindex.update(walk_tree(G, tree))
    for name in ROOT_FILES:
        p = os.path.join(G, name)
        if os.path.isfile(p):
            gindex[name] = os.path.getsize(p)

    print("C: files in scope: %d    G: files in scope: %d" % (len(index), len(gindex)))

    t0 = time.time()
    for i, (rel, size) in enumerate(sorted(index.items())):
        gpath = os.path.join(G, rel.replace("/", os.sep))
        cpath = os.path.join(C, rel.replace("/", os.sep))
        try:
            if not os.path.exists(gpath):
                action = "copy"
            else:
                # Equality by size AND mtime: hashing tens of thousands of assets over
                # external media takes hours, and copy2 preserves the mtime, so a synced
                # file compares equal without reading it.
                gstat = os.stat(gpath)
                cstat = os.stat(cpath)
                if gstat.st_size == cstat.st_size and int(gstat.st_mtime) == int(cstat.st_mtime):
                    plan["identical"].append(rel)
                    continue
                action = "overwrite"
        except OSError as exc:
            plan["errors"].append({"file": rel, "error": str(exc)})
            continue

        if args.apply:
            try:
                if action == "overwrite":
                    # The G: version is kept: it may be the only copy of something.
                    # Some G: files carry the read-only attribute, and a read-only
                    # destination cannot be overwritten - clear it first.
                    if os.path.exists(gpath):
                        try:
                            os.chmod(gpath, stat.S_IWRITE | stat.S_IREAD)
                        except OSError:
                            pass
                    bpath = os.path.join(BACKUP, rel.replace("/", os.sep))
                    os.makedirs(os.path.dirname(bpath), exist_ok=True)
                    shutil.copy2(gpath, bpath)
                    plan["backed_up"].append(rel)
                os.makedirs(os.path.dirname(gpath), exist_ok=True)
                shutil.copy2(cpath, gpath)
                plan["copied"].append({"file": rel, "action": action, "bytes": size})
                plan["bytes_copied"] += size
            except Exception as exc:  # noqa: BLE001
                plan["errors"].append({"file": rel, "error": str(exc)})
        else:
            plan["copied"].append({"file": rel, "action": action, "bytes": size})
            plan["bytes_copied"] += size

        if (i + 1) % 500 == 0:
            print("  ... %d/%d  (%.1f GB planned)" % (i + 1, len(index), plan["bytes_copied"] / 1073741824.0))

    plan["only_on_g"] = sorted(set(gindex) - set(index))
    # Keep the receipt small: the full lists of 95k identical paths are noise, and the
    # receipt is itself inside the synced scope.
    identical_count = len(plan["identical"])
    only_on_g_count = len(plan["only_on_g"])
    plan["identical"] = {"count": identical_count, "sample": plan["identical"][:50]}
    plan["only_on_g"] = {"count": only_on_g_count, "sample": plan["only_on_g"][:50]}
    elapsed = time.time() - t0

    print("\n--- plan ---")
    print("  files to copy/update : %d  (%.2f GB)" % (len(plan["copied"]), plan["bytes_copied"] / 1073741824.0))
    print("  already identical    : %d" % identical_count)
    print("  only on G: (left)    : %d" % only_on_g_count)
    print("  elapsed              : %.1fs" % elapsed)
    if not args.apply:
        print("  (dry run - nothing was written)")
    else:
        print("  backups written to   : %s" % BACKUP)

    os.makedirs(os.path.dirname(RECEIPT), exist_ok=True)
    with open(RECEIPT, "w", encoding="utf-8") as fh:
        json.dump(plan, fh, indent=2)
    print("receipt:", RECEIPT)
    return 1 if plan["errors"] else 0


if __name__ == "__main__":
    sys.exit(main())
