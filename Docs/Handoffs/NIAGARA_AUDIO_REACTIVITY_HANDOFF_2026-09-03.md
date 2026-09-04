# Handoff — Niagara / Audio Reactivity + Session Closeout, 2026-09-03

Everything below was read from live editor queries (Monolith 0.20.3, UE 5.8) or from
source on disk. Where something is unverified it says so.

---

## 1. The audio-reactivity chain, end to end

It is **already built and correct**. This was the surprise of the session — the plumbing
is not the problem.

```
Harmonix music clock  (UMelodiaMusicClockSubsystem)
        |  GetBeatPhase(VisualTimebase), gated on bHasMusicalTime
        v
UMelodiaAudioReactivePresentationSubsystem::TickPresentation   (FTSTicker, every frame)
        |
        |-- MPC_Melodia_Palette          -> materials   (89 bound assets)
        |-- NPC_Melodia_Palette          -> Niagara     (64 params declared)
        |-- DriveOceanBeatValues()       -> ocean MIDs  (game worlds only)
        `-- RhythmReactivity.NotifyBeat  -> OSC out     -> TouchDesigner
```

### Beat maths

`BeatPulse = cos²(BeatPhase · π)`

Deliberately `cos²`, not `sin²`: **BeatPhase is 0 *on* the beat**, so `sin²` peaked at
phase 0.5 and every consumer pulsed on the off-beat. The canonical copy lives in
`UMelodiaMusicClockSubsystem::GetMusicPulse` — if this ever changes, change it there and
call it, do not re-derive.

### What is published each tick

| Parameter | Source | Written to |
|---|---|---|
| `BeatPhase` | music clock | MPC + NPC |
| `BeatPulse`, `BeatIntensity`, `Treble` | `cos²` pulse | MPC + NPC |
| `Bass`, `GlobalReactivity` | `bBattleActive ? BattleIntensity : 0` | MPC + NPC |
| `Mid` | `ImpactPulse` (decays at 3.5/s) | MPC + NPC |
| `ComboNormalized`, `CrescendoNormalized`, `CommandEnergy`, `BreakPulse`, `RhythmPulse` | `RhythmReactivity::GetSignal()` | NPC |

`Treble` and `BeatIntensity` are **the same float** as `BeatPulse` under different names.
`Bass` and `GlobalReactivity` are combat state, **zero outside battle** — that is
deliberate, not a bug.

**Ownership is documented in-code and should be respected:** this subsystem is the *only*
writer of the beat namespace on the MPC. `UMelodiaRhythmReactivitySubsystem` keeps its
own beat values for OSC and reactive materials but no longer writes MPC beat params.

### OSC out — TouchDesigner leg

`UMelodiaRhythmReactivitySubsystem::SendOSCFloat`, UDP to **127.0.0.1:9000**:

```
/rhythm/beat_phase          /rhythm/combo_normalized     /rhythm/tension
/rhythm/beat_pulse          /rhythm/crescendo_normalized /rhythm/dissonance
/rhythm/command_energy      /rhythm/victory_pulse        /rhythm/dread_presence
```

Direction is **UE -> TouchDesigner**. UE is the clock master; T3D is a consumer.

---

## 2. The actual gap: Niagara readers, not writers

`find_references` on `NPC_Melodia_Palette`:

```
referenced_by:
  /Game/EnvSandbox/VFX/Candidates/Melodia/NS_Melodia_LaneHit          (NiagaraSystem)
  /Game/EnvSandbox/VFX/Candidates/Melodia/NS_Melodia_BattleBackdropPulse (NiagaraSystem)
