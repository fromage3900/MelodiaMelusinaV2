# Melodia — Gameplay Vertical Slice + Environment Art Platform

```
✧ ┊ ⋆ ┊ . ┊ ┊┊ ┊⋆ ┊ .┊ ┊ ⋆˚  ✧  ┊ ┊ ⋆ ┊ . ┊ ┊┊ ┊⋆ ┊ .┊ ┊ ⋆˚  ✧
```

![Build](https://img.shields.io/github/actions/workflow/status/fromage3900/MelodiaMelusinaV2/unreal_build.yml?branch=main&label=UE%20build)
![Echo Gates](https://img.shields.io/github/actions/workflow/status/fromage3900/MelodiaMelusinaV2/echo_gates.yml?branch=main&label=Echo%20static%20gates)
![Release](https://img.shields.io/github/v/release/fromage3900/MelodiaMelusinaV2?label=release)

UE 5.8 + Blender 5.2 production project with two active tracks:

1. **Gameplay vertical slice ("First Dream")** — a compact Persona-lite JRPG loop: QuillScript dialogue, stock JRPG combat, rhythm-combat (Harmonix), canonical save/load, travel/input authorities, a Melody Token economy, and co-op skills.
2. **Environment-art platform** — real-time Blender↔Unreal level design bridge, procedural geometry generation, automatic material crosswalk, and a portfolio capture/publish pipeline.

```
 ◇─◇──◇──◇─◇
```

> **New here?** [QUICKSTART.md](QUICKSTART.md) — 5 minutes to first demo.
>
> **Gameplay scope?** [_VERTICAL_SLICE_SCOPE.md](_VERTICAL_SLICE_SCOPE.md) — current scope authority.
>
> **Most recent session?** [_SESSION_HANDOFF.md](_SESSION_HANDOFF.md) — read fresh every time.
>
> **Tonight’s cloud prep?** [Docs/Handoffs/CLOUD_AGENT_GIT_HEALTH_2026-08-12.md](Docs/Handoffs/CLOUD_AGENT_GIT_HEALTH_2026-08-12.md) — git health + RestoreParty PRs, merge order for the PC.
>
> **Phone / cloud queue?** [Docs/PhoneOps/BACKLOG.md](Docs/PhoneOps/BACKLOG.md) — Now/Next for Cursor iOS + cloud agents.
>
> **Live task tracker?** [_TASK_QUEUE.md](_TASK_QUEUE.md) — P0/P1/P2/P3, per-task status/agent.
>
> **Architecture overview?** [PIPELINE.md](PIPELINE.md) — full system map.
>
> **Machine setup?** [Docs/ENVIRONMENT_RUNBOOK_2026-08-11.md](Docs/ENVIRONMENT_RUNBOOK_2026-08-11.md) — portable Windows environment.
>
> **Repo status (2026-08-12):** Private V2 at `https://github.com/fromage3900/MelodiaMelusinaV2`. `main` protected (PR + linear history); self-hosted runner `melodia-v2-win`. Production UE worktree on PC: `C:\EnvironmentPortfolio\BS_GodFile` (same remote). Cloud/phone agents use this GitHub clone — not a live editor. LFS is metered — see [Docs/GIT_BATCH_DISCIPLINE.md](Docs/GIT_BATCH_DISCIPLINE.md). Ready PRs for tomorrow: **#4** (git health / LFS gate / untrack junk), **#6** (slim `RestorePartyAfterBattle` call site).

```
 ◇─◇──◇──◇─◇
```

---

## 🎮 Primary Track: First Dream Vertical Slice

> **Status (2026-08-12 evening):** `static_gates` **PASS**. `runtime` still **OPEN/FAIL** until real-input ledger. Playable levels now tracked on `main`. RestoreParty on **PR #6** (rebased, not merged). Owner: Quill/WillScript updated (verify owed); P0 battles still broken on dreamstate/collider paths; rhythm highway unverified. Board: [PIE_RUNTIME_NOTES_2026-08-12.md](Docs/Handoffs/PIE_RUNTIME_NOTES_2026-08-12.md).

### The loop

```text
sanctuary conversation
  -> authored departure
  -> short dream traversal
  -> one stock JRPG encounter
  -> typed terminal result
  -> narrative consequence
  -> stable checkpoint/save
```

### Playable route (target)

`L_MelusinaMorning` → dream traversal → `L_KaleidoNave` (boss / stock rhythm encounter)

Real paths:
- `/Game/Melodia/Levels/Opening/L_MelusinaMorning`
- `/Game/EnvSandbox/Environments/L_KaleidoNave` (includes merged dreamstate content; old `L_Melodia_Dreamstate` allowlist entry stripped — backup under `Saved/Recovery/`)

### Tomorrow on the PC (after merging #4 + #6)

1. Pull `main` on `C:\EnvironmentPortfolio\BS_GodFile` — **one** UnrealEditor + Monolith `:9316`
2. Full closed-editor build → PIE: highway survives both HUD writers; battle-end logs `MELODIA_RECOVERY…`
3. `python Tools/playtest_harness.py` with real keys → assertion JSON beside frames → `record_gate.py runtime pass|fail`

### Core systems

| System | What it is |
|--------|-----------|
| **QuillScript dialogue** | Narrative authority; NPC interaction + typed terminal results |
| **Stock JRPG combat** | Turn/target/damage/result authority (TurnBasedJRPGTemplate) |
| **Rhythm combat** | Harmonix music clock + `UMelodiaRhythmCombatSubsystem`; optional, not mandatory |
| **Canonical save/load** | `BP_JRPGSaveGame` slot across process restart |
| **Travel authority** | `UMelodiaTravelSubsystem` — single travel path with allowlist validation |
| **Input authority** | `UMelodiaInputContextSubsystem` — push/pop context stack |
| **Melody Token economy** | `UMelodiaTokenWalletSubsystem` — pickups + HUD |
| **Co-op skills** | Petal Cadence, Skybound Refrain, Resonance (stock authority) |

### Where to start reading

- [_VERTICAL_SLICE_SCOPE.md](_VERTICAL_SLICE_SCOPE.md) — current scope authority
- [_SESSION_HANDOFF.md](_SESSION_HANDOFF.md) — most recent session state
- [_TASK_QUEUE.md](_TASK_QUEUE.md) — live task tracker
- [_DECISION_LOG.md](_DECISION_LOG.md) — append-only strategic decisions
- [Docs/BLUEPRINT_WIRING_CONTRACT_2026-08-07.md](Docs/BLUEPRINT_WIRING_CONTRACT_2026-08-07.md) — canonical wiring source of truth

---

## 🏗️ Secondary Track: Environment Art Platform

UE 5.8 + Blender 5.2 production platform for stylized portfolio work: real-time Blender↔Unreal level design bridge, procedural geometry generation, automatic material crosswalk, and a portfolio capture/publish pipeline.

### Onboarding paths

| Path | Time | What You'll Do | For |
|------|------|----------------|-----|
| **Viewer** | 5 min | Open & explore levels | Reviewers, new team members |
| **Geometry** | 10 min | Build & send assets to UE | Level designers, environment artists |
| **Materials** | 15 min | Create & preview materials | Technical artists, shader folks |
| **Full Collaborator** | 30 min | Complete live workflow | Active contributors |

Run setup check: `.\deploy\validate_collaborator_setup.sh`

### Port map

| Port | Service | Direction |
|------|---------|-----------|
| `9876` | LiveLink — FBX/texture/animation stream | Blender → UE |
| `9316` | UE Monolith MCP — Python execution | Any → UE |
| `9317` | Blender MCP — genome/agent control | Any → Blender |
| `50021` | VOICEVOX — TTS (7 characters) | Any → VOICEVOX |
| `50022` | Melusina Voice — custom SBV2 | Any → Melusina |

### Troubleshooting

| Problem | Fix |
|---------|-----|
| Port 9876 "in use" | Close extra Blender instances (Task Manager) |
| Materials gray in UE | `resolve_material_crosswalk.resolve_all()` |
| Speaker not found | VOICEVOX Settings -> Manage Voice Libraries -> download |
| PIE crash | Rebuild MelodiaCore (.dll) |

### Key scripts

| Script | Does | Where |
|--------|------|-------|
| `Tools/setup_zunzun_studio.py` | Import ZunZun models + studio layout | Blender |
| `Tools/generate_all_voices.py` | Batch-generate 102 NPC voice WAVs | Terminal |
| `Content/Python/import_zundamon.py` | Import Zundamon FBX + materials | UE |
| `Content/Python/create_zunzun_bps.py` | Auto-create 7 NPC BPs + quests/shop/party | UE |
| `Content/Python/resolve_material_crosswalk.py` | Post-import material auto-resolver | UE |
| `deploy/bootstrap_environment.ps1` | Opt-in Python/website environment bootstrap | Terminal |

### Two-designer workflow

| Role | Tool | Responsibility |
|------|------|---------------|
| **Geometry Designer** | Blender | Procedural gen, mesh editing, materials, live sync |
| **Level Scripter** | Unreal | Blueprints, encounters, lighting, PCG scatter, NPCs |

Live sync ON -> Designer tweaks -> UE auto-updates -> Scripter places gameplay.

Full guide: [Docs/SETUP_COLLAB.md](Docs/SETUP_COLLAB.md)

```
◇──◇──◇──◇─◇
```

---

## Documentation

```
◇─── Docs ───◇
```

**Gameplay (read these first):**
- [_VERTICAL_SLICE_SCOPE.md](_VERTICAL_SLICE_SCOPE.md) — current scope authority
- [_SESSION_HANDOFF.md](_SESSION_HANDOFF.md) — most recent session state
- [Docs/Handoffs/CLOUD_AGENT_GIT_HEALTH_2026-08-12.md](Docs/Handoffs/CLOUD_AGENT_GIT_HEALTH_2026-08-12.md) — 2026-08-12 cloud git-health prep
- [Docs/PhoneOps/INDEX.md](Docs/PhoneOps/INDEX.md) — phone / Cursor iOS entry
- [_TASK_QUEUE.md](_TASK_QUEUE.md) — live task tracker
- [_DECISION_LOG.md](_DECISION_LOG.md) — append-only strategic decisions
- [DOC_INDEX.md](DOC_INDEX.md) — complete documentation map

**Getting started (environment-art):**
- [QUICKSTART.md](QUICKSTART.md) — 5-minute setup
- [PIPELINE.md](PIPELINE.md) — unified pipeline architecture
- [CURRENT_STATE.md](CURRENT_STATE.md) — system readiness

**Workflows:**
- [UNIVERSAL_ENVIRONMENT_PIPELINE.md](UNIVERSAL_ENVIRONMENT_PIPELINE.md) — production flow
- [MATERIAL_LOOKDEV_PIPELINE.md](MATERIAL_LOOKDEV_PIPELINE.md) — material & look-dev
- [AGENT_OPERATING_MODEL.md](AGENT_OPERATING_MODEL.md) — agent roles & safety

**Collaboration:**
- [Docs/SETUP_COLLAB.md](Docs/SETUP_COLLAB.md) — lightweight collab setup (50 MB)
- [COLLABORATOR_SETUP.md](COLLABORATOR_SETUP.md) — tiered onboarding
- [Docs/LEVEL_DESIGNER_ONBOARDING.md](Docs/LEVEL_DESIGNER_ONBOARDING.md) — level design workflow
- [Docs/COLLABORATION_WORKFLOW.md](Docs/COLLABORATION_WORKFLOW.md) — Git/LFS handoff rules

**Status:**
- [PORTFOLIO_READINESS.md](PORTFOLIO_READINESS.md) — readiness checklist

```
◇──◇──◇──◇─◇
```

---

## Systems

```
◇─── Systems ───◇
```

**Materials:** [PIPELINE](MATERIAL_PIPELINE.md) / [Review](MATERIAL_SYSTEM_REVIEW.md) / [Integration](Docs/MATERIAL_INTEGRATION.md) / [Node Tree](Docs/MATERIAL_NODE_TREE_REVIEW.md)

**Portfolio:** [Portfolio Pipeline](PORTFOLIO_PIPELINE.md) / [Audit](PORTFOLIO_PIPELINE_AUDIT.md) / [Readiness](PORTFOLIO_READINESS.md)

**Agents:** [Framework](AGENTS.md) / [Boundaries](AGENT_BOUNDARIES.md) / [Ownership](AGENT_OWNERSHIP.md)

**Pipeline:**
```
Material/PCG/world systems
  -> L_Template or neutral test map validation
  -> Saved/Portfolio render and metadata fragments
  -> renders_manifest.json
  -> portfolio_package.json
  -> website / Figma / ArtStation handoff
```

**Agent loops:**
```powershell
.\deploy\start_cursor_agent_loop.ps1   # Agent loop
.\deploy\start_surreal_loop.ps1        # Architecture loop
.\deploy\start_surreal_tierb_loop.ps1  # Tier-B loop
.\deploy\start_world_loop.ps1          # World loop
.\deploy\start_td_loop.ps1             # TouchDesigner loop
.\deploy\start_hermes_daemon.ps1       # Meta/orchestrator
.\deploy\start_ollama_fleet.ps1        # AI voice fleet
.\deploy\status.ps1                    # Live dashboard (PID/state per loop)
```
Blender-side (4): surreal_micro10, surreal_micro2, surreal_tierb, world_micro10
UE Python (6): material_aaa, master_texture, portfolio_orch, specialist_pcg, specialist_terrain, sdf_factory
Meta (1): recursive_learner

**SDF Material Catalog:** 32 Substrate Toon instances across Cathedral/Gothic (8), Cosmo (6), Landscape (6), Stylized (6), Base (5). 6 drop-in ready, 16 adaptable. [Scorecard](NEXT_HIGHEST_LEVERAGE_TASK.md)

```
◇──◇──◇──◇─◇
```

```
✧ ┊ ⋆ ┊ . ┊ ┊┊ ┊⋆ ┊ .┊ ┊ ⋆˚  ✧  ┊ ┊ ⋆ ┊ . ┊ ┊┊ ┊⋆ ┊ .┊ ┊ ⋆˚  ✧
```

**Boundary:** Do not automate final Sakura level art direction. `L_SakuraPath` is human-owned.
