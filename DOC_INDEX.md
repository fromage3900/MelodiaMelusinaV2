# Melodia — Documentation Index & Authority Map

**Front Door for Project Documentation**
**Last Updated:** 2026-09-01 (Evening P0 Closeout & Chapter Loop Checkpoint)
**Single Source of Truth Rule:** Prefer updating this index over creating unanchored status notes.

---

## 1. The Core Authority Hierarchy

When working on Melodia, consult these documents in order. They define the architecture, state authority, and execution priorities of the project.

| Priority | Document | Authority & Scope |
|:---:|---|---|
| **1** | [**`PROJECT.md`**](../PROJECT.md) / [**`README.md`**](README.md) | **What this project is.** Melodia is a single-author Rhythm-JRPG in Unreal Engine 5.8. QuillScript and TurnBased JRPG are absolute authorities. AI/MCP tooling is supporting infrastructure. |
| **2** | [**`Docs/Handoffs/MELODIA_EVENING_PLAN_P0_AND_CHAPTER_LOOP_2026-09-01.md`**](Docs/Handoffs/MELODIA_EVENING_PLAN_P0_AND_CHAPTER_LOOP_2026-09-01.md) | **Active Evening Execution Plan.** The authoritative execution plan for closing out and shipping P0, validating the 6-phase reusable chapter gameplay loop, and freezing immutable evidence. |
| **3** | [**`CURRENT_STATE.md`**](CURRENT_STATE.md) | **Canonical State Document.** 10/10 P0 gameplay gates passing, 524/524 automated tests passing, preflight status, and level/subsystem health. |
| **4** | [**`TODO.md`**](TODO.md) | **Master Task Ledger.** Verified P0 milestones, tonight's active execution sequence, and Chapter 2 roadmap. |
| **5** | [**`Docs/ORCHESTRA_CONVERGENCE_2026-08-20.md`**](Docs/ORCHESTRA_CONVERGENCE_2026-08-20.md) & [**`Docs/ORCHESTRA_CONTRACT_2026-08-20.md`**](Docs/ORCHESTRA_CONTRACT_2026-08-20.md) | **Architectural Blueprint.** The Two Authorities (QuillScript narrative, TurnBased JRPG state) and Four Converged Pillars (Rhythm Combat, Wardrobe Traversal, Music-as-Key, Single-Writer UI Bridge). |
| **6** | [**`QUICKSTART.md`**](QUICKSTART.md) | **Developer Quickstart.** Setup instructions, automated test runner execution (`run_tests.ps1`), PIE gameplay walk, and Win64 packaging commands. |
| **7** | [**`_VERTICAL_SLICE_SCOPE.md`**](_VERTICAL_SLICE_SCOPE.md) & [**`_PORTFOLIO_SHIP_CHECKLIST.md`**](_PORTFOLIO_SHIP_CHECKLIST.md) | **Scope & Shipping Criteria.** P0 vertical slice boundaries, gate verification checklist, and shipping acceptance standards. |
| **8** | [**`SYSTEM_MAP.md`**](SYSTEM_MAP.md) & [**`DATA_FLOW.md`**](DATA_FLOW.md) | **System Architecture & Data Flow.** Complete lifecycle trace from QuillScript dialogue to traversal, rhythm combat, reward distribution, and save game persistence. |
| **9** | [**`TEST_READY.md`**](TEST_READY.md) | **Test Verification Record.** Test suite structure, validation tiers, and benchmark verification details. |

---

## 2. Universal Reusable Chapter Gameplay Loop Documentation

Every chapter in Melodia adheres to the 6-phase universal loop. Key contracts and specifications:

- **Loop Architecture & Invariants:** [Docs/Handoffs/MELODIA_EVENING_PLAN_P0_AND_CHAPTER_LOOP_2026-09-01.md](Docs/Handoffs/MELODIA_EVENING_PLAN_P0_AND_CHAPTER_LOOP_2026-09-01.md)
- **P0 Golden Run Contract:** `specs/p0/core_p0_dream_golden_run.v1.json`
- **Narrative Subsystem & 7-Verb Grammar:** `Source/BS_GodFile/MelodiaIntegration/MelodiaNarrativeSubsystem.h`
- **Wardrobe Traversal Provider Contract:** `Source/BS_GodFile/MelodiaIntegration/MelodiaTraversalCapabilityProvider.h`
- **UI Bridge Single-Writer Contract:** `Source/BS_GodFile/MelodiaIntegration/MelodiaUIBridgeSubsystem.h`
- **Battle & Rhythm Presentation Seam:** `Docs/Handoffs/P0_BATTLE_UI_CLOSEOUT_HANDOFF_2026-08-27.md`

---

## 3. Automation, Testing & Tooling Documentation

- **Core Automated Test Runner:** `run_tests.ps1` (Executes GMM simulations, P0 integration tests, and ECHO contracts)
- **Offline P0 Preflight Gate:** `Tools/verify_p0_offline.py`
- **Melodia MCP Regression Suite:** `Tools/test_melodia_mcp.py`
- **End-to-End Release & Hygiene Suite:** `Tools/test_e2e_melusina_release.py`
- **MATH Evaluation Benchmark:** `Docs/MELUSINA_AGENT_TEST_HARNESS.md`
- **Gate Ledger & Immutable Evidence:** `Saved/gate_ledger.json`

---

## 4. Environment Art, Levels & Shaders

- **Sanctuary Level (`L_MelusinaMorning`):** Narrative start, departure gate, lighting lookdev.
- **Overworld Journey Level (`LV_SeaAbove_Prototype`):** Recast navmesh, Starskiff docking, `APCGHeroMusicGraphHost` phrase stepping.
- **Battle Arena (`L_KaleidoNave`):** Turn-based combat, Rhythm Highway integration, kaleidoscope shaders.
- **Substrate Toon Shader Spine:** `Docs/T3D_Baseline/` and `MATERIAL_LOOKDEV_PIPELINE.md`.

---

## 5. Credits, Provenance & Legal

- **Asset Credits Ledger:** [Docs/CREDITS.md](Docs/CREDITS.md)
- **Source Matrix:** [Docs/SOURCES_MATRIX.md](Docs/SOURCES_MATRIX.md)
- **License Terms:** [LICENSE](LICENSE) (MIT License)
- **Code of Conduct:** [CODE_OF_CONDUCT.md](CODE_OF_CONDUCT.md)
- **Security Policy:** [SECURITY.md](SECURITY.md)

---
*Melodia Documentation Index — Maintained under strict single-source-of-truth discipline.*
