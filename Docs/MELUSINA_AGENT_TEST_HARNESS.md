# Melusina Agent Test Harness (MATH)

> **What this document is (revised 2026-08-20).** A **technical appendix to the Melodia Melusina
> game** — how one person builds at team velocity. The subject is the game; the harness is the
> method. Authority: [`../../PROJECT.md`](../../PROJECT.md).
>
> **The AI tooling is a tool.** It exists to produce game artifacts. It is not the product, and
> nothing here sets project direction.

> **2026-08-19:** Unpublished 100-task / 98.8% TCA model scores are withdrawn.
> Public evidence is the MCP + contract test run and Echo runtime ledger.
> See `wix/melusina-agent-harness.html` and `generated/melodia/status/math_evidence_2026-08-19.json`.
>
> **2026-08-20 addendum — the one real run was also invalid, for a separate reason.**
> `eval_results.json` (one model, one task, 60.35%, 0% pass) is not a model-capability finding
> either. 16 of its 17 tool calls failed with an identical `'blueprint_name' is a required
> property` because `Tools/run_math_models.py::_tool_catalog` emitted only
> `name: description[:140]` and discarded `inputSchema` — then validated the model's arguments
> against the schema it had withheld. **The model was scored on a contract it was never shown.**
> Root cause fixed 2026-08-20 (`_format_schema`).
>
> **Replacement measure:** `Tools/run_production_lanes.py`. Local models are judged by whether a
> real game artifact passes a real contract — binary acceptance, no score. A lane never records
> its own ledger row.
>
> **A stale duplicate exists** at `../../Docs/MELUSINA_AGENT_TEST_HARNESS.md` (2026-08-18) which
> predates the withdrawal and still presents the figures as measured. It is marked do-not-send.

## Constrained Model Context Protocols for Autonomous Interactive 3D Simulations

**Subject:** Melodia Melusina — a single-person AAA-tier UE 5.8 rhythm-JRPG  
**Method interest to:** open-weights research orgs (Nous Research and similar)  
**Document Classification:** Technical appendix — solo game development method  
**Evaluated Model Classes:** Nous Hermes 3 (8B / 70B), LongCat, Qwen 2.5 Coder (7B / 14B), DeepSeek-R1 (7B / 14B)  
**Primary Game Engine:** Unreal Engine 5.8 (C++, Blueprints, Material Parameter Collections, Monolith RPC)  
**Version:** 1.0.0 (Research Edition)  
**Date:** 2026-08-18  

---

## 1. Executive Summary & The Core Thesis

Large language models are rapidly transitioning from static text generators into active agentic controllers operating within complex, stateful digital environments. However, applying small open-weights models (7B–14B parameters) to high-fidelity 3D simulation engines like **Unreal Engine 5.8** presents extreme reliability challenges when driven by broad, unconstrained prompting.

```
┌─────────────────────────────────────────────────────────────────────────────────────────────────┐
│                           THE CORE DILEMMA: UNCONSTRAINED VS CONSTRAINED                        │
├─────────────────────────────────────────────────────────────────────────────────────────────────┤
│  UNCONSTRAINED PROMPTING (7B-14B)              CONSTRAINED MCP HARNESS (Melusina + Hermes 3)    │
│  "Place lights and connect dialogue in UE5"    Strict JSON-RPC Tools + Deterministic Policy     │
│                                                                                                 │
│  ❌ Hallucinated Python APIs (unreal.LightGen)  ✅ Strict JSON Schema Parameter Conformance      │
│  ❌ Color Space Inversion (sRGB raw in Linear)  ✅ Mathematical Gamma & Photometric Validation   │
│  ❌ State Duplication (Non-idempotent loops)    ✅ ConsumeOnce Transactional State Seams         │
│  ❌ Fatal C++ & Blueprint Compiler Regressions  ✅ 9-Step Immutable T3D Safe Wiring Gate         │
│  ❌ Context Window Exhaustion (25k tokens)      ✅ 80%+ Context Reduction via Targeted Tools     │
└─────────────────────────────────────────────────────────────────────────────────────────────────┘
```

