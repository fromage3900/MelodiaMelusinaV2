# Melodia World Compiler — Tomorrow Scaffold Plan

**Date:** 2026-08-30  
**Status:** dated implementation handoff for the next PC session  
**Branch:** `docs/2026-08-29-character-p1-p2-canon-audit` / PR #28  
**Companion docs in this PR:**

- `Docs/Houdini/MELUSINA_HOUDINI_UE58_TECHNICAL_RESEARCH_2026-08-30.md`
- `Docs/Houdini/MARA_P0_P3_HOUDINI_EXECUTION_PLAN_2026-08-29.md`
- `Docs/Houdini/LATE_MONOLITH_VISUAL_ESCALATION_BIBLE_2026-08-29.md`
- `Docs/Research/INFINITY_NIKKI_UE5_TRANSLATION_FOR_MELODIA_2026-08-30.md`
- `Docs/Research/UE58_EXPLORATION_WORLD_BUILDING_RESEARCH_2026-08-29.md`
- `Docs/RIDER_JUNIE_UNREAL_WORKFLOW_2026-08-28.md`

This document is the **tomorrow-on-PC handoff**, not the full canonical Houdini bible. If this proves useful, extract the stable contracts into an undated canonical doc later. Keep this file as a dated execution record.

---

# Executive decision

The highest-leverage first prototype is:

```text
MIDI_WORLD_GRAMMAR
```

Reason: the project already has the nearest verified foothold here. Current repo/PR context includes a Blender 5.2 Geometry Nodes instrument handoff with `roll_field.py`, a `melodia_roll_field_v1` JSON contract, 222-cell MIDI-derived walkable fields, Blender GN consumers, and planned UE PCG sidecar import. That means tomorrow can produce a meaningful proof without starting from zero.

Do **not** start by building a full Monolith world compiler. Build the smallest pipeline where:

```text
MIDI / roll field
    -> Houdini HDA reads data
    -> emits geometry + attributes + PCG points
    -> Unreal receives a baked/static result
    -> verification proves the contract
```

Then `MONOLITH_INFLUENCE` can reuse the same field/attribute/export architecture. `REGION_HISTORY` should remain design/schema-only tomorrow.

---

# Core doctrine

```text
Houdini authors impossible evidence.
Unreal decides when the player experiences it.
Blender supplies authored beauty and reusable kit pieces.
```

Houdini is an **offline/editor-time procedural compiler**, not a shipping runtime dependency.

## Cook/runtime boundary

| Work type | Owner | Tomorrow status |
|---|---|---|
| MIDI parse / musical cells | Existing Blender/Python toolchain | reuse, do not rewrite |
| HDA graph / SOP attribute logic | Houdini | scaffold |
| Batch variation generation | PDG/TOPs | design only unless trivial |
| Terrain deformation fields | Houdini HeightFields/VDB/SDF | stub only |
| Runtime state, gameplay, saves | Unreal | no new runtime system tomorrow |
| Runtime scatter/streaming | UE PCG / World Partition | consume later; do not migrate |
| Niagara reaction | Unreal | consume attributes later |
| Hero mesh polish | Blender/ZBrush | unchanged tomorrow |
| Generated mesh outputs | baked/cached | small test assets only |

No feature tomorrow should require Houdini to be installed on the player machine or running during gameplay.

---

# Why Infinity Nikki matters here

The Infinity Nikki comparison is a production warning, not a cloning target.

Public Unreal/Infold material shows Infinity Nikki solved open-world fashion by combining:

- UE cloth workflow and Chaos-style garment categorization;
- versatile fabric master materials;
- proprietary OIT for sheer fabric;
- proprietary skeletal-chain / clipping solutions;
- GPU-driven vegetation/instance rendering;
- Virtual Heightfield Mesh and Virtual Texturing optimizations;
- precomputed expensive wardrobe intersection data.

Melodia translation:

```text
Do not clone their proprietary tech.
Copy the layering pattern.
Precompute expensive relationships.
Scale complexity by screen importance.
Treat outfit abilities as exploration verbs.
Then go further: make outfits and music change the world's procedural grammar.
```

For tomorrow, that means:

1. precompute/cook the geometry result rather than dynamically solving it in runtime;
2. emit semantic metadata instead of only triangles;
3. keep Unreal as the responsive/live layer;
4. avoid general wardrobe/terrain/renderer rewrites;
5. make the proof player-facing enough to justify Houdini.

Infinity Nikki's observed design behavior: outfits create exploration verbs.  
Melodia's differentiator: outfits/music define **which procedural interpretation of reality is active**.

