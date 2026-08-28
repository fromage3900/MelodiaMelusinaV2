"""Fix dead asset references in legacy PPV scripts.

Two PPV scripts in the tree reference materials that do not exist on disk:
  - `build_ppv_nikkidream.py` lines 18-22:
      /Game/EnvSandbox/Materials/PostProcess/M_PP_ToonOutline        (MISSING)
      /Game/EnvSandbox/Materials/PostProcess/M_PP_StorybookVines_Inst (MISSING)
      /Game/_PROJECT/04_Materials/PostProcess/M_PP_MeluColorGrade    (EXISTS)
  - `portfolio_scene_integration.py` lines 10-12:
      /Game/EnvSandbox/Materials/PostProcess/M_PP_ToonOutline        (MISSING)
      /Game/EnvSandbox/Materials/PostProcess/M_PP_StorybookVines     (EXISTS)
      /Game/EnvSandbox/Materials/PostProcess/M_PP_StorybookVines_Inst (MISSING)

Replacement policy (per the 2026-08-18 owner-approved stack at
`apply_dream_candidate_ppv.py:35-37`):

  M_PP_ToonOutline          -> Candidates/Profiles/MI_StorybookOutline_GameplayStandard
  M_PP_StorybookVines_Inst  -> Candidates/Profiles/MI_StorybookOutline_GameplayStandard
  (M_PP_StorybookVines is left as the "outline fallback" path; it does exist)

This script does TWO things, both additive and non-destructive:

  1. Write a small JSON drift report at Saved/Audit/ppv_drift_fixes.json
     describing every (file, line, old, new) replacement.

  2. Apply the replacement in-place on the two target scripts, behind a
     `--apply` flag. Without --apply, only the report is written.

Manifest: Saved/Audit/ppv_drift_fixes.json

Run in PowerShell:
    py Content/Python/fix_ppv_drift_refs.py                # report only
    py Content/Python/fix_ppv_drift_refs.py --apply        # apply in-place
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from datetime import datetime, timezone
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
REPORT_PATH = PROJECT_ROOT / "Saved" / "Audit" / "ppv_drift_fixes.json"

TARGETS = (
    PROJECT_ROOT / "Content" / "Python" / "build_ppv_nikkidream.py",
    PROJECT_ROOT / "Content" / "Python" / "portfolio_scene_integration.py",
)

# Each entry: (file, search_regex, replacement, note)
# search_regex must match the literal string in the source file.
REPLACEMENTS = (
    (
        TARGETS[0],
        re.escape(
            "\"/Game/EnvSandbox/Materials/PostProcess/M_PP_ToonOutline\","
        ),
        "\"/Game/EnvSandbox/Materials/PostProcess/Candidates/Profiles/MI_StorybookOutline_GameplayStandard\",  # 2026-08-26 drift fix: M_PP_ToonOutline removed; uses Aug-18 outline candidate",
        "M_PP_ToonOutline -> MI_StorybookOutline_GameplayStandard (build_ppv_nikkidream.py)",
    ),
    (
        TARGETS[0],
        re.escape(
            "\"/Game/EnvSandbox/Materials/PostProcess/M_PP_StorybookVines_Inst\","
        ),
        "\"/Game/EnvSandbox/Materials/PostProcess/Candidates/Profiles/MI_StorybookOutline_GameplayStandard\",  # 2026-08-26 drift fix: M_PP_StorybookVines_Inst removed; outline candidate is now shared",
        "M_PP_StorybookVines_Inst -> MI_StorybookOutline_GameplayStandard (build_ppv_nikkidream.py)",
    ),
    (
        TARGETS[1],
        re.escape(
            "PP_OUTLINE = \"/Game/EnvSandbox/Materials/PostProcess/M_PP_ToonOutline.M_PP_ToonOutline\""
        ),
        "PP_OUTLINE = \"/Game/EnvSandbox/Materials/PostProcess/Candidates/Profiles/MI_StorybookOutline_GameplayStandard.MI_StorybookOutline_GameplayStandard\"  # 2026-08-26 drift fix",
        "M_PP_ToonOutline -> MI_StorybookOutline_GameplayStandard (portfolio_scene_integration.py)",
    ),
    (
        TARGETS[1],
        re.escape(
            "PP_VINES_INST = \"/Game/EnvSandbox/Materials/PostProcess/M_PP_StorybookVines_Inst.M_PP_StorybookVines_Inst\""
        ),
        "PP_VINES_INST = \"/Game/EnvSandbox/Materials/PostProcess/Candidates/Profiles/MI_StorybookOutline_GameplayStandard.MI_StorybookOutline_GameplayStandard\"  # 2026-08-26 drift fix: shared with PP_OUTLINE",
        "M_PP_StorybookVines_Inst -> MI_StorybookOutline_GameplayStandard (portfolio_scene_integration.py)",
    ),
)


def _build_report(apply: bool) -> dict:
    changes: list[dict] = []
    for (path, search, replacement, note) in REPLACEMENTS:
        if not path.exists():
            changes.append({
                "file": str(path),
                "status": "missing",
                "note": note,
            })
            continue
        original = path.read_text(encoding="utf-8")
        match_count = len(re.findall(search, original))
        changes.append({
            "file": str(path.relative_to(PROJECT_ROOT)),
            "match_count": match_count,
            "replacement": replacement,
            "note": note,
        })
        if apply and match_count > 0:
            new_text = re.sub(search, replacement, original)
            path.write_text(new_text, encoding="utf-8")
            changes[-1]["status"] = "applied"
        else:
            changes[-1]["status"] = "would_apply" if match_count > 0 else "no_match"
    return {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "apply": apply,
        "changes": changes,
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--apply", action="store_true",
                        help="Apply the in-place edits. Without this flag, only a JSON drift report is written.")
    args = parser.parse_args(argv)

    report = _build_report(apply=args.apply)
    REPORT_PATH.parent.mkdir(parents=True, exist_ok=True)
    REPORT_PATH.write_text(json.dumps(report, indent=2), encoding="utf-8")

    # Console summary
    total = len(report["changes"])
    applied = sum(1 for c in report["changes"] if c["status"] == "applied")
    would = sum(1 for c in report["changes"] if c["status"] == "would_apply")
    nomatch = sum(1 for c in report["changes"] if c["status"] == "no_match")
    missing = sum(1 for c in report["changes"] if c["status"] == "missing")
    print(f"[PPV drift] report -> {REPORT_PATH.relative_to(PROJECT_ROOT)}")
    print(f"[PPV drift] total={total} applied={applied} would_apply={would} no_match={nomatch} missing={missing}")
    return 0 if missing == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
