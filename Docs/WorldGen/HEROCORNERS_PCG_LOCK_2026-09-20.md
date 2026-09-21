# HeroCorners PCG Lock — L_MelusinaMorning (2026-09-20)

Do **not** re-duplicate `PCG_WorldCompiler_PointField` onto WestRim/EastBank/NorthDress.
PointField requires the morning rainbow DataTable and will look empty/wrong on other corners.

## Locked primary graphs

| Corner | Volume | Graph asset | Source kit |
|--------|--------|-------------|------------|
| MeadowChorus | `WC_morning_rainbow_bloom_Field` | `/Game/Melodia/WorldCompiler/PCG_WorldCompiler_PointField` | KEEP (rainbow DT) |
| WestRim | `WC_HeroCorner_WestRim_PCG` | `/Game/Melodia/WorldCompiler/HeroCorners/PCG_HeroCorner_WestRim` | from `PCG_Nikki_PhyllotaxisGarden_Walkable` (PCGEx Fiblat) |
| EastBank | `WC_HeroCorner_EastBank_PCG` | `/Game/Melodia/WorldCompiler/HeroCorners/PCG_HeroCorner_EastBank` | from `PCG_MeadowBloom` |
| NorthDress | `WC_HeroCorner_NorthDress_PCG` | `/Game/Melodia/WorldCompiler/HeroCorners/PCG_HeroCorner_NorthDress` | from `PCG_OrnamentalDetail` |

## Companions

- `WC_HeroCorner_WestRim_PCG_Companion` → `PCG_RockScatter`
- `WC_HeroCorner_EastBank_PCG_Companion` → `PCG_PathScatter`
- `WC_HeroCorner_NorthDress_PCG_Companion` → `PCG_Universal_RockScatter`

## Cams

- `WC_HeroCorner_MeadowChorus_Cam`
- `WC_HeroCorner_WestRim_Cam`
- `WC_HeroCorner_EastBank_Cam`
- `WC_HeroCorner_NorthDress_Cam`

## Materials

- Flowers: `MI_RainbowSpeedTree_B0–B6` → `M_MelodiaPlant_Wind_NikkiToon` (DreamGrade+Rim+Sparkle+Pearl)
- Do not parent SpeedTree bands to bare `M_Master_Toon_Universal` (drops SharedBend)

## Skip for morning meadow

Musical PCGex heroes: ArpeggioBridge, XylophoneTrail, ResonanceCathedral, CrystalHarpGrove.

## Receipts

- `Saved/Audit/hero_corners_plan_2026-09-20.json`
- `Saved/Audit/hero_corners_pcg_integration_2026-09-20.json`
- `Saved/Audit/scale_fix_2026-09-20.json`

