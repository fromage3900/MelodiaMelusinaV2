# L3 Morph Receipt — ZenLantern V2

Date: 2026-09-24T03:46:24 (America/Toronto)

## Summary
Living morph layer on a **joined duplicate** of `zenlantern_V2` + eave charms.
Paint original + L1L2 charmfix source objects kept intact (Save-As workflow).

## Shape keys
| Key | Intent | Max delta (m) |
|---|---|---|
| `SK_FlameBreath` | Fire-box radial expand ~+8% + slight lift | 0.14017 |
| `SK_RoofLift` | Roof tier +15 cm Z (ramped) | 0.19000 |
| `SK_CharmSway_L` | Left charms tilt -12° about eave pivot | 0.46197 |
| `SK_CharmSway_R` | Right charms tilt +12° about eave pivot | 0.46175 |
| `SK_DawnDusk` | Subtle dusk bias (roof flare / fire soft squash) | 0.02619 |

## Paths
- Working blend: `C:\EnvironmentPortfolio\BS_GodFile\Saved\KimiWork\HandpaintPrep_2026-09-23\02_ZenLantern\ZenLantern_V2_L3_morphs.blend`
- Morph FBX: `C:\EnvironmentPortfolio\BS_GodFile\Saved\KimiWork\HandpaintPrep_2026-09-23\02_ZenLantern\substance\meshes\ZenLantern_V2_L3_morphs.fbx`
- JSON: `C:\EnvironmentPortfolio\BS_GodFile\Saved\KimiWork\HandpaintPrep_2026-09-23\02_ZenLantern\L3_morph_report.json`
- Source (untouched via Save-As): `ZenLantern_V2_L1L2_vcol_charmfix.blend`

## Mesh
- Export object: `zenlantern_V2_L3`
- Verts / faces: **15670** / **15572**
- Charms joined: **10**

## UE drivers (plan — not wired this pass)
| Key | Suggested driver |
|---|---|
| SK_FlameBreath | BeatPulse |
| SK_RoofLift | BeatPhase crest one-shot |
| SK_CharmSway_L/R | BassIntensity |
| SK_DawnDusk | W_Melodia_FadeDayNight |

## Gates
- G2 morph FBX authored: **YES** (UE re-import proof still owner session)
- L4 shine / L5 evidence: **NOT this pass**
- Painter SMS / real `.spsm`: still owner-gated (M2)

## Hard-rule compliance
- Paint original not mutated
- No Monolith save_packages / recompile_material
- Melodia naming only
