# Melodia Studio — Blender 5.2 Music to Nodes Convergence Plan

**Date:** 2026-08-30  
**Project:** Melodia Melusina  
**Blender target:** 5.2 LTS  
**Status:** **REVISED AFTER RECENT-GIT REVIEW**  
**Planning branch:** `rnd/2026-08-30-blender52-music-gn-studio`  
**Reviewed main:** `54c94e0a5abe741316e41d80ca61e38d079fe3af`

This file supersedes the original greenfield version of the Blender 5.2 Music-to-Nodes plan.

---

# Executive decision

The original plan assumed that Melodia still needed to prove Blender 5.2 Sound sockets / `Sample Sound Frequencies`, build first-generation audio Geometry Nodes, and then wrap them in Melodia Studio.

That assumption is now stale.

Recent commits on `main` have already landed a first production-shaped audio-GN authoring stack:

- `Tools/audio_terrain_pipeline.py`
  - Blender 5.2 headless batch authoring;
  - existing `MEL_audio_spectrum_terrain`;
  - existing `MEL_audio_spectrum_towers`;
  - existing `MEL_audio_radial_field`;
  - Sound datablock input;
  - Low/High Hz inputs;
  - time sampling;
  - named `audio_amplitude` / `frequency_hz` data;
  - `.blend`, FBX and JSON handoff output.
- `Tools/stage_melodia_aaa_presets.py`
  - builds a 1920x1080 visual review stage;
  - already binds real audio to those GN groups;
  - contains Sea Above-oriented presets such as `SEA_ABOVE_FALSE_HORIZON`, `SEA_ABOVE_BELL_RIBS`, and `SEA_ABOVE_MEMBRANE`.
- `Tools/BlenderAddons/melodia_studio` is now **v1.5.0**, not the v1.3 shape this plan originally reviewed.
- `midi_bridge.py` now has AddonPreferences / `$MELODIA_PROJECT_ROOT` path authority, corrected generator wiring, D7 divisor support and expanded musical presets.
- `studio_panel.py` now has AddonPreferences, extra MIDI dirs, Tandem controls, dressing instancing, seed/budget controls and additional production modules.

Therefore:

> **Do not rebuild Blender audio analysis. Converge, productize and hybridize what already landed.**

The new target is:

```text
EXISTING MIDI SEMANTICS        EXISTING BLENDER 5.2 AUDIO GN
pitch / velocity / duration    Sound + Sample Sound Frequencies
beat / track / phrase          amplitude / frequency fields
             \                   /
              \                 /
               HYBRID ADAPTER
                     |
             Melodia-shaped GN
                     |
        ordinary authored outputs
                     |
          Houdini when beneficial
                     |
                  Unreal
             runtime authority
```

And the live-reference lane remains:

```text
TouchDesigner -> OSC -> Unreal
       |
       +---- semantic calibration / lookdev reference ----> Blender
```

TouchDesigner and Blender share **meaning**, not runtime authority.

---

# Recent Git review

## `297717cf2b56b215a10e2af5aada967646cc616e`

`feat(tools): model router, T3D injectors, materialize scripts, surreal GN, melodia studio`

### Impact on this plan

Melodia Studio itself advanced significantly.

Current main now has:

- addon version `1.5.0`;
- `gaea_panel`;
- `tandem_bridge`;
- `melodia_chrome`;
- AddonPreferences project-root behavior;
- extra MIDI search directories;
- broader musical/world-generation presets.

**Plan change:** do not fork a second Studio UI architecture or duplicate root/source discovery.

---

## `cfb446acc560265998701d23b9006db6ed5ecb63`

`feat(copernicus): AAA dress/terrain/fabric COP scaffold ...`

### Impact on this plan

This commit explicitly tracks:

- `Tools/audio_terrain_pipeline.py`;
- `Tools/stage_melodia_aaa_presets.py`;
- the new Copernicus/Houdini lookdev scaffold.

It confirms that Blender audio terrain is already considered a real authoring lane, while Houdini/Copernicus remain the stronger refinement/material-generation lane.

**Plan change:** Blender music-GN is a musical-form accelerator, not a Houdini replacement.

---

## `b7455431edb7de9ae66e02f8947be434200e4db8`

