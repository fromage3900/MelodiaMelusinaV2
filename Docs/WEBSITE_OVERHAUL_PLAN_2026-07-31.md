# Website Overhaul Plan — Align with First 20 Minutes Vertical Slice

**Date:** 2026-07-31  
**Status:** Planning Phase  
**Priority:** High — Recruiter sendoff preparation

---

## Executive Summary

The current portfolio website showcases 4 environment pillars (Sakura Dream, Space Cathedral, Cosmic Orrery, Baroque Grotto) as standalone portfolio worlds. However, the actual game's first 20 minutes uses a different level structure:

**Actual Gameplay Levels (First 20 Minutes):**
1. `L_Melodia_Dreamstate` — Prologue/bifrost bridge
2. `L_MelusinaMorning` — Bedroom interior
3. `ZenForestTest` — Combat smoke-test map
4. Recursive expedition rooms (procedural)

**Current Website Levels:**
- Sakura Dream (portfolio world)
- Space Cathedral (portfolio world)
- Cosmic Orrery (portfolio world)
- Baroque Grotto (portfolio world)

**Gap:** The website does not reflect the actual gameplay experience. Recruiters viewing the site will see portfolio worlds, not the vertical slice that demonstrates the game's core loop.

---

## Blender MCP Status

**Adapter:** `BS_GodFile/deploy/blender_mcp_adapter.py`  
**Connection:** TCP socket addon on port 9878  
**Current State:** NOT connected to this session

**Available Tools:**
- `blender_scene_info` — Get current scene info
- `blender_object_info` — Get detailed object info
- `blender_execute_code` — Execute arbitrary Blender Python
- `blender_viewport_screenshot` — Capture viewport screenshot
- `blender_shared_context` — Get shared context state
- `blender_create_handle` — Create object handle

**Action Required:** To use Blender MCP, the Blender addon must be running and the adapter must be started. This is a **blackbox AI task** — requires manual Blender session setup.

---

## Current Website Asset Inventory

### Character Renders (DO NOT TOUCH — EEVEE/Melusina content is current)
- `character/melusina_beauty_34.png`
- `character/melusina_eevee_beauty_34.png`
- `character/melusina_eevee_glam_20260715c_01.png` through `_05.png`
- `character/melusina_beauty_eevee_20260715c_01.png`
- `character/melusina_portrait_face.png`
- `character/melusina_turntable_0001.png`, `_0060.png`, `_0120.png`
- `character/melusina_verify_beauty.png`, `_macro.png`
- `character/melusina_water_splash_001.png`, `_waterhair_macro.png`
- `character/melusina_sirmelodious_companion.png`
- `character/melusina_low.png`, `_low_nikki_001.png`
- `character/melusina_34_wireframe_grey_20260715.png`
- `character/melusina_front_wireframe_grey_20260715.png`
- `character/melusina_design_sketch.png`
- `character/melusina_diorama_beauty.png`
- `character/melusina_cycles_smoke.png`
- `character/melusina_beauty_depth_color.png`
- `character/melusina_beauty_jewelry_001.png`
- `character/melusina_beauty_nikki_001.png`, `_20260714_01.png`
- `character/melusina_beauty_void_iri.png`
- `character/melusina_eevee_front.png`, `_three_quarter.png`
- `character/melusina_eevee_portrait.png`
- `character/melusina_glam_audvis_001.png` (sequence 0001-0146)
- `character/hero_20260712/`, `hero_sim/`

**Status:** ✅ INTACT — These are current EEVEE renders from the hybrid pipeline (Blender EEVEE + UE). Do not modify or remove.

### Landscape Loops (Portfolio Worlds — Need Mapping to Gameplay)
- `landscape-loops/WP_SakuraDream_terrain.png` + `.webm`
- `landscape-loops/WP_SpaceCathedral_terrain.png` + `.webm`
- `landscape-loops/WP_CosmicOrrery_terrain.png` + `.webm`
- `landscape-loops/WP_BaroqueGrotto_terrain.png` + `.webm`

