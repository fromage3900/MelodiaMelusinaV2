# Recent Commit Triage + Documentation Status — 2026-08-30

Purpose: provide a durable map from the recent Aug 26–30 documentation/agent-workflow burst into the next implementation commits, while preventing session-scoped notes from being mistaken for current canonical instructions.

## Status legend

- **CANONICAL** — safe to treat as current policy or current design direction.
- **ACTIVE HANDOFF** — still useful for implementation, but narrower than project-wide policy.
- **SESSION SNAPSHOT** — historical execution context; do not treat time-local wording such as “tonight” as a standing instruction.
- **IMPLEMENTATION NEEDED** — policy/design exists, but runtime/tooling work still needs to land.
- **ARCHIVE CANDIDATE** — preserve for history, but remove from the default agent reading path once a canonical replacement exists.

## Commit train map

```text
DONE / KEEP
│
├─ docs safe-batch merge: monolith backlog + level-design bible
├─ Sea Above system-integration docs
├─ P0/P1 character + art handoff
├─ Shorewake shader cookbook
├─ Rider + Junie workflow policy
└─ AGENT_LANES link to Rider + Junie policy

POLICY / DESIGN EXISTS, IMPLEMENTATION STILL NEEDED
│
├─ portable repo discovery across UE + Blender tooling
├─ fail-closed verification contracts
├─ offline-vs-live Unreal proof separation
├─ shared Rider run/verification configurations
└─ Junie project guidance / inherited task boundaries

SAFE TOOLING HARDENING LANDED
│
├─ _ExternalReference/ is git-ignored
└─ Starskiff downloader now uses durable reference-only wording

NEXT RUNTIME / TOOLING COMMITS
│
1. fix(tooling): portable repo discovery
2. test(tooling): fail-closed verification contracts
3. test(ue5): separate offline validation from live UE proof
4. chore(rider): shared Melodia run configurations
5. chore(junie): codify inherited Melodia proof/safety boundaries
6. feat(...): resume feature growth in narrow verified lanes
```

## Canonical documents

### Project/agent workflow

- `AGENTS.md` — top-level safe-working authority.
- `Docs/AGENT_LANES.md` — active lane/ownership guidance.
- `Docs/RIDER_JUNIE_UNREAL_WORKFLOW_2026-08-28.md` — **CANONICAL workflow hardening policy** until an undated successor is created.

The date in the Rider/Junie filename records when the policy was established; its contents are not session-limited. If materially revised, prefer creating an undated canonical successor and leaving this file as the historical policy baseline.

### Sea Above / P0 art direction

- `Docs/Art/SEA_ABOVE_SYSTEM_INTEGRATION_VISUAL_SHADER_BREAKDOWN_2026-08-26.md` — **ACTIVE HANDOFF** for system integration and visual layering.
- `Docs/Art/SHOREWAKE_DRESS_P0_SHADER_COOKBOOK_2026-08-28.md` — **ACTIVE HANDOFF** for Shorewake/Shorelistener material implementation.
- Character/party reference material merged through PR #25 — **CANONICAL design direction** for the P0 trio and first traversal concept unless superseded by explicit owner decisions.

### Monolith direction

The Aug 26 monolith backlog and level-design bible are **CANONICAL design/planning references** for the abstract Monolith roster. Generated boards remain reference acceleration, not final production assets.

## Session-scoped / stale-by-wording documents

The following files remain useful as historical execution snapshots but contain time-local wording that must not be interpreted literally after their authored session:

- `Docs/Art/TONIGHT_P0_P1_COMMIT_PLAN_2026-08-28.md` — **SESSION SNAPSHOT / ARCHIVE CANDIDATE**.
- `Docs/Art/STARSKIFF_TONIGHT_FREE_SYSTEMS_AND_DOWNLOADS_2026-08-28.md` — **SESSION SNAPSHOT**; extract durable Starskiff integration guidance before archiving.
- `Docs/Art/SEA_ABOVE_TONIGHT_EXECUTION_AND_AGENT_HANDOFF_2026-08-26.md` — **SESSION SNAPSHOT**; implementation facts may still be useful, but schedule language is stale.
- `Docs/Art/SEA_ABOVE_P0_BEAUTY_LOCK_TONIGHT_2026-08-28.md` — **ACTIVE ART DIRECTION + stale session wording**. Preserve its P0 visual priorities, but “tonight” should be read as “for the P0 beauty-lock pass,” not as a current deadline.

Do not delete these merely because they are dated. First extract any still-current rules into canonical files, then archive or clearly mark the originals.

## Immediate doc-cleanup rules

1. Replace time-local prose in executable scripts and canonical policy files first.
2. Do not mass-rename dated docs while active links depend on them.
3. Prefer a status header or canonical-index entry over rewriting large historical handoffs.
4. When a session plan becomes obsolete, preserve it as history but remove it from agent “read first” paths.
5. Distinguish **design canon**, **implementation handoff**, **session snapshot**, and **proof/evidence** in document headers.
6. Never let a dated planning note outrank `AGENTS.md`, `Docs/AGENT_LANES.md`, current owner locks, STOP sentinels, or a newer explicit canonical document.

## Current cleanup completed in this pass

- Added `_ExternalReference/` to `.gitignore` so optional research repositories cannot be accidentally staged.
- Reworded `Tools/External/Download_Starskiff_References.ps1` from “do not enable ... tonight” to a durable reference-only dependency rule.
- Added this status/index document so agents can classify the recent documentation burst without treating every dated file as equally current.

## Remaining stale-doc triage

### P0 — clean next

- Add explicit status headers to the four `TONIGHT`-named Sea Above / Starskiff documents above.
- Ensure no canonical agent file links to a session snapshot as if it were standing policy.
- Search for absolute workstation paths in currently active docs/tooling and move any machine-local examples behind portable variables.

### P1 — consolidate after implementation starts

- Create an undated `Docs/RIDER_JUNIE_UNREAL_WORKFLOW.md` only when the current policy materially changes; until then avoid duplicate policy text.
- Create a small undated Sea Above implementation index once the P0 material/level assets actually exist, linking design docs to the real asset paths and proof state.
- Move completed one-night commit plans to an archive folder only after link/reference checks.

### P2 — later cleanup

- Audit older experiment docs (`nemotron`, temporary agent harnesses, prior phone workflows) for whether they are active infrastructure, historical experiments, or safe-to-archive evidence.
- Reduce duplicated “read this first” chains so a new Rider/Junie session has one obvious entry path.

## Decision rule for agents

When two documents disagree, prefer in this order:

1. explicit current owner instruction;
2. `AGENTS.md` / STOP sentinels / owner locks;
3. current canonical workflow and lane docs;
4. active implementation handoffs;
5. dated design references;
6. session snapshots / historical execution plans.

If a lower-priority document conflicts with a higher-priority one, do not silently merge the instructions; follow the higher-priority source and note the stale conflict for cleanup.
