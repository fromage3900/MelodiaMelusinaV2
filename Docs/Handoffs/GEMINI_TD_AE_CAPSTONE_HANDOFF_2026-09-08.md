# Gemini Handoff — Choral Sheep TouchDesigner + After Effects Capstone Lane

**Date:** 2026-09-08  
**Lane owner:** Gemini  
**Scope:** TouchDesigner + After Effects planning/prep and capstone documentation  
**Do not own:** Unreal gameplay architecture, save, narrative, companion recruitment, world-state authority

## 2026-09-08 asset-state correction

The Choral Sheep source is now **owner-confirmed fully rigged**. Do not treat the older “0 vertex groups / weight-paint blocked” note as current truth.

The remaining owner-side asset check is narrower:
- verify the current rig deforms correctly;
- use an **Auto-Rig Pro (ARP) re-export** if the current UE FBX needs refreshing;
- verify the resulting skeletal mesh/deformation in UE.

Gemini should continue TD/AE work in parallel and should not open a re-rigging lane.

Owner execution plan:
`Docs/Semester/CHORAL_SHEEP_DAY1_EXECUTION_PLAN_2026-09-08.md`

## Cross-repo implementation authority

Read first:
`Docs/TouchDesigner/MELODIA_TD_AE_CROSS_REPO_CONTRACT_2026-09-08.md`

Implementation rule:
- gather runtime/game truth from `fromage3900/MelodiaMelusinaV2`;
- implement new TouchDesigner work in the canonical `grandmaster_melodia` Git checkout at `C:/MelodiaTouchDesigner/td/grandmaster_melodia/`;
- treat `fromage3900/EnvironmentPortfolio/_TouchDesigner/grandmaster_melodia/` as a frozen historical mirror, not the active build target;
- use TD/AE as the concert-visual, editorial-graphics, compositing, and showcase pipeline for the main game project;
- keep the repos separate; do not vendor or submodule the TD project into the game repo.

## 2026-09-08 live-performance research landing gate

A complete TouchDesigner performance-research packet was prepared on the **unmerged staging branch**:

`docs/td-live-performance-contract-2026-09-08`

Do **not** merge that branch into `MelodiaMelusinaV2`; the V2 `_TouchDesigner` tree is historical/frozen.

Before expanding the canonical TD implementation, transfer/adapt these six files from that staging branch into the **canonical TD Git** at:

`C:/MelodiaTouchDesigner/td/grandmaster_melodia/`

Recommended destination: `Docs/`.

Files to land in the TD repo:

1. `MELODIA_LIVE_VISUAL_IDENTITY_CONTRACT_2026-09-08.md`
2. `ACTUAL_LIVE_SHOW_PIPELINES_RESEARCH_2026-09-08.md`
3. `MELODIA_SHOW_SYSTEM_ARCHITECTURE_2026-09-08.md`
4. `PIPELINE_RECIPES_CHORAL_SHEEP_2026-09-08.md`
5. `AGENT_BUILD_CONTRACT.md`
6. `CHORAL_SHEEP_CAPSTONE_TD_IMPLEMENTATION_PLAN_2026-09-08.md`

After transfer:
- commit them in the **TD repo**, not the game repo;
- record the TD commit SHA in the capstone handoff/evidence;
- treat them as TD-side authority before building new concert scenes.

### Visual identity that must be enforced

> **Steal the timing, not the branding.**

Canonical show grammar:

```text
QUIET
→ ROOT HIT
→ INTERVAL HIT
→ RESOLUTION HIT
→ WORLD HIT
→ AFTERIMAGE
```

Hard visual rules:
- subject silhouette first;
- black-violet negative space + pearl / sea-cyan / lavender;
- one primary musical structure per hit;
- stillness/rest states are mandatory;
- giant scale change is used sparingly;
- typography is a semantic event, not constant HUD;
- feedback/glitch is punctuation, never the default texture;
- no generic rainbow/cyberpunk VJ drift;
- no copied Ninajirachi / BABYMETAL / 2hollis / PC Music branding.

### Pipeline architecture that must be enforced

