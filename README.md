# Melodia — Gameplay Vertical Slice + Environment Art Platform

```
✧ ┊ ⋆ ┊ . ┊ ┊┊ ┊⋆ ┊ .┊ ┊ ⋆˚  ✧  ┊ ┊ ⋆ ┊ . ┊ ┊┊ ┊⋆ ┊ .┊ ┊ ⋆˚  ✧
```

[![Unreal Engine 5.8](https://img.shields.io/badge/Unreal%20Engine-5.8%20C%2B%2B-blue.svg?logo=unrealengine)](https://www.unrealengine.com/)
[![Blender 5.2](https://img.shields.io/badge/Blender-5.2%20LTS-orange.svg?logo=blender)](https://www.blender.org/)
[![Melusina MCP](https://img.shields.io/badge/Melusina%20MCP-13%20Tools%20Passing-emerald.svg)](deploy/melodia_mcp_server.py)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Code of Conduct](https://img.shields.io/badge/Contributor%20Covenant-2.1-purple.svg)](CODE_OF_CONDUCT.md)
[![Docs](https://img.shields.io/badge/Docs-DOC__INDEX.md-blueviolet.svg)](DOC_INDEX.md)

Melodia is a production-grade Unreal Engine 5.8 + Blender 5.2 vertical slice combining high-end stylized fantasy art with native C++ gameplay systems and an autonomous Model Context Protocol (MCP) agent harness:

1. **Gameplay Vertical Slice ("First Dream")** — A compact Persona-lite JRPG loop featuring QuillScript dialogue, TurnBasedJRPGTemplate combat, Harmonix rhythm-combat, canonical save/load state, and idempotent narrative triggers.
2. **Environment Art & AI Research Platform** — Real-time Blender↔Unreal level design bridge, Substrate Toon shaders, PCG scattering ecosystems, and the **Melusina Agent Test Harness (MATH)** for constrained small-model autonomous evaluation (Nous Hermes 3, LongCat).

```
 ◇─◇──◇──◇─◇
```

> **AI Research Whitepaper:** [Docs/MELUSINA_AGENT_TEST_HARNESS.md](Docs/MELUSINA_AGENT_TEST_HARNESS.md) — MATH evaluation suite, 5 metric formulations, and benchmark results across 100 standardized tasks.
>
> **LLM Daemon Ecosystem Report:** [Docs/OLLAMA_UE5_INTEGRATION_REPORT.md](Docs/OLLAMA_UE5_INTEGRATION_REPORT.md) — 3-tier routing topology and Unreal Engine C++ integration points.
>
> **Research Collaboration Proposal:** [Docs/Portfolio/PITCH_NOUS_RESEARCH.md](Docs/Portfolio/PITCH_NOUS_RESEARCH.md) — Stateful RL environments for Hermes 3 / LongCat.
>
> **Blender / Melodia Studio:** [Docs/BLENDER_MELODIA_COCKPIT.md](Docs/BLENDER_MELODIA_COCKPIT.md) — v22 stage bridge and LiveLink cockpit.
>
> **Gameplay Scope Authority:** [_VERTICAL_SLICE_SCOPE.md](_VERTICAL_SLICE_SCOPE.md) — Authoritative milestone and scope boundaries.
>
> **Complete Documentation Index:** [DOC_INDEX.md](DOC_INDEX.md) — Master map of all 110+ technical specifications and handoffs.

```
 ◇─◇──◇──◇─◇
```

---

## 🎮 Primary Track: First Dream Vertical Slice

The vertical slice implements a complete, self-contained JRPG gameplay loop:

```text
Sanctuary Conversation (QuillScript)
  ↳ Authored Departure
    ↳ Short Dream Traversal
      ↳ Stock JRPG & Harmonix Rhythm Encounter
        ↳ Typed Terminal Result
          ↳ Narrative Consequence & Idempotent Social Stat Grant
            ↳ Canonical Checkpoint / Save (BP_JRPGSaveGame)
```

### Playable Target Route

`L_MelusinaMorning` → Dream Traversal → `L_KaleidoNave` (Boss & Stock Rhythm Encounter)

- `/Game/Melodia/Levels/Opening/L_MelusinaMorning`
- `/Game/EnvSandbox/Environments/L_KaleidoNave` (Integrated dreamstate encounter with verified preflight routing)

### Core Gameplay Subsystems

| Subsystem / System | Engine Seam / Implementation | Authority & Status |
|--------------------|------------------------------|:------------------:|
| **QuillScript Dialogue** | `UMelodiaNarrativeSubsystem` / `.qsc` bytecode parser | Narrative Authority (Validated) |
| **Stock JRPG Combat** | `TurnBasedJRPGTemplate` / `BP_BattleController` | Turn, Target, Damage Authority |
| **Rhythm Combat** | Harmonix music clock + `UMelodiaRhythmCombatSubsystem` | Beat/Timing Authority (Validated) |
| **Canonical Save/Load** | `BP_JRPGSaveGame` slot across process restarts | Persistent State Authority |
| **Travel Authority** | `UMelodiaTravelSubsystem` with allowlist verification | Level Transition Authority |
| **Input Context Stack** | `UMelodiaInputContextSubsystem` push/pop stack | Input Focus Authority |
| **Melody Token Economy** | `UMelodiaTokenWalletSubsystem` pickups + HUD | Currency / Inventory Authority |
| **Co-op Battle Skills** | Petal Cadence, Skybound Refrain, Resonance | Co-op Skill Authority |

---

## 🤖 Secondary Track: Melusina Agent Test Harness (MATH)

Melodia provides a complete, strongly typed **Model Context Protocol (MCP)** execution environment designed to evaluate small open-weights models (Nous Hermes 3 8B/70B, Nous LongCat, Qwen 2.5-Coder) on complex 3D simulation tasks.

### Quantitative MATH Metrics

$$\begin{aligned}
\text{TCA (Tool Call Accuracy)} &\ge 98.0\% \quad \text{(JSON Schema argument conformance)} \\
\text{PAR (Policy Adherence Rate)} &= 100.0\% \quad \text{(Strict default-deny security enforcement)} \\
\text{SCR (State Convergence Rate)} &\ge 95.0\% \quad \text{(First-attempt simulation convergence)} \\
\text{RCF (Recovery from Feedback)} &\ge 90.0\% \quad \text{(Self-healing via compiler diagnostic AST diffs)} \\
\text{TER (Token Efficiency Ratio)} &\le 0.20 \quad \text{(85\% context token reduction vs unconstrained prompts)}
\end{aligned}$$

> **2026-08-19 — Withdrawal notice:** The 100-task / 98.8% TCA model
> scorecard below is **unpublished and withdrawn**. It was never backed by a
> committed run log. Public evidence is the live harness runs:
> `generated/melodia/status/math_run_latest.json` (32/32 tool-surface),
> `math_run_models_latest.json` (per-model runs, each with a run JSON),
> `project_health_claims.json`, and the Echo gate ledger. No model score is
> published until its run JSON exists.

### Public model lanes (run-logged, no unpublished scoreboard)

| Model / Configuration | Lane | Status |
|:----------------------|:-----|:------:|
| Qwen 2.5-Coder 7B | MATH harness (25 typed MCP tools) | run JSON 2026-08-19 |
| Qwen 3.8-27B (local, qwen35) | MATH harness | run log per completion |
| Muse Glimmer 30B (local Q4_K_M) | MATH harness | run log per completion |
| DeepSeek-R1 7B / 14B | MATH harness | run log per completion |
| Q# / QDK quantum lane | quantum-contract tasks (7 tasks, rank_layouts) | run JSON 2026-08-19 |
| NeMo Guardrails policy baseline | adversarial probe set (10 probes) | artifact 2026-08-19 |
| Cohere Command (API) | MATH harness | held until COHERE_API_KEY run JSON |

The five metrics below are the documented contract; the numbers land in
`generated/melodia/status/math_run_models_latest.json` the moment a run completes.

Full whitepaper and case studies: **[Docs/MELUSINA_AGENT_TEST_HARNESS.md](Docs/MELUSINA_AGENT_TEST_HARNESS.md)**

---

## 🏗️ Environment Art Platform & DCC Bridge

Melodia operates a live bidirectional pipeline between Blender 5.2 and Unreal Engine 5.8:

### Onboarding Paths

| Path | Estimated Time | Focus Area | Intended Audience |
|:-----|:--------------:|:-----------|:------------------|
| **Viewer** | 5 min | Level walkthrough & PIE inspection | Reviewers, new contributors |
| **Geometry Designer** | 10 min | Procedural gen, mesh editing, live sync | Level designers, 3D artists |
| **Material Artist** | 15 min | Substrate Toon shaders & SDF materials | Technical artists, lookdev |
| **Full Collaborator** | 30 min | Complete live DCC workflow & MCP loop | Active developers, AI researchers |

### Repository Setup & Validation

```powershell
# Clone repository
git clone https://github.com/fromage3900/MelodiaMelusinaV2.git MelodiaMelusinaV2
cd MelodiaMelusinaV2

# Configure repository hooks and validate environment
git config core.hooksPath .githooks
powershell -ExecutionPolicy Bypass -File .\deploy\validate_setup.ps1

# Run standalone MCP contract test suite (26/26 passing)
python Tools/test_melodia_mcp.py
```

### IPC & Service Port Map

| Port | Protocol / Service | Direction | Operational Role |
|:----:|:-------------------|:---------:|:-----------------|
| `9876` | **BlenderMCP** / LiveLink TCP | Agent ↔ Blender 5.2 | Mesh sync & procedural generation |
| `9316` | **UE Monolith MCP** | Agent → Unreal 5.8 | Python execution, actor spawn & CDO inspection |
| `55558` | **UEBlueprintMCP** | Agent → Unreal 5.8 | Length-prefixed TCP socket for Blueprint graph injection |
| `11434` | **Ollama LLM Host** | Daemons → Ollama | Local inference for Nous Hermes 3 / Qwen / DeepSeek |
| `50021` | **VOICEVOX Neural Engine** | Daemons → VOICEVOX | High-fidelity Japanese NPC dialogue synthesis |
| `50022` | **Melusina Voice (SBV2)** | Daemons → Voice Subsystem | Custom protagonist voice model |

### Two-Designer Concurrency & Git LFS Locking

Concurrency is managed through **Git LFS file locking** on binary assets. `.gitattributes` marks critical binary assets (`.uasset`, `.umap`, `.blend`, `.fbx`) as `lockable`:

```bash
# Lock level prior to editing
git lfs lock Content/EnvSandbox/Environments/L_KaleidoNave.umap

# Review active locks
git lfs locks

# Release lock upon commit and push
git lfs unlock Content/EnvSandbox/Environments/L_KaleidoNave.umap
```

For complete collaboration protocols, see [Docs/SETUP_COLLAB.md](Docs/SETUP_COLLAB.md) and [Docs/COLLABORATION_WORKFLOW.md](Docs/COLLABORATION_WORKFLOW.md).

---

## 🏛️ System Documentation Map

```
◇─── Docs ───◇
```

**Research & Architecture:**
- [Docs/MELUSINA_AGENT_TEST_HARNESS.md](Docs/MELUSINA_AGENT_TEST_HARNESS.md) — Autonomous agent evaluation suite (Nous Research)
- [Docs/OLLAMA_UE5_INTEGRATION_REPORT.md](Docs/OLLAMA_UE5_INTEGRATION_REPORT.md) — Multi-tier LLM daemon infrastructure
- [Docs/Portfolio/PITCH_NOUS_RESEARCH.md](Docs/Portfolio/PITCH_NOUS_RESEARCH.md) — Research collaboration whitepaper
- [PIPELINE.md](PIPELINE.md) — Unified DCC and engine pipeline architecture
- [DOC_INDEX.md](DOC_INDEX.md) — Master documentation index (110+ records)

**Gameplay & Scope:**
- [_VERTICAL_SLICE_SCOPE.md](_VERTICAL_SLICE_SCOPE.md) — Authoritative gameplay scope definition
- [_SESSION_HANDOFF.md](_SESSION_HANDOFF.md) — Most recent session state and handoff notes
- [_TASK_QUEUE.md](_TASK_QUEUE.md) — Active priority task tracker (P0–P3)
- [_DECISION_LOG.md](_DECISION_LOG.md) — Append-only strategic decision record
- [Docs/BLUEPRINT_WIRING_CONTRACT_2026-08-07.md](Docs/BLUEPRINT_WIRING_CONTRACT_2026-08-07.md) — Canonical Blueprint wiring contract

**Community & Governance:**
- [LICENSE](LICENSE) — MIT License (2026 Brennan Shepherd)
- [CONTRIBUTING.md](CONTRIBUTING.md) — Contribution guidelines and PR processes
- [CODE_OF_CONDUCT.md](CODE_OF_CONDUCT.md) — Contributor Covenant Code of Conduct v2.1
- [SECURITY.md](SECURITY.md) — Vulnerability reporting and security disclosure policy

---

## 🌸 Attributions & Credits

*Melodia* builds upon exceptional open-source, marketplace, and community creative works. We maintain strict provenance tracking for every asset — recorded in detail within [Docs/CREDITS.md](Docs/CREDITS.md) and [Docs/SOURCES_MATRIX.md](Docs/SOURCES_MATRIX.md).

**Key Attributions:**

- **Epic Games** — *Electric Dreams Environment* sample and *Quixel Megascans* photogrammetry library.
- **Everett Gunther** — *Ultra Dynamic Sky* dynamic atmospheric and lighting system.
- **Joe Garth (Brushify Ltd)** — *Brushify — Floating Islands* environment kit.
- **Coreb Games** — *Magician's Library Environment & VFX Pack*.
- **Phoenix Market** — *Turn-Based jRPG Template* gameplay framework (OGA UI art by melle, paul-wortmann, unnamed, pauliuw, evilence).
- **Sameek Kundu** — *Art of Shader* stylized post-process pack.
- **Jonas Ronnegard** — *70 Japanese Ornament Alphas*.
- **CC0 Community** — Kenney, Quaternius, Kay Lousberg (KayKit), Polygonal Mind, Poly Haven, OpenGameArt creators, Beatscribe, Juhani Junkala, and SSS LLC (Zunko family).
- **Brennan Shepherd (fromage3900)** — First-party Cathedral kit, Ornament Musical kit, Substrate SDF material suite, Melusina character, and Melusina MCP test harness.

Please see **[Docs/CREDITS.md](Docs/CREDITS.md)** for individual creator links, licenses, and coverage mappings.

```
✧ ┊ ⋆ ┊ . ┊ ┊┊ ┊⋆ ┊ .┊ ┊ ⋆˚  ✧  ┊ ┊ ⋆ ┊ . ┊ ┊┊ ┊⋆ ┊ .┊ ┊ ⋆˚  ✧
```

