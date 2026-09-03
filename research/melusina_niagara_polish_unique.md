# Melusina — What Else Is Unique + Niagara Polish

**Date 2026-08-24 · Build mode · Inventory `Content/Melodia/VFX/*` `EnvSandbox/VFX/*` `Water/v10/*`**

## Part A — Two More Signature Ideas (beyond Sorrow Seam)

### 1) The Pool That Remembers (world-as-mirror)
Melusina's pool in `L_MelusinaMorning` (`WATER_V10_NATIVE:89` ShallowWaterSim) is not decoration — it's a **save-mirror**. Every piano phrase you play ripples `NDC_MelodiaWaterContact` `Water/v10/NDC_MelodiaWaterContact.uasset:1` and is stored as `melodia:flag:pool_memory.<phrase>`; on reload, `UMelodiaWaterNiagaraBridgeComponent` replays faint reverse ripples. At high `DreadPresence` the pool shows the *other* morning — empty bed, chair pulled out — as a screen-space `MF_Madoka` warp on water `M_Water_Master_Grand_v10`. No jump scare; just the room remembers when you don't.

Unique because: Yume Nikki has dream pools, OMORI has mirrors, neither is a persistent physics sim that is literally your save file visualized.

### 2) Ribbon Score (battle-as-calligraphy)
`NS_Melusina_SwingTrail` + `NS_Melusina_Arc` today are sprite confetti. Rebuild as **2-emitter CPU ribbon**: Leader spawns per `SwingIntensity` → Receiver ribbons `M_SakuraRibbon`/`MI_Niagara_Melodia_Ribbon` with `M_SeedRibbonLinkOrder`+`CurlNoise 120/0.6`+`RibbonWidth 22→2` taper. Perfect→Great rhythm adds width and curl; grade never blocks damage (`DECISION 009/016`). The ribbon *is* the music staff — you draw the battle's song and it lingers 3.2s as a `ConstellationTwinkle` rosette `NS_ConstellationDraw` draws.

Unique because: Rhythm games show notes; this **writes** notes in world space that become the next puzzle's piano pattern.

## Part B — Niagara Polish: Make What Exists Beautiful

**Inventory:** 87 `NS_*.uasset` live, 16 Melusina suite `Melodia/VFX/*` (Globules/Splash/Ripple/EyeSparkle/SwingTrail/Arc/Superposition/ChaosDrift/EntropyDust/Sigil), Water v10 NDC pooled 60/sec `WATER_SYSTEM_TEST_MATRIX`, Uni/Magical 11 systems re-authored `VFX_NIAGARA_FINALIZATION:28`.

**Debt:** 10 BLACK preview (ConstellationTwinkle/DreamSparkle/PondShimmer/LanternMotes), warmup 19.9s, `DynamicBounds`, pale `SDFStarburst` placeholder `RENDERER_AUDIT:49`, mismatched flipbooks, no shear/biome tint, sprite-only ribbons.

### 5 Additive Polish Upgrades (no system deleted until proven)

| # | System | Polish | Beauty Gain | Verify |
|---|---|---|---|---|
| **1** | **Globules/Splash/Ripple/EyeSparkle** | Unify on `M_Niagara_MelodiaFlipbook` 4×4 FlipFPS15, `User.BiolumTint`+`ShearThreshold` via `NDC_MelodiaWaterContact.RippleEnergy`, `exp(-Age/Decay)*smoothstep` + DepthFade 25cm + SoftParticle | Shear-cyan ghosting, warm→cyan decay, no Z pop | validate_system 0 err, pie_smoke 6 writes/60 cap, GPU <1ms Tier1 |
| **2** | **SwingTrail/Arc → Ribbon** | CPU Leader→Ribbon `M_SeedRibbonLinkOrder`/`M_SetRibbonGroupID`, CurlNoise 120, Drag 1.8, Width 22→2, UVTile 3, `User.SwingIntensity` drives width/curl | Calligraphic ink staff, not confetti | Isolated preview non-black, `stat Niagara` < 0.25 CPU |
| **3** | **EyeSparkle/Superposition** | Add CPU Light renderer `Intensity 1.2→0 Radius12→0 8Hz` × QuantumPulse, `NSM_MelusinaEyeDriver` with `EyeLocationWS/ForwardWS` offset 6, gate ChaosDrift on `NDC MaxReadsPerTick` + QuantumPulse>0.18, Sigil mesh-card `ShrineSeal` atlas | Breathes with skill quantum, iris-locked, no double-spawn | compile + eye-forward probe |
| **4** | **Dust/EntropyDust** | GPU FixedBounds 800×800×400, Warmup0, `ENV_StorybookAmbientVFX` Q 7/12/18k `CODEX_NIAGARA_EXECUTION:33`, Wind 85/Vortex45/Drag0.9, Spawn22 Life6-9 Size2.5-5, CollisionQuery depth60 bounce0.15, `User.DreamVisibility` duck | Ghibli drift with wind + ground kiss, story-thin when needed | bounds fixed, `stat Niagara` <1ms GPU |
| **5** | **Sigil Ceremony/Constellation Hero** | Promote `NS_SakuraPetals_v3_Candidate` DeathEvent→PondRipple+Pile as skirt settle; re-author `ProviderSigil_Ceremony` 12 cards 3.2s `MI_Niagara_Melodia_ConstellationRosette` SDF 8, FLIP2D Splash on Impulse>0.7 keep 3D pool cine only | Wardrobe-summon dissolve into petal piles that ripple native water via `MF_WaterNativeInteraction_v10` | Candidates/ until A/B capture approved |

**Docs:** `Docs/WATER_V10_NATIVE_NIAGARA_SUBSTRATE_TOON_2026-08-09.md:87` NDC schema, `WATER_V10_FINALIZATION_STATUS:14` FLIP tiers, `VFX_NIAGARA_FINALIZATION:88` flipbook family, `CODEX_NIAGARA_LIBRARY_AUDIT:16` BLACK list.

## Part C — Ship Order

**Now (this PR, spec-only):**
- Create `specs/niagara/melusina_polish_pack.v1.json` for Upgrades 1+2 (Sorrow Seam veil + ribbons) — no .uasset mutation, passes `validate_system` contract.
- Drive veil Sheen via `MPCollection MPC_Melodia_Palette.Iridescence` already on `MI_Fabric_Melusina_SorrowSeam` — no new collection.

**Next live editor (one writer 9316):**
- Import Upgrade 1 flipbook unification → `NS_Melusina_Globules` → isolated preview → pie_smoke_9.
- Import Upgrade 2 ribbon chain → `NS_Melusina_SwingTrail` → width test `User.SwingIntensity 0.4→1.2`.

No mass replace of `ZenForestTest` 5 actors until A/B same-camera.

