# Documentation Index

This is the front door for project documentation. Prefer updating this index over creating another floating status document.

## Latest checkpoint — 2026-08-12 (cloud git-health prep)

| Doc | Purpose |
|---|---|
| [Docs/Handoffs/CLOUD_AGENT_GIT_HEALTH_2026-08-12.md](Docs/Handoffs/CLOUD_AGENT_GIT_HEALTH_2026-08-12.md) | Tonight’s cloud work: PRs #4/#6, untrack/ignore, tomorrow merge order |
| [Docs/PhoneOps/BACKLOG.md](Docs/PhoneOps/BACKLOG.md) | Phone/cloud Now list aligned to merge → build → playtest |
| [README.md](README.md) | Front-door project status refreshed 2026-08-12 |

## Environment checkpoint — 2026-08-11

Read these before changing setup, ECHO, or cross-checkout tooling:

| Doc | Purpose |
|---|---|
| [Docs/ENVIRONMENT_SOURCE_OF_TRUTH_2026-08-11.md](Docs/ENVIRONMENT_SOURCE_OF_TRUTH_2026-08-11.md) | Workspace topology, authority boundaries, service contract, and drift register |
| [Docs/ENVIRONMENT_RUNBOOK_2026-08-11.md](Docs/ENVIRONMENT_RUNBOOK_2026-08-11.md) | Portable Windows setup and execution path |
| [Docs/Handoffs/ENVIRONMENT_BUILD_VALIDATION_2026-08-11.md](Docs/Handoffs/ENVIRONMENT_BUILD_VALIDATION_2026-08-11.md) | Evidence from the implemented environment and remaining blockers |
| [Docs/ECHO_PIPELINE_2026-08-09.md](Docs/ECHO_PIPELINE_2026-08-09.md) | ECHO stages, evidence rules, and campaign contract |

Read [`Docs/Handoffs/PROJECT_HANDOFF_2026-08-09.md`](Docs/Handoffs/PROJECT_HANDOFF_2026-08-09.md) first when
resuming gameplay work from another session. It records the earlier local Git
state, validation evidence, and known remote-network limitations as of 2026-08-09.

## ⭐ Gameplay/vertical-slice canonical docs (project root, read these first for gameplay)

As of 2026-07-30 these are the real, actively-maintained source of truth for gameplay/vertical-slice work — not a test, confirmed adopted over several days:

| Doc | Purpose |
|---|---|
| [`_AGENT_WORKING_AGREEMENT.md`](_AGENT_WORKING_AGREEMENT.md) | **Binding on every agent; outranks every other agent doc here.** Do the job asked and stop. No compensation mechanisms. "Kill it" means delete. Don't re-verify what the owner told you. A fix is not a review. Decision 026. |
| [`_SESSION_HANDOFF.md`](_SESSION_HANDOFF.md) | Most recent session's accomplished/pending/do-not-do list. Overwritten each session — read fresh every time. |
| [`_DECISION_LOG.md`](_DECISION_LOG.md) | Append-only strategic decisions (currently through 042). Check before re-litigating a settled question. |
| [`_TASK_QUEUE.md`](_TASK_QUEUE.md) | The real, live, granular task tracker — P0/P1/P2/P3, per-task status/agent. |
| [`_VERTICAL_SLICE_SCOPE.md`](_VERTICAL_SLICE_SCOPE.md) | Current scope authority for the First Dream vertical slice. Explicitly supersedes older SakuraDream/Phase-2 scope. |
| [`_ROADBLOCKS_2026-07-31.md`](_ROADBLOCKS_2026-07-31.md) | **Read before trusting any dated doc.** Consolidated roadblock inventory plus the contradiction register — which docs currently contain false claims, and the verdict on each. |

### ⏱ Dated-doc rule

A doc's filename date is when it was **written**, not when it was last **true**. This repo has
produced same-day contradictions more than once — `Docs/GAMEPLAY_REVIEW_2026-07-30.md` was wrong
about the travel system three minutes after being saved, and
`Docs/MELODIA_SYSTEMS_COMPOSITION_CONTRACT_2026-07-30.md` contradicts itself between §2 and §5a.
Before acting on a claim that something is missing or broken, check the relevant source file's
mtime. `_ROADBLOCKS_2026-07-31.md` tracks the known cases.