`feat(integration): Melodia core subsystems, Blueprints, narrative, and config`

### Impact on this plan

Runtime integration continues to move rapidly.

**Plan change:** keep Blender outputs intentionally boring at the UE boundary — meshes, curves, attributes, caches and metadata. Do not hard-bind authoring tooling to transient gameplay implementation details.

---

## `f729f3df97432cf39064cc1686cf37cfae12d369`

`feat(content): Sea Above reef meshes, QuillScript interpreter, P0 content tests`

### Impact on this plan

Sea Above is becoming a stronger real benchmark rather than a hypothetical demo scene.

**Plan change:** first hybrid test should use an existing Sea Above audio builder rather than inventing a generic music visualizer.

---

## Current authority documents / repo policy

`AGENTS.md` now makes the project rule explicit:

> **The current job is convergence, not construction.**

That rule applies directly here.

Do not create:

- a second MIDI parser;
- a second audio-spectrum implementation;
- a second runtime beat clock;
- a second Unreal material/rhythm bus;
- a separate `music_to_nodes` Blender addon;
- a parallel Studio panel.

---

# Branch safety

At review time:

```text
main: 54c94e0a5abe741316e41d80ca61e38d079fe3af
PR35 branch merge-base: 4dd5edb9d46c587571743be816303f0c2adb5ed9
PR35 branch: ahead 4 / behind 7 / diverged
```

This documentation branch is safe to keep for planning, but **implementation code must not begin from the old merge base**.

Before code changes:

1. update local `main`;
2. start the implementation commit train from current `main` or cleanly sync/rebase the R&D branch;
3. rerun baseline Melodia Studio tests/tools;
4. do not overwrite newer v1.5 Studio behavior with v1.3 assumptions.

No implementation should blindly cherry-pick an old `studio_panel.py` or `__init__.py` from this branch.

---

# Current authoritative Blender-side stack

## MIDI authority

`Tools/BlenderAddons/melodia_studio/midi_bridge.py`

Owns:

- project-root resolution;
- MIDI discovery;
- proven `midi_voxel_v3` bridge;
- musical-to-spatial presets;
- beatgrid/generator integration.

**Do not create a second MIDI parser.**

---

## Audio-GN authority

Existing audio builders referenced by `Tools/audio_terrain_pipeline.py`:

```text
MEL_audio_spectrum_terrain
MEL_audio_spectrum_towers
MEL_audio_radial_field
```

They come through:

```python
from surreal_arch.melodia_gn.core import GROUP_BUILDERS
from surreal_arch.melodia_gn.presets import preset_param_sets
```

The batch pipeline already injects:

```text
Sound
Time
Low Hz
High Hz
Size X M
Size Y M
Radius M
```

and records useful provenance/attributes.

**Do not reproduce these builders in `music_reactivity.py`.**

---

## Audio batch/export authority

`Tools/audio_terrain_pipeline.py`

Owns:

- headless Blender launch;
- preview/region/continent profiles;
- audio source loading;
- time samples;
- builder/preset selection;
- tile layout;
- optional FBX;
- batch and UE-handoff manifests.

Treat this as the first CLI/backend for audio-driven authoring.

---

## Review-stage authority

`Tools/stage_melodia_aaa_presets.py`

Already creates a production-shaped visual review scene and uses real audio-GN groups.

Treat this as **review/evaluation infrastructure**, not duplicate it inside Studio.

---

## Studio UI authority

`Tools/BlenderAddons/melodia_studio/studio_panel.py`

Current v1.5 panel already owns:

- MIDI selection/filtering;
- preset selection;
- generation/reporting;
- project preferences;
- Tandem controls;
- dressing controls.

Music-to-Nodes UI must be a small extension of this surface.

---

# Immediate defect found during review

`Tools/audio_terrain_pipeline.py` currently writes this UE handoff metadata:

```text
runtime_audio_authority = "MPC_Portfolio_Audio / Melodia presentation subsystem"
```

That is stale relative to the current documented UE authority:

```text
UMelodiaRhythmReactivitySubsystem
        -> MPC_Melodia_Palette
```

The Sea Above integration docs explicitly warn not to use the older `MPC_Portfolio_Audio` assumption.

## Required correction

Before promoting audio-terrain handoff as canonical:

