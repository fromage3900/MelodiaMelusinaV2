# UE5.8 Gameplay Level Render Capture Checklist

**Session Date:** July 31, 2026  
**Agent:** BlackBoxAI  
**Status:** Ready for Capture

---

## Quick Reference

| Level | Description | Output Prefix |
|-------|-------------|---------------|
| L_KaleidoNave | Prologue · Bifrost Bridge | `L_KaleidoNave_*.png` |
| L_MelusinaMorning | Bedroom Interior | `L_MelusinaMorning_*.png` |
| ZenForestTest | Combat Smoke-Test | `ZenForestTest_*.png` |
| L_FallenMoon | Recursive Expedition | `L_FallenMoon_*.png` |

**Output Directory:** `my-site-deploy/generated/assets/landscape-loops/`

---

## Render Specifications

| Setting | Value |
|---------|-------|
| Resolution | 1920×1080 |
| Format | PNG (lossless) |
| Color Space | sRGB |
| Anti-aliasing | Enabled |
| Master Material | M_Master_Toon_Universal (Substrate Toon) |

---

## Level 1: L_KaleidoNave (Prologue · Bifrost Bridge)

### Level Description
- Short, controlled prologue/cutscene on floating bifrost-like bridge
- Establishes emotional Dissonance and Sir Melodious's distance/absence
- Open sky environment with floating bridge structure

### Capture Steps

- [ ] **Step 1:** Open `L_KaleidoNave` in UE5.8 Editor
- [ ] **Step 2:** Position camera for hero shot (bridge overview with open sky)
- [ ] **Step 3:** Enable Substrate Toon master material (M_Master_Toon_Universal)
- [ ] **Step 4:** Capture **beauty render** → Save as `L_KaleidoNave_beauty.png`
- [ ] **Step 5:** Switch to wireframe view mode
- [ ] **Step 6:** Capture **wireframe render** → Save as `L_KaleidoNave_wireframe.png`
- [ ] **Step 7:** Enable material ID view mode
- [ ] **Step 8:** Capture **material breakdown** → Save as `L_KaleidoNave_materials.png`
- [ ] **Step 9:** Enable PCG debug visualization
- [ ] **Step 10:** Capture **PCG overlay** → Save as `L_KaleidoNave_pcg.png`
- [ ] **Step 11:** Open stats panel (Ctrl+Shift+H)
- [ ] **Step 12:** Capture **performance stats** → Save as `L_KaleidoNave_stats.png`

### Verification

- [ ] All 5 renders saved to `my-site-deploy/generated/assets/landscape-loops/`
- [ ] File names match exactly: `L_KaleidoNave_beauty.png`, etc.
- [ ] Resolution is 1920×1080 for all renders
- [ ] Substrate Toon shading visible in beauty render

---

## Level 2: L_MelusinaMorning (Bedroom Interior)

### Level Description
- First controllable authored level
- Limited initially to Melusina's bedroom interior
- Contains bed/save sanctuary, empty companion perch, first failed Songcraft cue

### Capture Steps

- [ ] **Step 1:** Open `L_MelusinaMorning` in UE5.8 Editor
- [ ] **Step 2:** Position camera for hero shot (bedroom overview showing bed, perch, Songcraft area)
- [ ] **Step 3:** Enable Substrate Toon master material (M_Master_Toon_Universal)
- [ ] **Step 4:** Capture **beauty render** → Save as `L_MelusinaMorning_beauty.png`
- [ ] **Step 5:** Switch to wireframe view mode
- [ ] **Step 6:** Capture **wireframe render** → Save as `L_MelusinaMorning_wireframe.png`
- [ ] **Step 7:** Enable material ID view mode
- [ ] **Step 8:** Capture **material breakdown** → Save as `L_MelusinaMorning_materials.png`
- [ ] **Step 9:** Enable PCG debug visualization
- [ ] **Step 10:** Capture **PCG overlay** → Save as `L_MelusinaMorning_pcg.png`
- [ ] **Step 11:** Open stats panel (Ctrl+Shift+H)
- [ ] **Step 12:** Capture **performance stats** → Save as `L_MelusinaMorning_stats.png`

### Verification

- [ ] All 5 renders saved to `my-site-deploy/generated/assets/landscape-loops/`
- [ ] File names match exactly: `L_MelusinaMorning_beauty.png`, etc.
- [ ] Resolution is 1920×1080 for all renders
- [ ] Substrate Toon shading visible in beauty render

---

## Level 3: ZenForestTest (Combat Smoke-Test Map)

### Level Description
- Combat smoke-test map
- Used until bedroom and Dreamstate transitions are stable
- Forest environment with combat encounter areas

### Capture Steps

