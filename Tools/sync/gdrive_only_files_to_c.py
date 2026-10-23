"""Safety copy: the files that exist ONLY on G: get a second home on C:.

Measured 2026-10-22: G: holds 119 dirty files and ~17.9k paths that C: does not have,
including the Painterly 4K texture set and the toon master variants. Their branch
history (wip/main-local-20261013, HEAD 688b688cc) is on NO remote branch, so G: is
their only copy. This copies them onto C: as insurance - it touches neither side's
git state and deletes nothing.

Run: C:/Python314/python.exe Tools/sync/gdrive_only_files_to_c.py [--apply]
"""
from __future__ import annotations

import argparse
import json
import os
import shutil
import sys

C = r"C:\EnvironmentPortfolio\BS_GodFile"
G = r"G:\EnvironmentPortfolio\BS_GodFile"
DEST = os.path.join(C, "Saved", "Audit", "gdrive_only_20261022")
RECEIPT = os.path.join(C, "Saved", "Audit", "gdrive_only_20261022.json")
TREES = ["Content", "Source", "specs", "Tools", "Docs", "Config", "Plugins",
         "RawArt", "Reference", "Scripts", "Imports", "deploy"]


def index(root, tree):
    base = os.path.join(root, tree)
    out = set()
    if not os.path.isdir(base):
        return out
    for dirpath, dirs, files in os.walk(base):
        for f in files:
            out.add(os.path.relpath(os.path.join(dirpath, f), root).replace("\\", "/"))
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true")
    args = ap.parse_args()

    cfiles = set()
    for tree in TREES:
        cfiles |= index(C, tree)
    gfiles = set()
    for tree in TREES:
        gfiles |= index(G, tree)
    only = sorted(gfiles - cfiles)
    print("only on G: %d files" % len(only))

    copied, skipped, errors = [], [], []
    total = 0
    for rel in only:
        src = os.path.join(G, rel.replace("/", os.sep))
        dst = os.path.join(DEST, rel.replace("/", os.sep))
        try:
            size = os.path.getsize(src)
        except OSError:
            errors.append({"file": rel, "error": "unreadable"})
            continue
        if args.apply:
            try:
                os.makedirs(os.path.dirname(dst), exist_ok=True)
                shutil.copy2(src, dst)
                copied.append({"file": rel, "bytes": size})
                total += size
            except Exception as exc:  # noqa: BLE001
                errors.append({"file": rel, "error": str(exc)})
        else:
            copied.append({"file": rel, "bytes": size})
            total += size

    print("%s %d files (%.2f GB) -> %s" % ("would copy" if not args.apply else "copied",
                                           len(copied), total / 1073741824.0, DEST))
    print("errors: %d" % len(errors))
    os.makedirs(os.path.dirname(RECEIPT), exist_ok=True)
    with open(RECEIPT, "w", encoding="utf-8") as fh:
        json.dump({"source": G, "destination": DEST, "apply": args.apply,
                   "only_on_g": len(only), "copied": copied, "errors": errors}, fh, indent=2)
    print("receipt:", RECEIPT)
    return 1 if errors else 0


if __name__ == "__main__":
    sys.exit(main())
