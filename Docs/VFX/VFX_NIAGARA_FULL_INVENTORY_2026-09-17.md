# VFX Niagara full inventory — 2026-09-17

**Type:** LIVE_MONOLITH census of 65 ship Niagara systems under `/Game/Melodia` +
`/Game/EnvSandbox` (Candidates / `_Archive` excluded), merged with bound
materials. Documentary first pass is superseded for Fix A pin state.
**Home:** [`Docs/VFX/`](README.md).
**Canonical table:** [`VFX_NIAGARA_INVENTORY_2026-09-17.csv`](VFX_NIAGARA_INVENTORY_2026-09-17.csv)
**Pin authority:** [`VFX_FIXA_DETAIL_2026-09-17.csv`](VFX_FIXA_DETAIL_2026-09-17.csv)
**Graph:** [`VFX_NIAGARA_GRAPH_2026-09-17.md`](VFX_NIAGARA_GRAPH_2026-09-17.md)
**Fix A:** [`VFX_FIXA_RISKS_2026-09-17.md`](VFX_FIXA_RISKS_2026-09-17.md)
**LeafPile receipt:** [`VFX_FIXA_LEAFPILE_2026-09-17.md`](VFX_FIXA_LEAFPILE_2026-09-17.md)
**BeatPulse BP contract:** [`VFX_BEATPULSE_BP_WIRE_2026-09-17.md`](VFX_BEATPULSE_BP_WIRE_2026-09-17.md)

LeafPile Fix A is **applied live** (owner Ctrl+S). SubImageSize **2×2 kept**
(atlas). Ship **RISK_DOUBLE = 0**.

## 1. Method

- Coarse ship inventory: 65 NS (`VFX_NIAGARA_SHIP_NS_LIVE_2026-09-17.csv`).
- DETAIL pin read (emitter, renderer, material, `subuv_present`, `subuv_live`,
  SubImage): **authority** for Fix A, including post-Ctrl+S LeafPile.
- Live NS→material edges: 106 rows (`VFX_NS_MATERIAL_EDGES_2026-09-17.csv`).
- Canonical CSV merges those into 125 rows (65 NS + bound MI / masters /
  NiagaraFluids engine materials still referenced by the Water v10 systems).
- Live risks table is empty (`VFX_FIXA_RISKS_LIVE_2026-09-17.csv`).

## 2. Summary counts

| Slice | Count | Notes |
|---|---:|---|
| Ship Niagara systems | **65** | `/Game/Melodia` + `/Game/EnvSandbox`; Candidates/_Archive out |
| Canonical CSV rows | **125** | 65 ns + 36 mi + 13 master + 11 engine_mi |
| DETAIL emitter rows | **48** | pin-level SubUV / SubImage |
| Live NS→MI edges | **106** | renderer bindings |
| NS **CLEAN** | **45** | no live SubUV clock |
| NS **CLEAN_FIXA** | **5** | four Choral Sheep (SubUV off, SubImage 1×1) + LeafPile (SubUV off, **2×2 atlas kept**) |
| NS **RISK_DOUBLE** | **0** | none remaining |
| NS **N_A** (ribbon/mesh) | **15** | no sprite-atlas Fix A clock |
| Live RISK rows | **0** | `VFX_FIXA_RISKS_LIVE_2026-09-17.csv` header only |
| Unresolved owner aliases | **0** | HybridSparkles / PetalCascade / MotionTrails / FluidSplash / WoolMotes are real ChoralSheep NS |

CSV `fix_a_status` values used: `CLEAN`, `CLEAN_FIXA`, `N_A`,
`UNKNOWN` (three unbound petal-loop masters with no ship renderer). `RISK_DOUBLE`
is unused after the LeafPile apply.

## 3. Fix A headline (65 ship NS)

### 3.1 CLEAN_FIXA — `NS_Melodia_LeafPileLoop` (applied live)

`/Game/EnvSandbox/VFX/Systems/Sakura/NS_Melodia_LeafPileLoop`

- Emitter **LeafPile**; sprite; material `/Game/Effects/Environments/Leaves/Materials/MI_Leaves`
- `SubUVAnimation` **enabled = false** (was true)
- `SubImageSize` **2×2 kept** — leaf atlas variants via `MI_Leaves` SubUV Columns/Rows=2, **not** flipbook scrub. Do not claim 1×1.
- Owner Ctrl+S; dirty packages = 0. Niagara binary is not in this docs PR.

`NS_Uni_LeafDrift` also uses `MI_Leaves` and is **CLEAN** (no live SubUV).

