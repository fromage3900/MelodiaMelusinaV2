# Faraway Mother — Cloth Tiers per Garment (Nikki Principle 3 + Cost Ladder 10)

**Date:** 2026-09-02
**Authority:** `Docs/Research/INFINITY_NIKKI_UE5_TRANSLATION_FOR_MELODIA_2026-08-30.md` §3-5,10 + `Docs/Art/FAR_AWAY_MOTHER_PRODUCTION_SHEET_2026-08-29.md`
**Level:** `LV_FarawayMother_Prototype` — `Content/Python/faraway_mother_prototype_build.py`

## Rule (Nikki)
> The garment piece carrying gameplay meaning receives the expensive solution. The rest support it cheaply.

Cost ladder: `Material/WPO → Niagara/instanced → authored transform/spline → Chaos → Houdini VAT/cache → custom runtime`

## Per-placement tiers

| # | Label | Mesh | MI | Screen role | Tier | Cost | Why this tier |
|---|-------|------|----|-------------|------|------|---------------|
| 1 | FM_Ridge_Rosette_Crest | SM_Orn_RosetteMedallion | MI_Copernicus_GildedLoom | Ridge hero landmark (player navigates by it) | **A rigid authored** | Cheap (static + baked rotation) | Ornament is structured metal/filigree — Chaos would add noise. Deterministic. |
| 2 | FM_Valley_Arch_Entrance | SM_ATL_Palace_ArchA | MI_Mother_Mantle (NightSkyVelvet) | Valley threshold / traversal gate | **C WPO** (`MF_FabricMountainWPO` wind + cymatic) | Cheap | Arch drape is distant environmental cloth — WPO sufficient, no collision needed. |
| 3 | FM_Shoulder_Capital | SM_Orn_ColumnCapital | MI_Copernicus_SilkWaterfall | Shoulder fold landmark | **A rigid authored** | Cheap | Stone/column cap — stiff, no sim. |
| 4 | FM_Heart_Finial_Gate | SM_Orn_PendantFinial | MI_Copernicus_FinalDreamweaver | Heart Gate hero — rhythm puzzle closes/opens route | **B Chaos Cloth** (planned) / **C WPO** until then | Expensive (gameplay meaning) | Finial veil at Heart Gate is the ability-gated cloth seam — player resonance releases tension. Give it collision fidelity. Until Chaos wired, WPO with BeatPulse flag `tier=B_pending`. |
| 5 | FM_Torso_RoseWindow | SM_Orn_RoseWindow_8Petal | MI_Mother_Veil (AquaticLullabyLace) | Torso vista | **B Chaos Cloth** (sheer/lace) | Expensive (sheer translucency) | Nikki OIT lesson: minimize overlapping translucent layers (≤2). RoseWindow lace is translucent hero — needs depth-priority + precomputed hidden-body mask. WPO for distant view, Chaos for approach. |

## Terrain fabric

| Asset | Tier | Notes |
|-------|------|-------|
| SM_FarawayMother_FabricRidge (Nanite terrain, 32k tris, 4km) | **C WPO** (`MF_FabricMountainWPO` 4-layer: Macro 50m + Medium 10m + Micro + Wind) + **D VAT** for impossible contraction event | Kilometer-scale draped anatomy — WPO handles breathing cheap; authored VAT cache for the contraction when Heart Gate opens (Houdini `HDA_CH_WardrobeIntersectionAudit` style bake, not runtime sim). Never Chaos. |
| FM_MoonHaze_VolumeBox | **C WPO** (frost haze drift) | Implies limbs without mesh — cheap noise. |
| Fog / PP | Not cloth — see `SURREAL_FABRIC_NIKKI_AUDIT_2026-09-02.md` Fix 3 (readable lighting). |

## Precompute (Nikki P9)
- Body-hide / outfit compatibility: not applicable to terrain, but RoseWindow Veil records `pending_hide_mask = torso_valley_underlay` — generate in Houdini `HDA_CH_WardrobeIntersectionAudit` when body mesh present.
- Chladni LODs: POM/Toksvig/Bayer precomputed offline (`specs/lookdev/*`) — already done.
- Heightmap→Nanite bake: manifest hashed (`Saved/Audit/faraway_mother/fabric_ridge_terrain/manifest.json`) — deterministic.

## Streaming & screen importance (Nikki P6 + P10)
- Terrain Nanite + WP; placements are `StaticMeshActor` (ISM candidate for scatter phase). WPO scale 1.0→0.0 across LOD 0-3 matches screen importance (close = POM 32 + WPO 1.0; vista = Toksvig 1.0 + rim 1.8 + WPO 0).
- Budget: no Chaos on km mesh; Chaos only on 2 hero canopy pieces within 30 m of player.

## Wardrobe ability hook
Heart Gate veil (Tier B) is the Hemkeeper ontology test: "the world is fabric — tension/seam/fold interpretation." Equipping `mother_velvet_mantle` (reward `reward.wardrobe.mother_velvet_mantle`) toggles `WorldField.Tension` which drives both WPO amplitude on terrain and Chaos release on the Veil. Same field, two costs.

## Checklist for editor pass
- [ ] Tag actors with `ClothTier` string metadata (done in `faraway_mother_prototype_build.py:CLOTH_TIERS`)
- [ ] Heart Gate finial: set `ChaosPending=true` until Chaos Cloth asset bound
- [ ] RoseWindow: set `TranslucentSortPriority=10`, verify ≤2 overlapping translucent layers in capture
- [ ] Terrain: verify `M_Master_Nikki_Landscape` with `MF_FabricMountainWPO` — not a new master
