# Melodia — Production Master Index

**Last updated:** 2026-09-02
**Status:** CANONICAL NAVIGATION HUB

---

## 1. Purpose

This is the central cross-reference for all production-critical documentation. Every key doc is listed here with its role, relationships, and current status. Use this to find what you need and to verify nothing is orphaned.

---

## 2. Product Strategy (canonical, read in this order)

| Doc | Role | Status |
|-----|------|--------|
| `Docs/Strategy/MELODIA_ENDLESS_JOURNEY_NORTH_STAR_2026-09-02.md` | Product vision: evergreen single-player journey, Volume/Movement/Chapter structure, anti-live-service guardrails | CANONICAL PRODUCT VISION |
| `Docs/Strategy/MELODIA_CHAPTER_TIER_AND_VOLUME_ARCHITECTURE_2026-09-02.md` | 52-chapter grid, 7 metadata fields per chapter, Monolith pacing rule, tier permissions | CANONICAL CONTENT-STRUCTURE |
| `Docs/Strategy/MELODIA_EVERGREEN_CONTENT_AND_GIFT_MODEL_2026-09-02.md` | Gifts, Reveries, Voyages, no-FOMO default, Starskiff mailbox, save-history model | CANONICAL LONG-TERM UPDATE MODEL |

**Companion relationships:**
- Endless Journey ↔ Chapter Tier (cross-referenced)
- Endless Journey ↔ Evergreen Content (cross-referenced)
- Chapter Tier ↔ Evergreen Content (cross-referenced)

---

## 3. Current State (living documents, updated frequently)

| Doc | Role | Last Updated |
|-----|------|--------------|
| `CURRENT_STATE.md` | What is real today: systems, P0 proof status, closure song, git health | 2026-09-02 |
| `CURRENT_SYSTEM_MAP.md` | Architecture shape, stable owners, proof status, closure graph, content-scale shift | 2026-09-02 |
| `SYSTEM_MAP.md` | System architecture map: renewable content, chapter package layer, stable gameplay core | 2026-09-02 |

---

## 4. Development Workflow

| Doc | Role |
|-----|------|
| `QUICKSTART.md` | Entry point for new setup: read-first docs, setup requirements, toolchain |
| `COLLABORATOR_SETUP.md` | Collaborator onboarding: clone tiers, LFS, art delivery, toolchain import |
| `AGENTS.md` | AI agent rules: working agreement, skills, model lanes, MCP protocol, jcode swarm |
| `CLAUDE.md` | Claude-specific rules: agent boundaries, MCP surfaces, T3D pipeline, evidence standard |

---

## 5. Two-PC Development (new, 2026-09-02)

| Doc | Role |
|-----|------|
| `Docs/Production/TWO_PC_DEVELOPMENT_WORKFLOW_2026-09-02.md` | Five-lane workflow: Gateway, VS Code SSH, UBA, Git handoff, Hermes orchestration |
| `Docs/Production/LAPTOP_ONBOARDING_CLOSEOUT_2026-09-02.md` | Laptop (LAPTOP-Q8S5OSQ2) onboarding closeout: what was done, manual handoffs, verification log |

**Machine profile:** `worker-first-16GB` — Acer Nitro AN515-51, i5-7300HQ, 16 GB RAM, GTX 1050 Ti

---

## 6. Toolchain & Emerging Tech

| Doc | Role |
|-----|------|
| `Docs/Research/EMERGING_TOOLCHAIN_MASTER_INDEX_2026-08-31.md` | SSOT for toolchain discovery: PRESENT, SCAFFOLDED, WATCH, external |
| `Docs/Production/T3D_MONOLITH_REFERENCE.md` | T3D injection pipeline: specs, Monolith actions, CI gates |
| `Docs/Production/MODEL_LANES_2026-08-12.md` | Model lane routing: task classes, must-not rules |

---

## 7. Agent Infrastructure

| Doc | Role |
|-----|------|
| `.jcode/swarm-prompt.md` | jcode spawn scopes, concurrency cap, no recursive spawning |
| `.jcode/coordinator-bootstrap.md` | jcode coordinator bootstrap |
| `deploy/ai_tool_quickstart.ps1` | AI tool quickstart |
| `deploy/start_jcode_swarm.ps1` | jcode swarm launcher |

---

## 8. Key Entry Points (read these first)

1. `README.md` — project overview
2. `Docs/Strategy/MELODIA_ENDLESS_JOURNEY_NORTH_STAR_2026-09-02.md` — product vision
3. `CURRENT_STATE.md` — current truth
4. `QUICKSTART.md` — setup requirements
5. This index (`MASTER_INDEX.md`) — navigation hub

---

## 9. Archived

All deprecated scripts have been moved to `deploy/archive/deprecated-loops/`:

- `cursor_surreal_agent_loop.ps1`, `cursor_surreal_tierb_loop.ps1` — deprecated for parallel coding wakes
- `start_surreal_loop.ps1`, `start_surreal_tierb_loop.ps1`, `start_world_loop.ps1` — referenced archived loop scripts
- `start_cursor_agent_loop.ps1` — referenced archived cursor_surreal_agent_loop
- `stop_cursor_agent_loop.ps1`, `stop_surreal_loop.ps1`, `stop_surreal_tierb_loop.ps1`, `stop_world_loop.ps1` — cleanup for archived loops
- `surreal_micro_loop.ps1`, `surreal_world_loop.ps1` — deprecated (superseded by jcode swarm)

Active deploy scripts: `run_verify.ps1`, `test_laptop_workstation.ps1`, `validate_setup.ps1`, `start_jcode_swarm.ps1`, `sync_site_to_github.ps1`, `inspect_workstation.ps1`, `collaborator_onboarding.sh`, and ~30 others.

Preserved for reference. Do not reactivate without owner approval.

---

## 10. Verification

- All strategy docs dated 2026-09-02 and marked CANONICAL
- All state docs dated 2026-09-02
- Two-PC workflow and laptop onboarding indexed above
- Cross-references verified: Endless Journey ↔ Chapter Tier ↔ Evergreen Content
- Deprecated scripts identified for archival