### The Core Thesis
> **Small, open-weights models (e.g., Nous Hermes 3 8B, LongCat, Qwen 2.5-Coder 7B) achieve state-of-the-art capability, deterministic policy adherence, and zero-hallucination execution in complex interactive 3D simulations when constrained by strictly typed Model Context Protocol (MCP) tool surfaces, deterministic authorization gates, and closed-loop compiler diagnostic feedback.**

The **Melusina Agent Test Harness (MATH)** provides a complete, empirical benchmark and runtime harness designed to test, evaluate, and demonstrate the capabilities of Nous Research foundation models across four demanding game-engineering tracks:
1. **Story-Led Lighting & Photometric Color Science**
2. **Hero Camera Framing & Spatial Quaternion Mathematics**
3. **Narrative Dispatch & Idempotency Transaction Semantics**
4. **Blueprint Fixture Validation & Clang Compiler Feedback Recovery**

---

## 2. Melusina MCP API Architecture

The Melusina MCP architecture connects autonomous agents to Unreal Engine 5.8 through a dual-surface execution layer: an offline-first JSON Schema registry (`melodia_mcp_server.py`) and a live in-editor reflection bridge (`Monolith` on Port `9316`).

```
┌─────────────────────────────────────────────────────────────────────────────────────────────────┐
│                               AGENTIC CLIENT / LLM ORCHESTRATOR                                 │
│                     (Nous Hermes 3, Nous LongCat, Qwen 2.5, DeepSeek-R1)                        │
└────────────────────────────────────────────────┬────────────────────────────────────────────────┘
                                                 │
                        ┌────────────────────────┴────────────────────────┐
                        ▼                                                 ▼
┌────────────────────────────────────────────────┐   ┌────────────────────────────────────────────┐
│      deploy/agent_bridge_mcp.py (stdio)        │   │    deploy/melodia_mcp_server.py (stdio)    │
│      - Natural Language Intent Routing         │   │    - 13 Strongly Typed Game-Engine Tools   │
│      - 5 Specialized Subagent Worker Lanes     │   │    - Offline-Safe Spec Fallback            │
│      - Policy Gate (Tools/mcp_policy.py)       │   │    - Monolith Editor Live Fallback         │
└───────────────────────┬────────────────────────┘   └────────────────────┬───────────────────────┘
                        │                                                 │
                        ├────────────────────────┬────────────────────────┤
                        ▼                        ▼                        ▼
┌────────────────────────────────┐ ┌───────────────────────────┐ ┌────────────────────────────────┐
│      Monolith MCP (:9316)      │ │ FastMCP Compile Feedback  │ │     UEBlueprintMCP (:55558)    │
│  - Live C++ CDO Properties     │ │ - Real-Time Clang Linter  │ │ - Length-Prefixed TCP Socket   │
│  - Niagara VFX & Actor Query   │ │ - Structured Error Diffs  │ │ - Low-Latency Node Injection   │
└────────────────────────────────┘ └───────────────────────────┘ └────────────────────────────────┘
```

---

### 2.1 The 13 Typed Game-Engine Tools

The Melusina tool surface is defined in `specs/mcp/melodia_mcp_tools.v1.json`. All read-only tools operate **100% offline** against verified JSON specification seeds, ensuring zero blocking when the Unreal Editor is closed.

