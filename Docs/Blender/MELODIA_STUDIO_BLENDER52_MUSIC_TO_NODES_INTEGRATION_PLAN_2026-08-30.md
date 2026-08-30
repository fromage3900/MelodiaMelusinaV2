# Melodia Studio — Blender 5.2 Music to Nodes Integration Plan

**Date:** 2026-08-30  
**Project:** Melodia Melusina  
**Target:** `Tools/BlenderAddons/melodia_studio`  
**Blender target:** 5.2 LTS  
**Branch:** `rnd/2026-08-30-blender52-music-gn-studio`

---

# Executive decision

Integrate Blender 5.2's native **Sound socket + Sample Sound Frequencies** Geometry Nodes workflow directly into **Melodia Studio** as a new offline-authoring lane.

Do **not** replace the existing MIDI pipeline.

Melodia Studio should expose two complementary musical representations:

```text
MIDI
  = discrete musical intent
  = pitch / velocity / duration / channel / beat position

AUDIO SPECTRUM
  = performed sonic energy
  = bass / mids / highs / timbre / transients / crescendos
```

The target architecture is therefore:

```text
                    MELODIA STUDIO
                           │
          ┌────────────────┴────────────────┐
          │                                 │
     MIDI SEMANTICS                    AUDIO ENERGY
          │                                 │
 existing midi_bridge.py          Blender 5.2 Sound socket
          │                        Sample Sound Frequencies
          │                                 │
 note / chord / beat                 spectral bands
 structure attributes              continuous amplitude
          │                                 │
          └──────────────┬──────────────────┘
                         ▼
                MUSIC REACTIVE GN
                         │
              geometry / curves /
             instances / simulations
                         │
                         ▼
                authored Melodia asset
                         │
             ┌───────────┴───────────┐
             ▼                       ▼
          Houdini                  Unreal
      optional refinement       runtime integration

UNREAL RHYTHM SYSTEM = runtime authority
```

> **MIDI tells the world what the composition is. Audio tells the world how the performance feels.**

---

# Why this should live inside Melodia Studio

The repository already has the correct foundation:

- `Tools/BlenderAddons/melodia_studio/midi_bridge.py`
  - discovers project MIDI;
  - loads the existing `Tools/midi_to_voxel/midi_voxel_v3.py` parser/generator;
  - already owns musical-to-spatial presets;
  - already provides a stable place for musical source discovery and path handling.
- `Tools/BlenderAddons/melodia_studio/studio_panel.py`
  - already exposes MIDI selection;
  - presets;
  - generation;
  - reports / QOL;
  - Blender-side asset generation.
- existing musical Geometry Nodes work already exists around instruments, terrain and procedural worlds.

Therefore do **not** create a separate `music_to_nodes` addon.

Extend Melodia Studio.

---

# Product goal

A Melodia artist should be able to open the existing **Melodia** N-panel, select a musical source, and generate a procedural structure that can react to:

- exact notes;
- chords;
- velocity;
- duration;
- beat / bar position;
- low-frequency energy;
- mid-frequency energy;
- high-frequency energy;
- overall spectral energy;
- optional custom bands.

The first version is an **authoring system**, not gameplay middleware.

---

# Phase 0 — safety and compatibility audit

Before touching production Studio code:

1. Confirm installed Blender build is 5.2.x.
2. Confirm the exact Python API identifiers for:
   - Sound sockets;
   - Sample Sound Frequencies node;
   - Sound datablock assignment;
   - FFT size / frequency-range inputs;
   - stereo/channel selection.
3. Run the current Melodia Studio offline/unit tests before modification.
4. Record baseline pass count.
5. Verify addon source-of-truth path versus `%APPDATA%` installed copy.
6. Confirm any older manually mirrored addon files are not silently shadowing repo files.

**Gate:** no implementation until baseline tests are green.

---

# Phase 1 — new module: `music_reactivity.py`

Create:

`Tools/BlenderAddons/melodia_studio/music_reactivity.py`

This module owns only **audio/spectrum authoring** and the unified music-reactive GN contract.

It must remain import-safe where practical and should avoid making existing MIDI tools depend on Blender-only APIs unnecessarily.

## Responsibilities

### Source discovery

Discover common project audio assets from known project roots, initially:

