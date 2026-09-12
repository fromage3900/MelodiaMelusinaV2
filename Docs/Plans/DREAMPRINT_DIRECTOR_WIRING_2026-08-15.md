# Dreamprint — LookdevDirector Wiring Spec (2026-08-15)

Target: `/Game/EnvSandbox/Lookdev/Candidates/BP_MelodiaLookdevDirector_Candidate`
(the existing candidate BP — ProfileIndex 0/1/2, no write path yet).

Purpose: close the last "callable, never called" seam for the Dreamprint stack —
the director becomes the runtime conductor that (a) plays the MetaSound music
pulse source, (b) samples its Envelope output into `MPC_MelodiaInk`, and
(c) switches profile MIs per ProfileIndex.

## 1. Why Blueprint (not C++)

`UMetaSoundOutputSubsystem::WatchOutput` is `BlueprintCallable` and requires an
`UAudioComponent` — a BP actor owns that naturally. This avoids touching the
battle-audio authority (`UMelodiaAudioComponent`) and avoids a closed-editor
build. Musical time (Harmonix) and rhythm-hit intake (`NotifyCommandResolved`)
are already wired in C++ and need no change.

## 2. Components (actor defaults)

| Name | Class | Notes |
|---|---|---|
| MusicPulseSource | UAudioComponent | Sound = `/Game/Melodia/_PROJECT/04_Audio/Music/MSS_MelodiaMusicPulse`; Auto Activate = false; Loop via the MetaSound graph (WavePlayer loop), not the component |

## 3. BeginPlay wiring

1. Set `ProfileIndex` int (exposed, default 1 = Narrative).
2. `MusicPulseSource->Play()`.
3. `UMetaSoundOutputSubsystem` (Get World Subsystem) →
   `WatchOutput(AudioComponent=MusicPulseSource, OutputName="Envelope", OnOutputValueChanged=<custom event>)`.
4. Call the profile-apply custom event (below).

## 4. OnEnvelopeChanged(float Value) — the amplitude bridge

```
SetScalarParameterValue(MPC_MelodiaInk, "InkReact", clamp(Value, 0.0, 1.0))
```

That is the whole runtime bridge for v1: one full-band envelope → `InkReact`,
which the ink master uses for print liveliness. The band detail
(InkBass/InkMid/InkTreble) stays on the TouchDesigner OSC bridge
(`MPC_Portfolio_Audio`) as the documented fallback; a future MetaSound graph
pass can expose per-band outputs (3x band-pass + envelope) and the director
then writes the same three channels in-engine.

## 5. ApplyProfile (ProfileIndex 0/1/2)

Swap the candidate PPV's `M_PP_MelodiaInk_*` blendable to the matching profile
MI and set `InkMasterWeight`:

| Index | Profile | InkMasterWeight |
|---|---|---|
| 0 | GameplayStandard | 0.45 |
| 1 | Narrative | 0.65 |
| 2 | PortfolioHero | 1.0 |

## 6. A/B verification before promotion

Use `setup_dreamprint_ab.py` in-editor: `mode("candidate", profile=...)` vs
`mode("source")` at fixed 16:9 cameras on `L_KaleidoNave`, `L_FallenMoon`,
`ZenForestTest`, `L_MelusinaMorning`. No live-PPV edits until owner sign-off.

## 7. Assets produced by the headless build (queue)

| Asset | Path |
|---|---|
| MPC_MelodiaInk | `/Game/Melodia/_PROJECT/04_Materials/MPC_MelodiaInk` |
| M_PP_MelodiaInk (master, After Tonemap) | `/Game/Melodia/_PROJECT/04_Materials/PostProcess/M_PP_MelodiaInk` |
| MI_MelodiaInk_{GameplayStandard,Narrative,PortfolioHero} | `.../PostProcess/Candidates/Profiles/` |
| M_PP_MeluColorGrade + SyncVision block | `/Game/_PROJECT/04_Materials/PostProcess/M_PP_MeluColorGrade` |
| MSS_MelodiaMusicPulse (wave+envelope) | `/Game/Melodia/_PROJECT/04_Audio/Music/MSS_MelodiaMusicPulse` |

Scripts: `Content/Python/build_dreamprint_{mpc,material,metasound}.py`,
`upgrade_grade_dreamprint.py`, `verify_dreamprint.py`,
`setup_dreamprint_ab.py`. Runner: `deploy/run_dreamprint_build.ps1`.
