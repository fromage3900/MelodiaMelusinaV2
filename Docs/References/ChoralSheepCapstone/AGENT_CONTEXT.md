# Choral Sheep — Mandatory Agent Context

**Date:** 2026-09-08  
**Status:** CANONICAL READ-FIRST CONTRACT  
**Scope:** Choral Sheep / Chladni Fleece / Nikki Cymatics / TouchDesigner / Blender Geometry Nodes / UE5.8 capstone work

This file exists so a fresh agent cannot accidentally redesign the Sheep, revive stale blockers, duplicate gameplay authority, or misread the laptop Geometry Nodes lane.

## Read order — mandatory before making changes

1. `Docs/Art/VISUAL_REFERENCE_INDEX.md`
2. `Docs/References/ChoralSheepCapstone/REFERENCE_MANIFEST.md`
3. `Docs/References/ChoralSheepCapstone/BOARD_01_CREATURE_FLEECE.md`
4. `Docs/References/ChoralSheepCapstone/BOARD_02_CHLADNI_PATTERN_LANGUAGE.md`
5. `Docs/References/ChoralSheepCapstone/BOARD_03_HYPERPOP_RAVE_CONCERT_DRAMATURGY.md`
6. `Docs/References/ChoralSheepCapstone/BOARD_04_TD_HARMONIC_FIELD.md`
7. `Docs/References/ChoralSheepCapstone/BOARD_05_CAMERA_COMPOSITE.md`
8. `Docs/References/ChoralSheepCapstone/BOARD_06_OWNER_APPROVED_CONCEPT_SHEETS_2026-09-08.md`
9. `Docs/References/VisualBoards/2026-09-08/ChoralSheep/choral_sheep_creature_fleece.webp`
10. `Docs/References/VisualBoards/2026-09-08/ChoralSheep/choral_sheep_chladni_fleece.webp`

For current execution, also read:
- `Docs/CHORAL_SHEEP_DIRECT_PLAN_2026-09-08.md`
- `Docs/Semester/CHORAL_SHEEP_DAY1_EXECUTION_PLAN_2026-09-08.md`
- `Docs/Semester/CHORAL_SHEEP_CAPSTONE_SHOWCASE_PLAN_2026-09-08.md`

## Visual authority

**Board 06 + the two committed Choral Sheep WebP boards are the owner-approved visual lock.**

Boards 01–05 are analytical/research translation rules. They support the visual lock; they do not authorize replacing it with generic fantasy sheep, generic rave imagery, or arbitrary concert branding.

Core identity:
- lovable creature readability before VFX;
- soft rounded fleece and calm silhouette;
- blush / pearl / lilac / luminous-cream material language;
- restrained cyan water-light accent;
- Chladni / cymatic pattern logic;
- pitch and harmonic identity;
- Melodia pearl / water / embroidery / musical language;
- hyperpop concert **timing and dramaturgy**, not copied branding.

Rule:

> **Steal the timing, not the branding.**

## Material authority — non-negotiable

**THE APPROVED NIKKI-DERIVED CYMATICS MATERIAL MUST BE USED FOR FINAL CHORAL SHEEP LOOKDEV AND P0/CAPSTONE PROOF.**

Current route:

```text
MI_ChoralSheep_Body
  → M_Master_Toon_Character

MI_ChoralSheep_Body_Chladni_C
  → inherits MI_ChoralSheep_Body
  → consumes T_Chladni_C_ROOT
```

Chladni Fleece is musical structure emerging **through** the approved Nikki character-material language, not a replacement shader.

Do not:
- revive `M_Chorus_Wool_Master` as the P0/final authority;
- reparent Sheep to water, landscape, or unrelated material masters;
- substitute a generic toon/PBR material for the approved Nikki path;
- turn Chladni into pasted glowing swirls or generic audio-reactive noise.

Prefer parameterized visual response driven by real musical/game semantics such as pitch class, Harmonize state, harmonic intensity, beat phase, resonance state, and world-response strength.

## Gameplay authority

World-building / chapter / cymatics / TD visual contract (stacked with this file; does not replace Board 06 or the Nikki material lock):

`Docs/WorldBuilding/WORLD_BUILDING_SOURCE_OF_TRUTH.md`

Use this mental model:

```text
C++ owns gameplay truth
  → Blueprint connects / assembles / presents
    → Materials + Niagara + audio visualize state
      → TouchDesigner performs / editorializes signal
```

C++ decides whether Harmonize, reward, traversal, companion state, persistence, or other gameplay facts are true.

Blueprints may wire and present those facts.

Materials, Niagara, audio, and TouchDesigner may react to those facts. They do not independently create gameplay truth.

Example:

```text
C++: Harmonize=true, PitchClass=C, Resonance=0.72
  → Blueprint / MID / MPC update
    → Nikki Cymatics fleece response
    → Niagara / audio / TD harmonic-field response
```

## TouchDesigner authority

TouchDesigner is the real-time **visual instrument / signal laboratory**, not the gameplay brain.

It may consume:
- audio;
- MIDI;
- OSC;
- deterministic replay;
- game-semantic events.

It may create:
- Chladni fields;
- harmonic interference;
- masks;
- transparent overlays;
- concert visuals;
- editorial graphics;
- deterministic presentation passes.

It must not own:
- save state;
- rewards;
- quest truth;
- companion recruitment;
- traversal unlocks;
- canonical combat/rhythm outcomes.

Reuse the existing semantic music / OSC architecture. Do not create a second bridge, beat clock, global reactivity subsystem, or replacement TD grandmaster.

## Laptop Geometry Nodes lane

`collab/laptop/longterm` is an **intentional parallel Blender / Geometry Nodes workstation lane**.

Purpose:
- allow the ASUS laptop to produce Geometry Nodes, Blender, procedural-worldbuilding, and DCC work while the main PC remains available for Unreal/render/gameplay work;
- support on-the-go procedural authoring;
- preserve longer-running GN experiments and source work until deliberately promoted.

Rules:
- do **not** classify this branch as disposable merely because it diverges from `main`;
- do **not** wholesale-merge the branch over current `main`;
- do **not** delete it during generic branch cleanup;
- promote/salvage useful GN work deliberately, in scoped batches, against current canon;
- `main` remains game/runtime truth.

Mental model:

```text
reference / design lock
  → laptop Blender / Geometry Nodes lane
  → procedural asset / tool / source
  → deliberate promotion
  → UE validation
  → runtime/render evidence
  → main
```

## Chladni / cymatics interpretation

Chladni patterns are a physically motivated subset of cymatics. Pattern identity is not arbitrary decoration.

A useful production model is:

```text
pitch / frequency
+ surface geometry
+ material properties
+ boundary conditions
+ excitation
  → standing-wave mode
  → nodal structure
  → visible Chladni pattern
```

Melodia may artistically map these ideas to note identity, instrument identity, character/material language, emotion/intensity, and ability state, while keeping the result musically legible.

## Agent stop rules

Before proposing a new Sheep system, ask:

1. Does current C++/Blueprint architecture already own this truth?
2. Is this a presentation consumer instead of a new authority?
3. Does the proposal obey Board 06 + the two WebP visual locks?
4. Does it preserve the approved Nikki Cymatics material?
5. Does it reuse existing TD/OSC/cymatics architecture?
6. Is laptop GN work being deliberately promoted rather than blindly merged?

If a task conflicts with the owner-approved visual/material lock, **preserve the lock and flag the conflict** instead of silently redesigning the Sheep.
