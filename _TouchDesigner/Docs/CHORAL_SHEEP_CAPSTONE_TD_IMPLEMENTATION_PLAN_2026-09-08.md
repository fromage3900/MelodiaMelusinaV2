# Choral Sheep Capstone — TouchDesigner Implementation Plan

**Status:** ACTIVE  
**Experiment:** Chladni Fleece  
**Show grammar:** QUIET → ROOT → INTERVAL → RESOLUTION → WORLD → AFTERIMAGE

## Phase 0 — integrate without rebuilding

Do not start with a new project.

Inside current `grandmaster_melodia`:

1. create `/project1/performance`;
2. reference existing audio / OSC inputs;
3. create a normalized `semantic_bus`;
4. create replay/live switch;
5. create show-state component;
6. create `scenes/chladni_fleece`;
7. create stable outputs.

No UE texture bridge is required for this phase.

## Phase 1 — C-note field

Inputs:

```text
pitch_class = C
harmonize_active
amplitude
beat_phase
beat_pulse
motif_phase
```

Build:
- pitch→mode lookup;
- Chladni GLSL TOP;
- soft grade;
- one pearlescent palette mapping;
- reveal envelope;
- explicit reset.

Outputs:
- `OUT_MAIN`
- `OUT_ALPHA`
- `OUT_FIELD`
- `OUT_DEBUG`

Pass:
the C pattern is recognizable as one stable visual identity at multiple amplitudes.

## Phase 2 — ROOT HIT concert moment

Add:
- one huge screen-scale version of the same C field;
- optional giant `C` glyph;
- one event-gated feedback hit;
- immediate recovery.

This is the Ninajirachi/hyperpop lesson translated into Melodia:
**graphic scale + punctuation**, not copied styling.

## Phase 3 — C/E/G

Add three pitch bases.

Do not simply crossfade.

State progression:

```text
C
→ C+E interference
→ C+E+G resolution
```

Expose:
- harmony tension;
- harmony resolved;
- shared field strength.

Pass:
the resolved state feels visually more coherent even in grayscale.

## Phase 4 — world field

Output a separate world mask.

Do not build the UE world response in TD.

TD supplies:
- shared harmonic field;
- world mask;
- intensity.

UE decides how its actual water/reef/material scene responds.

## Phase 5 — capstone render layers

Required:
- Chladni field;
- shared field;
- glyph;
- optional particle/pearl layer;
- clean debug/reference;
- final TD composite preview.

Final editorial remains AE.

## Phase 6 — optional live-show extension

After capstone proof:
- MIDI control surface;
- scene preset buttons;
- show-state UI;
- Perform Mode;
- optional DMX/sACN test;
- optional verified Spout bridge.

None are blockers for Capstone 01.

## Evidence naming

```text
TD_CF_01_QUIET
TD_CF_02_C_ROOT
TD_CF_03_C_ROOT_HIT
TD_CF_04_CE_INTERVAL
TD_CF_05_CEG_RESOLVED
TD_CF_06_WORLD_FIELD
TD_CF_07_AFTERIMAGE
TD_CF_DEBUG_SIGNAL
TD_CF_DEBUG_PERFORM
```

## Stop rule

When the C ROOT image is beautiful:

**capture it before adding E.**
