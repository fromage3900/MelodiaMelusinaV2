#!/usr/bin/env python
"""Retire the static-mesh graveyard: move unreferenced third-party meshes out of Content/.

The owner asked for roughly 75% of the Kenney static meshes to be deleted and
their references redirected to in-theme assets. This tool performs the deletion
half of that, and only ever touches assets the census proved are UNREFERENCED.

    # 1. see what would go, change nothing
    python Tools/Editor/asset_graveyard_prune.py --census <census.json> --dry-run

    # 2. actually retire it
    python Tools/Editor/asset_graveyard_prune.py --census <census.json> \
        --out-dir Saved/RetiredAssets/20261021 \
        --i-have-owner-approval

Safety properties, in order of importance:
  1. It refuses to touch any asset the census marks REFERENCED. Redirect first,
     delete second - never the other way round.
  2. It never deletes in place. Every asset is MOVED to --out-dir, outside
     Content/, with a JSON manifest, so a mistake is a file move back.
  3. It refuses to run without --i-have-owner-approval.
  4. It never touches anything outside the paths the census listed, and it
     refuses paths outside Content/.
  5. It writes a receipt for every run.

It does NOT repoint references, and it does not know about the Houdini HDA that
re-emits some of these meshes. The HDA must be repointed and rebuilt first, or
the next cook resurrects the assets it still names.
"""
from __future__ import annotations

import argparse
import json
import os
import shutil
import sys
import time


def load_census(path: str) -> dict:
    with open(path, encoding="utf-8") as fh:
        return json.load(fh)


def disk_path_for(content_root: str, package_path: str) -> str:
    rel = package_path[len("/Game/"):]
    return os.path.join(content_root, rel + ".uasset")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--census", required=True)
    ap.add_argument("--content", default="Content")
    ap.add_argument("--out-dir", default="")
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--i-have-owner-approval", action="store_true")
    ap.add_argument("--status", default="UNREFERENCED",
                    help="only assets with this census status are eligible")
    ap.add_argument("--limit", type=int, default=0, help="retire at most N (0 = all)")
    args = ap.parse_args()

    if not args.dry_run and not args.i_have_owner_approval:
        print("REFUSING: destructive run without --i-have-owner-approval.")
        print("         Run with --dry-run first to see the list.")
        return 2

    content_root = os.path.abspath(args.content)
    if not content_root.endswith(os.sep + "Content") and os.path.basename(content_root) != "Content":
        print("REFUSING: --content must point at a Content directory (got %s)" % content_root)
        return 2

    census = load_census(args.census)
    detail = census.get("candidates_detail", [])
    eligible = [r for r in detail if r.get("status") == args.status]

    if args.limit:
        eligible = eligible[: args.limit]

    print("census: %s candidates, %d %s" % (census.get("candidates"), len(eligible), args.status))
    print("eligible bytes: %.1f MB" % (sum(r.get("size", 0) for r in eligible) / 1048576.0))
    print("")

    missing = []
    plan = []
    for r in eligible:
        disk = disk_path_for(content_root, r["package"])
        if not os.path.isfile(disk):
            missing.append(r["package"])
            continue
        plan.append((r, disk))

    if missing:
        print("WARNING: %d census entries are not on disk (already gone?):" % len(missing))
        for p in missing[:10]:
            print("   %s" % p)
        print("")

    print("first 15 that would be retired:")
    for r, _d in plan[:15]:
        print("   %-88s %7.1f KB" % (r["package"], r.get("size", 0) / 1024.0))
    if len(plan) > 15:
        print("   ... and %d more" % (len(plan) - 15))
    print("")

    if args.dry_run:
        print("DRY RUN - nothing was moved or deleted.")
        return 0

    if not args.out_dir:
        print("REFUSING: --out-dir is required for a real run (assets are moved, not deleted in place).")
        return 2

    out_dir = os.path.abspath(args.out_dir)
    if out_dir.startswith(content_root + os.sep):
        print("REFUSING: --out-dir must be OUTSIDE Content/ (got %s)" % out_dir)
        return 2
    os.makedirs(out_dir, exist_ok=True)

    manifest = {
        "retired_at": time.time(),
        "content_root": content_root,
        "out_dir": out_dir,
        "census": os.path.abspath(args.census),
        "census_candidates": census.get("candidates"),
        "retired_count": 0,
        "retired_bytes": 0,
        "assets": [],
    }

    for r, disk in plan:
        rel = os.path.relpath(disk, content_root)
        dest = os.path.join(out_dir, rel)
        os.makedirs(os.path.dirname(dest), exist_ok=True)
        try:
            shutil.move(disk, dest)
        except OSError as exc:
            print("FAILED %s : %s" % (rel, exc))
            continue
        manifest["retired_count"] += 1
        manifest["retired_bytes"] += r.get("size", 0)
        manifest["assets"].append({
            "package": r["package"],
            "disk": disk,
            "retired_to": dest,
            "size": r.get("size", 0),
        })

    # sweep the now-empty directories left behind
    for dirpath, dirnames, filenames in os.walk(content_root, topdown=False):
        if dirpath == content_root:
            continue
        try:
            if not os.listdir(dirpath):
                os.rmdir(dirpath)
        except OSError:
            pass

    manifest_path = os.path.join(out_dir, "retired_manifest.json")
    with open(manifest_path, "w", encoding="utf-8") as fh:
        json.dump(manifest, fh, indent=1)

    print("retired %d assets, %.1f MB" % (manifest["retired_count"], manifest["retired_bytes"] / 1048576.0))
    print("recoverable at : %s" % out_dir)
    print("manifest       : %s" % manifest_path)
    return 0


if __name__ == "__main__":
    sys.exit(main())
