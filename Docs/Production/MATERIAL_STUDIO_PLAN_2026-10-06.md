# Material Studio & Portfolio Preview Staging Plan

**Date:** 2026-10-06
**Project:** Melodia Melusina V2 — BS_GodFile
**Scope:** Fix broken texture references, restore missing textures, stage material studio and portfolio preview

---

## 1. Current State

### Texture Inventory
| Category | Status | Count |
|----------|--------|-------|
| Cymatics | ✅ Restored | 148 |
| PBR Sets | ✅ Restored | 24 |
| Melodia | ✅ Restored | 17 |
| Melusina | ✅ Restored | 6 |
| Utility | ⚠️ Partial | 5 |
| Defaults | ❌ Missing | 0 |
| Atlantis | ❌ Missing | 0 |
| Rhinestone | ❌ Missing | 0 |

### Broken References
- **1,694 broken texture references** across 1,026 material instances
- Most common missing: `T_Default_Albedo`, `T_Default_Normal`, `T_Default_ORM`, `T_Neutral_Normal`, `T_Neutral_ORM`
- Atlantis textures (KB3D_ATL_*) completely missing
- Rhinestone textures (Bling_Rhinestone*) completely missing

---

## 2. Recovery Plan

### Phase 1: Restore Missing Textures (30 min)

#### 2.1 Utility Textures (5 files)
**Source:** `.claude/worktrees/eyewear-editorial-0912/Content/EnvSandbox/Textures/Utility/`
**Target:** `Content/EnvSandbox/Textures/Utility/`
- `T_Neutral_Height.uasset`
- `T_Neutral_Metallic.uasset`
- `T_Neutral_Normal.uasset`
- `T_Neutral_ORM.uasset`
- `T_Neutral_Roughness.uasset`

#### 2.2 Defaults Textures (3+ files)
**Source:** Unknown — may need to be created or found in another worktree
**Target:** `Content/EnvSandbox/Textures/Defaults/`
- `T_Default_Albedo.uasset`
- `T_Default_Normal.uasset`
- `T_Default_ORM.uasset`

#### 2.3 Atlantis Textures (100+ files)
**Source:** Unknown — may be in a different worktree or backup
**Target:** `Content/EnvSandbox/Textures/Atlantis/`
- All `T_KB3D_ATL_*` textures

#### 2.4 Rhinestone Textures (15+ files)
**Source:** Unknown — may need to be re-imported or found in Downloads
**Target:** `Content/EnvSandbox/Textures/BlingVol3/` or similar
- All `T_Bling_Rhinestone*` textures

### Phase 2: Fix Material Instances (20 min)

#### 2.1 Re-link Broken References
For each material instance with broken references:
1. Open in UE Material Editor
2. Re-assign the correct texture
3. Save

#### 2.2 Create Missing Default Textures
If `T_Default_*` textures cannot be found:
1. Create simple 1x1 pixel textures in UE
2. Assign to material instances
3. Save

### Phase 3: Material Studio Organization (15 min)

#### 3.1 Folder Structure
```
Content/EnvSandbox/
├── Materials/
│   ├── Functions/          # Material functions (MF_*)
│   ├── Instances/          # Material instances (MI_*)
│   │   ├── Architecture/   # Architecture-specific
│   │   ├── Atlantis/       # Atlantis-themed
│   │   ├── BlingVol3/      # Rhinestone/bling
│   │   ├── Character/      # Character materials
│   │   ├── Copernicus/     # Cymatic materials
│   │   ├── Environment/    # Environment/PBR
│   │   ├── Flora/          # Plant materials
│   │   ├── Foliage/        # Foliage materials
│   │   ├── FromMasters/    # Derived from masters
│   │   ├── Gemstone/       # Gemstone materials
│   │   ├── Glitter/        # Glitter/sparkle
│   │   ├── Grotto/         # Grotto-themed
│   │   ├── Kenney/         # Kenney assets
│   │   ├── Landscape/      # Landscape materials
│   │   ├── Validation/     # Validation/test
│   │   └── ...
│   ├── Masters/            # Master materials (M_*)
│   └── ToonProfiles/       # Toon profiles (TP_*)
├── Textures/
│   ├── Alphas_Melodia/     # Alpha masks
│   ├── Alphas_Sparkles/    # Sparkle alphas
│   ├── Atlantis/           # Atlantis textures
│   ├── Copernicus/         # Cymatic textures
│   ├── Defaults/           # Default textures
│   ├── Eigenplate/         # Eigenplate textures
│   ├── Melodia/            # Melodia textures
│   ├── Melusina/           # Melusina textures
│   ├── MelusinaAnimated/   # Animated textures
│   ├── PackTextures/       # Packed textures
│   ├── PBR_Sets/           # PBR texture sets
│   ├── PearlWoven_Painterly_4K/
│   ├── SurrealCobble/
│   ├── SurrealFlora/
│   └── Utility/            # Utility textures
```

