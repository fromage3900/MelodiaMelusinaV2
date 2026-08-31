# Agent Toolchain Discovery Index — Houdini / Copernicus / Dash / Magpie

**Date:** 2026-08-30  
**Purpose:** stop agents from wasting time searching the wrong branch or looking for visual boards that were never committed.

---

# Read this first

There are currently **two different realities** in the repository:

1. **Current `main`** contains active Copernicus/Houdini implementation work and live integration evidence.
2. **Open PR #28 / branch `docs/2026-08-29-character-p1-p2-canon-audit`** contains the large Houdini + emerging-toolchain research corpus, including Dash and Magpie research.

Agents working only from `main` will miss much of the research unless they explicitly inspect PR #28 or fetch its branch.

PR #28:
`https://github.com/fromage3900/MelodiaMelusinaV2/pull/28`

Research branch:
`docs/2026-08-29-character-p1-p2-canon-audit`

Known PR #28 head at this audit:
`1c4976f22f19085be3be10bed541055f61fbfdf6`

---

# Current `main` — live Copernicus / Houdini implementation

These are not speculative research notes. They are the current implementation/evidence lane and should be checked before proposing new Copernicus work.

## Copernicus tool root

`Tools/Houdini/copernicus/README.md`

Primary implementation files:

- `Tools/Houdini/copernicus/melodia_dress_cop.hip.template.md`
- `Tools/Houdini/copernicus/copernicus_dress_bake.py`
- `Tools/Houdini/copernicus/copernicus_petal_variants.py`
- `Tools/Houdini/copernicus/copernicus_fabric_sheen.py`
- `Tools/Houdini/copernicus/copernicus_terrain_height_to_nanite.py`
- `Tools/Houdini/copernicus/hda_melodia_lookdev_spec.json`

Related verification / UE intake:

- `Content/Python/verify_tex_contract.py`
- `Content/Python/ingest_sea_above_p0.py`

Current reports / handoffs:

- `Docs/Plans/COPERNICUS_AAA_LIVE_REPORT_2026-08-31.md`
- `Docs/Art/DRESS_HOUDINI_SETUP_REVIEW_2026-08-30.md`
- `Docs/Handoffs/SESSION_HANDOFF_DRESS_BAKE_2026-08-30.md`
- `Docs/Art/DRESS_BAKE_EVIDENCE_2026-08-30/dress_bake_manifest.json`

Important recent Copernicus commits seen during this audit:

- `cfb446acc560265998701d23b9006db6ed5ecb63` — AAA dress/terrain/fabric COP scaffold + lookdev/material work
- `7d93b97a7e38193a7ef1cdf03a737d437a38dd75` — petal VAT / validation queue
- `31b0616932fbed6c7d32a325ead836322666e630` — petal COP arrow + VAT fix

## Agent rule

Before creating a new Copernicus graph/tool, inspect the files above and answer:

> Is this already implemented, partially implemented, or deliberately scoped differently?

Do not create a second Copernicus architecture because a branch-only research document was not visible.

---

# PR #28 — branch-only Houdini research corpus

The following documents are present in PR #28 and may not be discoverable from an agent operating only on `main`.

## Houdini architecture / execution

- `Docs/Houdini/MARA_P0_P3_HOUDINI_EXECUTION_PLAN_2026-08-29.md`
  - character + world procedural execution plan
  - Mara/KineFX lane
  - P1/P2/P3 HDA families
  - Houdini/UE ownership boundaries

- `Docs/Houdini/MELUSINA_HOUDINI_UE58_TECHNICAL_RESEARCH_2026-08-30.md`
  - detailed Houdini Engine + UE5.8 research
  - Node Sync / SessionSync / KineFX / World Partition / Data Layers / attributes / materials / VAT / curves / bake policy

- `Docs/Houdini/LATE_MONOLITH_VISUAL_ESCALATION_BIBLE_2026-08-29.md`
  - late Monolith visual doctrine
  - negative-space anatomy
  - camera reveal composition
  - field-response and offline-sim strategies

- `Docs/Houdini/MELODIA_WORLD_COMPILER_TOMORROW_SCAFFOLD_2026-08-30.md`
  - scaffold for turning procedural authoring into a repeatable world-compilation lane

