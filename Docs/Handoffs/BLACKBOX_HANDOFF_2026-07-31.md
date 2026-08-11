ere should bea lowpoly retpod version of the corss and sculpt; # Blackbox AI Handoff — Render Capture & Asset Mapping

**Session Date:** July 31, 2026  
**Handoff Type:** UE5.8 Render Capture & Prop Mapping  
**Status:** Website deployed, UE5 level renders pending

---

## Executive Summary

This document provides detailed instructions for capturing UE5.8 gameplay level renders and mapping props to their respective levels. The website has been updated to reference the actual UE5.8 gameplay levels, but currently uses placeholder renders from the old portfolio worlds. Your task is to capture the real gameplay level renders and map props to their levels.

**Key Objective:** Replace placeholder renders with actual UE5.8 gameplay level renders and create prop-to-level mapping documentation.

---

## Current State

### Website Status
- ✅ Level mapping updated to reflect actual UE5.8 gameplay levels
- ✅ All EEVEE/Melusina renders preserved (DO NOT TOUCH)
- ✅ Hybrid pipeline documentation added (Blender EEVEE → UE Substrate Toon)
- ⚠️ Landscape loop renders — Using portfolio world renders as temporary placeholders
- ⚠️ Prop renders — Not yet mapped to specific gameplay levels

### Level Mapping (Updated)

| Old Portfolio World | New UE Level | Description |
|---------------------|--------------|-------------|
| Sakura Dream | **L_KaleidoNave** | Prologue · Bifrost Bridge |
| Space Cathedral | **L_MelusinaMorning** | Bedroom Interior |
| Cosmic Orrery | **ZenForestTest** | Combat Smoke-Test |
| Baroque Grotto | **L_FallenMoon** | Recursive Expedition |

---

## Priority 1: Capture Gameplay Level Renders

### Task Overview

Use UE5.8 Editor to capture beauty renders of the four actual gameplay levels. Each level needs multiple render types for comprehensive portfolio documentation.

### Levels to Capture

#### 1. L_KaleidoNave (Prologue/Bifrost Bridge)

**Level Description:**
- Short, controlled prologue/cutscene on floating bifrost-like bridge
- Establishes emotional Dissonance and Sir Melodious's distance/absence
- Open sky environment with floating bridge structure

**Renders Required:**

| Render Type | Purpose | Technical Specs |
|-------------|---------|-----------------|
| **Beauty Render** | Final lookdev showcase | 1920x1080, PNG, Substrate Toon active |
| **Wireframe View** | Technical proof | 1920x1080, PNG, wireframe overlay |
| **Material Breakdown** | Material system proof | 1920x1080, PNG, material ID view |
| **PCG Overlay** | Procedural proof | 1920x1080, PNG, PCG debug visualization |
| **Performance Stats** | Technical documentation | Screenshot of stats panel |

**Capture Instructions:**
1. Open `L_KaleidoNave` in UE5.8 Editor
2. Position camera for hero shot (bridge overview with open sky)
3. Enable Substrate Toon master material
4. Capture beauty render at 1920x1080
5. Switch to wireframe view, capture wireframe render
6. Enable material ID view, capture material breakdown
7. Enable PCG debug visualization, capture PCG overlay
8. Open stats panel (Ctrl+Shift+H), capture performance stats

**Output Location:**
```
my-site-deploy/generated/assets/landscape-loops/
├── L_KaleidoNave_beauty.png
├── L_KaleidoNave_wireframe.png
├── L_KaleidoNave_materials.png
├── L_KaleidoNave_pcg.png
└── L_KaleidoNave_stats.png
```

#### 2. L_MelusinaMorning (Bedroom Interior)

**Level Description:**
- First controllable authored level
- Limited initially to Melusina's bedroom interior
- Contains bed/save sanctuary, empty companion perch, first failed Songcraft cue

**Renders Required:**

