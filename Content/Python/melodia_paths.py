"""Portable filesystem paths shared by Unreal-side Python tools.

The project is often opened from a different drive than the author's original
machine. Resolve the active checkout from the script location first, then
allow an explicit `MELODIA_PROJECT_ROOT` override for packaged/remote runners.
"""
from __future__ import annotations

import os
from pathlib import Path


def _root_from_environment() -> Path:
    configured = os.environ.get("MELODIA_PROJECT_ROOT")
    if configured:
        return Path(configured).expanduser().resolve()
    return Path(__file__).resolve().parents[2]


PROJECT_ROOT = _root_from_environment()
WORKSPACE_ROOT = Path(
    os.environ.get("MELODIA_WORKSPACE_ROOT", str(PROJECT_ROOT.parent))
).expanduser().resolve()
WEBSITE_ROOT = Path(
    os.environ.get("MELODIA_WEBSITE_ROOT", str(WORKSPACE_ROOT / "my-site-clean"))
).expanduser().resolve()
DEPLOY_WORKTREE = Path(
    os.environ.get("MELODIA_DEPLOY_WORKTREE", str(WORKSPACE_ROOT / "_github_deploy"))
).expanduser().resolve()


def project_path(*parts: str) -> Path:
    return PROJECT_ROOT.joinpath(*parts)


def workspace_path(*parts: str) -> Path:
    return WORKSPACE_ROOT.joinpath(*parts)