- `Docs/Houdini/HOUDINI_LICENSING_CORE_FX_INDIE_TRANSITION_RESEARCH_2026-08-30.md`
  - license / edition transition research and constraints

## Emerging toolchain master research

- `Docs/Research/EMERGING_3D_RENDERING_TOOLCHAIN_RESEARCH_2026-08-30.md`
  - **this is the main document containing Dash and Magpie research**
  - also covers SpeedTree, Houdini 22, Copernicus, IlluGen, LiquiGen, EmberGen, Cascadeur, Gaea, World Creator, Toolbag, UE5.8 Mesh Terrain, Procedural Vegetation Editor, Unreal MCP, RTX Kit, neural shaders/materials, Procedura, etc.

- `Docs/Research/TOOLCHAIN_INTEGRATION_SPIKE_PLAN_2026-08-31.md`
  - integration tests and ADOPT / PARK / REJECT / WATCH gates
  - includes real Melodia-shaped benchmarks rather than vendor-demo evaluation

- `Docs/Research/TOOLCHAIN_KICKOFF_2026-08-30_CASCADEUR_ILLUGEN_BLENDER_RHYTHM.md`
  - same-day first-wave tool tests

- `Docs/Research/EMERGING_3D_TOOLCHAIN_TRENCH_SWEEP_02_2026-08-30.md`
- `Docs/Research/TOOLCHAIN_TRENCH_SWEEP_02_TEST_PLAN_2026-08-31.md`
- `Docs/Research/EMERGING_3D_TOOLCHAIN_TRENCH_SWEEP_03_2026-08-30.md`
  - deeper tool/render/representation research

---

# Dash — exact research location

There is **no standalone `DASH_*.md` document** in PR #28.

Dash is documented inside:

`Docs/Research/EMERGING_3D_RENDERING_TOOLCHAIN_RESEARCH_2026-08-30.md`

and referenced by the integration-spike planning docs.

Current intended role:

```text
Houdini / PCG / SpeedTree
    -> systemic world generation

Dash
    -> fast artist-facing final dressing / composition / local override pass
```

Agent interpretation:

- Do not treat Dash as a replacement for Houdini.
- Do not treat Dash as a replacement for SpeedTree.
- Test it specifically against the last-mile environment-art bottleneck: hero clutter, composition cleanup, local physical placement and fast dressing inside Unreal.

If an agent cannot find a Dash-specific file, it should read the master emerging-toolchain document rather than conclude the research is missing.

---

# Magpie — exact research location

There is **no standalone `MAGPIE_*.md` document** in PR #28 or current `main` at this audit.

Magpie is documented inside:

`Docs/Research/EMERGING_3D_RENDERING_TOOLCHAIN_RESEARCH_2026-08-30.md`

Current status is **research-only / watch**, not production integration.

The relevant concept is a generative-rendering architecture where conventional game simulation remains authoritative while a generative renderer produces final visual frames.

For Melodia this is useful as a long-range research reference because it separates:

```text
simulation truth
from
visual truth
```

It is **not** an approved runtime dependency, shipping renderer, or current UE replacement plan.

Agents must not start a Magpie integration project unless a new explicit task promotes it out of WATCH/RESEARCH.

---

# Copernicus — research vs current implementation

Copernicus exists in both lanes:

## Research doctrine

Branch-only research in PR #28 describes Copernicus as Houdini's GPU image/texture authoring layer that can share procedural fields with SOP geometry and bake normal UE texture outputs.

Conceptual ownership:

```text
Houdini SOPs
    -> procedural form / anatomy / masks / fields

Copernicus
    -> procedural visual evidence / texture families / maps

Substance / artist finishing
    -> authored beauty pass when useful

Unreal
    -> runtime material/state/presentation authority
```

## Current implementation

The `Tools/Houdini/copernicus/` files on `main` are newer and should be considered before executing old research tasks literally.

**Current implementation outranks speculative branch plans when they conflict.**

Do not delete research; mark it as superseded or update the plan after comparing with live code.

---

# Visual / image-board audit