| Render Type | Purpose | Technical Specs |
|-------------|---------|-----------------|
| **Beauty Render** | Final lookdev showcase | 1920x1080, PNG, Substrate Toon active |
| **Wireframe View** | Technical proof | 1920x1080, PNG, wireframe overlay |
| **Material Breakdown** | Material system proof | 1920x1080, PNG, material ID view |
| **PCG Overlay** | Procedural proof | 1920x1080, PNG, PCG debug visualization |
| **Performance Stats** | Technical documentation | Screenshot of stats panel |

**Capture Instructions:**
1. Open `L_MelusinaMorning` in UE5.8 Editor
2. Position camera for hero shot (bedroom overview showing bed, perch, Songcraft area)
3. Enable Substrate Toon master material
4. Capture beauty render at 1920x1080
5. Switch to wireframe view, capture wireframe render
6. Enable material ID view, capture material breakdown
7. Enable PCG debug visualization, capture PCG overlay
8. Open stats panel (Ctrl+Shift+H), capture performance stats

**Output Location:**
```
my-site-deploy/generated/assets/landscape-loops/
├── L_MelusinaMorning_beauty.png
├── L_MelusinaMorning_wireframe.png
├── L_MelusinaMorning_materials.png
├── L_MelusinaMorning_pcg.png
└── L_MelusinaMorning_stats.png
```

#### 3. ZenForestTest (Combat Smoke-Test Map)

**Level Description:**
- Combat smoke-test map
- Used until bedroom and Dreamstate transitions are stable
- Forest environment with combat encounter areas

**Renders Required:**

| Render Type | Purpose | Technical Specs |
|-------------|---------|-----------------|
| **Beauty Render** | Final lookdev showcase | 1920x1080, PNG, Substrate Toon active |
| **Wireframe View** | Technical proof | 1920x1080, PNG, wireframe overlay |
| **Material Breakdown** | Material system proof | 1920x1080, PNG, material ID view |
| **PCG Overlay** | Procedural proof | 1920x1080, PNG, PCG debug visualization |
| **Performance Stats** | Technical documentation | Screenshot of stats panel |

**Capture Instructions:**
1. Open `ZenForestTest` in UE5.8 Editor
2. Position camera for hero shot (forest overview showing combat area)
3. Enable Substrate Toon master material
4. Capture beauty render at 1920x1080
5. Switch to wireframe view, capture wireframe render
6. Enable material ID view, capture material breakdown
7. Enable PCG debug visualization, capture PCG overlay
8. Open stats panel (Ctrl+Shift+H), capture performance stats

**Output Location:**
```
my-site-deploy/generated/assets/landscape-loops/
├── ZenForestTest_beauty.png
├── ZenForestTest_wireframe.png
├── ZenForestTest_materials.png
├── ZenForestTest_pcg.png
└── ZenForestTest_stats.png
```

#### 4. L_FallenMoon (Recursive Expedition)

**Level Description:**
- Recursive expedition rooms (procedural)
- Seeded run recording: Room A → blessing/burden → Room B/encounter → exit
- Procedurally generated dungeon environment

**Renders Required:**

| Render Type | Purpose | Technical Specs |
|-------------|---------|-----------------|
| **Beauty Render** | Final lookdev showcase | 1920x1080, PNG, Substrate Toon active |
| **Wireframe View** | Technical proof | 1920x1080, PNG, wireframe overlay |
| **Material Breakdown** | Material system proof | 1920x1080, PNG, material ID view |
| **PCG Overlay** | Procedural proof | 1920x1080, PNG, PCG debug visualization |
| **Performance Stats** | Technical documentation | Screenshot of stats panel |

**Capture Instructions:**
1. Open `L_FallenMoon` in UE5.8 Editor
2. Position camera for hero shot (dungeon overview showing Room A, blessing/burden area, Room B)
3. Enable Substrate Toon master material
4. Capture beauty render at 1920x1080
5. Switch to wireframe view, capture wireframe render
6. Enable material ID view, capture material breakdown
7. Enable PCG debug visualization, capture PCG overlay
8. Open stats panel (Ctrl+Shift+H), capture performance stats

**Output Location:**
```
my-site-deploy/generated/assets/landscape-loops/
├── L_FallenMoon_beauty.png
├── L_FallenMoon_wireframe.png
├── L_FallenMoon_materials.png
├── L_FallenMoon_pcg.png
└── L_FallenMoon_stats.png
```