### 3.2 CLEAN_FIXA_SUBUV_OFF — Choral Sheep (4)

All under `/Game/Melodia/Companions/ChoralSheep/VFX/`. SubUV module present,
disabled; SubImage 1×1 where applicable.

| NS | Emitter | Material |
|---|---|---|
| `NS_ChoralSheep_BeatBurst` | BeatStars | `MI_NS_ChoralSheep_BeatStar` |
| `NS_ChoralSheep_HybridSparkles` | FlipSparkles | same BeatStar MI |
| `NS_ChoralSheep_PetalCascade` | PetalLoop | `MI_NS_ChoralSheep_PetalLoop` |
| `NS_ChoralSheep_MotionTrails` | MotionRibbon (ribbon) | `MI_NS_ChoralSheep_MotionRibbon` |

BeatBurst is **FIXED/CLEAN_FIXA live**. Batch B “SubUV on 4×2” is superseded.

Sibling sheep systems, live and CLEAN (not aliases):

| NS | Emitters | Materials |
|---|---|---|
| `NS_ChoralSheep_WoolMotes` | WoolMotes | `MI_NS_ChoralSheep_WoolMote` |
| `NS_ChoralSheep_FluidSplash` | FluidGlobule, SplashBurst | `MI_NS_ChoralSheep_FluidGlobule`, `MI_NS_ChoralSheep_SplashBurst` |
| HybridSparkles SoftGlints | SoftGlints | `MI_NS_ChoralSheep_WoolMote` |
| PetalCascade PetalPile | PetalPile | `MI_NS_ChoralSheep_PetalPile` |
| MotionTrails TrailSparks | TrailSparks | `MI_NS_ChoralSheep_WoolMote` |

Live sheep MIs: BeatStar, WoolMote, PetalLoop, PetalPile, MotionRibbon,
FluidGlobule, SplashBurst.

`BP_ChoralSheep` Event Tick drives `User.BeatPulse` on all six sheep NS from
`CompanionComponent.ResonanceIntensity`. Graph contract:
[`VFX_BEATPULSE_BP_WIRE_2026-09-17.md`](VFX_BEATPULSE_BP_WIRE_2026-09-17.md)
(compile UpToDate, 0 errors; Blueprint binary not in this PR).

### 3.3 ConstellationDraw

**CLEAN.** Stars sprite → `/Game/_PROJECT/04_Materials/MooaToon/M_StardustParticle_Glow`.
SubUV live=false, SubImage 1×1. Dream\* user bus (not BeatPulse) is a separate
wiring topic.

## 4. Ship systems by bucket

### 4.1 Melodia (`/Game/Melodia/VFX/` + ChoralSheep)

| NS | Status | Live materials |
|---|---|---|
| `NS_Melusina_Ripple` | CLEAN | Static_Ripple, **Static_DropletRing** |
| `NS_Melusina_Splash` | CLEAN | SplashFlip, Static_SplashBurst |
| `NS_Melusina_ChaosDrift` | CLEAN | Static_Chaos |
| `NS_Melusina_EntropyDust` | CLEAN | Static_Dust |
| `NS_Melusina_Dust` | CLEAN | Static_Dust |
| `NS_Melusina_EyeSparkle` | CLEAN | `M_Niagara_MelodiaFlipbook` (master, SubUV off / 1×1) |
| `NS_Melusina_Arc` | CLEAN | Static_Arc |
| `NS_Melusina_Glint` | CLEAN | Static_Glint |
| `NS_Melusina_Globules` | CLEAN | Flipbook_Water, Static_GlobuleCluster |
| `NS_Melusina_ProviderSigil` | CLEAN | Static_Provider |
| `NS_Melusina_Sigil` | CLEAN | Static_Sigil |
| `NS_Melusina_Superposition` | CLEAN | StateA=Static_Glint, StateB=Static_StateB |
| `NS_Melusina_SwingTrail` | CLEAN | NoteBeam sprites + AuroraRibbon ribbons |
| `NS_Melodia_CursorTrail` | CLEAN | **Static_StarGold** |
| `NS_Melodia_ClickSparkle` | CLEAN | `/Game/Melodia/_PROJECT/VFX/Materials/MI_Niagara_Melodia_ClickSparkle` |
| `NS_Melusina_ImpactBurst` | CLEAN | Static_ImpactBurst |
| `NS_Melusina_Mist` | CLEAN | Static_Mist |
| `Melusina_WaterFX` | N_A | `M_Niagara_Ripple` (mesh/sheet) |
| `NS_ChoralSheep_WoolMotes` | CLEAN | WoolMote |
| `NS_ChoralSheep_BeatBurst` | **CLEAN_FIXA** | BeatStar |
| `NS_ChoralSheep_HybridSparkles` | **CLEAN_FIXA** | BeatStar + WoolMote |
| `NS_ChoralSheep_PetalCascade` | **CLEAN_FIXA** | PetalLoop + PetalPile |
| `NS_ChoralSheep_MotionTrails` | **CLEAN_FIXA** | MotionRibbon + WoolMote |
| `NS_ChoralSheep_FluidSplash` | CLEAN | FluidGlobule + SplashBurst |