---

# The three Melodia-specific Houdini systems

## 1. `MIDI_WORLD_GRAMMAR`

**Goal:** turn music into spatial grammar rather than one-note-one-cube novelty.

Initial input:

```text
melodia_roll_field_v1 JSON
```

Initial output:

```text
- traversable block/bridge geometry
- path spline
- module placement points
- material family attributes
- PCG point cloud candidate
- debug labels / audit report
```

Suggested mapping:

| Musical signal | Spatial meaning |
|---|---|
| pitch | elevation / tier / vertical register |
| velocity | mass, thickness, brightness, decoration intensity |
| duration | module length / footprint / column height |
| beat index | grid x or path time |
| bar index | neighborhood/phrase segment |
| channel/instrument | module family / material family |
| chord density | support structure density |
| dissonance | fracture/tilt/noise amplitude |
| cadence/resolution | bridge closure / stable platform |
| accidental | alternate material marker / unsafe edge / ornament |

**Tomorrow proof:** generate a small walkable MIDI bridge/stair/island from one known roll-field file, with attributes that Unreal can later consume.

## 2. `MONOLITH_INFLUENCE`

**Goal:** hidden anatomy/influence fields procedurally affect terrain, water, ecology, roads, settlement placement, and foreshadowing.

Tomorrow scope: **schema and empty HDA shell only**, unless the MIDI proof finishes early.

The reusable pattern should be:

```text
hidden anatomy curves / proxy mesh / SDF
    -> influence field
    -> terrain mask
    -> water/current mask
    -> vegetation orientation mask
    -> route/road bias
    -> PCG point metadata
    -> debug heatmap
```

Example attributes:

```text
melodia_system = "monolith_influence"
monolith_id = "sea_above" | "faraway_mother" | "god_that_molts" | "horizon_eater"
influence = 0.0..1.0
anatomy_role = "rib" | "membrane" | "tendon" | "molt_shell" | "mouth_edge"
foreshadow_level = 0..5
world_state_tag = "water_may_be_anatomy"
```

Do not deform production maps tomorrow. Use a sandbox grid or tiny imported landscape patch.

## 3. `REGION_HISTORY`

**Goal:** generate present-day ruins and settlements from layered events rather than scatter damage randomly.

Tomorrow scope: schema only.

Proposed event model:

```json
{
  "schema": "melodia_region_history_v1",
  "region_id": "test_midi_islet",
  "events": [
    {"year": -500, "type": "settlement_seed", "culture": "shore_listener"},
    {"year": -320, "type": "water_shift", "strength": 0.3},
    {"year": -140, "type": "monolith_influence", "monolith_id": "sea_above", "strength": 0.45},
    {"year": -60, "type": "flood", "sediment": 0.7},
    {"year": 0, "type": "present"}
  ]
}
```

This should later feed Houdini rules for roads, walls, ruins, sediment, material aging, and reuse. Do not implement the simulation tomorrow.

---

# Data contract v0

Tomorrow should establish one neutral sidecar that both Houdini and Unreal can understand.

## Input sidecar: `melodia_roll_field_v1`

Reuse existing project format. Do not replace it.

Minimum expected fields per cell:

```json
{
  "schema": "melodia_roll_field_v1",
  "bpm": 128,
  "cells": [
    {
      "x": 0,
      "y": 0,
      "beat": 0,
      "bar": 0,
      "pitch": 60,
      "velocity": 96,
      "duration_beats": 1.0,
      "walk": 1.0,
      "is_accidental": false,
      "channel": 0
    }
  ]
}
```

## Houdini point attributes

Use stable, lowercase attributes. Avoid clever names.

```text
s@melodia_schema          = "melodia_world_grammar_v0"
s@melodia_system          = "midi_world_grammar"
s@source_schema           = "melodia_roll_field_v1"
s@music_phrase_id         = "phrase_000"
i@bar                     = 0
i@beat                    = 0
i@pitch                   = 60
f@velocity01              = 0.75
f@duration_beats          = 1.0
f@walkable                = 1.0
f@stability               = 0.0..1.0
f@dissonance              = 0.0..1.0
s@module_family           = "bridge" | "stair" | "pillar" | "coral" | "ruin"
s@material_family         = "shore_pearl" | "sea_glass" | "grotto_gold" | "nikki_mirage"
s@pcg_tag                 = "Melodia.Music.Geometry"
s@world_state_tag         = "MusicBuildsMatter"
```

## Output sidecar: `melodia_world_compiler_output_v0`