**Status:** ⚠️ These are portfolio worlds, not actual gameplay levels. Need to either:
1. Map them to gameplay levels (if they're used in the vertical slice)
2. Replace with actual gameplay level renders
3. Keep as "concept art" and add new "gameplay" section

### Material Loops (Current — Hybrid Pipeline Proof)
- `material-loops/MI_Cosmic_*.png` + `.webm` (6 materials)
- `material-loops/MI_SDF_*.png` + `.webm` (6 materials)
- `material-loops/celestial_nebula_nasa_sphere.webm`

**Status:** ✅ Current — These demonstrate the Substrate Toon master material and SDF ornamental detail. Keep as technical proof.

### Props (Need Gameplay Mapping)
- `props/cross_hero_*.png` (cross prop renders)
- `props/gazebo_komikaze_*.png` (gazebo prop renders)
- `props/zenlantern_komikaze_*.png` (zen lantern prop renders)
- `props/sakura_petal_komikaze_*.png`
- `props/violin_komikaze_*.png`
- `props/magical_wand_komikaze_*.png`
- `props/melody_slime_komikaze_*.png`
- `props/brick*_komikaze_*.png`

**Status:** ⚠️ These are prop renders but not mapped to specific gameplay levels. Need to identify which props appear in which levels.

### Nightshift (Material Isolates — Current)
- `nightshift/MI_Cosmic_*.png` (material isolates)
- `nightshift/MI_SDF_*.png` (material isolates)
- `nightshift/grid_cosmic_all.png`, `grid_nikki_heroes.png`
- `nightshift/celestial_nebula_nasa_sphere.png`

**Status:** ✅ Current — These are material isolate views for technical proof. Keep.

### Melodia Game UI (Current — Technical Art Proof)
- `melodia-game-ui/T_Melodia_*.png` (50+ UI textures)
- Includes filigree, grade halos, highway, hitline, note heads, etc.

**Status:** ✅ Current — These demonstrate the rhythm game UI system. Keep as technical art proof.

### Ornaments, Portfolio-Scan, Sculpt, Signature, Unreal
- Not yet inventoried in detail

**Status:** 🔍 Need detailed inventory

---

## Hybrid Pipeline Documentation

**Current State:** The project uses a hybrid pipeline:
- **Blender 5.1** — Procedural geometry (49 Geometry Nodes builders), EEVEE renders, character lookdev
- **Unreal Engine 5.8** — Substrate Toon master material (916–1015 expressions), PCG scattering (77 graphs), final game renders

**Website Reflection:** The current website shows Blender renders (EEVEE glam, beauty plates) and UE renders (landscape loops, material loops) but does not explicitly document the hybrid pipeline.

**Action Required:** Add a "Pipeline" or "Technical Art" section to the website that explains:
1. Blender → UE asset flow
2. EEVEE lookdev → Substrate Toon final
3. PCG integration
4. Geometry Nodes → UE import

---

## Comprehensive Overhaul Plan

### Phase 1: Content Audit & Mapping (Blackbox AI Tasks)

**Task 1.1: Inventory All UE Levels**
- Use UE MCP to list all levels in `Content/Maps/`
- Identify which levels are part of the first 20 minutes
- Document level names, purposes, and current state

**Task 1.2: Capture Gameplay Level Renders**
- For each gameplay level (`L_Melodia_Dreamstate`, `L_MelusinaMorning`, `ZenForestTest`):
  - Capture beauty renders (UE)
  - Capture wireframe/graybox renders
  - Capture material breakdowns
  - Capture PCG overlay visualizations

**Task 1.3: Map Props to Levels**
- Identify which props appear in which levels
- Create a prop-to-level mapping document

**Task 1.4: Capture Blender Renders**
- Use Blender MCP to capture:
  - Character turntable renders (if not already done)
  - Environment concept renders
  - Material lookdev renders

### Phase 2: Website Structure Overhaul

**Task 2.1: Add "Vertical Slice" Section**
- Create new section: "First 20 Minutes — Vertical Slice"
- Show the 4 gameplay levels in sequence
- For each level:
  - Beauty render
  - Wireframe/technical view
  - Key gameplay beat (from the timeline doc)
  - Technical notes (materials, PCG, etc.)

**Task 2.2: Reorganize "Environments" Section**
- Current: 4 portfolio worlds (Sakura Dream, Space Cathedral, Cosmic Orrery, Baroque Grotto)
- New structure:
  - **Gameplay Levels** (vertical slice)
    - L_Melodia_Dreamstate
    - L_MelusinaMorning
    - ZenForestTest
    - Recursive Expedition
  - **Portfolio Worlds** (concept art / future content)
    - Sakura Dream
    - Space Cathedral
    - Cosmic Orrery
    - Baroque Grotto

**Task 2.3: Add "Hybrid Pipeline" Section**
- Explain Blender → UE flow
- Show side-by-side: Blender EEVEE render vs UE Substrate Toon render
- Document PCG integration
- Show Geometry Nodes → UE import

**Task 2.4: Update "Character" Section**
- Keep all EEVEE/Melusina renders (DO NOT TOUCH)
- Add Sir Melodious companion renders
- Add character-to-gameplay mapping (which character renders appear in which levels)

**Task 2.5: Update "Props" Section**
- Map props to gameplay levels
- Show props in context (in-level screenshots)

### Phase 3: Content Creation (Blackbox AI Tasks)

**Task 3.1: Capture New Renders**
- Use UE MCP to capture beauty renders of gameplay levels
- Use UE MCP to capture wireframe/technical views
- Use UE MCP to capture PCG overlay visualizations
- Use Blender MCP to capture any missing character renders

**Task 3.2: Create Pipeline Diagrams**
- Create visual diagram of Blender → UE asset flow
- Create material comparison (EEVEE vs Substrate Toon)
- Create PCG graph visualization

**Task 3.3: Write Technical Descriptions**
- For each gameplay level, write:
  - Purpose in the vertical slice
  - Key technical features (materials, PCG, etc.)
  - Performance notes (triangles, draw calls, etc.)

### Phase 4: Website Implementation (Cline Tasks)

**Task 4.1: Update HTML Structure**
- Add "Vertical Slice" section to `application-hub.html`
- Reorganize "Environments" section
- Add "Hybrid Pipeline" section
- Update navigation

**Task 4.2: Update CSS**
- Add styles for new sections
- Ensure readability (font sizes, contrast)
- Mobile responsiveness

**Task 4.3: Update Content**
- Replace placeholder text with real content
- Add technical descriptions
- Add pipeline documentation

**Task 4.4: Deploy**
- Commit changes to `my-site-deploy`
- Push to GitHub
- Verify GitHub Pages deploy

---

## Blackbox AI Task List

The following tasks require blackbox AI (manual Blender/UE session setup):

### Blender Tasks
1. **Start Blender MCP addon** — Open Blender, enable the MCP addon on port 9878
2. **Capture character turntable** — If not already done, capture Melusina turntable renders
3. **Capture environment concepts** — Capture any Blender environment concept renders
4. **Capture material lookdev** — Capture material lookdev renders from Blender

### UE Tasks
1. **Start UE MCP** — Ensure UE is running and MCP server is active on port 9316
2. **List all levels** — Use UE MCP to list all levels in `Content/Maps/`
3. **Capture gameplay level renders** — For each gameplay level:
   - Open level in UE
   - Capture beauty render
   - Capture wireframe view
   - Capture material breakdown
   - Capture PCG overlay
4. **Map props to levels** — Identify which props appear in which levels
5. **Capture prop-in-context renders** — Show props in their gameplay context

### Documentation Tasks
1. **Create prop-to-level mapping** — Document which props appear in which levels
2. **Create level-to-gameplay-beat mapping** — Document which level corresponds to which minute in the vertical slice
3. **Write technical descriptions** — For each level, write technical notes

---

## Cline Task List

The following tasks can be done by Cline (no manual session setup required):

### Website Structure
1. **Update `application-hub.html`** — Add "Vertical Slice" section, reorganize "Environments"
2. **Add "Hybrid Pipeline" section** — Create new section explaining Blender → UE flow
3. **Update navigation** — Add links to new sections
4. **Update CSS** — Add styles for new sections, ensure readability

### Content Integration
1. **Integrate new renders** — Once blackbox AI captures renders, integrate them into the website
2. **Update prop section** — Map props to gameplay levels
3. **Update character section** — Add Sir Melodious, map to gameplay
4. **Write technical descriptions** — Add technical notes to each section

### Deployment
1. **Commit changes** — Commit all website updates to `my-site-deploy`
2. **Push to GitHub** — Push to `fromage3900/my-site`
3. **Verify deploy** — Check GitHub Pages deploy status

---

## Preservation Rules

**DO NOT TOUCH:**
- All EEVEE renders in `character/` directory
- All Melusina renders (beauty, glam, wireframe, turntable, etc.)
- All material loops (these demonstrate the Substrate Toon master material)
- All nightshift material isolates
- All melodia-game-ui textures

**These are current and demonstrate the hybrid pipeline (Blender EEVEE + UE Substrate Toon).**

---

## Success Criteria

The website overhaul is complete when:
1. ✅ The "First 20 Minutes" vertical slice is clearly documented
2. ✅ Each gameplay level has beauty renders, wireframe views, and technical notes
3. ✅ The hybrid pipeline (Blender → UE) is explicitly documented
4. ✅ Props are mapped to gameplay levels
5. ✅ Sir Melodious companion is documented
6. ✅ All EEVEE/Melusina renders are preserved
7. ✅ The website is deployed to GitHub Pages
8. ✅ A recruiter can understand the game's core loop from the website

---

## Next Steps

1. **User Decision:** Confirm this plan
2. **Blackbox AI:** Start Blender/UE sessions and capture renders
3. **Cline:** Begin website structure updates (can be done in parallel)
4. **Integration:** Once renders are captured, integrate into website
5. **Deploy:** Push to GitHub Pages

---

## Notes

- The current website is **recruiter-ready** in terms of visual polish and technical proof
- The overhaul is about **aligning content with the actual gameplay experience**
- The hybrid pipeline is a **key differentiator** and should be prominently documented
- EEVEE/Melusina renders are **current and should not be modified**
- The first 20 minutes vertical slice is the **primary demo** for recruiters

---

**End of Plan**