### 4.2 EnvSandbox ship

CLEAN sprite/ribbon systems (no live SubUV): `NS_SakuraPetals_v2` (`M_SakuraPetal` +
`M_Niagara_Ripple`), `NS_SakuraPetalGust`, `NS_WindRibbonGust`, `NS_SakuraLanternMotes`,
`NS_SakuraDreamSparkle`, `NS_ConstellationDraw`, `NS_ConstellationTwinkle`,
`NS_Uni_{DustShafts,PollenSparkle,WaterMist,RainRipples,MistSheet,LeafDrift,GroundWisps,Fireflies}`,
`NS_MagicTrail` (two paths: `Systems/Magical/` and `Systems/`), `NS_MagicalHenshinBurst`,
`NS_FairyDust`, `NS_EmberMotes`, `NS_MelodiaWaterContact` (Flipbook_Water),
`NS_SeaAbove_UpwardDroplets_Prototype`, four Water v10 FLIP systems.

N_A ribbon/mesh: `NS_SDF_{PulsingGeometry,ParallaxPulse,ParallaxFish,Foliage_Vine,Foliage_Grass,Foliage_Bush}`,
`NS_Sakura{WaterPetals,PondShimmer,Petals,GroundPetals,CosmicAurora}`,
`NS_Melodia_PetalEndlessLoop`, `NS_CosmicPetalOrbit`, `NS_EscherTorusKnot`.

CLEAN_FIXA (atlas 2×2 kept): `NS_Melodia_LeafPileLoop`.

Two `NS_MagicTrail` paths are both in the 65 and both CLEAN. That duplication is
live inventory, not a merge in this PR.

## 5. Material families (live bindings)

### 5.1 Flipbook master — `M_Niagara_MelodiaFlipbook`

Material-side clock. Live sprite consumers in the 65 all have SubUV **off** and
SubImage **1×1** (EyeSparkle binds the master directly; Globules/Splash/water
contact bind Water / SplashFlip instances).

StarGold and DropletRing are **not** orphans.

### 5.2 Sakura / EnvSandbox

Live petal systems bind `M_SakuraPetal` (not `MI_Niagara_Petal` on the ship
renderers DETAIL saw). Lantern / Dream / Twinkle bind `M_Niagara_SakuraSprite`.
Mote role-tints (`MI_Niagara_Mote_*`) still bind the Uni / Ember / Fairy systems.

Unbound tracked masters (no ship renderer in the 65): `M_Niagara_PetalSprite_Loop`,
`M_Niagara_PetalPile`, `M_Niagara_SDF_Loop` — CSV **UNKNOWN**, not RISK.

### 5.3 Sheep

Seven live MIs under `Content/Melodia/Companions/ChoralSheep/VFX/Materials/`.
BeatStar / PetalLoop / MotionRibbon inherit CLEAN_FIXA from the disabled-SubUV
emitters that use them.

## 6. Orphans after the live pass

**Masters with no ship NS binding:** `M_Niagara_PetalSprite_Loop`,
`M_Niagara_PetalPile`, `M_Niagara_SDF_Loop`.

**Former orphans, now bound:** `MI_Niagara_Melodia_Static_DropletRing` (Ripple
DropletRing), `MI_Niagara_Melodia_Static_StarGold` (CursorTrail).

**Names that are assets, not aliases:** HybridSparkles, PetalCascade,
MotionTrails, FluidSplash, WoolMotes.

Candidates (`NS_*_AdvancedCandidate`, BattleBackdropPulse) stay out of the 65.

## 7. What this PR does not do

- No `.uasset` edits (LeafPile Fix A and BeatPulse BP wire live in owner-saved
  binaries; this PR documents the graph/pin contract only).
- No second MCP surface, no Python load of skill Blueprints.