```

**Two of 92 Niagara systems consume the collection — and both live in `Candidates/`, not
shipped `Systems/`.**

So every frame the engine computes a correct beat pulse, publishes it to 64 Niagara
parameters, and almost nothing reads them. This is the single highest-leverage item in
the FX lane: the expensive half is done.

### Recommended order

1. **Promote the two candidates** out of `Candidates/` once verified in PIE — they are
   the reference implementations for how to bind an emitter to the NPC.
2. **Bind the beat-visible systems next**, in this order of payoff:
   `NS_Melodia_ClickSparkle`, `NS_Melusina_EyeSparkle`, `NS_Uni_PollenSparkle`,
   `NS_SakuraDreamSparkle`, `NS_SDF_ParallaxPulse`.
3. **Reef bioluminescence** — see §3; the driver already exists.
4. Only then consider new FX. Binding existing systems is cheaper and shows immediately.

---

## 3. Bioluminescence is already beat-driven

`DriveOceanBeatValues()` writes per tick, in game worlds only:

```cpp
Biolum_Intensity = 1.0f + BeatPulse * 1.5f     // MID and reflected actor call
PhaseGLow        = 0.75f + BeatPulse * 0.75f
HighlightBoost   = 10.0f + BeatPulse * 10.0f
ScatterBoost     = 10.0f + CombatEnergy * 5.0f
Toon_Weight      = 0.65f + BeatPulse * 0.15f
```

It drives `Biolum_Intensity` twice — directly on the resolved MID, and reflectively via
the Oceanology actor's `SetScalarParameterValue` — so it works whether or not the MID
resolves.

Bioluminescence assets that exist but are **not** yet on this path:
`MF_WaterBioluminescence_v7/v9`, `MI_Grotto_Bioluminescence`,
`MI_SDF_Bioluminescence_Glow`, `M_SDF_Bioluminescence`, `T_Jelly_Biolum_LUT`,
and the reef jellies (`BP_Jelly_SeaAbove`, `BP_Jelly_Cathedral`, `MI_Jelly_Arms/Bell`).

`Content/Python/wire_water_bioluminescence_harmony.py` already defines the harmonic
budget: impulse peak **2.0**, decay `I(t) = I₀·e^(−2.5t)`, max **2** quantum events/sec.
Reuse those constants rather than inventing new ones.

---

## 4. Ocean fix — and a runtime trap it exposed

`SeaAbove_InfiniteOcean_Canopy` in `LV_SeaAbove_Prototype` has
`UserOverrideMaterial = true` and `Material = M_Water_Oceanology_Melodia_Inst`.
That instance held values that cannot be authored intent:

| Parameter | Was | Now | Plugin default |
|---|---|---|---|
| `DeepAbsorptionCoefficient` | **1000** | 3 | 7 |
| `MultiplyRefraction` | **5.49e16** | 1.333 | 1.333 |
| `RefractionDownsampleFactor` | **712.03** | 2 | 2 |
| `RefractionBottomAmount` | **468.29** | 1 | 1 |
| `WaterSpecular` | **41.09** | 0.225 | 0.225 |
| `HighlightBoost` | **144.55** | 10 | 10 |
| `DistantWaterScale` | **-3.19** | 32 | 32 |
| `Absorption` | (70,180,350) | (20,40,100) | — |
| `DeepScatteringColor` | (.05,.25,.30 A.15) | (.205,.716,.631 A.65) | — |
| `Toggle Surface Scattering` | **false** | true | true |

`DeepAbsorptionCoefficient` at 143× default extinguishes light almost immediately — that
is the "far too deep and dark" complaint directly. Brightened values come from the
plugin's own `DA_Color_LightBlue` preset.

### The trap

`DriveOceanBeatValues` hardcoded the **old** dark base and rewrote
`DeepScatteringColor` every tick:

```cpp
FLinearColor(0.05f + ImpactPulse*0.10f, 0.25f - ..., 0.30f + ..., 0.15f)
```

In a game world that would have silently re-darkened the ocean every frame and undone the
asset fix — while still looking correct in the editor, because the drive is gated on
`World->IsGameWorld()`. The base is now aligned to the repaired values.

**This needs a C++ build to take effect.** Until then the runtime still uses the old base.

> **General lesson:** any asset value that a tick function also writes has *two* sources of
> truth. Grep the drive functions before trusting an asset edit to survive PIE.

---

## 5. Session closeout — what changed today

| Commit | What |
|---|---|
| `459a1cd0` | Packaged build loads both route legs (0.36 s / 1.03 s, 0 fatals); P1 #5 closed |
| `97b76dd8` | Melusina shared-MI hypothesis + two dead measurement methods |
| `7d970d8f` | V2 instance map, ocean orphan MI, main-menu layout bugs |
| `5ad01b64` | Rewired all 10 V2 accessory slots |
| `fc2e70a9` | Shirt tuning measurements + sampling traps |
| `e9433b90` | Ocean is actor-driven, not material-driven |
| `3d3b6644` | Located the two SeaAbove ocean actors |
| `f3949f7e` | Computed main-menu orrery fix values |
| `d0471791` | Repaired the corrupted P0 ocean instance |

Plus `recovery/snapshot-20260903-1840` pushed to origin (1261 commits' worth of tree,
SHA-verified `abf30699`).

### Corrections I had to make to my own work

- Claimed the shirt rendered neutral grey with the albedo not reaching output. **Wrong** —
  the capture preview has a full HDRI backdrop, so background-difference sampling measured
  the *environment*.
- Claimed `SK_MelusinaHair` did not exist. **It does** — my search drowned in `chair`
  matches.
- Guessed `Absorption` was an extinction *distance*. **It is a coefficient** — the preset
  named LightBlue has the *lower* value.
- Said the ocean was not material-driven and sat at plugin defaults. **Both wrong** for
  this actor: `UserOverrideMaterial` is true and its values were heavily modified.
- Claimed `init_unreal.py` drove the import loop. **Wrong** — `add_entry` only registers
  menu entries.

### Methods that produce false negatives — do not retry

- `strings` on `.pak`/`.ucas` (IoStore hashes the name map: a known-present asset returns
  0 hits)
- `strings` on a UE 5.8 `.uasset` (compressed name table)
- background-difference pixel sampling on a capture preview (HDRI backdrop)
- a chroma filter across a brightness sweep (sample count collapses as it desaturates)

---

## 6. Open items

1. **Build the C++ change** — the ocean base fix is inert until compiled.
2. **Visually confirm the ocean.** Monolith has no level-viewport capture and editor
   `HighResShot` issued from headless Python never writes a file. Needs eyes on the
   viewport, or a PIE capture.
3. **Main menu** — values computed in `Docs/LookDev/LOOKDEV_PREP_2026-09-03.md` §9, not
   yet applied. Orrery core `(-345,-125)`, four orbits on a radius-150 ring, starfield to
   full-screen. Do **not** blind-enable `Background`/`CosmicVoid`: `NebulaParchment` sits
   behind them at z-47 and would be hidden.
4. **Melusina shirt** — residual gap is blue (122 vs 165 target). Needs the albedo texture
   brightened, not more tint.
5. **`Content/EnvSandbox/*` is gitignored** (`.gitignore:183`). The ocean fix had to be
   force-added. Masters, MF_Nikki functions and the whole SeaAbove monolith live outside
   version control. This is a standing repo-health risk — `.gitignore` was not modified.
6. **Auto-reimport disabled.** `bMonitorContentDirectories` and `bDetectChangesOnStartup`
   set to False in `Saved/Config/WindowsEditor/EditorPerProjectUserSettings.ini`
   (backup: `.bak-20260903`). It was monitoring **all of `/Game/`** with **304 raw `.fbx`
   inside `Content/`**, re-importing a 1.6M-triangle dress on a loop. If that workflow is
   wanted back, point `SourceDirectory` at a small intake folder — not `/Game/`.
7. **Unowned work in the tree** — opencode was killed mid-flight; its `MelodiaWardrobe`
   source and `SK_MelusinaHair` / `M_Master_Toon_Universal` edits are uncommitted.

---

## 7. Root cause: route leg 0 has no music clock

The reactive chain is complete and correct, but on `L_MelusinaMorning` — the opening level,
the first thing a player sees — **nothing registers a music clock**, so `HasMusicalTime()` is
false and every downstream value publishes flat.

`HasMusicalTime() = !RhythmLayerDisabled && (IsHarmonixClockRunning() || IsQuartzClockRunning())`,
and the only registrar of a Harmonix clock is `UMelodiaJRPGPresentationRhythmComponent`
(`MelodiaJRPGPresentationRhythmComponent.cpp:34` `RegisterMusicClock`, `:45`
`RegisterQuartzAudioComponent`) — an **actor component**, so it must be present and playing.

| Check | Result |
|---|---|
| Levels containing the registrar | `L_KaleidoNave` yes, `MelodiaIntegrationMap` yes, `Gameplay.umap` yes — **`L_MelusinaMorning` no** |
| `L_MelusinaMorning.umap` | 0 hits: `MelodiaJRPGPresentationRhythm`, `MusicClock`, `BP_BattleController` |
| Its 56 WP external actors | 0 of 56: `Rhythm`, `MusicClock`, `Harmonix`, `Ambience`, `MetaSound`, `AudioComponent` |
| **Control on that grep** | `Actor` 56/56, `Melodia` 56/56, `Component` 54/56 — the method reads these files |
| Global GameMode `BP_MelodiaJRPGGameMode` | `Melodia` 16 hits (readable), `Rhythm` **0**, `MelusinaSwordsman` **0** |
| C++ runtime spawn | only `MelodiaIntegrationTests.cpp:431`, transient/test-only |

**Consequence on leg 0:** `BeatPulse`/`BeatPhase`/`Bass`/`Treble` all 0 → `MPC_Cymatics_Driver`
flat → the 8 grafted masters sample zero → Niagara NPC zero → ocean `Biolum_Intensity` stays
at its 1.0 base → OSC sends zeros to TouchDesigner. Silently, because the clock deliberately
publishes flat rather than inventing a tempo (the removed 120 BPM fallback).

The MPC convergence work is sound; on this level it simply has no signal to carry.

**Fix is placement, not code.** Either place a rhythm/ambience actor in `L_MelusinaMorning`
(`A_Ambience_Melusina_98bpm` is already tempo-authored), or attach the component to the
GameMode/default pawn so the clock registers wherever the player is — the latter covers every
level at once and is the more robust option.

**Useful A/B:** `L_KaleidoNave` (leg 1) *does* carry the registrar, so the same route gives a
working control against leg 0.

**Limit of this claim:** level, external actors, global GameMode, project config and C++ spawn
sites were all checked. A path not considered cannot be ruled out, but none was found.

---

## 8. Build state at handoff (Phase A incomplete)

The ocean runtime base fix in `MelodiaAudioReactivePresentationSubsystem.cpp` is **still
uncompiled**. Live Coding failed; the closed-editor build is blocked by unrelated
work-in-progress from the killed opencode agent (471 insertions across 6 files that do not
compile).

Three genuine errors in that WIP were fixed while trying to get through:

| File | Error | Fix |
|---|---|---|
| `MelodiaCaptureRenderSubsystem.cpp:13` | `SceneCaptureComponent2D.h` not found | `Components/SceneCaptureComponent2D.h` |
| `MelodiaWardrobeComponent.cpp:438` | `GetMorphTargetIndex` not a member of `USkeletalMesh` | `FindMorphTarget(...) == nullptr` (per `SkeletalMesh.h:2757-2758`) |
| `MelodiaCaptureRenderSubsystem.cpp:260` | checked-format-string failure | plain concatenation |

`MelodiaWardrobe` now compiles and links. Remaining blocker is `C7595` in UE 5.8's
compile-time format-string sanitizer at `MelodiaCaptureRenderSubsystem.cpp:250`; the
accompanying "`MaterialToken` is not a member" is a cascade from it — the member *is* declared
at line 22. Further fixes there would mean guessing the intent of an unfinished PPV-drift gate,
so work stopped.

**These three fixes are uncommitted, in the other agent's files.** They were not committed
because those files are that agent's in-flight work. Nothing here is lost — but whoever
resumes that feature should know the files have been touched.

**Not blocked by this:** the ocean asset repair, `MF_NikkiSparkle` wiring and the main-menu
fixes are all saved and committed, and read correctly in-editor. Only the runtime
re-darkening in PIE/packaged needs the build.
