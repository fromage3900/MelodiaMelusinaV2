# Master-Material Graph — purpose, use, and parented instances

**Date:** 2026-09-12 · **Status:** living doc for the materials freeze
**Method:** on-disk census + binary parent-ref extraction + doc-evidence cross-check
(2026-09-10/11). Sizes/dates are disk truth; instance counts cite docs where noted.

## The graph

```text
M_Master_Toon_Universal (727KB) ── DEFAULT SPINE — everything not below
├── 1762 MIs: Env/props/trims/showcase; MPC_Hero_Material hero MIs
├── Melusina garments (gen-3): bow/frontpanel/gloves/shawl/skirt/sleeve,
│   IRISFRONT (V2), Dress_Shorewake, MI_Material_008
├── MI_Melusina_Hair (1 body-map binding; owner art call pending)
├── Brass 8 (rebuilt 09-11) · Starskiff Hull/Wake/Night + 6 Clothes MIs
├── Copernicus ~40 (cymatics driver samplers, by contract)
└── PBR_Auto pretty twins (96, landed)

M_Master_Toon_Universal_Alpha ── MASKED/CUTOUT ONLY (lace, foliage, decals)
M_Master_Toon_Universal_NikkiChainIntegratedV1 ── AUTHORITATIVE Nikki chain (8 MIs)
M_Master_Toon_Character (67KB) ── CHARACTER toon
├── INTENDED: MI_ChoralSheep_Body (+ Chladni_C child), MI_Melusina_SorrowSeam
└── ⚠️ ACTUAL: sheep Body still → M_Chorus_Wool_Master (reparent owed, Hermes lane)
M_Master_Nikki_Landscape (284KB) ── kawaii terrain (Glacier/NikkiDream/P2 terrain)
M_Master_Toon_Landscape_HeightBlend ── 4-layer terrain (Gaea/SeaAbove/Canonical)
M_Universal_Enhanced_Fabric ── PBR fabric: garments, P2 Gown/Mantle/Corset/
  Cradle/Ornament/Veil (reparented 09-11), remap target for Faraway phantom refs
M_Universal_Enhanced_{Crystal,Metal,Stone,Water} ── channel-tuned PBR, thin families
M_Water_Master_Grand_v10_Upgrade ── CANONICAL water (v6/v7/v9 superseded)
M_Cymatic_SingingDune ── sole M_Cymatic master; 24 sibling folders texture-only
M_SpeedTreeMaster ── plant authority (wind instances, kelp/cards)
M_AudioReactive_BaseMaster ── rhythm surfaces (reads nothing; 2 MIs + MI_Rhythm_*)
M_Glitter_{Enhanced_Master,UltimateSparkling,VolumetricInk,WorldAligned} ── glitter
M_Cosmo_Master (stub) · M_Chorus_Wool_Master (SUPERSEDED — ban as parent, keep file)

DEMOTE (do not instance): NikkiChain plain fork, Repair/RepairV2 diagnostics,
Toon_Unified (→Universal), Simple_Universal (light only), SDF_Toon SDF/ fork,
v10_Substrate (study), v6/v7/v9 waters, Melodia_Fabric_Master (never built).

PHANTOMS (referenced, zero bytes — remap, do not author unless owner signs):
├── M_Master_Nikki (character) — only in CompatibilityLabs backup; Gown ex-parent
├── M_Master_FarawayMother_Fabric — 4 LOD MIs + 12 sidecars + 44 spec rows
├── M_Master_Melusina_Costume — Shorewake Gown LOD specs
├── M_Master_Starskiff_Rigid — Hull LOD specs
└── M_Master_Toon_Cosmic / Impressionist / Melodia_Fabric — retired/research-only
```

## Per-master breakdown (freeze-relevant)

| Master | Purpose | Instance families (verified) | Freeze rule |
|---|---|---|---|
| Toon_Universal | Default surface spine | 1762 Env/showcase; all Melusina garments; brass 8; Starskiff; Copernicus ~40; PBR twins | Default; new MIs justify any other parent |
| …_Alpha | Cutout | Lace/foliage/decals/opacity sets | Masked use only |
| NikkiChainIntegratedV1 | Nikki look | 8 NikkiIntegrated MIs | Nikki look only |
| Toon_Character | Character toon | SorrowSeam; sheep Body PENDING reparent | Sheep reparent owed |
| Nikki_Landscape / HeightBlend | Terrain | Glacier/NikkiDream/P2 vs Gaea/SeaAbove/Canonical | Never cross |
| Enhanced_Fabric | PBR fabric | Garments; 6 P2 (09-11); Faraway remap target | Fabric + P2 |
| Water v10_Upgrade | Water | SeaAbove/Oceanology/Hero | Only water parent |
| SingingDune | Cymatic ground | Promotion queue (24 staged folders) | Staged, not blocking |
| SpeedTree / AudioReactive / Glitter / Cosmo | Specialist | Wind, rhythm, sparkle, staged-cosmic | As documented |

## Audio-reactivity overlay (orthogonal to parenting)

`AudioReactivePresentationSubsystem` → `MPC_Melodia_Palette` →
`CymaticsWriterSubsystem` → `MPC_Cymatics_Driver` → Copernicus/Faraway/KleinVeil
(read-only via `UMelodiaCymaticsSubsystem`). Brass binds the palette lane by
design. Melusina garments: health-done, cymatics P1. Sheep fleece: texture-staged,
`MI_ChoralSheep_Body_Chladni_C` pending (Hermes lane).

## Freeze gates (all must hold)

1. `verify_baseline` re-freeze against this graph (4 known drifts need owning lanes).
2. No new master without owner sign-off; no instance may parent to a phantom or
   a demoted master (CI-checkable via parent-ref census:
   `Tools/duplicate_assets_audit.py` + MI parent scan).
3. Sheep Body → Toon_Character reparent completes before freeze (Hermes lane).
4. Read-only sweep gate: no ReadOnly `.uasset` under `Content/` (crashed 2 lanes;
   audit `Saved/Audit/READONLY_SWEEP_2026-09-12.md`).
