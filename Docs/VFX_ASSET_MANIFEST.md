# Melodia VFX — Niagara Asset Manifest & Unification Record (2026-08-15)

**Status:** LIVE — canonical snapshot after the 2026-08-15 unification session.
**Engine:** UE 5.8 · **Branch:** `feature/repo-lockin-20260813`
**Scope:** unify, organize, and expand the project's Niagara effects to triple-AAA;
finalize the material petal/leaf loops and flipbook family.

---

## 1. Canonical folder taxonomy

Single source of truth under `Content/EnvSandbox/VFX/` + `Content/_PROJECT/VFX/`:

```
Content/EnvSandbox/VFX/
  Systems/
    Universal/     # NS_Uni_* ambient systems (dust, pollen, fireflies, leaf drift, mist)
    Ambient/       # NS_EmberMotes, NS_FairyDust, NS_ConstellationTwinkle
    Sakura/        # petal/leaf systems incl. the two promoted endless loops
    Magical/       # henshin burst, magic trail
  Materials/
    M_Niagara_PetalMesh_Loop      # canonical mesh-petal loop (promoted 2026-08-15)
    M_Niagara_PetalSprite_Loop    # canonical far-field sprite loop (promoted 2026-08-15)
    M_Niagara_PetalPile           # canonical pile parent (promoted 2026-08-15)
    M_Niagara_SDF_Loop            # canonical SDF wrapper (promoted 2026-08-15)
    Functions/
      MF_MelodiaPetalLifecycle    # single shared loop lifecycle function (promoted 2026-08-15)
    MI_Niagara_Mote_{MistSheet,WaterMist,GroundWisps,Ember,FairyDust}
      # role-tinted material instances differentiating the 5 mote systems (new 2026-08-15)
  Candidates/      # quarantined prototypes — not promoted (kept as reference)
  _Quarantine_2026-08-15/TextureDuplicates/
    # 64 duplicate alpha/flipbook textures moved out of the canonical tree (reversible rename)

Content/_PROJECT/VFX/
  Textures/        # canonical alpha + flipbook texture library (single copy)
  Materials/
    M_Niagara_MelodiaFlipbook            # flipbook master (FlipFPS=15, Grid 4x4)
    MI_Niagara_MelodiaFlipbook_Water     # globule flipbook instance
    MI_Niagara_Melodia_SplashFlip        # metaball flipbook instance
    MI_Niagara_Melodia_Static_*          # static pattern instances (quantum palette)
```

## 2. System manifest

