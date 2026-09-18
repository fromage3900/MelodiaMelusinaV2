#!/usr/bin/env python3
"""Dry-run triage of the working tree into owner-approvable commit buckets.

Read-only with respect to git: this tool never adds, commits, resets, stashes,
checks out, or cleans. It reads ``git status`` once, sizes every path, applies
the collapse guard (paths deleted by commit 08a608bc must not be re-added),
flags private material that must never be committed, and proposes buckets.

Run:
  python Tools/triage_working_tree.py                 # writes Saved/Audit/working_tree_triage_<date>.json
  python Tools/triage_working_tree.py --print-paths   # also list every path per bucket
  python Tools/triage_working_tree.py --out <path>

Reuses ``changed_paths`` from Tools/source_control_triage.py and the collapse
commit from Tools/guard_collapsed_paths.py so there is one status parser and
one collapse authority.
"""
from __future__ import annotations

import argparse
import json
import subprocess
import sys
from collections import defaultdict
from datetime import date, datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "Tools"))

from guard_collapsed_paths import COLLAPSE  # noqa: E402
from source_control_triage import changed_paths  # noqa: E402

EXT_CLASS = {
    ".uasset": "uasset",
    ".umap": "umap",
    ".py": "py",
    ".md": "md",
    ".json": "json",
    ".cpp": "cpp",
    ".h": "cpp",
    ".cs": "cpp",
    ".ini": "ini",
    ".fbx": "source-art",
    ".blend": "source-art",
    ".png": "image",
    ".jpg": "image",
    ".jpeg": "image",
    ".exr": "image",
    ".wav": "audio",
    ".mp3": "audio",
    ".ogg": "audio",
    ".t3d": "t3d",
    ".txt": "text",
    ".csv": "text",
    ".yml": "yaml",
    ".yaml": "yaml",
}

SIZE_BUCKETS = (
    ("0-64KiB", 64 * 1024),
    ("64KiB-1MiB", 1024 * 1024),
    ("1-10MiB", 10 * 1024 * 1024),
    ("10-100MiB", 100 * 1024 * 1024),
    (">100MiB", float("inf")),
)

# Paths that may never land in the game repo (private-repo rule).
MUST_NOT_COMMIT_PREFIXES = ("Humber_FinalYear_Prep/",)
MUST_NOT_COMMIT_TOKENS = (
    "resume", "cover_letter", "coverletter", "transcript", "personal",
    "career", "school", "humber", "grades", "passport", "tax",
)

# Paths already flagged by CURRENT_STATE as held for owner sign-off.
HELD_FOR_OWNER = ("Config/DefaultEngine.ini",)

# Vendor / marketplace packs: size and licence decisions belong to the owner.
THIRD_PARTY_PREFIXES = (
    "Content/UltraDynamicSky/",
    "Content/ArtOfShader/",
    "Content/Brushify",
    "Content/Greybox_Kit/Brushify",
    "Content/Textures/sbs_-_",
    "Content/Textures/70_Japanese_Ornament_Alphas",
    "Content/TurnBasedJRPGTemplate/",
    "Content/KawaiiPhysics",
)

# Derived / cache material under Content that should be gitignored, not committed.
DERIVED_MARKERS = ("_Scratch/", "/LOOKDEV_", "Autosaves/", "/Backup/", "__ExternalActors__/_Scratch")


def _git(*args: str) -> str:
    return subprocess.run(
        ["git", "-C", str(ROOT), *args], text=True, capture_output=True, check=False
    ).stdout


def _collapsed_paths() -> set[str]:
    raw = subprocess.run(
        ["git", "-C", str(ROOT), "diff", "--no-renames", "--diff-filter=D", "--name-only", "-z",
         COLLAPSE + "^", COLLAPSE],
        capture_output=True, check=False,
    ).stdout
    return {p.decode("utf-8") for p in raw.split(b"\0") if p}


def _size_bucket(size: int) -> str:
    for label, ceiling in SIZE_BUCKETS:
        if size < ceiling:
            return label
    return SIZE_BUCKETS[-1][0]


def _status_kind(code: str) -> str:
    if code == "??":
        return "untracked"
    if "D" in code:
        return "deleted"
    if "R" in code:
        return "renamed"
    if "A" in code:
        return "added"
    if "M" in code:
        return "modified"
    return "other"


