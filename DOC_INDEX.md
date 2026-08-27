# Documentation Index

This is the front door for project documentation. Prefer updating this index over creating another floating status document.


---

## Read these five, in this order

Everything below this section is reference. These five are authority.

| # | Doc | What it settles |
|---|---|---|
| 1 | [`../PROJECT.md`](../PROJECT.md) | **What this project is.** Melodia Melusina is a game. QuillScript + TurnBased JRPG are absolute authority. The AI tooling is a tool. If any doc below disagrees, this one wins. |
| 2 | [`Docs/ORCHESTRA_CONVERGENCE_2026-08-20.md`](Docs/ORCHESTRA_CONVERGENCE_2026-08-20.md) | **Which implementation owns which pillar.** This names one canonical owner per pillar, records contained competitors, and separates source convergence from still-open live proof. Check before writing anything. |
| 3 | [`Docs/ORCHESTRA_CONTRACT_2026-08-20.md`](Docs/ORCHESTRA_CONTRACT_2026-08-20.md) | **How the pillars meet the authority layers.** One owner and one direction per seam, each with the gate that proves it. Unproven seams are labelled UNPROVEN. |
| 4 | [`_AGENT_WORKING_AGREEMENT.md`](_AGENT_WORKING_AGREEMENT.md) | **How work gets done here.** Do the job, ship it, stop. Never compensate. Kill means delete. Owner statements are ground truth. |
| 5 | [`Docs/Handoffs/MELODIA_CONVERGENCE_CLOSEOUT_AND_P0_PLAN_2026-08-24.md`](Docs/Handoffs/MELODIA_CONVERGENCE_CLOSEOUT_AND_P0_PLAN_2026-08-24.md) | **What to do next.** Current P0 truth, the shortest convergence/proof path, and the long-term development order. |

**The current job is convergence, not construction.** A new parallel implementation of something
that already exists is a defect, not progress.

### Current checkpoint — 2026-08-24

| Doc | What |
|---|---|
| [`Docs/Handoffs/MELODIA_CONVERGENCE_CLOSEOUT_AND_P0_PLAN_2026-08-24.md`](Docs/Handoffs/MELODIA_CONVERGENCE_CLOSEOUT_AND_P0_PLAN_2026-08-24.md) | Convergence closeout, proof-tier truth, shortest P0 critical path, and post-P0 architecture plan. |
| [`Docs/P0_CLOSEOUT_TEST_PLAYBOOK_2026-08-24.md`](Docs/P0_CLOSEOUT_TEST_PLAYBOOK_2026-08-24.md) | Evidence-grade operator sequence for NPC/quest, four battle outcomes, restart, animation readback, and packaged P0 proof. |
| [`Docs/MELODIA_OVERALL_STATUS_2026-08-24.md`](Docs/MELODIA_OVERALL_STATUS_2026-08-24.md) | Current cross-cutting project status; keeps source, offline, historical-runtime, and current-live proof separate. |
| [`Docs/GIT_HEALTH_2026-08-24.md`](Docs/GIT_HEALTH_2026-08-24.md) | Local Git/LFS health, outgoing baseline, remaining holds, and push-ready checklist. |
| [`Docs/GIT_WORKTREE_INVENTORY_2026-08-24.md`](Docs/GIT_WORKTREE_INVENTORY_2026-08-24.md) | Current worktree ownership holds and safe batch order. |

The August 20 session closeout and animation review remain historical evidence;
use the August 24 checkpoint above for current routing.

### Marketing, funding and hiring material

`Docs/Career/` and `Docs/Portfolio/` are **downstream of the game**. They exist to fund and staff
it. **No agent may cite anything in them as project direction.**

---



## New 2026-08-13 — repo lock-in

