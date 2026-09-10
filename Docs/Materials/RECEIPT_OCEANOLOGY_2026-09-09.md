# Receipt - Oceanology Melodia material - 2026-09-09

**Status:** DOC-FINAL
**Date:** 2026-09-09
**Authority:** /Game/EnvSandbox/Materials/Masters/M_Water_Oceanology_Melodia
**Inst:** /Game/EnvSandbox/Materials/Masters/M_Water_Oceanology_Melodia_Inst (parent = Melodia master)
**Hero MI:** /Game/EnvSandbox/Materials/Instances/Oceanology/MI_Oceanology_Melodia_Hero
**Index:** Docs/Materials/README.md

## Checklist
- [x] Plugin enable / EngineVersion trap noted
- [x] Melodia-owned knobs listed
- [x] Cymatics on this master: none (MPC/bridge elsewhere)
- [x] validate_material read-back (2026-09-09, NO recompile)
- [ ] PIE smoke (owner)
- [ ] Owner Ctrl+S if intentional graph edits (Monolith save_packages FORBIDDEN)
- [ ] PR + main SHA

## validate_material (NO recompile)
- Melodia master: 0 errors; island/unused warnings (~11)
- Melodia Inst: loads (SLW); parent = Melodia master; validate MIC quirk may false-fail
- **Hero MI parent quirk:** /Oceanology_Plugin/.../SingleLayerWater/M_Oceanology_Inst (plugin), NOT Melodia master

## Cymatics
none / MPC-only on Melodia ocean master

## Do-not-run
Monolith recompile_material; Monolith save_packages; plugin master edits; V9/V10 OceanPreview as authority

## PR
Branch materials/oceanology-2026-09-09 off main (Melodia bot). Docs-only unless owner Ctrl+S intentional uassets.
