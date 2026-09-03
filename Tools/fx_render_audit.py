# -*- coding: utf-8 -*-
"""Headless CLI wrapper for the Melodia FX render-visibility audit.

  blender -b <stage.blend> -P Tools/fx_render_audit.py

Loads the shared engine from the live Blender 5.2 addons copy
(deploy/melodia_fx_audit_panel.py). Read-only: never saves the stage.
"""
from __future__ import annotations

import os
import sys

ADDONS = os.path.join(
    os.environ.get("APPDATA", ""),
    "Blender Foundation", "Blender", "5.2", "scripts", "addons",
)
if os.path.isdir(ADDONS) and ADDONS not in sys.path:
    sys.path.insert(0, ADDONS)

import melodia_fx_audit_panel as mfx  # noqa: E402

if __name__ == "__main__":
    mfx.run_audit(print_summary=True)
