# -*- coding: utf-8 -*-
"""Shared website root resolver for Melodia Blender/Tools scripts.

Canonical live site: {MELODIA_WORKSPACE_ROOT}/my-site-clean
Override with MELODIA_WEBSITE_ROOT.
"""
from __future__ import annotations

import os
from pathlib import Path


def project_root_from_tools() -> Path:
    """BS_GodFile root when this file lives under Tools/."""
    return Path(__file__).resolve().parents[1]


def resolve_website_root(project_root: Path | None = None) -> Path:
    """Return the live my-site-clean path (never prefer the BS_GodFile stub)."""
    env = os.environ.get("MELODIA_WEBSITE_ROOT")
    if env:
        return Path(env).expanduser().resolve()

    project = (project_root or project_root_from_tools()).resolve()
    workspace = Path(
        os.environ.get("MELODIA_WORKSPACE_ROOT", str(project.parent))
    ).expanduser().resolve()

    live = workspace / "my-site-clean"
    if live.is_dir():
        return live

    # Last resort: stub under project (legacy writers)
    return (project / "my-site-clean").resolve()
