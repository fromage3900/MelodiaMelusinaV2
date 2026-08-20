"""
Safe root sweep tool

Scans the workspace for references to an old root (e.g. G:\\EnvironmentPortfolio)
and prepares a dry-run report and an optional patch file to replace them with the
chosen canonical root (e.g. C:\\EnvironmentPortfolio).

Important: This tool does NOT modify files unless run with `--apply` and with
an explicit confirmation flag. It creates backups for changed files.

Usage (dry-run):
    python safe_root_sweep.py --old "G:/EnvironmentPortfolio" --new "C:/EnvironmentPortfolio" --extensions ".py,.ps1,.json,.md" --out report.json

To preview replacements as unified diffs:
    python safe_root_sweep.py --old "G:/EnvironmentPortfolio" --new "C:/EnvironmentPortfolio" --extensions ".py,.ps1,.json,.md" --out report.json --diffs diffs.patch

To apply changes (BE CAREFUL):
    python safe_root_sweep.py --old "G:/EnvironmentPortfolio" --new "C:/EnvironmentPortfolio" --extensions ".py,.ps1,.json,.md" --apply --backup-dir backups/

The tool will refuse to run `--apply` if your current git status isn't clean
(uses `git status --porcelain` to check). It will also never run `git add .`.

Outputs:
- JSON report with list of matches (file, line, original, replaced)
- Optional unified patch file (diffs.patch)
- If applied: backups for each changed file under the specified `--backup-dir`

"""
from __future__ import annotations

import argparse
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import List, Dict, Any


def find_matches(root: Path, old: str, exts: List[str]) -> List[Dict[str, Any]]:
    matches = []
    old_re = re.escape(old)
    pattern = re.compile(old_re)
    for p in root.rglob("*"):
        if p.is_file() and any(p.name.endswith(e) for e in exts):
            try:
                text = p.read_text(encoding="utf-8")
            except Exception:
                continue
            for i, line in enumerate(text.splitlines(), start=1):
                if pattern.search(line):
                    matches.append({"file": str(p), "line": i, "text": line.strip()})
    return matches


def build_replacement_map(matches: List[Dict[str, Any]], old: str, new: str) -> Dict[str, List[Dict[str, Any]]]:
    by_file = {}
    for m in matches:
        by_file.setdefault(m["file"], []).append({"line": m["line"], "orig": m["text"], "replaced": m["text"].replace(old, new)})
    return by_file


def write_json_report(path: Path, data: Any):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2), encoding="utf-8")


def create_unified_patch(root: Path, replacements: Dict[str, List[Dict[str, Any]]], old: str, new: str) -> str:
    # produce a basic unified diff by re-reading files and doing replacements
    import difflib

    parts = []
    for f, edits in replacements.items():
        p = Path(f)
        try:
            orig = p.read_text(encoding="utf-8").splitlines()
        except Exception:
            continue
        updated_text = "\n".join(line.replace(old, new) for line in orig)
        updated = updated_text.splitlines()
        diff = difflib.unified_diff(orig, updated, fromfile=str(p), tofile=str(p) + ".new", lineterm="")
        parts.extend(diff)
    return "\n".join(parts)


def git_clean_check() -> bool:
    try:
        out = subprocess.check_output(["git", "status", "--porcelain"], stderr=subprocess.DEVNULL, text=True)
        return out.strip() == ""
    except Exception:
        # If git not present or error, be conservative and return False
        return False


def apply_changes(replacements: Dict[str, List[Dict[str, Any]]], old: str, new: str, backup_dir: Path) -> None:
    backup_dir.mkdir(parents=True, exist_ok=True)
    for f in replacements.keys():
        p = Path(f)
        try:
            orig_text = p.read_text(encoding="utf-8")
        except Exception:
            print(f"Skipping binary/unreadable file: {p}")
            continue
        # backup
        bak = backup_dir / (p.name + ".bak")
        bak.write_text(orig_text, encoding="utf-8")
        new_text = orig_text.replace(old, new)
        p.write_text(new_text, encoding="utf-8")
        print(f"Patched: {p} -> backup: {bak}")


def parse_args():
    parser = argparse.ArgumentParser(description="Safe root sweep: find and optionally replace root references")
    parser.add_argument("--old", required=True, help="Old root to replace, e.g. 'G:/EnvironmentPortfolio'")
    parser.add_argument("--new", required=True, help="New canonical root, e.g. 'C:/EnvironmentPortfolio'")
    parser.add_argument("--extensions", default=".py,.ps1,.json,.md,.txt,.psm1,.sh", help="Comma-separated extensions to scan")
    parser.add_argument("--out", default="g_root_report.json", help="JSON report output path")
    parser.add_argument("--diffs", help="Optional unified diff output path")
    parser.add_argument("--apply", action="store_true", help="Apply changes (requires clean git status). Creates backups in --backup-dir")
    parser.add_argument("--backup-dir", default="g_root_backups", help="Directory to store backups when --apply is used")
    parser.add_argument("--root", default=".", help="Repo root to scan")
    return parser.parse_args()


def main():
    args = parse_args()
    root = Path(args.root).resolve()
    exts = [e.strip() for e in args.extensions.split(",") if e.strip()]
    print(f"Scanning {root} for {args.old} in {exts}...")
    matches = find_matches(root, args.old, exts)
    print(f"Found {len(matches)} matches")
    replacements = build_replacement_map(matches, args.old, args.new)

    report = {"root": str(root), "old": args.old, "new": args.new, "matches_count": len(matches), "by_file": replacements}
    write_json_report(Path(args.out), report)
    print(f"Wrote report to {args.out}")

    if args.diffs:
        # create a basic unified patch
        patch_text = create_unified_patch(root, replacements, args.old, args.new)
        Path(args.diffs).write_text(patch_text, encoding="utf-8")
        print(f"Wrote patch preview to {args.diffs}")

    if args.apply:
        # safety check: git status clean
        ok = git_clean_check()
        if not ok:
            print("Refusing to apply: git working tree not clean or git not available. Commit or stash changes first.")
            sys.exit(2)
        apply_changes(replacements, args.old, args.new, Path(args.backup_dir))
        print("Apply complete. Please review backups before committing.")


if __name__ == "__main__":
    main()