---

## Priority 2: Map Props to Gameplay Levels

### Task Overview

Identify which props appear in which gameplay levels and create prop-to-level mapping documentation. Capture prop-in-context renders showing props in their actual gameplay levels.

### Props to Map

| Prop Name | File Pattern | Description |
|-----------|--------------|-------------|
| **Cross Hero** | `props/cross_hero_*.png` | Cross prop (hero variant) |
| **Gazebo** | `props/gazebo_komikaze_*.png` | Gazebo structure prop |
| **Zen Lantern** | `props/zenlantern_komikaze_*.png` | Zen lantern prop |
| **Sakura Petal** | `props/sakura_petal_komikaze_*.png` | Sakura petal particle prop |
| **Violin** | `props/violin_komikaze_*.png` | Violin instrument prop |
| **Magical Wand** | `props/magical_wand_komikaze_*.png` | Magical wand prop |
| **Melody Slime** | `props/melody_slime_komikaze_*.png` | Melody slime enemy prop |
| **Brick Props** | `props/brick*_komikaze_*.png` | Brick building material props |

### Mapping Instructions

For each prop:

1. **Identify Level Placement**
   - Open each gameplay level in UE5.8 Editor
   - Search for the prop in the level's asset browser
   - Document which level(s) contain the prop

2. **Capture Prop-in-Context Renders**
   - Position camera to show prop in its gameplay context
   - Capture beauty render at 1920x1080
   - Include surrounding environment for context

3. **Document Prop Metadata**
   - Prop name and file pattern
   - Level(s) where prop appears
   - Prop purpose/role in gameplay
   - Technical specs (triangles, materials, etc.)

### Output Documentation

Create a prop-to-level mapping document:

```
my-site-deploy/generated/assets/props/PROP_MAPPING.md

# Prop-to-Level Mapping

## Cross Hero
- **File Pattern:** `props/cross_hero_*.png`
- **Level(s):** L_KaleidoNave, ZenForestTest
- **Purpose:** Collectible item, combat encounter trigger
- **Technical Specs:** [triangles, materials, etc.]

## Gazebo
- **File Pattern:** `props/gazebo_komikaze_*.png`
- **Level(s):** L_MelusinaMorning
- **Purpose:** Environmental decoration, photo spot
- **Technical Specs:** [triangles, materials, etc.]

[... continue for all props ...]
```

### Prop-in-Context Renders

Capture prop-in-context renders for each prop:

```
my-site-deploy/generated/assets/props/
├── cross_hero_in_context.png
├── gazebo_in_context.png
├── zenlantern_in_context.png
├── sakura_petal_in_context.png
├── violin_in_context.png
├── magical_wand_in_context.png
├── melody_slime_in_context.png
└── brick_in_context.png
```

---

## Technical Specifications

### Render Settings

**Beauty Renders:**
- Resolution: 1920x1080
- Format: PNG (lossless)
- Color Space: sRGB
- Anti-aliasing: Enabled
- Substrate Toon: Active (M_Master_Toon_Universal)

**Wireframe Renders:**
- Resolution: 1920x1080
- Format: PNG (lossless)
- View Mode: Wireframe overlay on beauty
- Line Color: White (or project standard)

**Material Breakdown Renders:**
- Resolution: 1920x1080
- Format: PNG (lossless)
- View Mode: Material ID
- Color Coding: Project standard material ID colors

**PCG Overlay Renders:**
- Resolution: 1920x1080
- Format: PNG (lossless)
- View Mode: PCG debug visualization
- Overlay: PCG graph connections and instance counts

### Performance Stats

Capture the following stats for each level:
- Triangle count
- Draw calls
- Material count
- Texture count
- PCG instance count
- Frame rate (FPS)

**Capture Method:**
1. Open stats panel (Ctrl+Shift+H)
2. Navigate to "Game" or "Engine" tab
3. Screenshot the stats panel
4. Save as `[LevelName]_stats.png`

---

## Preservation Rules

