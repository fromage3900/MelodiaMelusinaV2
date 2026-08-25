# -*- coding: utf-8 -*-
"""capture_to_portfolio.py - Blender-side viewport grab into the portfolio site.

Drop this in Blender's Text Editor and hit Run, or execute from the Blender
Python console:

    exec(open(r"C:/EnvironmentPortfolio/BS_GodFile/Tools/capture_to_portfolio_blender.py").read())
    capture_active_viewport("Melusina idle pose still")

What it does (honest, minimal):
  1. Renders the active viewport to a PNG via OpenGL (fast, matches what you see).
  2. Stages a dated copy into my-site-clean/generated/assets/editor_capture/.
  3. Appends a manifest row.

It does NOT push or commit - review the shot, then run the site deploy to ship.
"""
from __future__ import annotations

import datetime
import json
import shutil
from pathlib import Path

import bpy

# Resolve the workspace root robustly, with a fallback to the known G: path.
try:
    _HERE = Path(__file__).resolve().parent
    REPO_ROOT = _HERE.parent
except NameError:
    REPO_ROOT = Path(r"G:\EnvironmentPortfolio\BS_GodFile")
SITE_ROOT = REPO_ROOT.parent / "my-site-clean"
DEST_DIR = SITE_ROOT / "generated" / "assets" / "editor_capture"
MANIFEST = DEST_DIR / "manifest.json"


def _timestamp() -> str:
    return datetime.datetime.now().strftime("%Y-%m-%d_%H%M%S")


def capture_active_viewport(caption: str = "Blender capture") -> str | None:
    DEST_DIR.mkdir(parents=True, exist_ok=True)
    stamped = DEST_DIR / f"capture_{_timestamp()}.png"

    # OpenGL viewport render - what you see is what you get, fast.
    bpy.ops.render.opengl(animation=False, view_context=True, write_still=True)
    rendered = Path(bpy.app.tempdir) / "0001.png"  # default still output
    if not rendered.exists():
        rendered = Path.cwd() / "0001.png"
    if not rendered.exists():
        print("[capture_to_portfolio] OpenGL render not produced")
        return None

    shutil.copy2(rendered, stamped)
    _append_manifest(caption, stamped.name)
    print(f"[capture_to_portfolio] staged -> {stamped}")
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
        "source": "Blender active viewport",
    })
    rows = rows[:20]
    MANIFEST.parent.mkdir(parents=True, exist_ok=True)
    MANIFEST.write_text(json.dumps(rows, indent=2, ensure_ascii=False), encoding="utf-8")