## Session docs — 2026-07-30 (were unindexed until 2026-07-31)

| Doc | Purpose |
|---|---|
| [Docs/BLUEPRINT_WIRING_CHECKLIST_2026-07-30.md](Docs/BLUEPRINT_WIRING_CHECKLIST_2026-07-30.md) | **The actionable list.** Five ordered editor-wiring items, each independently testable, none breaking anything if left undone. Its "cannot read graph topology" premise was corrected 2026-07-31. |
| [Docs/GAMEPLAY_REVIEW_2026-07-30.md](Docs/GAMEPLAY_REVIEW_2026-07-30.md) | Rhythm / teleport / Quill gap analysis. **§2 (teleport) is superseded** — see the banner at the top of the file. |
| [Docs/FOUNDATION_CLOSEOUT_DECISIONS_2026-07-30.md](Docs/FOUNDATION_CLOSEOUT_DECISIONS_2026-07-30.md) | Closeout decision record behind Decisions 012–021. |
| [Docs/MELODIA_SYSTEMS_COMPOSITION_CONTRACT_2026-07-30.md](Docs/MELODIA_SYSTEMS_COMPOSITION_CONTRACT_2026-07-30.md) | The composition/adapter pattern. **§2–3 historical; only §5a is current.** |
| [Docs/MELODIA_IDENTITY_AND_LOOP_2026-07-30.md](Docs/MELODIA_IDENTITY_AND_LOOP_2026-07-30.md) | What the game is, and the loop it is trying to close. |
| [Docs/FOUNDATION_LOCKIN_PLAN_2026-07-30.md](Docs/FOUNDATION_LOCKIN_PLAN_2026-07-30.md) | Morning plan for the closeout. Several "blocked" rows are stale — build gate has since closed. |
| [Docs/RHYTHM_COMBAT_SYSTEM_HANDOFF_2026-07-30.md](Docs/RHYTHM_COMBAT_SYSTEM_HANDOFF_2026-07-30.md) | Handoff for the quarantined rhythm-combat trio (Decision 011). |
| [Docs/MELUSINA_HAIR_REEXPORT_CHECKLIST_2026-07-30.md](Docs/MELUSINA_HAIR_REEXPORT_CHECKLIST_2026-07-30.md) | Hair re-export procedure. Its "still broken, shared_bones=0" headline is superseded — root cause was the ARP "Match to Rig" toggle. |
| [Docs/MELUSINA_BLENDER_AAA_PIPELINE_2026-07-30.md](Docs/MELUSINA_BLENDER_AAA_PIPELINE_2026-07-30.md) | Character pipeline reference. |

## Canonical Project Docs (environment-art / portfolio)

