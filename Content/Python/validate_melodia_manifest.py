"""Validate a Melodia Studio/GMM manifest outside Unreal or Blender.

Usage:
    PYTHONPATH=Content/Python python Content/Python/validate_melodia_manifest.py path.json
"""
from __future__ import annotations

from gmm.family.cli import main


if __name__ == "__main__":
    raise SystemExit(main())
