# JetBrains Rider Handoff — 2026-07-31

**Session Date:** July 31, 2026  
**Handoff Type:** Website Overhaul + UE5 Level Mapping Update  
**Status:** Website deployed, UE5 level renders pending

---

## Executive Summary

This session completed a comprehensive website overhaul to align the portfolio with the actual UE5.8 gameplay levels from the first 20 minutes vertical slice. The website now correctly references the four gameplay levels instead of the old portfolio world names.

**Key Achievement:** Website is live and deployed with correct level mapping. All EEVEE/Melusina renders preserved.

---

## What Was Completed

### 1. Website Level Mapping Update ✅

**Files Modified:**
- `my-site-deploy/wix/application-hub.html`
- `my-site-deploy/wix/recruiter-one-sheet.html`

**Level Mapping Changes:**

| Old Portfolio World | New UE Level | Description |
|---------------------|--------------|-------------|
| Sakura Dream | **L_KaleidoNave** | Prologue · Bifrost Bridge |
| Space Cathedral | **L_MelusinaMorning** | Bedroom Interior |
| Cosmic Orrery | **ZenForestTest** | Combat Smoke-Test |
| Baroque Grotto | **L_FallenMoon** | Recursive Expedition |

**Commit:** `44157e2` — "Update level mapping to reflect actual UE5.8 gameplay levels"  
**Deploy Status:** ✅ Live on GitHub Pages

### 2. Website Readability Improvements ✅

**CSS Files Updated:**
- `wix/melodia-luxury-type.css` — Added minimum font size of 0.75rem for UI text
- `wix/melodia-editorial.css` — Improved nav, buttons, kicker, footer contrast
- `wix/portfolio-pages.css` — Improved table rows, badges, info cells contrast

**Changes:**
- Bumped minimum font sizes from 0.65–0.7rem → 0.75rem (12px)
- Improved text contrast: raised opacity from 0.62–0.72 → 0.82–0.92
- Updated stub pages from "Coming Soon" → "In Progress"

### 3. Contact Information Update ✅

**File Modified:** `wix/recruiter-one-sheet.html`

**Updated Contact Info:**
- Email: `brennan.shepherd3900@gmail.com`
- LinkedIn: `https://www.linkedin.com/in/brennan-shepherd-3b6111307/`
- ArtStation: `https://www.artstation.com/fromage3900`

### 4. Documentation Created ✅

**New Files:**
- `BS_GodFile/Docs/WEBSITE_OVERHAUL_PLAN_2026-07-31.md` — Comprehensive overhaul plan
- `BS_GodFile/Docs/WEBSITE_OVERHAUL_LEVEL_MAPPING_2026-07-31.md` — Level mapping details
- `BS_GodFile/Docs/Handoffs/RIDER_HANDOFF_2026-07-31.md` — This document

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

**Tools:**
- UE5.8 Editor
- UE MCP (if available) for automated capture
- Screenshot tool for manual capture

**Output Location:**
- `my-site-deploy/generated/assets/landscape-loops/` (replace existing placeholders)
- Or create new folder: `my-site-deploy/generated/assets/gameplay-levels/`

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

### Priority 3: Update Website with New Renders (Cline)

**Task:** Once gameplay level renders are captured, integrate them into the website.

**Steps:**
1. Replace placeholder renders in `application-hub.html`
2. Replace placeholder renders in `recruiter-one-sheet.html`
3. Add technical descriptions for each level
4. Add performance stats (triangles, draw calls, materials)
5. Commit and push to GitHub Pages

### Priority 4: Add Hybrid Pipeline Documentation (Cline)

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

1. **L_Melodia_Dreamstate** → Now called **L_KaleidoNave**
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

## Rider-Specific Tasks

### C++ Side (If Applicable)

If you're working on the UE5 C++ side in Rider:

1. **Verify Level Names in Code**
   - Check if any C++ code references the old level names
   - Update references to use new level names (KaleidoNave, MelusinaMorning, ZenForestTest, FallenMoon)

2. **Check Map Transition Components**
   - `MelodiaMapTransitionComponent.cpp` / `.h`
   - Ensure transition logic uses correct level names

3. **Verify PCG Graph References**
   - Check if PCG graphs reference specific levels
   - Update any hardcoded level references

4. **Build and Test**
   - Build the project in Rider
   - Verify no compilation errors
   - Test level transitions in UE5.8 Editor

### Blueprint Side (If Applicable)

If you're working on Blueprints:

1. **Update Level Streaming References**
   - Check any Blueprint level streaming logic
   - Update to use new level names

2. **Verify Map Transition Blueprints**
   - Check any Blueprint-based map transitions
   - Update to use new level names

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

---

**End of Handoff**