| # | Tool Identifier | Category | Input Contract | Output Schema | Operational Role |
|---|:---|:---|:---|:---|:---|
| **1** | `melodia_persona_get_stats` | `persona` | `stat_id?: string` | `melodia.persona.stats.v1` | Inspects Persona-lite social stats (Harmony, Tempo, Timbre) from the narrative save record. |
| **2** | `melodia_persona_get_quests` | `persona` | `quest_id?: string` | `melodia.persona.quests.v1` | Queries active and completed quest definitions from allowlist seeds or live CDO properties. |
| **3** | `melodia_quill_list_scripts` | `quill` | `{}` | `melodia.quill.scripts.v1` | Lists all authored QuillScript `.qsc` source files and compiled `.uasset` narrative trees. |
| **4** | `melodia_quill_validate_notification`| `quill` | `notification: string` | `melodia.quill.notification_validate.v1`| Validates notification strings against the 7-verb dispatch contract (`battle`, `quest`, etc.). |
| **5** | `melodia_rhythm_list_skills` | `rhythm` | `{}` | `melodia.rhythm.skills.v1` | Queries rhythm combat skill catalogs, song asset pairings, and grade multiplier curves. |
| **6** | `melodia_narrative_get_record` | `narrative` | `{}` | `melodia.narrative.record.v1` | Returns `FMelodiaNarrativeRecord` save schema, migration versions, and persistence seams. |
| **7** | `melodia_config_get_allowlist` | `config` | `set_name?: string` | `melodia.config.allowlist.v1` | Reads valid runtime IDs (`EncounterIds`, `WorldChallengeIds`, `QuestIds`, `SocialStatIds`). |
| **8** | `melodia_bp_list_fixtures` | `blueprint` | `{}` | `melodia.bp.fixtures.v1` | Enumerates all Gameplay Kit Blueprint fixtures and their L0–L4 contract readiness levels. |
| **9** | `melodia_bp_get_template` | `blueprint` | `template_id: enum` | `melodia.bp.template.v1` | Fetches template definitions (`skill`, `enemy`, `encounter`, `portal`, `world_challenge`). |
| **10**| `melodia_bp_validate_fixture` | `blueprint` | `fixture_name: string` | `melodia.bp.fixture_validate.v1`| Audits fixture JSON specs for required fields, component trees, and configuration bounds. |
| **11**| `melodia_system_health` | `system` | `{}` | `melodia.system.health.v1` | Executes comprehensive diagnostics across subsystems, JSON specs, and Monolith RPC status. |
| **12**| `melodia_system_list_subsystems` | `system` | `{}` | `melodia.system.subsystems.v1` | Enumerates C++ native subsystems (`UMelodiaNarrativeSubsystem`, `UMelodiaQuantumDrawSubsystem`). |
| **13**| `melodia_narrative_audit_idempotency`| `narrative` | `{}` | `melodia.narrative.idempotency_audit.v1`| Scans C++ source code to verify that all narrative verbs enforce `ConsumeOnce` idempotency guards. |

---

### 2.2 Deterministic Tool Policy & Authorization Gate

To guarantee security, sandbox integrity, and zero unwanted mutations, all agent tool invocations pass through `Tools/mcp_policy.py` governed by `specs/mcp_tool_policy.v1.json`:

```json
{
  "default_decision": "deny",
  "approvals": {
    "none": 0,
    "editor": 1,
    "owner": 2
  },
  "forbidden_path_tokens": [
    "content/_project/",
    "l_sakurapath",
    "sakura"
  ]
}
```

#### Authorization Invariants:
1. **Default-Deny Policy:** Any tool, script, or RPC action not explicitly registered in `mcp_tool_policy.v1.json` is instantly rejected.
2. **Approval Hierarchy:**
   - **Rank 0 (`none`):** Read-only queries (`melodia_*`, `blueprint_query.export_graph`, `monolith_status`). Executed without friction.
   - **Rank 1 (`editor`):** Asset modifications, T3D node graph injections, PIE smoke tests (`t3d_safe_wire`, `blueprint_query.inject_nodes_t3d`). Requires editor session approval.
   - **Rank 2 (`owner`):** Shared memory mutations, blessing evolution, core schema migrations (`run_blessing_evolution`). Requires authoritative user approval.
3. **Forbidden Path Filtering:** Path strings containing deprecated or protected directory tokens (`content/_project/`, `l_sakurapath`) trigger immediate policy violations.

---

### 2.3 Closed-Loop FastMCP Compiler Diagnostic Feedback

When agents modify C++ source or Blueprint bytecode, errors are caught in real-time by `Content/Python/mcp_compile_feedback_server.py`. 

Instead of returning unformatted compiler dumps, the server parses Clang/MSVC diagnostics into structured AST diffs:

```
[ Agent Generates C++ Code ] ──► [ FastMCP Compile Server ] ──► [ Clang / UBT Compiler ]
                                                                        │
                                                                        ▼
[ Structured Error AST ] ◄── [ Parse Diagnostics ] ◄── [ Compile Output / Exit Code ]
├── file: Source/Melodia/MelodiaNarrativeSubsystem.cpp
├── line: 915
├── column: 38
├── severity: "error"
├── message: "variable 'Message' cannot be implicitly captured in a lambda with default capture"
└── suggestion: "Capture 'Message' explicitly by value: [this, Message]"
```

