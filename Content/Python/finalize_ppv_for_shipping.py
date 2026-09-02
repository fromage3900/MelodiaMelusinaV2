"""Finalize the PPV_NikkiDream stack for gameplay shipping.

This is the entry point: it runs the 3 sibling finalizers in sequence and
writes a single consolidated manifest at Saved/Audit/ppv_shipping_finalize.json.

Finalization sequence (each step is independent and idempotent):

  1. fix_ppv_drift_refs.py        -- redirect M_PP_ToonOutline /
                                       M_PP_StorybookVines_Inst dead refs
                                       to the Aug-18 candidate outline MI.
  2. prune_ppv_dead_levels.py     -- drop 4 L_Render_* dead level paths
                                       from the 3 PPV scripts' LEVELS tuples.
  3. strip_ppv_color_overrides.py -- remove 7 color-grading scene overrides
                                       from every live PPV_NikkiDream actor.
                                       Bloom_intensity override is preserved
                                       (lens character, not grading).

After this script, the shipped PPV state is:
  - The 3 PPV scripts reference assets that exist on disk.
  - The 3 PPV scripts target only the 5 live levels.
  - The 5 live PPV_NikkiDream actors carry the Aug-18 3-blendable stack
    (Outline + Grade + Ink) with weights (1.0, 0.69, 1.0) and no residual
    color-grading scene overrides.

This script does NOT:
  - Edit any master material.
  - Edit any C++ source.
  - Add a new top-level pipeline.
  - Re-clobber per-level blendable weights.
  - Modify the audio-reactive path (UMelodiaAudioReactivePresentationSubsystem
    owns MPC_Melodia_Palette; PPV only consumes via blendable materials).

Manifest: Saved/Audit/ppv_shipping_finalize.json

Run in PowerShell:
    py Content/Python/finalize_ppv_for_shipping.py            # report only
    py Content/Python/finalize_ppv_for_shipping.py --apply    # apply all 3

Note: the strip step requires an open editor (uses the EditorActorSubsystem
+ save_current_level). The other 2 steps are pure-file. The script
auto-detects an open editor and skips the strip step if absent.
"""
from __future__ import annotations

import argparse
import importlib.util
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
REPORT_PATH = PROJECT_ROOT / "Saved" / "Audit" / "ppv_shipping_finalize.json"

SIBLINGS = (
    ("drift_refs", "fix_ppv_drift_refs.py"),
    ("dead_levels", "prune_ppv_dead_levels.py"),
    ("color_overrides", "strip_ppv_color_overrides.py"),
)


def _import_sibling(name: str, filename: str):
    """Import a sibling script as a module by file path."""
    path = Path(__file__).resolve().parent / filename
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def _has_editor() -> bool:
    try:
        import unreal  # noqa: F401
        return True
    except ImportError:
        return False


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--apply", action="store_true",
                        help="Apply the edits. Without this flag, only a JSON report is written.")
    args = parser.parse_args(argv)

    in_editor = _has_editor()
    report = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "apply": args.apply,
        "in_editor": in_editor,
        "steps": [],
    }

    for name, filename in SIBLINGS:
        mod = _import_sibling(name, filename)
        step: dict = {"name": name, "script": filename}
        if name == "color_overrides" and not in_editor:
            # The strip step needs the editor. Report status; skip.
            step["status"] = "skipped_no_editor"
            report["steps"].append(step)
            continue
        try:
            if name == "drift_refs":
                # Detect already-applied state: a no_match means the drift
                # strings are no longer in the target files, i.e. the patch
                # already landed.
                pre = mod._build_report(apply=False)
                no_match = all(c["status"] == "no_match" for c in pre["changes"])
                applied_before = no_match and bool(pre["changes"])
                if args.apply:
                    rc = mod.main(["--apply"])
                    step["returncode"] = rc
                    step["status"] = "applied" if rc == 0 else "failed"
                else:
                    step["returncode"] = 0
                    step["status"] = "already_applied" if applied_before else "report_only"
            elif name == "dead_levels":
                pre = mod._build_report(apply=False)
                no_op = all(c["status"] == "no_op" for c in pre["changes"])
                applied_before = no_op and bool(pre["changes"])
                if args.apply:
                    rc = mod.main(["--apply"])
                    step["returncode"] = rc
                    step["status"] = "applied" if rc == 0 else "failed"
                else:
                    step["returncode"] = 0
                    step["status"] = "already_applied" if applied_before else "report_only"
            elif name == "color_overrides":
                if args.apply:
                    rpt = mod.apply_all()
                    step["status"] = "applied"
                    step["levels_processed"] = len(rpt.get("levels", []))
                else:
                    step["status"] = "report_only"
            else:
                step["status"] = "unknown"
        except SystemExit as se:
            step["returncode"] = se.code
            step["status"] = "applied" if se.code == 0 else "failed"
        except Exception as exc:
            step["status"] = "exception"
            step["error"] = f"{type(exc).__name__}: {exc}"
        report["steps"].append(step)

    REPORT_PATH.parent.mkdir(parents=True, exist_ok=True)
    REPORT_PATH.write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(f"[PPV finalize] report -> {REPORT_PATH.relative_to(PROJECT_ROOT)}")
    for step in report["steps"]:
        print(f"  {step['name']:>16}: {step['status']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
