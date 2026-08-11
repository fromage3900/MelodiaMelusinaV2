# jcode swarm — MelodiaMelusina

Project harness for [jcode](https://jcode.sh) parallel agents (swarm) mapped to Melodia PGA/MPA/PPA/WIA/SQA ownership.

## Files

| File | Purpose |
|---|---|
| `swarm-prompt.md` | Swarm routing + role spawn templates |
| `mcp.json` | Monolith MCP via **stdio** proxy (UE must be open) |
| `config.example.toml` | Copy/merge into `%USERPROFILE%\.jcode\config.toml` |
| `coordinator-bootstrap.md` | Paste-ready Recipe A/B coordinator prompt |

## One-time setup (Windows UE box)

```powershell
# Install jcode
irm https://jcode.sh/install.ps1 | iex
jcode login --provider claude   # or openai, copilot, gemini, ...

# User config (merge if you already have ~/.jcode/config.toml)
New-Item -ItemType Directory -Force -Path "$env:USERPROFILE\.jcode" | Out-Null
Copy-Item .jcode\config.example.toml "$env:USERPROFILE\.jcode\config.toml"

# Melodia skills → ~/.jcode/skills
.\deploy\install_jcode_melodia_skills.ps1

# Launch
.\deploy\start_jcode_swarm.ps1
```

Then paste `.jcode\coordinator-bootstrap.md` into the root session.

## Monolith MCP

`.jcode/mcp.json` points at `Plugins/Monolith/Scripts/monolith_proxy.bat`.

- jcode only supports **stdio** MCP (not HTTP `:9316` directly).
- Unreal Editor must be running with Monolith listening for those tools to work.
- Recipe A/B (docs/audits) work **without** the editor.

## Loops

- Keep: `deploy/start_surreal_*.ps1`, `start_world_loop.ps1`, `run_verify.ps1`
- Deprecated for parallel coding wakes: `deploy/cursor_*_loop.ps1` (use jcode swarm instead)

Full pipeline notes: `Docs/PhoneOps/JCODE_SWARM_PIPELINE.md`
