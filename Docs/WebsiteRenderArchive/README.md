# Website Render Archive

**Created:** July 31, 2026  
**Purpose:** Central archive for UE5.8 gameplay level renders used on the portfolio website

---

## Overview

This directory contains documentation and metadata for UE5.8 gameplay level renders that replace the old portfolio world placeholders on the website.

### Gameplay Levels (First 20 Minutes Vertical Slice)

| Level Name | Description | Website Section |
|------------|-------------|-----------------|
| **L_KaleidoNave** | Prologue · Bifrost Bridge | application-hub.html, recruiter-one-sheet.html |
| **L_MelusinaMorning** | Bedroom Interior | application-hub.html, recruiter-one-sheet.html |
| **ZenForestTest** | Combat Smoke-Test | application-hub.html, recruiter-one-sheet.html |
| **L_FallenMoon** | Recursive Expedition | application-hub.html, recruiter-one-sheet.html |

---

## Directory Structure

```
WebsiteRenderArchive/
├── README.md                          # This file
├── RENDER_CAPTURE_CHECKLIST.md        # BlackBoxAI capture checklist
└── metadata/
    └── render-specs.json              # Technical specifications
```

### Render Output Location

All captured renders go to:
```
my-site-deploy/generated/assets/landscape-loops/
```

---

## Sync Strategy (BlackBoxAI Coordination)

### File Naming Convention

All renders must follow this naming pattern:
```
{LevelName}_{RenderType}.png
```

**Render Types:**
- `beauty` — Final lookdev showcase (Substrate Toon active)
- `wireframe` — Wireframe overlay on beauty
- `materials` — Material ID breakdown view
- `pcg` — PCG debug visualization overlay
- `stats` — Performance stats panel screenshot

### Example Files

```
L_KaleidoNave_beauty.png
L_KaleidoNave_wireframe.png
L_KaleidoNave_materials.png
L_KaleidoNave_pcg.png
L_KaleidoNave_stats.png

L_MelusinaMorning_beauty.png
L_MelusinaMorning_wireframe.png
...

ZenForestTest_beauty.png
ZenForestTest_wireframe.png
...

L_FallenMoon_beauty.png
L_FallenMoon_wireframe.png
...
```

### Metadata Tags

Each render should include the following metadata (documented in render-specs.json):

| Tag | Value | Description |
|-----|-------|-------------|
| `engine` | UE5.8 | Unreal Engine version |
| `material` | M_Master_Toon_Universal | Substrate Toon master material |
| `resolution` | 1920x1080 | Render resolution |
| `format` | PNG | Lossless format |
| `colorspace` | sRGB | Color space |
| `level` | {LevelName} | Gameplay level name |
| `render_type` | {type} | beauty/wireframe/materials/pcg/stats |
| `pipeline` | Hybrid (Blender EEVEE → UE) | Pipeline documentation |

---

## Website Integration

### HTML Files to Update

1. **application-hub.html** (lines 169-194)
   - Section: "First 20 minutes · Four gameplay levels"
   - Replace placeholder images with new renders

2. **recruiter-one-sheet.html** (lines 114-131)
   - Section: "Environment art proof"
   - Replace placeholder images with new renders

### Image Path Mapping

| Old Placeholder | New Render |
|-----------------|------------|
| `WP_SpaceCathedral_terrain.png` | `L_KaleidoNave_beauty.png` |
| `WP_BaroqueGrotto_terrain.png` | `L_MelusinaMorning_beauty.png` |
| `WP_SakuraDream_terrain.png` | `ZenForestTest_beauty.png` |
| `WP_CosmicOrrery_terrain.png` | `L_FallenMoon_beauty.png` |

---

## Preservation Rules

**DO NOT MODIFY:**
- `generated/assets/character/` — All EEVEE/Melusina renders
- `generated/assets/material-loops/` — All material loop renders
- `generated/assets/nightshift/` — All material isolate views
- `generated/assets/melodia-game-ui/` — All UI textures

These demonstrate the hybrid pipeline and are current.

---

## Validation Checklist

After captures are complete, verify:

- [ ] All 20 renders exist (5 per level × 4 levels)
- [ ] File names match convention exactly
- [ ] Resolution is 1920×1080 for all renders
- [ ] Substrate Toon material is active in beauty renders
- [ ] Wireframe overlays are visible in wireframe renders
- [ ] Material IDs are color-coded in material renders
- [ ] PCG debug visualization is visible in PCG renders
- [ ] Stats panel shows triangle count, draw calls, FPS
- [ ] All renders committed to `my-site-deploy/generated/assets/landscape-loops/`

---

## References

- `BS_GodFile/Docs/WEBSITE_OVERHAUL_PLAN_2026-07-31.md` — Full overhaul plan
- `BS_GodFile/Docs/Handoffs/BLACKBOX_HANDOFF_2026-07-31.md` — BlackBoxAI instructions
- `BS_GodFile/Docs/WEBSITE_OVERHAUL_LEVEL_MAPPING_2026-07-31.md` — Level mapping details

---

**End of README**