- [ ] **Step 1:** Open `ZenForestTest` in UE5.8 Editor
- [ ] **Step 2:** Position camera for hero shot (forest overview showing combat area)
- [ ] **Step 3:** Enable Substrate Toon master material (M_Master_Toon_Universal)
- [ ] **Step 4:** Capture **beauty render** → Save as `ZenForestTest_beauty.png`
- [ ] **Step 5:** Switch to wireframe view mode
- [ ] **Step 6:** Capture **wireframe render** → Save as `ZenForestTest_wireframe.png`
- [ ] **Step 7:** Enable material ID view mode
- [ ] **Step 8:** Capture **material breakdown** → Save as `ZenForestTest_materials.png`
- [ ] **Step 9:** Enable PCG debug visualization
- [ ] **Step 10:** Capture **PCG overlay** → Save as `ZenForestTest_pcg.png`
- [ ] **Step 11:** Open stats panel (Ctrl+Shift+H)
- [ ] **Step 12:** Capture **performance stats** → Save as `ZenForestTest_stats.png`

### Verification

- [ ] All 5 renders saved to `my-site-deploy/generated/assets/landscape-loops/`
- [ ] File names match exactly: `ZenForestTest_beauty.png`, etc.
- [ ] Resolution is 1920×1080 for all renders
- [ ] Substrate Toon shading visible in beauty render

---

## Level 4: L_FallenMoon (Recursive Expedition)

### Level Description
- Recursive expedition rooms (procedural)
- Seeded run recording: Room A → blessing/burden → Room B/encounter → exit
- Procedurally generated dungeon environment

### Capture Steps

- [ ] **Step 1:** Open `L_FallenMoon` in UE5.8 Editor
- [ ] **Step 2:** Position camera for hero shot (dungeon overview showing Room A, blessing/burden area, Room B)
- [ ] **Step 3:** Enable Substrate Toon master material (M_Master_Toon_Universal)
- [ ] **Step 4:** Capture **beauty render** → Save as `L_FallenMoon_beauty.png`
- [ ] **Step 5:** Switch to wireframe view mode
- [ ] **Step 6:** Capture **wireframe render** → Save as `L_FallenMoon_wireframe.png`
- [ ] **Step 7:** Enable material ID view mode
- [ ] **Step 8:** Capture **material breakdown** → Save as `L_FallenMoon_materials.png`
- [ ] **Step 9:** Enable PCG debug visualization
- [ ] **Step 10:** Capture **PCG overlay** → Save as `L_FallenMoon_pcg.png`
- [ ] **Step 11:** Open stats panel (Ctrl+Shift+H)
- [ ] **Step 12:** Capture **performance stats** → Save as `L_FallenMoon_stats.png`

### Verification

- [ ] All 5 renders saved to `my-site-deploy/generated/assets/landscape-loops/`
- [ ] File names match exactly: `L_FallenMoon_beauty.png`, etc.
- [ ] Resolution is 1920×1080 for all renders
- [ ] Substrate Toon shading visible in beauty render

---

## Final Validation

### File Count Check

- [ ] **20 total renders** captured (5 per level × 4 levels)

### Expected Files

```
my-site-deploy/generated/assets/landscape-loops/
├── L_KaleidoNave_beauty.png         □
├── L_KaleidoNave_wireframe.png      □
├── L_KaleidoNave_materials.png      □
├── L_KaleidoNave_pcg.png            □
├── L_KaleidoNave_stats.png          □
├── L_MelusinaMorning_beauty.png     □
├── L_MelusinaMorning_wireframe.png  □
├── L_MelusinaMorning_materials.png  □
├── L_MelusinaMorning_pcg.png        □
├── L_MelusinaMorning_stats.png      □
├── ZenForestTest_beauty.png         □
├── ZenForestTest_wireframe.png      □
├── ZenForestTest_materials.png      □
├── ZenForestTest_pcg.png            □
├── ZenForestTest_stats.png          □
├── L_FallenMoon_beauty.png          □
├── L_FallenMoon_wireframe.png       □
├── L_FallenMoon_materials.png       □
├── L_FallenMoon_pcg.png             □
└── L_FallenMoon_stats.png           □
```

### Quality Check

- [ ] All beauty renders have Substrate Toon shading active
- [ ] All wireframe renders show clear wireframe overlay
- [ ] All material renders show color-coded material IDs
- [ ] All PCG renders show debug visualization overlay
- [ ] All stats renders show readable performance metrics

---

## Next Steps After Capture

1. **Notify Cline** that renders are ready
2. **Cline will:**
   - Update `application-hub.html` with new renders
   - Update `recruiter-one-sheet.html` with new renders
   - Commit changes to `fromage3900/my-site` main branch
   - Verify GitHub Pages deploy

---

## Troubleshooting

### If level doesn't exist:
- Check `Content/Maps/` for exact level name
- Level may need to be created from template

### If Substrate Toon not working:
- Verify M_Master_Toon_Universal is assigned to materials
- Check that Substrate plugin is enabled

### If PCG debug not showing:
- Enable PCG debug visualization in viewport settings
- Check that PCG graphs are properly configured

---

**End of Checklist**