**DO NOT TOUCH:**
- All EEVEE renders in `character/` directory
- All Melusina renders (beauty, glam, wireframe, turntable, etc.)
- All material loops (demonstrate Substrate Toon master material)
- All nightshift material isolates
- All melodia-game-ui textures

These are current and demonstrate the hybrid pipeline (Blender EEVEE + UE Substrate Toon).

---

## Output Summary

### Gameplay Level Renders

```
my-site-deploy/generated/assets/landscape-loops/
├── L_KaleidoNave_beauty.png
├── L_KaleidoNave_wireframe.png
├── L_KaleidoNave_materials.png
├── L_KaleidoNave_pcg.png
├── L_KaleidoNave_stats.png
├── L_MelusinaMorning_beauty.png
├── L_MelusinaMorning_wireframe.png
├── L_MelusinaMorning_materials.png
├── L_MelusinaMorning_pcg.png
├── L_MelusinaMorning_stats.png
├── ZenForestTest_beauty.png
├── ZenForestTest_wireframe.png
├── ZenForestTest_materials.png
├── ZenForestTest_pcg.png
├── ZenForestTest_stats.png
├── L_FallenMoon_beauty.png
├── L_FallenMoon_wireframe.png
├── L_FallenMoon_materials.png
├── L_FallenMoon_pcg.png
└── L_FallenMoon_stats.png
```

### Prop Mapping Documentation

```
my-site-deploy/generated/assets/props/
├── PROP_MAPPING.md
├── cross_hero_in_context.png
├── gazebo_in_context.png
├── zenlantern_in_context.png
├── sakura_petal_in_context.png
├── violin_in_context.png
├── magical_wand_in_context.png
├── melody_slime_in_context.png
└── brick_in_context.png
```

---

## Next Steps After Capture

Once renders are captured:

1. **Commit Renders to Repository**
   - Add all new renders to `my-site-deploy/generated/assets/`
   - Commit with message: "Add UE5.8 gameplay level renders and prop mapping"
   - Push to `fromage3900/my-site` main branch

2. **Update Website (Claude Task)**
   - Replace placeholder renders in `application-hub.html`
   - Replace placeholder renders in `recruiter-one-sheet.html`
   - Add technical descriptions for each level
   - Add performance stats (triangles, draw calls, materials)
   - Commit and push to GitHub Pages

3. **Verify Deploy**
   - Check GitHub Pages deploy status
   - Verify renders are live on website
   - Test all level links and prop mapping

---

## References

### Documentation
- `BS_GodFile/Docs/WEBSITE_OVERHAUL_PLAN_2026-07-31.md` — Comprehensive overhaul plan
- `BS_GodFile/Docs/WEBSITE_OVERHAUL_LEVEL_MAPPING_2026-07-31.md` — Level mapping details
- `BS_GodFile/Docs/MELODIA_FIRST_20_MINUTES_VERTICAL_SLICE.md` — Vertical slice specification
- `BS_GodFile/Docs/Handoffs/CLAUDE_HANDOFF_2026-07-31.md` — Claude project overview
- `BS_GodFile/Docs/Handoffs/RIDER_HANDOFF_2026-07-31.md` — JetBrains Rider handoff

### Website Files
- `my-site-deploy/wix/application-hub.html` — Main portfolio hub
- `my-site-deploy/wix/recruiter-one-sheet.html` — Recruiter one-sheet

### Git Repository
- **Remote:** `https://github.com/fromage3900/my-site.git`
- **Branch:** `main`
- **Latest Commit:** `44157e2` — "Update level mapping to reflect actual UE5.8 gameplay levels"
- **Deploy Status:** ✅ Live on GitHub Pages

---

## Contact

If you have questions about this handoff:
- **Render Capture:** Refer to this document (BLACKBOX_HANDOFF_2026-07-31.md)
- **Level Mapping:** Refer to `WEBSITE_OVERHAUL_LEVEL_MAPPING_2026-07-31.md`
- **Vertical Slice:** Refer to `MELODIA_FIRST_20_MINUTES_VERTICAL_SLICE.md`
- **Website Integration:** Refer to `CLAUDE_HANDOFF_2026-07-31.md`

---

**End of Handoff**