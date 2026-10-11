# Melodia Emerging-Toolchain Master Index — 2026-08-31

**PURPOSE:** Single authoritative discovery SSOT for all emerging-toolchain / render / audio research.
Read this FIRST before proposing or building anything in these systems. It records, with exact paths:
what is **already present/implemented**, what is **scaffolded**, what is **research-only**, and what is an
**external tool** — so no agent re-derives, duplicates, or claims-absent what exists.

**Supercedes-as-SSOT:** `Docs/Research/AGENT_TOOLCHAIN_DISCOVERY_INDEX_2026-08-30.md` (keep both; this one
extends it with on-disk verification + the subsystems built 2026-08-31).
**Evidence basis:** everything below was verified against `Source/`, `Plugins/`, `Content/`, and the
research corpus on 2026-08-31 (not assumed).

---

## 0. The non-negotiable rule

> **Before creating a new graph / subsystem / tool for ANY of these systems, check the "STATUS" column
> below and the cited path. If it says PRESENT or SCAFFOLDED, extend it — do not build a parallel copy.**
> "A new parallel implementation is a defect, not progress" (AGENTS.md convergence rule).

---

## 1. Already PRESENT on disk (verified) — do NOT rebuild

| System | Status | Path / evidence |
|---|---|---|
| **SpeedTree** | **PRESENT — Core plant authority** | `Content/EnvSandbox/Materials/Masters/M_SpeedTreeMaster.uasset` · `Content/Python/reset_speedtree_wind_instances.py` |
| **Houdini 22 / Houdini Engine** | **PRESENT** | `Plugins/HoudiniEngine/` · Houdini 22.0.368 at `C:/Program Files/Side Effects Software/Houdini 22.0.368` |
| **Copernicus** (Houdini GPU texture/mask) | **PRESENT (implementation)** | `Tools/Houdini/copernicus/` (README, dress bake, petal variants, fabric sheen, terrain→nanite) |
| **Gaea** | **PRESENT** | `Plugins/GaeaUnrealTools/` |
| **PCG + toolkit** | **PRESENT** | `Plugins/PCGExtendedToolkit/` · UE PCG enabled |
| **Unreal MCP / Monolith** | **PRESENT** | `Plugins/UnrealMCP/` · `Plugins/Monolith/` (1330+ actions) |
| **NNERuntimeORT** | **PRESENT** | in `BS_GodFile.uproject` (enables neural inference) |
| **Audio-Reactive presentation (synesthesia Tiers 1–3)** | **PRESENT — full impl** | `Source/.../MelodiaAudioReactivePresentationSubsystem.h/.cpp` — writes `MPC_Melodia_Palette` + `NPC_Melodia_Palette` (BeatPulse/BeatPhase/BeatIntensity/…). **This is the single audio writer — never add a second.** |
| **Music clock** | **PRESENT** | `Source/.../MelodiaMusicClockSubsystem.h/.cpp` |
| **onnx model** | **PRESENT** | `Plugins/Claireon/Resources/Models/bge-small-en-v1.5-int8/model.onnx` (34 MB, text-embedding for Claireon) + onnxruntime installed |
| **Claireon** | **PRESENT — editor-ACTIVE (owner-approved in-editor usage)** | `Plugins/Claireon/` vendored @ `ed0b457`, enabled in `.uproject` (`6e48ffbc`), editor-module binary built 08-22. Client probe `Tools/test_claireon_toolcalls.py` — qwen3-coder:30b **7/8** (2026-08-31). Owner confirmed concurrent in-editor use is fine; the older "isolate from Monolith" warning no longer applies as a hard rule. See `Docs/CLAIREON_PREP_2026-08-20.md`. |
| **Cymatics / audio→geometry Chladni** | **PRESENT — source-verified, read-only MPC consumer** | `Source/.../MelodiaCymaticsSubsystem.h/.cpp` (`UGameInstanceSubsystem`, `FTSTicker`, reads `MPC_Melodia_Palette` `BeatPulse`/`BassIntensity` read-only via `GetParameterCollectionInstance` — no writes, `IsReadOnlyByContract()=true`, Chladni `cos(n·π·u)cos(m·π·v)−cos(m·π·u)cos(n·π·v)`) · `Tools/Houdini/copernicus_cymatic_parallax.py` · `Saved/Audit/copernicus_cymatic/` **21 variants × 1665 PNGs (185 Height, 9 maps: BaseColor/Normal/Roughness/Metallic/Height/ORM/Emissive/Iridescence/Opacity, 139 MB, all PNG magic valid)** · probe `Saved/Audit/cymatics_probe_2026-08-31.json` 5/5 PASS · audit `Saved/Audit/cymatics_audit_2026-09-01.json`. Build: closed-editor `Build.bat` required for PIE. Single-writer guard: `UMelodiaAudioReactivePresentationSubsystem` remains the sole MPC writer — this subsystem is READ-ONLY. Promoted from §2 SCAFFOLDED 2026-09-01 (grand_review phase_1). |