| System | Role | Emitter | Sim | Bounds | Renderer/Material | Contract | Status |
|---|---|---|---|---|---|---|---|
| `NS_Uni_DustShafts` | Ambient light shafts | Motes | GPU | Fixed | Sprite / `MI_Niagara_Mote` | 20 params | LIVE, culled 15km |
| `NS_Uni_PollenSparkle` | Ambient pollen | Motes | GPU | Fixed | Sprite / `MI_Niagara_Sparkle` | 20 params | LIVE, culled 10km |
| `NS_Uni_Fireflies` | Ambient fireflies | Firefly | CPU* | Fixed | Sprite+Light / `MI_Niagara_Mote` | 20 params | LIVE, culled 8km (*CPU: light renderer) |
| `NS_Uni_LeafDrift` | Ambient leaf drift | LeafDrift | GPU | Fixed | Sprite / `MI_Leaves` | 20 params | LIVE, culled 12km |
| `NS_Uni_MistSheet` | Ambient mist sheet | EmberMotes | GPU | Fixed | Sprite / `MI_Niagara_Mote_MistSheet` | 20 params | LIVE (GPU-migrated) |
| `NS_Uni_WaterMist` | Water surface mist | EmberMotes | GPU | Fixed | Sprite / `MI_Niagara_Mote_WaterMist` | 20 params | LIVE (GPU-migrated) |
| `NS_Uni_GroundWisps` | Low ground wisps | EmberMotes | GPU | Fixed | Sprite / `MI_Niagara_Mote_GroundWisps` | 20 params | LIVE (GPU-migrated) |
| `NS_Uni_RainRipples` | Rain surface ripples | Ribbon 3-emitter | CPU | Fixed | Ribbon+burst | partial | LIVE, dedup candidate |
| `NS_EmberMotes` | Ember motes | EmberMotes | GPU | Fixed | Sprite / `MI_Niagara_Mote_Ember` | 20 params | LIVE (GPU-migrated) |
| `NS_FairyDust` | Fairy dust | FairyDust | GPU | Fixed | Sprite / `MI_Niagara_Mote_FairyDust` | 20 params | LIVE (GPU-migrated) |
| `NS_ConstellationTwinkle` | Ambient twinkle | — | — | — | — | partial | LIVE |
| **`NS_Melodia_PetalEndlessLoop`** | **Focal petal loop (Infinite)** | PetalLoop | GPU | Fixed | **Mesh** `SM_SakuraPetal` 310-tri / **`M_Niagara_PetalMesh_Loop`** | 20 params | **PROMOTED 2026-08-15**, culled 8km |
| **`NS_Melodia_LeafPileLoop`** | **Ground leaf pile (Infinite)** | LeafPile | GPU | Fixed | Sprite SubUV 2x2 / `MI_Leaves` | 20 params | **PROMOTED 2026-08-15**, culled 6km |
| `NS_SakuraPetals_v2` | Reference living-sakura | Petals CPU + 2 receivers | CPU | Fixed | Sprite+Mesh | — | LIVE reference |
| `NS_SakuraPetals_v3_Candidate` | v3 event-chain candidate | Petals CPU + receivers | CPU | Fixed | Sprite+Mesh | 20 params | CANDIDATE (valid) |
| `NS_SakuraPetalPiles_Candidate` | Transient piles | — | — | Fixed | — | scalars | CANDIDATE |
| `NS_SurrealSakuraGust_Candidate` | Hero gust | — | — | Fixed | Mesh Nanite | scalars | CANDIDATE |

## 3. Material loop family (unified 2026-08-15)

| Material | Source | Intent | Compile |
|---|---|---|---|
| `M_Niagara_PetalMesh_Loop` | dup of `M_NiagaraPetal_Loop_v2_Candidate` | Mesh petal loop (Masked, two-sided, DefaultLit) | clean |
| `M_Niagara_PetalSprite_Loop` | dup of `M_NiagaraPetal_Loop_Candidate` | Far-field sprite loop | clean |
| `M_Niagara_PetalPile` | dup of `M_SakuraPetal` | Pile parent | clean |
| `M_Niagara_SDF_Loop` | dup of `M_Niagara_SakuraSprite` | SDF wrapper | clean |
| `MF_MelodiaPetalLifecycle` | promoted from `MF_MelodiaPetalLifecycle_Candidate` | single lifecycle loop function | clean |

Instance token surface (per finalization plan §1): Palette A/B, opacity, emissive cap,
loop speed, flutter, sheen, reaction gain, audio gain, wind gain, density.

## 4. Flipbook family (finalized 2026-08-15)

| Asset | Detail |
|---|---|
| `M_Niagara_MelodiaFlipbook` | Master: FlipFPS=15, GridCols/Rows=4, texture param `FlipbookTexture` |
| `MI_Niagara_MelodiaFlipbook_Water` | → `T_Alpha_water_globule_flipbook` (4x4, 1024^2) |
| `MI_Niagara_Melodia_SplashFlip` | → `T_Alpha_fluid_metaball_flipbook` (2048^2), Grid 4x4 override |
| `M_Niagara_MelodiaFlipbook` default | → `T_Alpha_sparkle_pulse_flipbook` (4x4, 1024^2) |
| Consumers | `NS_Melodia_ClickSparkle`, `NS_Melusina_EyeSparkle`, `NS_Melusina_Globules`, `NS_Melusina_Splash` — all 0 err / 0 warn |

