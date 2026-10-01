# Model Routing Canon — tiers, frontier discipline, cheap-model leverage

**Created:** 2026-09-26
**Registry (machine-readable):** `specs/orchestration/model_tiers.v1.json`
**Live routing:** `Tools/model_router.py` — `pick`, `chat`, `tier`, `tasks`, `test`, `ledger`, `cost`, `classes`
**Validator:** `Tools/validate_model_tiers.py` · **Tests:** `Tools/test_model_tiers.py`
**Orchestration plan (extend, never replace):** `.hermes/plans/2026-09-26_hermes-orchestrator-infra-plan.md`
**Swarm lane policy:** `.jcode/swarm-prompt.md` · **Status authority:** `CURRENT_STATE.md`
**Class-level model policy (per-class fallback chains):** `MODEL_LANES_2026-08-12.md`

---

## 0. Why this document exists

The project already routes *models* by task class (`Tools/model_router.py` `POLICY`) and already has an
orchestration topology (Hermes runs, Jev routes, Claude verifies). What it did not have was a written
rule for **which class of model is allowed to make which class of decision**.

That gap is how a fleet burns frontier tokens on README fold-ins and lets a free 8B model quietly
re-design a save format. This document closes it with one deterministic rule:

> **Frontier models decide architecture. Cheap and free models execute the decision. A verifier that
> did not produce the artifact opens the artifact and tries to falsify it.**

Nothing here replaces `Tools/model_router.py`; it adds tiers, escalation triggers and context policy on
top of the class policy that already exists.

---

## 1. The five tiers

| Tier | Label | Cost | Default classes | Job |
|---|---|---|---|---|
| **T0_ARCHITECT** | Frontier architect | frontier paid ($10 default / $40 cap) | `cpp` `deep` `orchestrator` | Module graph, persistence format, public owner surface, schema/contract, migration and convergence strategy. Writes a **decision spec**; executes nothing heavy. |
| **T1_VERIFIER** | Independent verifier | paid ($5 / $20 cap) | `review` `vision` `playtest` | Fresh eyes. Opens the artifact, measures, reports pass/fail and residual uncertainty. Never the producer. |
| **T2_EXECUTOR** | Bounded executor | cheap paid ($2 / $10 cap) | `code` `mcp` | Implements an already-decided change inside a declared write fence. |
| **T3_BULK** | Bulk / easy work | free tier ($2 / $5 cap) | `docs` `audit` `triage` | The 80% that is not a decision: docs prose, log triage, manifests, indexes, fixtures, summaries. |
| **T4_LOCAL** | Local / free daemon | $0 (hard cap 0) | `daemon` `author` + the five production lanes | Overnight volume, drafts, gate-accepted production content. Never reaches a paid endpoint. |

Every router class is claimed by exactly one tier — the validator fails if a class is unclaimed or
double-claimed, so adding a class to `POLICY` without tiering it breaks the gate instead of silently
defaulting to something expensive.

---

## 2. The decision procedure (deterministic, no vibes)

`python Tools/model_router.py route --packet packet.json` (or `--class/--goal/--paths/--needs-editor`)

1. **Base tier** = the tier whose `default_classes` contains the packet's `task_class`.
2. **Escalate.** For every row in `escalation_triggers` that matches the packet's paths or goal text,
   raise the tier to that trigger's `required_tier`. **Widest tier wins** — no averaging, no judgement.
3. **Local-only lock.** `daemon` and the five production classes are forced to `T4_LOCAL`; cloud entries
   in their `POLICY` chain are dropped, so a local lane fails loudly instead of billing.
4. **Editor lock.** `needs_editor: true` (or a `Content/**/*.uasset` write target) adds
   `editor_lease_required: true` and a `T1_VERIFIER` floor: one editor writer, verified by opening the
   artifact.
5. **Verification.** Any artifact claimed as evidence raises the floor to `T1_VERIFIER` with the
   producer pinned as the excluder.
6. **Model chain** = `POLICY[class]` filtered to the tier's permitted endpoints, in order. The decision
   is emitted as JSON and is reproducible byte-for-byte from the same packet.

### Escalation triggers (registry rows)

- `module_graph` · `never_touch_table` · `persistence_contract` · `public_api_surface` · `schema_change` ·
  `world_composition` · `vcs_operation` · `secret_or_credential` → **T0_ARCHITECT**
- `editor_mutation` · `independent_verification` → **T1_VERIFIER**

If a packet matches nothing, it stays at its class tier — which is the point. A log triage is not an
architecture decision and should never cost frontier tokens.

---

## 3. How frontier models are actually capitalized on

Frontier spend buys exactly three things. If a T0 packet produces none of them, it was a misroute.

1. **A decision spec (ADR) cheap tiers can execute mechanically.** Name the files, the existing owner
   that is extended (never a new parallel owner), the must-not list, and the acceptance check. T2/T3
   then implement it without re-deciding anything.
2. **A falsification of a plan that looked fine.** T0 paired with a different T1 model on the same
   artifact catches the class of error that costs a week: dual writers, silent allowlist no-ops, missing
   call sites — the failure modes already named in `MODEL_LANES_2026-08-12.md` §6.
3. **A convergence decision**: which of two parallel systems dies. This is the one thing no cheap model
   can be trusted with, because the cost of getting it wrong is permanent duplication.

### Context economy (the real cost lever)

| Tier | Gets | Does not get |
|---|---|---|
| T0 | Repo-scale context: `CURRENT_STATE.md`, `SYSTEM_MAP.md`, `DATA_FLOW.md`, playbook, named owner files (≤40 files / 200k) | The whole tree, all logs |
| T1 | The artifact, its contract, the producer's report (≤15 / 120k) | The producer's reasoning |
| T2 | The decision spec, `may_write` globs, the named owner, the existing test (≤20 / 60k) | Repo-wide reading |
| T3 | The citation list and the file it edits (≤8 / 32k) | The repository |
| T4 | The contract, the allowlist, its output path (≤6 / 32k) | Anything else |

