# Receipt — broken_texture_ref triage (Universal + Wool) — 2026-09-09

**Status:** TRIAGE (live Monolith expression read-back; **no** fix / save / recompile)  
**Date:** 2026-09-09  
**Follows:** [RECEIPT_WIRING_BATCH4_2026-09-09.md](RECEIPT_WIRING_BATCH4_2026-09-09.md)

## Verdict

These are **not** missing Cymatic wiring and mostly **not** orphan islands.

`validate_material` `broken_texture_ref` errors = expression `Texture` property is **`None`** on layered PBR TextureObjectParameter / TextureSample chains. Masters expose optional Layer A/B/C slots; unbound defaults trip the validator even while `is_compiled=true`.

Island overlap: Universal **2/33**, Wool **2/35** — almost all broken refs are **wired** into the graph.

## Universal (`M_Master_Toon_Universal`) — 33 errors

Unbound slots (sample → param | group), all `tex=None`:

| Slot | Group |
|------|-------|
| Albedo, HeightMap, MetallicMap, NormalMap, ORM, RoughnessMap | 03 Texture Layer A |
| LayerB_Albedo/Height/Metallic/Normal/ORM/Roughness | 04 Texture Layer B |
| LayerC_Albedo/Height/Metallic/Normal/ORM/Roughness | 05 Texture Layer C |
| DetailNormal | 07 Macro & Detail |
| TriplanarDetailMap | 02 Triplanar |
| MotifMask | 19 Magical (Henshin) |

Plus 3 bare `TextureSample_5/8/9` with `Texture=None` (no ParameterName — legacy samples).

## Wool (`M_Chorus_Wool_Master`) — 35 errors

Same Layer A/B/C / Detail / Triplanar / Motif pattern, plus:

| Slot | Group | Note |
|------|-------|------|
| ChladniPatternTexture | 03 Texture Layer A | Chladni path expects a pattern map; unbound on master |
| RoughnessMap / LayerC_RoughnessMap | Layer A/C | also flagged as TextureObjectParameter directly |

## Recommended owner actions (Ctrl+S; agents do not save)

1. **Do not bulk `fix_issues`** without review — empty optional slots may be intentional.
2. Bind defaults on **SHIP** masters only where a missing texture actually breaks lookdev (priority: Wool `ChladniPatternTexture` if fleece Chladni is dark; Layer A albedo/ORM if MI inherits None).
3. Prefer binding on **coat MIs** (`MI_ChoralSheep_Coat_PC*`) for sheep; leave Layer B/C empty if unused (consider static switch gate later to silence validator).
4. Investigate Universal/Wool `TextureSample_5/8/9` — rebind or delete if dead.

## Hard rules
- No Monolith `save_packages` / `recompile_material`
- Owner Ctrl+S only
