"""Tonight's Portfolio Capture Orchestration Script

Instance-only material policy: never modifies core masters (M_*/MF_*).

Run in-editor:
  py Content/Python/tonight_capture_pipeline.py
"""
from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

REPORT_PATH = Path(__file__).resolve().parents[2] / "Saved" / "Audit" / "tonight_capture_pipeline.json"


def run_pipeline() -> dict:
    """Execute instance-only steps for tonight's portfolio captures."""
    report = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "policy": "instances_only",
        "steps": {},
    }

    try:
        import sync_portfolio_instances_only as sync_inst

        report["steps"]["instance_sync"] = sync_inst.run_sync()
    except Exception as exc:
        report["steps"]["instance_sync"] = {"error": str(exc)}

    try:
        import portfolio_texture_catalog as catalog

        report["steps"]["instance_textures"] = {
            "refreshed": len(catalog.refresh_all_instance_textures()),
        }
    except Exception as exc:
        report["steps"]["instance_textures"] = {"error": str(exc)}

    try:
        import build_ppv_nikkidream as ppbuild

        ppbuild.build()
        report["steps"]["ppv_nikkidream"] = {"status": "configured"}
    except Exception as exc:
        report["steps"]["ppv_nikkidream"] = {"error": str(exc)}

    try:
        import setup_template_showcase as showcase

        show_result = showcase.build_all()
        report["steps"]["template_showcase"] = {"status": "ok", "result": str(show_result)}
    except Exception as exc:
        report["steps"]["template_showcase"] = {"error": str(exc)}

    REPORT_PATH.parent.mkdir(parents=True, exist_ok=True)
    REPORT_PATH.write_text(json.dumps(report, indent=2), encoding="utf-8")

    return report


def print_capture_instructions() -> None:
    """Print instructions for remaining manual steps."""
    print("""
=== PORTFOLIO CAPTURE INSTRUCTIONS ===

1. OPEN THE EDITOR:
   - Launch Unreal Engine 5.8 with BS_GodFile.uproject

2. RUN THE PIPELINE (in editor Python console):
   import tonight_capture_pipeline
   tonight_capture_pipeline.run_pipeline()

3. MANUAL STEPS (in editor):
   a) Open each L_WP_* pillar level
   b) Regenerate PCG volumes — target ISM > 0
   c) Pilot Cam_Hero_Establishing — frame hero pocket (not sky-only)
   d) MeshTerrain block-in per evening checklist

4. INSTANCE TEXTURE FIX (if needed):
   py Content/Python/portfolio_texture_catalog.py --refresh-instances

5. CAPTURE RENDERS:
   py Content/Python/render_exporter.py --all-heroes

6. WEBSITE INGEST (after captures):
   powershell -ExecutionPolicy Bypass -File my-site-clean/tools/ingest_unreal_portfolio.ps1
""")


if __name__ == "__main__":
    try:
        import unreal  # noqa: F401

        print("Running capture pipeline in-editor...")
        result = run_pipeline()
        print(json.dumps(result, indent=2))
        print_capture_instructions()
    except ImportError:
        print("Not in Unreal Editor - printing instructions only:")
        print_capture_instructions()