```json
{
  "schema": "melodia_world_compiler_output_v0",
  "generator": "HDA_MEL_MIDI_WorldGrammar_v001",
  "source": "Saved/Audit/roll_field_128BPMarpeggiomelody.json",
  "outputs": {
    "mesh": "Exports/Houdini/MIDIWorldGrammar/SM_MEL_MIDI_Bridge_Test.fbx",
    "points": "Exports/Houdini/MIDIWorldGrammar/PCG_MEL_MIDI_Bridge_Test.json",
    "audit": "Saved/Audit/houdini_midi_world_grammar_test.json"
  },
  "metrics": {
    "point_count": 222,
    "module_count": 0,
    "walkable_segments": 0,
    "max_height": 0.0,
    "cook_seconds": 0.0
  },
  "status": "PASS|FAIL|SKIPPED",
  "notes": []
}
```

---

# Recommended repo/project structure

Add folders only when they contain real files. Do not create empty folders for vibes.

```text
Docs/Houdini/
  MELODIA_WORLD_COMPILER_TOMORROW_SCAFFOLD_2026-08-30.md

Houdini/
  HDAs/
    HDA_MEL_MIDI_WorldGrammar_v001.hda
  Hip/
    WIP_MEL_MIDI_WorldGrammar_v001.hip
  PDG/
    # later only
  README.md

Exports/Houdini/
  MIDIWorldGrammar/
    # generated test outputs, commit only tiny text sidecars first

Saved/Audit/
  houdini_midi_world_grammar_test.json
```

Source-control policy:

| Asset | Commit? | Notes |
|---|---|---|
| `.md` docs | yes | small, reviewable |
| `.hda` | yes, if small and intentional | LFS if binary/large |
| `.hip` | optional / LFS | keep only canonical WIP snapshots, not every autosave |
| generated FBX | usually no tomorrow | commit only if tiny and required for proof |
| generated `.uasset` | no tomorrow unless separately reviewed | avoid binary churn |
| audit JSON | yes if small | proof over prose |
| images/video | no by default | attach only if needed |
| Houdini cache/sim/VDB | no | external/local/perforce later |

Add ignore rules later if real cache folders appear:

```text
Houdini/Cache/
Houdini/**/backup/
*.hipnc.autosave
Exports/Houdini/**/_Temp/
```

Do not add broad ignores until actual paths exist and are understood.

---

# Tomorrow PC sequence

## 0. Pull and choose branch

```powershell
git fetch origin
git switch docs/2026-08-29-character-p1-p2-canon-audit
git pull --ff-only origin docs/2026-08-29-character-p1-p2-canon-audit
```

If this PR branch is not wanted locally yet, use a new branch off current main and cherry-pick this doc later. Do not mix experimental Houdini binaries into `main` accidentally.

## 1. Verify Houdini / Unreal compatibility

Record exact local versions in a scratch note first:

```text
Houdini build:
Houdini Engine for Unreal build:
UE build: 5.8
Plugin location: project | engine
SessionSync available: yes/no
```

Official current facts to keep in mind:

- SideFX documentation currently lists Houdini Engine for Unreal binaries for UE5.8 and UE5.7.
- SideFX changelog entries show UE5.8 support added for Houdini 21.0.751 and 22.0.355 lines.
- In Houdini 21.0, the Unreal plugin had UE5.X and UE5.X-PCG variants; with UE5.7+ PCG is no longer considered experimental by Epic, and current SideFX docs note they no longer provide a separate PCG-support plugin build.

Do not commit generated content until the version pair is written down.

## 2. Locate existing roll-field fixture

Find the current generated/audit roll-field path. If missing, regenerate the known 128 BPM arpeggio fixture from the Blender/Python toolchain rather than inventing a new schema.

Expected prior convention from the GN handoff:

```text
Saved/Audit/roll_field_128BPMarpeggiomelody.json
```

If the fixture does not exist on this machine, create a tiny checked-in sample under a docs/spec path only after confirming schema from `roll_field.py`.

## 3. Create HDA shell

Name:

```text
HDA_MEL_MIDI_WorldGrammar_v001
```

Inputs:

```text
json_path
scale_xy
scale_z
module_mode = debug_blocks | bridge | stairs | coral | ruin
material_family_default
emit_pcg_points = true
emit_debug_labels = true
```

Outputs:

```text
mesh output
point output
curve/path output
attribute report
```

SOP sketch:

```text
Python SOP / JSON loader
    -> create points from cells
    -> set pitch/beat/bar/velocity attributes
    -> derive height = pitch_to_height(pitch)
    -> derive module_family
    -> Copy to Points debug modules
    -> Connect Adjacent Pieces / PolyPath for walkable path
    -> Labs/ROP export later
```

