#!/usr/bin/env python3
"""Quick breakdown of git dirty files by type."""
import subprocess, json
from pathlib import Path
from collections import Counter

repo = r"C:\EnvironmentPortfolio\BS_GodFile"
result = subprocess.run(
    ["git", "-C", repo, "status", "--porcelain=1"],
    capture_output=True, text=True
)
lines = [l for l in result.stdout.strip().split("\n") if l]

status_codes = Counter()
ext_counter = Counter()
for line in lines:
    # porcelain format: XY filename
    status = line[:2].strip()
    filename = line[3:].strip()
    status_codes[status] += 1
    # get extension
    if "." in filename:
        ext = filename.rsplit(".", 1)[-1]
        ext_counter[ext] += 1
    else:
        ext_counter["(no_ext)"] += 1

print(f"Total dirty files: {len(lines)}")
print("\n=== By Status ===")
for code, count in sorted(status_codes.items(), key=lambda x: -x[1]):
    labels = {"M": "Modified", "A": "Added", "D": "Deleted", "R": "Renamed",
              "?": "Untracked", "U": "Unmerged", "!": "Ignored"}
    name = labels.get(code[0], code)
    print(f"  {code}: {count}  ({name})")

print("\n=== By Extension (top 20) ===")
for ext, count in ext_counter.most_common(20):
    print(f"  .{ext}: {count}")

# List untracked .mcp.json and root-level .py files
print("\n=== Key Files to Check ===")
for line in lines:
    filename = line[3:].strip()
    if ".mcp.json" in filename:
        print(f"  {filename}: {line[:2]}")
    if filename.startswith("check_") or filename.startswith("fix_") or filename.startswith("pie_"):
        print(f"  ROOT DEBRIS: {filename}: {line[:2]}")
    if filename.endswith("bedrock_research.py") or filename.endswith("bedrock_research_run.py") or filename.endswith("bedrock_model_test.py"):
        print(f"  RESEARCH SCRIPT: {filename}: {line[:2]}")
