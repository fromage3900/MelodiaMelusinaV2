# VFX Fix A risks — flipbook double-scrub (2026-09-17)

**Type:** LIVE_MONOLITH pin read (DETAIL CSV is authority).
**Home:** `Docs/VFX/`.
**Status authority:** `CURRENT_STATE.md`.
**Scope:** 65 ship Niagara systems under `/Game/Melodia` + `/Game/EnvSandbox`.
`Candidates/` and `_Archive` are excluded.

This file does **not** claim `NS_Melodia_LeafPileLoop` was fixed in-engine.

## 0. What Fix A is

**Risk:** a material instance owns flipbook scrub (`Grid` / `SubImage` / `FlipFPS`)
**and** the Niagara emitter has `SubUVAnimation` enabled and/or sprite
`SubImageSize ≠ 1×1`. Both clocks advance the atlas. Playback looks broken
(double-speed, skipped cells, torn frames).

**Fix A:** the material owns scrub. Disable Niagara `SubUVAnimation`. Set
renderer `SubImageSize` to `1×1`.

`CLEAN_FIXA_SUBUV_OFF` means the SubUV module is **present but disabled**, and
`SubImageSize` is `1×1` where the renderer exposes it. That is the applied Fix A
shape, not a remaining double-scrub.

Do **not** invert that without an owner look call: Niagara-owns-scrub
(`SubUVAnimation` + `SubImageSize` matching the sheet, material sampling the
full UV) is a valid single-owner design. Double-scrub is the defect.

## 1. RISK_DOUBLE — one system only (not fixed)

| Item | Live pin read (DETAIL) | `fix_a_status` |
|---|---|---|
| **`NS_Melodia_LeafPileLoop`** `/Game/EnvSandbox/VFX/Systems/Sakura/NS_Melodia_LeafPileLoop` | Emitter **LeafPile**; renderer sprite; **`SubUVAnimation` enabled = true**; **`SubImageSize` 2×2**; material `/Game/Effects/Environments/Leaves/Materials/MI_Leaves`. Same double-scrub class BeatBurst used to have. | **RISK_DOUBLE** |

Coarse 65-NS inventory scored LeafPile **CLEAN** (0 coarse RISK). The SubImageSize
property read is what caught it. Edges CSV also lists LeafPile `fix_a=CLEAN`,
`subX/subY=2/2`, `subuv_live=False` — that `subuv_live` disagrees with DETAIL.
**DETAIL wins.** Do not treat the coarse/edges CLEAN as a fix.

`NS_Uni_LeafDrift` also binds `MI_Leaves` and is **CLEAN** (no live SubUV on that
emitter). RISK is the LeafPile emitter, not every consumer of the MI.

No other ship system in the 65 is RISK_DOUBLE.

## 2. CLEAN_FIXA_SUBUV_OFF — four Choral Sheep systems

SubUV module present, **disabled**; SubImage `1×1` where applicable. These are
real assets under `/Game/Melodia/Companions/ChoralSheep/VFX/`.

| NS | Emitter | Material | Notes |
|---|---|---|---|
| `NS_ChoralSheep_BeatBurst` | BeatStars | `MI_NS_ChoralSheep_BeatStar` | **FIXED / CLEAN_FIXA live.** Batch B 2026-09-12 “SubUV on, SubImageSize 4×2” is **superseded**. Not RISK. |
| `NS_ChoralSheep_HybridSparkles` | FlipSparkles | same `MI_NS_ChoralSheep_BeatStar` | SoftGlints → `MI_NS_ChoralSheep_WoolMote` is CLEAN (no SubUV module). |
| `NS_ChoralSheep_PetalCascade` | PetalLoop | `MI_NS_ChoralSheep_PetalLoop` | PetalPile → `MI_NS_ChoralSheep_PetalPile` is CLEAN. |
| `NS_ChoralSheep_MotionTrails` | MotionRibbon (ribbon) | `MI_NS_ChoralSheep_MotionRibbon` | TrailSparks → `MI_NS_ChoralSheep_WoolMote` is CLEAN. |

Also live and **CLEAN** (not aliases, not missing):

- `NS_ChoralSheep_WoolMotes` → `MI_NS_ChoralSheep_WoolMote`
- `NS_ChoralSheep_FluidSplash` → `MI_NS_ChoralSheep_FluidGlobule` + `MI_NS_ChoralSheep_SplashBurst`

## 3. Other live confirmations (stale claims corrected)

| Claim from documentary first pass | Live result |
|---|---|
| BeatBurst is RISK until Monolith confirms Fix A | **CLEAN_FIXA_SUBUV_OFF.** SubUV present, live=false, SubImage 1×1. |
| HybridSparkles / PetalCascade / MotionTrails / FluidSplash / WoolMotes are unresolved aliases | **Real NS** under `Content/Melodia/Companions/ChoralSheep/VFX/`. |
| ConstellationDraw Fix A OK; Dream\* bus (not BeatPulse); material unnamed | **CLEAN.** Stars sprite → `M_StardustParticle_Glow`. SubUV live=false, SubImage 1×1. Dream\* user bus is a **separate** wiring topic, not a double-scrub proof. |
| ClickSparkle / EyeSparkle / Globules / Splash UNKNOWN (gitignored here) | **CLEAN** on DETAIL. ClickSparkle binds `MI_Niagara_Melodia_ClickSparkle` (`/Game/Melodia/_PROJECT/...`). EyeSparkle binds the flipbook **master** with SubUV off / 1×1. |
| StarGold / DropletRing orphan MIs | **Live-bound.** StarGold → `NS_Melodia_CursorTrail`. DropletRing → Ripple emitter on `NS_Melusina_Ripple`. |
| Superposition StateB parent unverified | StateA = `MI_Niagara_Melodia_Static_Glint`, StateB = `MI_Niagara_Melodia_Static_StateB`. Both CLEAN. |
| `NS_SakuraPetals_v2` SubUV + `MI_Niagara_Petal` UNKNOWN | **CLEAN.** Live material is `M_SakuraPetal` (+ mesh `M_Niagara_Ripple` pond). No live SubUV. |

## 4. Coarse vs DETAIL (do not mix)

| Source | Ship NS scores |
|---|---|
| Coarse `VFX_NIAGARA_SHIP_NS_LIVE_2026-09-17.csv` | **50 CLEAN / 15 N_A_RIBBON_MESH / 0 RISK** |
| DETAIL `VFX_FIXA_DETAIL_2026-09-17.csv` (authority) | **45 CLEAN / 4 CLEAN_FIXA_SUBUV_OFF / 1 RISK_DOUBLE / 15 N_A** (the 15 N_A are systems DETAIL did not need to pin-read as sprite-atlas clocks) |

Canonical CSV `fix_a_status` follows DETAIL for the four sheep NS and LeafPile.

## 5. Out of scope (do not call Fix A)

- `Candidates/` and `_Archive` (excluded from the 65).
- UltraDynamicSky `Basic_SubUV_Animation`, TurnBasedJRPG `M_Fire_SubUV` / explosion sheets, ArtOfShader glitch NS, Greybox `NS_WaterFall_*`, Nikki fixture JSON systems never proven on disk.
- Cloth/Copernicus flipbook masters (`MI_Copernicus_*_Flipbook`, PearlWoven frame stacks).
- NiagaraFluids engine materials on the Water v10 FLIP systems (including `WhitewaterMaterial` SubImage 8×8 with SubUV off). Not a Melodia sprite-atlas owner.
- PPV / StarryNight (separate work order).
- Applying Fix A to LeafPile — **document RISK only** in this PR. No `.uasset` edits.
