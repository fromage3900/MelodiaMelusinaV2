# PBR Orphan Instance Spec — 2026-08-30

**Source:** `Saved/Audit/material_catalog_consolidated_2026-08-31.json` (12 complete PBR sets, 0 instances)
**Mode:** Offline disk scan. No `.uasset` writes. Editor Monolith pass required to create MIs.

---

## Summary

| Category | Count | Action |
|---|---|---|
| Truly orphaned (textures exist, no MI) | 4 | Propose MI spec |
| Has MI but name mismatch | 1 | Flag for owner review |
| Has MI (covered) | 7 | No action |

---

## Block 1 — Truly Orphaned Sets (4 items)

These 4 texture sets have complete PBR maps on disk but **zero material instances** consuming them.

### 1. ZenTrim_CrackedToHell

| Field | Value |
|---|---|
| Texture location | `Content/Textures/ZenTrim_CrackedToHell_*` (8 maps: Alpha, BaseColor, Displacement, Emission, Metallic, Normal, Roughness, ORM) |
| Proposed MI path | `Content/EnvSandbox/Materials/Instances/Environment/Stylized/MI_ZenTrim_CrackedToHell.uasset` |
| Parent master | `M_Master_Toon_Universal` (safe default; if a trimsheet-specific master exists, use that) |
| Tiling scale | 1.0 (trimsheet UVs drive tiling) |
| Roughness | 0.85 (cracked stone/rock heuristic) |
| NormalAssign | Standard tangent-space normal (not OpenGL) |
| Notes | 8-map set with ORM packed. Displacement + Emission suggest animated or glowing cracked surface. |

### 2. basetrim

| Field | Value |
|---|---|
| Texture location | `Content/Melodia/_PROJECT/04_Materials/Textures/basetrim_*` (7 maps: Alpha, BaseColor, Displacement, Emission, Metallic, Normal, Roughness) |
| Proposed MI path | `Content/EnvSandbox/Materials/Instances/Environment/Stylized/MI_basetrim.uasset` |
| Parent master | `M_Master_Toon_Universal` |
| Tiling scale | 1.0 |
| Roughness | 0.80 (base trim, likely stone/concrete) |
| NormalAssign | Standard |
| Notes | 7-map set. "Base" suggests foundational trim material. Displacement + Emission present. |

### 3. concretetrim

| Field | Value |
|---|---|
| Texture location | `Content/Melodia/_PROJECT/04_Materials/Textures/Textures/concretetrim_*` (7 maps: Alpha, BaseColor, Displacement, Emission, Metallic, Normal, Roughness) |
| Proposed MI path | `Content/EnvSandbox/Materials/Instances/Environment/Stylized/MI_concretetrim.uasset` |
| Parent master | `M_Master_Toon_Universal` |
| Tiling scale | 1.0 |
| Roughness | 0.78 (concrete heuristic) |
| NormalAssign | Standard |
| Notes | 7-map set. Concrete-specific trim. |

### 4. landscape_grass

| Field | Value |
|---|---|
| Texture location | `Content/Melodia/_PROJECT/04_Materials/Textures/Textures/grass/landscape_grass_*` (4 maps: albedo, height, normal, orm) |
| Proposed MI path | `Content/EnvSandbox/Materials/Instances/Landscape/MI_Landscape_Grass.uasset` |
| Parent master | `M_Master_Toon_Landscape_HeightBlend` (landscape height-blend master) |
| Tiling scale | 2.0 (grass needs high tiling; adjust per world scale) |
| Roughness | 0.90 (grass/foliage heuristic) |
| NormalAssign | Standard |
| Notes | 4-map set with ORM packed (Occlusion/Roughness/Metallic). Height map for landscape blending. |

---

## Block 2 — Name Mismatch (1 item)

| Texture Set | Existing MI | Issue |
|---|---|---|
| `ZenTrim_FlowersLIttleBit` | `MI_ZenTrim_FlowersLittle` | Stem name has `LIttleBit` (capital L, capital I), MI name has `Little`. Likely the same asset but naming inconsistency. |

**Action:** Owner to confirm if `MI_ZenTrim_FlowersLittle` consumes `ZenTrim_FlowersLIttleBit` textures. If yes, no new MI needed — just a naming note. If no, propose `MI_ZenTrim_FlowersLIttleBit` under `Environment/Stylized/`.

---

## Block 3 — Already Covered (7 items)

These sets have existing MIs. No action required.

| Texture Set | Existing MI | Location |
|---|---|---|
| T_FloralBrickGrayScale | MI_Melusina_FloralBrickGrayScale | `Instances/Melusina/` |
| T_FloralBrickGrayScale | MI_M_Master_Toon_Universal_FloralBrickGrayScale | `Instances/MelusinaReal/M_Master_Toon_Universal/` |
| ZenTrim_Base4K | MI_ZenTrim_Base4K | `Instances/Environment/Stylized/` |
| ZenTrim_ColourShift | MI_ZenTrim_ColourShift | `Instances/Environment/Stylized/` |
| ZenTrim_FlowersLOTS | MI_ZenTrim_FlowersLots | `Instances/Environment/Stylized/` |
| ZenTrim_FlowersMid | MI_ZenTrim_FlowersMid | `Instances/Environment/Stylized/` |
| ZenTrim_Wet | MI_ZenTrim_Wet | `Instances/Environment/Stylized/` |
| landscapegrayscale | MI_Melusina_LandscapeGrayscale | `Instances/Melusina/` |
| landscapegrayscale | MI_M_Master_Toon_Landscape_HeightBlend_LandscapeGrayscale | `Instances/MelusinaReal/M_Master_Toon_Landscape_HeightBlend/` |

---

## Pre-Execution Checklist

1. **Verify parent masters exist** — confirm `M_Master_Toon_Universal` and `M_Master_Toon_Landscape_HeightBlend` are the correct parents for these texture sets. If a trimsheet-specific master exists (e.g., `M_Master_ZenTrim`), prefer it.
2. **Check texture dimensions** — confirm all textures are 4K (or note if mixed resolution affects tiling).
3. **Dry-run** — execute with `--what-if` flag before `--go`:
   ```bash
   python Tools/create_mi_batch.py --map Docs/Plans/PBR_ORPHAN_MI_MAP_2026-08-30.json --what-if
   ```
4. **Backup** — commit current state before MI creation:
   ```bash
   git add -A && git commit -m "chore(materials): pre-MI-creation checkpoint"
   ```

---

## Safety Notes

- **Never hand-edit .uasset** — all MI creation via Monolith MCP or T3D command
- Spec only — do not execute without owner sign-off
- After creation, run `melodia_material_audit` to confirm all 4 new MIs compile clean
- If a texture set is found to be a duplicate of an existing one, flag for deletion instead of MI creation