# ASUS Laptop Workstation — Source of Truth

**Date:** 2026-09-11  
**Status:** CANONICAL LAPTOP / DCC WORKSTATION CONTRACT  
**Workstation branch:** `collab/laptop/longterm`  
**Canonical runtime authority:** `main`  
**Branch policy:** [`BRANCH_WORKSTATION_POLICY.md`](BRANCH_WORKSTATION_POLICY.md)  
**Research input:** [`../Research/UE58_PROCEDURAL_WORLDBUILDING_TEST_NOW_2026-09-11.md`](../Research/UE58_PROCEDURAL_WORLDBUILDING_TEST_NOW_2026-09-11.md)

This is the single current source of truth for ASUS Nitro laptop work. It replaces the need to read multiple laptop planning/discovery notes before assigning Blender, Geometry Nodes, lightweight texture, or procedural-authoring tasks.

> The laptop is a production source lane, not a second game/runtime authority. `main` remains canonical for Unreal/runtime/capstone truth. Promote useful DCC work deliberately; never wholesale-merge workstation or recovery history over `main`.

---

## 1. What the laptop is for now

Use the ASUS Nitro for:

- Blender 5.2 LTS Geometry Nodes authoring;
- procedural asset and ecology prototypes;
- Blender Python automation for GN builders;
- audio-reactive geometry experiments;
- lightweight asset / texture experimentation;
- ArmorPaint build and evaluation work;
- on-the-go DCC iteration while Humber/home-PC lanes handle Unreal, heavy baking, builds, and runtime validation.

Do **not** move core UE gameplay, save, combat, quest, UI authority, or canonical runtime state into this lane.

---

## 2. Workstation / Git contract

Current preserved workstation branch:

```text
collab/laptop/longterm
```

Rules:

- divergence from `main` is not automatically a defect;
- never auto-delete the branch as stale;
- never wholesale-merge it over `main`;
- compare it to `main` before promotion;
- move only named, reviewed DCC artifacts / utilities through a scoped promotion branch or PR;
- `main` remains runtime truth.

### Sync before work / handoff

Before opening Blender/Rider/Unreal on either workstation:

```powershell
.\deploy\sync_workstation.ps1
```

Safe fast-forward + lane-specific hydration:

```powershell
.\deploy\sync_workstation.ps1 -Mode Sync -LfsProfile House
```

Full workstation sync contract: [`TWO_WORKSTATION_SYNC_CONTRACT_2026-09-04.md`](TWO_WORKSTATION_SYNC_CONTRACT_2026-09-04.md).

A workstation is not cleanly handed off while the report says `dirty`, `ahead`, `behind`, `diverged`, or `lfs-error`.

---

## 3. Current execution order

Do not open five simultaneous tool experiments.

1. **Finish and preserve the GN work already in progress.**
2. Build the smallest `GN_Melodia_AudioResonance` proof.
3. Package useful recurring GN values into a small `MelodiaEcologyBundle` only if the first proof benefits.
4. Finish compiling ArmorPaint and run **one** real-asset benchmark.
5. Promote only proven useful artifacts / explicit attributes into the UE `Resonance Ecology v0` experiment.
6. Leave World Creator / Geo-Scatter / broader terrain-tool evaluation parked unless a current task specifically needs them.

Goal: **more finished Melodia art per hour**, not accumulating procedural software.

---

## 4. Blender baseline — Blender 5.2 LTS

Use **Blender 5.2 LTS** as the preferred baseline for new laptop procedural-authoring work unless an established production `.blend` requires an older version.

Relevant capabilities:

- native sound-frequency sampling inside Geometry Nodes;
- Geometry Bundles for reusable procedural context;
- cleaner Python control of Geometry Nodes modifier inputs through current RNA properties;
- LTS stability instead of daily-build churn during capstone production.

Before upgrading an established `.blend`, preserve a known-good copy and verify custom scripts / add-ons.

---

## 5. P0 — `GN_Melodia_AudioResonance`

### Goal

Prove that a Melodia music source can drive an art-directed procedural geometry system directly in Blender without creating a second gameplay/audio authority.

```text
Melodia audio / stem
  -> Sample Sound Frequencies
  -> 3 authored frequency bands
  -> GN fields
  -> geometry / instances / motion
  -> baked or exported DCC result
```

First version should use three readable responses, for example:

- low band -> large-form displacement / breathing;
- mid band -> scatter density / growth;
- high band -> instance scale / sparkle / micro-motion.

Keep the visual language Melodia/cymatics-adjacent rather than generic equalizer art.

### Required proof

1. one `.blend` source;
2. one short capture showing three bands with distinct behavior;
3. one screenshot of the GN graph;
4. note audio source / band ranges / exposed controls;
5. one exported static or baked result only if UE promotion is useful.

**Pass:** reusable, art-directable geometry produced faster than the current alternative.  
**Park:** interesting but no production advantage over Houdini / UE PCG / authored animation.  
**Reject:** fragile, opaque, or generic audio-reactive decoration.

---

## 6. P1 — `MelodiaEcologyBundle`

Use Blender 5.2 Geometry Bundles to prototype a compact authoring context only after the P0 experiment proves useful.

Candidate context:

```text
Resonance
Density
Scale
Seed
AssetFamily
CymaticStrength
MaterialVariant
```

Bundles are **Blender authoring state only**. Before promotion, convert downstream-relevant values into explicit geometry, named attributes, textures, or documented export metadata.

```text
GN authoring context
  -> explicit exportable attributes
  -> UE 5.8 PCG / material consumers
```

This complements, but does not replace, the UE/Houdini `Resonance Ecology v0` proof.

---

## 7. P1 — Blender Python automation

Use Blender 5.2 Python for authoring automation where it saves real production time:

- set exposed GN modifier inputs;
- set seeds / resonance / asset-family parameters;
- generate controlled variants;
- run validation checks;
- batch naming / export preparation;
- capture small evidence sets.

Preferred pattern:

```text
Python
  -> configure GN modifier
  -> generate one controlled variant
  -> validate
  -> export / capture
```

Do not build a generalized automation framework before one real Melodia asset benefits from it.

---

## 8. ArmorPaint — active local evaluation

**Current user-reported status (2026-09-11): ArmorPaint is being compiled locally.**

Treat ArmorPaint as an evaluation, **not** as a replacement for Substance Painter / Sampler yet.

### One-asset benchmark

```text
open/import
-> bake
-> paint
-> masks/layers
-> export PBR maps
-> import into UE 5.8
-> inspect material result
```

Evaluate:

- laptop stability;
- bake quality;
- layer / mask ergonomics;
- speed for quick lookdev;
- export consistency;
- packed-map flexibility;
- UE round-trip friction;
- any meaningful advantage over the existing Substance workflow.

End with one decision:

- **ADOPT AUXILIARY** — genuinely useful for lightweight laptop painting;
- **PARK** — works but does not beat Substance;
- **REJECT** — instability / friction is not worth maintaining.

Do not migrate existing Substance assets simply because ArmorPaint is lightweight/open-source.

---

## 9. Bounded watch list

### Gaea 2.3 — use where it already helps

Macros / region workflows may support reusable terrain recipes such as:

- `Melodia_FloatingIsland`
- `Melodia_SeaAbove_Cliff`
- `Melodia_MonolithErosion`
- `Melodia_ResonanceValley`

Export useful masks / height data into the normal UE / Houdini / PCG pipeline.

### World Creator 2026 — watch / evaluate, do not migrate

Potential value: fast terrain composition with Blender / UE bridge workflows. Evaluate only through a low-risk test and compare against Gaea + Houdini on one real Melodia task.

### Geo-Scatter — optional

Useful only if it materially accelerates Blender layout / portfolio scatter. It does **not** replace UE PCG as the canonical Unreal world-population lane.

---

## 10. Promotion contract — laptop -> Unreal

```text
visual / procedural idea
  -> collab/laptop/longterm
  -> Blender / GN / texture source
  -> validate locally
  -> identify exact promotable artifact
  -> scoped promotion branch / PR
  -> UE import
  -> PCG / material / runtime validation
  -> evidence
  -> main
```

Promotable artifacts may include:

- selected `.blend` source with intentional provenance;
- FBX / glTF / Alembic / textures where appropriate;
- explicit point / mesh attributes;
- masks / heightfields / cymatic textures;
- Python utilities with a proven production use;
- screenshots / captures needed for evidence.

Never move unrelated laptop history merely to promote one useful artifact.

---

## 11. Authority boundaries

The laptop lane must not create replacements for established owners:

- UE gameplay/runtime truth -> `main`;
- UE PCG -> final Unreal procedural assembly / environment population;
- Houdini -> stronger topology / spatial / variant procedural work where appropriate;
- Nikki Cymatics -> approved Sheep material path;
- Substance -> core texture-authoring stack until a benchmark explicitly changes that decision;
- TouchDesigner -> visual/performance instrument, never gameplay truth;
- Blender audio sampling -> procedural authoring input, not a beat clock or rhythm grader.

---

## 12. Recovery / historical laptop work

The old laptop recovery branches are **evidence / salvage sources**, not current task batons.

### `recovery/laptop-main-20260904`

Captured on 2026-09-04 as a diverged recovery source (then 13 commits ahead / 24 behind the old `main`). It contains historical house / city / music-convergence work including:

- `Tools/house_v7_base_build.py`
- `Tools/house_detailed.py`
- `Tools/house_facade.py`
- `Tools/house_greybox.py`
- `Tools/house_roof.py`
- `Tools/house_shingle_patch.py`
- `deploy/surreal_arch/melodia_gn/` work;
- historical `Saved/MelusinasHouse/*.blend` sources.

Do **not** merge this branch wholesale; it also contains broad old removals / quarantine cleanup. Extract only named reviewed work if anything unique is still needed.

### Superseded reconciliation branches / PRs

- PR #79 / `collab/laptop/integration-batch-2026-09-02` — closed / historical;
- PR #81 / `collab/laptop/main-reconciliation-2026-09-04` — closed / superseded;
- PR #82 promoted the V7 house runtime/source baseline to `main`.

Other old branches such as `collab/laptop/onboarding-closeout-2026-09-02`, `collab/laptop/workstation-health`, and the `integration/*house*` branches are recovery/history only unless a specific missing artifact is proven unique.

### Canonical recovered house baseline

```text
RawArt/MelusinasHouse/MelusinasHouse_V7_Base.blend
```

This is already on `main`; do not resurrect recovery branches just to obtain it.

---

## 13. Agent rule

Before claiming laptop work is absent, or before merge / deletion / salvage, an agent must establish:

- branch class;
- current `main` comparison;
- unique intended work;
- destination / promotion path;
- binary / LFS implications;
- evidence that nothing important will be lost.

If those facts are unknown, leave the branch alone and investigate first.

---

## 14. Research relationship

Research remains separate from workstation operations on purpose.

Read [`../Research/UE58_PROCEDURAL_WORLDBUILDING_TEST_NOW_2026-09-11.md`](../Research/UE58_PROCEDURAL_WORLDBUILDING_TEST_NOW_2026-09-11.md) for the current UE/Houdini/PCG technical findings. This laptop contract imports only the parts that are actionable here: Blender 5.2 GN, audio-reactive authoring, explicit semantic export, and small controlled tool benchmarks.

Do not duplicate weekly research notes into this document; update this file only when they change the actual laptop execution contract.