| Doc | Status | Purpose |
|---|---|---|
| [Docs/QUEUE.md](Docs/QUEUE.md) | **Active** | Environment-art/portfolio tracker only as of 2026-07-30 — gameplay tracking moved to the root docs above. |
| [Docs/PROJECT_STATUS_2026-07-25.md](Docs/PROJECT_STATUS_2026-07-25.md) | **Active** | Current cross-cutting status and decision record; supersedes stale sections of CURRENT_STATE.md. |
| [Docs/MELODIA_UE58_INTEGRATION_ARCHITECTURE_2026-07-26.md](Docs/MELODIA_UE58_INTEGRATION_ARCHITECTURE_2026-07-26.md) | **Active** | Gameplay-authority decision: JRPG template is mechanical authority, QuillScript narrative-candidate, ACFU archived. |
| [Docs/PCG_PORTFOLIO_HANDOFF_DEEPSEEK_2026-07-26.md](Docs/PCG_PORTFOLIO_HANDOFF_DEEPSEEK_2026-07-26.md) | **Active** | Handoff for DeepSeek: verify/finish 2-3 flagship PCG scenes (depth over breadth), fix stale `PCG_CATALOG.md` + RockScatter naming. |
| [Docs/MELODIA_INTEGRATION_EVIDENCE_REGISTER_2026-07-26.md](Docs/MELODIA_INTEGRATION_EVIDENCE_REGISTER_2026-07-26.md) | **Active** | Sol's proof-grade register for every gameplay-integration claim (Runtime/Tool/Compile-proven vs Planned vs Rejected). |
| [Docs/MELODIA_JRPG_CHARACTER_SKILL_SLICE_2026-07-26.md](Docs/MELODIA_JRPG_CHARACTER_SKILL_SLICE_2026-07-26.md) | **Active** | Sol's current gameplay work-in-progress; today's next steps are written verbatim at the bottom. |
| [Docs/AI_AGENTS_MODELS_WORKFLOW_GUIDE_2026-07-26.md](Docs/AI_AGENTS_MODELS_WORKFLOW_GUIDE_2026-07-26.md) | Reference | Which AI models/agents fit which of this project's 4 workflow lanes, with July 2026 benchmarks. |
| [Docs/AWS_AGENT_TOOLKIT_SETUP_2026-07-26.md](Docs/AWS_AGENT_TOOLKIT_SETUP_2026-07-26.md) | Reference | AWS CLI + Agent Toolkit setup record; flags the root-vs-IAM-user follow-up. |
| [README.md](README.md) | Implemented | Project pitch and entry point. |
| [CURRENT_STATE.md](CURRENT_STATE.md) | Partial — see PROJECT_STATUS | Truth table for platform readiness; gameplay sections superseded by the two rows above. |
| [MELIDIA_LONGTERM_HEALTH_SAFETY_PLAN.md](MELIDIA_LONGTERM_HEALTH_SAFETY_PLAN.md) | Implemented | Strategic roadmap for long-term health, safety, and sustainability. |
| [UNIVERSAL_ENVIRONMENT_PIPELINE.md](UNIVERSAL_ENVIRONMENT_PIPELINE.md) | Implemented | Generic environment production flow. |
| [MATERIAL_LOOKDEV_PIPELINE.md](MATERIAL_LOOKDEV_PIPELINE.md) | Implemented | Master-to-instance-to-preview workflow. |
| [AGENT_OPERATING_MODEL.md](AGENT_OPERATING_MODEL.md) | Implemented | Recursive agent roles and safety lanes. |
| [PORTFOLIO_READINESS.md](PORTFOLIO_READINESS.md) | Implemented | Portfolio infrastructure checklist. |

## Architecture

| Doc | Status | Notes |
|---|---|---|
| [SYSTEM_MAP.md](SYSTEM_MAP.md) | Implemented | High-level system map. |
| [CURRENT_SYSTEM_MAP.md](CURRENT_SYSTEM_MAP.md) | Implemented | Reality audit of portfolio generation loop. |
| [DATA_FLOW.md](DATA_FLOW.md) | Implemented | End-to-end data lifecycle. |
| [DEPENDENCY_GRAPH.md](DEPENDENCY_GRAPH.md) | Implemented | Subsystem dependencies. |
| [TASK_GRAPH.md](TASK_GRAPH.md) | Implemented | Production task dependency graph. |
| [SYSTEM_EVOLUTION_MAP.md](SYSTEM_EVOLUTION_MAP.md) | Planned/v2 | Evolution from MVP package to v2 tokens. |

## Materials And Look-Dev

| Doc | Status | Notes |
|---|---|---|
| [MATERIAL_PIPELINE.md](MATERIAL_PIPELINE.md) | Implemented | Core shader architecture. |
| [MATERIAL_SYSTEM_REVIEW.md](MATERIAL_SYSTEM_REVIEW.md) | Implemented | Principal-TA review and cleanup priorities. |
| [Docs/MATERIAL_NODE_TREE_REVIEW.md](Docs/MATERIAL_NODE_TREE_REVIEW.md) | Implemented | Universal and landscape node-stack review. |
| [Docs/MATERIAL_INTEGRATION.md](Docs/MATERIAL_INTEGRATION.md) | Implemented | Run order, instance families, loop notes. |
| [Docs/MATERIAL_SPECIALISTS_PLAN.md](Docs/MATERIAL_SPECIALISTS_PLAN.md) | Partial | Specialist landscape/water plan. |
| [Docs/MATERIAL_MIGRATION.md](Docs/MATERIAL_MIGRATION.md) | Partial | Migration context and legacy systems. |