1. search for consumers of `melodia.audio_terrain_ue_handoff.v1`;
2. if no consumer relies on the old string, correct the field;
3. if the handoff is already consumed as a contract, bump to `melodia.audio_terrain_ue_handoff.v2`;
4. add a regression assertion that generated handoffs never name `MPC_Portfolio_Audio` as current authority.

Recommended value:

```text
UMelodiaRhythmReactivitySubsystem -> MPC_Melodia_Palette
```

This metadata is descriptive only. Blender still does not control runtime rhythm.

---

# Revised architecture

```text
                              MELODIA MUSIC AUTHORING
                                       |
                 +---------------------+---------------------+
                 |                                           |
                 v                                           v
        MIDI / composition                           rendered audio/stems
                 |                                           |
          midi_bridge.py                           existing MEL_audio_* GN
                 |                                  Sample Sound Frequencies
                 |                                           |
                 +-------------------+-----------------------+
                                     |
                                     v
                         MUSIC SEMANTIC ADAPTER
                       melodia_music_signal_v1
                                     |
                  +------------------+------------------+
                  |                  |                  |
                  v                  v                  v
             Sea Above          Faraway Mother    Horizon Eater
              hybrid              hybrid             hybrid
                  |                  |                  |
                  +------------------+------------------+
                                     |
                             bake / export / cache
                                     |
                       +-------------+-------------+
                       |                           |
                       v                           v
                    Houdini                      Unreal
             refinement / simulation       runtime presentation

LIVE PARALLEL REFERENCE
TouchDesigner -> OSC -> UMelodiaRhythmReactivitySubsystem -> MPC_Melodia_Palette
        |
        +------ use as envelope/response calibration, not Blender authority
```

---

# Semantic contract

Keep the concept from the original plan, but make it an **adapter contract**, not a new FFT engine.

Canonical conceptual schema:

`melodia_music_signal_v1`

## Timing

```text
tempo_bpm
beat_phase
beat_pulse
phrase_progress
```

## MIDI semantics

```text
note_pitch
note_velocity
note_duration
track_id
normalized_beat
chord_density
```

## Audio semantics

```text
spectral_low
spectral_lowmid
spectral_mid
spectral_high
overall_energy
```

## Preview/world semantics

These are mappings, not new runtime signals:

```text
world_breath
structural_pressure
branch_energy
shimmer
```

Example:

```text
MONOLITH_BREATH
spectral_low      -> world_breath
spectral_lowmid   -> structural_pressure
spectral_mid      -> branch_energy
spectral_high     -> shimmer
```

Then an artist/preset may compare those concepts with existing UE signals such as:

```text
BeatPulse
CrescendoNormalized
TensionSustain
CommandEnergy
DreamRipple
```

Do not assume a permanent 1:1 global mapping.

---

# Revised module plan

The original plan proposed `music_reactivity.py` as the place to build audio sampling from scratch.

**Retire that responsibility.**

Preferred thin modules are now:

```text
Tools/BlenderAddons/melodia_studio/music_signal_contract.py
Tools/BlenderAddons/melodia_studio/music_hybrid.py
```

Potential later module:

```text
Tools/BlenderAddons/melodia_studio/music_export.py
```

## `music_signal_contract.py`

Owns only:

- semantic names;
- band preset definitions;
- validation;
- mapping presets;
- provenance schema helpers;
- TD/UE alias table;
- no heavy geometry creation.

It should remain mostly `bpy`-independent.

## `music_hybrid.py`

Owns:

- retrieval of existing MIDI semantic data;
- binding MIDI semantics onto or beside existing audio-GN builder outputs;
- creation of hybrid study groups;
- preserving MIDI and audio values as separately inspectable inputs/attributes;
- no second audio analyzer.

---

# Source discovery / preferences

Do not create another project-root system.

Reuse current v1.5 precedence:

```text
Melodia Studio AddonPreferences project_root
    -> $MELODIA_PROJECT_ROOT
    -> repository-relative fallback
```

Current Studio already has `midi_extra_dirs`.

Add, only if useful after testing:

```text
audio_extra_dirs
```

Use the same preferences surface and cache discipline.

Do not recursively scan the entire repository every panel redraw.

---

# Revised Studio UI

Do not add a second giant music panel.

