# Board 06 — Owner-Approved Choral Sheep Concept Sheets

**Date:** 2026-09-08  
**Status:** OWNER-APPROVED VISUAL DIRECTION  
**Use:** TouchDesigner / After Effects / Unreal presentation alignment  
**Relationship to Boards 01–05:** this sheet set converts the analytical reference boards into a concrete visual target.

## Approval

Two generated concept boards were approved by the owner on 2026-09-08:

1. **CHORAL SHEEP — Creature + Fleece Direction**
2. **CHORAL SHEEP — Harmonic Motif + Chladni Fleece**

They should be treated as the clearest current visual interpretation of the written Choral Sheep reference set.

Optimized WebP copies of both approved concept sheets are now committed on `main`:

- `Docs/References/VisualBoards/2026-09-08/ChoralSheep/choral_sheep_creature_fleece.webp`
- `Docs/References/VisualBoards/2026-09-08/ChoralSheep/choral_sheep_chladni_fleece.webp`

The committed copies are Git-friendly reference previews; the generation-session originals were higher resolution. This document remains the semantic/art-direction authority, while the WebPs are the directly viewable visual reference.

## Sheet A — Creature + Fleece Direction

### Overall page language

- off-white / ivory paper field;
- thin lavender / blue-violet drafting lines;
- large serif title + handwritten annotation language;
- clean concept-art-board framing rather than a raw moodboard;
- one dominant hero creature with smaller supporting studies;
- soft painterly pink / mauve rendering;
- restrained stars, musical marks, and tiny ornamental glyphs.

### Creature target

The approved sheep reads as:
- compact and rounded;
- soft pink / blush;
- calm, gentle, slightly ceremonial;
- simplified but not toy-like;
- large readable fleece masses;
- drooping ears;
- rounded muzzle;
- slim legs / neat hooves;
- musical curl motifs integrated into fleece form.

The sheep should feel lovable **before** any reactive effect is enabled.

### Approved supporting studies

The board includes:
- front / side / back / 3/4 turnaround;
- 12 silhouette explorations;
- calm / curious / happy / content / singing / serene expression studies;
- fleece curl close-up;
- ear-shape study;
- muzzle-shape study;
- leg / hoof study;
- wool-surface study;
- musical curl motif strip;
- dusty pink / mauve / lavender / cream palette;
- matte / painterly textile references.

### Written art-direction lock

Keep:
- lovable creature first;
- soft dusty fleece;
- simplified readable silhouette;
- musical curl language in form and detail;
- calm ceremonial presence;
- painterly softness;
- quiet material variation.

Avoid:
- noisy wool albedo;
- overlong Groom hiding the face;
- hard sci-fi linework;
- rainbow glitter everywhere;
- turning the creature into a VFX display object.

## Sheet B — Harmonic Motif + Chladni Fleece

### Hero idea

The same sheep remains readable while a pearlescent / lilac / blue-violet musical field appears through the fleece.

The effect should feel like:

> **sound finding an existing hidden structure inside the wool**

not a projected texture pasted onto the body.

### Approved transformation grammar

#### 01 — REST

- soft natural wool;
- minimal patterning;
- calm and quiet;
- creature beauty is already complete.

#### 02 — HARMONIZE C

- a single pitch becomes visible;
- faint cymatic lines appear;
- local fleece structure begins to resonate;
- brightness remains secondary to pattern identity.

#### 03 — HARMONY BLOOM

- richer Chladni / cymatic structure;
- pearl + lilac + soft blue-violet;
- multiple harmonic relationships become visible;
- patterning grows more organized;
- the sheep remains readable.

This three-state progression should directly inform the TD scene states.

## Approved fleece pattern family

The concept sheet visualizes six useful motif families:

1. **Fundamental Rings**
2. **Spiral Resonance**
3. **Nodal Weave**
4. **Harmonic Blossom**
5. **Interference Lines**
6. **Celestial Motif**

These are not six simultaneous layers.

Use them as an authored motif vocabulary and choose the smallest subset that makes C → E → G legible.

## Pitch glyph direction

The approved sheet gives C / E / G distinct vertical musical sigils.

Interpretation:
- **C** — foundation / circular root;
- **E** — third / diamond-star vertical structure;
- **G** — fifth / flowing staff-like spiral.

TD may refine these, but the glyphs should remain:
- delicate;
- legible;
- sparse;
- event-based;
- decorative rather than HUD-like.

## Scale progression

The sheet explicitly supports:

```text
A. SINGLE SHEEP
    one note / self-contained harmony

B. CHORD GROUP
    C + E + G / interlocking patterns

C. WORLD RESPONSE
    the field leaves the sheep and becomes environmental consequence
```

This maps directly onto the capstone thesis:

> **Creature → Motif → Harmony → World**

## Color / light lock

Primary family:
- sheep pink;
- blush rose;
- pearl;
- lilac;
- blue-violet;
- luminous cream.

Use cool cyan only as a restrained accent where needed to connect into Melodia's existing water-light vocabulary.

Do not let the TD pass drift into generic RGB/rainbow spectral color.

## TouchDesigner translation

Gemini / TD should treat these concept sheets as a look target for:

`performance/scenes/chladni_fleece`

The TD scene should expose at least these authored visual states:

```text
REST
ROOT_C
INTERVAL_CE
RESOLUTION_CEG
WORLD_HIT
AFTERIMAGE
```

Suggested layer mapping:

```text
REST
  no active harmonic overlay
  only subtle field ambience

ROOT_C
  fundamental rings / calm root sigil
  low-density fleece mask

INTERVAL_CE
  nodal weave / interference
  spatial instability increases

RESOLUTION_CEG
  harmonic blossom / coherent shared field
  large-scale pattern locks into order

WORLD_HIT
  shared structure exits sheep-only framing
  one environmental response becomes dominant

AFTERIMAGE
  visual field decays
  return to intimate creature readability
```

## After Effects translation

The board language should also control the breakdown graphics:

- ivory / black-violet negative space;
- lavender drafting lines;
- sparse handwritten-style annotations where appropriate;
- C / E / G glyphs as semantic events;
- close-up fleece crops;
- clean before / during / resolved comparisons;
- no software-dashboard opening;
- final creature image returns after the technical reveal.

## Use in current Gemini lane

Before building or revising the Chladni Fleece TD module, Gemini should read:

1. this document;
2. `BOARD_01_CREATURE_FLEECE.md`;
3. `BOARD_02_CHLADNI_PATTERN_LANGUAGE.md`;
4. `BOARD_03_HYPERPOP_RAVE_CONCERT_DRAMATURGY.md`;
5. `BOARD_04_TD_HARMONIC_FIELD.md`;
6. `BOARD_05_CAMERA_COMPOSITE.md`.

The owner-approved concept sheets override generic assumptions about:
- sheep silhouette;
- fleece softness;
- palette;
- Chladni visual density;
- C/E/G graphic language;
- scale progression.

Do not replace this direction with a generic VJ look.
