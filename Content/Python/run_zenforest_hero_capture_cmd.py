"""Headless entrypoint: place ZenForest hero cameras and capture all hero plates.

This script is intended to be run via UnrealEditor-Cmd.exe:
  UnrealEditor-Cmd.exe <uproject> -ExecutePythonScript=<this_file>

It mirrors the in-editor workflow:
  py Content/Python/setup_zenforest_hero_cameras.py
  py Content/Python/render_exporter.py --all-heroes
"""

from __future__ import annotations

import sys
import time


def main() -> int:
    # Unreal cmdlet startup can be slow; give the editor world time to initialize.
    time.sleep(12)

    import setup_zenforest_hero_cameras as cams
    import render_exporter as rex

    # Place cameras and save level.
    sys.argv = ["setup_zenforest_hero_cameras"]
    cams.main()

    # Capture all tagged hero cameras.
    sys.argv = ["render_exporter", "--all-heroes", "json"]
    return rex.main()


if __name__ == "__main__":
    raise SystemExit(main())

