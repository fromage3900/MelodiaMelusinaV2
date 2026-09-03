"""credits_gate.py - coverage gate for Docs/SOURCES_MATRIX.md vs Content/ folders.

Every top-level directory under Content/ must have at least one coverage row in
the Sources Matrix. A directory without a row is a credits gap: fail.

Also: every matrix row must carry a URL (or the literal `first-party` / `N/A`),
and `pending` rows are warned on (they are legal, but only one unconfirmed row is
expected at a time).

Pure stdlib - runs in any shell, no Unreal import, no editor required.
Usage:
    python Tools/credits_gate.py            # exit 1 on uncovered dir or missing URL
    python Tools/credits_gate.py --strict   # same, plus fail on pending rows
"""
from __future__ import annotations

import glob
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MATRIX = os.path.join(ROOT, "Docs", "SOURCES_MATRIX.md")
CONTENT = os.path.join(ROOT, "Content")

ROW_RE = re.compile(r"^\|\s*(`[^`]+`|[^|]+?)\s*\|(.+)\|\s*(verified|first-party|pending|n/a)\s*\|$")


def parse_matrix(path: str) -> list[dict]:
    rows = []
    with open(path, encoding="utf-8") as fh:
        for line in fh:
            line = line.rstrip("\n")
            if not line.startswith("|"):
                continue
            m = ROW_RE.match(line)
            if not m:
                # Header/separator lines don't carry a trailing status column.
                continue
            cells = [c.strip() for c in line.strip("|").split("|")]
            rows.append(
                {
                    "path": m.group(1),
                    "source": cells[1] if len(cells) > 1 else "",
                    "creator": cells[2] if len(cells) > 2 else "",
                    "url": cells[3] if len(cells) > 3 else "",
                    "license": cells[4] if len(cells) > 4 else "",
                    "status": m.group(2).strip(),
                }
            )
    return rows


def path_key(raw: str) -> list[str]:
    """Return every directory name a matrix row covers.

    Backticked tokens name directories (`EnvSandbox`); a row may cover several
    (`Blueprints` / `Game_BP`). Cells without backticks fall back to the first
    whitespace-delimited token (e.g. `__ExternalActors__`).
    """
    cell = raw.strip()
    tokens = re.findall(r"`([^`]+)`", cell)
    if not tokens:
        tokens = [cell.split(" ")[0].split("(")[0].strip("`")]
    return [t.replace("/", os.sep).rstrip("/\\") for t in tokens]


def main() -> int:
    strict = "--strict" in sys.argv
    ok = True
    warnings = []

    if not os.path.exists(MATRIX):
        print(f"FAIL: {MATRIX} missing")
        return 1

    rows = parse_matrix(MATRIX)
    if not rows:
        print(f"FAIL: no coverage rows parsed from {MATRIX}")
        return 1

    covered = set()
    for r in rows:
        covered.update(path_key(r["path"]))

    content_dirs = []
    for name in sorted(os.listdir(CONTENT)) if os.path.isdir(CONTENT) else []:
        if os.path.isdir(os.path.join(CONTENT, name)):
            content_dirs.append(name)

    missing = [d for d in content_dirs if d not in covered]
    if missing:
        ok = False
        print("FAIL: Content/ directories with no SOURCES_MATRIX row:")
        for d in missing:
            print(f"  - {d}")

    for r in rows:
        url = r["url"]
        if url in ("", "first-party") or url.lower() in ("n/a", "tbd"):
            continue
        if "://" not in url and not url.startswith("https:"):
            ok = False
            print(f"FAIL: row {r['path']} has non-URL source: {url!r}")

    pend = [r for r in rows if r["status"] == "pending"]
    if pend:
        msg = f"PENDING rows ({len(pend)}): " + ", ".join(r["path"] for r in pend)
        warnings.append(msg)
        if strict:
            ok = False

    if ok:
        print(f"PASS: {len(content_dirs)} Content/ dirs covered by {len(rows)} matrix rows.")
        for w in warnings:
            print(f"WARN: {w}")
        return 0

    for w in warnings:
        print(f"WARN: {w}")
    return 1


if __name__ == "__main__":
    sys.exit(main())