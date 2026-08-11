# Commit Plan for Untracked Paths — July 2026

**Generated:** 2026-07-17  
**Untracked Paths:** ~70 files  

---

## Untracked Path Groups from `git status`

### Group 1: Roguelike Battle System Data (92 files)
**Path:** `Imports/Data/...`  
**Rationale:** Battle system data tables for enemy variants, skill charts, room modifiers — scoped for vertical slice implementation.

| Folder | Count | Purpose |
|--------|-------|---------|
| `Imports/Data/Charts/` | 24 files | Enemy skill chart variants |
| `Imports/Data/EnemyVariants/` | 48 files | MelodySlime enemy configurations |
| `Imports/Data/RoomMods/` | 20 files | Procedural room modifier configs |

**Suggested Commit Message:**
```
feat(battle-system): add enemy variant charts and room modifiers for roguelike mode

- 24 enemy skill charts for Arcane, Forte, Gale, Radiant, Stone, Tide, Umbral types
- 48 enemy variant configurations for MelodySlime variants
- 20 room modifiers for procedural level generation
- Supporting data tables from AI content daemon
```

---

### Group 2: UI Widget Blueprint Specs (14 files)
**Path:** `Imports/UI/Specs/...`  
**Rationale:** Cursor lane deliverables - WBP specs for filigree atlas and resonance UI.

| File | Type | Purpose |
|------|------|---------|
| `Imports/UI/Specs/WBP_Battle_Command.md` | WBP spec | Battle command widget |
| `Imports/UI/Specs/WBP_Battle_Results.md` | WBP spec | Battle results display |
| `Imports/UI/Specs/WBP_BlessingBurden.md` | WBP spec | Blessing burden indicator |
| `Imports/UI/Specs/WBP_DissonanceBanner.md` | WBP spec | Dissonance banner widget |
| `Imports/UI/Specs/WBP_FieldHUD.md` | WBP spec | Field HUD layout |
| `Imports/UI/Specs/WBP_IntensityWarning.md` | WBP spec | Intensity warning display |
| `Imports/UI/Specs/WBP_MainMenu.md` | WBP spec | Main menu widget |
| `Imports/UI/Specs/WBP_MenuButton.md` | WBP spec | Menu button component |
| `Imports/UI/Specs/WBP_ResonanceBond.md` | WBP spec | Resonance bond widget |
| `Imports/UI/Specs/WBP_SaveLoad.md` | WBP spec | Save/load interface |
| `Imports/UI/Specs/WBP_UltCutIn.md` | WBP spec | Ultimate cut-in animation |
| `Imports/UI/Specs/_MOTION_CHANNELS.md` | Motion spec | Motion channel definitions |
| `Imports/UI/Specs/_TOKENS_AND_ATOMS.md` | Token spec | UI token/atom mapping |

**Suggested Commit Message:**
```
docs(ui): add WBP specs for battle system and menu interfaces

- 12 widget blueprint specifications for upcoming UI work
- Motion channels and token definitions for cursor lane
- Filigree atlas preparation ready for editor import
```

---

### Group 3: Asset Exports (8 files)
**Path:** `UpdatedShirt.*`, `KitbashExport/`  
**Rationale:** Character texture updates and mesh exports needing source control.

| File | Type | Purpose |
|------|------|---------|
| `UpdatedShirt.fbx` | FBX mesh | Updated shirt geometry |
| `Melusina'sUpdatedShirt_Alpha.png` | Texture | Shirt alpha map |
| `Melusina'sUpdatedShirt_BaseColor.png` | Texture | Shirt base color |
| `Melusina'sUpdatedShirt_Displacement.png` | Texture | Shirt displacement |
| `Melusina'sUpdatedShirt_Emission.png` | Texture | Shirt emission map |
| `Melusina'sUpdatedShirt_Metallic.png` | Texture | Shirt metallic map |
| `Melusina'sUpdatedShirt_Normal.png` | Texture | Shirt normal map |
| `Melusina'sUpdatedShirt_Roughness.png` | Texture | Shirt roughness map |

**Suggested Commit Message:**
```
assets(character): add updated Melusina shirt textures and FBX

- Complete PBR texture set for shirt material update
- FBX geometry for character customization support
```

---

### Group 4: Audit Reports (5 files)
**Path:** `Saved/Audit/*.json`  
**Rationale:** Fresh audit data from disk-based validation runs.