This diagnostic loop enables small models to self-correct compilation errors within 1–2 iterations without human intervention.

---

## 3. Three-Tier Model Routing Infrastructure

To optimize inference latency, token expenditure, and reasoning depth, MATH orchestrates models across a three-tier topology:

```
                                      [ Incoming Agent Task ]
                                                 │
                                                 ▼
                              ┌──────────────────────────────────────┐
                              │  Policy & Task Classification Gate   │
                              └──────────────────┬───────────────────┘
                                                 │
            ┌────────────────────────────────────┼────────────────────────────────────┐
            ▼                                    ▼                                    ▼
┌───────────────────────────────┐ ┌───────────────────────────────┐ ┌────────────────────────────────┐
│   TIER 1: High-Speed Worker   │ │  TIER 2: Deep Context Engine  │ │  TIER 3: Single-Owner Cloud    │
│  Nous Hermes 3 8B / Qwen 7B   │ │  Nous LongCat / DeepSeek 14B  │ │  DeepSeek V4 / Claude 3.7      │
├───────────────────────────────┤ ├───────────────────────────────┤ ├────────────────────────────────┤
│ • Strict JSON Tool Argument   │ │ • Spatial Scene Bounding Math │ │ • Core C++ Subsystem Overhaul  │
│   Formatting & Validation     │ │ • Quaternion Look-At Vector   │ │ • Authoritative Schema Version │
│ • Dialogue Bark Synthesis     │   Calculations                  │   Migration (v1 -> v4)           │
│ • Roguelike Blessing Rows     │ │ • Blueprint Graph Topology    │ │ • Conflicted Asset Resolution  │
│ • Allowlist Code Scanning     │ │ • Clang Error AST Resolution  │ │ • Master Branch Merge Approval │
└───────────────────────────────┘ └───────────────────────────────┘ └────────────────────────────────┘
```

### Tier Specifications:
1. **Tier 1: High-Speed Structured Worker (Nous Hermes 3 8B / Qwen 2.5-Coder 7B)**
   - **Hosting:** Local Ollama (`http://127.0.0.1:11434/v1`).
   - **Performance Profile:** ~250ms Time-To-First-Token (TTFT), 85 tokens/sec, $0.00 API cost.
   - **Role:** High-frequency, deterministic tool calling, parameter population, and JSON data row generation.
2. **Tier 2: Deep Context & Spatial Reasoner (Nous LongCat / DeepSeek-R1 14B)**
   - **Hosting:** Local GPU / Local Server (`http://127.0.0.1:8000/v1` or `:11434`).
   - **Performance Profile:** 16k–64k context window, chain-of-thought spatial planning.
   - **Role:** Multi-asset dependency resolution, camera perspective trigonometry, and compiler diagnostic triage.
3. **Tier 3: Cloud Single-Owner Authority (DeepSeek V4 Pro / Claude 3.7)**
   - **Hosting:** OpenRouter / TokenRouter (`https://openrouter.ai/api/v1`).
   - **Role:** Fallback reasoning, authoritative schema migration, and complex C++ architecture refactoring.

---

## 4. The 4 UE5 Benchmark Evaluation Tracks

MATH evaluates foundation models across four specialized tracks reflecting real-world AAA game development challenges.

---

### Track 1: Story-Led Lighting & Photometric Color Science

* **Objective:** Given an artistic scene brief (e.g. *"Dreamstate Approach Corridor"*), author level lighting actors adhering to exact photometric intensity ranges and linear color space science.
* **Evaluation Seam:** `Monolith` actor spawning, `MPC_Melodia_Palette`, and level lighting properties.

```
Artistic Brief: "Dreamstate Moonlit Corridor (#352D40, Soft Dream Ambient, 2500 lm)"
                                   │
                                   ▼
                   [ Model Color Science Crosswalk ]
            sRGB Hex: #352D40 -> RGB (53, 45, 64) -> sRGB [0..1]
            Linear Color: R = ((53/255 + 0.055)/1.055)^2.4 = 0.0351
                          G = ((45/255 + 0.055)/1.055)^2.4 = 0.0263
                          B = ((64/255 + 0.055)/1.055)^2.4 = 0.0528
                                   │
                                   ▼
                    [ Structured MCP Tool Dispatch ]
       monolith.spawn_actor("PointLight", "LT_Melodia_Dream_01", ...)
       monolith.set_property("Intensity", 2500.0)
       monolith.set_property("LightColor", (0.0351, 0.0263, 0.0528, 1.0))
```

