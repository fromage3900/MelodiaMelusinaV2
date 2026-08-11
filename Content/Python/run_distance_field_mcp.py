"""Run one distance-field editor script through the live Unreal MCP editor."""
from __future__ import annotations

import sys

from gmm.core.mcp_client import MonolithClient


def run(path: str) -> dict:
    return MonolithClient(timeout=240).run_python(path, mode="execute_file")


if __name__ == "__main__":
    target = sys.argv[1] if len(sys.argv) > 1 else "G:/EnvironmentPortfolio/BS_GodFile/Content/Python/build_distance_field_blend_lab.py"
    print(run(target))
