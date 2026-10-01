# Melodia Documentation Map

**Purpose:** navigation only. This file is not a status report, task queue, handoff, or evidence claim.

For anything involving **what is true now, what is blocked, or what to do next**, read `CURRENT_STATE.md`. If another document appears to disagree about current status, `CURRENT_STATE.md` wins.

## Start here

- `CURRENT_STATE.md` — only current status / priority / blocker / open-work authority.
- `Docs/Production/AGENT_PRODUCTION_PLAYBOOK.md` — canonical task router for World Compiler, Hython, Rokoko, Rider and editor mutation workflows.
- `Docs/Production/RIDER_UE58_CANONICAL_WORKFLOW.md` — canonical JetBrains Rider + UE5.8 engineering runbook.
- `Docs/Production/JEV_CANONICAL_WORKFLOW.md` — canonical always-available Jev decision/orchestration runbook; Jev chooses/directs while existing owners execute.
- `qodana.yaml` — canonical Qodana `QDJB` static-analysis profile; RiderLink is covered by the Rider runbook as the focused live-editor automation bridge.
- `SYSTEM_MAP.md` — runtime ownership and stable system architecture, including the canonical Melusina system diagram and Universe Foundry boundary.
- `Docs/P1_TASK_LEDGER.json` → `melusina_work` — Melusina work gates and links to their evidence; current status still comes from `CURRENT_STATE.md`.
- `DATA_FLOW.md` — how state/data move through the runtime.
- `Docs/Production/CANONICAL_PROJECT_PIPELINE_2026-09-08.md` — cross-repo and cross-lane routing contract.

## Production / agent / workstation contracts

- `_AGENT_WORKING_AGREEMENT.md` — binding fast-start conductor path and scope rules.
- `Docs/Production/AGENTIC_STUDIO_OPERATING_MODEL.md` — how agents, evidence, Git, workstations, knowledge tools, and 3D scene-context preflight cooperate.
- `.claude/skills/melodia-conductor/SKILL.md` / `.agents/skills/melodia-conductor/SKILL.md` — routes a task to the smallest correct skill/context surface; not a task queue or authority.
- `Content/Python/scene_context_snapshot.py` — generates the machine-local `melodia.scene_context.v1` spatial packet for Unreal worldbuilding awareness.
- `Content/Python/scene_context_cycle.py` — records before/after 3D packets and a compact spatial/PCG diff for falsification.
- `.claude/skills/melodia-world-builder/SKILL.md` / `.agents/skills/melodia-world-builder/SKILL.md` — spatially aware world/PCG/environment runbook using the begin → build → end cycle.
- `Docs/Production/BRANCH_WORKSTATION_POLICY.md` — branch classes, workstation roles, cleanup and promotion rules.
- `Docs/Production/LAPTOP_PROCEDURAL_LANE_2026-09-11.md` — durable ASUS/Blender/GN/DCC lane contract.
- `Docs/Production/MODEL_ROUTING_CANON.md` — canonical model tier router policy (Nikki-grade multi-agent fleet: T0 Frontier through T4 Local).
- `specs/orchestration/model_tiers.v1.json` — machine-readable model tiering and task routing contract.


## Worldbuilding / procedural environment

- `Docs/WorldGen/WORLD_COMPILER_CONTRACT.md` — canonical compiled-world recipe/bundle/UE-driver contract; compile stays CLI.
- `Docs/Production/HOUDINI_CREATIVE_PIPELINE_REFERENCE_2026-08-28.md` — Hython/Houdini production caveats and verified export behavior; status still comes from `CURRENT_STATE.md`.
- `Docs/WorldBuilding/WORLD_BUILDING_SOURCE_OF_TRUTH.md` — chapter/world ownership and sound-to-form contract.
- `Docs/Production/PCG/README.md` — canonical UE5.8 PCG authoring contract, including the validated Python Data Processor → semantic metadata → native PCG → per-instance material-data workflow used by Resonance Ecology / Sea Above.
- `Docs/WorldGen/TERRAIN_HANDOFF_CONTRACT.md` — durable intake contract for terrain-authoring lanes before UE world integration.
- `Docs/Research/README.md` — research index; research informs implementation but does not assign current work.

## Art / narrative / references

- `Docs/Art/VISUAL_REFERENCE_INDEX.md` — canonical visual-reference entry point.
- `Docs/References/Narrative/MELODIA_CHARACTER_VOICE_BIBLE.md` — durable Melusina + Sir dialogue/performance/voicebank writing reference, including Quill line discipline and the "world as third speaker" rule.
- `Docs/References/Narrative/MELODIA_COMPENDIUM_BIBLE.md` — durable in-game Compendium content/UI contract: categories, entry grammar, narrative-flag discovery, Melusina field notes, optional voicebank snippets, and the existing Persona read-model seam.
- `Docs/References/ChoralSheepCapstone/AGENT_CONTEXT.md` — durable Choral Sheep visual/material/gameplay contract.

## Animation / performance capture

- `Docs/CASCADEUR_MELUSINA_PIPELINE_2026-08-07.md` — canonical Melusina Cascadeur / performance-capture authoring contract.
- `Docs/Handoffs/ROKOKO_MELUSINA_ANIM_EVIDENCE_2026-09-22.md` — evidence-backed Rokoko -> Blender -> guarded UE import lane; use with the production playbook, not as a second status authority.

## TouchDesigner / After Effects

- `Docs/TouchDesigner/MELODIA_TD_AE_CROSS_REPO_CONTRACT_2026-09-08.md` — UE ↔ TD ↔ AE ownership and handoff boundary.

## Compatibility / historical material

- `AGENT_START_HERE.md` and `CAPSTONE_NOW.md` are compatibility redirects for historical links, not authorities.
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

For procedural/world-building sessions, bookmark `Docs/Production/PCG/README.md` beside the world-building authority so future agents do not rediscover the UE5.8 Python/PCG API traps from scratch. The generated Scene Context packets/diffs remain under `Saved/Audit/SceneContext/` and should not become an Obsidian status/dashboard system.

For dialogue/Quill/voicebank writing, use `Docs/References/Narrative/MELODIA_CHARACTER_VOICE_BIBLE.md` as the durable character-performance reference; current narrative implementation/evidence still belongs to `CURRENT_STATE.md` and the runtime authorities.

For Compendium writing/UI work, use `Docs/References/Narrative/MELODIA_COMPENDIUM_BIBLE.md`; runtime entries live on `DA_MelodiaPersonaContent` and the UI reads them through `UMelodiaPersonaSubsystem` rather than maintaining a second lore database.

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