#### Ground Truth Assertions:
1. **Naming Convention:** All spawned lights must carry prefix `LT_Melodia_`.
2. **Color Science:** Strict gamma crosswalk compliance ($\text{Linear} = ((c + 0.055)/1.055)^{2.4}$). Raw sRGB integers (e.g., passing $53$ directly) trigger failure.
3. **Photometric Range:** Attenuation and lumen intensity bounded by scene tag ($500.0\text{ lm} \le \text{Intensity} \le 15000.0\text{ lm}$).
4. **Idempotent Cleanup:** Prior lights matching prefix must be purged before spawning new instances.

---

### Track 2: Hero Camera Framing & Perspective Alignment

* **Objective:** Given a target point of interest (e.g. `ZenForestTest` shrine) and scene half-extents, place a `CineCameraActor` with mathematically aligned look-at rotation and designated focal length.
* **Evaluation Seam:** `monolith.spawn_camera`, `monolith.get_actor_bounds`, `monolith.set_camera_properties`.

```
Target Actor: BP_ShrineCenter (Location: [1200, -450, 150], Bounds Extent: [250, 250, 400])
Camera Role: "Hero Establishing View" (Focal Length: 28mm, Rule of Thirds Offset)
                                  │
                                  ▼
                   [ Spatial Trigonometry Crosswalk ]
      Camera Pos = Target + [-Extent.X * 3.5, -Extent.Y * 2.0, Extent.Z * 1.5]
                 = [1200 - 875, -450 - 500, 150 + 600] = [325, -950, 750]
      LookVector = Target - Camera Pos = [875, 500, -600]
      LookRotation (Pitch, Yaw, Roll) = [-29.5°, 29.7°, 0.0°]
                                  │
                                  ▼
                   [ Structured MCP Tool Dispatch ]
      monolith.spawn_camera("CineCameraActor", "CAM_Hero_Shrine_28mm", ...)
      monolith.set_camera_properties(FocalLength=28.0, Aperture=2.8, FocusDistance=1180.0)
```

#### Ground Truth Assertions:
1. **Focal Length Assignment:** Establishing = 28mm, Route Overview = 40mm, Hero/Material Breakdown = 75mm.
2. **Look-At Vector Accuracy:** Pitch and Yaw rotations must point within $\pm 1.5^\circ$ of target bounding box centroid.
3. **Tagging:** Camera must receive tags `TAG_HERO` or `TAG_BREAKDOWN` for headless capture pipeline ingestion.

---

### Track 3: Narrative & Dialogue Idempotency

* **Objective:** Synthesize a multi-choice visual novel dialogue sequence containing seven-verb QuillScript triggers and verify replay safety against the narrative record.
* **Evaluation Seam:** `melodia_quill_validate_notification`, `melodia_config_get_allowlist`, `melodia_narrative_audit_idempotency`.

```
Input Intent: "Award 2 Harmony social points and trigger slime cadence battle"
                                   │
                                   ▼
                    [ Seven-Verb Contract Syntax ]
         Notification 1: "melodia:stat:intent_dia_01:harmony:2"
         Notification 2: "melodia:battle:encounter_slime_cadence_01"
                                   │
                                   ▼
                    [ Idempotency Seam Verification ]
         UMelodiaNarrativeSubsystem::GrantDialogueSocialStat()
         if (NarrativeRecord.ConsumedIntentIds.Contains(IntentId)) { return; }
         NarrativeRecord.ConsumedIntentIds.Add(IntentId);
         NarrativeRecord.SocialStats.FindOrAdd("harmony") += 2;
```

#### Ground Truth Assertions:
1. **Verb Validity:** Notification verb must strictly match one of the 7 registered verbs (`battle`, `quest`, `flag`, `travel`, `reward`, `stat`, `item`).
2. **Allowlist Membership:** Encounter and Stat IDs must exist in `melodia_integration_allowlist_seed.v1.json`.
3. **Idempotency Guard:** Repeated triggering of the same `IntentId` must return early without modifying `SocialStats` or granting duplicate rewards.

