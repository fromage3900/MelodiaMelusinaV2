#!/usr/bin/env python3
"""
doc_lint.py — Documentation stability gate for BS_GodFile.

Checks:
  1. Broken relative links in markdown files (Docs/ and root)
  2. Duplicate doc basenames across the repo
  3. README badge/repo-map count drift vs actual repo state
  4. CURRENT_STATE.md timestamp freshness (warns if > 7 days old)

Exit 0 = all checks passed (warnings OK)
Exit 1 = one or more errors found

Usage:
  python Tools/doc_lint.py              # full check
  python Tools/doc_lint.py --fix        # auto-fix what is safe to fix
  python Tools/doc_lint.py --ci         # CI mode: stricter, no warnings
"""

import argparse
import os
import re
import subprocess
import sys
from collections import defaultdict
from datetime import datetime, timedelta
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent


# ── Helpers ──────────────────────────────────────────────────────────

def find_md_files() -> list[Path]:
    """Tracked .md files in Docs/, repo root, and key project dirs.
    Excludes Plugins/ (third-party), Saved/ (runtime evidence), and .agents/.claude/.hermes (tool-managed)."""
    result = subprocess.run(
        ["git", "-C", str(REPO), "ls-files", "*.md"],
        capture_output=True, text=True
    )
    files = []
    for line in result.stdout.strip().split("\n"):
        if not line:
            continue
        # Skip third-party and tool-managed directories
        if line.startswith(("Plugins/", "Saved/", ".agents/", ".claude/", ".hermes/", "Website/", "Imports/", "deploy/", "Content/", "Chapters/", "melodia-design-system/", "hda/", "Reference/", "RawArt/")):
            continue
        files.append(REPO / line)
    return files


def find_all_files() -> list[str]:
    """All tracked files (for counting)."""
    result = subprocess.run(
        ["git", "-C", str(REPO), "ls-files"],
        capture_output=True, text=True
    )
    return result.stdout.strip().split("\n") if result.stdout.strip() else []


def count_tracked(pattern: str) -> int:
    """Count tracked files matching a glob pattern."""
    result = subprocess.run(
        ["git", "-C", str(REPO), "ls-files", pattern],
        capture_output=True, text=True
    )
    return len([l for l in result.stdout.strip().split("\n") if l])


# ── Check 1: Broken relative links ──────────────────────────────────

def check_broken_links(md_files: list[Path]) -> list[dict]:
    """Find markdown links that point to non-existent files."""
    broken = []
    for md in md_files:
        try:
            content = md.read_text(encoding="utf-8", errors="ignore")
        except Exception:
            continue
        for match in re.finditer(r"\[([^\]]+)\]\(([^)]+)\)", content):
            link_text, link_path = match.group(1), match.group(2)
            # Skip URLs, anchors, mailto, file://
            if link_path.startswith(("http://", "https://", "#", "mailto:", "file://")):
                continue
            # Skip UE asset paths (not filesystem paths)
            if link_path.startswith(("/Game/", "/Engine/")):
                continue
            # Skip links that are clearly not file paths (contain spaces, wildcards, etc.)
            if " " in link_path or "*" in link_path or "<" in link_path or ">" in link_path:
                continue
            # Skip anchor-only links within the same file
            if link_path.startswith("#"):
                continue
            # Resolve relative to the md file's directory
            resolved = (md.parent / link_path).resolve()
            if not resolved.exists():
                broken.append({
                    "file": str(md.relative_to(REPO)),
                    "link": link_path,
                    "text": link_text,
                })
    return broken


# ── Check 2: Duplicate doc basenames ────────────────────────────────

def check_duplicate_names(md_files: list[Path]) -> list[dict]:
    """Find markdown files with the same basename in different directories.
    Skips expected duplicates (README, SKILL, CHANGELOG, etc.) and files in
    different top-level directories that happen to share a name."""
    # Expected duplicate basenames — these are fine in multiple locations
    EXPECTED_DUPES = {
        "readme.md", "skill.md", "changelog.md", "contributing.md",
        "security.md", "code_of_conduct.md", "agents.md", "provenance.md",
        "evidence.md", "bug_report.md", "feature_request.md",
    }
    by_name: dict[str, list[str]] = defaultdict(list)
    for md in md_files:
        by_name[md.name.lower()].append(str(md.relative_to(REPO)))
    dupes = []
    for name, paths in by_name.items():
        if len(paths) > 1 and name not in EXPECTED_DUPES:
            dupes.append({"name": name, "paths": sorted(paths)})
    return dupes


# ── Check 3: README count drift ────────────────────────────────────

