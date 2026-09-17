# VFX Fix A risks — flipbook double-scrub (2026-09-17)

**Type:** LIVE_MONOLITH pin read + owner-saved LeafPile apply.
**Home:** `Docs/VFX/`.
**Status authority:** `CURRENT_STATE.md`.
**Scope:** 65 ship Niagara systems under `/Game/Melodia` + `/Game/EnvSandbox`.
`Candidates/` and `_Archive` are excluded.

**Ship RISK_DOUBLE = 0.** Live risks CSV is empty:
[`VFX_FIXA_RISKS_LIVE_2026-09-17.csv`](VFX_FIXA_RISKS_LIVE_2026-09-17.csv).

## 0. What Fix A is

**Risk:** a material instance owns flipbook scrub (`Grid` / `SubImage` / `FlipFPS`)
**and** the Niagara emitter has `SubUVAnimation` enabled. Both clocks advance the
atlas. Playback looks broken (double-speed, skipped cells, torn frames).

**Fix A (flipbook):** the material owns scrub. Disable Niagara `SubUVAnimation`.
Set renderer `SubImageSize` to `1×1`.

**Fix A (static atlas, LeafPile):** disable Niagara `SubUVAnimation` and **keep**
`SubImageSize` at the atlas grid. `MI_Leaves` is a 2×2 static leaf atlas
(`SubUV Columns/Rows=2`), not a flipbook clock. SubImage 2×2 selects variants.
Do **not** claim LeafPile is SubImage 1×1.

`CLEAN_FIXA` / `CLEAN_FIXA_SUBUV_OFF` means SubUV is **present but disabled**.
That is the applied Fix A shape, not a remaining double-scrub.

## 1. RISK_DOUBLE — none remaining

The only prior RISK was `NS_Melodia_LeafPileLoop`. Owner applied Fix A and
Ctrl+S (dirty packages = 0). Receipt:
[`VFX_FIXA_LEAFPILE_2026-09-17.md`](VFX_FIXA_LEAFPILE_2026-09-17.md).

| Item | After Ctrl+S | `fix_a_status` |
|---|---|---|
| **`NS_Melodia_LeafPileLoop`** `/Game/EnvSandbox/VFX/Systems/Sakura/NS_Melodia_LeafPileLoop` | Emitter **LeafPile**; sprite; **`SubUVAnimation` enabled = false**; **`SubImageSize` 2×2 kept** (atlas variants via `MI_Leaves`); material `/Game/Effects/Environments/Leaves/Materials/MI_Leaves` | **CLEAN_FIXA** |

`NS_Uni_LeafDrift` also binds `MI_Leaves` and stays **CLEAN** (no live SubUV).

## 2. CLEAN_FIXA — five systems

### 2.1 Choral Sheep (SubUV off, SubImage 1×1)

Real assets under `/Game/Melodia/Companions/ChoralSheep/VFX/`.

| NS | Emitter | Material | Notes |
|---|---|---|---|
| `NS_ChoralSheep_BeatBurst` | BeatStars | `MI_NS_ChoralSheep_BeatStar` | **FIXED / CLEAN_FIXA live.** Batch B 2026-09-12 “SubUV on, SubImageSize 4×2” is **superseded**. |
| `NS_ChoralSheep_HybridSparkles` | FlipSparkles | same `MI_NS_ChoralSheep_BeatStar` | SoftGlints → `MI_NS_ChoralSheep_WoolMote` is CLEAN. |
| `NS_ChoralSheep_PetalCascade` | PetalLoop | `MI_NS_ChoralSheep_PetalLoop` | PetalPile → `MI_NS_ChoralSheep_PetalPile` is CLEAN. |
| `NS_ChoralSheep_MotionTrails` | MotionRibbon (ribbon) | `MI_NS_ChoralSheep_MotionRibbon` | TrailSparks → `MI_NS_ChoralSheep_WoolMote` is CLEAN. |

Also live and **CLEAN** (not aliases): WoolMotes, FluidSplash.

BeatPulse user-bus wire on those six NS: [`VFX_BEATPULSE_BP_WIRE_2026-09-17.md`](VFX_BEATPULSE_BP_WIRE_2026-09-17.md)
(`BP_ChoralSheep` Event Tick → `User.BeatPulse` from `CompanionComponent.ResonanceIntensity`).
Binary is not in this PR.

### 2.2 LeafPile (SubUV off, SubImage **2×2 kept**)

Atlas grid is intentional. Only the Niagara SubUV clock was disabled.

## 3. Other live confirmations (stale claims corrected)

| Claim from documentary first pass | Live result |
|---|---|
| BeatBurst is RISK until Monolith confirms Fix A | **CLEAN_FIXA.** SubUV present, live=false, SubImage 1×1. |
| LeafPile is RISK_DOUBLE / not fixed in-engine | **CLEAN_FIXA.** SubUV off; SubImage **2×2 kept**. Owner Ctrl+S. |
| HybridSparkles / PetalCascade / MotionTrails / FluidSplash / WoolMotes are unresolved aliases | **Real NS** under `Content/Melodia/Companions/ChoralSheep/VFX/`. |
| ConstellationDraw Fix A OK; Dream\* bus (not BeatPulse); material unnamed | **CLEAN.** Stars sprite → `M_StardustParticle_Glow`. Dream\* user bus is a **separate** wiring topic. |
| ClickSparkle / EyeSparkle / Globules / Splash UNKNOWN | **CLEAN** on DETAIL. |
| StarGold / DropletRing orphan MIs | **Live-bound.** StarGold → CursorTrail. DropletRing → Ripple. |

## 4. Coarse vs DETAIL (do not mix)

| Source | Ship NS scores |
|---|---|
| Coarse `VFX_NIAGARA_SHIP_NS_LIVE_2026-09-17.csv` | originally 50 CLEAN / 15 N_A / 0 RISK (missed LeafPile SubUV live) |
| DETAIL after LeafPile Ctrl+S | **45 CLEAN / 5 CLEAN_FIXA / 0 RISK_DOUBLE / 15 N_A** |
| `VFX_FIXA_RISKS_LIVE_2026-09-17.csv` | **0 rows** |

LeafPile CLEAN_FIXA is **not** SubImage 1×1.

## 5. Out of scope (do not call Fix A)

- `Candidates/` and `_Archive` (excluded from the 65).
- UltraDynamicSky `Basic_SubUV_Animation`, TurnBasedJRPG `M_Fire_SubUV` / explosion sheets, ArtOfShader glitch NS, Greybox `NS_WaterFall_*`, Nikki fixture JSON systems never proven on disk.
- Cloth/Copernicus flipbook masters.
- NiagaraFluids engine materials on Water v10 FLIP (including `WhitewaterMaterial` SubImage 8×8 with SubUV off).
- PPV / StarryNight (separate work order).
- Committing Niagara / Blueprint `.uasset` binaries in this PR.