## 2. SCAFFOLDED by me 2026-08-31 (buildable, additive new files) — extend, don't duplicate

| System | Purpose | Source files | Build status |
|---|---|---|---|
| `UMelodiaCaptureRenderSubsystem` | offscreen SceneCapture HDR render pipeline (4-view, PPV gate) | `Source/.../MelodiaCaptureRenderSubsystem.h/.cpp` | needs closed-editor build |
| `UMelodiaDressingSubsystem` | Dash-capability native dressing/art-pass (hero props, debris, composition) | `Source/.../MelodiaDressingSubsystem.h/.cpp` | needs build |
| `UMelodiaVisualRepresentationSubsystem` | Magpie simulation↔visual seam (read-only) | `Source/.../MelodiaVisualRepresentationSubsystem.h/.cpp` | needs build |
| `UMelodiaVegetationGrowthSubsystem` | PCG growth supplementing PRESENT SpeedTree | `Source/.../MelodiaVegetationGrowthSubsystem.h/.cpp` | needs build |
| ~~`UMelodiaCymaticsSubsystem`~~ | ~~audio→geometry Chladni pattern (READ-ONLY consumer of the existing MPC writer)~~ | ~~`Source/.../MelodiaCymaticsSubsystem.h/.cpp`~~ | **PROMOTED to §1 PRESENT 2026-09-01 — see Cymatics row above; audit `Saved/Audit/cymatics_audit_2026-09-01.json`** |

Tools (runnable, committed): `Tools/mcp_tool_surface.py` (Unreal-MCP safe tool surface, dry-run default),
`Tools/test_dressing.py`, `Tools/test_visual_seam.py`, `Tools/test_cymatics.py`, `Tools/test_dash_capture.py`,
`Tools/branch_health.py`. Probes → `Saved/Audit/{dressing,visual_seam,cymatics,dash_probe}_*.json`.

## 3. Research-only / WATCH — do NOT promote without an explicit task

| System | Status | Where |
|---|---|---|
| **Magpie** (generative realtime renderer) | WATCH — seam scaffolded only, NO renderer | `Docs/Research/MAGPIE_SEAM_ARCHITECTURE_2026-08-31.md` |
| **Neural shaders / materials** | WATCH — needs a *material* onnx (present onnx is embedding-only) | `EMERGING_3D_RENDERING_TOOLCHAIN_RESEARCH` §neural |
| **Procedura** | RESEARCH ONLY | `EMERGING_3D_RENDERING_TOOLCHAIN_RESEARCH` §Procedura |
| **RTX Kit / NvRTX** | WATCH — do not fork shipping renderer | `EMERGING_3D_TOOLCHAIN_TRENCH_SWEEP_03` §14 |

## 4. External commercial tools — NOT buildable natively, not vendored

