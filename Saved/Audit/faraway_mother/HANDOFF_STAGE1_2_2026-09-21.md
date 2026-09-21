# Faraway Mother — Stage 1+2 Handoff (careful measurements)
Date: 2026-09-21
Level: `/Game/EnvSandbox/Monoliths/FarawayMother/Prototype/LV_FarawayMother_Prototype`
**Never touch** `L_MelusinaMorning`.

## Contract
- Authority: `Saved/Audit/faraway_mother/STAGING_CONTRACT_v1.md` (revised: **no new Landscape**; height-aware / manifest Z)
- Seed: `20260829`
- Manifest: `C:\EnvironmentPortfolio\BS_GodFile\Saved\Audit\faraway_mother_height_aware_pcg.json`
- Manifest SHA-256: `239ff4f41e63e326fceb45a09dbf0c5b05b8bf88fa4d327d177ec664f5bb75ea`

## Stage 1 — layout (verified)
Receipt: `Saved/Audit/faraway_mother_stage1_2026-09-21.json`

| Field | Value |
|------|--------|
| reload_ok | `True` |
| actor_count (post-reload) | `10` |
| ground_present | `True` |
| player_present | `True` |
| placed | `7/7` |
| missing | `[]` |
| Landscape created | **no** |
| Morning untouched | `True` |
| PCGWorldActor | `absent — note for assembly pass` |
| Raycast | Visibility API failed (DrawDebugTrace vs TraceChannel); **Z = manifest final_z fallback** (logged) |

### Per-instance measurements (post-reload Z re-read)

| ID | Mesh | Material (at place) | XY (cm) | Z final (cm) | Yaw | Scale X/Y/Z | DataLayer |
|----|------|---------------------|---------|--------------|-----|-------------|-----------|
| `FM_Ridge_HeadSilhouette_01` | `SM_Cathedral_Spire` | `MI_Mother_Mantle` | (0, 9000) | 38.95 | 0 | 3.5/2.2/2.0 | `DL_FarawayMother_Fabric` |
| `FM_Ridge_Fabric_02` | `SM_ATL_Palace_ArchesA` | `MI_Mother_Gown` | (1200, 5500) | 24.82 | 18 | 4.2/2.8/1.15 | `DL_FarawayMother_Fabric` |
| `FM_Hair_Cascade_03` | `SM_Cathedral_EscherWaterfall` | `MI_Mother_Veil` | (-900, 6200) | 62.07 | -22 | 1.6/4.5/1.0 | `DL_FarawayMother_Fabric` |
| `FM_Ridge_Fabric_04` | `SM_ATL_Palace_ArchA` | `MI_Mother_Gown` | (-2600, 1800) | 22.98 | 35 | 0.95/0.95/0.75 | `DL_FarawayMother_Fabric` |
| `FM_Valley_Shoulder_05` | `SM_Coral_ReefCluster` | `MI_Mother_Corset` | (0, -800) | -45.49 | -8 | 5.2/5.2/0.32 | `DL_FarawayMother_Fabric` |
| `FM_Valley_Torso_06` | `SM_Kelp_Cluster` | `MI_Mother_Corset` | (400, -4200) | -92.29 | 12 | 5.8/4.2/0.28 | `DL_FarawayMother_Fabric` |
| `FM_Haze_Limbs_07` | `SM_Cathedral_Tower` | `MI_Copernicus_FarawayMoonChiffon` | (0, -7800) | 167.96 | 45 | 2.8/2.8/1.6 | `DL_FarawayMother_Haze` |

Z re-read dict: `{'FM_Ridge_HeadSilhouette_01': 38.95, 'FM_Ridge_Fabric_02': 24.82, 'FM_Hair_Cascade_03': 62.07, 'FM_Ridge_Fabric_04': 22.98, 'FM_Valley_Shoulder_05': -45.49, 'FM_Valley_Torso_06': -92.29, 'FM_Haze_Limbs_07': 167.96}`

## Stage 2 — materials (executed)
Receipt: `Saved/Audit/faraway_mother_stage2_mi_2026-09-21.json`

| Field | Value |
|------|--------|
| ok | `True` |
| parents | Nikki / Universal / Universal_Alpha (EnvSandbox Masters) |
| MPC policy | consume-only (`MPC_Cymatics_Driver` not written) |
| level_saved | `True` |

### Suite wiring
- **MI_Mother_Mantle** from `FarawayNightVelvet` | NikkiPearlSheen=0.4 NikkiPastelStrength=0.55 | status=reused
- **MI_Mother_Gown** from `FarawayCelestialSilk` | NikkiPearlSheen=0.55 NikkiPastelStrength=0.65 | status=reused
- **MI_Mother_Veil** from `FarawayAquaLace` | NikkiPearlSheen=0.45 NikkiPastelStrength=0.6 | status=reused
- **MI_Mother_Corset** from `FarawayGildedRidge` | NikkiPearlSheen=0.35 NikkiPastelStrength=0.5 | status=reused

### Actor assignments
- `FM_Ridge_HeadSilhouette_01` -> `MI_Mother_Mantle` ok=True
- `FM_Ridge_Fabric_02` -> `MI_Mother_Gown` ok=True
- `FM_Hair_Cascade_03` -> `MI_Mother_Veil` ok=True
- `FM_Ridge_Fabric_04` -> `MI_Mother_Gown` ok=True
- `FM_Valley_Shoulder_05` -> `MI_Mother_Corset` ok=True
- `FM_Valley_Torso_06` -> `MI_Mother_Corset` ok=True
- `FM_Haze_Limbs_07` -> `uses_MoonChiffon` ok=True

### Known gap — texture parameter binds
Textures **imported** under `/Game/EnvSandbox/Textures/Copernicus/Faraway/<Family>/T_Cymatic_*` but Stage 2 reported **bound=false** on map slots (master param names did not match guesses). Scalars (`NikkiPearlSheen`, `NikkiPastelStrength`) **did** apply.
Stage 2b script ready: `Content/Python/faraway_mother_stage2b_texbind_2026-09-21.py` (receipt not on disk at closeout) — run before beauty if surfaces still read flat.
AO maps: several families lack `_AO.png` (expected missing_png).

## Owners going forward
| Lane | Owner | Next |
|------|--------|------|
| Layout / height-aware PCG / WP save | Grok Bot | Fix raycast TraceChannel; PCGWorldActor assembly; Stage 3 density |
| MI texture bind + lookdev | Material Artist | Exec Stage 2b bind pass; verify AlabasterDrape |
| Go/no-go | User | Viewport read of prototype |

## Do not
- Mutate `L_MelusinaMorning`
- Create Landscape without explicit owner green
- Mass destroy+save
- Write `MPC_Cymatics_Driver`
- Run `asset_fixup_redirectors`
- Treat `__ExternalActors__` as commit source of truth — evidence is Saved/Audit JSON

## Evidence paths
- `Saved/Audit/faraway_mother/STAGING_CONTRACT_v1.md`
- `Saved/Audit/faraway_mother_stage1_2026-09-21.json`
- `Saved/Audit/faraway_mother_stage2_mi_2026-09-21.json`
- `Content/Python/faraway_mother_stage2_mi_2026-09-21.py`
- `Content/Python/faraway_mother_stage2b_texbind_2026-09-21.py`
- `Saved/Audit/copernicus_cymatic/Faraway*/`
