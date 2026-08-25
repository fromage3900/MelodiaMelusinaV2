"""capture_to_portfolio.py - One-click viewport grab from the UE editor into the
portfolio site's asset folder.

Run this from the Unreal Editor Python console
(unreal.PythonScriptLibrary or the Output Log > Python):

    import importlib.util, sys
    spec = importlib.util.spec_from_file_location(
        "capture_to_portfolio",
        r"C:/EnvironmentPortfolio/BS_GodFile/Tools/capture_to_portfolio.py")
    m = importlib.util.module_from_spec(spec); spec.loader.exec_module(m)
    m.capture_active_viewport("Space Cathedral hero still")

What it does (honest, minimal, no AI claims):
  1. Grabs the active level-editor viewport to a PNG in Saved/Screenshots.
  2. Stages a dated copy into my-site-clean/generated/assets/editor_capture/
     (the folder the portfolio site deploys).
  3. Appends a manifest row so the site can list "latest from the editor".

It does NOT push or commit - that stays a deliberate human step (you review the
shot before it ships). Run .\deploy\sync_site_to_github.ps1 afterwards to publish.
"""
from __future__ import annotations

import datetime
import json
import shutil
from pathlib import Path

# Resolve the workspace root relative to this file: BS_GodFile/Tools -> root.
TOOLS_DIR = Path(__file__).resolve().parent
REPO_ROOT = TOOLS_DIR.parent                       # BS_GodFile/
SITE_ROOT = REPO_ROOT.parent / "my-site-clean"     # the live site repo
DEST_DIR = SITE_ROOT / "generated" / "assets" / "editor_capture"
MANIFEST = DEST_DIR / "manifest.json"


def _timestamp() -> str:
    return datetime.datetime.now().strftime("%Y-%m-%d_%H%M%S")


def capture_active_viewport(caption: str = "Editor capture") -> str | None:
    import unreal

    out = Path(unreal.Paths.project_saved_dir()) / "Screenshots" / "EditorViewport.png"
    out.parent.mkdir(parents=True, exist_ok=True)

    # High-res viewport screenshot of the active viewport.
    success = unreal.AutomationLibrary.take_high_resolution_screenshot(
        1920, 1080, str(out),
        name="", capture_resolution_multiplier=1.0,
        additional_primitive_actors_to_include=None,
    )
    if not success or not out.exists():
        # Fallback: older API surface.
        try:
            unreal.EditorLevelLibrary().take_screenshot_of_active_editor_viewport(str(out))
        except Exception:
            pass
    if not out.exists():
        unreal.log_warning("[capture_to_portfolio] screenshot not produced")
        return None

    DEST_DIR.mkdir(parents=True, exist_ok=True)
    stamped = DEST_DIR / f"capture_{_timestamp()}.png"
    shutil.copy2(out, stamped)

    _append_manifest(caption, stamped.name)
    unreal.log(f"[capture_to_portfolio] staged -> {stamped}")
    return str(stamped)


def _append_manifest(caption: str, filename: str) -> None:
    rows = []
    if MANIFEST.exists():
        try:
            rows = json.loads(MANIFEST.read_text(encoding="utf-8"))
        except Exception:
            rows = []
    rows.insert(0, {
        "caption": caption,
        "file": filename,
        "taken_utc": datetime.datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ"),
        "source": "Unreal Editor active viewport",
    })
    rows = rows[:20]  # keep the latest 20
    MANIFEST.parent.mkdir(parents=True, exist_ok=True)
    MANIFEST.write_text(json.dumps(rows, indent=2, ensure_ascii=False), encoding="utf-8")


if __name__ == "__main__":
    print("Run this from inside the Unreal Editor Python console, not as a standalone script.")
