# World Field Bus PIE — Readiness Spec (2026-09-02)

Gate: `world_field_bus_pie` · Mode: OFFLINE spec/inventory · **editor_lock: held by another agent — capture_pending_this_run**

## Single-writer contract (verified from source)

```
MusicClock (UMelodiaMusicClockSubsystem: HasMusicalTime/GetBeatPhase/GetTempoBPM)
  └─> UMelodiaAudioReactivePresentationSubsystem   <<< SOLE MPC audio writer
        └─> MPC_Melodia_Palette  [7 lanes written]
              ├─> UMelodiaCymaticsSubsystem            READ-ONLY
              ├─> UMelodiaNeuralHeroMaterialSubsystem  READ-ONLY -> writes MPC_Hero_Material
              ├─> UMelodiaCymaticsWriterSubsystem      READ-ONLY -> writes MPC_Cymatics_Driver
              └─> hero gem MI (M_Master_Toon_Universal)  READ-ONLY
```

**Writer publishes exactly (source `MelodiaAudioReactivePresentationSubsystem.cpp` L307-313):**
`GlobalReactivity, Bass, Mid, Treble, BeatPhase, BeatPulse, BeatIntensity`

**Read-only consumers request:** `BeatPulse, BassIntensity` (cymatics) · `BassIntensity, BeatIntensity, BeatPhase, BeatPulse, BeatTracker` (neural) · `BassIntensity, BeatIntensity, MidIntensity` (cymatics-writer).

### ⚠️ Honest finding — namespace is PARTIALLY MISALIGNED
Aligned across writer + all consumers: **BeatPhase, BeatPulse, BeatIntensity** only.
Missing lanes (requested, never written by the audio writer):
- **`BassIntensity`** — writer emits `Bass` instead.
- **`MidIntensity`** — writer emits `Mid` instead (cymatics-writer has a fallback).
- **`BeatTracker`** — requested by neural seam, never written by anyone.

The plan's intended contract set (plan §2 + `specs/lookdev/hero_material_mpc_contract.v1.json`) is
`{BassIntensity, BeatIntensity, BeatPhase, BeatPulse, BeatTracker}` — this does NOT match the current writer source.
**The PIE param-name-match assertion must FAIL today on these lanes.** No source changes were made (task is offline spec-only).

## WorldField barometer (FWorldFieldSample / UWorldFieldBus)
Fields: `ResonanceN` (int32), `ResonanceM` (int32), `Tension` (float 0..1), `BeatPulse` (float), `WorldPosition` (FVector).
Published by `UMelodiaCymaticsSubsystem::RefreshFromMPC -> UWorldFieldBus::PublishResonance(N,M,Tension,BeatPulse)`.
`WorldField.Resonance/Tension` are **bus struct fields, not MPC params** — no MPC-level Resonance/Tension parameter exists in source.
Status: **SCAFFOLD** (needs closed-editor build); offline probe `Tools/test_world_field_bus.py`.

## Other flags
- **Load-path discrepancy:** neural seam loads `/Game/Melodia/MPC_Melodia_Palette`; presentation+cymatics load `/Game/Melodia/_PROJECT/04_Materials/MPC_Melodia_Palette`. PIE must confirm one live collection.
- Single-writer structurally intact: no other system writes MPC_Melodia_Palette.

## Capture plan (deferred — editor locked)
Save → `Saved/Audit/world_field_bus_pie_2026-09-02.json` + `.mp4`.
Assertions:
- **A_PARAM_NAME_MATCH** — name-match table (writer ∪ consumers); EXPECTED FAIL on `BassIntensity/MidIntensity/BeatTracker`.
- **B_AUDIO_BAND_TO_LANE** — band->MPC-lane amplitude response over ≥4 bars.
- **C_WORLDFIELD_BAROMETER** — `ResonanceN/M/Tension` move on a beat (`Tension = |Chladni|·max(BeatPulse,0.15)`).

Full detail: `Saved/Audit/world_field_bus_pie_spec_2026-09-02.json`.