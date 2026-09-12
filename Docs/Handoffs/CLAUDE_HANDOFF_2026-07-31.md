# Claude Handoff — Project Overview & Recent Changes

**Session Date:** July 31, 2026  
**Handoff Type:** Comprehensive Project Overview  
**Status:** Website deployed, UE5 level renders pending

---

## Executive Summary

This document provides a comprehensive overview of the Melodia project, all work completed to date, and recent changes made during the July 31, 2026 session. The project is a UE5.8 stylized environment art portfolio with a hybrid Blender→UE pipeline, targeting Infinity Nikki / Papergames / Infold studios.

**Key Achievement (July 31):** Website overhaul completed — level mapping updated to reflect actual UE5.8 gameplay levels, all EEVEE/Melusina renders preserved, deployed to GitHub Pages.

---

## Project Overview

### What is Melodia?

Melodia is a UE5.8 stylized environment art portfolio project demonstrating:
- **Hybrid Pipeline:** Blender 5.1 (procedural geometry, EEVEE renders) → UE5.8 (Substrate Toon, PCG scattering)
- **First 20 Minutes Vertical Slice:** Four gameplay levels showcasing core loop
- **Infinity Nikki Alignment:** Stylized fantasy, magical girl aesthetic, fashion-fantasy worlds
- **Technical Art Proof:** 916–1015 expression Substrate Toon master material, 77 PCG graphs, 49 Geometry Nodes builders

### Project Structure

```
BS_GodFile/
├── Content/
│   ├── Maps/                    # UE5.8 levels
│   │   ├── L_KaleidoNave        # Prologue/bifrost bridge (formerly L_Melodia_Dreamstate)
│   │   ├── L_MelusinaMorning    # Bedroom interior
│   │   ├── ZenForestTest        # Combat smoke-test map
│   │   └── L_FallenMoon         # Recursive expedition (4th level)
│   ├── Python/                  # Automation scripts
│   └── ...
├── Source/
│   └── BS_GodFile/
│       └── MelodiaIntegration/  # C++ integration components
├── Docs/
│   ├── Handoffs/                # Agent handoff documents
│   ├── WEBSITE_OVERHAUL_PLAN_2026-07-31.md
│   └── MELODIA_FIRST_20_MINUTES_VERTICAL_SLICE.md
└── my-site-clean/               # Website source (GitHub Pages)
    └── wix/                     # HTML/CSS/JS files
```

### Website Repository

- **Remote:** `https://github.com/fromage3900/my-site.git`
- **Branch:** `main`
- **Latest Commit:** `44157e2` — "Update level mapping to reflect actual UE5.8 gameplay levels"
- **Deploy Status:** ✅ Live on GitHub Pages

---

## All Work Completed (Historical)

### Phase 1: Foundation (Pre-July 31)

1. **UE5.8 Project Setup**
   - Configured Substrate Toon master material (916–1015 expressions)
   - Built 77 PCG graphs for procedural scattering
   - Created 49 Geometry Nodes builders in Blender 5.1

2. **Vertical Slice Design**
   - Authored `MELODIA_FIRST_20_MINUTES_VERTICAL_SLICE.md`
   - Defined four gameplay levels and core loop
   - Documented Resonance Bond, Dissonance Profile, Recursive Expedition contract

3. **Character Development**
   - Created Melusina character (EEVEE renders, glam variants, wireframe views)
   - Developed Sir Melodious companion (cockatoo)
   - Built turntable renders and beauty plates

4. **Material System**
   - 12 parameter families in Substrate Toon master
   - 19 showcase Material Instances (NikkiHero, CelestialNebula, SDF, Cosmic)
   - SDF ornamental detail system

5. **Game UI**
   - 50+ UI textures (filigree, grade halos, highway, hitline, note heads)
   - Rhythm game interface
   - SheetMusicHUD

### Phase 2: Website Development (Pre-July 31)

1. **Initial Website Build**
   - Created portfolio website with 4 environment pillars
   - Sakura Dream, Space Cathedral, Cosmic Orrery, Baroque Grotto
   - Deployed to GitHub Pages