IlluGen, LiquiGen, EmberGen (JangaFX) · Cascadeur · Marmoset Toolbag · World Creator · Rokoko Vision ·
MetaTailor · InstaMAT · Material Maker · ArmorPaint · Style3D · Autodesk Flow Studio · Notch · D5/Octane/V-Ray ·
Polygonflow **Dash** (dressing plugin — absent; native `UMelodiaDressingSubsystem` is the buildable fallback).
Full catalog + Melodia roles: `EMERGING_3D_TOOLCHAIN_TRENCH_SWEEP_02_2026-08-30.md` (24 tools),
`EMERGING_3D_TOOLCHAIN_TRENCH_SWEEP_03_2026-08-30.md`.

## 5. Two architecture contracts to formalize (do NOT build a giant framework)

**5a. SpeedTree semantic bridge** — 9 world-description fields Houdini/PCG/material systems use to decide
how SpeedTree assets appear (SpeedTree does NOT ingest these directly):
`melodia_moisture, melodia_slope, melodia_wind_exposure, melodia_soil_depth, melodia_monolith_proximity,
melodia_molt_age, melodia_filter_flow, melodia_tension, melodia_ecological_density`.
Source: `TOOLCHAIN_INTEGRATION_SPIKE_PLAN_2026-08-31.md` §SpeedTree.

**5b. Melodia World Field Bus** — a *minimum* shared spatial-field contract so plugins stop inventing their
own world truth: `WorldField.FilterFlow / Tension / Moisture / Contact / Residue / Reaction /
AnchorStability / Resonance`. Representations by scale (MPC / RVTs / Niagara grids / Houdini fields / PCG
metadata). **Do not build a generalized field framework tomorrow** — discover the minimum contract via R&D.
Source: `EMERGING_3D_TOOLCHAIN_TRENCH_SWEEP_02_2026-08-30.md` §A.

**5b-i. Cymatic pattern publishers** (added 2026-09-06 per `cymatics_present_remaining_steps_2026-09-03.json` step 3):
`UMelodiaCymaticsSubsystem` publishes to the World Field Bus via its Chladni interference output — cymatic
`ModeN / ModeM` integer pair maps to `WorldField.Resonance` (the standing-wave harmonic signature at a point),
and `SampleCymaticAmplitude` (0..1 spread) maps to `WorldField.Tension` (how strongly the pattern is "pulling"
at that location). Downstream consumers (water ripple displacement, PCG scatter density, material emissive
pulse) read these fields — they do not call the cymatic subsystem directly. Cross-reference:
`Saved/Audit/ecosystem_integration_report.json` mapping_01_cymatic_to_rhythm + mapping_04_cymatic_to_water.

**5c. Unified terrain-handoff contract (added 2026-09-12):** all three terrain
authoring lanes — MIDI voxel (`melodia_studio`), Blender 5.2 audio GN
(`Tools/audio_terrain_pipeline.py`), and Gaea 2 native (`Docs/WorldGen/GAEA_SETUP_*`)
— emit a sibling `terrain_handoff.json` in the single `melodia.terrain_handoff.v1`
schema implemented by `Tools/terrain_handoff.py` (converters + validators + CLI),
then validate with `python Tools/terrain_handoff.py validate --strict`. A handoff
that does not validate is not UE-ready; a new lane schema without a converter is a
defect. Contract: `Docs/WorldGen/TERRAIN_HANDOFF_CONTRACT.md`. Evidence:
`Saved/Audit/terrain_handoffs/`.

## 6. Houdini execution plan (executable, reviewed)

