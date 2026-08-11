# Session Handoff Template

**Purpose:** One-page handoff between sessions. Fill this out at the end of each session so the next session (or next agent) can start immediately without re-reading 30 docs.

**Instructions:** Copy-paste this template into the session's working document or use it as the header of your session notes. Do NOT create a new file per session — just one running `_SESSION_HANDOFF.md` that gets overwritten each time.

---

## Session Handoff

**Date:** YYYY-MM-DD
**Session type:** Portfolio / Vertical Slice / Pipeline Fix / Gameplay / Other
**Phase:** Phase 1 / Phase 2

### What was accomplished this session

- 
- 
- 

### What is left undone (specific, verifiable)

- 
- 
- 

### Decisions made this session

- 
- 

### Files modified this session

- 
- 

### Next session MUST start with

1. 
2. 
3. 

### Blueprint wiring tasks (if any this session)

> **Before wiring:** read `Docs/BLUEPRINT_WIRING_SKILL_2026-08-07.md` (operating procedure)
> and `Docs/BLUEPRINT_WIRING_CONTRACT_2026-08-07.md` (API source of truth).
> **Use `ueblueprintmcp` for all Blueprint graph work** — NOT Monolith or it-is-unreal.

| Blueprint | Graph | Task | `compile_blueprint` result | Verified? |
|---|---|---|---|---|
| | | | error_count: ___ / warning_count: ___ | ✅ / ❌ |
| | | | error_count: ___ / warning_count: ___ | ✅ / ❌ |

**Definition of done:** `compile_blueprint` returns `error_count == 0` and the graph was auto-saved.

### Known broken things (not blocking, but don't waste time debugging)

- 
- 

### Portfolio pipeline status

| Section | Status | Notes |
|---|---|---|
| scene | ✅ / ❌ / 🟡 | |
| assets | ✅ / ❌ / 🟡 | |
| materials | ✅ / ❌ / 🟡 | |
| renders | ✅ / ❌ / 🟡 | |
| pcg | ✅ / ❌ / 🟡 | |
| stats | ✅ / ❌ / 🟡 | |
| metadata | ✅ / ❌ / 🟡 | |

### Vertical slice status

| Component | Status | Notes |
|---|---|---|
| MelodiaCore compiles | ✅ / ❌ / 🟡 | |
| Player spawn | ✅ / ❌ / 🟡 | |
| NPC + dialogue | ✅ / ❌ / 🟡 | |
| Enemy encounter | ✅ / ❌ / 🟡 | |
| Battle loop | ✅ / ❌ / 🟡 | |
| Reward delivery | ✅ / ❌ / 🟡 | |
| End trigger | ✅ / ❌ / 🟡 | |
| Windows build | ✅ / ❌ / 🟡 | |
| itch.io page | ✅ / ❌ / 🟡 | |

---

## Session Startup (Read This First Next Time)

Before starting work, check:
1. `_DECISION_LOG.md` — any new decisions since last session?
2. `_SESSION_HANDOFF.md` — what was left undone?
3. `_PORTFOLIO_SHIP_CHECKLIST.md` or `_VERTICAL_SLICE_SCOPE.md` — where are we in the phase?
4. **If the task involves Blueprint wiring:** read `Docs/BLUEPRINT_WIRING_SKILL_2026-08-07.md`
   and `Docs/BLUEPRINT_WIRING_CONTRACT_2026-08-07.md` first. Use `ueblueprintmcp`, not Monolith.

Do NOT re-read CURRENT_STATE.md, CHANGELOG_24H.md, NEXT_ACTIONS.md, or any agent coordination docs. They are historical context, not actionable checklists.