| Doc | What |
|---|---|
| [`Docs/PERFORCE_MIGRATION_PLAN_2026-08-13.md`](Docs/PERFORCE_MIGRATION_PLAN_2026-08-13.md) | **Next phase.** Perforce for content, git for code. Plan only; not before the three completion gates close. |
| [`Docs/PERFORCE_MIGRATION_HANDOFF_2026-08-26.md`](Docs/PERFORCE_MIGRATION_HANDOFF_2026-08-26.md) | Perforce prep handoff — PREP ONLY, P4 not live |
| [`Docs/Handoffs/PERFORCE_SETUP_GUIDE_2026-08-26.md`](Docs/Handoffs/PERFORCE_SETUP_GUIDE_2026-08-26.md) | Helix + Tailscale + hybrid content seed steps |
| [`Docs/INTEGRATION_ROADMAP_2026-08-26.md`](Docs/INTEGRATION_ROADMAP_2026-08-26.md) | GitHub + P4 + phone/WSL + optional GitLab mirror |
| [`Docs/Reports/LFS_HEALTH_2026-08-13.md`](Docs/Reports/LFS_HEALTH_2026-08-13.md) | LFS evidence. `Exports/` is 63% of LFS; one `.git/lfs/bad` object is live-referenced. |
| [`Docs/AGENT_TOOLS.md`](Docs/AGENT_TOOLS.md) | Tool catalogue split out of AGENTS.md (32 KB subagent cap). |
| [`Docs/CREDITS.md`](Docs/CREDITS.md) | All asset credits: creator, source URL, license, usage — Epic/Fab, ArtStation, CC0, BOOTH, first-party, assembled kit, staging provenance. |
| [`Docs/SOURCES_MATRIX.md`](Docs/SOURCES_MATRIX.md) | Coverage map: every `Content/` folder → its credit row. Gate: `Tools/credits_gate.py` (must PASS on every import). |
| [`Docs/AGENT_MCP_SURFACES.md`](Docs/AGENT_MCP_SURFACES.md) | All MCP servers, one-writer rule, Monolith commands, CI. |
| [`Docs/AGENT_LANES.md`](Docs/AGENT_LANES.md) | Parallelisation, `.agents/plans/`, STOP sentinels, stage-save gate, owner locks. |
| [`Docs/_Superseded/README.md`](Docs/_Superseded/README.md) | 16 archived root docs and why each went. |

## Latest checkpoint — 2026-08-13 ~00:42 ET (loop stopped)

| Doc | Purpose |
|---|---|
| [Docs/Handoffs/SESSION_REVIEW_NEXT_PROMPTS_2026-08-13.md](Docs/Handoffs/SESSION_REVIEW_NEXT_PROMPTS_2026-08-13.md) | **Pick up here** — session review, close-or-not, paste-ready N0–N6 prompts |
| [Saved/Audit/melusina_blender_idle_wire.md](Saved/Audit/melusina_blender_idle_wire.md) | Blender idle import; meters/cm collapse; mocap restored to speed 0 |
| [Saved/Audit/tonight_prep_loop.md](Saved/Audit/tonight_prep_loop.md) | 15m loop ticks 1–17; **loop stopped** |

## Source-control checkpoint — 2026-08-13 ~00:50 ET

| Repository | State |
|---|---|
| `BS_GodFile` | `main` and `v2/main` synchronized at `840b7650`; working tree still has uncommitted editor/agent artifacts |
| `my-site-clean` | Local `3cfa5f0`; configured remote has unrelated history, so no merge or force-push was performed |
| Website checks | Site facts and assets pass; token lint remains blocked with `99` hard errors and `1113` warnings |

Full details: [SOURCE_CONTROL_STATUS_2026-08-13.md](Docs/Handoffs/SOURCE_CONTROL_STATUS_2026-08-13.md).

## Latest checkpoint — 2026-08-12 (cloud git-health prep)