#### 3.2 Naming Conventions
- Textures: `T_<Category>_<Name>_<Type>.uasset`
  - Types: `BaseColor`, `Normal`, `ORM`, `Roughness`, `Metallic`, `Height`, `Opacity`, `Emissive`
- Material Instances: `MI_<Category>_<Name>.uasset`
- Material Functions: `MF_<Name>.uasset`
- Master Materials: `M_<Name>.uasset`
- Toon Profiles: `TP_<Name>.uasset`

### Phase 4: Portfolio Preview Staging (15 min)

#### 4.1 Select Showcase Materials
Choose 10-15 best materials for portfolio:
1. **Cymatic Marble** — `MI_Copernicus_CymaticMarble`
2. **Cymatic Reactive** — `MI_Copernicus_CymaticReactive`
3. **Hero Gem Cymatic** — `MI_HeroGem_Cymatic`
4. **Klein Veil Cymatic** — `MI_KleinVeil_CymaticReactive`
5. **Sea Above Kelp Cymatic** — `MI_Copernicus_SeaAbove_KelpCymaticSheen`
6. **Bling Rhinestone** — `MI_T_Bling_Rhinestone01` (if restored)
7. **Toon Character** — `MI_Toon_Character`
8. **Toon Environment** — `MI_Toon_Environment`
9. **Toon Face** — `MI_Toon_Face`
10. **Toon Hair** — `MI_Toon_Hair`
11. **Toon Glass** — `MI_Toon_Glass`
12. **Toon Gold** — `MI_Toon_Gold`
13. **Toon Hero** — `MI_Toon_Hero`
14. **Toon Landscape** — `MI_Toon_Landscape`
15. **Toon Melusina** — `MI_Toon_Melusina`

#### 4.2 Create Preview Scenes
For each showcase material:
1. Create a simple preview scene (sphere or plane)
2. Apply the material
3. Set up lighting (key + fill + rim)
4. Render a beauty shot (1920x1080)
5. Save to `Saved/PortfolioPreviews/`

#### 4.3 Generate Contact Sheet
Create a contact sheet with all preview renders:
- Grid layout (3x5 or 4x4)
- Material name labels
- Save as `Saved/PortfolioPreviews/ContactSheet.png`

---

## 3. Execution Order

### Step 1: Restore Utility Textures (5 min)
```bash
cp -r .claude/worktrees/eyewear-editorial-0912/Content/EnvSandbox/Textures/Utility/ \
      Content/EnvSandbox/Textures/Utility/
```

### Step 2: Find and Restore Missing Textures (20 min)
- Search all worktrees for missing textures
- Search Downloads folder
- Search G: drive
- Re-import from source if needed

### Step 3: Fix Material Instances in UE (20 min)
- Open UE
- Use Material Editor to re-link broken references
- Save all fixed materials

### Step 4: Organize Material Studio (15 min)
- Verify folder structure
- Rename any misnamed assets
- Create missing folders

### Step 5: Stage Portfolio Previews (15 min)
- Select showcase materials
- Create preview scenes
- Render beauty shots
- Generate contact sheet

---

## 4. Missing Textures Summary

| Texture Category | Count | Status | Action Needed |
|-----------------|-------|--------|---------------|
| Utility | 5 | ⚠️ In worktree | Copy to main |
| Defaults | 3+ | ❌ Missing | Find or create |
| Atlantis | 100+ | ❌ Missing | Find or re-import |
| Rhinestone | 15+ | ❌ Missing | Find or re-import |
| Melusina/LandscapeGrayscale | 2 | ❌ Missing | Find or re-import |
| Melusina/Soil | 2 | ❌ Missing | Find or re-import |

---

## 5. Success Criteria

- [ ] All 1,694 broken references fixed
- [ ] All material instances show correct textures in UE
- [ ] Material studio folder structure clean and organized
- [ ] 10-15 portfolio preview renders completed
- [ ] Contact sheet generated
- [ ] All changes committed to git

---

## 6. Risks & Mitigation

| Risk | Impact | Mitigation |
|------|--------|------------|
| Missing textures cannot be found | High | Create placeholder textures, re-import from source |
| Material instances too many to fix manually | Medium | Use batch re-linking script in UE |
| Portfolio preview renders take too long | Low | Use lower resolution (1280x720) for previews |
| Git LFS storage limit reached | Medium | Check LFS usage before committing |

---

## 7. Next Steps

1. **Immediate:** Restore Utility textures from worktree
2. **Short-term:** Search for missing Atlantis and Rhinestone textures
3. **Medium-term:** Fix all broken material references in UE
4. **Long-term:** Stage portfolio previews and generate contact sheet