2. **Content Organization**
   - Character renders, material loops, nightshift isolates
   - Props, ornaments, portfolio-scan, sculpt, signature, unreal folders
   - Hybrid pipeline documentation

### Phase 3: July 31, 2026 Session (Recent Work)

#### 1. Website Readability Audit ✅

**Problem:** Text was illegible due to small font sizes and low contrast.

**Solution:**
- Updated `wix/melodia-luxury-type.css` — Added minimum font size of 0.75rem for UI text
- Updated `wix/melodia-editorial.css` — Improved nav, buttons, kicker, footer contrast
- Updated `wix/portfolio-pages.css` — Improved table rows, badges, info cells contrast

**Changes:**
- Bumped minimum font sizes from 0.65–0.7rem → 0.75rem (12px)
- Improved text contrast: raised opacity from 0.62–0.72 → 0.82–0.92
- Updated stub pages from "Coming Soon" → "In Progress"

**Commit:** `5ad0596` — "fix: readability audit - contact info, font sizes, contrast, stub copy"

#### 2. Contact Information Update ✅

**Problem:** Recruiter one-sheet had placeholder contact info.

**Solution:**
- Updated `wix/recruiter-one-sheet.html` with real contact info:
  - Email: `brennan.shepherd3900@gmail.com`
  - LinkedIn: `https://www.linkedin.com/in/brennan-shepherd-3b6111307/`
  - ArtStation: `https://www.artstation.com/fromage3900`

**Commit:** Included in `5ad0596`

#### 3. Website Level Mapping Overhaul ✅

**Problem:** Website showed portfolio world names (Sakura Dream, Space Cathedral, etc.) instead of actual UE5.8 gameplay level names.

**Solution:**
- Updated `wix/application-hub.html` — Changed "Four pillars" section to "First 20 minutes"
- Updated `wix/recruiter-one-sheet.html` — Changed environment showcase labels

**Level Mapping Changes:**

| Old Portfolio World | New UE Level | Description |
|---------------------|--------------|-------------|
| Sakura Dream | **L_KaleidoNave** | Prologue · Bifrost Bridge |
| Space Cathedral | **L_MelusinaMorning** | Bedroom Interior |
| Cosmic Orrery | **ZenForestTest** | Combat Smoke-Test |
| Baroque Grotto | **L_FallenMoon** | Recursive Expedition |

**Commit:** `44157e2` — "Update level mapping to reflect actual UE5.8 gameplay levels"

#### 4. Documentation Created ✅

**New Files:**
- `BS_GodFile/Docs/WEBSITE_OVERHAUL_PLAN_2026-07-31.md` — Comprehensive overhaul plan
- `BS_GodFile/Docs/WEBSITE_OVERHAUL_LEVEL_MAPPING_2026-07-31.md` — Level mapping details
- `BS_GodFile/Docs/Handoffs/RIDER_HANDOFF_2026-07-31.md` — JetBrains Rider handoff
- `BS_GodFile/Docs/Handoffs/CLAUDE_HANDOFF_2026-07-31.md` — This document
- `BS_GodFile/Docs/Handoffs/BLACKBOX_HANDOFF_2026-07-31.md` — Blackbox render handoff

#### 5. Git Repository Issue Resolved ✅

**Problem:** `.git` folder was corrupted during a partial `rmdir` command that left Windows file locks on `.git/objects`.

**Resolution:**
1. Force-deleted the broken folder using PowerShell
2. Re-cloned using `gh repo clone`
3. Re-applied all changes
4. Successfully committed and pushed

**Prevention:** Avoid using `rmdir /s /q` on git repositories on Windows. Use `git clean` or manually delete non-`.git` files instead.

---

## Current State

### Website Status
- ✅ Level mapping updated to reflect actual UE5.8 gameplay levels
- ✅ All EEVEE/Melusina renders preserved (DO NOT TOUCH)
- ✅ Hybrid pipeline documentation added (Blender EEVEE → UE Substrate Toon)
- ✅ Contact information updated
- ✅ Readability improvements applied
- ✅ Deployed to GitHub Pages