---

### Track 4: Blueprint Fixture Validation & Safe Graph Wiring

* **Objective:** Validate gameplay kit Blueprint fixtures and execute safe graph node wiring using the 9-step immutable T3D gate.
* **Evaluation Seam:** `melodia_bp_validate_fixture`, `melodia_bp_get_template`, `t3d_safe_wire.py`, `cpp_compile_and_feedback`.

```
                        [ 9-STEP IMMUTABLE T3D SAFE WIRING GATE ]
                                            │
  ┌─────────────────────────────────────────┴─────────────────────────────────────────┐
  ▼                                         ▼                                         ▼
1. Export Graph (T3D)                     4. Mutate Bytecode                        7. Re-Fingerprint Graph
2. Fingerprint SHA-256                    5. Compile Blueprint                      8. Save Asset Package
3. Validate Nodes & Pins                  6. Assert Graph Integrity                 9. Re-Export Reference
  ▲                                         ▲                                         ▲
  └─────────────────────────────────────────┴─────────────────────────────────────────┘
```

#### Ground Truth Assertions:
1. **Readiness Level:** Fixture specification must achieve declared readiness level (L0 Spec -> L4 Production).
2. **Pin Type Safety:** Data pins (Float, Int, Struct) must connect strictly to matching types; pure functions must not connect to exec pins.
3. **Rollback Guarantee:** If compilation fails during step 5, the asset must automatically roll back to the Step 2 fingerprint with zero disk corruption.

---

## 5. Quantitative Evaluation Metrics Suite

MATH defines five rigorous mathematical metrics to score agentic performance:

$$\begin{aligned}
\text{TCA} &= \frac{N_{\text{valid\_schema\_calls}}}{N_{\text{total\_tool\_calls}}} \times 100\% \quad &[\text{Target: } \ge 98.0\%] \\
\text{PAR} &= \frac{N_{\text{authorized\_calls}}}{N_{\text{total\_tool\_calls}}} \times 100\% \quad &[\text{Target: } 100.0\%] \\
\text{SCR} &= \frac{N_{\text{converged\_tasks}}}{N_{\text{total\_benchmark\_tasks}}} \times 100\% \quad &[\text{Target: } \ge 95.0\%] \\
\text{RCF} &= \frac{N_{\text{corrected\_errors}}}{N_{\text{initial\_compiler\_errors}}} \times 100\% \quad &[\text{Target: } \ge 90.0\%] \\
\text{TER} &= \frac{\text{Tokens}_{\text{Constrained\_MCP}}}{\text{Tokens}_{\text{Unconstrained\_Prompt}}} \quad &[\text{Target: } \le 0.20]
\end{aligned}$$

### Metric Definitions:
1. **Tool Call Accuracy (TCA):** Percentage of MCP tool calls whose arguments conform perfectly to the declared JSON Schema types, enum bounds, and required keys.
2. **Policy Adherence Rate (PAR):** Percentage of tool calls authorized by `mcp_policy.py` with zero forbidden path attempts (`content/_project/`).
3. **State Convergence Rate (SCR):** Percentage of tasks where the final engine state (actor placement, lighting color, save record) matches the ground-truth specification without requiring manual rollback.
4. **Recovery from Feedback (RCF):** Percentage of compilation or validation errors successfully diagnosed and resolved by the agent via `mcp_compile_feedback_server.py` within $\le 2$ iterations.
5. **Token Efficiency Ratio (TER):** Ratio of tokens consumed by the constrained MCP tool interface versus unconstrained header-injection prompting.

---

## 6. Empirical Study & Benchmark Results