## Portfolio, Website, And Design

| Doc | Status | Notes |
|---|---|---|
| [PORTFOLIO_PIPELINE.md](PORTFOLIO_PIPELINE.md) | Partial | Aspirational + implemented capture/package design. |
| [PORTFOLIO_PIPELINE_AUDIT.md](PORTFOLIO_PIPELINE_AUDIT.md) | Implemented | Audit of Unreal to package to Figma loop. |
| [Docs/PORTFOLIO_ORCHESTRATOR_PLAN.md](Docs/PORTFOLIO_ORCHESTRATOR_PLAN.md) | Partial | Rotating environment specialist loop. |
| [../Docs/DESIGN_SYSTEM.md](../Docs/DESIGN_SYSTEM.md) | Implemented | Design-system source of truth. |
| [../Docs/FIGMA_IMPLEMENTATION_GUIDE.md](../Docs/FIGMA_IMPLEMENTATION_GUIDE.md) | Implemented | Figma implementation guide. |
| [_github_deploy/README.md](_github_deploy/README.md) | Implemented | Wix/GitHub deployment baseline. |

## Agents And Automation (Historical as of Decision 002, 2026-07-26)

Per `_DECISION_LOG.md` Decision 002: no agent ownership boundaries, no interface contracts — direct access to everything. These docs are read for tool-capability context only, not followed as process. Current lane allocation (informal, file-claim based) is in `Docs/2026-07-29_PROJECT_HANDOFF.md`'s "Multi-agent parallel work allocation" section instead.

| Doc | Status | Notes |
|---|---|---|
| [AGENTS.md](AGENTS.md) | Historical | Multi-agent production framework — superseded process, kept for tool-capability reference. |
| [AGENT_BOUNDARIES.md](AGENT_BOUNDARIES.md) | Historical | Write boundaries and conflict prevention — no longer enforced. |
| [AGENT_OWNERSHIP.md](AGENT_OWNERSHIP.md) | Historical | Ownership and handshakes — no longer enforced. |
| [AUTOMATION_OPPORTUNITIES.md](AUTOMATION_OPPORTUNITIES.md) | Partial | Automation gap list. |

## Reports And Reviews

| Doc | Status | Notes |
|---|---|---|
| [ART_DIRECTOR_REVIEW.md](ART_DIRECTOR_REVIEW.md) | Report | Hiring-manager review. Sakura art pass remains human-owned. |
| [PCG_REFINEMENT_REPORT.md](PCG_REFINEMENT_REPORT.md) | Report | PCG refinement cycle summary. |
| [NEXT_HIGHEST_LEVERAGE_TASK.md](NEXT_HIGHEST_LEVERAGE_TASK.md) | Report | Previous capture-spine priority. |
| [deploy/SURREAL_ARCH_LOOP_STATE.md](deploy/SURREAL_ARCH_LOOP_STATE.md) | Report | Long-running architecture loop state. |

## Archive (2026-07-26)

Explicitly named as reference/superseded in `Docs/MELODIA_UE58_INTEGRATION_ARCHITECTURE_2026-07-26.md` — moved, not deleted:

- `Docs/_Reference/` — `MELODIA_ACFU_QUILLSCRIPT_COMPATIBILITY_MATRIX_2026-07-25.md`, `MELODIA_GAME_SYSTEMS_DEEP_REVIEW_2026-07-14.md`, `BP_INTEGRATION_REVIEW_2026-07-18.md`
- `Docs/_Superseded/` — `MELODIA_ROGUELIKE_GAMELOOP_COMPLETION_PLAN_2026-07-14.md`

Not yet archived (named only vaguely as "MelodiaCore rhythm/presentation implementation documents" — needs Sol/user confirmation on exact files before moving, to avoid archiving something still actively referenced).

## Reclassification Targets

These folders are the intended organization for future docs. Existing files do not need to be moved immediately.

- `Docs/Production/Materials/`
- `Docs/Production/LookDev/`
- `Docs/Production/PCG/`
- `Docs/Production/Capture/`
- `Docs/Reports/`
- `Docs/AgentMemory/`
- `Docs/Career/`
