# Melodia â€” Gameplay Vertical Slice + Environment Art Platform

```
âœ§ â”Š â‹† â”Š . â”Š â”Šâ”Š â”Šâ‹† â”Š .â”Š â”Š â‹†Ëš  âœ§  â”Š â”Š â‹† â”Š . â”Š â”Šâ”Š â”Šâ‹† â”Š .â”Š â”Š â‹†Ëš  âœ§
```

![Build](https://img.shields.io/github/actions/workflow/status/fromage3900/MelodiaMelusinaV2/unreal_build.yml?branch=main&label=UE%20build)
![Echo Gates](https://img.shields.io/github/actions/workflow/status/fromage3900/MelodiaMelusinaV2/echo_gates.yml?branch=main&label=Echo%20static%20gates)
![Release](https://img.shields.io/github/v/release/fromage3900/MelodiaMelusinaV2?label=release)

UE 5.8 + Blender 5.2 production project with two active tracks:

1. **Gameplay vertical slice ("First Dream")** â€” a compact Persona-lite JRPG loop: QuillScript dialogue, stock JRPG combat, rhythm-combat (Harmonix), canonical save/load, travel/input authorities, a Melody Token economy, and co-op skills.
2. **Environment-art platform** â€” real-time Blenderâ†”Unreal level design bridge, procedural geometry generation, automatic material crosswalk, and a portfolio capture/publish pipeline.

```
 â—‡â”€â—‡â”€â”€â—‡â”€â”€â—‡â”€â—‡
```

> **Blender / Melodia Studio?** [Docs/BLENDER_MELODIA_COCKPIT.md](Docs/BLENDER_MELODIA_COCKPIT.md) â€” v22 stage, MCP **9876**, Health `12/12` / `165`.
>
> **Gameplay scope?** [_VERTICAL_SLICE_SCOPE.md](_VERTICAL_SLICE_SCOPE.md) â€” current scope authority.
>
> **Most recent session?** [_SESSION_HANDOFF.md](_SESSION_HANDOFF.md) â€” read fresh every time.
>
> **Tonightâ€™s cloud prep?** [Docs/Handoffs/CLOUD_AGENT_GIT_HEALTH_2026-08-12.md](Docs/Handoffs/CLOUD_AGENT_GIT_HEALTH_2026-08-12.md) â€” git health + RestoreParty PRs, merge order for the PC.
>
> **Phone / cloud queue?** [Docs/PhoneOps/BACKLOG.md](Docs/PhoneOps/BACKLOG.md) â€” Now/Next for Cursor iOS + cloud agents.
>
> **Parallel agents tonight?** [PARALLEL_LANESâ€¦](Docs/Handoffs/PARALLEL_LANES_2026-08-12.md) Â· [paste sessionsâ€¦](Docs/Handoffs/PARALLEL_SESSIONS_2026-08-12.md).
>
> **Live task tracker?** [_TASK_QUEUE.md](_TASK_QUEUE.md) â€” P0/P1/P2/P3, per-task status/agent.
>
> **Architecture overview?** [PIPELINE.md](PIPELINE.md) â€” full system map.
>
> **Machine setup?** [Docs/ENVIRONMENT_RUNBOOK_2026-08-11.md](Docs/ENVIRONMENT_RUNBOOK_2026-08-11.md) â€” portable Windows environment.
>
> **Source control (2026-08-13):** See [SOURCE_CONTROL_STATUS_2026-08-13.md](Docs/Handoffs/SOURCE_CONTROL_STATUS_2026-08-13.md) for the authoritative multi-repo checkpoint.
>
> **Unreal repo â€” the source of truth:** `https://github.com/fromage3900/MelodiaMelusinaV2`, remote name **`origin`**. The older `MelodiaMelusina` repo is remote `legacy-melodia` and is **not** current; do not clone, push, or merge it. For live branch/commit state see [SOURCE_CONTROL_STATUS_2026-08-13.md](Docs/Handoffs/SOURCE_CONTROL_STATUS_2026-08-13.md) â€” a commit SHA pinned in this README goes stale the same day. LFS is metered â€” see [Docs/GIT_BATCH_DISCIPLINE.md](Docs/GIT_BATCH_DISCIPLINE.md). GitHub connectivity from this workstation is **intermittent**; a failed push is usually the network, so retry before diagnosing.
>
> **Website repo:** `C:\EnvironmentPortfolio\my-site-clean` has local tip `3cfa5f0`, but its configured remote has unrelated history and remains intentionally unsynchronized. Do not force-push or merge unrelated histories.
>
> **RHYTHM + QUILL WORKED (owner locks):** [RHYTHMâ€¦](Docs/Handoffs/RHYTHM_GAME_LOCKED_2026-08-12.md) Â· [QUILLâ€¦](Docs/Handoffs/QUILLSCRIPT_LOCKED_2026-08-12.md) â€” tell the family; do not reopen highway or Quill as unverified.

```
 â—‡â”€â—‡â”€â”€â—‡â”€â”€â—‡â”€â—‡
```

---

## ðŸŽ® Primary Track: First Dream Vertical Slice

> **Status (2026-08-13):** `static_gates` **PASS**. **Rhythm WORKED** Â· **QuillScript WORKED** (owner locks). **`runtime` gate CLOSED** â€” owner verified real keyboard input through `BP_BattleUI::OnKeyDown`; ledger row `[PASS] runtime 2026-08-13`. Remaining completion gates: **`save_load`**, **`repeat_consume`**, **`package_launch`**. Board: [PIEâ€¦](Docs/Handoffs/PIE_RUNTIME_NOTES_2026-08-12.md) Â· [RHYTHMâ€¦](Docs/Handoffs/RHYTHM_GAME_LOCKED_2026-08-12.md) Â· [QUILLâ€¦](Docs/Handoffs/QUILLSCRIPT_LOCKED_2026-08-12.md).

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

`L_MelusinaMorning` â†’ dream traversal â†’ `L_KaleidoNave` (boss / stock rhythm encounter)

Real paths:
- `/Game/Melodia/Levels/Opening/L_MelusinaMorning`
- `/Game/EnvSandbox/Environments/L_KaleidoNave` (includes merged dreamstate content; old `L_Melodia_Dreamstate` allowlist entry stripped â€” backup under `Saved/Recovery/`)

### Next on the PC (post rhythm lock)

1. ~~Pull + closed-editor build + rhythm highway~~ **DONE â€” owner confirmed rhythm game WORKED**
2. ~~WillScript / QuillScript~~ **DONE â€” owner confirmed WORKED**
3. ~~Real-key runtime gate~~ **DONE 2026-08-13 â€” owner verified; `[PASS] runtime 2026-08-13`**
4. `save_load` â€” canonical `BP_JRPGSaveGame` slot survives a full process restart
5. `repeat_consume` â€” flag + reward restore without duplication; `melodia:stat:` idempotent per IntentId
6. `package_launch` â€” Development build launches and plays the route outside the editor

### Core systems

| System | What it is |
|--------|-----------|
| **QuillScript dialogue** | Narrative authority â€” **OWNER LOCK 2026-08-12: WORKED in PIE** |
| **Stock JRPG combat** | Turn/target/damage/result authority (TurnBasedJRPGTemplate) |
| **Rhythm combat** | Harmonix music clock + `UMelodiaRhythmCombatSubsystem` â€” **OWNER LOCK 2026-08-12: WORKED in PIE** |
| **Canonical save/load** | `BP_JRPGSaveGame` slot across process restart |
| **Travel authority** | `UMelodiaTravelSubsystem` â€” single travel path with allowlist validation |
| **Input authority** | `UMelodiaInputContextSubsystem` â€” push/pop context stack |
| **Melody Token economy** | `UMelodiaTokenWalletSubsystem` â€” pickups + HUD |
| **Co-op skills** | Petal Cadence, Skybound Refrain, Resonance (stock authority) |

### Where to start reading

- [_VERTICAL_SLICE_SCOPE.md](_VERTICAL_SLICE_SCOPE.md) â€” current scope authority
- [_SESSION_HANDOFF.md](_SESSION_HANDOFF.md) â€” most recent session state
- [_TASK_QUEUE.md](_TASK_QUEUE.md) â€” live task tracker
- [_DECISION_LOG.md](_DECISION_LOG.md) â€” append-only strategic decisions
- [Docs/BLUEPRINT_WIRING_CONTRACT_2026-08-07.md](Docs/BLUEPRINT_WIRING_CONTRACT_2026-08-07.md) â€” canonical wiring source of truth

---

## ðŸ—ï¸ Secondary Track: Environment Art Platform

UE 5.8 + Blender 5.2 production platform for stylized portfolio work: real-time Blenderâ†”Unreal level design bridge, procedural geometry generation, automatic material crosswalk, and a portfolio capture/publish pipeline.

### Onboarding paths

| Path | Time | What You'll Do | For |
|------|------|----------------|-----|
| **Viewer** | 5 min | Open & explore levels | Reviewers, new team members |
| **Geometry** | 10 min | Build & send assets to UE | Level designers, environment artists |
| **Materials** | 15 min | Create & preview materials | Technical artists, shader folks |
| **Full Collaborator** | 30 min | Complete live workflow | Active contributors |

### Clone and validate

```powershell
git clone https://github.com/fromage3900/MelodiaMelusinaV2.git MelodiaMelusinaV2
cd MelodiaMelusinaV2
git config core.hooksPath .githooks
powershell -ExecutionPolicy Bypass -File .\deploy\validate_setup.ps1
```

Note the explicit clone target and the `core.hooksPath` line â€” a fresh clone does
**not** enable the repo's hooks on its own, so the LFS budget gate and the
binary-hygiene pre-commit check are inert until you set it.

`deploy/validate_setup.ps1` is the Windows validator. The two `.sh` scripts in
`deploy/` require **Git Bash** (bash 4+) and are not runnable from PowerShell.

**Read [COLLABORATOR_SETUP.md](COLLABORATOR_SETUP.md) before expecting a level to
open.** Bulk environment art (~4.6 GB) is deliberately *not* in this repository â€”
`L_KaleidoNave` will load with missing references on a fresh clone. That is expected,
not a broken checkout, and no `git lfs pull` will fix it. Ask the owner for the art
drop.

### Port map

| Port | Service | Direction |
|------|---------|-----------|
| `9876` | **BlenderMCP** (agent â†” open 5.2 GUI) **and** LiveLink TCP â€” do not run both | See [cockpit](Docs/BLENDER_MELODIA_COCKPIT.md) |
| `9316` | UE Monolith MCP â€” Python execution | Any â†’ UE |
| `9317` | Legacy Blender HTTP claims â€” **not** the live GUI MCP | Do not use |
| `50021` | VOICEVOX â€” TTS (7 characters) | Any â†’ VOICEVOX |
| `50022` | Melusina Voice â€” custom SBV2 | Any â†’ Melusina |

### Troubleshooting

| Problem | Fix |
|---------|-----|
| Port 9876 "in use" | Close extra Blender **or** stop LiveLink if you need BlenderMCP (same port) |
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

**What "live" does and does not mean.** This project has **no Unreal Multi-User
Editing / Concert / Switchboard** â€” none is present in `BS_GodFile.uproject` or
`Config/`. "Live" here is a Blenderâ†’Unreal *asset streaming* bridge (LiveLink,
port 9876). **Two people cannot co-edit the same level.** The workflow above is one
person in Blender and one in Unreal, working on *different files*.

Concurrency is enforced socially plus by **Git LFS file locking**. `.gitattributes`
marks 2,224 files `lockable`, which means LFS checks them out **read-only** â€” if
Unreal or Blender says a `.uasset`/`.umap` is read-only, that is the lock system, not
corruption. Take the lock before you edit, release it when you push:

```bash
git lfs lock   Content/EnvSandbox/Environments/L_KaleidoNave.umap
git lfs locks                      # see who holds what
git lfs unlock Content/EnvSandbox/Environments/L_KaleidoNave.umap
```

Full guide: [Docs/SETUP_COLLAB.md](Docs/SETUP_COLLAB.md) Â· [Docs/COLLABORATION_WORKFLOW.md](Docs/COLLABORATION_WORKFLOW.md)

```
â—‡â”€â”€â—‡â”€â”€â—‡â”€â”€â—‡â”€â—‡
```

---

## Documentation

```
â—‡â”€â”€â”€ Docs â”€â”€â”€â—‡
```

**Gameplay (read these first):**
- [_VERTICAL_SLICE_SCOPE.md](_VERTICAL_SLICE_SCOPE.md) â€” current scope authority
- [_SESSION_HANDOFF.md](_SESSION_HANDOFF.md) â€” most recent session state
- [Docs/Handoffs/CLOUD_AGENT_GIT_HEALTH_2026-08-12.md](Docs/Handoffs/CLOUD_AGENT_GIT_HEALTH_2026-08-12.md) â€” 2026-08-12 cloud git-health prep
- [Docs/PhoneOps/INDEX.md](Docs/PhoneOps/INDEX.md) â€” phone / Cursor iOS entry
- [_TASK_QUEUE.md](_TASK_QUEUE.md) â€” live task tracker
- [_DECISION_LOG.md](_DECISION_LOG.md) â€” append-only strategic decisions
- [DOC_INDEX.md](DOC_INDEX.md) â€” complete documentation map

**Getting started (environment-art):**
- [QUICKSTART.md](QUICKSTART.md) â€” 5-minute setup
- [PIPELINE.md](PIPELINE.md) â€” unified pipeline architecture
- [CURRENT_STATE.md](CURRENT_STATE.md) â€” system readiness

**Workflows:**
- [UNIVERSAL_ENVIRONMENT_PIPELINE.md](Docs/_Superseded/UNIVERSAL_ENVIRONMENT_PIPELINE.md) â€” production flow
- [MATERIAL_LOOKDEV_PIPELINE.md](MATERIAL_LOOKDEV_PIPELINE.md) â€” material & look-dev
- [AGENT_OPERATING_MODEL.md](Docs/_Superseded/AGENT_OPERATING_MODEL.md) â€” agent roles & safety

**Collaboration:**
- [Docs/SETUP_COLLAB.md](Docs/SETUP_COLLAB.md) â€” lightweight collab setup (50 MB)
- [COLLABORATOR_SETUP.md](COLLABORATOR_SETUP.md) â€” tiered onboarding
- [Docs/LEVEL_DESIGNER_ONBOARDING.md](Docs/LEVEL_DESIGNER_ONBOARDING.md) â€” level design workflow
- [Docs/COLLABORATION_WORKFLOW.md](Docs/COLLABORATION_WORKFLOW.md) â€” Git/LFS handoff rules

**Status:**
- [PORTFOLIO_READINESS.md](Docs/_Superseded/PORTFOLIO_READINESS.md) â€” readiness checklist

```
â—‡â”€â”€â—‡â”€â”€â—‡â”€â”€â—‡â”€â—‡
```

---

## Systems

```
â—‡â”€â”€â”€ Systems â”€â”€â”€â—‡
```

**Materials:** [PIPELINE](MATERIAL_PIPELINE.md) / [Review](MATERIAL_SYSTEM_REVIEW.md) / [Integration](Docs/MATERIAL_INTEGRATION.md) / [Node Tree](Docs/MATERIAL_NODE_TREE_REVIEW.md)

**Portfolio:** [Portfolio Pipeline](PORTFOLIO_PIPELINE.md) / [Audit](PORTFOLIO_PIPELINE_AUDIT.md) / [Readiness](Docs/_Superseded/PORTFOLIO_READINESS.md)

**Agents:** [Framework](AGENTS.md) / [Boundaries](Docs/_Superseded/AGENT_BOUNDARIES.md) / [Ownership](Docs/_Superseded/AGENT_OWNERSHIP.md)

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

**SDF Material Catalog:** 32 Substrate Toon instances across Cathedral/Gothic (8), Cosmo (6), Landscape (6), Stylized (6), Base (5). 6 drop-in ready, 16 adaptable. [Scorecard](Docs/_Superseded/NEXT_HIGHEST_LEVERAGE_TASK.md)

```
â—‡â”€â”€â—‡â”€â”€â—‡â”€â”€â—‡â”€â—‡
```

---

## Attributions & Credits

*Melodia* relies on the incredible work of creators spanning the UE/Fab marketplace, the CC0 open-source community, BOOTH.pm, and the owner's own first-party art. We maintain strict provenance tracking for every imported asset — named creator, source link, and license, all recorded.

**Headline thanks:**

- **Epic Games** — *Electric Dreams Environment* sample (river/cave assemblies, ambience audio) and the **Quixel Megascans** library (photogrammetry nature)
- **Everett Gunther** — *Ultra Dynamic Sky* weather/lighting system
- **Joe Garth (Brushify Ltd)** — *Brushify – Floating Islands* kits
- **Coreb Games** — *Magician's Library Environment & VFX Pack*
- **Phoenix Market** — *Turn-Based jRPG Template* gameplay framework (UI art by OGA creators melle, paul-wortmann, unnamed, pauliuw, evilence)
- **Sameek Kundu** — *Art of Shader* stylized post-process pack
- **Jonas Ronnegard** — *70 Japanese Ornament Alphas*
- **CC0 community** — Kenney, Quaternius, Kay Lousberg (KayKit), Polygonal Mind, Poly Haven, OpenGameArt creators, Beatscribe, Juhani Junkala, and the Zunko-family (SSS LLC) & BOOTH character creators
- **fromage3900** — first-party Cathedral kit, Ornament Musical kit, the SDF material suite, and the Melusina character

The modular environment mega-kit in `Content/EnvSandbox/Meshes/Environment` is an assembled set built by the owner from ArtStation + staged packs — its components are credited per-pack in CREDITS.md.

Please see the full **[CREDITS.md](Docs/CREDITS.md)** — complete list of individual creators, direct source links, and licenses — and the coverage map in **[SOURCES_MATRIX.md](Docs/SOURCES_MATRIX.md)**. Thank you to every creator making this vertical slice possible!

```
âœ§ â”Š â‹† â”Š . â”Š â”Šâ”Š â”Šâ‹† â”Š .â”Š â”Š â‹†Ëš  âœ§  â”Š â”Š â‹† â”Š . â”Š â”Šâ”Š â”Šâ‹† â”Š .â”Š â”Š â‹†Ëš  âœ§
```

**Boundary:** Do not automate final Sakura level art direction. `L_SakuraPath` is human-owned.