`Docs/Houdini/MARA_P0_P3_HOUDINI_EXECUTION_PLAN_2026-08-29.md` — Mara + P0–P3. HDA families:
`HDA_ENV_TerrainStamp, HDA_ENV_PathCorridor, HDA_ENV_ScatterMaskBuilder, HDA_ENV_HeroRockFamily,
HDA_ENV_LOD_Collision_Batch, HDA_CH_CurlCluster`. **Primary rule: Houdini manufactures reusable geometry/
masks/LODs/scatter; gameplay authority + final composition stay in Unreal. Bake — never leave final playable
scenes dependent on live HDA cooking.** Companion: `Docs/Houdini/MELUSINA_HOUDINI_UE58_TECHNICAL_RESEARCH_2026-08-30.md`.

## 7. Cymatics / audio-visual synesthesia (implemented thread)

`Docs/MELODIA_AUDIO_VISUAL_SYNESTHESIA_LAYER_2026-08-28.md` — 5-tier (Music Clock → MPC → MetaSounds/PPV/Niagara).
Tiers 1–3 implemented (`MelodiaAudioReactivePresentationSubsystem`); audio→geometry (Test E) **PRESENT** as
`UMelodiaCymaticsSubsystem` (Chladni pattern, read-only — promoted §2→§1 2026-09-01, audit `Saved/Audit/cymatics_audit_2026-09-01.json`). The only "Sakura" here is `NS_Melodia_PetalLoop`
(audible-reactive petals) — a **legitimate** melodic use, distinct from the banned art direction.

## 8. Integration spike plan — 16 tests, tiered

`Docs/Research/TOOLCHAIN_INTEGRATION_SPIKE_PLAN_2026-08-31.md`: Tier A (Copernicus, IlluGen, Cascadeur,
Unreal MCP, Mesh Terrain+PCG), Tier B (Dash, LiquiGen, EmberGen, Toolbag, Gaea, World Creator, PVE),
Tier C/D (RTX, neural, Procedura, Magpie). **Every test uses the required-result template; ADOPT/PARK/REJECT gates.**

## 8a. Agent harness / MCP trench sweep — 2026-09-22

**Status for every item in this section: RESEARCH / WATCH unless a PRESENT row elsewhere explicitly says otherwise.**
This is the owner-approved "install twelve things" research queue, not permission to replace canonical Melodia
authorities. The goal is to make models replaceable workers around the existing World Compiler, Hython,
Rider/Qodana, gameplay owners, evidence gates, and Jev director — not to create twelve competing frameworks.

### The twelve candidates

