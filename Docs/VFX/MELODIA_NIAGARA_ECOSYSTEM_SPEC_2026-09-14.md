# Melodia Niagara Ecosystem Spec — Flipbook, Params & Material Loops (2026-09-14)

**Type:** integration spec + work plan (not a status doc).
**Inventory (2026-09-17):** [`VFX_NIAGARA_FULL_INVENTORY_2026-09-17.md`](VFX_NIAGARA_FULL_INVENTORY_2026-09-17.md)
· [`VFX_FIXA_RISKS_2026-09-17.md`](VFX_FIXA_RISKS_2026-09-17.md) · [`README.md`](README.md).
**Lens:** Infinity Nikki — abilities read at silhouette distance, cloth and
sparkle hold up nose-close, photo mode is a pillar, every effect answers the music.
**Evidence basis:** disk census + live-editor compile reads 2026-09-14; flipbook
frames eye-verified this session. Editor-lane wiring steps are marked EDITOR.

## 1. Organization (as built — protect this shape)

One flipbook master, `M_Niagara_MelodiaFlipbook`
(`/Game/_PROJECT/VFX/Materials/`), with 11 instances each swapping one alpha
texture. Registered consumers: 17 Niagara systems (`Content/Melodia/**/NS_*`),
all bindings resolving, zero DefaultSpriteMaterial stragglers (census 2026-09-14).
Sheep run a healthy side pair (`MI_NS_ChoralSheep_BeatStar/WoolMote`, both live
compile-clean, translucent 2-sided). Protection closure PR #215 tracks the 12
materials + 58 textures as LFS (integrity 70/70, zero dangling refs).

Master's live knobs (read from the asset): `FlipbookTexture`, `FlipbookUV`,
`FlipFPS`, `GridRows`/`GridCols` (`Rows`/`Cols`), `Opacity`, `Intensity`,
`RimIntensity`, `Glow`. The master reads NO Material Parameter Collection —
every global channel below stops at its door today. That is gap #1.

## 2. Live-param contracts (already publishing — wire the consumers)

**Global bus** `MPC_Melodia_Palette` (`/Game/Melodia/_PROJECT/04_Materials/`),
written every frame/pulse by `UMelodiaRhythmReactivitySubsystem::Publish()`
(plus the beat namespace `BeatPulse/BeatPhase/BeatIntensity` owned by the audio
subsystem — one writer per surface, never two):
`RhythmPulse`, `GlobalSparkleIntensity`, `PaletteShift`, `GlobalEmissiveBoost`,
`ProximityGlow`, `TemporalJitter`, `DreadPresence`, `DissonanceAmount`,
`WarmthGlow`, `PetalFallIntensity`, `DreamRipple`, `EmberDance`, `CozyBloom`.
Same signal fans out over OSC (`/rhythm/*`, port 9000) for TouchDesigner.

**Per-instance MIDs** (wardrobe transform + reactive meshes):
`Bloom`, `Sparkle`, `Beat`, `Tint`, `DreamPulseAmp`, `Iridescence`,
`TemporalStrength`, `ParallaxStrength`. Stencil setter exists
(`SetReactiveStencil`, incl. hero stencil 4).

**Niagara user params** (sheep scaffold, still open): `WoolGlow` 0.35,
`ChladniDrive` 0, `PitchHue` 0.75 + Melodia bus. BP wiring owed: WoolMotes to
fleece, `ChladniDrive` from coat `BeatAccent`/`ChladniEmissive`, BeatBurst on
pitch hits. Sheep files have another hand in them — claim the lane first.

## 3. Eye verdicts (frames inspected 2026-09-14)

- `T_Alpha_sparkle_pulse_flipbook` (4x4): professional — dot, glow, 4-point,
  8-point + satellites, peak, decay, clean black last frame. Loops safely.
- `T_Alpha_fluid_metaball_flipbook` (4x4): good core behavior (grow, emit,
  detach, dissipate) BUT the last frames park satellite dots in the frame
  corners and the loop restarts at a single center dot — visible corner-pop on
  loop. Play ping-pong or clamp, or re-bake the tail to black.
- General: the sheets are not why anything "looks like shit." The ugly lives
  in static playback (no beat response), unverified grid matches, and systems
  never bound to their BP params.

## 4. Integration sequence (EDITOR steps, in order)

1. **Grid audit.** Every water/fluid MI: `Rows`/`Cols`/`FlipFPS` vs its
   texture's true layout (all inspected sheets are 4x4 — confirm each MI says
   so). Mismatch here is the cheapest "broken look" in the building.
2. **StarGold glance.** `MI_Niagara_Melodia_Static_StarGold` carries no texture
   override — confirm color-only intent or bind one. One look.
3. **StateB decision.** Reparent onto the flipbook master or bless Cosmic —
   record it; two masters means two art directions.
4. **SwingTrail/WaterFX.** Re-home onto flipbook MIs or bless the EnvSandbox
   bindings (AuroraRibbon, Ripple — both tracked). No straddling.
5. **Global response.** Add Collection params to the flipbook master:
   `GlobalSparkleIntensity` → `Glow`/`Intensity`,
   `BeatPulse` → outline `Edge_BeatBoost`,
   `PetalFallIntensity` → petal spawn/size,
   `DreadPresence`/`DissonanceAmount` → cold shift.
   Presentation-only; never gameplay logic.
6. **Leaf/petal piles.** Leaf system (`NS_Leaves_Falling_Frustum_01`, mesh +
   MI_Leaves + 4 textures, whole folder untracked — needs closure #3) and
   petal loop (3 masters for 1 job: live `M_Niagara_PetalMesh_Loop` + 2
   Candidates — converge to one, bless/bury the rest) get the same
   protect→converge→respond treatment.
7. **Proof.** Per touched system: recompile clean + one lit PIE frame + JSON
   receipt (frames, params, log gate). Sky pinned before every capture.

## 5. Acceptance

- Every MI's grid matches its sheet; no system plays a stranger's frames.
- All 17 systems answer at least one live channel (bus, MID, or BP param).
- Metaball tail fixed (ping-pong, clamp, or rebake).
- B1 respected: no new post-process starry material, ever.
- No clean-checkout casualty: every referenced file tracked.