Extend the existing Melodia Studio UI with one compact section:

```text
MUSIC HYBRID AUTHORING

Mode
  AUDIO
  MIDI
  HYBRID

MIDI
  [ reuse existing selector ]

Audio
  [ source ]

Audio Builder
  Spectrum Terrain
  Spectrum Towers
  Radial Field

Music Mapping
  Melodia Balanced
  Monolith Breath
  Wardrobe

Hybrid Study
  Sea Above Membrane
  Filter Filaments
  Rhythm Garden

[ Generate Study ]
[ Build Review Stage ]
[ Export / Handoff ]
```

Advanced controls should expose existing builder/preset parameters rather than creating new hidden duplicates.

---

# Revised implementation phases

## Phase 0 — sync + baseline

**Goal:** prevent v1.3-era planning from overwriting v1.5 work.

- [ ] work from current `main` or cleanly synced implementation branch;
- [ ] record exact Blender 5.2 build;
- [ ] record current Melodia Studio version (`1.5.0` at this review);
- [ ] run available Studio/Blender checks;
- [ ] dry-run existing audio pipeline;
- [ ] pick one real Melodia MIDI + rendered-audio pair;
- [ ] capture the exact TD OSC channels/ranges using `MELODIA_TD_OSC_SIGNAL_MAP_CAPTURE_2026-08-30.md`.

**Gate:** no new audio implementation until existing pipeline baseline is understood.

---

## Phase 1 — validate what already exists

Run the smallest existing path first:

```text
Tools/audio_terrain_pipeline.py
    --profile preview
```

Validate:

- [ ] Blender launches cleanly;
- [ ] all three `MEL_audio_*` builders resolve;
- [ ] Sound source persists in `.blend`;
- [ ] time values produce differing results where expected;
- [ ] frequency range changes alter output;
- [ ] `audio_amplitude` is present where promised;
- [ ] FBX path works when requested;
- [ ] JSON handoff is valid;
- [ ] generated output can be reopened.

Then run/stage the existing Sea Above review path.

**Gate:** if existing audio builders are broken, repair them before adding hybrid logic.

---

## Phase 2 — fix handoff authority metadata

Search current repo for consumers of:

```text
melodia.audio_terrain_ue_handoff.v1
runtime_audio_authority
```

Then:

- [ ] correct old `MPC_Portfolio_Audio` metadata;
- [ ] use current rhythm authority wording;
- [ ] bump schema if compatibility requires it;
- [ ] add regression test.

This is a small but important convergence fix.

---

## Phase 3 — create semantic contract, not another analyzer

Create:

`music_signal_contract.py`

V1 includes:

- [ ] canonical names;
- [ ] frequency mapping presets;
- [ ] normalization expectations;
- [ ] MIDI semantic names;
- [ ] TD aliases;
- [ ] UE preview aliases;
- [ ] validation helpers;
- [ ] provenance serialization.

Do **not** create new `Sample Sound Frequencies` nodes here unless the existing audio builders cannot expose the needed data.

---

## Phase 4 — hybrid adapter

Create:

`music_hybrid.py`

The first adapter should combine:

```text
MIDI STRUCTURE
+ existing audio amplitude/spectral behavior
```

without flattening them to a single number.

Desired inspectable data:

```text
Music.MIDI.Pitch
Music.MIDI.Velocity
Music.MIDI.Duration
Music.MIDI.Beat
Music.Audio.Low
Music.Audio.LowMid
Music.Audio.Mid
Music.Audio.High
```

Names may be implemented as sockets, attributes or nested-group outputs depending on the current builder architecture.

---

# First benchmark — Sea Above Membrane Hybrid

This replaces the original generic Rhythm Garden as the first infrastructure test.

Use the already-existing:

```text
MEL_audio_radial_field
SEA_ABOVE_MEMBRANE
```

as the audio half.

## MIDI contribution

Use one actual Sea Above / Melodia phrase.

Map:

```text
note / chord onset  -> radial seam or ring anchors
pitch class         -> ring family / angular offset
velocity            -> seam importance / width
note duration       -> radial persistence / segment length
phrase structure    -> macro membrane organization
```

## Audio contribution

Reuse existing spectrum behavior for:

```text
low energy      -> membrane inhale / macro swell
low-mid         -> pressure / ring thickness
mid             -> tissue rippling
high            -> pearl shimmer / micro-ridges
```

## Compare three outputs

```text
AUDIO ONLY
MIDI ONLY
HYBRID
```

The hybrid passes only if it reads as **composed biological motion**, not merely a better equalizer.

### Success question

> Does the performance animate a structure whose anatomy was authored by the composition?

If yes, the system is doing something distinctive.

---

# Second benchmark — P3 Filter Filaments Hybrid

After Sea Above passes:

```text
MIDI
  -> large filter hierarchy / plate spacing / recurring anatomy

AUDIO
  -> inhale, flex, compression, flutter, particulate micro-response
```

Output can then feed:

- Houdini curve/anatomy refinement;
- IlluGen/Niagara flow texture work;
- UE static/VAT/cache presentation.

No runtime non-Euclidean or monster simulation dependency is created.

---

# Third benchmark — Rhythm Garden

Keep `Rhythm Garden`, but demote it from infrastructure proof to **artist-facing generative template**.

It remains useful for:

- flora;
- coral;
- shell growth;
- musical shrines;
- decorative ecology;
- runtime-geometry reference.

The first version should reuse the hybrid contract proven on Sea Above rather than inventing another mapping stack.

---

# TouchDesigner / OSC integration

The existing live TD workflow is an advantage, not a fourth authority.

Use the existing capture worksheet to record:

```text
TD channel
OSC address
raw range
normalized range
attack
release / lag
Unreal target
artistic meaning
```

Then run the same short phrase in:

```text
TouchDesigner
Blender
Unreal
```

Compare semantic envelopes rather than exact sample values.

Useful parity questions:

- Does “beat pulse” feel equally sharp?
- Does “crescendo” build on a comparable time scale?
- Does low-frequency world breathing feel similarly weighted?
- Does sustained tension decay similarly?
- Does the Blender authoring preview exaggerate anything that UE later cannot reproduce cheaply?

Do not attempt sample-perfect DSP parity unless a real production need appears.

---

# Optional future live Blender lane

Only after offline hybrid authoring is stable:

```text
TouchDesigner
     |
     +--> OSC --> Unreal
     |
     +--> OSC --> Blender preview
```

This could allow live procedural Monolith lookdev.

It is **not V1** and must not become required for asset generation.

---

# Houdini / Copernicus relationship after recent commits

Recent Copernicus work makes the division clearer:

```text
Blender Music GN
    -> fast musical form / response ideation

Houdini SOPs
    -> anatomy, topology, fields, robust procedural refinement

Copernicus
    -> matched masks, material evidence, texture families

Unreal
    -> gameplay state, rhythm truth, streaming, material runtime, Niagara
```

Example:

```text
Sea Above hybrid membrane in Blender
        -> approve musical anatomy
        -> Houdini clean/refine/variant family if needed
        -> Copernicus pearl/tissue/tension masks
        -> UE ordinary assets + rhythm-driven runtime presentation
```

Do not force every Blender result through Houdini, but use Houdini when the approved study needs production robustness.

---

# Export / handoff contract

Keep conventional outputs:

1. mesh;
2. curves;
3. named attributes;
4. realized instances when needed;
5. optional FBX;
6. Alembic / VAT source only when motion requires it;
7. JSON provenance.

Proposed hybrid provenance schema:

```json
{
  "schema": "melodia.music_geo.v1",
  "source_midi": "...",
  "source_audio": "...",
  "mode": "hybrid",
  "audio_builder": "MEL_audio_radial_field",
  "audio_preset": "SEA_ABOVE_MEMBRANE",
  "hybrid_study": "SEA_ABOVE_MEMBRANE_HYBRID_v0",
  "mapping_preset": "MONOLITH_BREATH",
  "seed": 20260830,
  "runtime_authority": "UMelodiaRhythmReactivitySubsystem -> MPC_Melodia_Palette"
}
```

Do not serialize huge per-frame FFT arrays unless a later tool actually consumes them.

---

# Tests to add

## Existing-pipeline regression

- audio builders resolve;
- preview profile generates output;
- `.blend` save succeeds;
- handoff JSON parses;
- output object count > 0;
- frequency ranges are valid;
- same seed/config is deterministic where expected.