| # | Tool / harness | What it adds | Melodia-shaped use | Canary / boundary |
|---|---|---|---|---|
| 1 | **Epic Unreal MCP (UE 5.8, Experimental)** | Engine-native local MCP server + Toolset Registry; AllToolsets exposes actor, lighting, material, Slate, automation and other editor tools; dedicated PCG guidance exists | Native UE control surface and eventual custom Melodia toolsets | Enable only in an Unreal Sandbox / disposable canary first. Calls execute serially on the game thread. **Never overlap tool calls or let native Unreal MCP and Monolith mutate the same graph/asset transaction.** Source: https://dev.epicgames.com/documentation/unreal-engine/unreal-mcp-in-unreal-editor |
| 2 | **per-simmons/unreal-agent-harness** | UE 5.8 agent recipes, viewport capture decoding and a see → act → check → fix QA loop around Epic's Unreal MCP | Steal the visual-verification pattern so an agent proves a world/edit looks right instead of merely reporting tool success | Quarry patterns; do not wholesale import city/Cesium assumptions. Validate viewport capture + compact evidence on one canary level. Source: https://github.com/per-simmons/unreal-agent-harness |
| 3 | **Pi coding agent** | Small, extensible coding-agent core designed to be composed rather than treated as a monolith | Candidate lightweight runtime beneath Jev-directed specialist work | Test in a disposable clone with no UE writer attached. Prefer project-local config and explicit permissions. Source: https://pi.dev/ |
| 4 | **pi-muselinn-harness** | Adds concurrent subagents, goal/budget lifecycle, plan mode, permission chain, background tasks, cron, hooks, todos and skills to Pi | Strong candidate for the missing **Melodia Orchestrator runtime**: Jev emits bounded jobs; Pi/Muselinn dispatches specialists | Third-party package can execute code. Review source before install. First canary = three read-only/repo-safe specialists with a concurrency cap; no editor mutation. Source: https://pi.dev/packages/pi-muselinn-harness |
| 5 | **SUNRNEHUI Agent Harness v10** | Provider-neutral portable handoff/acceptance layer: native / portable / audited modes with compact contract, event log and capsule | Cross-model continuity across Codex / Claude / Grok / Qwen-style workers without another giant status document | **Pattern to adopt before framework.** Map portable state to Melodia's existing SSOT; never make capsule/status files authoritative over CURRENT_STATE.md. Source: https://github.com/SUNRNEHUI/agent-harness |
| 6 | **GameStudio** | Provider-neutral game-dev studio brain with specialist agents, skills, hooks, rules and Unreal/Three.js coverage | A **skill quarry** for UE, technical-art, VFX/shader, QA, Three.js and asset-pipeline specialist definitions | Do not install all 55 agents / 182 skills into production. Diff and selectively port a small set into existing `.agents/skills` / `.claude/skills`, rewritten against Melodia authorities. Source: https://github.com/bullish0x/GameStudio |
| 7 | **JTCHE/houdini-mcp** | Houdini node/geometry inspection and edit, HDA, cook/render/PDG, viewport capture, Python/HScript/VEX, offline docs; can start headless Hython | Gives a Houdini specialist actual perception + execution around the existing Hython/Copernicus forge | Canary on a **copy** of an existing cymatics network: inspect → modify → cook → capture → export → report. Never let it make Houdini the runtime world authority. Source: https://github.com/JTCHE/houdini-mcp |
| 8 | **johnsabath/touchdesigner-mcp** | Optional TD MCP surface for Python execution, OP inspection, DAT access and visual capture | **Belongs in the separate `fromage3900/MelodiaTouchDesigner` repo**, where Embody/Envoy is already PRESENT and is the canonical TD-side control/orchestration surface. This candidate is only an adapter/inspection experiment if it adds a capability Embody does not already cover. | **Do not install or vendor TD tooling into this game repo.** Evaluate it only in `MelodiaTouchDesigner`, against copied/test TD content first. Preserve that repo's Embody/Envoy + OSC/Spout contracts; the game repo owns only the integration boundary. Source: https://github.com/johnsabath/touchdesigner-mcp |
| 9 | **Microsoft Agent Framework Harness** | Batteries-included harness with loop, planning/todos, state/context, approvals, background agents, shell/filesystem tools and telemetry | Heavier alternative to Pi for a durable multi-agent Melodia Mission Control | Prototype outside production repo first. Judge it on orchestration/evidence value, not feature count. Do not duplicate CURRENT_STATE, task authority, or existing model router. Sources: https://learn.microsoft.com/agent-framework/agents/harness and https://devblogs.microsoft.com/agent-framework/the-microsoft-agent-framework-harness-is-now-released/ |
| 10 | **OpenAI Codex App Server** | Exposes the Codex harness as an embeddable service / protocol surface with persistent agent threads, tool events and approvals | Candidate Codex worker backend beneath Jev/orchestrator instead of treating a Codex UI session as the architecture | Use as a worker interface, not another project authority. Validate one bounded repo task and one resumable handoff before deeper integration. Source: https://openai.com/index/unlocking-the-codex-harness/ |
| 11 | **Claude Managed Agents** | Stateful/versioned agents with tools, MCP servers, skills, persistent sessions, sandbox environments and multiagent coordinator declarations | Candidate cloud specialist fleet for expensive planning/review lanes while local DCC execution remains machine-side | Beta surface. Start with read-only planner/reviewer agents; secrets stay in vault/auth surfaces, never Git. Do not let cloud sessions directly compete with the one-editor writer rule. Source: https://platform.claude.com/docs/en/managed-agents/overview |
| 12 | **goose (AAIF)** | Local open-source agent with CLI/Desktop/API, 70+ MCP extensions, provider choice, recipes, subagents, permissions/sandboxing and ACP support | Excellent interoperability canary: can Melodia package a reusable mission recipe that runs against different model providers? | Test a **read-only Melodia audit recipe** first. If adopted, recipes describe jobs; they do not supersede AGENTS.md, CURRENT_STATE.md or the Production Playbook. Source: https://block.github.io/goose/ |

