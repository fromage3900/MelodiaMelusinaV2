# Choral Sheep — Harmonic Ecology Capstone Showcase Plan

**Status:** ACTIVE — Capstone Assignment 01  
**Date:** 2026-09-08  
**Project:** Melodia Melusina  
**Presentation spine:** **Creature → Motif → Harmony → World**  
**Primary real-time renderer:** Unreal Engine 5.8  
**Procedural audiovisual presentation:** TouchDesigner  
**Final compositing / editorial:** After Effects

## 1. Capstone thesis

The Choral Sheep are not a standalone mascot exercise. They are the first compact proof of Melodia's broader design thesis:

> **A creature carries musical identity. Musical relationships become world relationships.**

The assignment should first read as a charming authored creature piece, then reveal the technical system underneath it.

The final showcase must make four ideas legible without requiring code explanation:

1. **Creature** — the Choral Sheep feels alive and lovable.
2. **Motif** — each sheep carries a pitch-class / musical identity.
3. **Harmony** — multiple sheep form an audible and visible relationship.
4. **World** — that relationship changes the Resonant World presentation.

## 2. Grounded project architecture

The showcase must extend the current Melodia contracts rather than replacing them.

Current companion facts:

- native actor: `AMelodiaChoralSheepActor`;
- data owner: `UMelodiaCompanionDefinitionAsset`;
- behavior states include Idle, Follow, Graze, Harmonize, Seek, Rest;
- authored interactions are Graze, Harmonize, Guide;
- companion is non-combat;
- base follow distance is 180 cm with 75 cm acceptance radius;
- query interaction radius is 160 cm;
- visual/rig identity belongs to the definition asset rather than level actors;
- Groom is optional and may not block base companion behavior;
- save authority is not owned by the companion presentation actor.

Current musical variation facts:

- one skeletal mesh is intended to serve the chromatic family;
- 12 pitch-class variants: C, C#, D, D#, E, F, F#, G, G#, A, A#, B;
- variant identity is material/data driven;
- current material override vocabulary includes CoatHueShift, CoatSaturation, TrimEmissive, BellToneScale;
- behavior binding already identifies pitch class as the motif cell source;
- the Resonant World contract defines motif creatures as creatures whose behavior follows a repeating rhythmic or melodic cell.

These contracts are the foundation of the capstone explanation.

## 2.5 Locked first technical-art experiment — Chladni Fleece

The first capstone technical-art experiment is **Chladni Fleece**.

Canonical spec:

`Docs/Semester/CHORAL_SHEEP_CHLADNI_FLEECE_EXPERIMENT_2026-09-08.md`

Locked progression:

```text
one sheep + C
→ pitch-linked fleece pattern
→ C + E + G
→ synchronized harmonic field
→ one world-propagation response
```

This is **not a new TD ↔ Unreal architecture**. It is the first capstone-specific consumer of Melodia's pre-existing **UniversalMusicalInfluence** spine.

Existing prior art that owns the architecture:

- `Docs/UNIVERSAL_MUSICAL_INFLUENCE_SCAFFOLD_2026-07-18.md` — project-wide rule: one music signal, MPC broadcast, generic reactive meshes, TD bridge;
- `UMelodiaRhythmReactivitySubsystem` — existing project signal object, reactive-material registration, UE→TD OSC on port 9000;
- `UMelodiaAudioReactivePresentationSubsystem` — sole continuous beat/audio writer to `MPC_Melodia_Palette` + Niagara twin;
- `UMelodiaReactiveMeshRegistrar` — existing `ReactiveToMusic` tag path for arbitrary visible mesh components;
- `UMelodiaCymaticsSubsystem` + `UMelodiaCymaticsWriterSubsystem` — existing Chladni evaluator and `MPC_Cymatics_Driver` presentation surface;
- `_TouchDesigner/grandmaster_melodia/` + `wire_audio_reactive_flower.py` — existing TD CHOP/audio/OSC implementation;
- `Content/Python/osc_server.py` + `deploy/osc_routing.json` — existing TD→UE mapping contract;
- `Docs/Blender/MELODIA_MUSIC_SIGNAL_BRIDGE_TD_BLENDER_UNREAL_2026-08-30.md` — existing principle: **one semantic music language, three execution contexts**.

Therefore Chladni Fleece should be implemented as a **specialized profile/consumer** of the existing music-reactivity architecture, not as a new visual-instrument framework. It reuses Melodia's read-only cymatics/resonance language and does not create a second music, save, or gameplay authority.

## 2.6 Cross-repo implementation boundary

The TD/AE presentation pipeline is intentionally kept separate from the Unreal game repository.

