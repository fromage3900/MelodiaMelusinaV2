# 11 — Gate 11 (P1, only if P0 is healthy): Faraway Mother Vellum factory

| | |
|---|---|
| **Purpose** | Reusable textile-terrain archetypes baked as deterministic variants, extending the Faraway Mother fabric families. |
| **Authority** | Faraway Mother level/PCG owners (`LV_FarawayMother_Prototype`, 8 × 8 km; `specs/pcg/faraway_mother_pcg_manifest.v1.json`); World Zero genome `specs/universe/faraway_mother.world_genome.v1.json`. Baked assets only. **No runtime cloth simulation.** |
| **Inputs** | Existing families to extend (do not restart): `Tools/Houdini/vdm_fabric_mountains/vdm_fabric_baker.py`, `Tools/Houdini/sea_above_reef/build_cloth_mountains.py`, `Houdini/FarawayDrape.hip(nc)`, `Docs/Houdini/FARAWAY_MOTHER_DRAPE_SPEC_2026-09-01.md`, `Docs/Production/FARAWAY_MOTHER_P1_RESONANCE_FIELD_INTEGRATION_SPEC.md`. |
| **Outputs** | Per archetype × variant: rest mesh (OBJ/FBX), optional VDM/displacement map, optional short deformation cache → baked VAT/LUT (the OBJ path cannot carry per-vertex VAT; see the kelp half-wrap-LUT precedent), manifest. |
| **Evidence** | `Saved/Audit/houdini_foundry/vellum_textile_<archetype>/` |
| **Status** | STAGED, lowest priority. |

## Archetypes

pleated silk mountain · velvet valley · lace cliff · hanging textile forest · ribbon canopy · embroidered terrain · fabric arch · draped architecture.

## Rules

1. One recipe per archetype (product `vellum_textile`), 3–5 seeds each, named `<archetype>_s<seed>`.
2. The Vellum sim runs on the heavy lane. Export the **settled** frame only unless a deformation bake is explicitly wanted.
3. The Faraway static field (`faraway_static_field.py`) is the field authority for tension/resonance. Textiles *read* it, e.g. pleat density ∝ `WorldField.Tension`.
4. Scale: Houdini metres, UE ×100 cm, recorded in the manifest.

## Done when

Brennan picks canonical variants from a contact sheet. Each picked variant has a verifying manifest. UE import is follow-up work on the owner PC unless Gates 1–4 finished early.
