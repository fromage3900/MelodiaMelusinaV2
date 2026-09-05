#!/usr/bin/env python3
"""Quick breakdown of the ACTIVE checkout's dirty files by type."""
from __future__ import annotations

import subprocess
from collections import Counter
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]

result = subprocess.run(
    ["git", "-C", str(REPO), "status", "--porcelain=1"],
    capture_output=True,
    text=True,
)
if result.returncode != 0:
    raise SystemExit(result.stderr.strip() or "git status failed")

lines = [line for line in result.stdout.splitlines() if line]

status_codes = Counter()
ext_counter = Counter()

for line in lines:
    status = line[:2].strip()
    filename = line[3:].strip()
    status_codes[status] += 1
    if "." in filename:
        ext_counter[filename.rsplit(".", 1)[-1]] += 1
    else:
        ext_counter["(no_ext)"] += 1

branch = subprocess.run(
    ["git", "-C", str(REPO), "branch", "--show-current"],
    capture_output=True,
    text=True,
).stdout.strip()
head = subprocess.run(
    ["git", "-C", str(REPO), "rev-parse", "--short=12", "HEAD"],
    capture_output=True,
    text=True,
).stdout.strip()

print(f"Repo:   {REPO}")
print(f"Branch: {branch}")
print(f"HEAD:   {head}")
print(f"Total dirty files: {len(lines)}")

print("\n=== By Status ===")
for code, count in sorted(status_codes.items(), key=lambda x: -x[1]):
    labels = {
        "M": "Modified",
        "A": "Added",
        "D": "Deleted",
        "R": "Renamed",
        "?": "Untracked",
        "U": "Unmerged",
        "!": "Ignored",
    }
    name = labels.get(code[0], code)
    print(f"  {code}: {count}  ({name})")

print("\n=== By Extension (top 20) ===")
for ext, count in ext_counter.most_common(20):
    print(f"  .{ext}: {count}")

print("\n=== Key Files to Check ===")
for line in lines:
    filename = line[3:].strip()
    if ".mcp.json" in filename:
        print(f"  {filename}: {line[:2]}")
    if filename.startswith(("check_", "fix_", "pie_")):
        print(f"  ROOT DEBRIS: {filename}: {line[:2]}")
    if filename.endswith(("bedrock_research.py", "bedrock_research_run.py", "bedrock_model_test.py")):
        print(f"  RESEARCH SCRIPT: {filename}: {line[:2]}")