Canonical contract:
`Docs/TouchDesigner/MELODIA_TD_AE_CROSS_REPO_CONTRACT_2026-09-08.md`

- `MelodiaMelusinaV2` owns runtime/music/companion truth, schemas, and capstone evidence.
- canonical `grandmaster_melodia` Git checkout owns TouchDesigner implementation, concert visuals, replay-driven graphics, and TD capture tooling.
- After Effects owns final editorial/compositing assembly.
- the old `EnvironmentPortfolio/_TouchDesigner/grandmaster_melodia/` tree is a frozen historical mirror.
- do not copy, submodule, or fork the full TD project into this repo.

This is a coordination boundary, not a new architecture.

## 3. Tool ownership

### Unreal Engine 5.8 owns

- final authored creature/environment scene;
- camera and cinematic staging;
- character/companion animation;
- lighting;
- materials as they appear in the game;
- final world response;
- gameplay-facing companion behavior;
- MRQ beauty and utility passes.

### TouchDesigner owns

- pitch / harmony visualization;
- cymatic/interference presentation;
- deterministic replay of music/companion presentation data;
- chromatic flock identity graphics;
- spectral / pearl / staff-line overlays;
- optional live OSC preview;
- transparent presentation passes for final composite.

TouchDesigner **does not own** save, quest, travel, reward, combat, companion recruitment, or canonical world-state progression.

### After Effects owns

- final 60–90 second assembly;
- compositing Unreal and TouchDesigner passes;
- typography and explanatory graphics;
- before/after and breakdown transitions;
- selective glow / atmospheric integration;
- depth-assisted compositing where useful;
- final editorial rhythm;
- delivery masters.

After Effects should not be where the procedural system is invented.

## 4. Final film structure

Target: **60–90 seconds**.

### ACT 01 — CREATURE

Goal: audience falls in love with the sheep before seeing technical explanation.

Suggested shots:
- quiet wide or medium introduction;
- grazing idle;
- face / ears / bell close-up;
- wool/groom macro;
- Harmonize reaction;
- Melusina approaching or sharing frame.

Minimal title:

**CHORAL SHEEP**  
*Harmonic Ecology Prototype*

No graphs or code in the opening.

### ACT 02 — MOTIF

Reveal the chromatic identity system.

Start with one sheep and expand toward the pitch-class family.

Visual concept:
- a restrained pitch constellation;
- one sheep / one note identity;
- material variation;
- bell/emissive response;
- optional circular twelve-note lineup.

Important caption:

**one companion rig · twelve pitch-class identities**

The full twelve-variant lineup is a stretch presentation target, not a blocker for the first working prototype.

### ACT 03 — HARMONY

This is the capstone centerpiece.

Start with three sheep:
- C — root;
- E — third;
- G — fifth.

Sequence:
1. C sings / resonates.
2. E answers.
3. Their visual fields begin to interfere.
4. G joins.
5. The chord becomes visibly stable.
6. Fleece / bell / halo response synchronizes.
7. The environment prepares to answer.

TouchDesigner may visualize:
- note identity;
- amplitude;
- beat phase;
- motif phase;
- harmonic tension/consonance;
- group state;
- resonance strength.

The final look should remain Melodia: pearl, embroidery, staff-line, cymatic, water-light, delicate rather than EDM-spectrum spectacle.

### ACT 04 — WORLD

The complete chord produces a visible Resonant World payoff.

Candidate payoff for first capstone:
- water cymatic pattern resolves;
- pearl/reef forms bloom;
- a traversal path emerges;
- Starskiff mooring / destination responds;
- Melusina and the flock begin moving toward the revealed route.

This is the proof that the sheep are ecological actors, not audio switches.

## 5. Three-step production scope

### Minimum viable capstone

**one sheep + one note + visible wool/material resonance**

Required proof:
- one approved/usable sheep;
- one Harmonize animation/state;
- one musical input;
- one visible presentation reaction;
- one beauty render;
- one breakdown.

### Core capstone

**three sheep + C/E/G harmony + synchronized response**

Required proof:
- three readable identities;
- harmonic progression;
- visible group-state change;
- environmental response;
- polished short cinematic.

### Stretch capstone

**twelve-note chromatic flock**

Useful for:
- contact sheet;
- pitch-class showcase;
- technical breakdown;
- poster / portfolio layout.

Do not let twelve final variants block the three-sheep hero interaction.

## 6. TouchDesigner presentation contract

Live OSC is useful for development, but final renders should prefer deterministic replay.

Existing shared project rules remain:
- TD listener lane is already defined; do not open a second competing listener;
- existing beat pulse / beat phase and audio channels should be reused where possible;
- new capstone signals must remain presentation data.