## Authority regression

Generated current-version manifests must not claim:

```text
MPC_Portfolio_Audio
```

as current runtime authority.

## Hybrid contract

- MIDI and audio fields independently inspectable;
- audio-only path still works;
- MIDI-only path still works;
- hybrid path works;
- existing MIDI generator behavior unchanged;
- existing audio builder behavior unchanged when hybrid is off.

## Blender headless

Use the **existing pipeline**, not a new throwaway API test, as the primary harness.

At minimum evaluate:

```text
T0
T1
T2
```

for one audio source and verify the intended output changes.

## Save/reload

A generated hybrid `.blend` must reopen with:

- sound source linked;
- node groups present;
- provenance present;
- no missing relative path surprises.

---

# Today's direct execution order

## 1. Sync / baseline — 15 min

- update current main locally;
- use current v1.5 Studio;
- select one MIDI + rendered-audio pair;
- confirm Blender 5.2 path;
- capture TD OSC signal names if the patch is open.

## 2. Existing audio pipeline proof — 20–30 min

Run preview mode and open the result.

No new code unless this fails.

## 3. Existing AAA stage — 20 min

Build the existing Sea Above stage and inspect:

- False Horizon;
- Bell Ribs;
- Membrane.

Pick the strongest builder/preset as hybrid host.

## 4. Authority metadata correction — 15–30 min

Audit consumer usage and fix/bump handoff schema as appropriate.

## 5. MIDI -> existing audio builder hybrid proof — 45–75 min

Do **Sea Above Membrane Hybrid v0**.

Do not build Studio UI yet.

## 6. Compare Audio / MIDI / Hybrid — 15 min

Record which one communicates:

- composition;
- performance;
- anatomy;
- Monolith character.

## 7. Studio UI hook — 30–45 min

Only if hybrid passes.

Expose the proven backend through existing v1.5 panel.

## 8. TD semantic calibration — 20–30 min

Use the same phrase and compare response curves qualitatively.

## 9. Decision log — 10 min

Record:

```text
Existing audio stack: KEEP / REPAIR
Hybrid adapter: ADOPT / PARK / REJECT
Studio exposure: ADOPT / PARK
TD parity layer: ADOPT / PARK
Houdini refinement needed: YES / NO / SOMETIMES
```

---

# What is retired from the original plan

## RETIRE

- “prove `Sample Sound Frequencies` exists” as first task;
- build a basic one-band cube demo;
- create duplicate audio source discovery from scratch;
- create a second set of audio GN builders;
- make `music_reactivity.py` own FFT construction;
- treat Rhythm Garden as first infrastructure proof.

## KEEP

- MIDI vs audio distinction;
- hybrid authoring goal;
- TD semantic bridge;
- Studio integration;
- ordinary export boundary;
- Unreal runtime authority;
- Melodia-shaped benchmarks.

## ADD

- branch divergence/sync gate;
- existing audio-pipeline baseline;
- current Studio v1.5 compatibility;
- handoff-authority metadata correction;
- semantic-contract adapter;
- Sea Above Membrane Hybrid first benchmark;
- audio/MIDI/hybrid A-B-C comparison;
- no-authority-regression tests.

---

# V1 adoption gate

The integrated Blender music workflow is **ADOPTED** only if all are true:

- current Melodia Studio MIDI generation remains intact;
- existing audio builders remain intact;
- no duplicate FFT/audio system is introduced;
- no duplicate MIDI parser is introduced;
- one MIDI + audio pair can generate a hybrid study without manual rewiring every time;
- Audio / MIDI / Hybrid can be compared independently;
- the hybrid result is visibly more authored than audio-only;
- output bakes/exports conventionally;
- manifests name current Unreal authority correctly;
- Blender is never required at runtime;
- TouchDesigner remains optional live/calibration tooling;
- compelling Melodia-shaped output can be reached quickly enough to beat doing the same study manually from scratch.

---

# Final ownership rule

> **MIDI describes the composition. Audio describes the performance. TouchDesigner teaches us how the response should feel live. Blender turns those signals into authored form. Houdini makes approved procedural ideas robust. Unreal owns the actual world.**

And, per current repository policy:

> **Converge onto what already works before constructing anything new.**
