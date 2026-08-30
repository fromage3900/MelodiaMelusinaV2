# Arch Toon Missing MI Spec — 2026-08-30

**Source:** `Saved/Audit/arch_toon_conversion.json` cross-referenced against disk.
**Scan tool:** `Tools/_arch_toon_missing_mi_scan.py`
**Scan output:** `Saved/Audit/_arch_toon_missing_mi.json`
**Parent material:** `Content/EnvSandbox/Materials/Masters/M_Master_Toon_Universal`
**Mode:** Spec only — no `.uasset` writes.

---

## Summary

| Metric | Cathedral | Atlantis | Total |
|---|---|---|---|
| Spec entries | 41 | 333 | 374 |
| Found anywhere on disk | 0 | 0 | 0 |
| **Truly missing** | **41** | **333** | **374** |

> The target directories `Content/EnvSandbox/Materials/Instances/Architecture/Cathedral/`
> and `.../Architecture/Atlantis/` do NOT exist. All MIs must be created via Editor
> Monolith MCP or `convert_arch_to_toon.py` script. None of the spec MIs were found
> anywhere on disk — they share no filenames with the 83 existing `Atlantis/` MIs.

---

## Cathedral — 41 Missing MIs

| mesh_path | mi_path | shadow_dream_preset | tint_color |
|---|---|---|---|
| Content/EnvSandbox/Meshes/Cathedral/SM_Cathedral_Altar.uasset | Content/EnvSandbox/Materials/Instances/Architecture/Cathedral/MI_Arch_Cath_SM_Cathedral_Altar | marble/glass | blue |
| Content/EnvSandbox/Meshes/Cathedral/SM_Cathedral_BeatMedallion.uasset | Content/EnvSandbox/Materials/Instances/Architecture/Cathedral/MI_Arch_Cath_SM_Cathedral_BeatMedallion | gold | — |
| Content/EnvSandbox/Meshes/Cathedral/SM_Cathedral_Bed.uasset | Content/EnvSandbox/Materials/Instances/Architecture/Cathedral/MI_Arch_Cath_SM_Cathedral_Bed | wood/worn | — |
| Content/EnvSandbox/Meshes/Cathedral/SM_Cathedral_BifrostBridge.uasset | Content/EnvSandbox/Materials/Instances/Architecture/Cathedral/MI_Arch_Cath_SM_Cathedral_BifrostBridge | default | — |
| Content/EnvSandbox/Meshes/Cathedral/SM_Cathedral_Buttress.uasset | Content/EnvSandbox/Materials/Instances/Architecture/Cathedral/MI_Arch_Cath_SM_Cathedral_Buttress | stone/brick/trim | — |
| Content/EnvSandbox/Meshes/Cathedral/SM_Cathedral_Chandelier.uasset | Content/EnvSandbox/Materials/Instances/Architecture/Cathedral/MI_Arch_Cath_SM_Cathedral_Chandelier | marble/glass | blue |
| Content/EnvSandbox/Meshes/Cathedral/SM_Cathedral_Chapel.uasset | Content/EnvSandbox/Materials/Instances/Architecture/Cathedral/MI_Arch_Cath_SM_Cathedral_Chapel | stone/brick/trim | — |
| Content/EnvSandbox/Meshes/Cathedral/SM_Cathedral_ChapterHouse.uasset | Content/EnvSandbox/Materials/Instances/Architecture/Cathedral/MI_Arch_Cath_SM_Cathedral_ChapterHouse | stone/brick/trim | — |
| Content/EnvSandbox/Meshes/Cathedral/SM_Cathedral_CombatFloor.uasset | Content/EnvSandbox/Materials/Instances/Architecture/Cathedral/MI_Arch_Cath_SM_Cathedral_CombatFloor | stone/brick/trim | — |
| Content/EnvSandbox/Meshes/Cathedral/SM_Cathedral_Crypt.uasset | Content/EnvSandbox/Materials/Instances/Architecture/Cathedral/MI_Arch_Cath_SM_Cathedral_Crypt | stone/brick/trim | — |
| Content/EnvSandbox/Meshes/Cathedral/SM_Cathedral_CryptVault.uasset | Content/EnvSandbox/Materials/Instances/Architecture/Cathedral/MI_Arch_Cath_SM_Cathedral_CryptVault | stone/brick/trim | — |
| Content/EnvSandbox/Meshes/Cathedral/SM_Cathedral_EscherBelvedere.uasset | Content/EnvSandbox/Materials/Instances/Architecture/Cathedral/MI_Arch_Cath_SM_Cathedral_EscherBelvedere | stone/brick/trim | — |
| Content/EnvSandbox/Meshes/Cathedral/SM_Cathedral_EscherBridge.uasset | Content/EnvSandbox/Materials/Instances/Architecture/Cathedral/MI_Arch_Cath_SM_Cathedral_EscherBridge | default | — |
| Content/EnvSandbox/Meshes/Cathedral/SM_Cathedral_EscherPenrose.uasset | Content/EnvSandbox/Materials/Instances/Architecture/Cathedral/MI_Arch_Cath_SM_Cathedral_EscherPenrose | marble/glass | blue |
| Content/EnvSandbox/Meshes/Cathedral/SM_Cathedral_EscherWaterfall.uasset | Content/EnvSandbox/Materials/Instances/Architecture/Cathedral/MI_Arch_Cath_SM_Cathedral_EscherWaterfall | stone/brick/trim | — |
| Content/EnvSandbox/Meshes/Cathedral/SM_Cathedral_Garland.uasset | Content/EnvSandbox/Materials/Instances/Architecture/Cathedral/MI_Arch_Cath_SM_Cathedral_Garland | rose | pink |
| Content/EnvSandbox/Meshes/Cathedral/SM_Cathedral_HarmonicOrb.uasset | Content/EnvSandbox/Materials/Instances/Architecture/Cathedral/MI_Arch_Cath_SM_Cathedral_HarmonicOrb | marble/glass | blue |
| Content/EnvSandbox/Meshes/Cathedral/SM_Cathedral_LancetWindow.uasset | Content/EnvSandbox/Materials/Instances/Architecture/Cathedral/MI_Arch_Cath_SM_Cathedral_LancetWindow | marble/glass | blue |
| Content/EnvSandbox/Meshes/Cathedral/SM_Cathedral_MusicOrb.uasset | Content/EnvSandbox/Materials/Instances/Architecture/Cathedral/MI_Arch_Cath_SM_Cathedral_MusicOrb | marble/glass | blue |
| Content/EnvSandbox/Meshes/Cathedral/SM_Cathedral_Observatory.uasset | Content/EnvSandbox/Materials/Instances/Architecture/Cathedral/MI_Arch_Cath_SM_Cathedral_Observatory | marble/glass | blue |
| Content/EnvSandbox/Meshes/Cathedral/SM_Cathedral_Pavilion.uasset | Content/EnvSandbox/Materials/Instances/Architecture/Cathedral/MI_Arch_Cath_SM_Cathedral_Pavilion | stone/brick/trim | — |
| Content/EnvSandbox/Meshes/Cathedral/SM_Cathedral_Perch.uasset | Content/EnvSandbox/Materials/Instances/Architecture/Cathedral/MI_Arch_Cath_SM_Cathedral_Perch | wood/worn | — |
| Content/EnvSandbox/Meshes/Cathedral/SM_Cathedral_Pier.uasset | Content/EnvSandbox/Materials/Instances/Architecture/Cathedral/MI_Arch_Cath_SM_Cathedral_Pier | stone/brick/trim | — |
| Content/EnvSandbox/Meshes/Cathedral/SM_Cathedral_Portal.uasset | Content/EnvSandbox/Materials/Instances/Architecture/Cathedral/MI_Arch_Cath_SM_Cathedral_Portal | gold | — |
| Content/EnvSandbox/Meshes/Cathedral/SM_Cathedral_ResonantDoor.uasset | Content/EnvSandbox/Materials/Instances/Architecture/Cathedral/MI_Arch_Cath_SM_Cathedral_ResonantDoor | wood/worn | — |
| Content/EnvSandbox/Meshes/Cathedral/SM_Cathedral_RoseWindow.uasset | Content/EnvSandbox/Materials/Instances/Architecture/Cathedral/MI_Arch_Cath_SM_Cathedral_RoseWindow | marble/glass | blue |
| Content/EnvSandbox/Meshes/Cathedral/SM_Cathedral_RosetteMedallion.uasset | Content/EnvSandbox/Materials/Instances/Architecture/Cathedral/MI_Arch_Cath_SM_Cathedral_RosetteMedallion | marble/glass | blue |
| Content/EnvSandbox/Meshes/Cathedral/SM_Cathedral_SaintStatue.uasset | Content/EnvSandbox/Materials/Instances/Architecture/Cathedral/MI_Arch_Cath_SM_Cathedral_SaintStatue | marble/glass | blue |
| Content/EnvSandbox/Meshes/Cathedral/SM_Cathedral_SpiralStairs.uasset | Content/EnvSandbox/Materials/Instances/Architecture/Cathedral/MI_Arch_Cath_SM_Cathedral_SpiralStairs | stone/brick/trim | — |
| Content/EnvSandbox/Meshes/Cathedral/SM_Cathedral_Spire.uasset | Content/EnvSandbox/Materials/Instances/Architecture/Cathedral/MI_Arch_Cath_SM_Cathedral_Spire | stone/brick/trim | — |
| Content/EnvSandbox/Meshes/Cathedral/SM_Cathedral_StaffBalustrade.uasset | Content/EnvSandbox/Materials/Instances/Architecture/Cathedral/MI_Arch_Cath_SM_Cathedral_StaffBalustrade | default | — |
| Content/EnvSandbox/Meshes/Cathedral/SM_Cathedral_StainedGlassPanel.uasset | Content/EnvSandbox/Materials/Instances/Architecture/Cathedral/MI_Arch_Cath_SM_Cathedral_StainedGlassPanel | marble/glass | blue |
| Content/EnvSandbox/Meshes/Cathedral/SM_Cathedral_StainedRose.uasset | Content/EnvSandbox/Materials/Instances/Architecture/Cathedral/MI_Arch_Cath_SM_Cathedral_StainedRose | marble/glass | blue |
| Content/EnvSandbox/Meshes/Cathedral/SM_Cathedral_Stall.uasset | Content/EnvSandbox/Materials/Instances/Architecture/Cathedral/MI_Arch_Cath_SM_Cathedral_Stall | wood/worn | — |
| Content/EnvSandbox/Meshes/Cathedral/SM_Cathedral_Tower.uasset | Content/EnvSandbox/Materials/Instances/Architecture/Cathedral/MI_Arch_Cath_SM_Cathedral_Tower | stone/brick/trim | — |
| Content/EnvSandbox/Meshes/Cathedral/SM_Cathedral_TraceryPanel.uasset | Content/EnvSandbox/Materials/Instances/Architecture/Cathedral/MI_Arch_Cath_SM_Cathedral_TraceryPanel | marble/glass | blue |
| Content/EnvSandbox/Meshes/Cathedral/SM_Cathedral_TrebleRelief.uasset | Content/EnvSandbox/Materials/Instances/Architecture/Cathedral/MI_Arch_Cath_SM_Cathedral_TrebleRelief | stone/brick/trim | — |
| Content/EnvSandbox/Meshes/Cathedral/SM_Cathedral_Urn.uasset | Content/EnvSandbox/Materials/Instances/Architecture/Cathedral/MI_Arch_Cath_SM_Cathedral_Urn | marble/glass | blue |
| Content/EnvSandbox/Meshes/Cathedral/SM_Cathedral_VaultBay.uasset | Content/EnvSandbox/Materials/Instances/Architecture/Cathedral/MI_Arch_Cath_SM_Cathedral_VaultBay | stone/brick/trim | — |
| Content/EnvSandbox/Meshes/Cathedral/SM_Cathedral_Wall.uasset | Content/EnvSandbox/Materials/Instances/Architecture/Cathedral/MI_Arch_Cath_SM_Cathedral_Wall | stone/brick/trim | — |
| Content/EnvSandbox/Meshes/Cathedral/SM_Cathedral_WallParapet.uasset | Content/EnvSandbox/Materials/Instances/Architecture/Cathedral/MI_Arch_Cath_SM_Cathedral_WallParapet | stone/brick/trim | — |