## What is actually committed in PR #28

The PR #28 changed-file list contains only these image assets:

- `Docs/Art/Images/CharacterConcepts/mara_elettra_vell_ebenezer_primary_visual_canon_2026-08-30.webp`
- `Docs/Art/Images/shorewake_shader_flow_sea_above_p0_visual_target_2026-08-29.svg`

Neither is a Dash/Magpie/Houdini toolchain board.

## Therefore

At this audit, **no committed file matching a Houdini/Dash/Magpie toolchain image board was found** in `main` or PR #28's changed-file list.

If a board was generated or shown in ChatGPT but cannot be found by path, treat it as:

`CHAT-ONLY / UNCOMMITTED VISUAL REFERENCE`

and **do not keep searching the repository indefinitely**.

Future recovered visual boards should go under:

`Docs/Research/Images/Toolchain/`

Suggested canonical filenames:

- `melodia_super_pipeline_16x9_2026-08-30.png`
- `houdini_copernicus_unreal_ownership_map_16x9_2026-08-30.png`
- `dash_environment_dressing_integration_map_16x9_2026-08-30.png`
- `magpie_simulation_vs_visual_truth_research_board_16x9_2026-08-30.png`

Do not invent these files. Their names above are reserved destinations for recovered/regenerated boards.

---

# How an agent should read branch-only research

If the branch exists locally:

```bash
git fetch origin docs/2026-08-29-character-p1-p2-canon-audit
git show origin/docs/2026-08-29-character-p1-p2-canon-audit:Docs/Research/EMERGING_3D_RENDERING_TOOLCHAIN_RESEARCH_2026-08-30.md
```

For Houdini technical research:

```bash
git show origin/docs/2026-08-29-character-p1-p2-canon-audit:Docs/Houdini/MELUSINA_HOUDINI_UE58_TECHNICAL_RESEARCH_2026-08-30.md
```

For the execution plan:

```bash
git show origin/docs/2026-08-29-character-p1-p2-canon-audit:Docs/Houdini/MARA_P0_P3_HOUDINI_EXECUTION_PLAN_2026-08-29.md
```

If an agent cannot access that ref, it should report **branch unavailable** rather than claiming the document does not exist.

---

# Priority reading order for an agent working on these systems today

1. `AGENTS.md`
2. this index
3. current `Tools/Houdini/copernicus/README.md`
4. current live Copernicus report / handoff docs
5. branch-only `EMERGING_3D_RENDERING_TOOLCHAIN_RESEARCH_2026-08-30.md`
6. branch-only `MELUSINA_HOUDINI_UE58_TECHNICAL_RESEARCH_2026-08-30.md`
7. branch-only `MARA_P0_P3_HOUDINI_EXECUTION_PLAN_2026-08-29.md`
8. branch-only `TOOLCHAIN_INTEGRATION_SPIKE_PLAN_2026-08-31.md`
9. relevant chapter-specific Monolith docs
10. only then propose new architecture or integrations

---

# Non-negotiable anti-duplication rules

- **Copernicus:** inspect current `main` implementation before authoring another graph/tool.
- **Houdini:** author procedural evidence/assets; do not create parallel Unreal runtime authority.
- **Dash:** last-mile artist acceleration test, not a replacement world generator.
- **Magpie:** research/watch only unless explicitly promoted.
- **Image boards:** if absent from the paths above, state they are uncommitted; do not fabricate a path.
- **Branch research:** branch-only does not mean nonexistent.
- **Current code beats old speculative plan when they conflict.**

---

# Consolidation TODO

The long-term fix is to stop leaving high-value research stranded on an aging mega-PR.

Recommended follow-up:

1. extract still-valid Houdini/toolchain research from PR #28 onto a fresh branch from current `main`;
2. reconcile it against the live Copernicus implementation;
3. merge research-only docs independently from older canon changes;
4. recover/regenerate the missing 16:9 toolchain boards and commit them under `Docs/Research/Images/Toolchain/`;
5. leave PR #28 to handle only material that still genuinely belongs together.

Until that consolidation happens, **this file is the discovery SSOT** for Houdini / Copernicus / Dash / Magpie research.
