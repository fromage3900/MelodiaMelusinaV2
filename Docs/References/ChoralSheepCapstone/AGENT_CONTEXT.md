# Choral Sheep — Durable Agent Context

**Status:** CANONICAL READ-FIRST CONTRACT  
**Scope:** Choral Sheep / Chladni Fleece / Nikki Cymatics / TouchDesigner / Blender Geometry Nodes / UE5.8 capstone work

This file prevents fresh agents from redesigning the Sheep, reviving stale blockers, duplicating gameplay authority, or misreading the laptop Geometry Nodes lane.

**For current Sheep tasks, blockers, evidence level, or next actions, read `CURRENT_STATE.md`. Do not use dated execution plans as current authority.**

## 1. Reference read order

1. `Docs/Art/VISUAL_REFERENCE_INDEX.md`
2. `Docs/References/ChoralSheepCapstone/REFERENCE_MANIFEST.md`
3. `Docs/References/ChoralSheepCapstone/BOARD_06_OWNER_APPROVED_CONCEPT_SHEETS_2026-09-08.md`
4. `Docs/References/VisualBoards/2026-09-08/ChoralSheep/choral_sheep_creature_fleece.webp`
5. `Docs/References/VisualBoards/2026-09-08/ChoralSheep/choral_sheep_chladni_fleece.webp`

Boards 01–05 remain useful analytical/research translation material, but they do not override Board 06 or the two committed owner-approved WebP boards.

## 2. Visual authority

**Board 06 + the two committed Choral Sheep WebP boards are the owner-approved visual lock.**

Core identity:

- lovable creature readability before VFX;
- soft rounded fleece and calm silhouette;
- blush / pearl / lilac / luminous-cream material language;
- restrained cyan water-light accent;
- Chladni / cymatic pattern logic;
- pitch and harmonic identity;
- Melodia pearl / water / embroidery / musical language;
- hyperpop concert **timing and dramaturgy**, not copied branding.

> **Steal the timing, not the branding.**

## 3. Material authority — non-negotiable

**The approved Nikki-derived Cymatics material path MUST be used for final Choral Sheep lookdev and capstone proof.**

```text
MI_ChoralSheep_Body
  -> M_Master_Toon_Character

MI_ChoralSheep_Body_Chladni_C
  -> inherits MI_ChoralSheep_Body
  -> consumes T_Chladni_C_ROOT
```

Chladni Fleece is musical structure emerging **through** the approved Nikki character-material language, not a replacement shader.

Do not:

- revive `M_Chorus_Wool_Master` as final/P0 authority;
- reparent Sheep to water, landscape, or unrelated material masters;
- substitute a generic toon/PBR material for the approved Nikki path;
- turn Chladni into pasted glowing swirls or generic audio-reactive noise.

Prefer parameterized visual response driven by actual musical/game semantics such as pitch class, Harmonize state, harmonic intensity, beat phase, resonance state, and world-response strength.

## 4. Gameplay authority

World/chapter/cymatics boundary: `Docs/WorldBuilding/WORLD_BUILDING_SOURCE_OF_TRUTH.md`.

```text
C++ owns gameplay truth
  -> Blueprint connects / assembles / presents
    -> Materials + Niagara + audio visualize state
      -> TouchDesigner performs / editorializes signal
```

C++ decides whether Harmonize, reward, traversal, companion state, persistence, or other gameplay facts are true.

Blueprints may wire and present those facts. Materials, Niagara, audio, and TouchDesigner may react to them. They do not independently create gameplay truth.

Example:

```text
C++: Harmonize=true, PitchClass=C, Resonance=0.72
  -> Blueprint / MID / MPC update
    -> Nikki Cymatics fleece response
    -> Niagara / audio / TD harmonic-field response
```

## 5. TouchDesigner authority

TouchDesigner is the real-time **visual instrument / signal laboratory**, not the gameplay brain.

It may consume audio, MIDI, OSC, deterministic replay, and game-semantic events. It may create Chladni fields, harmonic interference, masks, transparent overlays, concert visuals, editorial graphics, and deterministic presentation passes.

It must not own save state, rewards, quest truth, companion recruitment, traversal unlocks, or canonical rhythm/combat outcomes.

Reuse the existing semantic music / OSC architecture. Do not create a second bridge, beat clock, global reactivity subsystem, or replacement TD grandmaster.

Durable cross-repo boundary: `Docs/TouchDesigner/MELODIA_TD_AE_CROSS_REPO_CONTRACT_2026-09-08.md`.

## 6. Laptop Geometry Nodes lane

`collab/laptop/longterm` is an intentional parallel Blender / Geometry Nodes workstation lane.

Durable workstation contract: `Docs/Production/LAPTOP_PROCEDURAL_LANE_2026-09-11.md`.

Rules:

- do not classify this branch as disposable merely because it diverges from `main`;
- do not wholesale-merge the branch over current `main`;
- do not delete it during generic branch cleanup;
- promote useful GN work deliberately, in scoped batches, against current canon;
- `main` remains game/runtime truth.

```text
reference / design lock
  -> laptop Blender / Geometry Nodes lane
  -> procedural asset / tool / source
  -> deliberate promotion
  -> UE validation
  -> runtime/render evidence
  -> main
```

## 7. Chladni / cymatics interpretation

Chladni patterns are a physically motivated subset of cymatics. Pattern identity is not arbitrary decoration.

```text
pitch / frequency
+ surface geometry
+ material properties
+ boundary conditions
+ excitation
  -> standing-wave mode
  -> nodal structure
  -> visible Chladni pattern
```

Melodia may artistically map these ideas to note identity, instrument identity, character/material language, emotion/intensity, and ability state while keeping the result musically legible.

## 8. Capstone presentation thesis

The durable presentation spine is:

```text
Creature -> Motif -> Harmony -> World
```

The showcase bible may define film/shot/presentation structure, but it must not become a second current task queue. Current milestone/proof state lives only in `CURRENT_STATE.md`.

## 9. Agent stop rules

Before proposing a new Sheep system, ask:

1. Does current C++/Blueprint architecture already own this truth?
2. Is this a presentation consumer instead of a new authority?
3. Does the proposal obey Board 06 + the two WebP visual locks?
4. Does it preserve the approved Nikki Cymatics material path?
5. Does it reuse existing TD/OSC/cymatics architecture?
6. Is laptop GN work being deliberately promoted rather than blindly merged?
7. Am I reading `CURRENT_STATE.md` for current work instead of reviving a dated plan?

If a task conflicts with the owner-approved visual/material lock, **preserve the lock and flag the conflict** instead of silently redesigning the Sheep.