Real show research repeatedly supports:

```text
semantic show/music signals
→ normalized control bus
→ authored scene/song module
→ generator
→ bounded FX stack
→ state/preset + manual trim
→ output/capture
```

For Melodia, implement this as an extension of the existing grandmaster project—not a replacement project or parallel bridge.

First flagship module:
`performance/scenes/chladni_fleece`.

## 2026-09-08 owner-approved concept-sheet lock

Before revising the Chladni Fleece scene, read:

`Docs/References/ChoralSheepCapstone/BOARD_06_OWNER_APPROVED_CONCEPT_SHEETS_2026-09-08.md`

This translates the owner-approved generated concept boards into the current visual authority for the TD/AE lane.

### Do not improvise away from these visual truths

- sheep remains soft, rounded, blush-pink, calm, and lovable before VFX;
- fleece motifs read as hidden musical structure inside wool, not a projected techno texture;
- palette stays sheep pink / blush / pearl / lilac / blue-violet / luminous cream, with cyan only as a restrained Melodia water-light accent;
- C / E / G use sparse distinct musical glyph identities;
- brightness is not the main harmony indicator;
- the harmonic field becomes **more coherent and organized** at C/E/G resolution;
- one major scale expansion is enough;
- after the world hit, return to intimate creature readability.

### Map the approved board directly into TD show states

```text
REST
→ ROOT_C
→ INTERVAL_CE
→ RESOLUTION_CEG
→ WORLD_HIT
→ AFTERIMAGE
```

Preferred motif vocabulary:
- Fundamental Rings;
- Spiral Resonance;
- Nodal Weave;
- Harmonic Blossom;
- Interference Lines;
- Celestial Motif.

Use the smallest useful subset. Do not stack all motifs at once.

The flagship `performance/scenes/chladni_fleece` module should make this progression immediately readable before expanding into additional concert scenes.

## Mission

Prepare the Choral Sheep capstone presentation lane so that the project can move directly from one working sheep prototype into a polished 60–90 second showcase.

The presentation grammar is:

> **Creature → Motif → Harmony → World**

Your job is to make the TouchDesigner and After Effects pipeline support that argument cleanly, deterministically, and without inventing a second gameplay system.

## Read first

Read in this order:

1. `Docs/References/ChoralSheepCapstone/BOARD_06_OWNER_APPROVED_CONCEPT_SHEETS_2026-09-08.md` — owner-approved current visual lock.
2. `Docs/Semester/CHORAL_SHEEP_CAPSTONE_SHOWCASE_PLAN_2026-09-08.md`
2. `Docs/Semester/CHORAL_SHEEP_CAPSTONE_DELIVERABLE_LEDGER_2026-09-08.md`
3. `Docs/CHORAL_SHEEP_INTEGRATION_RUNBOOK.md`
4. `Content/Melodia/Companions/ChoralSheep/ChoralSheepDefinition.json`
5. `Content/MelodiaIntegration/ResonantWorld/MotifCreatures/ChoralSheep/ChoralSheepVariants.json`
6. `Plugins/MelodiaCore/Source/MelodiaCore/MelodiaCompanionData.h`
7. `Plugins/MelodiaCore/Source/MelodiaCore/MelodiaChoralSheepActor.h`
8. `Docs/RESONANT_WORLD_SYSTEM.md`
9. `Docs/UNIVERSAL_MUSICAL_INFLUENCE_SCAFFOLD_2026-07-18.md` — **existing architecture; extend, do not replace**.
10. `Docs/Blender/MELODIA_MUSIC_SIGNAL_BRIDGE_TD_BLENDER_UNREAL_2026-08-30.md` — existing one-semantic-language / three-context contract.
11. `Docs/Handoffs/AUDIO_REACTIVE Flower_CHOP_OSC_2026-09-02.md` — existing live TD audio/OSC proof.
12. `Docs/NIAGARA_ECOSYSTEM_2026-08-09.md` — existing shared presentation parameter language.
13. `Docs/TouchDesigner/MELODIA_TD_AE_CROSS_REPO_CONTRACT_2026-09-08.md` — repo ownership and canonical TD checkout.
14. Canonical TD checkout: `C:/MelodiaTouchDesigner/td/grandmaster_melodia/`; use its current scripts/networks as implementation authority. The old `EnvironmentPortfolio/_TouchDesigner/grandmaster_melodia/` tree is historical reference only.
15. `deploy/osc_routing.json`
16. `Content/Python/osc_server.py`
17. `Plugins/MelodiaCore/Source/MelodiaCore/MelodiaRhythmReactivitySubsystem.h/.cpp`
18. `Plugins/MelodiaCore/Source/MelodiaCore/MelodiaReactiveMeshRegistrar.h/.cpp`
19. `Source/BS_GodFile/MelodiaIntegration/MelodiaAudioReactivePresentationSubsystem.h/.cpp`
20. `Source/BS_GodFile/MelodiaIntegration/MelodiaCymaticsSubsystem.h/.cpp`
21. `Source/BS_GodFile/MelodiaIntegration/MelodiaCymaticsWriterSubsystem.h/.cpp`
22. `Docs/HARMONIX_MIDI_RHYTHM_CONTRACT_2026-07-29.md`
23. `Docs/Handoffs/AAA_GN_TOUCHDESIGNER_WORLDGEN_AGENT_PROMPTS_2026-08-24.md` — reference only; do not blindly execute old scope.

