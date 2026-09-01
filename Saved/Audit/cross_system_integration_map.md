# Cross-System Integration Map

> Generated: 2026-09-01T04:15:00Z
> Source: grand_review_expansion_plan_2026-09-01.json (phase_4)
> Status: offline_spec — owner must materialize in Docs/ structure

## 1. Cymatics ↔ Rhythm Combat

| Cymatic Pattern | Rhythm Combat Mapping | Status |
|---|---|---|
| Standing wave nodes | Hit zone boundaries | Spec only |
| Interference patterns | Grade pattern overlays | Spec only |
| Resonance frequency | Tempo/bpm modulation | Spec only |
| Chladni figures | Attack formation shapes | Spec only |

## 2. Faraway Mother ↔ Wardrobe Fabric System

| FarawayMother Asset | Wardrobe Authority Mapping | Status |
|---|---|
| Fabric textures (T_FM_*) | Material input for wardrobe texturing | Spec only |
| GN builder geometry | PCG population for generated outfits | Spec only |
| PBR suites (Corset, Cradle, Gown, Mantle, Ornament, Veil) | Cosmetic catalog entries | 47 PNG+uasset pairs ready |

## 3. Cymatics ↔ Water Ripple Animation

| Cymatic Behavior | Water System Mapping | Status |
|---|------|
| Standing wave propagation | Ripple animation vertex shader | Spec only |
| Frequency harmonics | Wave spectrum distribution | Spec only |
| Boundary reflection | Shoreline interaction model | Spec only |

## 4. Cross-System Material Pipeline

```
cymatic PBR (21 variants, 1665 PNGs)
    ↓
water PBR (cymatic patterns as normal/height inputs)
    ↓
wardrobe PBR (fabric texture pipeline)
    ↓
Faraway Mother suites (6 PBR suites in Content/Textures/FarawayMother_Suites/)
```

## 5. Documentation Gaps

- `faraway_onboarding_guide.md` — NOT FOUND (grand_review rec_2_faraway_p1)
- `grand_review_document.md` — NOT FOUND (grand_review rec_6_grand_documentation)
- `onboarding_guide.md` — NOT FOUND (grand_review rec_6_grand_documentation)
- `hythm_monolith_bridge_report.json` — NOT FOUND (grand_review rec_3_hythm_monolith_bridge)
- `P1_TASK_LEDGER.json` — NOT FOUND

## 6. Owner Actions Required

1. Move this doc to `Docs/Integration/cross_system_integration_map.md`
2. Create `P1_TASK_LEDGER.json` referencing faraway_p1_status.json as evidence
3. Update `Docs/Production/GN_TAXONOMY_2026-08-29.md` to 238 builders + mother category
4. Generate V3 PBR sets via hython/Copernicus (see faraway_mother_v3_asset_import_gap_spec_2026-09-01.json)