# Board 04 — TouchDesigner Harmonic Field

## Production question

**What does TouchDesigner contribute that should feel distinct from a normal Unreal VFX pass?**

## Reference language

Favor:
- live compositional geometry;
- field behavior;
- line systems;
- point lattices;
- interference planes;
- temporal feedback used with restraint;
- typography/glyphs integrated with signal state;
- screen-scale transformations.

Useful live-visual production reference:
- YOVOZOL stage visuals / VJ practice: https://yovozol.com/stage-visuals

## KEEP

- one strong field at a time;
- explicit input→output causality;
- screen-space scale changes;
- deterministic replay for final render;
- visual states that can be named and art-directed;
- transparent passes that composite cleanly in AE.

## AVOID

- spectrum bars;
- default noise TOPs as finished art;
- full-screen particles at all times;
- constant feedback trails;
- effects whose only justification is “TD can do this.”

## Choral Sheep field layers

Preferred outputs:

```text
OUT_FLEECE_C
OUT_FLEECE_E
OUT_FLEECE_G
OUT_SHARED_HARMONY_FIELD
OUT_PITCH_CONSTELLATION
OUT_WORLD_FIELD
OUT_TYPO_GLYPH
OUT_DEBUG
```

## Event states

### ROOT HIT
Large calm C structure.

### INTERVAL HIT
C/E interference.

### RESOLUTION HIT
C/E/G field locks into coherence.

### WORLD HIT
Shared field leaves the screen/overlay vocabulary and becomes an Unreal world response.

This last handoff is essential:
TouchDesigner makes the harmony **legible**.
Unreal makes it **consequential**.
