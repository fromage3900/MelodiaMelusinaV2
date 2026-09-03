# Cascadeur MCP Bridge — Handoff 2026-08-08

## What shipped

A working Cascadeur ↔ agent bridge for the installed **Cascadeur 2025.1.0.13204**
(`C:\Program Files\Cascadeur\cascadeur.exe`), sourced from
[`ysk424/cascadeur-mcp`](https://github.com/ysk424/cascadeur-mcp) (MIT) and adapted.

| Piece | Location | Role |
|-------|----------|------|
| Cascadeur-side command | `C:\Program Files\Cascadeur\resources\scripts\python\commands\externals\csc_mcp_exec.py` (installed elevated, SHA256 `3B5EA00ADF288D9F63DFEBFB25C91F63A673F6CB3A88222E71218CC48E4E3E7C`) | Registered `commands.externals.csc_mcp_exec`; runs on Cascadeur main thread per call |
| Project copy | `deploy\cascadeur\csc_mcp_exec.py` | Source of truth mirror of the installed file |
| MCP server | `deploy\cascadeur_mcp_server.py` | Stdio MCP server; exposes `execute_cascadeur_code`, `get_scene_info`, `import_fbx`, `export_fbx` |
| Installer | `deploy\cascadeur\install_csc_mcp.ps1` | Elevated copy into Program Files (run manually, needs UAC) |
| Inbox entry | `.mcp.json` → `"cascadeur"` | Spawns `C:/Python314/python.exe deploy\cascadeur_mcp_server.py` |

## Wire protocol

Per call: server binds `127.0.0.1:53151`, writes `%TEMP%\cascadeur_mcp.json`
(`{"port": 53151}`), launches `cascadeur.exe --run-script` command, the running
app's main thread dials back, 64-byte ASCII length header + UTF-8 JSON
`{"code": "..."}` → `{"status", "result", "stdout"}`.

## Verified (2026-08-08, live test, no app restart needed)

- Command registered instantly in the already-running instance; no Cascade restart required.
- Read-only round trip working: `scene.model_viewer().get_objects()` returned `[]` for the current empty scene.
- API facts learned: `csc.domain.Scene` has **no `name()`**; current-scene info goes
  through `scene.model_viewer()`, frame via `get_current_frame`/`set_current_frame`,
  mutations via `modify_with_session(...)`.

## Usage from an agent

- Server: `execute_cascadeur_code(code)` — `csc`, `scene`, `app` in scope; assign `result`.
- Import Melusina target: `import_fbx("C:/EnvironmentPortfolio/BS_GodFile/Imports/Animations/Cascadeur/Target/SK_Melusina_Cascadeur_Target.fbx", method="import_model")`.
- Scores: muted Cascadeur app must allow programmatic FBX import/export (test directly against the app when a scene is open).

## Notes

- Port 53151 must be free; single server at a time (SO_REUSEADDR).
- The command file is owned by Program Files — fix via `install_csc_mcp.ps1` (elevated).
- Upstream repo declares MIT but ships no license file; files preserved verbatim
  modulo comments; attribution in headers.
- Cascadeur-side script is the `csc` API surface only; the agent-facing server runs
  locally via `C:/Python314` with `mcp`+`fastmcp` installed.