**Dedup:** 64 duplicate texture assets (full mirror of the library in
`_PROJECT/VFX/Alphas/` + partial mirror in `Content/Alphas_Sparkles/`) were moved to
`EnvSandbox/VFX/_Quarantine_2026-08-15/TextureDuplicates/` via reversible rename.
Canonical copies live only under `_PROJECT/VFX/Textures/`. `T_Spark_Sparkle4`
(16 refs) and `T_Spark_Twinkle8` (6 refs) were kept in place — they are referenced.

**Bake-set note:** source library under `C:\EnvironmentPortfolio\VFX\` contains only 3
flipbook grids (sparkle-pulse, water-globule, fluid-metaball) — all imported. The
remaining ~50 sources are single-frame alphas, not flipbooks. The "expand bake set"
(bubbles/glints/ripples/fish/caustics) requires new multi-frame source grids; the UE
5.8 Niagara Flipbook Baker path is documented in
`Docs/SDF_UTILITY_RETRO_GRAPHICS_CHEATS_PLAN_2026-08-09.md`.

## 5. AAA quality pass (2026-08-15)

- **Camera-distance culling** enabled on 6 ambient systems (max distances 6–15 km,
  role-appropriate).
- **Frustum culling** enabled on the mesh renderer (`PetalEndlessLoop`).
- **GPU migration:** 5 mote systems moved CPU→GPU with fixed bounds
  (`MistSheet`, `WaterMist`, `GroundWisps`, `EmberMotes`, `FairyDust`) — 0 err/0 warn.
  `NS_Uni_Fireflies` stays CPU (Light renderer requires CPU sim).
- **Cluster differentiation:** the 5 systems sharing emitter GUID
  `FA602D884154410214136DA477BED11D` now each consume a distinct role-tinted MI.
- **Mesh lanes:** PetalEndlessLoop uses the standard 310-tri `SM_SakuraPetal`
  (EnvSandbox); hero-focal Nanite lane remains for curated gusts.

## 6. Level set-dressing (ZenForestTest — canonical)

| Actor | System |
|---|---|
| NiagaraActor1 | `NS_Uni_DustShafts` |
| NiagaraActor2 | `NS_Uni_PollenSparkle` |
| NiagaraActor3 | `NS_Uni_Fireflies` |
| NiagaraActor4 | `NS_Uni_LeafDrift` |
| NiagaraActor5 | **`NS_Melodia_PetalEndlessLoop`** (promoted) |
| FX_Melodia_LeafPileLoop | **`NS_Melodia_LeafPileLoop`** (promoted, new placement) |

## 7. Verification evidence

- `Saved/Audit/niagara_scoped_audit_2026-08-15.json` — per-system validity (note: full
  `niagara_ecosystem_audit.py --contract` sweep times out on the `NS_Melodia_CursorTrail`
  engine-bug trigger; scoped run covers all owned systems).
- Per-system diagnostics re-verified via Monolith after every edit (0 err / 0 warn).
- Flipbook consumers re-verified after texture quarantine (4/4 compile clean).

## 8. Open items / deferred (owner sign-off required)

1. **Full `niagara_ecosystem_audit.py --contract`** still blocked on the CursorTrail
   engine bug — run only with that system excluded.
2. **SDF candidate conformance** (6 systems) — unchanged, still prototype.
3. **RainRipples 3-emitter ribbon-burst cluster** — dedup candidate (same family as
   MagicalHenshinBurst/PetalGust disconnected event chain).
4. **Flipbook bake-set expansion** — blocked on new multi-frame source grids from Blender.
5. **`NS_SakuraPetals` v1 retirement** and **`NS_SakuraPetals_v3_Candidate` promotion**
   — require visual A/B in-level before promoting; owner sign-off for retirement.
6. **Quality tiers** (Fast/Standard/Hero via scalability) — design is per the 08-01
   finalization plan §5; not yet wired to a project-wide quality switch.
