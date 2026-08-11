# Next Actions - Universal Environment Platform

## 🎯 Strategic Priority (2026-07-16)

**Long-term Health & Safety Plan:** [MELIDIA_LONGTERM_HEALTH_SAFETY_PLAN.md](MELIDIA_LONGTERM_HEALTH_SAFETY_PLAN.md)

**5-Pillar Strategic Roadmap:**
1. **System Health & Safety** - Multi-layer interlocks, automated recovery, data integrity
2. **Ease of Use & Accessibility** - Zero-config setup, progressive learning, workflow automation  
3. **Organization & Documentation** - Living docs, structure standards, knowledge management
4. **System Integration** - Unified MCP gateway, event bus, universal data format
5. **Monitoring & Analytics** - Performance dashboard, predictive failure detection, usage analytics

**Implementation Timeline:** 20-week phased approach
**Immediate Actions (Next 7 Days):** Safety interlocks, automated backup, unified setup script

---

## Current Priority

Build the generic material/look-dev spine without touching `L_SakuraPath`.

## 🔥 Agent Bridge Expansion (2026-07-20)

### Completed
- ✅ Created `deploy/agent_bridge_mcp.py` - Universal MCP bridge for all 5 agents
- ✅ Created `Content/Python/agent_status_panel.py` - UE in-editor status panel
- ✅ Created `deploy/blessing_evolution_daemon.py` - AI blessing generation daemon
- ✅ Created `deploy/start_agent_bridge.ps1` - Startup script
- ✅ Updated all MCP configs (.opencode.json, .cursor/mcp.json, .devin/mcp.json, .windsurf/mcp.json, .rider/mcp.json, user config)
- ✅ Updated `Content/Python/init_unreal.py` to register agent panel
- ✅ Updated `deploy/ai_tool_router.py` with bridge tools

### Available Agent Bridge Tools
- `delegate_to_agent` - Route intent to any agent (geometry/material/placement/integration/audit/blessing)
- `get_agent_status` - Get real-time status of all agents
- `get_agent_memory` - Query shared agent memory/context
- `run_blessing_evolution` - Queue blessing generation via Ollama
- `ue_editor_command` - Prepare commands for UE editor

### Test Results
```
Agent Bridge MCP Server: ✅ Working (5 tools available)
Agent Status Check: ✅ Shows all 5 agents + 21 blessings healthy
All MCP configs: ✅ Updated with agent-bridge server
```

### Next Steps
1. **Test in UE**: Launch Unreal Editor and verify "Agent Bridge Status" menu works
2. **Generate Blessings**: Use `run_blessing_evolution` to create new game content
3. **Query Agents**: Try `delegate_to_agent("geometry", "list_genomes")` for natural language
4. **Review Docs**: See `Docs/AGENT_BRIDGE_IMPLEMENTATION.md` for full details

## Recently Completed (2026-07-15)

### Migration Fixes (STOP file protected)
- Done: Grotto MI parent restoration - 4 orphaned MIs reparented to restored SDF masters
- Done: Marble texture recovery - 14 Marble textures copied to SDF/Textures/Marble/
- Done: MF_MooaToonBaseInput_2 - Copied to EnvSandbox Materials/Functions
- Done: Git revert recovery - BS_Melusina git restore complete (71 tracked files)
- Done: Texture ref cleanup - 56 of 63 missing refs cleared via disk copy/restore
- Done: 31 Material Functions restored (MF_VertexPaintBlend, MF_Triplanar, MF_ParallaxCore, etc.)
- Done: Greybox Kit meshes restored (4 wall meshes)
- Done: Genshin shader samples restored (2 shaders)

