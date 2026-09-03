# Phase 1.4 — Widget Blueprint Wiring (Worker Spec)

## Goal

Wire `UMelodiaRhythmReactivitySubsystem::OnSignalChanged` into `WBP_ComicOrrery` and `WBP_DialogueBubble` so they react to cozy MPC parameters in real time.

## Source

All data flows from `FMelodiaRhythmReactivitySignal` (C++ struct) broadcast via `OnSignalChanged` delegate on `UMelodiaRhythmReactivitySubsystem`.

## Cozy Signal Fields (new)

| Field | Decay | Meaning |
|-------|-------|---------|
| `WarmthGlow` (0→1) | 0.8 | Rises on every beat. Gentle ambient warmth. |
| `PetalFallIntensity` (0→1) | 1.2 | Rises with combo. Petal/floating-particle speed. |
| `DreamRipple` (0→1) | 0.6 | Rises on beat + enemy intent. Subtle world ripple. |
| `EmberDance` (0→1) | 1.0 | Rises on crescendo + victory. Ember/spark float. |
| `CozyBloom` (0→1) | 1.5 | Full on victory. Warm vignette/flare burst. |

## Connection Pattern (both widgets)

1. **Get subsystem**: `GetWorldSubsystem` from `UMelodiaRhythmReactivitySubsystem` (Blueprint class).
2. **Bind to `OnSignalChanged`**: Drag off the subsystem pin, assign `OnSignalChanged` event.
3. **In the event**: Read `Signal` struct pin → route specific fields to animation/visibility.

## WBP_ComicOrrery

- Expose cosmetic float params on the widget for each cozy field.
- On `OnSignalChanged`:
  - `WarmthGlow` → Orrery ring glow opacity / emissive.
  - `PetalFallIntensity` → Petal particle rate / float speed.
  - `DreamRipple` → Ring ripple scale (0→small wobble, 1→large wave).
  - `EmberDance` → Ember spawn rate / drift speed.
  - `CozyBloom` → Full-widget warm tint/bloom overlay (lerp in/out).
- Tick-decay is handled in C++; Blueprints only need to read snapshots.

## WBP_DialogueBubble

- On `OnSignalChanged`:
  - `WarmthGlow` → Bubble background warm tint intensity.
  - `DreamRipple` → Bubble edge shimmer/ripple material param.
- Simple targeting: just these two fields; others are combat/UI focused.

## MPC Asset Edit (P0.4 — Required)

`MPC_Melodia_Palette` at `/Game/Melodia/_PROJECT/04_Materials/` needs **5 new scalar parameters**:

| Parameter | Default |
|-----------|---------|
| `WarmthGlow` | 0.0 |
| `PetalFallIntensity` | 0.0 |
| `DreamRipple` | 0.0 |
| `EmberDance` | 0.0 |
| `CozyBloom` | 0.0 |

These are written by `UMelodiaRhythmReactivitySubsystem::Publish()` every tick. Without them the MPC writes silently no-op.

## OSC Routes (if TD needs them)

Four new OSC floats (port `55555`, target `127.0.0.1`):
- `/rhythm/combo_normalized`
- `/rhythm/crescendo_normalized`
- `/rhythm/command_energy`
- `/rhythm/victory_pulse`

## Order of Operations

1. Edit `MPC_Melodia_Palette` → add 5 scalars (unblocks P0.4)
2. Open `WBP_ComicOrrery` → bind `OnSignalChanged` → route 5 fields
3. Open `WBP_DialogueBubble` → bind `OnSignalChanged` → route 2 fields
4. Verify in PIE: run a battle → observe cozy signals affecting widgets
