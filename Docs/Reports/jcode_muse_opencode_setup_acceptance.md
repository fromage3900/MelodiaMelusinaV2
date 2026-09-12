# jcode MUSE lane setup -- acceptance (2026-08-11)

**Outcome:** done  
**Role:** MUSE + SQA (Cursor coordinator + jcode lane validate)  
**Validation:** `.\deploy\start_opencode_muse_lane.ps1` PASS

## Tool versions

| Tool | Status |
|---|---|
| jcode | v0.75.3 (`%LOCALAPPDATA%\jcode\bin`) |
| opencode | 1.18.3 (npm) |
| muse (WSL) | Muse Code 0.1.0 (0.1.0-R708.1) |

## Artifacts landed

| Path | Purpose |
|---|---|
| `.opencode/opencode.jsonc` | OpenCode project config; Monolith/Blender MCP off by default |
| `.opencode/agent/build.md` | First Dream B3/B4/B7 build agent |
| `.opencode/agent/plan.md` | Readonly plan agent |
| `deploy/start_opencode_muse_lane.ps1` | PATH + tool validate; Rider shortcuts; no UE |
| `Docs/Handoffs/TONIGHT_FIRST_DREAM_OPENCODE_2026-08-11.md` | Tonight prep checklist |
| `.jcode/swarm-prompt.md` | MUSE spawn role added |
| `Docs/PhoneOps/JCODE_SWARM_PIPELINE.md` | Companion IDE lanes section |
| `AGENTS.md` section 5 | Companion lane pointers |

## Lane map

- **jcode** = parallel repo swarm (incl. MUSE worker for OpenCode/Muse wiring)
- **OpenCode in Rider** = C++/PIE gameplay (Ctrl+\\)
- **Muse Code (WSL)** = Meta terminal agent (auth already DONE)

## Blockers / follow-ups

- Human: Rider OpenCode plugin + Ctrl+\\ session when ready
- Human: enable `mcp.monolith.enabled` only with UE open on 9316
- Dirty working tree may still exist (textures / untracked content) -- reconcile before gameplay closeout
- Tip is past Muse study HEAD `2623f02a` -- use current tip

## Paths touched

Listed under Artifacts; no Content/Plugin binary edits from this lane.