## Preserve these truths

- Choral Sheep is already a data-driven non-combat companion.
- Graze / Harmonize / Guide are the authored interaction vocabulary.
- The native actor is map-agnostic.
- Presentation does not own save/progression.
- One skeletal mesh is intended to serve 12 pitch-class variants.
- Pitch class is already the motif variation axis.
- TouchDesigner is presentation/lookdev, not gameplay authority.
- Existing shared OSC routing must not be duplicated.
- Final TD output should be replayable/deterministic.
- The first capstone proof requires only one sheep.
- The hero system proof uses three sheep: C / E / G.
- Full chromatic flock is stretch scope.

## Prior-art rule — critical

Melodia already has the architecture that this capstone needs.

Do **not** create:
- a second global music-reactivity subsystem;
- a second OSC bridge;
- a second beat clock;
- a second audio MPC;
- a new generic "visual instrument" framework;
- a replacement TD grandmaster project.

Treat **Chladni Fleece as a Choral Sheep-specific consumer/profile** of:
`UniversalMusicalInfluence → MPC_Melodia_Palette → cymatics/reactive MIDs → existing TD/OSC lane`.

The work should preferentially extend the existing `grandmaster_melodia` and its reusable components/networks.

## Locked experiment authority

Before designing the TD network, read:

`Docs/Semester/CHORAL_SHEEP_CHLADNI_FLEECE_EXPERIMENT_2026-09-08.md`

**Chladni Fleece is no longer an optional brainstorm. It is the first Capstone 01 technical-art experiment.**

Gemini's TD/AE planning must explicitly support:

1. one-sheep C fleece proof;
2. C/E/G shared harmonic field;
3. deterministic replay;
4. separate fleece and world masks;
5. one world-propagation response;
6. AE breakdown: musical state → TD field → UE fleece → resolved flock → world.

Do not replace this with a generic spectrum visualizer or unrelated audiovisual concept.

## Deliverables you should prepare

### A. TouchDesigner capstone spec

Create:

`Docs/Semester/CHORAL_SHEEP_TD_NETWORK_SPEC_2026-09-08.md`

It must define:

- root network hierarchy;
- named inputs/outputs for every COMP;
- deterministic replay source;
- exact proposed replay channels;
- how C/E/G are represented;
- how harmony state is represented;
- how visual layers derive from state;
- transparent output pass list;
- live OSC mode vs replay mode;
- performance budgets;
- capture resolution / frame-rate targets;
- audit/debug views;
- failure behavior when a signal is missing.

Do not open new ports without proving an existing route cannot carry the presentation data.

### B. Replay schema

Create:

`specs/presentation/choral_sheep_capstone_replay.v1.json`

This should be a **presentation-only schema**, not save/gameplay state.

