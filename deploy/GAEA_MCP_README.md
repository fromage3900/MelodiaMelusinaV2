# gaea-mcp

Model Context Protocol server for rapid, headless Gaea 2 terrain creation.

**Back-end:** `Gaea.Swarm.exe` CLI (proven 2026-08-26 against the Aurora Glacier graph).
**Transport:** stdio via the official `mcp` Python SDK (FastMCP).
**Policy:** builds are gated via `Tools/mcp_policy.py` (owner approval, `mutate`).

## Registration
Already added to `C:\EnvironmentPortfolio\.mcp.json`:
```json
"gaea": {
  "command": "C:/Python314/python.exe",
  "args": ["C:/EnvironmentPortfolio/BS_GodFile/deploy/gaea_mcp_server.py"],
  "env": {
    "GAEA_SWARM_EXE": "C:/Program Files/QuadSpinner/Gaea 2/Gaea.Swarm.exe",
    "GAEA_PROJECT_ROOT": "C:/EnvironmentPortfolio/BS_GodFile"
  }
}
```
Policy entries in `BS_GodFile/specs/mcp_tool_policy.v1.json` (`gaea_*`).

## Tools
| Tool | Op | Approval |
|---|---|---|
| `list_ga_recipes` | read | none |
| `inspect_terrain(source)` | read | none |
| `verify_build(directory)` | read | none |
| `build_terrain(source, buildpath, ...)` | exec | **owner** |

`build_terrain` refuses to build over stock `Examples/` graphs and confines paths
to the Gaea root + project root. It returns exit code, stderr tail, produced PNGs,
and per-file SHA-256.

## Files
- `deploy/gaea_mcp_server.py` — the server (run `python deploy/gaea_mcp_server.py`)
- `specs/mcp_tool_policy.v1.json` — `gaea_*` allow entries
- `.mcp.json` — `gaea` server block