### The intended Melodia shape

```text
owner intent
    ↓
Jev / high-reasoning planner
    ↓ typed mission + acceptance criteria
orchestrator runtime (Pi+Muselinn OR MAF; benchmark before choosing)
    ├── repo/code worker       (Codex / Claude / Qwen / Grok / local)
    ├── Houdini specialist     (Hython + optional Houdini MCP)
    ├── TouchDesigner worker   (optional TD MCP)
    ├── web / Three.js worker  (existing website lane)
    └── verifier/reviewer      (independent model where useful)
             ↓
capability surfaces
    ├── Git / shell / Rider / Qodana
    ├── World Compiler + existing Python/Hython tools
    └── ONE serialized Unreal mutation owner per transaction
             ↓
existing Melodia evidence gates / ledger / CURRENT_STATE
```

**Key rule:** parallelize **thinking, inspection, generation and verification**. Serialize **stateful DCC/editor
mutation** when the target cannot safely accept concurrent writes. In Unreal, Epic explicitly documents MCP
tool execution on the game thread as serial; Melodia's stronger local rule still wins: one editor and one
chosen writer owns a mutation transaction.

### Install/test ladder — yes, all twelve, but in waves

**Wave A — low-blast-radius harnesses / continuity:** Pi → pi-muselinn-harness → Agent Harness v10 →
goose. Success means the same bounded repo-safe mission can be planned, delegated, resumed and accepted
without creating a second project-status authority.

**Wave B — specialist capability surfaces:** Epic Unreal MCP → unreal-agent-harness patterns →
Houdini MCP → TouchDesigner MCP. Success means each DCC can complete **inspect → bounded mutation →
capture/verify → evidence** on sandbox/copied content. No production asset is the first test target.

**Wave C — heavier orchestration / remote worker backends:** GameStudio skill quarry → Microsoft Agent
Framework Harness → Codex App Server → Claude Managed Agents. Success means one useful specialist or
handoff capability survives integration without importing a second architecture, second task ledger, or
second gameplay/world authority.

### Promotion gate

A candidate moves from WATCH toward PRESENT only when all are true:

1. **One named Melodia job is measurably easier or safer** than with the existing stack.
2. It obeys the existing authority graph — especially World Compiler/Hython ownership and one Unreal writer.
3. It produces compact evidence that another agent can verify.
4. Uninstall/rollback is understood.
5. Credentials and machine-local config stay out of Git.
6. The result is recorded against an existing project gate/SSOT rather than creating a parallel status system.

**Default outcome is PARK, not integration.** Twelve experiments are welcome; twelve permanent daemons are not.

---

## 9. Anti-duplication checklist (read before proposing)

1. Is the system in §1 (PRESENT)? Extend it, don't rebuild. Especially: audio writer (single), music clock.
2. Is it in §2 (SCAFFOLDED)? Finish it before starting a parallel copy.
3. Is it in §3 (WATCH)? Requires an explicit owner task to promote.
4. Is it §4 (external)? You cannot build it natively; say so, don't fake it.
5. Is the field-name you want already in §5 (World Field Bus / SpeedTree bridge)? Reuse the contract.
6. Editor: one instance, one :9316. Batch saves `unattended:true`. No `Content/_PROJECT/` writes.
7. Evidence: offline probe + live PIE + ledger row. Prose is not a row.

## 8b. Specialist model fleet trench sweep — 2026-09-23