def check_readme_counts() -> list[dict]:
    """Verify README badge and repo-map numbers match actual repo state."""
    readme = REPO / "README.md"
    if not readme.exists():
        return [{"field": "README.md", "issue": "File not found"}]

    content = readme.read_text(encoding="utf-8", errors="ignore")
    issues = []

    # Badge counts
    badge_checks = [
        (r"uasset-(\d+[\d,]*)_tracked", "*.uasset", "uasset badge"),
        (r"umap-(\d+[\d,]*)_tracked", "*.umap", "umap badge"),
        (r"Plugins-(\d+)_project", None, "plugins badge"),
    ]

    for pattern, git_pattern, label in badge_checks:
        match = re.search(pattern, content)
        if not match:
            continue
        claimed = int(match.group(1).replace(",", ""))
        if git_pattern:
            actual = count_tracked(git_pattern)
        else:
            # Count plugin directories
            plugins_dir = REPO / "Plugins"
            actual = len([d for d in plugins_dir.iterdir() if d.is_dir()]) if plugins_dir.exists() else 0
        if claimed != actual:
            issues.append({
                "field": label,
                "claimed": claimed,
                "actual": actual,
            })

    # Repo map counts
    repo_map_checks = [
        (r"(\d+)\s*C\+\+/header source files", "*.cpp", "C++ source"),
        (r"(\d+)\s*Python automation scripts", "*.py", "Python scripts"),
        (r"(\d+)\s*JSON contract schemas", "*.json", "JSON schemas"),
    ]

    for pattern, git_pattern, label in repo_map_checks:
        match = re.search(pattern, content)
        if not match:
            continue
        claimed = int(match.group(1).replace(",", ""))
        # Count in the right subdirectory
        if "C++" in label:
            actual = len(list((REPO / "Source/BS_GodFile").rglob("*.cpp"))) + \
                     len(list((REPO / "Source/BS_GodFile").rglob("*.h")))
        elif "Python" in label:
            actual = len(list((REPO / "Tools").rglob("*.py")))
        elif "JSON" in label:
            actual = len(list((REPO / "specs").rglob("*.json")))
        else:
            actual = count_tracked(git_pattern)
        if claimed != actual:
            issues.append({
                "field": label,
                "claimed": claimed,
                "actual": actual,
            })

    return issues


# ── Check 4: CURRENT_STATE.md timestamp ────────────────────────────

def check_state_timestamp() -> list[dict]:
    """Warn if CURRENT_STATE.md hasn't been updated recently."""
    state = REPO / "CURRENT_STATE.md"
    if not state.exists():
        return [{"field": "CURRENT_STATE.md", "issue": "File not found"}]

    content = state.read_text(encoding="utf-8", errors="ignore")
    match = re.search(r"\*\*Updated:\*\*\s*(\d{4}-\d{2}-\d{2})", content)
    if not match:
        return [{"field": "CURRENT_STATE.md", "issue": "No **Updated:** date found"}]

    updated = datetime.strptime(match.group(1), "%Y-%m-%d")
    age = (datetime.now() - updated).days
    if age > 7:
        return [{
            "field": "CURRENT_STATE.md",
            "issue": f"Last updated {age} days ago ({match.group(1)}). Consider refreshing.",
        }]
    return []


# ── Main ────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description="Documentation stability gate")
    parser.add_argument("--fix", action="store_true", help="Auto-fix safe issues")
    parser.add_argument("--ci", action="store_true", help="CI mode: treat warnings as errors")
    args = parser.parse_args()

    md_files = find_md_files()
    errors = []
    warnings = []

    # Check 1: Broken links
    broken = check_broken_links(md_files)
    for b in broken:
        errors.append(f"BROKEN LINK: {b['file']} -> {b['link']} (text: '{b['text']}')")

    # Check 2: Duplicate names
    dupes = check_duplicate_names(md_files)
    for d in dupes:
        errors.append(f"DUPLICATE DOC: {d['name']} in {', '.join(d['paths'])}")

    # Check 3: README counts
    count_issues = check_readme_counts()
    for ci in count_issues:
        if "claimed" in ci:
            errors.append(
                f"README COUNT DRIFT: {ci['field']} claims {ci['claimed']}, actual is {ci['actual']}"
            )
        else:
            errors.append(f"README COUNT: {ci['issue']}")

    # Check 4: Timestamp freshness
    ts_issues = check_state_timestamp()
    for ts in ts_issues:
        if args.ci:
            errors.append(f"TIMESTAMP: {ts['issue']}")
        else:
            warnings.append(f"TIMESTAMP: {ts['issue']}")

    # Report
    if warnings:
        print("WARNINGS:")
        for w in warnings:
            print(f"  {w}")
        print()

    if errors:
        print("ERRORS:")
        for e in errors:
            print(f"  {e}")
        print()
        print(f"doc_lint: {len(errors)} error(s), {len(warnings)} warning(s)")
        sys.exit(1)

    print(f"doc_lint: OK ({len(md_files)} docs checked, {len(warnings)} warning(s))")
    sys.exit(0)


if __name__ == "__main__":
    main()
