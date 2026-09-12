# Melodia TouchDesigner / OSC Signal Map Capture

**Date:** 2026-08-30  
**Purpose:** capture the existing live TouchDesigner → OSC → Unreal/MPC signal map before adding Blender 5.2 parity.

Do **not** redesign the TouchDesigner patch while filling this out. This is an inventory first.

---

## Existing Unreal semantic targets

Current verified project rhythm/material vocabulary includes:

```text
BeatPulse
BeatPhase
BPM
ComboNormalized
CrescendoNormalized
CommandEnergy
CommandPulse
BreakPulse
VictoryPulse
EnemyTension
TensionSustain
DissonanceAmount
WarmthGlow
DreamRipple
```

Shared material bus:

`/Game/Melodia/_PROJECT/04_Materials/MPC_Melodia_Palette`

Runtime authority:

`UMelodiaRhythmReactivitySubsystem`

---

# Capture table

Fill one row per actual TD/OSC signal.

| TD channel / CHOP path | OSC address | Value type | Raw range | Normalized range | Attack / smoothing | Release / lag | Unreal destination | MPC scalar / local target | Artistic meaning | Keep / rename / local-only |
|---|---|---|---|---|---|---|---|---|---|---|
| TODO | TODO | float | TODO | TODO | TODO | TODO | TODO | TODO | TODO | TODO |
| TODO | TODO | float | TODO | TODO | TODO | TODO | TODO | TODO | TODO | TODO |
| TODO | TODO | float | TODO | TODO | TODO | TODO | TODO | TODO | TODO | TODO |
| TODO | TODO | float | TODO | TODO | TODO | TODO | TODO | TODO | TODO | TODO |
| TODO | TODO | float | TODO | TODO | TODO | TODO | TODO | TODO | TODO | TODO |

---

# Required screenshots / evidence

Capture only what is useful for reconstruction/reference:

- [ ] TD network overview showing the analysis/output section
- [ ] OSC Out DAT/CHOP or equivalent address list
- [ ] one example low-frequency channel over time
- [ ] one beat/transient channel over time
- [ ] Unreal receiver / mapping view if easily accessible
- [ ] MPC scalar names actually written by the live system

Do not commit personal/private machine paths, credentials, IP addresses, or tokens.

---

# Parity questions

For each meaningful signal, answer:

### Beat
- What creates the beat pulse?
- Is it impulse-like or an envelope?
- What is its decay time?
- Does it correspond to `BeatPulse` directly?

### Phase
- Is there a normalized 0–1 beat phase?
- Does it wrap cleanly?
- Is it tempo-derived or audio-derived?

### Low-frequency motion
- Which TD band currently creates the strongest macro deformation?
- Is it closer to `DreamRipple`, local WPO, or a dedicated material parameter?

### Tension / sustained energy
- Is there an existing slow envelope that corresponds to `TensionSustain`?
- How is it normalized?

### Crescendo / musical growth
- Is `CrescendoNormalized` fed directly by TD, calculated in Unreal, or authored elsewhere?

### High-frequency detail
- Which signal drives shimmer, particles, material sparkle, or micro motion?
- Is that global or local to a lookdev setup?

---

# Blender mapping worksheet

After the existing TD map is known, fill this table.

| Shared semantic | Existing TD source | Existing Unreal destination | Blender 5.2 preview source | Blender output name | Notes |
|---|---|---|---|---|---|
| beat pulse | TODO | `BeatPulse` or TODO | MIDI transient / envelope | `Music.BeatPulsePreview` | |
| beat phase | TODO | `BeatPhase` or TODO | MIDI normalized beat | `Music.BeatPhasePreview` | |
| low energy | TODO | TODO | 40–120 Hz | `Music.Low` | |
| low-mid energy | TODO | TODO | 120–500 Hz | `Music.LowMid` | |
| mid energy | TODO | TODO | 500–2500 Hz | `Music.Mid` | |
| high energy | TODO | TODO | 2500–10000 Hz | `Music.High` | |
| crescendo | TODO | `CrescendoNormalized` or TODO | derived phrase envelope | `Music.CrescendoPreview` | |
| tension | TODO | `TensionSustain` or TODO | slow filtered envelope | `Music.TensionPreview` | |
| dream/ripple | TODO | `DreamRipple` or TODO | low-frequency slow envelope | `Music.DreamRipplePreview` | |

---

# First comparison test

Use **one identical musical phrase** across all three environments:

1. TouchDesigner live patch
2. Blender 5.2 `MEL_MusicReactiveField_v1`
3. Unreal runtime/MPC visualization

Record:

```text
Phrase / file:
Tempo:
TD preset / patch:
Blender signal preset:
Unreal test map:

Beat response parity:
Low-band parity:
Crescendo parity:
Tension parity:
High-detail parity:

What felt semantically identical:
What should intentionally differ:
What needs remapping:
```

The goal is **semantic parity**, not numerically identical curves.

---

# Do not do yet

- do not make Blender a required OSC client;
- do not reroute shipping Unreal rhythm through Blender;
- do not rename current MPC parameters just for cosmetic parity;
- do not duplicate existing TouchDesigner smoothing logic until it is understood;
- do not expose raw FFT controls in the default Studio UI;
- do not create another global material parameter collection.

---

# Optional Phase 2

Only after offline Blender music-to-geometry is useful:

```text
TouchDesigner
     |
     +--> OSC -> Unreal
     |
     +--> OSC -> Blender live-preview adapter
```

This can become a spectacular live procedural-authoring mode, but it is not required for V1.

---

> **Capture first. Align meanings second. Automate third.**
