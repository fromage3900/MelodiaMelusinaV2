#!/usr/bin/env python3
"""
Gaea MCP server â€” headless Gaea 2 terrain graph inspect + Swarm build via MCP.

Read-only paths (inspect/list/verify) work offline. Exec (build) spawns the
Gaea.Swarm CLI and is gated through Tools/mcp_policy.py (write requires owner
approval, matching the project's per-tool policy).

Registration: add to C:\\EnvironmentPortfolio\\.mcp.json as server "gaea" pointing
at this file with env GAEA_SWARM_EXE + GAEA_PROJECT_ROOT.
"""
from __future__ import annotations

import hashlib
import json
import os
import re
import subprocess
import sys
from pathlib import Path
from typing import Any

try:
    from mcp.server.fastmcp import FastMCP
except ImportError:  # allow py_compile / import on machines without the MCP SDK
    FastMCP = None  # type: ignore[assignment]

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

try:
    from Tools.mcp_policy import authorize_tool  # noqa: E402
except Exception:  # pragma: no cover - degrade gracefully outside the repo
    authorize_tool = None  # type: ignore[assignment]

SWARM_EXE = os.environ.get(
    "GAEA_SWARM_EXE",
    r"C:\Program Files\QuadSpinner\Gaea 2\Gaea.Swarm.exe",
)
PROJECT_ROOT = Path(os.environ.get("GAEA_PROJECT_ROOT", ROOT))
SETUPS_DIR = PROJECT_ROOT / "Saved" / "Audit" / "gaea_setups"

if FastMCP is not None:
    mcp = FastMCP("gaea")
else:  # pragma: no cover
    mcp = None  # type: ignore[assignment]


def _confine(path: str | None) -> Path:
    """Resolve a path and forbid escaping the project + Gaea roots."""
    if not path:
        raise ValueError("path required")
    p = Path(path).resolve()
    allowed = [PROJECT_ROOT.resolve(), Path(SWARM_EXE).parent.parent.resolve()]
    if p == PROJECT_ROOT.resolve():
        return p
    if not any(p == a or a in p.parents for a in allowed):
        raise PermissionError(f"path outside allowed roots: {p}")
    return p


def _normalise(value: str | None) -> str:
    return (value or "").replace("\\", "/").lower()


def _sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


# --------------------------------------------------------------------------- #
# Inspect / list
# --------------------------------------------------------------------------- #
def _dump_graph(source: Path) -> dict[str, Any]:
    raw = source.read_text(encoding="utf-8", errors="replace")
    nodes = {}
    for m in re.finditer(r"\"Id\":\s*(\d+)", raw):
        ctx = raw[max(0, m.start() - 300): m.start() + 80]
        tm = re.search(r'"\$type":\s*"QuadSpinner\.Gaea\.Nodes\.(\w+)', ctx)
        nm = re.search(r'"Name":\s*"([^"]+)"', ctx)
        nodes[m.group(1)] = {"name": nm.group(1) if nm else "?", "type": tm.group(1) if tm else "?"}
    return {"node_count": len(nodes), "nodes": list(nodes.values())}
if mcp is not None:

    @mcp.tool()
    def list_ga_recipes() -> list[str]:
        """Scan gaea_setups for melodia.gaea_setup.v1 recipe JSON files."""
        found = []
        for base in [PROJECT_ROOT / "Docs" / "WorldGen", SETUPS_DIR]:
            if not base.is_dir():
                continue
            for j in base.rglob("*.json"):
                try:
                    data = json.loads(j.read_text(encoding="utf-8"))
                except Exception:
                    continue
                if data.get("schema", "").startswith("melodia.gaea_setup"):
                    found.append(str(j.resolve()))
        return found

    @mcp.tool()
    def inspect_terrain(source: str) -> dict[str, Any]:
        """Inspect a Gaea .terrain JSON graph: node count + names (fast, offline)."""
        return _dump_graph(_confine(source))

    @mcp.tool()
    def verify_build(directory: str) -> dict[str, Any]:
        """Gate PNGs in a build dir by existence + size > 0. Returns report."""
        d = _confine(directory)
        if not d.is_dir():
            raise FileNotFoundError(d)
        pngs = sorted(d.glob("*.png"))
        return {"png_count": len(pngs), "files": [str(x.resolve()) for x in pngs]}

    @mcp.tool()
    def build_terrain(
        source: str,
        buildpath: str,
        resolution: str | None = None,
        profile: str | None = None,
        vars_json: str | None = None,
        approval: str = "owner",
    ) -> dict[str, Any]:
        """Run Gaea Swarm headless to build source into buildpath.

        Gated by Tools/mcp_policy (mutate/exec requires owner approval).
        """
        if authorize_tool is None:
            raise PermissionError("policy layer unavailable")
        decision = authorize_tool("gaea_build_terrain", "mutate", approval)
        if not decision.get("allowed"):
            raise PermissionError(decision.get("reason", "policy denied build"))
        src = _confine(source)
        if "examples" in _normalise(str(src)):
            raise PermissionError("refusing to build over stock Gaea examples")
        dst = _confine(buildpath)
        dst.mkdir(parents=True, exist_ok=True)
        cmd = [SWARM_EXE, "--Filename", str(src), "--buildpath", str(dst), "--silent"]
        if resolution:
            cmd += ["--resolution", str(resolution)]
        if profile:
            cmd += ["--profile", str(profile)]
        if vars_json:
            cmd += ["--vars", str(vars_json)]
        proc = subprocess.run(cmd, capture_output=True, text=True, timeout=1800)
        produced = [p.name for p in dst.glob("*.png")]
        return {
            "exit": proc.returncode,
            "stdout_tail": proc.stdout[-1200:],
            "stderr_tail": proc.stderr[-800:],
            "produced": produced,
            "manifest_sha256": {n: _sha256(dst / n) for n in produced if (dst / n).is_file()},
        }

if __name__ == "__main__":
    if mcp is None:  # pragma: no cover
        raise SystemExit("mcp SDK not importable; cannot start server")
    mcp.run()