```text
Imports/Audio/
Content/MelodiaIntegration/Audio/
Content/MelodiaIntegration/Music/
```

Do not crawl the entire repository every panel draw.

Use a short-lived cache similar to the current MIDI discovery pattern.

### Audio source setup

Provide an operator/helper to:

1. select an audio source;
2. create/reuse the Blender Sound datablock;
3. optionally add it to the Video Sequence Editor for audible preview;
4. set playback sync appropriately when requested;
5. expose the sound to the generated Geometry Nodes group.

### Band presets

Start with a small, explicit Melodia preset library:

```text
MELODIA_BALANCED
  low:      40–120 Hz
  low_mid:  120–500 Hz
  mid:      500–2500 Hz
  high:     2500–10000 Hz

MONOLITH_BREATH
  body:     25–90 Hz
  pressure: 90–300 Hz
  tissue:   300–1800 Hz
  shimmer:  1800–9000 Hz

WARDROBE
  body:     60–180 Hz
  cloth:    180–1200 Hz
  trim:     1200–4500 Hz
  sparkle:  4500–12000 Hz
```

These ranges are artistic defaults, not immutable acoustic truths.

### Custom bands

After the first working version, allow 4 user-editable band ranges.

Do not begin with an arbitrary unlimited band editor.

---

# Phase 2 — Geometry Nodes contract

Create or generate one canonical group:

`MEL_MusicReactiveField_v1`

The group should **not** be a finished artwork. It is a reusable signal-preparation layer.

## Outputs / named values

Conceptual outputs:

```text
LowEnergy
LowMidEnergy
MidEnergy
HighEnergy
OverallEnergy
TransientLikeEnergy
TimeSeconds
NormalizedPulse
```

Where Blender's node system does not permit literal named field outputs in the desired way, expose these through a nested node group contract or Store Named Attribute path.

## Processing chain

Each band follows approximately:

```text
Sound
  -> Sample Sound Frequencies
  -> Map Range / Normalize
  -> optional Power / Contrast
  -> optional smoothing
  -> clamp 0..1
  -> named output
```

Avoid embedding artistic geometry directly in this signal group.

---

# Phase 3 — MIDI + audio hybrid contract

Do **not** re-parse MIDI inside the new audio module.

Use the existing `midi_bridge.py` as the MIDI authority.

Build a thin hybrid adapter layer that can expose:

```text
MIDI
pitch
velocity
duration
channel/track
beat position
phrase/chunk position

AUDIO
low energy
mid energy
high energy
overall energy
```

The important architectural rule:

> MIDI semantics and audio spectrum may influence the same geometry, but they remain independently inspectable.

Do not bake them into one opaque `MusicValue` float.

---

# Phase 4 — Melodia Studio UI

Extend `studio_panel.py` with a compact **Music Reactive Geometry** section.

Do not redesign the entire Studio UI.

## Proposed controls

```text
MUSIC REACTIVE GEOMETRY

Mode:
  [ MIDI ] [ AUDIO ] [ HYBRID ]

MIDI:
  existing Studio MIDI source

Audio:
  [ audio source dropdown ]
  [ custom file ]

Band Preset:
  Melodia Balanced
  Monolith Breath
  Wardrobe

[ Sync Audio Preview ]
[ Build Music Signal Rig ]

Template:
  Rhythm Garden
  Tide Seam
  Filter Filaments
  Cloth Tension

[ Generate Study ]
```

Advanced foldout:

```text
FFT size
window function
band ranges
normalization gain
smoothing
seed
```

Keep advanced DSP-looking controls hidden by default.

---

# Phase 5 — first four Melodia templates

The new workflow becomes valuable only when it generates Melodia-shaped results.

## Template A — `MEL_GN_RhythmGarden_v1`

Purpose: first proof.

MIDI mapping:

```text
pitch       -> vertical / radial placement
velocity    -> stem radius
note length -> filament length
chord       -> cluster
channel     -> species / material family
```

Audio mapping:

```text
low         -> macro breathing
low-mid     -> stem width modulation
mid         -> branching density
high        -> bloom / micro-instance density
```

Target read:

**music-grown ecology**, not spectrum visualizer.

---

## Template B — `MEL_GN_TideSeam_v1`

Use for Sea Above / Shorelistener studies.