| File | Type | Purpose |
|------|------|---------|
| `Saved/Audit/dupe_root_hashdiff.json` | Audit | Full hash-diff analysis |
| `Saved/Audit/mi_master_integrity_disk.json` | Audit | MI-master mapping report |
| `Saved/Audit/static_mesh_inventory.json` | Audit | Mesh inventory triage |
| `Saved/Audit/sdf_project_review.json` | Audit | SDF master analysis |
| `Saved/Audit/melusina_asset_integrity.json` | Audit | Melusina asset audit |

**Suggested Commit Message:**
```
docs(audit): add validation reports for release readiness

- Hash-diff analysis of duplicate roots
- Static mesh inventory triage (174 flagged)
- Material instance integrity check
- SDF master review for porting
- Melusina asset integrity verification
```

---

### Group 5: Deployment Infrastructure (15 files)
**Path:** `my-site-clean/`, `_github_deploy/`  
**Rationale:** Static site generation and deployment infrastructure.

| Path | Status | Notes |
|------|--------|-------|
| `my-site-clean/wix/sakura-case-study.html` | Modified | Sakura case study page |
| `my-site-clean/wix/` | Directory | Wix integration files |
| `my-site-clean/.wix/` | Modified | Wix config updates |
| `my-site-clean/application/` | Modified | Site application logic |
| `my-site-clean/components/` | Modified | Reusable components |
| `my-site-clean/content/` | Modified | Site content files |
| `my-site-clean/projects/` | Modified | Project showcase pages |
| `my-site-clean/public/` | Modified | Static assets |
| `my-site-clean/src/` | Modified | Source files |
| `my-site-clean/tools/` | Modified | Build tools |

**Suggested Commit Message:**
```
chore(deploy): update site infrastructure for sakura case study

- Wix site integration files and case study page
- Application and component updates
- Generated deployment assets
```

---

### Group 6: Research Assets (4 files)
**Path:** `research/`, `Melodia_Portfolio_Stage_v*.blend`  
**Rationale:** Blender research and portfolio stage files.

| File | Type | Purpose |
|------|------|---------|
| `Melodia_Portfolio_Stage_v16_SIR_VISIBLE.blend` | Blend file | Portfolio stage v16 |
| `Melodia_Portfolio_Stage_v17_SIR_VISIBLE.blend` | Blend file | Portfolio stage v17 |
| `Melodia_Portfolio_Stage_v18_SIR_VISIBLE.blend` | Blend file | Portfolio stage v18 |
| `research/` | Directory | Research notes and tests |

**Suggested Commit Message:**
```
research(blender): add portfolio stage blend files and research assets

- Stage v16-18 for surreal architecture research
- Research documentation and test files
```

---

## Commit Grouping Summary

| Group | Files | Scope |
|-------|-------|-------|
| 1 | 92 | Battle System Data (Charts + EnemyVariants + RoomMods) |
| 2 | 13 | UI Widget Blueprint Specs |
| 3 | 8 | Asset Exports (Shirt textures + FBX) |
| 4 | 5 | Audit Reports |
| 5 | 10+ | Deployment Infrastructure (my-site-clean) |
| 6 | 3 | Research Assets (Blend files) |
| **Total** | **~131 untracked paths** | **Scoped commits** |

*Note: Counts are approximate; actual `git status` will provide precise numbers.*

---

## Implementation Order

### Phase 1: Documentation & Audit
```bash
git add Saved/Audit/*.json
git commit -m "docs(audit): add validation reports for release readiness"
```

### Phase 2: Core Systems
```bash
git add Imports/Data/
git commit -m "feat(battle-system): add enemy variant charts and room modifiers"
```

### Phase 3: UI Integration
```bash
git add Imports/UI/
git commit -m "docs(ui): add WBP specs for battle system and menu interfaces"
```

### Phase 4: Assets
```bash
git add UpdatedShirt.fbx "Melusina'sUpdatedShirt_*.png"
git commit -m "assets(character): add updated Melusina shirt textures and FBX"
```

### Phase 5: Research & Deployment
```bash
git add Melodia_Portfolio_Stage_v*.blend research/
git add my-site-clean/
git commit -m "research(deploy): add portfolio stages and site updates"
```

---

## Files to Exclude from Commits

- `_ghpages_deploy_tmp` — Temporary directory, should be in `.gitignore`
- `_ollama_experiments/` — Experimental data, excluded per `.gitignore`
- `deploy/ollama_slice_content_daemon.py` — Runtime script, not needed
- `*.log` in root — Log files (only `deploy/ollama_slice_*.log` are tracked)