Proposed capstone replay channels:

```text
take_frame
beat_phase
beat_pulse
measure
bpm

sheep_c_amp
sheep_c_motif_phase
sheep_c_state

sheep_e_amp
sheep_e_motif_phase
sheep_e_state

sheep_g_amp
sheep_g_motif_phase
sheep_g_state

harmony_root
harmony_quality
harmony_tension
harmony_resolved
world_response_strength
```

The exact schema should be frozen before final render.

### Suggested TD network

```text
/project1/choral_sheep_capstone
  /control
  /source_replay
  /pitch_identity
  /harmony_analysis
  /cymatic_field
  /wool_resonance
  /constellation
  /pearls_stafflines
  /composite_preview
  /record
  /audit
```

Each network should expose a clear OUT operator and avoid hidden cross-network expressions.

## 7. Unreal render package

Render two families.

### Beauty

Use normal cinematic presentation:
- final lighting;
- final PPV;
- temporal effects;
- motion blur where desired;
- DOF where desired;
- final materials.

Prefer image sequences for final-quality delivery.

### Utility

Capture only what the AE composite actually needs:
- object/matte separation;
- world depth;
- motion vectors where usable;
- unlit / lighting-only or material breakdown frames as useful;
- viewport/process evidence.

Do not compromise the beauty render to force every utility into one pass.

## 8. TouchDesigner output package

Keep presentation elements separate for compositing.

Target outputs:

```text
TD_PitchConstellation
TD_CymaticField
TD_HarmonicLines
TD_SpectralPearls
TD_NoteGlyphs
TD_ResonanceHalo
TD_DebugReference
```

Prefer transparent image sequences where appropriate.

Final TD renders should be replay-driven rather than dependent on a perfect live performance.

## 9. After Effects assembly structure

Recommended project bins:

```text
01_UNREAL_BEAUTY
02_UNREAL_UTILITY
03_TD_RESONANCE
04_TD_GRAPHICS
05_BREAKDOWNS
06_FINAL_COMPS
07_AUDIO
08_DELIVERY
```

Recommended comp hierarchy:

```text
CAPSTONE_MASTER
  ACT01_CREATURE
  ACT02_MOTIF
  ACT03_HARMONY
  ACT04_WORLD
  TECH_BREAKDOWN
  END_CARD
```

Compositing priorities:
- preserve the Unreal image first;
- integrate TD elements into world depth and perspective where possible;
- keep typography sparse;
- reserve technical diagrams for the breakdown section;
- use effects to clarify musical structure, not to hide weak renders.

## 10. Required showcase shots

### Beauty set

1. Sheep hero portrait.
2. Wool/groom macro.
3. Graze or idle personality shot.
4. Harmonize close/medium.
5. Three-sheep chord composition.
6. Cymatic/world-response wide.
7. Melusina + flock + destination final wide.

### Breakdown set

1. Rig / skeletal overview.
2. One mesh → variant identity demonstration.
3. Pitch-class family / contact sheet.
4. Companion state diagram: Graze / Harmonize / Guide.
5. TD replay/network diagram.
6. C → E → G harmony build.
7. Unreal beauty vs TD presentation vs final AE composite.
8. World-response logic diagram.

## 11. Capstone visual rule

The final piece should read in this order:

**cute creature → musical idea → system discovery → impossible world payoff**

Do not begin with software.

Do not present a wall of nodes before the viewer understands why the system is delightful.

## 12. Evidence / output structure

Suggested working output:

```text
Saved/SemesterEvidence/2026-W37/ChoralSheep/
  creature/
  motif/
  harmony/
  world/
  td/
  ae/
  breakdown/
```

Suggested TD export area:

`_TouchDesigner/exports/choral_sheep_capstone/`

Suggested final delivery staging:

`Saved/Capstone/ChoralSheep/`

## 13. First milestone

The first milestone is intentionally tiny:

> **One approved Choral Sheep performs Harmonize and produces one clearly visible pitch-linked material/wool response.**

No flock AI.
No full twelve-note lineup.
No final world transformation.
No new save/progression system.

Once this works:
- add E;
- add G;
- detect/present the chord;
- add the world payoff.

## 14. Definition of capstone-ready

The assignment is ready for final editorial when:

- one sheep beauty shot is genuinely portfolio quality;
- three-sheep harmony reads without explanatory text;
- the environment response is clearly caused by the harmony;
- TD replay reproduces the final presentation deterministically;
- UE beauty and utility passes are organized;
- AE project can be rebuilt from source sequences;
- technical breakdown mirrors real project architecture;
- no showcase claim exceeds the implemented proof.