Sending a bulk task the repo context is how a "cheap" lane becomes an expensive one. Sending T3 the
citation list instead of the repository is what makes free-tier routing safe.

## 3. Infinity Nikki AAA Fleet Archetypes

How Infold Games / Papergames structured their multi-agent engine:

### Tier S: Grand Architect (Opus 4.5 / Claude Sonnet 4.6 / GPT-5)
- **Role:** Sole authority to propose or approve mutations to core contracts, architecture invariant documents, and multi-subsystem boundaries.
- **Enforcement:** Never invoked for line-level generation. Outputs design tokens, class interface specs, and invariant definitions that Tiers A and B must satisfy.

### Tier A: Deep Specialists (Claude Sonnet 3.7 / GPT-4o / DeepSeek-Coder-V2-0724 / Qwen-2.5-Coder-32B)
- **Role:** Subsystem-level implementation. Owns one domain per run (e.g., `MelodiaCompendiumWidget.cpp`, `UMelodiaSaveGameArchive`).
- **Enforcement:** Works within bounds handed down by Tier S. Output validated by compiler + headless test suite before commit.

### Tier B: High-Throughput Runners (Gemini 2.5 Flash / Claude 3.5 Haiku / DeepSeek-V3 / Qwen-2.5-7B)
- **Role:** File classification, commit message generation, documentation indexing, translation, JSON validation, boilerplate conversion, test suite expansion.
- **Cost Ratio:** ~1/20th the token cost of Tier A, ~1/100th of Tier S. Unlocks continuous multi-agent operation without budget blowouts.

### Tier C: Zero-Cost Deterministic / Local Runners (Ollama Qwen-2.5-Coder-7B / DeepSeek-R1-Distill-8B / Python Ast)
- **Role:** Git pre-commit hooks, syntax validation, doc front-matter checks, local test running, p4/git drift verification, regex linting.
- **Enforcement:** Runs on local developer machine / CI agent. Zero cloud dependency.

---

## 4. The 8 Routing Tasks

| Task | Tier | Model Primary | Model Fallback | Why |
|---|---|---|---|---|
| `architecture_decision` | S | claude-sonnet-4-6 | claude-opus-4-5 | Cross-subsystem invariants require maximal reasoning depth |
| `cpp_core_implementation` | A | deepseek-coder-v2-0724 | claude-sonnet-3-7 | High-depth C++ UE idioms, macro awareness, pointer safety |
| `shader_hlsl_rendering` | A | deepseek-coder-v2-0724 | gpt-4o | HLSL, Nanite/Lumen, Substrate materials, Niagara renderers |
| `ui_widget_implementation` | A | claude-sonnet-3-7 | gpt-4o | Slate/UMG hierarchy, binding, layout invariants |
| `test_generation` | B | deepseek-v3 | gemini-2-5-flash | Repetitive test patterns, headless contract coverage |
| `doc_indexing_synthesis` | B | gemini-2-5-flash | claude-3-5-haiku | High-context ingestion, rapid cross-file indexing |
| `git_vcs_automation` | C | ollama/qwen2.5-coder:7b | deterministic | Fast, safe, zero-cost, local-only git/p4 operations |
| `atlas_validation` | C | deterministic | None | Python schema and integrity checks without LLM hallucination |

---

## 5. UE 5.8 High-End Pipeline Adaptation (Nikki Benchmark)

Infold Games' *Infinity Nikki* established the standard for open-world character-centric UE pipelines. For `MelodiaMelusinaV2`, we adapt three specific 5.8 tech columns:

### 1. Substrate Multi-Layer Shading + Strand Hair
- **Nikki Pillar:** Fabric layering (silk, velvet, lace, iridescent coatings) + ultra-dense strand groom hair.
- **Melodia Adaptation:** Regalia V4/V5 lookdev transitions to Substrate multi-layer materials (`SubstrateSlabBSDF` with sheen and clearcoat layers). Groom asset caching via `r.HairStrands.DeepShadow.Resolution=2048`.

### 2. Nanite Skeletal Meshes + Cloth Simulation
- **Nikki Pillar:** High-poly character outfits with full Nanite detail preserved in motion; real-time Chaos Cloth with self-collision.
- **Melodia Adaptation:** Melusina and party member hero meshes converted to Nanite SkelMesh (`r.Nanite.SkeletalMeshes=1`). Chaos Cloth LOD profiles tuned for 60fps console/PC targets.

### 3. World Partition Data Layers + Spout Real-Time Broadcast
- **Nikki Pillar:** Dynamic open-world streaming with seamless visual transitions.
- **Melodia Adaptation:** Multi-World architecture (`L_MelusinaMorning`, `L_KaleidoNave`, `L_Shorewake`) organized into World Partition Data Layers. Combined with the 3/3-tested Spout beauty sender (`UE_Beauty`) routing real-time rendered frames directly into TouchDesigner for live AV installation playback.

---

## 6. How to Invoke the Model Router

### Python CLI
```powershell
# Tier-aware resolution
python Tools/model_router.py --task architecture_decision
# Output: claude-sonnet-4-6 (Tier S)

python Tools/model_router.py --task doc_indexing_synthesis
# Output: gemini-2-5-flash (Tier B)

python Tools/model_router.py --task git_vcs_automation
# Output: ollama/qwen2.5-coder:7b (Tier C)
```

### In-Engine C++
Use `UMelodiaLLMRouter::ResolveModelForTask(ETaskCategory::Architecture)` which returns the canonical model string defined in `specs/orchestration/model_tiers.v1.json`.