def _bucket_for(path: str, kind: str, ext_class: str, collapsed: set[str]) -> tuple[str, str]:
    """Return (bucket, reason)."""
    lower = path.lower()
    if path.startswith(MUST_NOT_COMMIT_PREFIXES) or any(t in lower for t in MUST_NOT_COMMIT_TOKENS):
        return "MUST-NOT-COMMIT", "private-repo rule: personal/school/career material"
    if path in HELD_FOR_OWNER:
        return "HELD-FOR-OWNER", "flagged in CURRENT_STATE; needs SKIP_PROTECTION=1 sign-off"
    if kind in {"untracked", "added"} and path in collapsed:
        return "COLLAPSE-GUARD-FAIL", f"re-adds a path deleted by {COLLAPSE}"
    if kind == "deleted":
        return "DELETIONS-VERIFY", "confirm deletion is intentional and not shadowing 08a608bc"
    if any(m in path for m in DERIVED_MARKERS):
        return "GITIGNORE-CANDIDATE", "derived/scratch material under Content"
    if path.startswith("Content/Python/rainbow_"):
        return "RETIRE-INTO-WORLD-COMPILER", "scratch rainbow_*.py superseded by Tools/world_compiler.py"
    if path.startswith("Content/Melodia/Maps/L_MelusinaMorning") or "L_MelusinaMorning" in path:
        return "LAND-MORNING", "L_MelusinaMorning map + external actors (Phase 0 scoped PR)"
    if "ChoralSheep" in path or "/Sheep" in path:
        return "LAND-SHEEP", "Choral Sheep retarget/anim/VFX (Phase 0 scoped PR)"
    if path.startswith(("Tools/", "Content/Python/", "deploy/", "specs/", ".agents/", ".claude/", ".codex/", ".hermes/")):
        return "LAND-TOOLING", "scripts/specs/agent context"
    if path.startswith("Docs/") or ext_class == "md":
        return "LAND-DOCS", "documentation"
    if path.startswith(("Source/", "Plugins/")):
        return "LAND-SOURCE", "C++/plugin source"
    if path.startswith("Config/"):
        return "HELD-FOR-OWNER", "Config changes need owner sign-off"
    if path.startswith(THIRD_PARTY_PREFIXES):
        return "THIRD-PARTY-PACK", "marketplace/vendor pack; owner decides LFS vs external store (license + size)"
    if path.startswith("Content/") and ext_class == "image":
        return "SOURCE-IMAGES-LFS", "raw texture sources under Content; belong in LFS or an external store, not plain git"
    if path.startswith("Content/") and ext_class in {"uasset", "umap"}:
        return "LAND-CONTENT-REVIEW", "binary content; review per folder before scoped PR"
    if path.startswith("Saved/"):
        return "GITIGNORE-CANDIDATE", "Saved/ is runtime output"
    return "REVIEW", "unclassified"


def build_report() -> dict:
    entries = changed_paths()
    collapsed = _collapsed_paths()
    branch = _git("branch", "--show-current").strip()
    head = _git("rev-parse", "--short=12", "HEAD").strip()
    ahead_behind = _git("rev-list", "--left-right", "--count", "HEAD...origin/main").strip().split()

    rows: list[dict] = []
    buckets: dict[str, dict] = defaultdict(lambda: {"count": 0, "bytes": 0, "paths": []})
    by_top: dict[str, int] = defaultdict(int)
    by_ext: dict[str, int] = defaultdict(int)
    by_kind: dict[str, int] = defaultdict(int)
    by_size: dict[str, int] = defaultdict(int)
    total_bytes = 0

    for entry in entries:
        path = entry["path"]
        kind = _status_kind(entry["status"])
        suffix = Path(path).suffix.lower()
        ext_class = EXT_CLASS.get(suffix, "other")
        fs_path = ROOT / path
        size = fs_path.stat().st_size if fs_path.is_file() else 0
        top = path.split("/", 1)[0] if "/" in path else "(root)"
        bucket, reason = _bucket_for(path, kind, ext_class, collapsed)
        guard_verdict = "FAIL" if bucket == "COLLAPSE-GUARD-FAIL" else "PASS"
        row = {
            "path": path,
            "status": entry["status"],
            "kind": kind,
            "top": top,
            "ext_class": ext_class,
            "bytes": size,
            "size_bucket": _size_bucket(size),
            "guard_verdict": guard_verdict,
            "bucket": bucket,
            "reason": reason,
        }
        rows.append(row)
        b = buckets[bucket]
        b["count"] += 1
        b["bytes"] += size
        b["paths"].append(path)
        by_top[top] += 1
        by_ext[ext_class] += 1
        by_kind[kind] += 1
        by_size[row["size_bucket"]] += 1
        total_bytes += size

    ordered = dict(sorted(buckets.items(), key=lambda kv: -kv[1]["count"]))
    for b in ordered.values():
        b["mib"] = round(b["bytes"] / (1024 * 1024), 2)

    # Private material that is ALREADY tracked (modified, not untracked) is a
    # standing violation of the private-repo rule, not just a pending one.
    tracked_private = [
        r["path"] for r in rows
        if r["bucket"] == "MUST-NOT-COMMIT" and r["kind"] in {"modified", "deleted", "renamed"}
    ]
    sensitive_masters = [
        r["path"] for r in rows
        if r["kind"] == "modified" and (
            "/MPC_" in r["path"] or "/Frozen/" in r["path"] or r["path"].startswith("Config/")
        )
    ]

    return {
        "schema": "working_tree_triage.v1",
        "generated_utc": datetime.now(timezone.utc).isoformat(),
        "repo": str(ROOT),
        "branch": branch,
        "head": head,
        "ahead_behind_origin_main": {
            "ahead": int(ahead_behind[0]) if len(ahead_behind) == 2 else None,
            "behind": int(ahead_behind[1]) if len(ahead_behind) == 2 else None,
        },
        "collapse_commit": COLLAPSE,
        "collapsed_path_count": len(collapsed),
        "total_changes": len(rows),
        "total_mib": round(total_bytes / (1024 * 1024), 2),
        "by_top_folder": dict(sorted(by_top.items(), key=lambda kv: -kv[1])),
        "by_ext_class": dict(sorted(by_ext.items(), key=lambda kv: -kv[1])),
        "by_kind": dict(by_kind),
        "by_size_bucket": dict(by_size),
        "buckets": ordered,
        "flags": {
            "tracked_private_paths": tracked_private,
            "modified_sensitive_masters": sensitive_masters,
        },
        "rows": rows,
        "policy": {
            "dry_run": True,
            "git_writes": "none",
            "next_step": "owner approves buckets; land LAND-* as scoped PRs per CURRENT_STATE Phase 0 "
                         "(editor closed -> PR to main -> UBT rebuild)",
        },
    }