Do not make it beautiful first. Make the attribute contract visible and testable.

## 4. Export a tiny proof

Desired local outputs:

```text
Exports/Houdini/MIDIWorldGrammar/PCG_MEL_MIDI_Bridge_Test.json
Saved/Audit/houdini_midi_world_grammar_test.json
```

Optional if small:

```text
Exports/Houdini/MIDIWorldGrammar/SM_MEL_MIDI_Bridge_Test.fbx
```

Do not import a new `.uasset` into production Content tomorrow unless the text-sidecar proof already passes.

## 5. Unreal side: consume as data, not as dependency

First UE proof should be one of:

```text
A. A debug Blueprint/Editor Utility reads the JSON and prints/places debug points.
B. A PCG graph consumes imported point data in a sandbox map.
C. A static baked mesh is placed in a throwaway test level.
```

Preferred test map name:

```text
L_HoudiniWorldCompiler_Sandbox
```

Keep it out of vertical-slice maps.

## 6. Verify

Minimum proof:

```text
PASS: HDA reads fixture without manual edits
PASS: point_count matches input cell count
PASS: required attributes exist on points
PASS: no absolute workstation paths in output sidecars
PASS: generated output lands only in declared sandbox/export paths
PASS: Unreal can see/consume at least one sidecar or baked result
```

Audit JSON should distinguish:

```text
PASS
FAIL
SKIPPED
EXPECTED_FAIL
```

No optimistic console prose. This follows Rider/Junie fail-closed policy.

---

# Atomic commit train

Do not make one giant Houdini blob.

## Commit 1

```text
docs(houdini): add world compiler scaffold handoff
```

This file only.

## Commit 2

```text
chore(houdini): add project folder readme and ignore rules
```

Only if folders/files actually exist. Include cache/autosave ignores only after confirming real paths.

## Commit 3

```text
feat(houdini): scaffold MIDI world grammar HDA
```

HDA/hip source only. No UE imports.

## Commit 4

```text
test(houdini): add MIDI world grammar audit fixture
```

Tiny sample fixture + audit script/report. Must fail closed.

## Commit 5

```text
feat(worldgen): import MIDI grammar points into sandbox map
```

Only after the Houdini/text proof works. Use sandbox map only.

## Commit 6

```text
docs(houdini): record world compiler proof result
```

Short handoff with exact paths, versions, pass/fail status, and next step.

---

# Agent/Rider/Junie boundaries

Follow `Docs/RIDER_JUNIE_UNREAL_WORKFLOW_2026-08-28.md`.

Rules for tomorrow:

1. One editor/houdini writer at a time.
2. No edits to production maps.
3. No edits to production water masters.
4. No edits to Melusina/Mara hero assets.
5. No broad generated asset commits.
6. No live-UE proof claims from offline Houdini/Blender checks.
7. No hard-coded workstation paths.
8. Every commit has one semantic lane.
9. Every generated output path is declared before writing.
10. Stop after the first verified proof; do not expand into REGION_HISTORY the same day unless the HDA proof is already stable.

---

# What NOT to build tomorrow

Do not build:

- full Monolith terrain deformation;
- real-time Houdini dependency;
- Houdini-PCG integration as the first step;
- PDG farm/batch system;
- custom renderer/OIT;
- generalized clothing/body clipping solver;
- runtime procedural civilization simulation;
- production World Partition edits;
- generated 100k-instance city;
- any system that requires deleting/reparenting existing material assets;
- any tool that rewrites `deploy/surreal_architecture_gen.py` wholesale.

The win condition is not scale. The win condition is a **trusted contract**.

---

# Definition of done for tomorrow

A successful first day ends with:

```text
one HDA shell or WIP .hip
one known roll-field input
one generated text sidecar
one audit report
one sandbox Unreal visibility proof or clear SKIPPED reason
one small commit train
zero production asset churn
```

Player-facing north star:

```text
A melody becomes a traversable spatial sentence.
```

Not:

```text
A note became a cube.
```

---

# Later extraction plan

If tomorrow works, split durable guidance into:

```text
Docs/Houdini/MELODIA_WORLD_COMPILER_ARCHITECTURE.md     # canonical
Docs/Houdini/DataContracts/MEL_WORLD_COMPILER_SCHEMA.md # canonical schema
Docs/Houdini/Handoffs/<dated proof>.md                  # dated execution/evidence
```

Keep this file as the dated origin record.