---

## Atlantis — 333 Missing MIs

| mesh_path | mi_path | shadow_dream_preset | tint_color |
|---|---|---|---|
| Content/EnvSandbox/Meshes/Atlantis/SM_Atlantis_ArchA.uasset | Content/EnvSandbox/Materials/Instances/Architecture/Atlantis/MI_Arch_Atl_ArchA | stone/brick/trim | — |
| Content/EnvSandbox/Meshes/Atlantis/SM_Atlantis_ArchB.uasset | Content/EnvSandbox/Materials/Instances/Architecture/Atlantis/MI_Arch_Atl_ArchB | stone/brick/trim | — |
| Content/EnvSandbox/Meshes/Atlantis/SM_Atlantis_ArchC.uasset | Content/EnvSandbox/Materials/Instances/Architecture/Atlantis/MI_Arch_Atl_ArchC | stone/brick/trim | — |
| Content/EnvSandbox/Meshes/Atlantis/SM_Atlantis_ArchD.uasset | Content/EnvSandbox/Materials/Instances/Architecture/Atlantis/MI_Arch_Atl_ArchD | stone/brick/trim | — |
| Content/EnvSandbox/Meshes/Atlantis/SM_Atlantis_ArchE.uasset | Content/EnvSandbox/Materials/Instances/Architecture/Atlantis/MI_Arch_Atl_ArchE | stone/brick/trim | — |
| Content/EnvSandbox/Meshes/Atlantis/SM_Atlantis_ArchF.uasset | Content/EnvSandbox/Materials/Instances/Architecture/Atlantis/MI_Arch_Atl_ArchF | stone/brick/trim | — |
| Content/EnvSandbox/Meshes/Atlantis/SM_Atlantis_ArchG.uasset | Content/EnvSandbox/Materials/Instances/Architecture/Atlantis/MI_Arch_Atl_ArchG | stone/brick/trim | — |
| Content/EnvSandbox/Meshes/Atlantis/SM_Atlantis_ArchH.uasset | Content/EnvSandbox/Materials/Instances/Architecture/Atlantis/MI_Arch_Atl_ArchH | stone/brick/trim | — |
| Content/EnvSandbox/Meshes/Atlantis/SM_Atlantis_ArchI.uasset | Content/EnvSandbox/Materials/Instances/Architecture/Atlantis/MI_Arch_Atl_ArchI | stone/brick/trim | — |
| Content/EnvSandbox/Meshes/Atlantis/SM_Atlantis_ArchesA.uasset | Content/EnvSandbox/Materials/Instances/Architecture/Atlantis/MI_Arch_Atl_ArchesA | stone/brick/trim | — |
| Content/EnvSandbox/Meshes/Atlantis/SM_Atlantis_ArchesB.uasset | Content/EnvSandbox/Materials/Instances/Architecture/Atlantis/MI_Arch_Atl_ArchesB | stone/brick/trim | — |
| Content/EnvSandbox/Meshes/Atlantis/SM_Atlantis_BannerA.uasset | Content/EnvSandbox/Materials/Instances/Architecture/Atlantis/MI_Arch_Atl_BannerA | default | — |
| Content/EnvSandbox/Meshes/Atlantis/SM_Atlantis_BannerB.uasset | Content/EnvSandbox/Materials/Instances/Architecture/Atlantis/MI_Arch_Atl_BannerB | default | — |
| Content/EnvSandbox/Meshes/Atlantis/SM_Atlantis_BannerC.uasset | Content/EnvSandbox/Materials/Instances/Architecture/Atlantis/MI_Arch_Atl_BannerC | default | — |
| Content/EnvSandbox/Meshes/Atlantis/SM_Atlantis_BannerD.uasset | Content/EnvSandbox/Materials/Instances/Architecture/Atlantis/MI_Arch_Atl_BannerD | default | — |
| Content/EnvSandbox/Meshes/Atlantis/SM_Atlantis_Barrel.uasset | Content/EnvSandbox/Materials/Instances/Architecture/Atlantis/MI_Arch_Atl_Barrel | wood/worn | — |
| Content/EnvSandbox/Meshes/Atlantis/SM_Atlantis_BarrelRackA.uasset | Content/EnvSandbox/Materials/Instances/Architecture/Atlantis/MI_Arch_Atl_BarrelRackA | wood/worn | — |
| Content/EnvSandbox/Meshes/Atlantis/SM_Atlantis_BarrelRackB.uasset | Content/EnvSandbox/Materials/Instances/Architecture/Atlantis/MI_Arch_Atl_BarrelRackB | wood/worn | — |
| Content/EnvSandbox/Meshes/Atlantis/SM_Atlantis_BarrelRackC.uasset | Content/EnvSandbox/Materials/Instances/Architecture/Atlantis/MI_Arch_Atl_BarrelRackC | wood/worn | — |
| Content/EnvSandbox/Meshes/Atlantis/SM_Atlantis_BarrelRackD.uasset | Content/EnvSandbox/Materials/Instances/Architecture/Atlantis/MI_Arch_Atl_BarrelRackD | wood/worn | — |
| Content/EnvSandbox/Meshes/Atlantis/SM_Atlantis_BarrelsA.uasset | Content/EnvSandbox/Materials/Instances/Architecture/Atlantis/MI_Arch_Atl_BarrelsA | wood/worn | — |
| Content/EnvSandbox/Meshes/Atlantis/SM_Atlantis_BarrelsB.uasset | Content/EnvSandbox/Materials/Instances/Architecture/Atlantis/MI_Arch_Atl_BarrelsB | wood/worn | — |
| Content/EnvSandbox/Meshes/Atlantis/SM_Atlantis_BarrelsC.uasset | Content/EnvSandbox/Materials/Instances/Architecture/Atlantis/MI_Arch_Atl_BarrelsC | wood/worn | — |
| Content/EnvSandbox/Meshes/Atlantis/SM_Atlantis_BarrelsD.uasset | Content/EnvSandbox/Materials/Instances/Architecture/Atlantis/MI_Arch_Atl_BarrelsD | wood/worn | — |
| Content/EnvSandbox/Meshes/Atlantis/SM_Atlantis_BaseA.uasset | Content/EnvSandbox/Materials/Instances/Architecture/Atlantis/MI_Arch_Atl_BaseA | stone/brick/trim | — |
| Content/EnvSandbox/Meshes/Atlantis/SM_Atlantis_BaseB.uasset | Content/EnvSandbox/Materials/Instances/Architecture/Atlantis/MI_Arch_Atl_BaseB | stone/brick/trim | — |
| Content/EnvSandbox/Meshes/Atlantis/SM_Atlantis_BaseC.uasset | Content/EnvSandbox/Materials/Instances/Architecture/Atlantis/MI_Arch_Atl_BaseC | stone/brick/trim | — |
| Content/EnvSandbox/Meshes/Atlantis/SM_Atlantis_BaseColumnsA.uasset | Content/EnvSandbox/Materials/Instances/Architecture/Atlantis/MI_Arch_Atl_BaseColumnsA | stone/brick/trim | — |
| Content/EnvSandbox/Meshes/Atlantis/SM_Atlantis_BaseColumnsB.uasset | Content/EnvSandbox/Materials/Instances/Architecture/Atlantis/MI_Arch_Atl_BaseColumnsB | stone/brick/trim | — |
| Content/EnvSandbox/Meshes/Atlantis/SM_Atlantis_BaseColumnsC.uasset | Content/EnvSandbox/Materials/Instances/Architecture/Atlantis/MI_Arch_Atl_BaseColumnsC | stone/brick/trim | — |
| Content/EnvSandbox/Meshes/Atlantis/SM_Atlantis_BaseD.uasset | Content/EnvSandbox/Materials/Instances/Architecture/Atlantis/MI_Arch_Atl_BaseD | stone/brick/trim | — |
| Content/EnvSandbox/Meshes/Atlantis/SM_Atlantis_BaseE.uasset | Content/EnvSandbox/Materials/Instances/Architecture/Atlantis/MI_Arch_Atl_BaseE | stone/brick/trim | — |
| Content/EnvSandbox/Meshes/Atlantis/SM_Atlantis_BaseF.uasset | Content/EnvSandbox/Materials/Instances/Architecture/Atlantis/MI_Arch_Atl_BaseF | stone/brick/trim | — |
| Content/EnvSandbox/Meshes/Atlantis/SM_Atlantis_BaseG.uasset | Content/EnvSandbox/Materials/Instances/Architecture/Atlantis/MI_Arch_Atl_BaseG | stone/brick/trim | — |
| Content/EnvSandbox/Meshes/Atlantis/SM_Atlantis_BasketA.uasset | Content/EnvSandbox/Materials/Instances/Architecture/Atlantis/MI_Arch_Atl_BasketA | wood/worn | — |
| Content/EnvSandbox/Meshes/Atlantis/SM_Atlantis_BasketB.uasset | Content/EnvSandbox/Materials/Instances/Architecture/Atlantis/MI_Arch_Atl_BasketB | wood/worn | — |
| Content/EnvSandbox/Meshes/Atlantis/SM_Atlantis_BenchA.uasset | Content/EnvSandbox/Materials/Instances/Architecture/Atlantis/MI_Arch_Atl_BenchA | wood/worn | — |
| Content/EnvSandbox/Meshes/Atlantis/SM_Atlantis_BenchB.uasset | Content/EnvSandbox/Materials/Instances/Architecture/Atlantis/MI_Arch_Atl_BenchB | wood/worn | — |
| Content/EnvSandbox/Meshes/Atlantis/SM_Atlantis_BenchC.uasset | Content/EnvSandbox/Materials/Instances/Architecture/Atlantis/MI_Arch_Atl_BenchC | wood/worn | — |
| Content/EnvSandbox/Meshes/Atlantis/SM_Atlantis_BenchD.uasset | Content/EnvSandbox/Materials/Instances/Architecture/Atlantis/MI_Arch_Atl_BenchD | wood/worn | — |
| Content/EnvSandbox/Meshes/Atlantis/SM_Atlantis_BenchE.uasset | Content/EnvSandbox/Materials/Instances/Architecture/Atlantis/MI_Arch_Atl_BenchE | wood/worn | — |
| Content/EnvSandbox/Meshes/Atlantis/SM_Atlantis_BenchF.uasset | Content/EnvSandbox/Materials/Instances/Architecture/Atlantis/MI_Arch_Atl_BenchF | wood/worn | — |
| Content/EnvSandbox/Meshes/Atlantis/SM_Atlantis_BenchG.uasset | Content/EnvSandbox/Materials/Instances/Architecture/Atlantis/MI_Arch_Atl_BenchG | wood/worn | — |
| Content/EnvSandbox/Meshes/Atlantis/SM_Atlantis_BenchH.uasset | Content/EnvSandbox/Materials/Instances/Architecture/Atlantis/MI_Arch_Atl_BenchH | wood/worn | — |
| Content/EnvSandbox/Meshes/Atlantis/SM_Atlantis_BenchI.uasset | Content/EnvSandbox/Materials/Instances/Architecture/Atlantis/MI_Arch_Atl_BenchI | wood/worn | — |
| Content/EnvSandbox/Meshes/Atlantis/SM_Atlantis_BenchJ.uasset | Content/EnvSandbox/Materials/Instances/Architecture/Atlantis/MI_Arch_Atl_BenchJ | wood/worn | — |
| Content/EnvSandbox/Meshes/Atlantis/SM_Atlantis_BenchK.uasset | Content/EnvSandbox/Materials/Instances/Architecture/Atlantis/MI_Arch_Atl_BenchK | wood/worn | — |
| Content/EnvSandbox/Meshes/Atlantis/SM_Atlantis_BenchL.uasset | Content/EnvSandbox/Materials/Instances/Architecture/Atlantis/MI_Arch_Atl_BenchL | wood/worn | — |
| Content/EnvSandbox/Meshes/Atlantis/SM_Atlantis_BenchM.uasset | Content/EnvSandbox/Materials/Instances/Architecture/Atlantis/MI_Arch_Atl_BenchM | wood/worn | — |
| Content/EnvSandbox/Meshes/Atlantis/SM_Atlantis_BenchN.uasset | Content/EnvSandbox/Materials/Instances/Architecture/Atlantis/MI_Arch_Atl_BenchN | wood/worn | — |
| Content/EnvSandbox/Meshes/Atlantis/SM_Atlantis_BenchO.uasset | Content/EnvSandbox/Materials/Instances/Architecture/Atlantis/MI_Arch_Atl_BenchO | wood/worn | — |
| Content/EnvSandbox/Meshes/Atlantis/SM_Atlantis_BenchP.uasset | Content/EnvSandbox/Materials/Instances/Architecture/Atlantis/MI_Arch_Atl_BenchP | wood/worn | — |
| Content/EnvSandbox/Meshes/Atlantis/SM_Atlantis_BenchQ.uasset | Content/EnvSandbox/Materials/Instances/Architecture/Atlantis/MI_Arch_Atl_BenchQ | wood/worn | — |
| Content/EnvSandbox/Meshes/Atlantis/SM_Atlantis_BenchR.uasset | Content/EnvSandbox/Materials/Instances/Architecture/Atlantis/MI_Arch_Atl_BenchR | wood/worn | — |
| Content/EnvSandbox/Meshes/Atlantis/SM_Atlantis_BenchS.uasset | Content/EnvSandbox/Materials/Instances/Architecture/Atlantis/MI_Arch_Atl_BenchS | wood/worn | — |
| Content/EnvSandbox/Meshes/Atlantis/SM_Atlantis_BenchesA.uasset | Content/EnvSandbox/Materials/Instances/Architecture/Atlantis/MI_Arch_Atl_BenchesA | wood/worn | — |
| Content/EnvSandbox/Meshes/Atlantis/SM_Atlantis_BenchesB.uasset | Content/EnvSandbox/Materials/Instances/Architecture/Atlantis/MI_Arch_Atl_BenchesB | wood/worn | — |
| Content/EnvSandbox/Meshes/Atlantis/SM_Atlantis_BenchesC.uasset | Content/EnvSandbox/Materials/Instances/Architecture/Atlantis/MI_Arch_Atl_BenchesC | wood/worn | — |
| Content/EnvSandbox/Meshes/Atlantis/SM_Atlantis_BenchesD.uasset | Content/EnvSandbox/Materials/Instances/Architecture/Atlantis/MI_Arch_Atl_BenchesD | wood/worn | — |
| Content/EnvSandbox/Meshes/Atlantis/SM_Atlantis_BenchesE.uasset | Content/EnvSandbox/Materials/Instances/Architecture/Atlantis/MI_Arch_Atl_BenchesE | wood/worn | — |
| Content/EnvSandbox/Meshes/Atlantis/SM_Atlantis_BenchesF.uasset | Content/EnvSandbox/Materials/Instances/Architecture/Atlantis/MI_Arch_Atl_BenchesF | wood/worn | — |
| Content/EnvSandbox/Meshes/Atlantis/SM_Atlantis_BenchesG.uasset | Content/EnvSandbox/Materials/Instances/Architecture/Atlantis/MI_Arch_Atl_BenchesG | wood/worn | — |
| Content/EnvSandbox/Meshes/Atlantis/SM_Atlantis_BenchesH.uasset | Content/EnvSandbox/Materials/Instances/Architecture/Atlantis/MI_Arch_Atl_BenchesH | wood/worn | — |
| Content/EnvSandbox/Meshes/Atlantis/SM_Atlantis_BuildingA.uasset | Content/EnvSandbox/Materials/Instances/Architecture/Atlantis/MI_Arch_Atl_BuildingA | stone/brick/trim | — |
| Content/EnvSandbox/Meshes/Atlantis/SM_Atlantis_BuildingB.uasset | Content/EnvSandbox/Materials/Instances/Architecture/Atlantis/MI_Arch_Atl_BuildingB | stone/brick/trim | — |
| Content/EnvSandbox/Meshes/Atlantis/SM_Atlantis_BuildingC.uasset | Content/EnvSandbox/Materials/Instances/Architecture/Atlantis/MI_Arch_Atl_BuildingC | stone/brick/trim | — |
| Content/EnvSandbox/Meshes/Atlantis/SM_Atlantis_BuildingD.uasset | Content/EnvSandbox/Materials/Instances/Architecture/Atlantis/MI_Arch_Atl_BuildingD | stone/brick/trim | — |
| Content/EnvSandbox/Meshes/Atlantis/SM_Atlantis_BuildingE.uasset | Content/EnvSandbox/Materials/Instances/Architecture/Atlantis/MI_Arch_Atl_BuildingE | stone/brick/trim | — |
| Content/EnvSandbox/Meshes/Atlantis/SM_Atlantis_BuildingF.uasset | Content/EnvSandbox/Materials/Instances/Architecture/Atlantis/MI_Arch_Atl_BuildingF | stone/brick/trim | — |
| Content/EnvSandbox/Meshes/Atlantis/SM_Atlantis_BuildingG.uasset | Content/EnvSandbox/Materials/Instances/Architecture/Atlantis/MI_Arch_Atl_BuildingG | stone/brick/trim | — |
| Content/EnvSandbox/Meshes/Atlantis/SM_Atlantis_BuildingH.uasset | Content/EnvSandbox/Materials/Instances/Architecture/Atlantis/MI_Arch_Atl_BuildingH | stone/brick/trim | — |
| Content/EnvSandbox/Meshes/Atlantis/SM_Atlantis_BuildingI.uasset | Content/EnvSandbox/Materials/Instances/Architecture/Atlantis/MI_Arch_Atl_BuildingI | stone/brick/trim | — |
| Content/EnvSandbox/Meshes/Atlantis/SM_Atlantis_BuildingJ.uasset | Content/EnvSandbox/Materials/Instances/Architecture/Atlantis/MI_Arch_Atl_BuildingJ | stone/brick/trim | — |
| Content/EnvSandbox/Meshes/Atlantis/SM_Atlantis_BuildingK.uasset | Content/EnvSandbox/Materials/Instances/Architecture/Atlantis/MI_Arch_Atl_BuildingK | stone/brick/trim | — |
| Content/EnvSandbox/Meshes/Atlantis/SM_Atlantis_BuildingL.uasset | Content/EnvSandbox/Materials/Instances/Architecture/Atlantis/MI_Arch_Atl_BuildingL | stone/brick/trim | — |
| Content/EnvSandbox/Meshes/Atlantis/SM_Atlantis_BuildingM.uasset | Content/EnvSandbox/Materials/Instances/Architecture/Atlantis/MI_Arch_Atl_BuildingM | stone/brick/trim | — |
| Content/EnvSandbox/Meshes/Atlantis/SM_Atlantis_BuildingN.uasset | Content/EnvSandbox/Materials/Instances/Architecture/Atlantis/MI_Arch_Atl_BuildingN | stone/brick/trim | — |
| Content/EnvSandbox/Meshes/Atlantis/SM_Atlantis_BuildingO.uasset | Content/EnvSandbox/Materials/Instances/Architecture/Atlantis/MI_Arch_Atl_BuildingO | stone/brick/trim | — |
| Content/EnvSandbox/Meshes/Atlantis/SM_Atlantis_BuildingP.uasset | Content/EnvSandbox/Materials/Instances/Architecture/Atlantis/MI_Arch_Atl_BuildingP | stone/brick/trim | — |
| Content/EnvSandbox/Meshes/Atlantis/SM_Atlantis_ChairA.uasset | Content/EnvSandbox/Materials/Instances/Architecture/Atlantis/MI_Arch_Atl_ChairA | wood/worn | — |
| Content/EnvSandbox/Meshes/Atlantis/SM_Atlantis_ChairB.uasset | Content/EnvSandbox/Materials/Instances/Architecture/Atlantis/MI_Arch_Atl_ChairB | wood/worn | — |
| Content/EnvSandbox/Meshes/Atlantis/SM_Atlantis_ChairC.uasset | Content/EnvSandbox/Materials/Instances/Architecture/Atlantis/MI_Arch_Atl_ChairC | wood/worn | — |
| Content/EnvSandbox/Meshes/Atlantis/SM_Atlantis_ColumnadeA.uasset | Content/EnvSandbox/Materials/Instances/Architecture/Atlantis/MI_Arch_Atl_ColumnadeA | stone/brick/trim | — |
| Content/EnvSandbox/Meshes/Atlantis/SM_Atlantis_ColumnadeB.uasset | Content/EnvSandbox/Materials/Instances/Architecture/Atlantis/MI_Arch_Atl_ColumnadeB | stone/brick/trim | — |
| Content/EnvSandbox/Meshes/Atlantis/SM_Atlantis_ColumnsA.uasset | Content/EnvSandbox/Materials/Instances/Architecture/Atlantis/MI_Arch_Atl_ColumnsA | stone/brick/trim | — |
| Content/EnvSandbox/Meshes/Atlantis/SM_Atlantis_ColumnsB.uasset | Content/EnvSandbox/Materials/Instances/Architecture/Atlantis/MI_Arch_Atl_ColumnsB | stone/brick/trim | — |
| Content/EnvSandbox/Meshes/Atlantis/SM_Atlantis_ColumnsC.uasset | Content/EnvSandbox/Materials/Instances/Architecture/Atlantis/MI_Arch_Atl_ColumnsC | stone/brick/trim | — |
| Content/EnvSandbox/Meshes/Atlantis/SM_Atlantis_ColumnsD.uasset | Content/EnvSandbox/Materials/Instances/Architecture/Atlantis/MI_Arch_Atl_ColumnsD | stone/brick/trim | — |
| Content/EnvSandbox/Meshes/Atlantis/SM_Atlantis_ColumnsE.uasset | Content/EnvSandbox/Materials/Instances/Architecture/Atlantis/MI_Arch_Atl_ColumnsE | stone/brick/trim | — |
| Content/EnvSandbox/Meshes/Atlantis/SM_Atlantis_ColumnsF.uasset | Content/EnvSandbox/Materials/Instances/Architecture/Atlantis/MI_Arch_Atl_ColumnsF | stone/brick/trim | — |
| Content/EnvSandbox/Meshes/Atlantis/SM_Atlantis_ColumnsG.uasset | Content/EnvSandbox/Materials/Instances/Architecture/Atlantis/MI_Arch_Atl_ColumnsG | stone/brick/trim | — |
| Content/EnvSandbox/Meshes/Atlantis/SM_Atlantis_ColumnsH.uasset | Content/EnvSandbox/Materials/Instances/Architecture/Atlantis/MI_Arch_Atl_ColumnsH | stone/brick/trim | — |
| Content/EnvSandbox/Meshes/Atlantis/SM_Atlantis_ColumnsI.uasset | Content/EnvSandbox/Materials/Instances/Architecture/Atlantis/MI_Arch_Atl_ColumnsI | stone/brick/trim | — |
| Content/EnvSandbox/Meshes/Atlantis/SM_Atlantis_ColumnsJ.uasset | Content/EnvSandbox/Materials/Instances/Architecture/Atlantis/MI_Arch_Atl_ColumnsJ | stone/brick/trim | — |
| Content/EnvSandbox/Meshes/Atlantis/SM_Atlantis_ColumnsK.uasset | Content/EnvSandbox/Materials/Instances/Architecture/Atlantis/MI_Arch_Atl_ColumnsK | stone/brick/trim | — |
| Content/EnvSandbox/Meshes/Atlantis/SM_Atlantis_ColumnsL.uasset | Content/EnvSandbox/Materials/Instances/Architecture/Atlantis/MI_Arch_Atl_ColumnsL | stone/brick/trim | — |
| Content/EnvSandbox/Meshes/Atlantis/SM_Atlantis_ColumnsM.uasset | Content/EnvSandbox/Materials/Instances/Architecture/Atlantis/MI_Arch_Atl_ColumnsM | stone/brick/trim | — |
| Content/EnvSandbox/Meshes/Atlantis/SM_Atlantis_ColumnsN.uasset | Content/EnvSandbox/Materials/Instances/Architecture/Atlantis/MI_Arch_Atl_ColumnsN | stone/brick/trim | — |
| Content/EnvSandbox/Meshes/Atlantis/SM_Atlantis_ColumnsO.uasset | Content/EnvSandbox/Materials/Instances/Architecture/Atlantis/MI_Arch_Atl_ColumnsO | stone/brick/trim | — |
| Content/EnvSandbox/Meshes/Atlantis/SM_Atlantis_ColumnsP.uasset | Content/EnvSandbox/Materials/Instances/Architecture/Atlantis/MI_Arch_Atl_ColumnsP | stone/brick/trim | — |
| Content/EnvSandbox/Meshes/Atlantis/SM_Atlantis_ColumnsQ.uasset | Content/EnvSandbox/Materials/Instances/Architecture/Atlantis/MI_Arch_Atl_ColumnsQ | stone/brick/trim | — |
| Content/EnvSandbox/Meshes/Atlantis/SM_Atlantis_ColumnsR.uasset | Content/EnvSandbox/Materials/Instances/Architecture/Atlantis/MI_Arch_Atl_ColumnsR | stone/brick/trim | — |
| Content/EnvSandbox/Meshes/Atlantis/SM_Atlantis_ColumnsS.uasset | Content/EnvSandbox/Materials/Instances/Architecture/Atlantis/MI_Arch_Atl_ColumnsS | stone/brick/trim | — |
| Content/EnvSandbox/Meshes/Atlantis/SM_Atlantis_ColumnsT.uasset | Content/EnvSandbox/Materials/Instances/Architecture/Atlantis/MI_Arch_Atl_ColumnsT | stone/brick/trim | — |
| Content/EnvSandbox/Meshes/Atlantis/SM_Atlantis_ColumnsU.uasset | Content/EnvSandbox/Materials/Instances/Architecture/Atlantis/MI_Arch_Atl_ColumnsU | stone/brick/trim | — |
| Content/EnvSandbox/Meshes/Atlantis/SM_Atlantis_ColumnsV.uasset | Content/EnvSandbox/Materials/Instances/Architecture/Atlantis/MI_Arch_Atl_ColumnsV | stone/brick/trim | — |
| Content/EnvSandbox/Meshes/Atlantis/SM_Atlantis_ColumnsW.uasset | Content/EnvSandbox/Materials/Instances/Architecture/Atlantis/MI_Arch_Atl_ColumnsW | stone/brick/trim | — |
| Content/EnvSandbox/Meshes/Atlantis/SM_Atlantis_ColumnsX.uasset | Content/EnvSandbox/Materials/Instances/Architecture/Atlantis/MI_Arch_Atl_ColumnsX | stone/brick/trim | — |
| Content/EnvSandbox/Meshes/Atlantis/SM_Atlantis_Cornice.uasset | Content/EnvSandbox/Materials/Instances/Architecture/Atlantis/MI_Arch_Atl_Cornice | stone/brick/trim | — |
| Content/EnvSandbox/Meshes/Atlantis/SM_Atlantis_DecorativeVaseA.uasset | Content/EnvSandbox/Materials/Instances/Architecture/Atlantis/MI_Arch_Atl_DecorativeVaseA | stone/brick/trim | — |
| Content/EnvSandbox/Meshes/Atlantis/SM_Atlantis_DecorativeVaseB.uasset | Content/EnvSandbox/Materials/Instances/Architecture/Atlantis/MI_Arch_Atl_DecorativeVaseB | stone/brick/trim | — |
| Content/EnvSandbox/Meshes/Atlantis/SM_Atlantis_DecorativeVaseC.uasset | Content/EnvSandbox/Materials/Instances/Architecture/Atlantis/MI_Arch_Atl_DecorativeVaseC | stone/brick/trim | — |
| Content/EnvSandbox/Meshes/Atlantis/SM_Atlantis_DecorativeVaseD.uasset | Content/EnvSandbox/Materials/Instances/Architecture/Atlantis/MI_Arch_Atl_DecorativeVaseD | stone/brick/trim | — |
| Content/EnvSandbox/Meshes/Atlantis/SM_Atlantis_DomeA.uasset | Content/EnvSandbox/Materials/Instances/Architecture/Atlantis/MI_Arch_Atl_DomeA | marble/glass | blue |
| Content/EnvSandbox/Meshes/Atlantis/SM_Atlantis_DomeB.uasset | Content/EnvSandbox/Materials/Instances/Architecture/Atlantis/MI_Arch_Atl_DomeB | marble/glass | blue |
| Content/EnvSandbox/Meshes/Atlantis/SM_Atlantis_DomeC.uasset | Content/EnvSandbox/Materials/Instances/Architecture/Atlantis/MI_Arch_Atl_DomeC | marble/glass | blue |
| Content/EnvSandbox/Meshes/Atlantis/SM_Atlantis_Door.uasset | Content/EnvSandbox/Materials/Instances/Architecture/Atlantis/MI_Arch_Atl_Door | wood/worn | — |
| Content/EnvSandbox/Meshes/Atlantis/SM_Atlantis_DoorLeftA.uasset | Content/EnvSandbox/Materials/Instances/Architecture/Atlantis/MI_Arch_Atl_DoorLeftA | wood/worn | — |
| Content/EnvSandbox/Meshes/Atlantis/SM_Atlantis_DoorLeftB.uasset | Content/EnvSandbox/Materials/Instances/Architecture/Atlantis/MI_Arch_Atl_DoorLeftB | wood/worn | — |
| Content/EnvSandbox/Meshes/Atlantis/SM_Atlantis_DoorLeftC.uasset | Content/EnvSandbox/Materials/Instances/Architecture/Atlantis/MI_Arch_Atl_DoorLeftC | wood/worn | — |
| Content/EnvSandbox/Meshes/Atlantis/SM_Atlantis_DoorLeftD.uasset | Content/EnvSandbox/Materials/Instances/Architecture/Atlantis/MI_Arch_Atl_DoorLeftD | wood/worn | — |
| Content/EnvSandbox/Meshes/Atlantis/SM_Atlantis_DoorLeftE.uasset | Content/EnvSandbox/Materials/Instances/Architecture/Atlantis/MI_Arch_Atl_DoorLeftE | wood/worn | — |
| Content/EnvSandbox/Meshes/Atlantis/SM_Atlantis_DoorLeftF.uasset | Content/EnvSandbox/Materials/Instances/Architecture/Atlantis/MI_Arch_Atl_DoorLeftF | wood/worn | — |
| Content/EnvSandbox/Meshes/Atlantis/SM_Atlantis_DoorLeftG.uasset | Content/EnvSandbox/Materials/Instances/Architecture/Atlantis/MI_Arch_Atl_DoorLeftG | wood/worn | — |
| Content/EnvSandbox/Meshes/Atlantis/SM_Atlantis_DoorLeftH.uasset | Content/EnvSandbox/Materials/Instances/Architecture/Atlantis/MI_Arch_Atl_DoorLeftH | wood/worn | — |
| Content/EnvSandbox/Meshes/Atlantis/SM_Atlantis_DoorRightA.uasset | Content/EnvSandbox/Materials/Instances/Architecture/Atlantis/MI_Arch_Atl_DoorRightA | wood/worn | — |
| Content/EnvSandbox/Meshes/Atlantis/SM_Atlantis_DoorRightB.uasset | Content/EnvSandbox/Materials/Instances/Architecture/Atlantis/MI_Arch_Atl_DoorRightB | wood/worn | — |
| Content/EnvSandbox/Meshes/Atlantis/SM_Atlantis_DoorRightC.uasset | Content/EnvSandbox/Materials/Instances/Architecture/Atlantis/MI_Arch_Atl_DoorRightC | wood/worn | — |
| Content/EnvSandbox/Meshes/Atlantis/SM_Atlantis_DoorRightD.uasset | Content/EnvSandbox/Materials/Instances/Architecture/Atlantis/MI_Arch_Atl_DoorRightD | wood/worn | — |
| Content/EnvSandbox/Meshes/Atlantis/SM_Atlantis_DoorRightE.uasset | Content/EnvSandbox/Materials/Instances/Architecture/Atlantis/MI_Arch_Atl_DoorRightE | wood/worn | — |
| Content/EnvSandbox/Meshes/Atlantis/SM_Atlantis_DoorRightF.uasset | Content/EnvSandbox/Materials/Instances/Architecture/Atlantis/MI_Arch_Atl_DoorRightF | wood/worn | — |
| Content/EnvSandbox/Meshes/Atlantis/SM_Atlantis_DoorRightG.uasset | Content/EnvSandbox/Materials/Instances/Architecture/Atlantis/MI_Arch_Atl_DoorRightG | wood/worn | — |
| Content/EnvSandbox/Meshes/Atlantis/SM_Atlantis_DoorRightH.uasset | Content/EnvSandbox/Materials/Instances/Architecture/Atlantis/MI_Arch_Atl_DoorRightH | wood/worn | — |
| Content/EnvSandbox/Meshes/Atlantis/SM_Atlantis_DrainA.uasset | Content/EnvSandbox/Materials/Instances/Architecture/Atlantis/MI_Arch_Atl_DrainA | stone/brick/trim | — |
| Content/EnvSandbox/Meshes/Atlantis/SM_Atlantis_DrainB.uasset | Content/EnvSandbox/Materials/Instances/Architecture/Atlantis/MI_Arch_Atl_DrainB | stone/brick/trim | — |
| Content/EnvSandbox/Meshes/Atlantis/SM_Atlantis_DrainC.uasset | Content/EnvSandbox/Materials/Instances/Architecture/Atlantis/MI_Arch_Atl_DrainC | stone/brick/trim | — |
| Content/EnvSandbox/Meshes/Atlantis/SM_Atlantis_DrainD.uasset | Content/EnvSandbox/Materials/Instances/Architecture/Atlantis/MI_Arch_Atl_DrainD | stone/brick/trim | — |
| Content/EnvSandbox/Meshes/Atlantis/SM_Atlantis_DrainE.uasset | Content/EnvSandbox/Materials/Instances/Architecture/Atlantis/MI_Arch_Atl_DrainE | stone/brick/trim | — |
| Content/EnvSandbox/Meshes/Atlantis/SM_Atlantis_FloorA.uasset | Content/EnvSandbox/Materials/Instances/Architecture/Atlantis/MI_Arch_Atl_FloorA | stone/brick/trim | — |
| Content/EnvSandbox/Meshes/Atlantis/SM_Atlantis_FloorB.uasset | Content/EnvSandbox/Materials/Instances/Architecture/Atlantis/MI_Arch_Atl_FloorB | stone/brick/trim | — |
| Content/EnvSandbox/Meshes/Atlantis/SM_Atlantis_FloorC.uasset | Content/EnvSandbox/Materials/Instances/Architecture/Atlantis/MI_Arch_Atl_FloorC | stone/brick/trim | — |
| Content/EnvSandbox/Meshes/Atlantis/SM_Atlantis_FountainA.uasset | Content/EnvSandbox/Materials/Instances/Architecture/Atlantis/MI_Arch_Atl_FountainA | stone/brick/trim | — |
| Content/EnvSandbox/Meshes/Atlantis/SM_Atlantis_FountainB.uasset | Content/EnvSandbox/Materials/Instances/Architecture/Atlantis/MI_Arch_Atl_FountainB | stone/brick/trim | — |
| Content/EnvSandbox/Meshes/Atlantis/SM_Atlantis_FountainC.uasset | Content/EnvSandbox/Materials/Instances/Architecture/Atlantis/MI_Arch_Atl_FountainC | stone/brick/trim | — |
| Content/EnvSandbox/Meshes/Atlantis/SM_Atlantis_GrapesStand.uasset | Content/EnvSandbox/Materials/Instances/Architecture/Atlantis/MI_Arch_Atl_GrapesStand | wood/worn | — |
| Content/EnvSandbox/Meshes/Atlantis/SM_Atlantis_GuardrailA.uasset | Content/EnvSandbox/Materials/Instances/Architecture/Atlantis/MI_Arch_Atl_GuardrailA | default | — |
| Content/EnvSandbox/Meshes/Atlantis/SM_Atlantis_GuardrailB.uasset | Content/EnvSandbox/Materials/Instances/Architecture/Atlantis/MI_Arch_Atl_GuardrailB | default | — |
| Content/EnvSandbox/Meshes/Atlantis/SM_Atlantis_GuardrailC.uasset | Content/EnvSandbox/Materials/Instances/Architecture/Atlantis/MI_Arch_Atl_GuardrailC | default | — |
| Content/EnvSandbox/Meshes/Atlantis/SM_Atlantis_GuardrailD.uasset | Content/EnvSandbox/Materials/Instances/Architecture/Atlantis/MI_Arch_Atl_GuardrailD | default | — |
| Content/EnvSandbox/Meshes/Atlantis/SM_Atlantis_GuardrailE.uasset | Content/EnvSandbox/Materials/Instances/Architecture/Atlantis/MI_Arch_Atl_GuardrailE | default | — |
| Content/EnvSandbox/Meshes/Atlantis/SM_Atlantis_GuardrailF.uasset | Content/EnvSandbox/Materials/Instances/Architecture/Atlantis/MI_Arch_Atl_GuardrailF | default | — |
| Content/EnvSandbox/Meshes/Atlantis/SM_Atlantis_GuardrailG.uasset | Content/EnvSandbox/Materials/Instances/Architecture/Atlantis/MI_Arch_Atl_GuardrailG | default | — |
| Content/EnvSandbox/Meshes/Atlantis/SM_Atlantis_GuardrailH.uasset | Content/EnvSandbox/Materials/Instances/Architecture/Atlantis/MI_Arch_Atl_GuardrailH | default | — |
| Content/EnvSandbox/Meshes/Atlantis/SM_Atlantis_GuardrailI.uasset | Content/EnvSandbox/Materials/Instances/Architecture/Atlantis/MI_Arch_Atl_GuardrailI | default | — |
| Content/EnvSandbox/Meshes/Atlantis/SM_Atlantis_GuardrailJ.uasset | Content/EnvSandbox/Materials/Instances/Architecture/Atlantis/MI_Arch_Atl_GuardrailJ | default | — |
| Content/EnvSandbox/Meshes/Atlantis/SM_Atlantis_Harp.uasset | Content/EnvSandbox/Materials/Instances/Architecture/Atlantis/MI_Arch_Atl_Harp | gold | — |
| Content/EnvSandbox/Meshes/Atlantis/SM_Atlantis_HayStack.uasset | Content/EnvSandbox/Materials/Instances/Architecture/Atlantis/MI_Arch_Atl_HayStack | wood/worn | — |
| Content/EnvSandbox/Meshes/Atlantis/SM_Atlantis_IvyHangingA.uasset | Content/EnvSandbox/Materials/Instances/Architecture/Atlantis/MI_Arch_Atl_IvyHangingA | default | — |
| Content/EnvSandbox/Meshes/Atlantis/SM_Atlantis_IvyHangingB.uasset | Content/EnvSandbox/Materials/Instances/Architecture/Atlantis/MI_Arch_Atl_IvyHangingB | default | — |
| Content/EnvSandbox/Meshes/Atlantis/SM_Atlantis_IvyHangingC.uasset | Content/EnvSandbox/Materials/Instances/Architecture/Atlantis/MI_Arch_Atl_IvyHangingC | default | — |
| Content/EnvSandbox/Meshes/Atlantis/SM_Atlantis_IvyHangingD.uasset | Content/EnvSandbox/Materials/Instances/Architecture/Atlantis/MI_Arch_Atl_IvyHangingD | default | — |
| Content/EnvSandbox/Meshes/Atlantis/SM_Atlantis_IvyHangingE.uasset | Content/EnvSandbox/Materials/Instances/Architecture/Atlantis/MI_Arch_Atl_IvyHangingE | default | — |
| Content/EnvSandbox/Meshes/Atlantis/SM_Atlantis_IvyHangingF.uasset | Content/EnvSandbox/Materials/Instances/Architecture/Atlantis/MI_Arch_Atl_IvyHangingF | default | — |
| Content/EnvSandbox/Meshes/Atlantis/SM_Atlantis_IvyHangingG.uasset | Content/EnvSandbox/Materials/Instances/Architecture/Atlantis/MI_Arch_Atl_IvyHangingG | default | — |
| Content/EnvSandbox/Meshes/Atlantis/SM_Atlantis_IvyHangingH.uasset | Content/EnvSandbox/Materials/Instances/Architecture/Atlantis/MI_Arch_Atl_IvyHangingH | default | — |
| Content/EnvSandbox/Meshes/Atlantis/SM_Atlantis_IvyHangingI.uasset | Content/EnvSandbox/Materials/Instances/Architecture/Atlantis/MI_Arch_Atl_IvyHangingI | default | — |
| Content/EnvSandbox/Meshes/Atlantis/SM_Atlantis_IvyHangingJ.uasset | Content/EnvSandbox/Materials/Instances/Architecture/Atlantis/MI_Arch_Atl_IvyHangingJ | default | — |
| Content/EnvSandbox/Meshes/Atlantis/SM_Atlantis_IvyHangingK.uasset | Content/EnvSandbox/Materials/Instances/Architecture/Atlantis/MI_Arch_Atl_IvyHangingK | default | — |
| Content/EnvSandbox/Meshes/Atlantis/SM_Atlantis_IvyHangingL.uasset | Content/EnvSandbox/Materials/Instances/Architecture/Atlantis/MI_Arch_Atl_IvyHangingL | default | — |
| Content/EnvSandbox/Meshes/Atlantis/SM_Atlantis_IvyHangingM.uasset | Content/EnvSandbox/Materials/Instances/Architecture/Atlantis/MI_Arch_Atl_IvyHangingM | default | — |
| Content/EnvSandbox/Meshes/Atlantis/SM_Atlantis_IvyWallA.uasset | Content/EnvSandbox/Materials/Instances/Architecture/Atlantis/MI_Arch_Atl_IvyWallA | stone/brick/trim | — |
| Content/EnvSandbox/Meshes/Atlantis/SM_Atlantis_IvyWallB.uasset | Content/EnvSandbox/Materials/Instances/Architecture/Atlantis/MI_Arch_Atl_IvyWallB | stone/brick/trim | — |
| Content/EnvSandbox/Meshes/Atlantis/SM_Atlantis_IvyWallC.uasset | Content/EnvSandbox/Materials/Instances/Architecture/Atlantis/MI_Arch_Atl_IvyWallC | stone/brick/trim | — |
| Content/EnvSandbox/Meshes/Atlantis/SM_Atlantis_NicheA.uasset | Content/EnvSandbox/Materials/Instances/Architecture/Atlantis/MI_Arch_Atl_NicheA | gold | — |
| Content/EnvSandbox/Meshes/Atlantis/SM_Atlantis_NicheB.uasset | Content/EnvSandbox/Materials/Instances/Architecture/Atlantis/MI_Arch_Atl_NicheB | gold | — |
| Content/EnvSandbox/Meshes/Atlantis/SM_Atlantis_NicheC.uasset | Content/EnvSandbox/Materials/Instances/Architecture/Atlantis/MI_Arch_Atl_NicheC | gold | — |
| Content/EnvSandbox/Meshes/Atlantis/SM_Atlantis_NicheD.uasset | Content/EnvSandbox/Materials/Instances/Architecture/Atlantis/MI_Arch_Atl_NicheD | gold | — |
| Content/EnvSandbox/Meshes/Atlantis/SM_Atlantis_NicheE.uasset | Content/EnvSandbox/Materials/Instances/Architecture/Atlantis/MI_Arch_Atl_NicheE | gold | — |
| Content/EnvSandbox/Meshes/Atlantis/SM_Atlantis_OrnamentsA.uasset | Content/EnvSandbox/Materials/Instances/Architecture/Atlantis/MI_Arch_Atl_OrnamentsA | gold | — |
| Content/EnvSandbox/Meshes/Atlantis/SM_Atlantis_OrnamentsB.uasset | Content/EnvSandbox/Materials/Instances/Architecture/Atlantis/MI_Arch_Atl_OrnamentsB | gold | — |
| Content/EnvSandbox/Meshes/Atlantis/SM_Atlantis_OrnamentsC.uasset | Content/EnvSandbox/Materials/Instances/Architecture/Atlantis/MI_Arch_Atl_OrnamentsC | gold | — |
| Content/EnvSandbox/Meshes/Atlantis/SM_Atlantis_OrnamentsD.uasset | Content/EnvSandbox/Materials/Instances/Architecture/Atlantis/MI_Arch_Atl_OrnamentsD | gold | — |
| Content/EnvSandbox/Meshes/Atlantis/SM_Atlantis_OrnamentsE.uasset | Content/EnvSandbox/Materials/Instances/Architecture/Atlantis/MI_Arch_Atl_OrnamentsE | gold | — |
| Content/EnvSandbox/Meshes/Atlantis/SM_Atlantis_PergolaA.uasset | Content/EnvSandbox/Materials/Instances/Architecture/Atlantis/MI_Arch_Atl_PergolaA | stone/brick/trim | — |
| Content/EnvSandbox/Meshes/Atlantis/SM_Atlantis_PergolaB.uasset | Content/EnvSandbox/Materials/Instances/Architecture/Atlantis/MI_Arch_Atl_PergolaB | stone/brick/trim | — |
| Content/EnvSandbox/Meshes/Atlantis/SM_Atlantis_PergolaC.uasset | Content/EnvSandbox/Materials/Instances/Architecture/Atlantis/MI_Arch_Atl_PergolaC | stone/brick/trim | — |
| Content/EnvSandbox/Meshes/Atlantis/SM_Atlantis_PergolaD.uasset | Content/EnvSandbox/Materials/Instances/Architecture/Atlantis/MI_Arch_Atl_PergolaD | stone/brick/trim | — |
| Content/EnvSandbox/Meshes/Atlantis/SM_Atlantis_PlanterA.uasset | Content/EnvSandbox/Materials/Instances/Architecture/Atlantis/MI_Arch_Atl_PlanterA | stone/brick/trim | — |
| Content/EnvSandbox/Meshes/Atlantis/SM_Atlantis_PlanterB.uasset | Content/EnvSandbox/Materials/Instances/Architecture/Atlantis/MI_Arch_Atl_PlanterB | stone/brick/trim | — |
| Content/EnvSandbox/Meshes/Atlantis/SM_Atlantis_PlanterC.uasset | Content/EnvSandbox/Materials/Instances/Architecture/Atlantis/MI_Arch_Atl_PlanterC | stone/brick/trim | — |
| Content/EnvSandbox/Meshes/Atlantis/SM_Atlantis_PlanterD.uasset | Content/EnvSandbox/Materials/Instances/Architecture/Atlantis/MI_Arch_Atl_PlanterD | stone/brick/trim | — |
| Content/EnvSandbox/Meshes/Atlantis/SM_Atlantis_PlanterE.uasset | Content/EnvSandbox/Materials/Instances/Architecture/Atlantis/MI_Arch_Atl_PlanterE | stone/brick/trim | — |
| Content/EnvSandbox/Meshes/Atlantis/SM_Atlantis_PlanterF.uasset | Content/EnvSandbox/Materials/Instances/Architecture/Atlantis/MI_Arch_Atl_PlanterF | stone/brick/trim | — |
| Content/EnvSandbox/Meshes/Atlantis/SM_Atlantis_PlanterG.uasset | Content/EnvSandbox/Materials/Instances/Architecture/Atlantis/MI_Arch_Atl_PlanterG | stone/brick/trim | — |
| Content/EnvSandbox/Meshes/Atlantis/SM_Atlantis_PlanterH.uasset | Content/EnvSandbox/Materials/Instances/Architecture/Atlantis/MI_Arch_Atl_PlanterH | stone/brick/trim | — |
| Content/EnvSandbox/Meshes/Atlantis/SM_Atlantis_PlanterI.uasset | Content/EnvSandbox/Materials/Instances/Architecture/Atlantis/MI_Arch_Atl_PlanterI | stone/brick/trim | — |
| Content/EnvSandbox/Meshes/Atlantis/SM_Atlantis_PlanterJ.uasset | Content/EnvSandbox/Materials/Instances/Architecture/Atlantis/MI_Arch_Atl_PlanterJ | stone/brick/trim | — |
| Content/EnvSandbox/Meshes/Atlantis/SM_Atlantis_PlanterK.uasset | Content/EnvSandbox/Materials/Instances/Architecture/Atlantis/MI_Arch_Atl_PlanterK | stone/brick/trim | — |
| Content/EnvSandbox/Meshes/Atlantis/SM_Atlantis_PlanterL.uasset | Content/EnvSandbox/Materials/Instances/Architecture/Atlantis/MI_Arch_Atl_PlanterL | stone/brick/trim | — |
| Content/EnvSandbox/Meshes/Atlantis/SM_Atlantis_PlanterM.uasset | Content/EnvSandbox/Materials/Instances/Architecture/Atlantis/MI_Arch_Atl_PlanterM | stone/brick/trim | — |
| Content/EnvSandbox/Meshes/Atlantis/SM_Atlantis_PlanterN.uasset | Content/EnvSandbox/Materials/Instances/Architecture/Atlantis/MI_Arch_Atl_PlanterN | stone/brick/trim | — |
| Content/EnvSandbox/Meshes/Atlantis/SM_Atlantis_PlanterO.uasset | Content/EnvSandbox/Materials/Instances/Architecture/Atlantis/MI_Arch_Atl_PlanterO | stone/brick/trim | — |
| Content/EnvSandbox/Meshes/Atlantis/SM_Atlantis_PlanterP.uasset | Content/EnvSandbox/Materials/Instances/Architecture/Atlantis/MI_Arch_Atl_PlanterP | stone/brick/trim | — |
| Content/EnvSandbox/Meshes/Atlantis/SM_Atlantis_PlanterQ.uasset | Content/EnvSandbox/Materials/Instances/Architecture/Atlantis/MI_Arch_Atl_PlanterQ | stone/brick/trim | — |
| Content/EnvSandbox/Meshes/Atlantis/SM_Atlantis_PlanterR.uasset | Content/EnvSandbox/Materials/Instances/Architecture/Atlantis/MI_Arch_Atl_PlanterR | stone/brick/trim | — |
| Content/EnvSandbox/Meshes/Atlantis/SM_Atlantis_PlanterS.uasset | Content/EnvSandbox/Materials/Instances/Architecture/Atlantis/MI_Arch_Atl_PlanterS | stone/brick/trim | — |
| Content/EnvSandbox/Meshes/Atlantis/SM_Atlantis_PlanterT.uasset | Content/EnvSandbox/Materials/Instances/Architecture/Atlantis/MI_Arch_Atl_PlanterT | stone/brick/trim | — |
| Content/EnvSandbox/Meshes/Atlantis/SM_Atlantis_PlanterU.uasset | Content/EnvSandbox/Materials/Instances/Architecture/Atlantis/MI_Arch_Atl_PlanterU | stone/brick/trim | — |
| Content/EnvSandbox/Meshes/Atlantis/SM_Atlantis_PlanterV.uasset | Content/EnvSandbox/Materials/Instances/Architecture/Atlantis/MI_Arch_Atl_PlanterV | stone/brick/trim | — |
| Content/EnvSandbox/Meshes/Atlantis/SM_Atlantis_PlanterW.uasset | Content/EnvSandbox/Materials/Instances/Architecture/Atlantis/MI_Arch_Atl_PlanterW | stone/brick/trim | — |
| Content/EnvSandbox/Meshes/Atlantis/SM_Atlantis_PlantersA.uasset | Content/EnvSandbox/Materials/Instances/Architecture/Atlantis/MI_Arch_Atl_PlantersA | stone/brick/trim | — |
| Content/EnvSandbox/Meshes/Atlantis/SM_Atlantis_PlantersB.uasset | Content/EnvSandbox/Materials/Instances/Architecture/Atlantis/MI_Arch_Atl_PlantersB | stone/brick/trim | — |
| Content/EnvSandbox/Meshes/Atlantis/SM_Atlantis_RoofA.uasset | Content/EnvSandbox/Materials/Instances/Architecture/Atlantis/MI_Arch_Atl_RoofA | stone/brick/trim | — |
| Content/EnvSandbox/Meshes/Atlantis/SM_Atlantis_RoofB.uasset | Content/EnvSandbox/Materials/Instances/Architecture/Atlantis/MI_Arch_Atl_RoofB | stone/brick/trim | — |
| Content/EnvSandbox/Meshes/Atlantis/SM_Atlantis_RoofC.uasset | Content/EnvSandbox/Materials/Instances/Architecture/Atlantis/MI_Arch_Atl_RoofC | stone/brick/trim | — |
| Content/EnvSandbox/Meshes/Atlantis/SM_Atlantis_RoofD.uasset | Content/EnvSandbox/Materials/Instances/Architecture/Atlantis/MI_Arch_Atl_RoofD | stone/brick/trim | — |
| Content/EnvSandbox/Meshes/Atlantis/SM_Atlantis_RoofE.uasset | Content/EnvSandbox/Materials/Instances/Architecture/Atlantis/MI_Arch_Atl_RoofE | stone/brick/trim | — |
| Content/EnvSandbox/Meshes/Atlantis/SM_Atlantis_RoofTiles.uasset | Content/EnvSandbox/Materials/Instances/Architecture/Atlantis/MI_Arch_Atl_RoofTiles | stone/brick/trim | — |
| Content/EnvSandbox/Meshes/Atlantis/SM_Atlantis_ShrubsA.uasset | Content/EnvSandbox/Materials/Instances/Architecture/Atlantis/MI_Arch_Atl_ShrubsA | default | — |
| Content/EnvSandbox/Meshes/Atlantis/SM_Atlantis_ShrubsB.uasset | Content/EnvSandbox/Materials/Instances/Architecture/Atlantis/MI_Arch_Atl_ShrubsB | default | — |
| Content/EnvSandbox/Meshes/Atlantis/SM_Atlantis_ShrubsC.uasset | Content/EnvSandbox/Materials/Instances/Architecture/Atlantis/MI_Arch_Atl_ShrubsC | default | — |
| Content/EnvSandbox/Meshes/Atlantis/SM_Atlantis_ShrubsD.uasset | Content/EnvSandbox/Materials/Instances/Architecture/Atlantis/MI_Arch_Atl_ShrubsD | default | — |
| Content/EnvSandbox/Meshes/Atlantis/SM_Atlantis_ShrubsE.uasset | Content/EnvSandbox/Materials/Instances/Architecture/Atlantis/MI_Arch_Atl_ShrubsE | default | — |
| Content/EnvSandbox/Meshes/Atlantis/SM_Atlantis_ShrubsF.uasset | Content/EnvSandbox/Materials/Instances/Architecture/Atlantis/MI_Arch_Atl_ShrubsF | default | — |
| Content/EnvSandbox/Meshes/Atlantis/SM_Atlantis_ShrubsG.uasset | Content/EnvSandbox/Materials/Instances/Architecture/Atlantis/MI_Arch_Atl_ShrubsG | default | — |
| Content/EnvSandbox/Meshes/Atlantis/SM_Atlantis_ShrubsH.uasset | Content/EnvSandbox/Materials/Instances/Architecture/Atlantis/MI_Arch_Atl_ShrubsH | default | — |
| Content/EnvSandbox/Meshes/Atlantis/SM_Atlantis_ShrubsI.uasset | Content/EnvSandbox/Materials/Instances/Architecture/Atlantis/MI_Arch_Atl_ShrubsI | default | — |
| Content/EnvSandbox/Meshes/Atlantis/SM_Atlantis_ShrubsJ.uasset | Content/EnvSandbox/Materials/Instances/Architecture/Atlantis/MI_Arch_Atl_ShrubsJ | default | — |
| Content/EnvSandbox/Meshes/Atlantis/SM_Atlantis_ShrubsK.uasset | Content/EnvSandbox/Materials/Instances/Architecture/Atlantis/MI_Arch_Atl_ShrubsK | default | — |
| Content/EnvSandbox/Meshes/Atlantis/SM_Atlantis_ShrubsL.uasset | Content/EnvSandbox/Materials/Instances/Architecture/Atlantis/MI_Arch_Atl_ShrubsL | default | — |
| Content/EnvSandbox/Meshes/Atlantis/SM_Atlantis_ShrubsM.uasset | Content/EnvSandbox/Materials/Instances/Architecture/Atlantis/MI_Arch_Atl_ShrubsM | default | — |
| Content/EnvSandbox/Meshes/Atlantis/SM_Atlantis_ShrubsN.uasset | Content/EnvSandbox/Materials/Instances/Architecture/Atlantis/MI_Arch_Atl_ShrubsN | default | — |
| Content/EnvSandbox/Meshes/Atlantis/SM_Atlantis_ShrubsO.uasset | Content/EnvSandbox/Materials/Instances/Architecture/Atlantis/MI_Arch_Atl_ShrubsO | default | — |
| Content/EnvSandbox/Meshes/Atlantis/SM_Atlantis_ShrubsP.uasset | Content/EnvSandbox/Materials/Instances/Architecture/Atlantis/MI_Arch_Atl_ShrubsP | default | — |
| Content/EnvSandbox/Meshes/Atlantis/SM_Atlantis_ShrubsQ.uasset | Content/EnvSandbox/Materials/Instances/Architecture/Atlantis/MI_Arch_Atl_ShrubsQ | default | — |
| Content/EnvSandbox/Meshes/Atlantis/SM_Atlantis_ShrubsR.uasset | Content/EnvSandbox/Materials/Instances/Architecture/Atlantis/MI_Arch_Atl_ShrubsR | default | — |
| Content/EnvSandbox/Meshes/Atlantis/SM_Atlantis_ShrubsS.uasset | Content/EnvSandbox/Materials/Instances/Architecture/Atlantis/MI_Arch_Atl_ShrubsS | default | — |
| Content/EnvSandbox/Meshes/Atlantis/SM_Atlantis_ShrubsT.uasset | Content/EnvSandbox/Materials/Instances/Architecture/Atlantis/MI_Arch_Atl_ShrubsT | default | — |
| Content/EnvSandbox/Meshes/Atlantis/SM_Atlantis_ShrubsU.uasset | Content/EnvSandbox/Materials/Instances/Architecture/Atlantis/MI_Arch_Atl_ShrubsU | default | — |
| Content/EnvSandbox/Meshes/Atlantis/SM_Atlantis_ShrubsV.uasset | Content/EnvSandbox/Materials/Instances/Architecture/Atlantis/MI_Arch_Atl_ShrubsV | default | — |
| Content/EnvSandbox/Meshes/Atlantis/SM_Atlantis_ShrubsW.uasset | Content/EnvSandbox/Materials/Instances/Architecture/Atlantis/MI_Arch_Atl_ShrubsW | default | — |
| Content/EnvSandbox/Meshes/Atlantis/SM_Atlantis_ShrubsX.uasset | Content/EnvSandbox/Materials/Instances/Architecture/Atlantis/MI_Arch_Atl_ShrubsX | default | — |
| Content/EnvSandbox/Meshes/Atlantis/SM_Atlantis_StairsA.uasset | Content/EnvSandbox/Materials/Instances/Architecture/Atlantis/MI_Arch_Atl_StairsA | stone/brick/trim | — |
| Content/EnvSandbox/Meshes/Atlantis/SM_Atlantis_StairsB.uasset | Content/EnvSandbox/Materials/Instances/Architecture/Atlantis/MI_Arch_Atl_StairsB | stone/brick/trim | — |
| Content/EnvSandbox/Meshes/Atlantis/SM_Atlantis_StairsC.uasset | Content/EnvSandbox/Materials/Instances/Architecture/Atlantis/MI_Arch_Atl_StairsC | stone/brick/trim | — |
| Content/EnvSandbox/Meshes/Atlantis/SM_Atlantis_StairsD.uasset | Content/EnvSandbox/Materials/Instances/Architecture/Atlantis/MI_Arch_Atl_StairsD | stone/brick/trim | — |
| Content/EnvSandbox/Meshes/Atlantis/SM_Atlantis_StairsE.uasset | Content/EnvSandbox/Materials/Instances/Architecture/Atlantis/MI_Arch_Atl_StairsE | stone/brick/trim | — |
| Content/EnvSandbox/Meshes/Atlantis/SM_Atlantis_StairsF.uasset | Content/EnvSandbox/Materials/Instances/Architecture/Atlantis/MI_Arch_Atl_StairsF | stone/brick/trim | — |
| Content/EnvSandbox/Meshes/Atlantis/SM_Atlantis_StepsA.uasset | Content/EnvSandbox/Materials/Instances/Architecture/Atlantis/MI_Arch_Atl_StepsA | stone/brick/trim | — |
| Content/EnvSandbox/Meshes/Atlantis/SM_Atlantis_StepsB.uasset | Content/EnvSandbox/Materials/Instances/Architecture/Atlantis/MI_Arch_Atl_StepsB | stone/brick/trim | — |
| Content/EnvSandbox/Meshes/Atlantis/SM_Atlantis_StepsC.uasset | Content/EnvSandbox/Materials/Instances/Architecture/Atlantis/MI_Arch_Atl_StepsC | stone/brick/trim | — |
| Content/EnvSandbox/Meshes/Atlantis/SM_Atlantis_StoolA.uasset | Content/EnvSandbox/Materials/Instances/Architecture/Atlantis/MI_Arch_Atl_StoolA | wood/worn | — |
| Content/EnvSandbox/Meshes/Atlantis/SM_Atlantis_StoolB.uasset | Content/EnvSandbox/Materials/Instances/Architecture/Atlantis/MI_Arch_Atl_StoolB | wood/worn | — |
| Content/EnvSandbox/Meshes/Atlantis/SM_Atlantis_StoolC.uasset | Content/EnvSandbox/Materials/Instances/Architecture/Atlantis/MI_Arch_Atl_StoolC | wood/worn | — |
| Content/EnvSandbox/Meshes/Atlantis/SM_Atlantis_StoolD.uasset | Content/EnvSandbox/Materials/Instances/Architecture/Atlantis/MI_Arch_Atl_StoolD | wood/worn | — |
| Content/EnvSandbox/Meshes/Atlantis/SM_Atlantis_StoolE.uasset | Content/EnvSandbox/Materials/Instances/Architecture/Atlantis/MI_Arch_Atl_StoolE | wood/worn | — |
| Content/EnvSandbox/Meshes/Atlantis/SM_Atlantis_StoolF.uasset | Content/EnvSandbox/Materials/Instances/Architecture/Atlantis/MI_Arch_Atl_StoolF | wood/worn | — |
| Content/EnvSandbox/Meshes/Atlantis/SM_Atlantis_StoolG.uasset | Content/EnvSandbox/Materials/Instances/Architecture/Atlantis/MI_Arch_Atl_StoolG | wood/worn | — |
| Content/EnvSandbox/Meshes/Atlantis/SM_Atlantis_StoolH.uasset | Content/EnvSandbox/Materials/Instances/Architecture/Atlantis/MI_Arch_Atl_StoolH | wood/worn | — |
| Content/EnvSandbox/Meshes/Atlantis/SM_Atlantis_StoolI.uasset | Content/EnvSandbox/Materials/Instances/Architecture/Atlantis/MI_Arch_Atl_StoolI | wood/worn | — |
| Content/EnvSandbox/Meshes/Atlantis/SM_Atlantis_StoolJ.uasset | Content/EnvSandbox/Materials/Instances/Architecture/Atlantis/MI_Arch_Atl_StoolJ | wood/worn | — |
| Content/EnvSandbox/Meshes/Atlantis/SM_Atlantis_StoolK.uasset | Content/EnvSandbox/Materials/Instances/Architecture/Atlantis/MI_Arch_Atl_StoolK | wood/worn | — |
| Content/EnvSandbox/Meshes/Atlantis/SM_Atlantis_StoolL.uasset | Content/EnvSandbox/Materials/Instances/Architecture/Atlantis/MI_Arch_Atl_StoolL | wood/worn | — |
| Content/EnvSandbox/Meshes/Atlantis/SM_Atlantis_StoolM.uasset | Content/EnvSandbox/Materials/Instances/Architecture/Atlantis/MI_Arch_Atl_StoolM | wood/worn | — |
| Content/EnvSandbox/Meshes/Atlantis/SM_Atlantis_StoolN.uasset | Content/EnvSandbox/Materials/Instances/Architecture/Atlantis/MI_Arch_Atl_StoolN | wood/worn | — |
| Content/EnvSandbox/Meshes/Atlantis/SM_Atlantis_StoolO.uasset | Content/EnvSandbox/Materials/Instances/Architecture/Atlantis/MI_Arch_Atl_StoolO | wood/worn | — |
| Content/EnvSandbox/Meshes/Atlantis/SM_Atlantis_TableA.uasset | Content/EnvSandbox/Materials/Instances/Architecture/Atlantis/MI_Arch_Atl_TableA | wood/worn | — |
| Content/EnvSandbox/Meshes/Atlantis/SM_Atlantis_TableB.uasset | Content/EnvSandbox/Materials/Instances/Architecture/Atlantis/MI_Arch_Atl_TableB | wood/worn | — |
| Content/EnvSandbox/Meshes/Atlantis/SM_Atlantis_TableC.uasset | Content/EnvSandbox/Materials/Instances/Architecture/Atlantis/MI_Arch_Atl_TableC | wood/worn | — |
| Content/EnvSandbox/Meshes/Atlantis/SM_Atlantis_TableD.uasset | Content/EnvSandbox/Materials/Instances/Architecture/Atlantis/MI_Arch_Atl_TableD | wood/worn | — |
| Content/EnvSandbox/Meshes/Atlantis/SM_Atlantis_TableE.uasset | Content/EnvSandbox/Materials/Instances/Architecture/Atlantis/MI_Arch_Atl_TableE | wood/worn | — |
| Content/EnvSandbox/Meshes/Atlantis/SM_Atlantis_TableF.uasset | Content/EnvSandbox/Materials/Instances/Architecture/Atlantis/MI_Arch_Atl_TableF | wood/worn | — |
| Content/EnvSandbox/Meshes/Atlantis/SM_Atlantis_TableG.uasset | Content/EnvSandbox/Materials/Instances/Architecture/Atlantis/MI_Arch_Atl_TableG | wood/worn | — |
| Content/EnvSandbox/Meshes/Atlantis/SM_Atlantis_TableH.uasset | Content/EnvSandbox/Materials/Instances/Architecture/Atlantis/MI_Arch_Atl_TableH | wood/worn | — |
| Content/EnvSandbox/Meshes/Atlantis/SM_Atlantis_TableI.uasset | Content/EnvSandbox/Materials/Instances/Architecture/Atlantis/MI_Arch_Atl_TableI | wood/worn | — |
| Content/EnvSandbox/Meshes/Atlantis/SM_Atlantis_TableJ.uasset | Content/EnvSandbox/Materials/Instances/Architecture/Atlantis/MI_Arch_Atl_TableJ | wood/worn | — |
| Content/EnvSandbox/Meshes/Atlantis/SM_Atlantis_TorchA.uasset | Content/EnvSandbox/Materials/Instances/Architecture/Atlantis/MI_Arch_Atl_TorchA | gold | — |
| Content/EnvSandbox/Meshes/Atlantis/SM_Atlantis_TorchB.uasset | Content/EnvSandbox/Materials/Instances/Architecture/Atlantis/MI_Arch_Atl_TorchB | gold | — |
| Content/EnvSandbox/Meshes/Atlantis/SM_Atlantis_TorchC.uasset | Content/EnvSandbox/Materials/Instances/Architecture/Atlantis/MI_Arch_Atl_TorchC | gold | — |
| Content/EnvSandbox/Meshes/Atlantis/SM_Atlantis_TorchD.uasset | Content/EnvSandbox/Materials/Instances/Architecture/Atlantis/MI_Arch_Atl_TorchD | gold | — |
| Content/EnvSandbox/Meshes/Atlantis/SM_Atlantis_TorchE.uasset | Content/EnvSandbox/Materials/Instances/Architecture/Atlantis/MI_Arch_Atl_TorchE | gold | — |
| Content/EnvSandbox/Meshes/Atlantis/SM_Atlantis_TreeA.uasset | Content/EnvSandbox/Materials/Instances/Architecture/Atlantis/MI_Arch_Atl_TreeA | default | — |
| Content/EnvSandbox/Meshes/Atlantis/SM_Atlantis_TreeB.uasset | Content/EnvSandbox/Materials/Instances/Architecture/Atlantis/MI_Arch_Atl_TreeB | default | — |
| Content/EnvSandbox/Meshes/Atlantis/SM_Atlantis_TreeBottomA.uasset | Content/EnvSandbox/Materials/Instances/Architecture/Atlantis/MI_Arch_Atl_TreeBottomA | default | — |
| Content/EnvSandbox/Meshes/Atlantis/SM_Atlantis_TreeBottomB.uasset | Content/EnvSandbox/Materials/Instances/Architecture/Atlantis/MI_Arch_Atl_TreeBottomB | default | — |
| Content/EnvSandbox/Meshes/Atlantis/SM_Atlantis_TreeBottomC.uasset | Content/EnvSandbox/Materials/Instances/Architecture/Atlantis/MI_Arch_Atl_TreeBottomC | default | — |
| Content/EnvSandbox/Meshes/Atlantis/SM_Atlantis_TreeBottomD.uasset | Content/EnvSandbox/Materials/Instances/Architecture/Atlantis/MI_Arch_Atl_TreeBottomD | default | — |
| Content/EnvSandbox/Meshes/Atlantis/SM_Atlantis_TreeBottomE.uasset | Content/EnvSandbox/Materials/Instances/Architecture/Atlantis/MI_Arch_Atl_TreeBottomE | default | — |
| Content/EnvSandbox/Meshes/Atlantis/SM_Atlantis_TreeBottomF.uasset | Content/EnvSandbox/Materials/Instances/Architecture/Atlantis/MI_Arch_Atl_TreeBottomF | default | — |
| Content/EnvSandbox/Meshes/Atlantis/SM_Atlantis_TreeBottomG.uasset | Content/EnvSandbox/Materials/Instances/Architecture/Atlantis/MI_Arch_Atl_TreeBottomG | default | — |
| Content/EnvSandbox/Meshes/Atlantis/SM_Atlantis_TreeC.uasset | Content/EnvSandbox/Materials/Instances/Architecture/Atlantis/MI_Arch_Atl_TreeC | default | — |
| Content/EnvSandbox/Meshes/Atlantis/SM_Atlantis_TreeD.uasset | Content/EnvSandbox/Materials/Instances/Architecture/Atlantis/MI_Arch_Atl_TreeD | default | — |
| Content/EnvSandbox/Meshes/Atlantis/SM_Atlantis_TreeE.uasset | Content/EnvSandbox/Materials/Instances/Architecture/Atlantis/MI_Arch_Atl_TreeE | default | — |
| Content/EnvSandbox/Meshes/Atlantis/SM_Atlantis_TreeF.uasset | Content/EnvSandbox/Materials/Instances/Architecture/Atlantis/MI_Arch_Atl_TreeF | default | — |
| Content/EnvSandbox/Meshes/Atlantis/SM_Atlantis_TreeG.uasset | Content/EnvSandbox/Materials/Instances/Architecture/Atlantis/MI_Arch_Atl_TreeG | default | — |
| Content/EnvSandbox/Meshes/Atlantis/SM_Atlantis_TreeH.uasset | Content/EnvSandbox/Materials/Instances/Architecture/Atlantis/MI_Arch_Atl_TreeH | default | — |
| Content/EnvSandbox/Meshes/Atlantis/SM_Atlantis_TreeI.uasset | Content/EnvSandbox/Materials/Instances/Architecture/Atlantis/MI_Arch_Atl_TreeI | default | — |
| Content/EnvSandbox/Meshes/Atlantis/SM_Atlantis_TreeJ.uasset | Content/EnvSandbox/Materials/Instances/Architecture/Atlantis/MI_Arch_Atl_TreeJ | default | — |
| Content/EnvSandbox/Meshes/Atlantis/SM_Atlantis_TreeK.uasset | Content/EnvSandbox/Materials/Instances/Architecture/Atlantis/MI_Arch_Atl_TreeK | default | — |
| Content/EnvSandbox/Meshes/Atlantis/SM_Atlantis_TreeL.uasset | Content/EnvSandbox/Materials/Instances/Architecture/Atlantis/MI_Arch_Atl_TreeL | default | — |
| Content/EnvSandbox/Meshes/Atlantis/SM_Atlantis_TreeM.uasset | Content/EnvSandbox/Materials/Instances/Architecture/Atlantis/MI_Arch_Atl_TreeM | default | — |
| Content/EnvSandbox/Meshes/Atlantis/SM_Atlantis_TreeN.uasset | Content/EnvSandbox/Materials/Instances/Architecture/Atlantis/MI_Arch_Atl_TreeN | default | — |
| Content/EnvSandbox/Meshes/Atlantis/SM_Atlantis_TreeO.uasset | Content/EnvSandbox/Materials/Instances/Architecture/Atlantis/MI_Arch_Atl_TreeO | default | — |
| Content/EnvSandbox/Meshes/Atlantis/SM_Atlantis_TreeP.uasset | Content/EnvSandbox/Materials/Instances/Architecture/Atlantis/MI_Arch_Atl_TreeP | default | — |
| Content/EnvSandbox/Meshes/Atlantis/SM_Atlantis_TreeQ.uasset | Content/EnvSandbox/Materials/Instances/Architecture/Atlantis/MI_Arch_Atl_TreeQ | default | — |
| Content/EnvSandbox/Meshes/Atlantis/SM_Atlantis_TreeR.uasset | Content/EnvSandbox/Materials/Instances/Architecture/Atlantis/MI_Arch_Atl_TreeR | default | — |
| Content/EnvSandbox/Meshes/Atlantis/SM_Atlantis_TreeS.uasset | Content/EnvSandbox/Materials/Instances/Architecture/Atlantis/MI_Arch_Atl_TreeS | default | — |
| Content/EnvSandbox/Meshes/Atlantis/SM_Atlantis_TreeTopA.uasset | Content/EnvSandbox/Materials/Instances/Architecture/Atlantis/MI_Arch_Atl_TreeTopA | default | — |
| Content/EnvSandbox/Meshes/Atlantis/SM_Atlantis_TreeTopB.uasset | Content/EnvSandbox/Materials/Instances/Architecture/Atlantis/MI_Arch_Atl_TreeTopB | default | — |
| Content/EnvSandbox/Meshes/Atlantis/SM_Atlantis_TreeTopC.uasset | Content/EnvSandbox/Materials/Instances/Architecture/Atlantis/MI_Arch_Atl_TreeTopC | default | — |
| Content/EnvSandbox/Meshes/Atlantis/SM_Atlantis_TreeTopD.uasset | Content/EnvSandbox/Materials/Instances/Architecture/Atlantis/MI_Arch_Atl_TreeTopD | default | — |
| Content/EnvSandbox/Meshes/Atlantis/SM_Atlantis_TreeTopE.uasset | Content/EnvSandbox/Materials/Instances/Architecture/Atlantis/MI_Arch_Atl_TreeTopE | default | — |
| Content/EnvSandbox/Meshes/Atlantis/SM_Atlantis_TreeTopF.uasset | Content/EnvSandbox/Materials/Instances/Architecture/Atlantis/MI_Arch_Atl_TreeTopF | default | — |
| Content/EnvSandbox/Meshes/Atlantis/SM_Atlantis_TreeTopG.uasset | Content/EnvSandbox/Materials/Instances/Architecture/Atlantis/MI_Arch_Atl_TreeTopG | default | — |
| Content/EnvSandbox/Meshes/Atlantis/SM_Atlantis_TreeTopH.uasset | Content/EnvSandbox/Materials/Instances/Architecture/Atlantis/MI_Arch_Atl_TreeTopH | default | — |
| Content/EnvSandbox/Meshes/Atlantis/SM_Atlantis_TreeTopI.uasset | Content/EnvSandbox/Materials/Instances/Architecture/Atlantis/MI_Arch_Atl_TreeTopI | default | — |
| Content/EnvSandbox/Meshes/Atlantis/SM_Atlantis_TreeTopJ.uasset | Content/EnvSandbox/Materials/Instances/Architecture/Atlantis/MI_Arch_Atl_TreeTopJ | default | — |
| Content/EnvSandbox/Meshes/Atlantis/SM_Atlantis_VaseA.uasset | Content/EnvSandbox/Materials/Instances/Architecture/Atlantis/MI_Arch_Atl_VaseA | stone/brick/trim | — |
| Content/EnvSandbox/Meshes/Atlantis/SM_Atlantis_VaseB.uasset | Content/EnvSandbox/Materials/Instances/Architecture/Atlantis/MI_Arch_Atl_VaseB | stone/brick/trim | — |
| Content/EnvSandbox/Meshes/Atlantis/SM_Atlantis_VaseC.uasset | Content/EnvSandbox/Materials/Instances/Architecture/Atlantis/MI_Arch_Atl_VaseC | stone/brick/trim | — |
| Content/EnvSandbox/Meshes/Atlantis/SM_Atlantis_VaseD.uasset | Content/EnvSandbox/Materials/Instances/Architecture/Atlantis/MI_Arch_Atl_VaseD | stone/brick/trim | — |
| Content/EnvSandbox/Meshes/Atlantis/SM_Atlantis_VaseE.uasset | Content/EnvSandbox/Materials/Instances/Architecture/Atlantis/MI_Arch_Atl_VaseE | stone/brick/trim | — |
| Content/EnvSandbox/Meshes/Atlantis/SM_Atlantis_VaseF.uasset | Content/EnvSandbox/Materials/Instances/Architecture/Atlantis/MI_Arch_Atl_VaseF | stone/brick/trim | — |
| Content/EnvSandbox/Meshes/Atlantis/SM_Atlantis_VaseG.uasset | Content/EnvSandbox/Materials/Instances/Architecture/Atlantis/MI_Arch_Atl_VaseG | stone/brick/trim | — |
| Content/EnvSandbox/Meshes/Atlantis/SM_Atlantis_VaseH.uasset | Content/EnvSandbox/Materials/Instances/Architecture/Atlantis/MI_Arch_Atl_VaseH | stone/brick/trim | — |
| Content/EnvSandbox/Meshes/Atlantis/SM_Atlantis_VaseI.uasset | Content/EnvSandbox/Materials/Instances/Architecture/Atlantis/MI_Arch_Atl_VaseI | stone/brick/trim | — |
| Content/EnvSandbox/Meshes/Atlantis/SM_Atlantis_VaseJ.uasset | Content/EnvSandbox/Materials/Instances/Architecture/Atlantis/MI_Arch_Atl_VaseJ | stone/brick/trim | — |
| Content/EnvSandbox/Meshes/Atlantis/SM_Atlantis_VaseK.uasset | Content/EnvSandbox/Materials/Instances/Architecture/Atlantis/MI_Arch_Atl_VaseK | stone/brick/trim | — |
| Content/EnvSandbox/Meshes/Atlantis/SM_Atlantis_VasesA.uasset | Content/EnvSandbox/Materials/Instances/Architecture/Atlantis/MI_Arch_Atl_VasesA | stone/brick/trim | — |
| Content/EnvSandbox/Meshes/Atlantis/SM_Atlantis_VasesB.uasset | Content/EnvSandbox/Materials/Instances/Architecture/Atlantis/MI_Arch_Atl_VasesB | stone/brick/trim | — |
| Content/EnvSandbox/Meshes/Atlantis/SM_Atlantis_VasesC.uasset | Content/EnvSandbox/Materials/Instances/Architecture/Atlantis/MI_Arch_Atl_VasesC | stone/brick/trim | — |
| Content/EnvSandbox/Meshes/Atlantis/SM_Atlantis_VasesD.uasset | Content/EnvSandbox/Materials/Instances/Architecture/Atlantis/MI_Arch_Atl_VasesD | stone/brick/trim | — |
| Content/EnvSandbox/Meshes/Atlantis/SM_Atlantis_VasesE.uasset | Content/EnvSandbox/Materials/Instances/Architecture/Atlantis/MI_Arch_Atl_VasesE | stone/brick/trim | — |

---

## Execution Notes

1. **Directory creation required:** `Architecture/Cathedral/` and `Architecture/Atlantis/`
   must be created before MI generation.
2. **Naming convention:** Cathedral uses `MI_Arch_Cath_SM_Cathedral_<Name>`,
   Atlantis uses `MI_Arch_Atl_<Suffix>`.
3. **ShadowDream tint mapping** (from `arch_toon_conversion.json` presets):
   - `marble/glass` → blue tint (roughness 0.08–0.25)
   - `rose` → pink tint (roughness 0.55)
   - `gold` → null tint, metallic 0.85
   - `stone/brick/trim` → null tint, roughness 0.7–0.85
   - `wood/worn` → null tint, roughness 0.6–0.7
4. **Bulk generation:** Run `convert_arch_to_toon.py` in UE editor with this spec.
5. **Pre-commit hook:** Will flag any `.uasset` hand-edits outside MCP/T3D workflow.