| Doc | Purpose |
|---|---|
| [Docs/Handoffs/TWINMOTION_REALITYSCAN_SIDE_LANE_2026-08-13.md](Docs/Handoffs/TWINMOTION_REALITYSCAN_SIDE_LANE_2026-08-13.md) | **Twinmotion + RealityScan side lane** — scan/Datasmith paths into EnvSandbox; not a second art pipeline |
| [Saved/Audit/ue_idle_apply_2026-08-12.md](Saved/Audit/ue_idle_apply_2026-08-12.md) | A-idle: T1 ZenTrim applied, T2 41 Cathedral uassets, T3 Geometry Cache imported |
| [Saved/Audit/flip_hair_bake_2026-08-12.md](Saved/Audit/flip_hair_bake_2026-08-12.md) | Flip bake 1–240 (480 `.bobj`); ABC `GC_MelusinaHairFlip_v22.abc` frames 1–96 |
| [Docs/Handoffs/WORKFLOW_UNIFY_2026-08-12.md](Docs/Handoffs/WORKFLOW_UNIFY_2026-08-12.md) | After live v22: five doors, three session types, GN visual review (not more trees) |
| [Docs/Handoffs/RHYTHM_GAME_LOCKED_2026-08-12.md](Docs/Handoffs/RHYTHM_GAME_LOCKED_2026-08-12.md) | **OWNER LOCK — rhythm game WORKED** |
| [Docs/Handoffs/QUILLSCRIPT_LOCKED_2026-08-12.md](Docs/Handoffs/QUILLSCRIPT_LOCKED_2026-08-12.md) | **OWNER LOCK — QuillScript WORKED** |
| [Docs/Handoffs/PARALLEL_LANES_2026-08-12.md](Docs/Handoffs/PARALLEL_LANES_2026-08-12.md) | **Parallel agent lanes** (post rhythm+Quill locks) — claim table |
| [Docs/Handoffs/PARALLEL_SESSIONS_2026-08-12.md](Docs/Handoffs/PARALLEL_SESSIONS_2026-08-12.md) | **Paste-ready session prompts** for each lane |
| [Docs/BLENDER_MELODIA_COCKPIT.md](Docs/BLENDER_MELODIA_COCKPIT.md) | **Start here for Blender / Melodia Studio** — v22 path, MCP 9876, Health `12/12` / `165` |
| [Docs/Handoffs/BLENDER_MELODIA_STUDIO_HANDOFFS_2026-08-12.md](Docs/Handoffs/BLENDER_MELODIA_STUDIO_HANDOFFS_2026-08-12.md) | Blender lanes — **B0/B1/B3 done**; B2 plate dry-run still open |
| [Saved/Audit/gn_library_audit_2026-08-12.md](Saved/Audit/gn_library_audit_2026-08-12.md) | **GN library audit** — 165 construct; P0 presets **24/165 (14.5%)** |
| [Saved/Audit/gn_presets_audit_2026-08-12.json](Saved/Audit/gn_presets_audit_2026-08-12.json) | P0 preset inventory — 24 builders / 73 looks, 0 orphans |
| [Saved/Audit/melusina_needed_work_2026-08-12.md](Saved/Audit/melusina_needed_work_2026-08-12.md) | Melusina wardrobe SSOT retargeted to v22 / MCP 9876; live 5.2 still needed |
| [Saved/Audit/handpainted_texture_inventory_2026-08-12.md](Saved/Audit/handpainted_texture_inventory_2026-08-12.md) | Owner handpaint hunt — 1208 hits; no named lantern/wand/cross maps |
| [Saved/Audit/p0_level_mesh_gaps_2026-08-12.md](Saved/Audit/p0_level_mesh_gaps_2026-08-12.md) | Four P0 umaps exist; Cathedral 41 FBX not imported; no vow-cross SM |
| [Saved/Audit/water_hair_layer_c_runbook_2026-08-12.md](Saved/Audit/water_hair_layer_c_runbook_2026-08-12.md) | Layer C: 0 `.bobj`; tune+alembic helpers ready; bake blocked on 5.2 |
| [Saved/Audit/hero_zentrim_assign.json](Saved/Audit/hero_zentrim_assign.json) | `--apply` **done** — `MI_ZenTrim_Base4K` on wand + StreetLamp |
| [Saved/Audit/cathedral_fbx_import.json](Saved/Audit/cathedral_fbx_import.json) | Cathedral kit **41/41** imported to `/Game/EnvSandbox/Meshes/Cathedral/` |
| [Saved/Audit/hair_flip_geometry_cache_import.json](Saved/Audit/hair_flip_geometry_cache_import.json) | Layer C Geometry Cache at `/Game/Cinematics/MelusinaWaterHair/GC_MelusinaHairFlip_v22` |
| [Docs/Handoffs/TONIGHT_PORTFOLIO_STUDIO_PREP_2026-08-12.md](Docs/Handoffs/TONIGHT_PORTFOLIO_STUDIO_PREP_2026-08-12.md) | **Tonight board** — P0 levels, ZenTrim on heroes, water-hair Geometry Cache |
| [deploy/surreal_arch/Docs/GN_EXPANSION_PLAN_2026-08-12.md](deploy/surreal_arch/Docs/GN_EXPANSION_PLAN_2026-08-12.md) | **GN expansion** — P0 landed closed-editor; water-hair cache is cine-only |
| [Docs/Handoffs/PIE_RUNTIME_NOTES_2026-08-12.md](Docs/Handoffs/PIE_RUNTIME_NOTES_2026-08-12.md) | P0 PIE/runtime board — rhythm + Quill locked WORKED; battles still open |
| [Docs/Handoffs/CLOUD_AGENT_GIT_HEALTH_2026-08-12.md](Docs/Handoffs/CLOUD_AGENT_GIT_HEALTH_2026-08-12.md) | Tonight’s cloud work: PRs #4/#6, untrack/ignore, tomorrow merge order |
| [Docs/PhoneOps/BACKLOG.md](Docs/PhoneOps/BACKLOG.md) | Phone/cloud Now: P0 live proof + OpenCode-first sendoffs (NVIDIA withdrawn) |
| [Docs/PhoneOps/REMOTE_WSL_AGENT_STACK_2026-08-25.md](Docs/PhoneOps/REMOTE_WSL_AGENT_STACK_2026-08-25.md) | Phone → Blink/SSH → WSL/tmux agent stack — cloud-readable audit; PC installs need approval |
| [Docs/PhoneOps/AGENT_LANE_HANDOFF.md](Docs/PhoneOps/AGENT_LANE_HANDOFF.md) | Lightweight lane handoff fields + STATUS states |
| [Docs/Career/RECRUITER_SENDOFFS_2026-08-25.md](Docs/Career/RECRUITER_SENDOFFS_2026-08-25.md) | Paste-ready recruiter sendoffs — OpenCode → Toronto studios; NVIDIA WITHDRAWN |
| [README.md](README.md) | Front-door project status refreshed 2026-08-13 |