def print_table(report: dict, print_paths: bool) -> None:
    print(f"Repo   : {report['repo']}")
    print(f"Branch : {report['branch']} @ {report['head']}  "
          f"(ahead {report['ahead_behind_origin_main']['ahead']} / behind {report['ahead_behind_origin_main']['behind']} origin/main)")
    print(f"Changes: {report['total_changes']}  ({report['total_mib']} MiB on disk)")
    print(f"Kinds  : {report['by_kind']}")
    print()
    print(f"{'bucket':30} {'count':>6} {'MiB':>10}  action")
    actions = {
        "LAND-MORNING": "scoped PR #1 (map + external actors)",
        "LAND-SHEEP": "scoped PR #2",
        "LAND-TOOLING": "scoped PR #3",
        "LAND-DOCS": "scoped PR #4",
        "LAND-SOURCE": "scoped PR (editor closed, UBT rebuild after)",
        "LAND-CONTENT-REVIEW": "review per folder, then scoped PRs",
        "RETIRE-INTO-WORLD-COMPILER": "delete after Tools/world_compiler.py lands",
        "DELETIONS-VERIFY": "confirm each; guard PASS means none shadow 08a608bc",
        "GITIGNORE-CANDIDATE": "owner approves .gitignore exceptions",
        "MUST-NOT-COMMIT": "move to C:/EnvironmentPortfolio/_offgame/",
        "THIRD-PARTY-PACK": "owner: LFS or external store; never plain git",
        "SOURCE-IMAGES-LFS": "owner: LFS or external store; never plain git",
        "HELD-FOR-OWNER": "owner sign-off (SKIP_PROTECTION=1)",
        "COLLAPSE-GUARD-FAIL": "BLOCK: re-adds collapsed path",
        "REVIEW": "unclassified; owner glance",
    }
    for name, b in report["buckets"].items():
        print(f"{name:30} {b['count']:>6} {b['mib']:>10}  {actions.get(name, '')}")
        if print_paths:
            for p in b["paths"]:
                print(f"    {p}")
    print()
    print("Top folders :", report["by_top_folder"])
    print("Ext classes :", report["by_ext_class"])
    flags = report["flags"]
    if flags["tracked_private_paths"]:
        print("\nFLAG tracked private paths (already in history; needs owner decision on filter/untrack):")
        for p in flags["tracked_private_paths"]:
            print(f"    {p}")
    if flags["modified_sensitive_masters"]:
        print("\nFLAG modified MPC / Frozen / Config assets (single-writer + owner sign-off rules apply):")
        for p in flags["modified_sensitive_masters"]:
            print(f"    {p}")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--out", type=Path, default=None)
    parser.add_argument("--print-paths", action="store_true")
    args = parser.parse_args()

    report = build_report()
    out = args.out or (ROOT / "Saved" / "Audit" / f"working_tree_triage_{date.today().isoformat()}.json")
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8")
    print_table(report, args.print_paths)
    print(f"\nReport: {out}")
    fails = report["buckets"].get("COLLAPSE-GUARD-FAIL", {}).get("count", 0)
    return 1 if fails else 0


if __name__ == "__main__":
    raise SystemExit(main())