MIDI:
- melody defines seam path / punctuation;
- sustained notes extend seam segments;
- chord changes create branching junctions.

Audio:
- low energy drives broad displacement;
- mids drive wave/tension variation;
- highs drive pearl/shimmer detail.

Export target:
- curve;
- mesh ribbon;
- optional masks/attributes for Houdini or UE.

---

## Template C — `MEL_GN_FilterFilaments_v1`

Use for Horizon Eater.

MIDI:
- phrase/chord structure defines large filter plate/filament organization.

Audio:
- low = inhale / macro flex;
- mids = filament compression;
- highs = micro-vibration / particulate attachment density.

This is an **offline authored reference / bake candidate**, not the runtime Horizon Eater controller.

---

## Template D — `MEL_GN_ClothTensionStudy_v1`

Use for Faraway Mother.

MIDI:
- notes create anchors / seam events;
- duration creates tension-line reach;
- velocity controls local pull strength.

Audio:
- low frequencies drive broad fold contraction;
- mids drive tension migration;
- highs drive fibers/prayer-strip response.

This can feed Blender 5.2 node-based physics experiments later, but initial v1 should work without depending on experimental simulation nodes.

---

# Phase 6 — export / handoff contract

Every generated study must be able to leave Blender as normal authored data.

Priority outputs:

1. mesh;
2. curves;
3. point/instance realization where needed;
4. vertex attributes;
5. shape keys / animation where appropriate;
6. Alembic or VAT source only when motion justifies it;
7. JSON sidecar for source/music metadata.

## Proposed sidecar

`melodia_music_geo_v1`

Example conceptual schema:

```json
{
  "schema": "melodia_music_geo_v1",
  "source_midi": "...",
  "source_audio": "...",
  "mode": "hybrid",
  "tempo_bpm": 128.0,
  "band_preset": "MONOLITH_BREATH",
  "bands_hz": {
    "low": [25, 90],
    "low_mid": [90, 300],
    "mid": [300, 1800],
    "high": [1800, 9000]
  },
  "template": "MEL_GN_FilterFilaments_v1",
  "seed": 17
}
```

Do not serialize expensive per-frame FFT arrays unless a later use case proves they are needed.

---

# Phase 7 — Unreal integration boundary

Critical rule:

```text
Blender audio analysis = AUTHORING
Unreal rhythm subsystem = RUNTIME TRUTH
```

Blender-generated musical forms may enter UE as:

- Static Meshes;
- splines/curves converted to UE-friendly data;
- textures/masks;
- VAT;
- Alembic/Geometry Cache for authored cinematic use;
- JSON metadata for provenance.

They must **not** create:
- a second gameplay beat clock;
- a second BPM authority;
- runtime audio FFT dependency for core rhythm gameplay;
- duplicated Combo/Crescendo logic.

The existing Unreal rhythm subsystem remains authoritative.

---

# Phase 8 — Houdini relationship

Do not frame Blender Music to Nodes as competition with Houdini.

Use this ownership split:

```text
Blender 5.2 Music GN
  -> fast musical sketching
  -> direct artist experimentation
  -> spectrum-reactive procedural motion/forms

Houdini
  -> heavy procedural refinement
  -> robust geometry processing
  -> anatomy/ecology consistency
  -> large variant families
  -> offline simulation/baking

Unreal
  -> runtime state
  -> rhythm authority
  -> interaction
  -> streaming
  -> presentation
```

A good path is:

```text
music -> Melodia Studio prototype -> approved form
      -> Houdini refine if necessary
      -> UE asset/runtime presentation
```

Do not force every Music GN output through Houdini.

---

# Phase 9 — implementation file plan

## New

```text
Tools/BlenderAddons/melodia_studio/music_reactivity.py
Tools/BlenderAddons/melodia_studio/music_templates.py
Tools/BlenderAddons/melodia_studio/tests/test_music_reactivity.py
Tools/BlenderAddons/melodia_studio/tests/test_music_template_contracts.py
```

Potentially later:

```text
Tools/BlenderAddons/melodia_studio/music_export.py
```

## Modify

```text
Tools/BlenderAddons/melodia_studio/__init__.py
Tools/BlenderAddons/melodia_studio/studio_panel.py
```

Only modify `midi_bridge.py` if a tiny reusable semantic-event API is genuinely missing.