## Environment checkpoint — 2026-08-11

Read these before changing setup, ECHO, or cross-checkout tooling:

| Doc | Purpose |
|---|---|
| [Docs/BLENDER_MELODIA_COCKPIT.md](Docs/BLENDER_MELODIA_COCKPIT.md) | **Start here for Blender / Melodia Studio** — v22 path, MCP 9876, Health `12/12` / `165` |
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
| [UNIVERSAL_ENVIRONMENT_PIPELINE.md](Docs/_Superseded/UNIVERSAL_ENVIRONMENT_PIPELINE.md) | Implemented | Generic environment production flow. |
| [MATERIAL_LOOKDEV_PIPELINE.md](MATERIAL_LOOKDEV_PIPELINE.md) | Implemented | Master-to-instance-to-preview workflow. |
| [AGENT_OPERATING_MODEL.md](Docs/_Superseded/AGENT_OPERATING_MODEL.md) | Implemented | Recursive agent roles and safety lanes. |
| [PORTFOLIO_READINESS.md](Docs/_Superseded/PORTFOLIO_READINESS.md) | Implemented | Portfolio infrastructure checklist. |

## Architecture

| Doc | Status | Notes |
|---|---|---|
| [SYSTEM_MAP.md](SYSTEM_MAP.md) | Implemented | High-level system map. |
| [CURRENT_SYSTEM_MAP.md](CURRENT_SYSTEM_MAP.md) | Implemented | Reality audit of portfolio generation loop. |
| [DATA_FLOW.md](DATA_FLOW.md) | Implemented | End-to-end data lifecycle. |
| [DEPENDENCY_GRAPH.md](DEPENDENCY_GRAPH.md) | Implemented | Subsystem dependencies. |
| [TASK_GRAPH.md](Docs/_Superseded/TASK_GRAPH.md) | Implemented | Production task dependency graph. |
| [SYSTEM_EVOLUTION_MAP.md](Docs/_Superseded/SYSTEM_EVOLUTION_MAP.md) | Planned/v2 | Evolution from MVP package to v2 tokens. |

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
| [../Docs/DESIGN_SYSTEM.md](Docs/DESIGN_SYSTEM.md) | Implemented | Design-system source of truth. |
| [../Docs/FIGMA_IMPLEMENTATION_GUIDE.md](Docs/FIGMA_IMPLEMENTATION_GUIDE.md) | Implemented | Figma implementation guide. |
| [_github_deploy/README.md](_github_deploy/README.md) | Implemented | Wix/GitHub deployment baseline. |

## Agents And Automation (Historical as of Decision 002, 2026-07-26)

Per `_DECISION_LOG.md` Decision 002: no agent ownership boundaries, no interface contracts — direct access to everything. These docs are read for tool-capability context only, not followed as process. Current lane allocation (informal, file-claim based) is in `Docs/2026-07-29_PROJECT_HANDOFF.md`'s "Multi-agent parallel work allocation" section instead.

| Doc | Status | Notes |
|---|---|---|
| [AGENTS.md](AGENTS.md) | Historical | Multi-agent production framework — superseded process, kept for tool-capability reference. |
| [AGENT_BOUNDARIES.md](Docs/_Superseded/AGENT_BOUNDARIES.md) | Historical | Write boundaries and conflict prevention — no longer enforced. |
| [AGENT_OWNERSHIP.md](Docs/_Superseded/AGENT_OWNERSHIP.md) | Historical | Ownership and handshakes — no longer enforced. |
| [AUTOMATION_OPPORTUNITIES.md](Docs/_Superseded/AUTOMATION_OPPORTUNITIES.md) | Partial | Automation gap list. |

## Reports And Reviews

| Doc | Status | Notes |
|---|---|---|
| [ART_DIRECTOR_REVIEW.md](ART_DIRECTOR_REVIEW.md) | Report | Hiring-manager review. Sakura art pass remains human-owned. |
| [PCG_REFINEMENT_REPORT.md](PCG_REFINEMENT_REPORT.md) | Report | PCG refinement cycle summary. |
| [NEXT_HIGHEST_LEVERAGE_TASK.md](Docs/_Superseded/NEXT_HIGHEST_LEVERAGE_TASK.md) | Report | Previous capture-spine priority. |
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
