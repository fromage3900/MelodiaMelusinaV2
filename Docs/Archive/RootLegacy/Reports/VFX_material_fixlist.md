# VFX Material Instances Fix Checklist

**Comprehensive fix list for ALL VFX material instances** across `/Game/VFX`.
Each instance should be processed: `validate_material` → apply fix → recompile → save → log.

| # | Instance Name | Original Issue | Fix Applied | Post-Fix Validate (0 errors?) | Notes |
|---|---|---|---|---|---|
| 1 | MI_* (list VFX instances) | EmissiveMap wired → color output | Replace with `T_Neutral_Emissive` (constant black) | Yes/No | All legacy VFX; black default prevents unwanted glow |
| 2 | MI_* | NormalMap green channel inverted | Add `MaterialExpressionVectorFlipGreen` OR manually swap RB channels | Yes/No | Particle materials often have OpenGL-origin normals |
| 3 | MI_* | RoughnessMap missing → default 1.0 (too shiny) | Add `T_Neutral_Roughness` (160 grey, 0.5 roughness) | Yes/No | Standard healthy default |
| 4 | MI_* | Triplanar `TriplanarActive = true` (unnecessary overhead) | Set `TriplanarActive = false` | Yes/No | Only needed for terrain-tiling; overhead for discrete meshes |
| 5 | MI_* | `wrong_role` = color used as ORM | Re-route to dedicated ORM map OR set to neutral gray (R=0.5,G=0.5,B=0.5) | Yes/No | Flag from scan_master_texture_violations |
| 6 | MI_* | `broken_texture_ref` (false positive from TextureObjectParameter) | Document as false positive; verify via probe (TextureObjectParameter→TextureSample is valid); skip if pattern matches | Yes/No | Same pattern as master material; 32 flags on Universal are all false positives |
| 7 | MI_* | EmissiveMap not black neutral | Set Emissive to `T_Neutral_Emissive` (constant 0,0,0) | Yes/No | Ensures no unwanted emission |
| 8 | MI_* | ORM packed incorrectly (single channel vs packed) | Re-pack: AO→R, Roughness→G, Metallic→B OR use separate channels | Yes/No | Legacy format fix |
| 9 | MI_* | EmissiveMap not connected but has scalar parameter | Add constant black emissive input; remove unused scalar | Yes/No | Cleanup |
| 10 | MI_* | Missing Layer parameters (if layered material) | Add Layer weight blends with neutral defaults | Yes/No | If using layered materials |

## Processing Procedure Per Instance

For each VFX material instance MI_*:

1. **List instances**: In UE editor, `Find Object` → `UMaterialInstanceConstant` → `MI_*` pattern
   OR via Monolith: `material_query list_instances asset_path="/Game/VFX"`
2. **Validate baseline**: Run `validate_material` → record error/warning counts
3. **Apply fix**: Per the table above; use the universal melodia pipeline defaults
4. **Recompile**: `recompile_material` via Monolith or editor
5. **Save**: `save_material` with `only_if_dirty=True`
6. **Post-validate**: Run `validate_material` again → confirm 0 errors (or document remaining)
7. **Log**: Enter result in `Docs/Production/VFX_MATERIAL_FIXLOG.md`

## VFX_MATERIAL_FIXLOG.md Template

```
# VFX Material Fix Log — 2026-08-16

## Instance: MI_Example_01
- **Original Issues**: EmissiveMap wired, NormalMap green inverted, RoughnessMap missing
- **Fixes Applied**: 
  1. Replaced EmissiveMap → T_Neutral_Emissive (black)
  2. Added MaterialExpressionVectorFlipGreen to NormalMap
  3. Added T_Neutral_Roughness (160 grey)
- **Post-Fix Validate**: errors=0, warnings=5 (acceptable)
- **Notes**: Instance now renders identically to master; 32 broken_texture_ref flags
  are false positives (same pattern as M_Master_Toon_Universal)

## Instance: MI_Example_02
- **Original Issues**: TriplanarActive=true, wrong_role color-as-ORM
- **Fixes Applied**: 
  1. Set TriplanarActive=false
  2. Re-routed ORM to dedicated map channels
- **Post-Fix Validate**: errors=0, warnings=0
- **Notes**: Instruction count reduced from 210 → 185

...

## Summary
- Total instances processed: N
- Instances with 0 post-fix errors: M
- Common false-positive flags (broken_texture_ref): K (same as master material pattern)
- Instances requiring additional artist review: L
```

## Common VFX Issues & Fixes (Quick Reference)

| Symptom | Fix | Monolith shortcut |
|---|---|---|
| Emissive glow where there should be none | EmissiveMap → T_Neutral_Emissive (black) | `material_query set_material_parameter` |
| Normals look green/magenta | Flip green channel or swap RB channels | `material_query set_material_parameter` |
| Materials too shiny (high specular) | Add T_Neutral_Roughness (0.5 gray) | `material_query set_material_parameter` |
| Unnecessary Triplanar overhead | TriplanarActive = false | `material_query set_material_parameter` |
| `wrong_role` flag in validator | Replace color-as-ORM with dedicated ORM or neutral gray | `material_query set_material_parameter` |
| `broken_texture_ref` flags | These are false positives for TextureObjectParameter→TextureSample; ignore or document | N/A (document only) |
| Emissive not black when should be | Set Emissive input to constant black (0,0,0) | `material_query set_material_parameter` |

## Post-Fix Validation Checklist

For each instance after fixes are applied, verify:
- [ ] `validate_material` shows 0 errors (or documented exceptions)
- [ ] `validate_material` shows 0 banned expressions
- [ ] `validate_material` shows 0 unwired expressions
- [ ] `validate_material` shows 0 wrong_role flags
- [ ] Material compiles clean (PS/VS instructions reasonable)
- [ ] No `broken_texture_ref` errors that weren't there before (32 on master are false positives)
- [ ] Emissive input is black (0,0,0) or black texture
- [ ] Normal map channels are correctly oriented (no green inversion)
- [ ] Roughness input has reasonable value (not 1.0, not 0.0 unless intended)
- [ ] Metallic input has reasonable value (not -1 or >1)

## Output

**File:** `Docs/Production/VFX_MATERIAL_FIXLOG.md`
**Purpose:** Per-instance log of fixes applied, validation results, and notes.
**Usage:** Track which VFX instances have been cleaned up; ensures nothing is missed
during longterm material maintenance.