Do not rewrite it.

---

# Phase 10 — test plan

## Offline / Python tests

Must test:

- audio discovery paths;
- band preset validation;
- frequency ranges are ordered and non-negative;
- sidecar serialization;
- hybrid source metadata;
- no-bpy import safety for pure helper sections where practical.

## Blender headless tests

On Blender 5.2:

1. create a GN tree containing Sound input path;
2. create four Sample Sound Frequencies nodes;
3. assign a known WAV/FLAC source;
4. evaluate at multiple frames;
5. confirm energy changes over time;
6. build `MEL_MusicReactiveField_v1`;
7. build Rhythm Garden template;
8. verify generated geometry has non-zero verts/curves;
9. save/reload blend and confirm sound link persists;
10. verify current existing Studio tests still pass.

## Interactive test

Use one real Melodia phrase.

Success means:

- audible playback can be synced;
- geometry visibly distinguishes low vs high-frequency events;
- MIDI and audio lanes can be toggled independently;
- hybrid result is more expressive than either source alone;
- no manual node surgery is required after using the Studio operator.

---

# Day-0 implementation order

## 0. Baseline — 15 min

- update local branch;
- run existing Studio tests;
- record Blender version;
- identify a short MIDI + rendered audio pair from the same phrase.

## 1. API proof — 30–45 min

Create the smallest possible throwaway script that:

- loads sound;
- creates a Geometry Nodes group;
- adds Sample Sound Frequencies;
- samples one band;
- drives one cube/curve parameter.

**Do not touch the Studio UI until this works.**

## 2. Signal group — 30–45 min

Build `MEL_MusicReactiveField_v1` with 4 bands.

## 3. Rhythm Garden — 45–60 min

Reuse existing MIDI source + new audio field.

Produce one compelling geometry proof.

## 4. Studio UI — 30–45 min

Add only:

- Audio source;
- Mode;
- Band preset;
- Build Music Signal Rig;
- Generate Rhythm Garden.

## 5. Tests + decision — 30 min

Run existing tests plus new music tests.

Record:

```text
setup friction
interactive speed
MIDI value
spectrum value
hybrid value
export quality
runtime independence
ADOPT / PARK / REJECT
```

---

# Acceptance criteria for v1

The feature is **ADOPTED** only if all are true:

- existing Melodia Studio MIDI generation still works;
- existing tests do not regress;
- one audio file can drive GN without manual node editing;
- one MIDI + audio pair can generate a hybrid procedural structure;
- artist can change source/preset from Melodia Studio UI;
- the result can be baked/exported without Blender runtime dependency;
- Unreal remains runtime rhythm authority;
- the workflow makes a compelling Melodia form in under 10 minutes after setup.

---

# Immediate first benchmark

Use the first integration test to generate:

## `MEL_GN_RhythmGarden_v1`

Visual target:

> A living field of translucent stems / ribbons / coral-like structures whose **architecture comes from MIDI** while their **breathing, bloom and micro-detail come from the actual audio performance**.

The benchmark should answer one question:

> **Does hybrid musical data create environment forms that feel composed rather than merely audio-reactive?**

If yes, promote Music to Nodes into Melodia Studio's normal procedural-authoring toolkit.

---

# Follow-up Melodia applications

Once v1 is stable:

- **Sea Above:** Tide Seam / Bell interference authoring;
- **Faraway Mother:** rhythm-driven cloth tension and fold studies;
- **God That Molts:** pulse-driven biological layer growth;
- **Horizon Eater:** filter filament / feeding-field authoring;
- **wardrobe:** trim, embroidery and silhouette studies from musical phrases;
- **musical instruments:** structural MIDI + timbral audio response;
- **SpeedTree/Houdini ecology:** use generated curves/masks as authored seeds, never as runtime authority.

---

# Explicit non-goals

Do not build:

- a DAW;
- a new runtime rhythm engine;
- a general MIDI editor;
- arbitrary node synthesis UI;
- a full FFT cache format;
- automatic finished Monolith generation;
- direct Blender-to-gameplay state coupling;
- a replacement for Houdini.

---

# Final architecture rule

> **Melodia Studio turns music into authored form. Houdini turns authored rules into coherent worlds. Unreal decides how those worlds respond to the player.**
