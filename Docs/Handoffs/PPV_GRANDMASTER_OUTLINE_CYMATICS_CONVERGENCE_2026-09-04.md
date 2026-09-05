# PPV Grandmaster Outline + Cymatics Convergence

**Status:** implementation in progress; asset writes are editor-owned and runtime certification remains gated on build/PIE/package evidence.
**Shipping correction:** `LV_SeaAbove_Prototype` is a packaged shipping level at:
`/Game/EnvSandbox/Monoliths/SeaAbove/Prototype/LV_SeaAbove_Prototype`

## Scope and level taxonomy

The contract is centralized in `Content/Python/ppv_contract.py`:

| Surface | Levels | Meaning |
|---|---|---|
| Packaged shipping maps | `L_MelodiaMainMenu`, `L_MelusinaMorning`, `ZenForestTest`, `MelodiaIntegrationMap`, `L_KaleidoNave`, `LV_SeaAbove_Prototype` | Cook/package inventory from `Config/DefaultGame.ini` |
| Gameplay PPV certification | `L_MelusinaMorning`, `L_KaleidoNave`, `ZenForestTest`, `LV_SeaAbove_Prototype` | Must pass PIE and packaged runtime outline/audio gates |
| Lookdev/regression | `L_FallenMoon`, `_Template/L_Template` | Visual regression and cinematic experimentation; not gameplay shipping coverage |

The former `/Game/Melodia/Maps/LV_SeaAbove_Prototype` alias is invalid and has
been removed from the project documentation.  The canonical EnvSandbox map is
the shipping Sea Above target.

## Runtime ownership

```text
UMelodiaMusicClockSubsystem
        │ musical time
        ▼
UMelodiaAudioReactivePresentationSubsystem
        │ sole writer: MPC_Melodia_Palette (BeatPhase, BeatPulse, Bass/Mid/Treble)
        ├──► PPV materials (read-only)
        ├──► NPC_Melodia_Palette (Niagara mirror)
        └──► Oceanology presentation drive (separate surface consumer)

MPC_Melodia_Palette ──► UMelodiaCymaticsWriterSubsystem
                           │ sole writer: MPC_Cymatics_Driver
                           └──► material/cymatic consumers (read-only)

UMelodiaCymaticsSubsystem ── read-only Chladni sampling
```

The recent lineage folded into this convergence is:

- `757bd774` — GameMode clock registration for every level.
- `b1cac649` — PIE proof that `BeatPhase` advances, `BeatPulse = cos²(BeatPhase·π)`, and the cymatic beat mirror agrees.
- `a62a2deb` / `1f7be825` — Sea Above landscape audio reactivity and restored cymatic landscape response.
- `2d499b41` — Oceanology bioluminescence through `MF_NikkiSparkle`.
- `fa4110c9` — repaired Oceanology `DeepScatteringColor` runtime baseline; requires a C++ build.
- `d28d1da1` — bounded cymatics/optical-LOD parameter contract across the material masters.
- `10a20de6` plus the Niagara handoff — single-writer ownership and runtime proof rules.

No second MPC writer or parallel outline authority is introduced.

## Grandmaster material contract

The live-editor migration promotes the current premium candidate into:

- Parent: `M_PP_Outline_Grandmaster`
- Gameplay profile: `MI_Outline_Grandmaster_Gameplay`
- Foundation: Art of Shader `MF_StencilDepthAlpha` + `MF_PostProcessBlend`

The grandmaster outline uses a deterministic pixel-center kernel with view-rect
clamping, continuous width weighting, `MinWidthPx >= 1`, and analytic AA.  It
does not use hash-rotated samples, `View.GameTime`, vines, animated grain,
temporal jitter, or beat/cymatic values to change edge position, sample radius,
or UVs.  Beat/cymatic response is presentation-only: bounded tint/opacity or
edge-energy modulation.  `StarryNight_Hero` remains hero/cinematic-only.

The budget gate is `<= 369` pixel instructions and `<= 6` estimated texture
samples, with a preferred result below the current premium candidate baseline.
Corrupted instance overrides are reset on the new gameplay profile rather than
copied forward.

## Current PPV truth and open runtime gap

Sea Above currently has a live `PPV_NikkiDream` carrying the premium outline.
The new gameplay profile is the target replacement for that outline slot and
for the other gameplay certification maps.  `L_MelusinaMorning` remains an
explicit runtime gap until its PPV is observed in PIE; source/docs presence is
not certification.

Gameplay stack:

1. `MI_Outline_Grandmaster_Gameplay` @ `1.0`
2. `MI_MeluColorGrade_GameplayStandard` @ `0.69`
3. `MI_MelodiaInk_GameplayStandard` @ `1.0`

Lookdev/cinematic stack remains separate and may include `MI_StarryNight_Hero`.

## Verification gates

1. Compile the updated C++ baseline.
2. On Sea Above in PIE and packaged runtime, record advancing `BeatPhase`, the
   `cos²` `BeatPulse`, matching `Cymatic_BeatPulse`, and responding Oceanology /
   landscape presentation.
3. Hold the camera still while sweeping beat/cymatic values; the outline mask
   must remain identical while only approved energy channels vary.
4. Capture 1080p, 1440p, 4K, mismatched capture resolution, orbit motion,
   foliage, thin silhouettes, Substrate surfaces, and translucent FX.
5. Reject one-frame edge toggling, width popping, stochastic crawl, and any
   outline response to `Cymatic_UVDistortion`, `Cymatic_ModeN/M`, animated world
   time, or raw audio values.

“Zero jitter” is reserved for deterministic repeated-frame and motion captures;
literal frame identity across TSR additionally requires a non-temporal AA mode.
