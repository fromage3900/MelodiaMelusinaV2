# Handoff — Dreamprint Audio Reactivity: Verified Seams + Remaining Prep (2026-08-18)

**Scope**: prep to ensure the dreamprint post-process materials are actually driven by
audio — MetaSound envelope + Harmonix beat hits. Material side is DONE (this session:
materials compile and their MPC inputs are bound). This doc records the verified chains,
the one real gap found, and the exact remaining wiring.

---

## 1. WORKING chain — Harmonix beat hits → materials (verified in C++)

```
UMusicClockComponent (HarmonixMetasound, on BP_BattleController, wall-clock driven)
  → UMelodiaMusicClockSubsystem::HandleHarmonixBeat/Bar, GetBeatPhase(VisualTimebase)
    (Source/BS_GodFile/MelodiaIntegration/MelodiaMusicClockSubsystem.cpp)
  → UMelodiaAudioReactivePresentationSubsystem (TickPresentation, per-frame;
    THE only writer of the beat params — comment at cpp:154)
  → MPC_Melodia_Palette: BeatPulse, BeatPhase, BeatIntensity, Bass, Mid, Treble,
    GlobalReactivity   (cpp:162-168)
  → M_PP_MelodiaInk + M_PP_MeluColorGrade read BeatPulse/MeluPrimary etc. via
    named custom-node inputs — NOW COMPILING + BOUND (this session).
```

BeatPulse = `cos²(BeatPhase·π)` peaking mid-beat (MelodiaMusicClockSubsystem.cpp:87-90 —
the "beat pulse must peak between beats" fix).

## 2. GAP found — ComboNormalized / VictoryPulse / BreakPulse / EnemyTension have NO writer

The MPC_Melodia_Palette **channels exist** (verified 08-18) and the dreamprint materials
read them by name — but nothing writes them today:

- `UMelodiaRhythmReactivitySubsystem` (MelodiaCore plugin,
  `MelodiaRhythmReactivitySubsystem.cpp:359-363`) maps them onto OTHER names:
  - `RhythmPulse ← CommandEnergy`
  - `GlobalSparkleIntensity ← max(VictoryPulse, CommandPulse)`
  - `PaletteShift ← ComboNormalized`
  - `GlobalEmissiveBoost ← 1 + CrescendoNormalized`
  - `ProximityGlow ← BreakPulse`
- `EnemyTension` — no C++ writer anywhere; source unknown (BP or director knob).

**Effect**: the ink's `ComboNormalized` (dot growth), `VictoryPulse` (sync vision), `BreakPulse`
(print-slip), `EnemyTension` (hatch darken) inputs sit at 0.0 until fixed.

### Recommended fix (prep — NOT applied)

In `Plugins/MelodiaCore/Source/MelodiaCore/MelodiaRhythmReactivitySubsystem.cpp`, next to
the L359-363 block (cpp-only, no header change → Live-Coding safe), add:

```cpp
SetMPCScalar(TEXT("ComboNormalized"), Signal.ComboNormalized);
SetMPCScalar(TEXT("VictoryPulse"),    Signal.VictoryPulse);
SetMPCScalar(TEXT("BreakPulse"),      Signal.BreakPulse);
```

`EnemyTension`: no Signal field exists — propose wiring from battle phase
(`EMelodiaBattlePhase` enemy-active + elapsed) or a director knob; owner decision.
Needs a closed-editor build + PIE verification (do NOT hot-load plugin cpp mid-editor).

## 3. WORKING asset — MetaSound envelope wrapper (BP wiring remains)

`MSS_MelodiaMusicPulse` exists + verified (08-16 17:48, `dreamprint_metasound_build.json`).
Graph: WavePlayer(SW_BGM_Zundamon_Sewaa_Full, loop) → EnvelopeFollower → graph output
"Envelope". **Missing (GUI/owner session)**: a `UAudioComponent` playing it, then

```
UMetaSoundOutputSubsystem::WatchOutput("Envelope")
  → SetScalarParameterValue(MPC_MelodiaInk, "InkReact", Envelope)
```

(optionally band-split into InkBass/InkMid/InkTreble). See
`DREAMPRINT_STACK_BUILD_2026-08-16.md` §BUILT for the binding facts.

## 4. Director knobs (BP, per DREAMPRINT_DIRECTOR_WIRING_2026-08-15.md)

`InkMasterWeight` (profile switch; GameplayStandard 1.0), `InkSyncVision` (0 = locked look),
`InkHueShift` (0.5 = identity), `InkAccentTint` — via `ApplyProfile()` (ProfileIndex 0/1/2).

## 5. Material-side readiness (DONE this session)

- Ink + grade compile clean; 0 unbound identifiers (`dreamprint_verify.json` ok=true).
- Ink reads: BeatPulse/ComboNormalized/EnemyTension/BreakPulse/VictoryPulse/MeluPrimary +
  Ink* (all now named inputs). Grade reads: BeatPulse/VictoryPulse/InkSyncVision/MeluPrimary.

## Next steps

1. (Agent, after owner ok) Apply §2 cpp block; closed-editor build; PIE check.
2. (Owner/GUI) §3 WatchOutput BP wiring + music component placement.
3. (Owner/GUI) A/B + look approval (`setup_dreamprint_ab.py`), then promote.