**Status:** RESEARCH / SETUP CANDIDATES. None of the entries below become PRESENT or production-routed by appearing here.

Durable setup plan:
`Docs/Plans/HERMES_SPECIALIST_MODEL_FLEET_SETUP_2026-09-23.md`

Machine-readable candidate registry:
`specs/orchestration/hermes_specialist_fleet.candidates.v1.json`

First-party-verified candidate families:

| Candidate | Research role | Integration shape | Status |
|---|---|---|---|
| Muse Spark 1.3 | long-context planner/reviewer, multimodal review | Meta Model API / Muse Code | RESEARCH |
| Muse Code 1.2.1 | MCP-aware coding worker | WSL CLI on Windows | RESEARCH |
| Muse Glimmer | local persistent observer | local open-weight model | WATCH |
| Muse Voice Transcribe | critique / spoken-note ingestion | speech specialist | WATCH |
| Muse Realtime Avatar | character-presence lab | realtime avatar specialist | WATCH |
| MiMo V2.6 Pro | general agent challenger | OpenAI/Anthropic-compatible API; first-party Hermes guide | RESEARCH — priority |
| MiMo V2.6 Pro UltraSpeed | latency / fast subagent canary | same MiMo API family | RESEARCH |
| Step 5 Preview | frontier planner challenger | StepFun OpenAI-compatible API | RESEARCH |
| SWE-2 | coding implementation specialist | Devin Desktop/CLI | RESEARCH |
| Qwen3.8-Omni-Flash | gameplay/video/audio inspection | multimodal API | RESEARCH |
| HappyOyster Adventure / Directing / Acting | walkable world ideation / previs | QwenCloud world-model APIs | RESEARCH — specialist |
| Qwen-Image-2.1 | transparent filigree / alpha / decal ideation | image specialist | WATCH |
| Fugu Max / Ultra v2 | orchestration-vs-Hermes comparison | vendor orchestration surface | WATCH |
| Mercury 2.5 | high-frequency low-latency subagent | OpenAI-compatible API | RESEARCH |

Promotion rule: **benchmark first, route second**. A successful connectivity probe is not evidence of Melodia fit.

Do not:
- replace Hermes with Fugu from a single demo;
- replace Jev with a low-latency model;
- let HappyOyster write canonical World Genome / UE state;
- treat SWE-2 as a generic HTTP model unless Cognition documents that access;
- hard-code Step 5's model id before the current API exposes/confirms it;
- store provider keys in Git;
- add every candidate as a permanent daemon.

Default outcome remains **PARK or SPECIALIST**, not fleet inflation.


---

## 9. Procedural worldbuilding research delta — 2026-09-25

**Latest detailed sweep:** [EMERGING_3D_TOOLCHAIN_TRENCH_SWEEP_05_2026-09-25.md](EMERGING_3D_TOOLCHAIN_TRENCH_SWEEP_05_2026-09-25.md)

This sweep was performed against current Git state rather than generic tool availability.

### Baseline now considered solved / present

- UE 5.8 PCG Python semantic enrichment;
- `Resonance / EcologyClass / MaterialVariant / ScaleBias` metadata production;
- native spawner + per-instance custom-data material response;
- World Compiler procedural ecology/presentation in `L_MelusinaMorning`;
- canonical Houdini/Hython offline forge;
- Copernicus batch texture/mask generation;
- Gaea/DEM -> metric source -> UE 5.8 Mesh Terrain P0 path.

Do **not** return these as new-tech recommendations without a materially different capability.

### Current research priority

