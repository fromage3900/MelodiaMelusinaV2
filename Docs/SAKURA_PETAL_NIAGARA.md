# Sakura Petal Niagara — Professional Guide

Portfolio-grade petal VFX for `L_SakuraPath`: canopy drift, ground path layer, and wind gust story beat. Sparkle, motes, and pond remain stable supporting layers.

## PCG vs Niagara responsibility

| Layer | Owner | Notes |
|-------|-------|-------|
| Static grass / moss ground cover | `PCG_Sakura_GroundCover` | ISM band 400–2500; greybox grass proxy until CC0 kit |
| Fallen petal **drift** on path | `NS_SakuraGroundPetals` | 30–80 visible; sparse under trunks (~200 UU falloff) |
| Canopy petal **drift** | `NS_SakuraPetals_v2` | Canonical spawn; 400–1200 visible in default volume |
| Wind gust story beat | `NS_SakuraPetalGust` | One-shot burst; `auto_activate=False` on level |
| Air shimmer / lantern / pond | Sparkle / Motes / Pond systems | Unchanged scaffolds |

**Deferred:** `PCG_Sakura_FallenPetals` — Niagara owns fallen drift; avoid double scatter with ground petals.

## Canonical canopy (v2)

`NS_SakuraPetals_v2` is the **canonical** canopy system for `VFX_SakuraCanopy` until v1 is retired:

- Python alias: `canonical_canopy_system()` prefers v2 when the asset exists on disk
- Legacy `NS_SakuraPetals` remains for showcase A/B comparison
- **Promotion procedure:** when v2 passes PIE review, move v1 to `_Deprecated/` and optionally rename v2 → `NS_SakuraPetals`

## MPC scalar cheat sheet (`MPC_SakuraDream`)

| Scalar | Default | Canopy | Ground | Gust | Material |
|--------|---------|--------|--------|------|----------|
| `WindStrength` | 0.3 | wind force magnitude | — | — | emissive scroll boost |
| `PetalDensity` | 1.0 | spawn rate multiplier | spawn rate multiplier | — | opacity clamp |
| `GustTrigger` | 0.0 | — | — | burst trigger (edge-detect) | — |
| `SparklePulse` | 0.0 | — | — | — | emissive pulse (sparkle systems) |

Wire Niagara emitters to read MPC via **Collection Parameter** modules or blueprint pulses on `MPC_SakuraDream`.

## Scene spawn anchors

Spawns derive from `L_SakuraPath` greybox actors via `_spawn_anchors_from_scene()`:

| Actor | Anchor | Source |
|-------|--------|--------|
| `VFX_SakuraCanopy` | Trunk cluster centroid, Z≈420 | `Trunk_*` actors |
| `VFX_SakuraGround` | Path midline, Z≈20 | `PathStone_*` row |
| `VFX_PetalGust` | Above torii, Z≈350 | `Torii_*` centroid |

Fallbacks match `SCENE_ANCHOR_FALLBACKS` in `setup_sakura_niagara.py` when scene actors are missing.

## Build & validate

```text
py Content/Python/run_sakura_niagara_plan.py --rebuild
py Content/Python/setup_sakura_niagara.py --spawn-only
py Content/Python/validate_sakura_niagara.py
py Content/Python/audit_sakura_petal_niagara.py
py Content/Python/run_sakura_niagara_plan.py --showcase
```

Reports:

- `Saved/Audit/sakura_niagara_build.json`
- `Saved/Audit/sakura_niagara_validation.json`
- `Saved/Audit/sakura_petal_niagara.json`

Portfolio menu: **LiveLink → Portfolio → Run Sakura Petal Audit**

## PIE acceptance checklist

| System | Acceptance |
|--------|------------|
| **Canopy v2** | Pink/cream petals drift through torii frame; no white clipping at exposure bias 11; 400–1200 visible |
| **Ground** | Fallen petals readable on moss/path stones; sparse under trunks; no z-fight with PCG grass |
| **Gust** | One burst reads as storybook wind; `GustTrigger` pulse visible; no pop-in at spawn edge |
| **Pipeline** | `validate_sakura_niagara.py` all_ok + petal audit `critical_count=0` (editor; particle bands PIE-only) |

## Hand-tune (Niagara Editor)

Python cannot fully author emitters in UE 5.8. After scaffold build:

1. **NS_SakuraPetals_v2** — spawn box 1200×800×400, curl wind, SubUV across `T_Sakura_Petal` / `T_Sakura_Blossom`, assign `MI_Niagara_Petal`
2. **NS_SakuraGroundPetals** — flat path box, trunk distance falloff ~200 UU, lower emissive than canopy
3. **NS_SakuraPetalGust** — burst 40–80 instances, bind `GustTrigger` / `User.BurstScale`, optional `User.AutoLoopDemo` for reel only

See `SAKURA_TUNING_NOTES` in `setup_sakura_niagara.py` for per-system detail.

## Headless vs editor

- **Headless (`-nullrhi`):** asset existence, spawn alignment, MPC material probe — particle count bands skipped
- **Editor PIE:** visual quality gate (pink/cream read, bloom, particle bands)
