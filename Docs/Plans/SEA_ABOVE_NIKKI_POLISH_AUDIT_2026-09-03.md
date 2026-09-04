# Sea Above — Infinity Nikki Lens Polish Audit (2026-09-03)

Goal: is the level *polished* the way a Nikki-form world must be — every asset
materialed, graded, and read as one dream? Audit ran live against
LV_SeaAbove_Prototype (editor :9316) after the golden-beat wiring.

## What's already AAA-clean

- **All 136 SA_HM placements materialed.** 84 MI_SeaAbove_CoralSkin, 40
  MI_SeaAbove_Sand, 6 MI_Jelly_Arms; the 6 CathedralHalo BP jellies resolve
  MI_Jelly_Bell (bell material via BP default — correct, not unassigned).
- **Palace kitbash on Copernicus cymatic MIs** (FrostBloom 10, PearlWeave 10,
  CavernWeave 9) — real authored cymatic surfaces, form-correct.
- **Zero default/engine materials** on placed actors — no greybox leaking.

## The Nikki gap: zero post-processing in the level

**No PostProcessVolume in LV_SeaAbove_Prototype.** The dream-water world renders
raw. Yet the project has a complete, authored, profiled lookdev post tier:

| Profile family | GameplayStandard | Narrative | PortfolioHero |
|---|---|---|---|
| StorybookOutline | MI_StorybookOutline_GameplayStandard | MI_StorybookOutline_Narrative | MI_StorybookOutline_PortfolioHero |
| MeluColorGrade | MI_MeluColorGrade_GameplayStandard | MI_MeluColorGrade_Narrative | MI_MeluColorGrade_PortfolioHero |
| MelodiaInk | MI_MelodiaInk_GameplayStandard | MI_MelodiaInk_Narrative | MI_MelodiaInk_PortfolioHero |
| StarryNight (sky overlay) | MI_StarryNight_Gameplay | (Narrative) | MI_StarryNight_Hero |

Paths (verified live):
- `EnvSandbox/Materials/PostProcess/` — MI_PP_StorybookOutline + Candidates/Profiles/*
- `Melodia/_PROJECT/04_Materials/PostProcess/Candidates/Profiles/` — grade+ink profiles
- `EnvSandbox/Materials/SDF/Instances/MI_PP_MeluColorGrade`

Storybook outline IS the Nikki signature (soft line on silhouettes, dream bloom).
With a 43%-submerged canyon sea + palace on water + drowned cathedral tiers, the
grade choice is a feel decision, not a technical one.

## Recommended Nikki-grade stack (single PPV, unbounded, priority blend)

1. `MI_StorybookOutline_GameplayStandard` (or `_Narrative` for softer) as the
   base post blendable
2. `MI_MeluColorGrade_GameplayStandard` layered for the water-teal grade
3. Optional `MI_StarryNight_*` overlay if the sky reads flat under UltraDynamicSky

## The only real defect found

- Earlier concern (6 unassigned halo pieces) was **false** — BP jellies correctly
  render with MI_Jelly_Bell via their authored defaults. No fix needed.

## Next step (one at a time)
- Add ONE unbounded PPV to LV_SeaAbove_Prototype with the StorybookOutline +
  MeluColorGrade standard profiles as blendables; verify it persists via reload;
  then owner picks Narrative/Hero profiles by eye in the viewport.

## Evidence
- Live audit 2026-09-03: material census on all 136 SA_HM + 29 SM_ATL actors,
  PPV actor scan (0 in level), 23 lookdev MI paths verified via asset registry.