# Melodia MCP System

**Version:** 1.0.0  
**Date:** 2026-08-18  
**Status:** Active — 28/28 tests passing, offline-capable, Monolith-fallback enabled  

---

## What this is

The Melodia MCP system is a dedicated Model Context Protocol server that exposes your core game systems — Persona-lite, QuillScript narrative, Rhythm Combat, Narrative state, and Blueprint fixture schema — to AI agents through a typed, policy-enforced tool surface.

It sits alongside your existing MCP servers (Monolith, agent_bridge, Blender, Cascadeur, TouchDesigner) and follows the same authorization and registration patterns.

---

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    AI Agent / Kimi Work                      │
│                      (MCP client)                            │
└────────────────────────┬────────────────────────────────────┘
                         │ stdio JSON-RPC
┌────────────────────────▼────────────────────────────────────┐
│              deploy/melodia_mcp_server.py                    │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────────────┐  │
│  │  Persona    │  │   Quill     │  │      Rhythm         │  │
│  │  get_stats  │  │  list/validate│  │    list_skills      │  │
│  │  get_quests │  │  scripts    │  │                     │  │
│  └─────────────┘  └─────────────┘  └─────────────────────┘  │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────────────┐  │
│  │  Narrative  │  │   Config    │  │    Blueprint        │  │
│  │ get_record  │  │ get_allowlist│  │ list/get/validate   │  │
│  │ audit_idem  │  │             │  │   validate_p0_route │  │
│  │ get_record  │  │ get_allowlist│  │ list/get/validate   │  │
│  │             │  │             │  │   fixtures          │  │
│  └─────────────┘  └─────────────┘  └─────────────────────┘  │
│  ┌────────────────────────────────────────────────────────┐  │
│  │              System (health, subsystems, preflight)     │  │
│  └────────────────────────────────────────────────────────┘  │
└────────────────────────┬────────────────────────────────────┘
         │               │               │
         ▼               ▼               ▼
   specs/*.json    Monolith 9316    Content/Python
   (offline)      (live fallback)    (future writes)
```

### Design principles

1. **Offline first** — Every read tool works from the spec registry without the editor running. No tool blocks on a dead Monolith.
2. **Policy enforced** — All tools check `specs/mcp_tool_policy.v1.json` via `Tools/mcp_policy.py`. Default decision is `deny`.
3. **Read-only v1** — No tool in v1 mutates project state. Future write tools (fixture materialization, allowlist merge) will require `editor` or `owner` approval.
4. **Schema aligned** — Template IDs match `specs/blueprints/melodia_gameplay_bp_kit.v1.json` exactly. Fixture validation checks the same fields the kit requires.
5. **Safe Python** — Avoids the fatal `D_DamageType` enum bug by never loading skill Blueprints through Python. Uses Monolith's C++ path for live asset inspection.

---

## Tool Reference

### Persona-lite

| Tool | Description | Offline? |
|------|-------------|----------|
| `melodia_persona_get_stats` | Read social stats (Harmony, Tempo, Timbre, etc.) | ✅ |
| `melodia_persona_get_quests` | List quests and their states | ✅ |

**Key contract:** Social stats live on `FMelodiaNarrativeRecord` (the project's single persistence seam). `UMelodiaPersonaSubsystem` reads and writes through `UMelodiaNarrativeSubsystem`, not a local copy. This is why stats survive reloads.

### QuillScript

| Tool | Description | Offline? |
|------|-------------|----------|
| `melodia_quill_list_scripts` | List `.qsc` sources and compiled `.uassets` | ✅ |
| `melodia_quill_validate_notification` | Validate a notification string against the 7-verb contract | ✅ |

**Seven-verb contract:**
- `melodia:battle:<EncounterId>`
- `melodia:quest:<QuestId>`
- `melodia:flag:<FlagId>:<true|false>`
- `melodia:travel:<LevelId>`
- `melodia:reward:<RewardId>`
- `melodia:stat:<IntentId>:<StatId>:<Delta>`
- `melodia:item:give:<ItemId>:<Count>`

**Idempotency:** `melodia:stat:` is idempotent per `<IntentId>`, not per `<StatId>`. The intent ID is recorded in `FMelodiaNarrativeRecord::ConsumedIntentIds`.

### Rhythm Combat

| Tool | Description | Offline? |
|------|-------------|----------|
| `melodia_rhythm_list_skills` | List rhythm skill definitions | ✅ |

**Grade multipliers** (from `MelodiaRhythmCombatTypes.h`):
- Poor = 0.35
- Good = 1.0
- Great = 1.2
- Perfect = 1.5

### Narrative

| Tool | Description | Offline? |
|------|-------------|----------|
| `melodia_narrative_get_record` | Return `FMelodiaNarrativeRecord` schema and idempotency seams | ✅ |
| `melodia_narrative_audit_idempotency` | Audit C++ source for ConsumeOnce guards and replay-safe paths | ✅ |

**Record schema version:** 4 (v1→v2 added SocialStats/BondRanks/PhaseIndex/SpawnContext; v2→v3 added Wardrobe; v3→v4 added WaterGameplayState)

**Idempotency guards verified:**
- `GrantDialogueSocialStat` — idempotent per `IntentId` via `ConsumedIntentIds`
- `GrantDialogueReward` — idempotent per `RewardId` via `ConsumedRewardIds`
- `CompleteQuest` — idempotent per quest key
- `CommitWorldChallenge` — atomic with intent+flag+reward consistency
- `ApplyStateAnchor` — replay-safe with operation-state matching
- `CompleteBattle` — guarded by `bBattleCompletionConsumed`

| Tool | Description | Offline? |
|------|-------------|----------|
| `melodia_narrative_get_record` | Return `FMelodiaNarrativeRecord` schema and idempotency seams | ✅ |

**Record schema version:** 4 (v1→v2 added SocialStats/BondRanks/PhaseIndex/SpawnContext; v2→v3 added Wardrobe; v3→v4 added WaterGameplayState)

### Config

| Tool | Description | Offline? |
|------|-------------|----------|
| `melodia_config_get_allowlist` | Read integration config allowlist entries | ✅ |

**Allowlist sets:** `WorldChallengeIds`, `StateAnchorIds`, `NarrativeFlagIds`, `DialogueRewardIds`, `QuestIds`, `SocialStatIds`, `EncounterIds`, `TravelLevelIds`

### Blueprint Fixtures

| Tool | Description | Offline? |
|------|-------------|----------|
| `melodia_bp_list_fixtures` | List all fixture specs and readiness levels | ✅ |
| `melodia_bp_get_template` | Get a template definition from the gameplay BP kit | ✅ |
| `melodia_bp_validate_fixture` | Validate a fixture spec has required fields | ✅ |
| `melodia_bp_validate_p0_route` | Validate P0 Dream golden run fixtures, scripts, and allowlist IDs | ✅ |

| Tool | Description | Offline? |
|------|-------------|----------|
| `melodia_bp_list_fixtures` | List all fixture specs and readiness levels | ✅ |
| `melodia_bp_get_template` | Get a template definition from the gameplay BP kit | ✅ |
| `melodia_bp_validate_fixture` | Validate a fixture spec has required fields | ✅ |

**Template IDs:** `skill`, `enemy`, `encounter`, `portal`, `traversal_gate`, `world_challenge`, `state_anchor`

**Readiness levels:**
- L0 = asset inventory recorded
- L1 = parent, interfaces, variables, events recorded
- L2 = live graph inspected
- L3 = disposable fixture exercised
- L4 = compile, reachability, evidence complete

### System

| Tool | Description | Offline? |
|------|-------------|----------|
| `melodia_system_health` | Health check across specs, assets, Monolith reachability | ✅ |
| `melodia_system_list_subsystems` | List native C++ subsystem authorities from headers | ✅ |
| `melodia_system_golden_run_preflight` | Pre-flight check for P0 golden run (maps, config, gates, echo) | ✅ |

### Resonant World

| Tool | Description | Offline? |
|------|-------------|----------|
| `melodia_resonant_world_get_atlas` | Read the deterministic asset-family atlas and movement inventory | ✅ |
| `melodia_resonant_world_compile_passage` | Compile one magical passage or the six-movement portfolio in memory | ✅ |
| `melodia_resonant_world_get_handoff` | Discover UI, gameplay, quantum, tool-call, and proof handoffs | ✅ |
| `melodia_resonant_world_validate` | Validate atlas, passages, PCG plan, and proof envelope | ✅ |

These calls are read/verify only. They do not write audit artifacts, maps, assets,
canonical narrative state, rewards, or traversal state. Their exact JSON examples
are documented in `Docs/Handoffs/RESONANT_WORLD_MCP_TOOL_CALLS_2026-08-22.md`.

| Tool | Description | Offline? |
|------|-------------|----------|
| `melodia_system_health` | Health check across specs, assets, Monolith reachability | ✅ |
| `melodia_system_list_subsystems` | List native C++ subsystem authorities from headers | ✅ |

---

## Registration

The server is registered in `.mcp.json` as the `melodia` server:

```json
"melodia": {
  "command": "C:/Python314/python.exe",
  "args": [
    "C:/EnvironmentPortfolio/BS_GodFile/deploy/melodia_mcp_server.py"
  ],
  "env": {
    "MONOLITH_URL": "http://localhost:9316/mcp"
  },
  "description": "Melodia MCP — Persona-lite, QuillScript, Rhythm Combat, Narrative, and Blueprint fixture tools"
}
```

To use it from Kimi Work or another MCP client, reference tools as `melodia_*`.

---

## Policy

All melodia tools are registered in `specs/mcp_tool_policy.v1.json` with:
- `decision`: `allow`
- `required_approval`: `none`
- `operations`: `["read"]` (and `["read", "verify"]` for validation tools)

Future write tools will require `editor` or `owner` approval.

---

## Testing

Run the validation suite:

```bash
python Tools/test_melodia_mcp.py
```

Tests verify:
1. Server imports cleanly
2. Tool registry matches schema spec
3. Every tool has a policy entry
4. Policy defaults to deny
5. All melodia tools are read-only
6. Offline tools work without Monolith
7. Quill notification validation is correct
8. Fixture validation finds specs and rejects unknowns
9. Server is registered in `.mcp.json`
10. Template lookup returns correct definitions
11. Idempotency audit detects all guarded mutation paths
12. P0 route validation checks fixtures, scripts, and allowlist IDs
13. Golden run pre-flight verifies maps, config, gates, and echo pipeline

All 28 tests pass.
1. Server imports cleanly
2. Tool registry matches schema spec
3. Every tool has a policy entry
4. Policy defaults to deny
5. All melodia tools are read-only
6. Offline tools work without Monolith
7. Quill notification validation is correct
8. Fixture validation finds specs and rejects unknowns
9. Server is registered in `.mcp.json`
10. Template lookup returns correct definitions

The legacy registry subset is covered by the full 28-test suite above.

---

## Integration with Existing Systems

### Monolith fallback
When `127.0.0.1:9316` is reachable, read tools delegate to Monolith for live asset state (e.g., `blueprint_query.get_cdo_properties` on `DA_MelodiaPersonaContent`). When Monolith is down, tools return offline data from the spec registry.

### Echo pipeline
The Melodia MCP system is compatible with the Echo pipeline:
- `melodia_system_health` can be called as a gate check
- `melodia_system_golden_run_preflight` verifies completion gates and route readiness
- `melodia_bp_validate_fixture` can verify fixture specs before materialization
- `melodia_bp_validate_p0_route` validates the full golden run fixture chain
- `melodia_quill_validate_notification` can validate authored dialogue beats
- `melodia_narrative_audit_idempotency` confirms idempotency contracts are enforced
The Melodia MCP system is compatible with the Echo pipeline:
- `melodia_system_health` can be called as a gate check
- `melodia_bp_validate_fixture` can verify fixture specs before materialization
- `melodia_quill_validate_notification` can validate authored dialogue beats

### Agent bridge
The existing `agent_bridge` MCP server routes intents to 5 agent types (geometry, material, placement, integration, audit, blessing). The Melodia MCP server is a separate, dedicated surface for game-system queries. Agents can use both:
- Use `agent_bridge` for routing to the right lane
- Use `melodia_*` tools for direct game-system inspection

---

## Files

| File | Purpose |
|------|---------|
| `deploy/melodia_mcp_server.py` | MCP stdio server (main entrypoint) |
| `specs/mcp/melodia_mcp_tools.v1.json` | Tool schema and contract documentation |
| `specs/mcp_tool_policy.v1.json` | Authorization policy (updated with melodia entries) |
| `.mcp.json` | MCP client registration |
| `Tools/test_melodia_mcp.py` | 28-test validation suite |
| `Docs/MCP_MELODIA_SYSTEM.md` | This document |
| `Docs/Handoffs/RESONANT_WORLD_UI_HANDOFF_2026-08-22.md` | UI event and HUD integration contract |
| `Docs/Handoffs/RESONANT_WORLD_GAMEPLAY_HANDOFF_2026-08-22.md` | Wardrobe/music/traversal gameplay handoff |
| `Docs/Handoffs/RESONANT_WORLD_QUANTUM_HANDOFF_2026-08-22.md` | Q#/classical fallback handoff |
| `Docs/Handoffs/RESONANT_WORLD_MCP_TOOL_CALLS_2026-08-22.md` | MCP and CLI tool-call record |

---

## Future Work

Planned v1.1+ tools (will require `editor`/`owner` approval):
- `melodia_bp_materialize_fixture` — Create a Blueprint from a fixture spec
- `melodia_config_merge_allowlist` — Merge the seed into `DA_MelodiaIntegrationConfig`
- `melodia_quill_compile_script` — Reparse and compile a `.qsc` asset
- `melodia_narrative_set_flag` — Set a narrative flag (with idempotency check)
- `melodia_persona_add_stat` — Add a social stat delta (with intent consumption)

---

## Authority Reminder

As with every surface in this project:
- **Persona-lite** owns social stats, quests, and equipment requests — but the JRPG template owns combat, inventory, and canonical saves.
- **QuillScript** owns dialogue flow — but the narrative subsystem owns validation, allowlists, and idempotency.
- **Rhythm Combat** owns skill catalog and grading — but the stock resolver owns damage, healing, and turn advancement.
- **The Melodia MCP server** owns inspection and validation — but never gameplay mutation without explicit approval.

One authority per concern. The MCP surface is read-only by design.
