# Cymatic Ecology — Tonight Spike Plan (2026-08-30)

**Map:** `LV_RND_CymaticEcology`
**Scope:** Stock UE5.8 only. No engine fork. No new gameplay authority.
**Hard rule:** No new clock, no regrading, no gameplay feedback path.

---

## Track A — Cymatic Ecology

### A0 — Static Field Canary

**Goal:** Verify the interference pattern reads as intentional hidden environmental physics, not generic concentric ripples.

**Deliverables:**
- Isolated R&D map `LV_RND_CymaticEcology`
- One simple field plane (flat mesh, ~10m×10m, single static mesh actor)
- Material `MI_CymaticStandingWave_Field` — analytic 4-source standing-wave interference
  - Four pulse origins as `Vector4` parameters (xy per source pair)
  - Per-source frequency (4 floats), amplitude (4 floats), phase offset (4 floats)
  - Final value = sum of `sin(2π·f·d + φ)` per source, normalized to [0,1]
  - Output drives emissive + displacement (world position offset, subtle ~2cm)
- Camera locked to overhead orthographic-ish angle, no depth-of-field
- Fixed screenshot to `Saved/Audit/RND/CymaticEcology/<timestamp>/A0_static_field.png`

**Pass criteria:** Four-source Chladni-like nodal pattern is clearly readable. No generic bullseye.

**Material parameter defaults (authored):**

| Param | Source 1 | Source 2 | Source 3 | Source 4 |
|---|---|---|---|---|
| Origin (XY) | (-3, -3) | (3, -3) | (-3, 3) | (3, 3) |
| Frequency | 1.0 | 1.3 | 0.9 | 1.1 |
| Amplitude | 1.0 | 0.8 | 0.9 | 0.7 |
| Phase | 0.0 | 0.5 | 1.2 | 2.1 |

---

### A1 — Rhythm Event Bridge

**Subsystem hook:** `UMelodiaRhythmCombatSubsystem::OnLaneHitJudged` only. No other delegate.

**New assets (presentation-only, no gameplay authority):**

#### `NDC_MelodiaRhythmPulse` (Niagara Data Channel)
- Channel type: ring buffer, capacity 4
- Payload struct `FMelodiaCymaticPulse`:
  - `Position` (FVector) — world-space origin of pulse
  - `Lane` (int32) — 0–3
  - `Grade` (uint8) — maps to `EMelodiaRhythmGrade`
  - `TimingError` (float) — ms, signed (early = negative)
  - `Phase` (float) — accumulated from subsystem beat counter
  - `PulseId` (int32) — monotonic counter, wraps at INT32_MAX

#### `BP_MelodiaCymaticPresentationBridge` (Actor Blueprint)
- Placed in `LV_RND_CymaticEcology`
- `BeginPlay`:
  1. Find `UMelodiaRhythmCombatSubsystem` via `GetGameInstanceSubsystem`
  2. Bind `OnLaneHitJudged` → `HandleLaneHit` (single binding)
  3. Store delegate handle in `BoundDelegateHandle`
- `EndPlay`: unbind using stored handle
- `HandleLaneHit(FMelodiaLaneHitResult Result)`:
  1. Write one `FMelodiaCymaticPulse` to `NDC_MelodiaRhythmPulse`
  2. Update `FieldMaterialInstance` dynamic params (see A2)
  3. No damage, no score, no state change

**Duplicate-bind guard:** `HandleLaneHit` checks `bDelegateBound` flag; `BeginPlay` sets it only once even across PIE restart. Dedicated unit test: `test_cymatic_bridge_no_duplicate_bind.py`.

---

### A2 — Live Coherence

**Field update rules (applied per pulse via `HandleLaneHit`):**

| Input | Field effect |
|---|---|
| `Lane` (0–3) | Maps to wavelength multiplier: `0→1.0, 1→1.3, 2→0.9, 3→1.1` (same as A0 defaults) |
| `TimingError` (ms) | Phase shift = `TimingError / 16.0 * π` (±16ms window → ±π/2 rad) |
| `Grade = Perfect` | Coherence factor → 1.0 (constructive, clean nodes) |
| `Grade = Great` | Coherence factor → 0.7 |
| `Grade = Good` | Coherence factor → 0.4 |
| `Grade = Miss` | Coherence factor → 0.0 + inject random phase noise on source 1 |

**Material dynamic parameters driven by bridge:**
- `PulseOrigins` (4×FVector2D)
- `Frequencies` (4×float)
- `Phases` (4×float)
- `CoherenceFactor` (float, 0–1)
- `NoiseAmount` (float, 0–1 — set to 0 on Perfect, ramps up on Miss)

**Ring buffer:** only latest 4 pulses affect field. Bridge maintains `TArray<FMelodiaCymaticPulse> RecentPulses` (max 4, pop front on overflow).

---

### A3 — Ecological Particles

**Asset:** `NS_Melodia_CymaticDust`

**Description:**
- Emitter type: GPU Sprite
- ~2000 particles max (budget: <0.5ms GPU)
- Spawn region: matches field plane bounds
- Velocity: driven by field gradient (sampled via `NDC_MelodiaRhythmPulse` or MPC)
- Visual: pearl/pollen aesthetic — small (~2cm), slight iridescent tint, soft falloff
- Nodal attraction: particles drift toward field nodes (constructive interference peaks)
- On `CoherenceFactor > 0.8`: tight clusters at nodes, slow drift
- On `CoherenceFactor < 0.2`: erratic dispersion, particle trails break up

**Capture targets:**
- `A3_perfect_streak.mp4` — 4-beat Perfect sequence, particles cluster
- `A3_miss_breakup.mp4` — Miss → particles scatter
- `A3_niagara_gpu_cost.txt` — frame time from Unreal Insights, GPU particle cost line

**Cost budget:** Niagara GPU budget ≤ 0.5ms at 1440p. Record actual in evidence manifest.

---

### A4 — OPTIONAL: Musical-Path Waveguide

**Precondition:** A0–A3 pass and time remains.

**Approach:**
- Use existing Musical Dream piano-roll spline/path (read-only reference)
- On pulse event: spawn a `NS_Melodia_PulseWavefront` Niagara emitter at pulse origin
- Emitter follows spline using UE5.8 Niagara Spline Location module
- Visual: bright ring that decays over ~2s as it travels the spline
- **No gameplay collision edits. No walkability changes. No spline modifications.**

---

## Evidence Layout

```
Saved/Audit/RND/CymaticEcology/<timestamp>/
  A0_static_field.png
  A1_bridge_bind_log.txt
  A2_coherence_demo.mp4          (optional)
  A3_perfect_streak.mp4
  A3_miss_breakup.mp4
  A3_niagara_gpu_cost.txt
  A4_waveguide_demo.mp4          (optional, if A4 attempted)
  manifest.json
```

**manifest.json schema:**
```json
{
  "timestamp": "ISO8601",
  "map": "LV_RND_CymaticEcology",
  "ue_build": "",
  "tracks_attempted": ["A0","A1","A2","A3"],
  "tracks_passed": [],
  "notes": ""
}
```

---

## Stop Rules

- A0 must pass before A1 work begins
- A1 must pass before A2 work begins
- A3 is independent of A4
- Session is successful if A0 + A1 + A2 pass with evidence

---

## What This Is Not

- Not a new rhythm authority
- Not a new clock or timing system
- Not a gameplay feedback path (no HP, no score, no state change)
- Not a new Niagara module that replaces existing particle systems
- Not a modification to `UMelodiaRhythmCombatSubsystem`