### Asset Status
- ✅ Character renders (EEVEE/Melusina) — Current, preserved
- ✅ Material loops (Substrate Toon proof) — Current, preserved
- ✅ Nightshift material isolates — Current, preserved
- ✅ Melodia Game UI textures — Current, preserved
- ⚠️ Landscape loop renders — Using portfolio world renders as temporary placeholders
- ⚠️ Prop renders — Not yet mapped to specific gameplay levels

### Git Repository Status
- ✅ Repository re-cloned after corruption issue
- ✅ All changes committed and pushed
- ✅ GitHub Pages auto-deploy triggered

---

## What Needs to Be Done Next

### Priority 1: Capture Actual Gameplay Level Renders (Blackbox AI)

**Task:** Use UE5.8 to capture beauty renders of the four actual gameplay levels.

**Levels to Capture:**
1. **L_KaleidoNave** — Prologue/bifrost bridge
2. **L_MelusinaMorning** — Bedroom interior
3. **ZenForestTest** — Combat smoke-test map
4. **L_FallenMoon** — Recursive expedition

**For Each Level, Capture:**
- Beauty render (final lookdev)
- Wireframe/graybox view
- Material breakdown
- PCG overlay visualization
- Performance stats (triangles, draw calls, materials)

**Output Location:**
- `my-site-deploy/generated/assets/landscape-loops/` (replace existing placeholders)
- Or create new folder: `my-site-deploy/generated/assets/gameplay-levels/`

**Reference:** `BS_GodFile/Docs/Handoffs/BLACKBOX_HANDOFF_2026-07-31.md`

### Priority 2: Map Props to Gameplay Levels (Blackbox AI)

**Task:** Identify which props appear in which gameplay levels.

**Props to Map:**
- `props/cross_hero_*.png` — Cross prop
- `props/gazebo_komikaze_*.png` — Gazebo prop
- `props/zenlantern_komikaze_*.png` — Zen lantern prop
- `props/sakura_petal_komikaze_*.png` — Sakura petal
- `props/violin_komikaze_*.png` — Violin prop
- `props/magical_wand_komikaze_*.png` — Magical wand
- `props/melody_slime_komikaze_*.png` — Melody slime
- `props/brick*_komikaze_*.png` — Brick props

**Output:**
- Create prop-to-level mapping document
- Capture prop-in-context renders (props in their actual gameplay levels)

### Priority 3: Update Website with New Renders (Claude)

**Task:** Once gameplay level renders are captured, integrate them into the website.

**Steps:**
1. Replace placeholder renders in `application-hub.html`
2. Replace placeholder renders in `recruiter-one-sheet.html`
3. Add technical descriptions for each level
4. Add performance stats (triangles, draw calls, materials)
5. Commit and push to GitHub Pages

### Priority 4: Add Hybrid Pipeline Documentation (Claude)

**Task:** Create a dedicated "Pipeline" or "Technical Art" section on the website.

**Content:**
- Explain Blender → UE asset flow
- Show side-by-side: Blender EEVEE render vs UE Substrate Toon render
- Document PCG integration
- Show Geometry Nodes → UE import process

**Reference:**
- `BS_GodFile/Docs/WEBSITE_OVERHAUL_PLAN_2026-07-31.md` — Phase 2, Task 2.3

---

## Technical Context

### Hybrid Pipeline

The project uses a hybrid pipeline:
- **Blender 5.1** — Procedural geometry (49 Geometry Nodes builders), EEVEE renders, character lookdev
- **Unreal Engine 5.8** — Substrate Toon master material (916–1015 expressions), PCG scattering (77 graphs), final game renders

### Level Structure (First 20 Minutes)

Based on `BS_GodFile/Docs/MELODIA_FIRST_20_MINUTES_VERTICAL_SLICE.md`:

1. **L_KaleidoNave** (formerly L_Melodia_Dreamstate)
   - Short, controlled prologue/cutscene on floating bifrost-like bridge
   - Establishes emotional Dissonance and Sir Melodious's distance/absence

2. **L_MelusinaMorning**
   - First controllable authored level
   - Limited initially to Melusina's bedroom interior
   - Contains bed/save sanctuary, empty companion perch, first failed Songcraft cue

3. **ZenForestTest**
   - Combat smoke-test map
   - Used until bedroom and Dreamstate transitions are stable

4. **L_FallenMoon** (formerly recursive expedition)
   - Recursive expedition rooms (procedural)
   - Seeded run recording: Room A → blessing/burden → Room B/encounter → exit

### Preservation Rules

**DO NOT TOUCH:**
- All EEVEE renders in `character/` directory
- All Melusina renders (beauty, glam, wireframe, turntable, etc.)
- All material loops (demonstrate Substrate Toon master material)
- All nightshift material isolates
- All melodia-game-ui textures

These are current and demonstrate the hybrid pipeline (Blender EEVEE + UE Substrate Toon).

---

## Known Issues

### Git Repository Corruption

**Issue:** The `.git` folder was corrupted during a partial `rmdir` command that left Windows file locks on `.git/objects`.

**Resolution:**
1. Force-deleted the broken folder using PowerShell
2. Re-cloned using `gh repo clone`
3. Re-applied all changes
4. Successfully committed and pushed

**Prevention:** Avoid using `rmdir /s /q` on git repositories on Windows. Use `git clean` or manually delete non-`.git` files instead.

### Unicode Encoding Issue

**Issue:** Python script failed with `UnicodeEncodeError` when printing Unicode characters (✓, ✗) to Windows console.

**Resolution:** Replaced Unicode characters with ASCII equivalents ([OK], [FAIL]).

**Prevention:** When writing Python scripts for Windows, avoid Unicode characters in print statements or use `sys.stdout.reconfigure(encoding='utf-8')`.

---

## References

### Documentation
- `BS_GodFile/Docs/WEBSITE_OVERHAUL_PLAN_2026-07-31.md` — Comprehensive overhaul plan
- `BS_GodFile/Docs/WEBSITE_OVERHAUL_LEVEL_MAPPING_2026-07-31.md` — Level mapping details
- `BS_GodFile/Docs/MELODIA_FIRST_20_MINUTES_VERTICAL_SLICE.md` — Vertical slice specification
- `BS_GodFile/Docs/Handoffs/RIDER_HANDOFF_2026-07-31.md` — JetBrains Rider handoff
- `BS_GodFile/Docs/Handoffs/BLACKBOX_HANDOFF_2026-07-31.md` — Blackbox render handoff

### Website Files
- `my-site-deploy/wix/application-hub.html` — Main portfolio hub
- `my-site-deploy/wix/recruiter-one-sheet.html` — Recruiter one-sheet
- `my-site-deploy/wix/melodia-luxury-type.css` — Base typography
- `my-site-deploy/wix/melodia-editorial.css` — Editorial styles
- `my-site-deploy/wix/portfolio-pages.css` — Portfolio page styles

### Git Repository
- **Remote:** `https://github.com/fromage3900/my-site.git`
- **Branch:** `main`
- **Latest Commit:** `44157e2` — "Update level mapping to reflect actual UE5.8 gameplay levels"
- **Deploy Status:** ✅ Live on GitHub Pages

---

## Contact

If you have questions about this handoff:
- **Website Issues:** Refer to `WEBSITE_OVERHAUL_PLAN_2026-07-31.md`
- **Level Mapping:** Refer to `WEBSITE_OVERHAUL_LEVEL_MAPPING_2026-07-31.md`
- **Vertical Slice:** Refer to `MELODIA_FIRST_20_MINUTES_VERTICAL_SLICE.md`
- **Render Capture:** Refer to `BLACKBOX_HANDOFF_2026-07-31.md`

---

**End of Handoff**