Minimum conceptual fields:

- schema/version;
- take id;
- fps;
- bpm;
- frame/time;
- beat phase/pulse;
- per-sheep id;
- pitch class;
- interaction/presentation state;
- amplitude;
- motif phase;
- group/harmony state;
- harmony tension/resolution;
- world-response presentation strength.

Provide a sample/replay fixture if useful, but do not fabricate runtime proof.

### C. TD build handoff

Create:

`Docs/Handoffs/TOUCHDESIGNER_CHORAL_SHEEP_CAPSTONE_BUILD_HANDOFF_2026-09-08.md`

It should define:
- exact TouchDesigner workspace paths;
- networks/components to create;
- files it may write;
- files it must not touch;
- how to use existing `grandmaster_melodia`;
- export/versioning expectations;
- how the first one-sheep test is run;
- how the three-sheep C/E/G test is run;
- how transparent passes are recorded.

### D. After Effects assembly spec

Create:

`Docs/Semester/CHORAL_SHEEP_AE_ASSEMBLY_SPEC_2026-09-08.md`

It must define:
- project bins;
- comp hierarchy;
- shot naming;
- expected UE inputs;
- expected TD inputs;
- 60–90 second editorial beat sheet;
- title/end-card approach;
- breakdown sequence;
- color-management assumptions;
- EXR/image-sequence intake strategy;
- matte/depth usage;
- delivery versions.

Keep the final aesthetic restrained and image-led.

### E. Shot / pass manifest

Create:

`Docs/Semester/CHORAL_SHEEP_CAPSTONE_SHOT_PASS_MANIFEST_2026-09-08.md`

For each planned shot, record:
- shot id;
- act;
- story purpose;
- UE camera/render source;
- required Unreal passes;
- required TD passes;
- AE composite name;
- audio cue;
- status;
- blocker.

Do not invent asset paths that are not verified.

### F. Capstone production README

Create:

`Docs/Semester/CHORAL_SHEEP_CAPSTONE_README.md`

This is the short human front door:
- what the capstone is;
- where the current truth lives;
- how to start TD;
- how to start AE;
- current milestone;
- next proof;
- known blockers.

## TouchDesigner design direction

Do not build generic spectrum bars.

Preferred vocabulary:
- pearl filigree;
- embroidered staff lines;
- cymatic interference;
- circular pitch constellation;
- delicate halo/rim structures;
- water-light;
- restrained note glyphs;
- soft spectral pearls.

Avoid:
- EDM equalizers;
- noisy full-screen particles;
- rainbow-for-rainbow's-sake;
- over-bloomed neon;
- effects that obscure sheep silhouettes.

## First TD prototype

Build/document toward this exact proof:

1. one sheep = pitch C;
2. Harmonize state becomes active;
3. amplitude rises;
4. wool/material resonance presentation rises;
5. one C-identifying constellation/halo appears;
6. silence/rest returns safely to baseline.

Then add E and G.

The second proof is:

> C → E → G → harmony_resolved → world_response_strength rises.

## After Effects editorial rule

The viewer must see the final art before the implementation diagram.

Opening:
- beauty;
- personality;
- wool;
- Harmonize.

Middle:
- pitch identity;
- C/E/G relationship;
- world response.

Late breakdown:
- one rig → variants;
- companion interaction contract;
- TouchDesigner replay;
- UE + TD + AE layering.

End:
- finished flock / Melusina / destination.

## Required honesty

When documentation distinguishes:
- implemented;
- source present;
- planned;
- pending owner asset;
- presentation-only;
- runtime-proven.

Do not convert a design target into a completion claim.

Current Choral Sheep source still describes final skeletal/groom beauty state as pending/optional. Respect that until a real owner-approved asset is proven.

## Stop condition

Your lane is complete when a fresh agent can open the capstone README and know:

- what the film says;
- what TD must build;
- what AE must assemble;
- what data each expects;
- what one-sheep proof comes first;
- what the C/E/G proof adds;
- which files are canonical;
- which claims are still pending.

Do not broaden into new gameplay systems or unrelated Melodia infrastructure.