### Portfolio Components
- Done: Melodia portfolio components deployed - 7 animated components copied into `my-site/melodia-design-system/wix/`.
- Done: Professional editorial index page created - full portfolio layout in `wix/index.html`.
- Done: Deployment manifest updated - v2.0 with component URL inventory.
- Done: Committed to my-site main - commit `3b420dc` (push still requires GitHub connectivity).
- Done: Package-to-website handoff adapter added - `Content/Python/package_to_website_handoff.py` converts `Saved/Portfolio/portfolio_package.json` into `_github_deploy/generated/*_config.json`.

## Queue

1. Push to GitHub when connectivity and approval are available.
   - Current note from prior agents: local website work is ahead of `origin/main`.
   - Do not publish externally without explicit approval.

2. Produce generic look-dev capture pass.
   - Target: `L_Template`, not Sakura.
   - Capture: showcase material grid, landscape slab, water plane, trimsheet panel.

3. Validate Unreal material-system repairs from Kiro.
   - Check universal A/B/C layer combinations compile and behave.
   - Check Nikki landscape scale/normal behavior if `setup_landscape_height_blend.py` is rebuilt.
   - Check water parameter groups after `setup_master_water.py` changes.

4. Decide whether `my-site-clean/` should replace or supplement `_github_deploy/`.
   - `my-site-clean/` is currently an untracked clean clone with generated design-system/technical files.
   - `_github_deploy/` is the active deploy lane used by the Unreal package adapter.

## Completed Pipeline Commands

1. Generate material family manifest.
   - Command: `python Content/Python/material_family_manifest_full.py`
   - Output: `Saved/Portfolio/Materials/material_family_manifest.json`
   - Output: `Saved/Portfolio/MaterialPreviews/previews_manifest.json`
   - Latest result: 30 materials (`Showcase`: 11, `Zen`: 15, `Baroque`: 4)

2. Aggregate portfolio package.
   - Command: `python Content/Python/portfolio_aggregator.py`
   - Output: `Saved/Portfolio/portfolio_package.json`
   - Latest result: `sections_ok=True`, warnings `0`

3. Build package-to-website handoff.
   - Command: `python Content/Python/package_to_website_handoff.py`
   - Input: `Saved/Portfolio/portfolio_package.json`
   - Output: `_github_deploy/generated/hero_config.json`
   - Output: `_github_deploy/generated/passport_config.json`
   - Output: `_github_deploy/generated/portfolio_package_config.json`
   - Output: `_github_deploy/generated/materials_config.json`
   - Output: `_github_deploy/generated/renders_config.json`
   - Output: `_github_deploy/generated/stats_config.json`

4. Add agent memory docs.
   - `Docs/AgentMemory/Decisions.md`
   - `Docs/AgentMemory/RejectedIdeas.md`
   - `Docs/AgentMemory/MaterialStandards.md`

## Portfolio Deployment Status

| Component | Location | Status |
|-----------|----------|--------|
| Portfolio index | `wix/index.html` | Committed locally |
| Cosmic hero | `wix/melodia-hero-cosmic.html` | Committed locally |
| Navigation | `wix/melodia-navigation-constellation.html` | Committed locally |
| Project cards | `wix/melodia-project-card.html` | Committed locally |
| Gallery grid | `wix/melodia-gallery-grid.html` | Committed locally |
| Breakdown cards | `wix/melodia-breakdown-card.html` | Committed locally |
| Section headers | `wix/melodia-section-header.html` | Committed locally |
| Smooth scroll | `wix/melodia-smooth-scroll.html` | Committed locally |
| Hero embed | `wix/melodia-hero-embed.html` | Committed locally |
| Passport embed | `wix/melodia-passport-embed.html` | Committed locally |
| Deployment manifest | `generated/deployment_manifest.json` | Updated locally |
| Package handoff configs | `_github_deploy/generated/*_config.json` | Generated locally |
| Push to GitHub | `origin/main` | Requires connectivity and approval |

## Red-Line Constraints

- Do not edit Sakura level content.
- Do not delete legacy material assets.
- Do not rewrite master material families.
- Do not publish externally without explicit approval.
