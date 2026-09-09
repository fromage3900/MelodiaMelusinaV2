# Receipt - SDF masters - 2026-09-09

**Status:** DOC-FINAL
**Date:** 2026-09-09
**Blessed parents:** /Game/EnvSandbox/Materials/Masters/M_Master_SDF_Toon, /Game/EnvSandbox/Materials/Masters/M_Toon_SDF
**Form:** Docs/sdf_parents_fix.json
**Index:** Docs/Materials/README.md

## Checklist
- [x] Blessed parents + dirty ornaments triaged
- [x] UtilityToolkit uasset MISSING; MF_SDF_UtilityToolkit_Core present
- [x] validate read-back (NO recompile)
- [x] QUARANTINE M_SDF_OrnamentLayer_Enhanced
- [ ] PR + main SHA

## validate / ship
| Asset | Result | Ship |
|-------|--------|------|
| M_Master_SDF_Toon | 0 errors; warnings | blessed OK |
| M_Toon_SDF | clean | blessed OK |
| M_SDF_GildedFiligree | clean | OK if intentional |
| M_SDF_GildedStucco | clean | OK if intentional |
| M_SDF_OrnamentLayer | 0 err / 2 warn | OK if intentional |
| M_SDF_TrebleClef_Ornament | clean | OK if intentional |
| M_SDF_OrnamentLayer_Enhanced | HARD missing_material_function x2 | QUARANTINE |

## Do-not-run
recompile_material; save_packages; ship Enhanced until fixed+owner Ctrl+S

## PR
Branch materials/sdf-masters-2026-09-09 off main (Melodia bot). Exclude Enhanced.