| Candidate | Status | Why it survives the repo-aware filter |
|---|---|---|
| **UE 5.8 PCG Manual Editing / Data Overrides** | **TEST NOW / Experimental** | Adds non-destructive artist override over generated PCG; targets the procedural-vs-authored composition problem rather than adding another generator |
| **Houdini 22 COP HDA in Unreal** | **TEST NOW** | Could collapse texture lookdev round-trip while keeping existing Melodia material authority and Hython batch lane |
| **Local-statistics texture synthesis / filtering** | **TEST SOON** | Targets large-surface repetition beyond current triplanar/randomization controls |
| **Iso-contour terrain authoring** | **TEST SOON** | Artist-first macro-composition representation that can feed the existing terrain handoff rather than replacing it |
| **Stochastic geomorphological transport** | **OFFLINE R&D** | Potentially richer flow/deposition masks for existing Gaea/Hython/PCG consumers |
| **InfiniteDiffusion / Terrain Diffusion** | **RESEARCH ONLY** | Deterministic unbounded learned terrain is strategically interesting, but must remain an offline source/ideation sidecar |
| **Richer procedural material data enhancement** | **PATTERN QUARRY** | Use layered physical-prior ideas; do not add a neural material runtime |
| **GPU PCG / Custom HLSL** | **BENCHMARK WHEN PROFILED** | Existing PCG contract already reserves this for dense/Python-bound graphs; no new architecture needed |

### Production constraint

`Docs/P1_TASK_LEDGER.json` currently parks broad procedural-system expansion. The table above is an R&D queue only. Any implementation should be a disposable or bounded canary that consumes existing World Compiler / PCG / Hython / material owners.


---

## 10. Procedural worldbuilding / material research delta — 2026-10-02

**Latest detailed sweep:** [EMERGING_3D_TOOLCHAIN_TRENCH_SWEEP_06_2026-10-02.md](EMERGING_3D_TOOLCHAIN_TRENCH_SWEEP_06_2026-10-02.md)

This is a delta over Sweep 05, verified against `main` @ `46ac21dd6`.

### Current production boundary

`Docs/P1_TASK_LEDGER.json` now records:

- `procedural_system_policy = BOUNDED_OWNER_APPROVED_SCHOOL_GATES`;
- owner-approved procedural scope is limited to the named P0 Sea Above FieldAtlas tile, Faraway Mother resonance-field integration, and Gate 6 Glitter Pile;
- general PCG / World Compiler / Universe Foundry / FieldAtlas architecture expansion remains disallowed.

The items below are therefore R&D canaries, not active production tasks.

### Delta

| Candidate | 2026-10-02 status | What changed |
|---|---|---|
| **GPU PCG + Custom HLSL** | **TEST NOW — benchmark only** | Promote from passive scale gate to one measured Resonance canary; Epic's UE5.8 GPU PCG path includes Compute Graphs, Custom HLSL Point Processor and GPU Static Mesh Spawner. Preserve CPU semantic authority. |
| **Python -> COP HDA -> Unreal** | **TEST NOW — refined** | SideFX's 2026 SciFi Panel example proves a useful pattern: Python authors sparse 2D structure, Copernicus develops height/detail/color, Houdini Engine carries it to Unreal. Test with one Melodia semantic surface. |
| **Local-statistics texture synthesis** | **TEST SOON** | Retained as the strongest anti-tiling paper for large patterned surfaces; prototype as an isolated material function before considering fuller implementation. |
| **Iso-contour terrain authoring** | **TEST SOON** | Retained as an artist-first terrain input representation feeding the existing handoff, not a new terrain system. |
| **Physics-inspired deformable-surface texturing** | **TEST SOON / NEW** | SIGGRAPH 2026 wave-based procedural texturing is relevant to cloth terrain, membranes, sludge and extreme magical deformation without stored simulation history. |

### Recommended canary order

1. `PCG_GPU_Resonance_Canary`
2. `COPHDA_MelodiaSemanticSurface_Canary`
3. `MF_LocalStatsBreakup_Prototype`
4. `IsoContour_TerrainAuthoring_Canary`
5. `MF_DeformationAwareSurface_Canary`

Do not reopen stochastic erosion, InfiniteDiffusion, neural-material runtime work, or general procedural architecture without a named blocker.