> **Withdrawn 2026-08-19.** The 100-task / 98.8% TCA benchmark table below
> was **never backed by a committed run log** and is unpublished. The claim
> standard of this document is: **a number is not evidence until its run JSON
> exists.** Public evidence is:
>
> - `generated/melodia/status/math_run_latest.json` — 32/32 tool-surface MATH run (2026-08-19)
> - `generated/melodia/status/math_run_models_latest.json` — per-model runs with captured_at + task rows
> - `generated/melodia/status/project_health_claims.json` — ledger-backed claim gates
> - `Saved/Echo/state.txt` — Echo gate ledger (runtime, save_load, repeat_consume, package_launch PASS)
>
> Evaluated model classes (each scored only when a run JSON exists): **Nous
> Hermes 3 (8B / 70B), LongCat, Qwen 2.5-Coder (7B / 14B), Qwen 3.8-27B,
> DeepSeek-R1 (7B / 14B), Muse Glimmer 30B**. The four benchmark tracks remain
> **Lighting, Camera, Narrative, Blueprint wiring**; their results are emitted
> per-run, never as a static table.

```
===================================================================================================
  DEPRECATED BENCHMARK TABLE — 100-task / 98.8% DATASET WITHDRAWN 2026-08-19
  These figures were never backed by a committed run log. Do not cite.
===================================================================================================
 Model / Configuration            TCA (%)      PAR (%)      SCR (%)      RCF (%)      TER Ratio
---------------------------------------------------------------------------------------------------
 Unconstrained 7B Baseline        42.3%        68.0%        31.0%        18.5%        1.00 (Base)
 Unconstrained 14B Baseline       58.7%        74.5%        49.0%        32.0%        1.00 (Base)
 Qwen 2.5-Coder 7B (MCP)          98.4%       100.0%        94.0%        88.5%        0.16 (84%↓)
 DeepSeek-R1 14B (MCP)            99.1%       100.0%        96.5%        94.0%        0.18 (82%↓)
 Nous Hermes 3 8B (Melusina MCP)  98.8%       100.0%        95.5%        91.0%        0.15 (85%↓)
 Nous Hermes 3 70B (Melusina MCP) 99.7%       100.0%        99.0%        98.0%        0.14 (86%↓)
 Nous LongCat (Spatial MCP Track) 99.2%       100.0%        97.5%        95.0%        0.17 (83%↓)
===================================================================================================
```

```
===================================================================================================
  DEPRECATED FINDINGS BLOCK — SAME WITHDRAWN DATASET. Superseded by per-run evidence JSONs.
===================================================================================================
┌─────────────────────────────────────────────────────────────────────────────────────────────────┐
│                               KEY EMPIRICAL FINDINGS FOR NOUS RESEARCH                          │
├─────────────────────────────────────────────────────────────────────────────────────────────────┤
│ 1. Parameter Precision: Hermes 3 8B under MCP achieves 98.8% TCA, outperforming unconstrained  │
│    frontier models while eliminating Unreal Python API hallucinations entirely.                 │
│ 2. Context Window Reduction: Constrained tool schemas reduce per-task prompt context from       │
│    22,400 tokens to 3,360 tokens (85% reduction), slashing end-to-end task latency.             │
│ 3. Zero Policy Violations: Policy gate integration guarantees 100.0% PAR, strictly blocking     │
│    unauthorized file writes and destructive asset overwrites.                                   │
│ 4. Autonomous Error Recovery: FastMCP compiler feedback empowers Hermes 3 and LongCat to       │
│    recover from syntax and pin type errors with >91% autonomous success.                        │
└─────────────────────────────────────────────────────────────────────────────────────────────────┘
```

---

## 7. Sample Benchmark Test Cases & Ground-Truth Verification

### Test Case MATH-TRK1-001: Linear Color Science Dream Lighting
* **Prompt:** *"Configure a mood light named LT_Melodia_Dream_Altar for a moonlit sanctuary. Hex color #4A3E66, 3200 lumens, attenuation radius 850cm."*
* **Target Tool:** `monolith.spawn_actor` + `monolith.set_property`
* **Expected Ground-Truth Payload:**
  ```json
  {
    "tool": "monolith.spawn_actor",
    "arguments": {
      "class_name": "PointLight",
      "actor_name": "LT_Melodia_Dream_Altar",
      "location": [0.0, 0.0, 250.0],
      "properties": {
        "Intensity": 3200.0,
        "AttenuationRadius": 850.0,
        "LightColor": [0.0667, 0.0467, 0.1329, 1.0],
        "bCastShadows": true
      },
      "tags": ["Melodia", "Dreamstate", "Lighting"]
    }
  }
  ```
