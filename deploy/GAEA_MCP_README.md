# gaea-mcp

Model Context Protocol server for rapid, headless Gaea 2 terrain creation.

**Back-end:** `Gaea.Swarm.exe` CLI.
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
| `stage_example_for_export(source, variant_name, ...)` | write | **owner** |
| `build_terrain(source, buildpath, ...)` | exec | **owner** |

`stage_example_for_export` copies a stock Gaea example into the project, auto-selects
a sink node (or uses an explicit `target_node_id`), and injects a PNG16 Export node
with matching `SaveDefinitions`. The resulting `.terrain` can be opened in Gaea for
visual confirmation or passed to `build_terrain`.

`build_terrain` refuses to build over stock `Examples/` graphs and confines paths
to the Gaea root + project root. It returns exit code, stderr tail, produced PNGs,
and per-file SHA-256.

## Files
- `deploy/gaea_mcp_server.py` — the server (run `python deploy/gaea_mcp_server.py`)
- `specs/mcp_tool_policy.v1.json` — `gaea_*` allow entries
- `.mcp.json` — `gaea` server block

## Known limitations
- **Swarm CLI instability:** Gaea Build Swarm 2.3.0.1 on this workstation intermittently
crashes with `System.ArgumentNullException: Value cannot be null. (Parameter 'task')`
when running headless builds, even against graphs that previously exported successfully.
Staging and inspection tools are stable; if Swarm fails, open the staged `.terrain` in the
Gaea GUI and run the export from there.
