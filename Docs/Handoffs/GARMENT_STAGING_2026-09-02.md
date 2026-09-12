# GARMENT STAGING — Universal Garment Push, Ready-Plan (2026-09-02)

**Goal.** Stage the Shorewake 'singing veil' garment umbrella (Skirt_Full / Bodice
layers / Collar / Veil) into `LV_SeaAbove_Prototype` on `CanonicalLandscape` with
height-aware, cymatic-wired, polished-PBR placement. **No floating pieces**, no new
landscape, no `.uasset` touched — offline planner only.

## What was delivered

| Artifact | Path |
|---|---|
| numpy height-aware generator | `Tools/PCG/build_garment_veil_staging.py` |
| staging manifest (120 pts) | `specs/garment_staging/garment_veil_staging.v1.json` |
| height-aware placement plan (120) | `specs/garment_staging/garment_veil_staging_placements.json` |
| polished-PBR reconciliation (seed 20260902) | `Saved/Audit/universal_garment/garment_staging_plan.json` |

**GENERATED** with `./.venv/Scripts/python.exe Tools/PCG/build_garment_veil_staging.py`
(numpy 2.4.6, seed 20260902). **120 points** = 30 × {Skirt, Bodice, Collar, Veil}.

## Height-aware contract (verified)
Every placement base-`Z` anchors to the recorded sea-line (`13455` cm) plus a layer
standoff; `height_cm` is the landscape floor (13405 + cymatic swell) below it. Assert
`base_z >= height_cm` for all 120 placements → **floating pieces: NONE**. Editor lane
re-verifies with a real line-trace before commit.

## Garment wiring per layer
| Layer | Zone | Harmonic | Placement MI (verified on disk) | Master |
|---|---|---|---|---|
| Skirt_Full | Skirt | 2,4 | `MI_SeaAbove_SurfaceOcean` | `M_Universal_Enhanced_Fabric` |
| Bodice_Base | Bodice | 3,5 | `MI_SeaAbove_FalseOcean` | `M_Master_Nikki` |
| Bodice_Lace | Bodice | 3,5 | `MI_SeaAbove_UpwardDroplet` | `M_Master_Toon_Universal_Alpha` |
| Collar | Collar | 1,3 | `MI_SeaAbove_FalseOcean` | `M_Master_Nikki` |
| Veil | Veil | 4,4 | `MI_SeaAbove_UpwardDroplet` | `M_Master_Toon_Universal_Alpha` |

Harmonic (4,4) for the Veil matches the recorded Shorewake-gown hero mode
(`Docs/LookDev/MELODIA_PERCEPTUAL_LOD_LOOKDEV_ARCHITECTURE.md:83`).

## Polish-PBR reconciliation + MI gaps
Reconciled families: `garment_refresh` (base PBR → Skirt / Bodice_Base / Collar),
`garment_refresh/cymatic` (reactive → Bodice_Lace / Veil), `water-veil` (shared cymatic
→ Veil / Bodice_Lace). **8 gaps flagged** — none of the three polish-map families is
verified on disk (0 matches; water-veil is placeholder-only, `MI_T_FarawayMother_*`
phantom). Every garment layer currently lacks a verified polish map wired to its MI:
- `MI_SeaAbove_UpwardDroplet` ← Veil, Bodice_Lace (needs `garment_refresh/cymatic`; Shorewake `T_*` dress set absent)
- `MI_SeaAbove_SurfaceOcean` ← Skirt_Full (needs `garment_refresh` base PBR)
- `MI_SeaAbove_FalseOcean` ← Bodice_Base, Collar (needs `garment_refresh` base PBR)

## Next
Author `garment_refresh` base PBR + `garment_refresh/cymatic` reactive maps, apply the
placements via an editor/Monolith height-aware lane, and re-map phantom FarawayMother
PBR_Auto garment MIs onto the verified fabric master family
(`SURREAL_FABRIC_NIKKI_AUDIT_2026-09-02`).