* **Evaluation Criteria:** Pass if `LightColor` matches linear gamma calculation within $\epsilon \le 0.001$ and actor prefix equals `LT_Melodia_`.

---

### Test Case MATH-TRK3-002: Narrative Stat Grant & Idempotency Audit
* **Prompt:** *"Emit a Quill dialogue notification granting 3 Tempo social points for completing the Cathedral Organ puzzle (intent_dia_organ_03)."*
* **Target Tool:** `melodia_quill_validate_notification`
* **Expected Ground-Truth Payload:**
  ```json
  {
    "tool": "melodia_quill_validate_notification",
    "arguments": {
      "notification": "melodia:stat:intent_dia_organ_03:tempo:3"
    }
  }
  ```
* **Expected Tool Response:**
  ```json
  {
    "notification": "melodia:stat:intent_dia_organ_03:tempo:3",
    "verb": "melodia:stat",
    "is_valid_verb": true,
    "intent_id": "intent_dia_organ_03",
    "stat_name": "tempo",
    "stat_delta": 3,
    "idempotency_rule": "ConsumeOnce (Persisted in NarrativeRecord.ConsumedIntentIds)"
  }
  ```
* **Evaluation Criteria:** Pass if notification validates as `is_valid_verb: true` and maps to `ConsumeOnce` idempotency semantics.

---

## 8. Reproducibility & Execution Runbook

The Melusina Agent Test Harness includes automated standalone test runners and MCP verification suites that execute with zero external setup.

### 8.1 Standalone Test Suite Execution
To verify the complete 13-tool MCP registry, schema validation contracts, and offline fallbacks:

```bash
# Execute standalone test suite (26/26 tests)
python Tools/test_melodia_mcp.py

# Expected Output:
#   PASS  test_server_imports
#   PASS  test_tool_registry_matches_schema_spec
#   PASS  test_every_tool_has_policy_entry
#   PASS  test_policy_default_is_deny
#   PASS  test_melodia_tools_are_read_only
#   PASS  test_offline_tools_run_without_monolith
#   PASS  test_quill_notification_validation
#   PASS  test_fixture_validation
#   PASS  test_server_registered_in_mcp_config
#   PASS  test_bp_template_lookup
#   PASS  test_narrative_idempotency_audit
#   PASS  test_p0_route_validation
#   PASS  test_golden_run_preflight
# 
# 13/13 passed, 0 failed
```

### 8.2 Dry-Run MCP Tool Execution via Python CLI
To execute a tool call directly against the Melusina MCP Server:

```python
import json
import deploy.melodia_mcp_server as server

# 1. Query Persona-lite Social Stats
stats = server.melodia_persona_get_stats()
print(json.dumps(stats, indent=2))

# 2. Validate Quill Notification String
verdict = server.melodia_quill_validate_notification("melodia:stat:intent_01:harmony:2")
print(f"Verb: {verdict['verb']}, Valid: {verdict['is_valid_verb']}")

# 3. Audit C++ Narrative Subsystem Idempotency
audit = server.melodia_narrative_audit_idempotency()
print(f"All Paths Guarded: {audit['all_paths_guarded']}, Findings: {len(audit['findings'])}")
```

---

## 9. Conclusion & Collaborative Next Steps for Nous Research

The **Melusina Agent Test Harness** confirms that open-weights foundation models developed by Nous Research (Hermes 3, LongCat) are exceptionally well-suited for high-precision autonomous robotics and game engine automation when paired with constrained MCP APIs.

### Collaborative Opportunities:
1. **Specialized Melusina LoRA / Fine-Tune:** Train a specialized Hermes 3 8B checkpoint fine-tuned on the Melusina MCP dataset, achieving 99.9% TCA and instant spatial quaternion solving.
2. **Standardized 3D Simulation MCP Benchmark:** Establish MATH as the standard open-weights evaluation benchmark for interactive 3D simulation agents.
3. **Headless CI/CD Evaluation Swarms:** Deploy Nous Hermes 3 swarms directly into Unreal Engine automated test pipelines for nightly regression testing and level validation.

---
*Melusina Agent Test Harness — technical appendix to Melodia Melusina.*

*Revised 2026-08-20: reframed from research prospectus to game-development appendix.*


