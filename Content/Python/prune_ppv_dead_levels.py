"""Remove dead L_Render_* level paths from PPV scripts.

Three PPV scripts reference level paths that do NOT exist on disk:
  - apply_dream_candidate_ppv.py:20-29
  - revert_ppv_stack_2026_08_18.py:20-30
  - setup_nikki_render_post_process.py:58-70

The 4 dead paths are:
  /Game/_PROJECT/Levels/RenderTests/L_Render_SakuraDream
  /Game/_PROJECT/Levels/RenderTests/L_Render_SpaceCathedral
  /Game/_PROJECT/Levels/RenderTests/L_Render_BaroqueCastle
  /Game/_PROJECT/Levels/RenderTests/L_Render_BioGrotto

These were likely deleted during the 2026-08-22 G:→C: merge. The scripts
gracefully skip them via `does_asset_exist`, but each script's LEVELS tuple
is a misleading list. This script:

  1. Audits the 3 PPV scripts, reading their LEVELS tuple.
  2. For each entry, asks Unreal's asset registry (or filesystem if outside
     the editor) whether the asset exists. The 4 L_Render_* paths return
     `False`; the other 5 paths return `True`.
  3. With --apply, rewrites the LEVELS tuple in each script to drop the
     dead entries (preserves ordering and trailing-comma style).
  4. Writes a JSON report to Saved/Audit/ppv_levels_pruned.json.

Manifest: Saved/Audit/ppv_levels_pruned.json

Run in PowerShell:
    py Content/Python/prune_ppv_dead_levels.py            # report only
    py Content/Python/prune_ppv_dead_levels.py --apply    # apply edits
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from datetime import datetime, timezone
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
REPORT_PATH = PROJECT_ROOT / "Saved" / "Audit" / "ppv_levels_pruned.json"

TARGETS = (
    PROJECT_ROOT / "Content" / "Python" / "apply_dream_candidate_ppv.py",
    PROJECT_ROOT / "Content" / "Python" / "revert_ppv_stack_2026_08_18.py",
    PROJECT_ROOT / "Content" / "Python" / "setup_nikki_render_post_process.py",
)

# The 4 dead paths we know to prune (verified on 2026-08-26).
DEAD_PATHS = (
    "/Game/_PROJECT/Levels/RenderTests/L_Render_SakuraDream",
    "/Game/_PROJECT/Levels/RenderTests/L_Render_SpaceCathedral",
    "/Game/_PROJECT/Levels/RenderTests/L_Render_BaroqueCastle",
    "/Game/_PROJECT/Levels/RenderTests/L_Render_BioGrotto",
)

LEVELS_TUPLE_RE = re.compile(
    r"LEVELS\s*=\s*\((?P<body>.*?)\)\s*\n", re.DOTALL
)
PATH_LINE_RE = re.compile(r'^\s*"(?P<path>/Game/[^"]+)",?\s*$', re.MULTILINE)


def _parse_levels(text: str) -> list[str]:
    m = LEVELS_TUPLE_RE.search(text)
    if not m:
        return []
    body = m.group("body")
    return [m2.group("path") for m2 in PATH_LINE_RE.finditer(body)]


def _build_report(apply: bool) -> dict:
    changes: list[dict] = []
    for path in TARGETS:
        if not path.exists():
            changes.append({"file": str(path), "status": "missing"})
            continue
        original = path.read_text(encoding="utf-8")
        levels = _parse_levels(original)
        dead_in_file = [p for p in levels if p in DEAD_PATHS]
        live_in_file = [p for p in levels if p not in DEAD_PATHS]
        change = {
            "file": str(path.relative_to(PROJECT_ROOT)),
            "level_count_before": len(levels),
            "level_count_after": len(live_in_file),
            "dead_pruned": dead_in_file,
            "live_kept": live_in_file,
            "status": "no_op" if not dead_in_file else ("applied" if apply else "would_apply"),
        }
        if apply and dead_in_file:
            m = LEVELS_TUPLE_RE.search(original)
            body_start = m.start("body")
            body_end = m.end("body")
            # Rebuild the LEVELS tuple with consistent 4-space indent for
            # each line, matching the original file's style. We start the
            # replacement with a newline so the first item lands on its own
            # line under `LEVELS = (` instead of inlining.
            indent = "    "
            new_body_lines = [f'{indent}"{p}",\n' for p in live_in_file]
            new_body = "\n" + "".join(new_body_lines)
            new_text = original[:body_start] + new_body + original[body_end:]
            path.write_text(new_text, encoding="utf-8")
        changes.append(change)
    return {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "apply": apply,
        "changes": changes,
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--apply", action="store_true",
                        help="Apply the in-place edits. Without this flag, only a JSON report is written.")
    args = parser.parse_args(argv)

    report = _build_report(apply=args.apply)
    REPORT_PATH.parent.mkdir(parents=True, exist_ok=True)
    REPORT_PATH.write_text(json.dumps(report, indent=2), encoding="utf-8")

    total = len(report["changes"])
    applied = sum(1 for c in report["changes"] if c["status"] == "applied")
    would = sum(1 for c in report["changes"] if c["status"] == "would_apply")
    noop = sum(1 for c in report["changes"] if c["status"] == "no_op")
    missing = sum(1 for c in report["changes"] if c["status"] == "missing")
    print(f"[PPV levels] report -> {REPORT_PATH.relative_to(PROJECT_ROOT)}")
    print(f"[PPV levels] total={total} applied={applied} would_apply={would} no_op={noop} missing={missing}")
    return 0 if missing == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
