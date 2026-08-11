# Universal Niagara Portfolio System

## Purpose

This is the reusable VFX layer for the Universal Environment Production Platform. It supports portfolio environment shots, look-dev captures, material passports, biome tests, and cinematic breakdowns without requiring edits to `L_SakuraPath`.

The Sakura Dream kit remains valid, but this universal layer is broader: fog, dust, water mist, fireflies, wind motion, rainfall accents, botanical sparkle, and magical ground atmosphere.

## Current Library

| Family | Systems | Purpose |
| --- | --- | --- |
| Ambient | `NS_FairyDust`, `NS_ConstellationTwinkle`, `NS_EmberMotes` | Existing general atmosphere and magical readability. |
| Universal | `NS_Uni_MistSheet`, `NS_Uni_Fireflies`, `NS_Uni_LeafDrift`, `NS_Uni_WaterMist`, `NS_Uni_DustShafts`, `NS_Uni_PollenSparkle`, `NS_Uni_RainRipples`, `NS_Uni_GroundWisps` | Portfolio-ready environment support for many biomes and art directions. |
| Magical | `NS_MagicalHenshinBurst`, `NS_MagicTrail` | Cinematic accents, reveal moments, stylized reel beats. |
| Sakura | `NS_Sakura*` | Sakura-specific kit. Allowed as reusable material/VFX infrastructure, but not used to art-direct the Sakura level here. |

## Professional VFX Review

The existing library was already structurally clean before expansion. The latest Unreal build created the 8 universal `NS_Uni_*` systems with no Niagara build errors. All 19 authored systems are now structurally ready and require editor/PIE visual tuning before portfolio capture.

Portfolio quality depends less on raw particle count and more on control, composition support, and readability:

| System | Portfolio Use | Key Risk | Acceptance |
| --- | --- | --- | --- |
| `NS_Uni_MistSheet` | Depth layering for cliffs, ponds, forest gates, ruins | Fog can flatten material contrast | Thin layers, readable silhouettes, no full-screen haze. |
| `NS_Uni_Fireflies` | Night forest, magical grove, small-scale wonder | Random sparkle can look cheap | Low density, warm/cool palette match, visible pulse rhythm. |
| `NS_Uni_LeafDrift` | Generic wind motion for forest, autumn, zen, ruin shots | Can conflict with Sakura petals | Non-pink leaf palette by default; Sakura remains its own lane. |
| `NS_Uni_WaterMist` | Waterfalls, pond edge, river contact, shoreline | Overdraw and bright clipping | Soft opacity, source-localized, no bloom blowout. |
| `NS_Uni_DustShafts` | Interiors, shrines, temples, baroque/cathedral spaces | Beams can hide trimsheet detail | Directional shafts with clear negative space. |
| `NS_Uni_PollenSparkle` | Meadows, flower fields, botanical hero reveals | Too similar to FairyDust | Smaller, warmer, biologic motion; not magical unless intended. |
| `NS_Uni_RainRipples` | Wet material demos, water plates, rainy reels | Needs surface contact believability | Short-lived rings, bounded spawn area, material wetness pairing. |
| `NS_Uni_GroundWisps` | Forest floor, shrine, graveyard, ruin atmosphere | Can feel gamey if too dense | Low, slow, transparent, composition-supporting. |

## Material Integration

The VFX systems should support material proof, not cover it. The pairing rules:

- Water systems pair with `MI_GrandWater_*` and wetness-enabled universal materials.
- Mist and dust systems pair with landscape, trimsheet, stone, and baroque surface reviews.
- Fireflies, pollen, FairyDust, and ground wisps pair with Nikki/Magical parameter lanes.
- Leaf drift is the generic wind-motion lane; Sakura petal drift stays in the Sakura kit.

## Execution

Disk-only manifest:

```text
python Content/Python/universal_niagara_manifest.py
```

Editor build:

```text
py Content/Python/setup_niagara_library.py
```

Optional showcase:

```text
py Content/Python/setup_niagara_library.py --showcase
```

Generated manifest:

```text
Saved/Portfolio/VFX/universal_niagara_manifest.json
```

## Readiness Gates

| Gate | Requirement |
| --- | --- |
| Structural | System asset exists, compiles, appears in `niagara_library_build.json`. |
| Control | `User.*` params are named consistently and can be driven by Sequencer or Blueprint. |
| Visual | No over-bright sprites, no full-screen haze, no noisy shimmer. |
| Material Support | VFX does not hide parallax, roughness, trimsheet wear, or water normals. |
| Portfolio | Each system has a thumbnail or short reel clip in a neutral `L_Template`/VFX showcase context. |

## Next Actions

1. Open the Niagara editor and tune spawn bounds, color, opacity, lifetime, and `User.*` parameters for the 8 `NS_Uni_*` systems.
2. Capture a universal VFX showcase plate separate from Sakura.
3. Run `universal_niagara_manifest.py` after tuning to keep readiness metadata current.
4. Add VFX entries to the portfolio package schema after the first successful capture pass.
5. Keep Sakura-specific VFX tuning separate from generic universal showcase tuning.


