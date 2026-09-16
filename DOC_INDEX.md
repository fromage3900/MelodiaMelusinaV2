# Melodia Documentation Map

**Purpose:** navigation only. This file is not a status report, task queue, handoff, or evidence claim.

For anything involving **what is true now, what is blocked, or what to do next**, read [`CURRENT_STATE.md`](CURRENT_STATE.md). If another document appears to disagree about current status, `CURRENT_STATE.md` wins.

## Start here

- [`CURRENT_STATE.md`](CURRENT_STATE.md) — only current status / priority / blocker / open-work authority.
- [`SYSTEM_MAP.md`](SYSTEM_MAP.md) — runtime ownership and stable system architecture.
- [`DATA_FLOW.md`](DATA_FLOW.md) — how state/data move through the runtime.
- [`Docs/Production/CANONICAL_PROJECT_PIPELINE_2026-09-08.md`](Docs/Production/CANONICAL_PROJECT_PIPELINE_2026-09-08.md) — cross-repo and cross-lane routing contract.

## Production / agent / workstation contracts

- [`Docs/Production/AGENTIC_STUDIO_OPERATING_MODEL.md`](Docs/Production/AGENTIC_STUDIO_OPERATING_MODEL.md) — how agents, evidence, Git, workstations, and knowledge tools cooperate.
- [`Docs/Production/BRANCH_WORKSTATION_POLICY.md`](Docs/Production/BRANCH_WORKSTATION_POLICY.md) — branch classes, workstation roles, cleanup and promotion rules.
- [`Docs/Production/LAPTOP_PROCEDURAL_LANE_2026-09-11.md`](Docs/Production/LAPTOP_PROCEDURAL_LANE_2026-09-11.md) — durable ASUS/Blender/GN/DCC lane contract.

## Worldbuilding / procedural environment

- [`Docs/WorldBuilding/WORLD_BUILDING_SOURCE_OF_TRUTH.md`](Docs/WorldBuilding/WORLD_BUILDING_SOURCE_OF_TRUTH.md) — chapter/world ownership and sound-to-form contract.
- [`Docs/Production/PCG/README.md`](Docs/Production/PCG/README.md) — canonical UE5.8 PCG authoring contract, including the validated Python Data Processor → semantic metadata → native PCG → per-instance material-data workflow used by Resonance Ecology / Sea Above.
- [`Docs/WorldGen/TERRAIN_HANDOFF_CONTRACT.md`](Docs/WorldGen/TERRAIN_HANDOFF_CONTRACT.md) — durable intake contract for terrain-authoring lanes before UE world integration.
- [`Docs/Research/README.md`](Docs/Research/README.md) — research index; research informs implementation but does not assign current work.

## Art / references

- [`Docs/Art/VISUAL_REFERENCE_INDEX.md`](Docs/Art/VISUAL_REFERENCE_INDEX.md) — canonical visual-reference entry point.
- [`Docs/References/ChoralSheepCapstone/AGENT_CONTEXT.md`](Docs/References/ChoralSheepCapstone/AGENT_CONTEXT.md) — durable Choral Sheep visual/material/gameplay contract.

## Animation / performance capture

- [`Docs/CASCADEUR_MELUSINA_PIPELINE_2026-08-07.md`](Docs/CASCADEUR_MELUSINA_PIPELINE_2026-08-07.md) — canonical Melusina Cascadeur / performance-capture authoring contract.

## TouchDesigner / After Effects

- [`Docs/TouchDesigner/MELODIA_TD_AE_CROSS_REPO_CONTRACT_2026-09-08.md`](Docs/TouchDesigner/MELODIA_TD_AE_CROSS_REPO_CONTRACT_2026-09-08.md) — UE ↔ TD ↔ AE ownership and handoff boundary.

## Compatibility / historical material

- [`AGENT_START_HERE.md`](AGENT_START_HERE.md) and [`CAPSTONE_NOW.md`](CAPSTONE_NOW.md) are compatibility redirects for historical links, not authorities.
- Dated plans, handoffs, scorecards, session notes, recovery documents, and archived reports are context/provenance only unless a durable contract explicitly incorporates their findings.
- Git history and the pre-collapse documentation tag preserve older material; do not recreate old status documents merely for discoverability.

## Obsidian usage

This repository may be opened as an Obsidian vault for human navigation. Git Markdown remains canonical.

Recommended bookmarks:

1. `CURRENT_STATE.md`
2. `DOC_INDEX.md`
3. `SYSTEM_MAP.md`
4. `DATA_FLOW.md`
5. the one lane contract relevant to the current task

For procedural/world-building sessions, bookmark `Docs/Production/PCG/README.md` beside the world-building authority so future agents do not rediscover the UE5.8 Python/PCG API traps from scratch.

Use backlinks, search, bookmarks, and local graph for discovery. Do not create Obsidian-only task queues, handoffs, dashboards, or duplicate status notes.

Because this is a large Unreal repository, exclude heavy/non-knowledge trees from Obsidian indexing where practical (for example build/cache/generated/binary content). `.obsidian/` workspace/config state is intentionally machine-local and Git-ignored by `.obsidian/.gitignore`.

## Documentation rule

A Markdown file should have one durable role:

- **CURRENT** — `CURRENT_STATE.md` only;
- **CONTRACT / SPEC / RUNBOOK** — stable rules and interfaces;
- **REFERENCE / BIBLE** — visual/design authority;
- **RESEARCH** — findings and experiments, not active assignments;
- **HISTORICAL** — provenance or compatibility only.

Do not create a second current-status surface.