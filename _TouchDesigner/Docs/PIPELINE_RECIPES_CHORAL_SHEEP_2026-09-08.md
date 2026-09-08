# Pipeline Recipes — Choral Sheep / Melodia Concert Visuals

**Purpose:** concrete TouchDesigner build recipes grounded in current production practice.

## Recipe A — Chladni Fleece field

### Goal
Create a deterministic pitch-linked mask for fleece and world use.

### Network

```text
semantic_bus
  ↓
Select CHOP
(pitch_class, amplitude, beat_phase, harmony_tension)
  ↓
Lookup/Table
pitch_class → mode_n / mode_m
  ↓
Null CHOP FIELD_PARAMS
  ↓ parameter references
GLSL TOP CHLADNI
  ↓
Level TOP
  ↓
Lookup TOP / Ramp TOP
  ↓
Blur TOP (very small, optional)
  ↓
Null TOP OUT_FIELD
```

### GLSL basis

Use the same family already represented in Melodia cymatics:

```text
cos(n*pi*u) * cos(m*pi*v)
-
cos(m*pi*u) * cos(n*pi*v)
```

Art direction:
- pitch class chooses stable mode indices/table;
- amplitude controls reveal/intensity;
- beat phase may introduce small phase/breathing change;
- harmony tension may distort symmetry slightly;
- harmony resolution should stabilize/clarify.

Do **not** map audio Hz directly to enormous arbitrary mode counts.

## Recipe B — Concert feedback hit

Current TD concert tutorial pattern:

```text
SOURCE
→ Edge TOP
→ Feedback TOP loop
→ Lookup TOP
→ Bloom TOP
→ Displace TOP
→ Composite TOP
```

Melodia source candidates:
- pitch glyph;
- Chladni contour;
- sheep silhouette/matte;
- ornament line drawing.

Control it with:
- Trigger CHOP on show-state change;
- decay envelope;
- explicit feedback reset.

Use for a transition/hit, not the idle visual.

## Recipe C — giant pitch typography

```text
state DAT / pitch DAT
→ Text TOP or Geo Text COMP
→ Transform TOP / Render TOP
→ optional Edge
→ optional one-shot feedback
→ Level / Composite
→ OUT_GLYPH
```

Art rule:
- one glyph;
- huge scale;
- short duration;
- black-violet negative space;
- pearl/sea-cyan/lavender;
- no permanent HUD.

## Recipe D — pearl constellation / harmonic lattice

Preferred current path:

```text
semantic_bus
→ point seed / Circle POP / line source
→ Particle POP or Proximity-style POP network
→ attributes driven by pitch/harmony
→ Geometry COMP / Render TOP
→ restrained Bloom
→ OUT_MAIN
```

Alternative if POP conversion is not worth touching the current project:
- use Geometry COMP instancing driven by CHOP/TOP data.

Use particles/points to articulate structure, not fill empty space.

## Recipe E — audio-reactive shaping

Existing Melodia practice already follows:

```text
Audio
→ Filter/Spectrum
→ Analyze RMS
→ Math
→ Lag
→ Null hub
→ semantic use
```

Keep it.

Every raw audio feature should pass through:
- range normalization;
- clamp;
- attack/decay shaping;
- semantic naming.

Do not wire raw spectrum bins directly into final bloom/scale everywhere.

## Recipe F — show-state triggers

```text
state id
→ Logic CHOP / Compare
→ Trigger CHOP
→ event envelope
→ scene intensity / FX gate
```

Example:

```text
RESOLUTION entry
→ Trigger CHOP
→ 0.08s attack
→ 0.25s hold
→ 0.8s decay
→ bloom + field lock
```

Tune by eye/music; values are starting points, not canon.

## Recipe G — C / E / G shared field

Do not render three unrelated fields.

```text
FIELD_C ─┐
FIELD_E ─┼→ combine/interference → shared grade → OUT_SHARED
FIELD_G ─┘
```

Possible operations:
- multiply/add signed fields before thresholding;
- difference;
- phase-weighted combination;
- common nodal extraction.

Visual target:
C = identity.
C+E = unstable relationship.
C+E+G = coherent shared language.

## Recipe H — world-hit screen composition

```text
OUT_SHARED
→ polar/scale transform
→ one architectural-scale form
→ mask with subject-safe region
→ Composite over/behind UE beauty
→ OUT_SHOW_MAIN
```

The subject should become small relative to one giant event.

Only once.

## Recipe I — local UE texture bridge

### P0
Render/capture TD pass to image sequence for AE / UE lookdev.

### P1
Spout Out TOP only after Unreal receiver is verified.

Spout is local-machine texture sharing; it is not a network render protocol.

Never make a scene unusable when Spout is off.

## Recipe J — live-performance control

Borrow the modular-VJ pattern:
- custom UI;
- preset/state buttons;
- manual intensity knobs;
- reset;
- per-scene bypass;
- optional MIDI mapping.

The controller should expose **artist choices**, not every parameter in the network.

## Required per-scene test

Every scene must demonstrate:
1. QUIET;
2. trigger;
3. peak;
4. decay;
5. reset;
6. replay determinism;
7. bypass;
8. intended FPS in Perform Mode.
