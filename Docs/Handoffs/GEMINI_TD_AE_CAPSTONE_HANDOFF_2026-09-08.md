# Gemini Handoff — Choral Sheep TouchDesigner + After Effects Capstone Lane

**Date:** 2026-09-08  
**Lane owner:** Gemini  
**Scope:** TouchDesigner + After Effects planning/prep and capstone documentation  
**Do not own:** Unreal gameplay architecture, save, narrative, companion recruitment, world-state authority

## Mission

Prepare the Choral Sheep capstone presentation lane so that the project can move directly from one working sheep prototype into a polished 60–90 second showcase.

The presentation grammar is:

> **Creature → Motif → Harmony → World**

Your job is to make the TouchDesigner and After Effects pipeline support that argument cleanly, deterministically, and without inventing a second gameplay system.

## Read first

Read in this order:

1. `Docs/Semester/CHORAL_SHEEP_CAPSTONE_SHOWCASE_PLAN_2026-09-08.md`
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
13. `_TouchDesigner/README.md`
14. `_TouchDesigner/grandmaster_melodia/scripts/wire_audio_reactive_flower.py`
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
