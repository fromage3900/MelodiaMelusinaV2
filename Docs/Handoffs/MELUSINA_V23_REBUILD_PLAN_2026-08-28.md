# Melusina v23 Rebuild Plan — 2026-08-28

**Author:** Melusina (Hermes agent, z-ai/glm-5.2)
**Date:** 2026-08-28
**Status:** Planning — file search in progress, editor needed for import

---

## Current Melusina Character State in UE

**Path:** `Content/Melodia/Characters/Melusina/`

The UE project has these Melusina assets (modified, untracked, or committed):
- `ABP_Melusina_Current.uasset` — Animation Blueprint (modified in git)
- `Hair/ABP_Melusina_WaterHair.uasset` — Hair animation BP (modified in git)
- Additional meshes, textures, and materials under this path

The character is functional in-editor but the user wants to rebuild from the v23 Blender source.

---

## V23 Blend File Search

**From the 2026-08-28 session:** The user found `.melodia_v23*` files at `C:\Users\froma\` but they were only 66K — compressed/LFS placeholders, not the real ~73MB .blend file.

**Search locations (to run when filesystem is accessible):**
1. `C:\Users\froma\` — `.melodia_v23*` (66K LFS placeholders, confirmed)
2. `C:\Users\froma\Desktop\` — check for .blend files
3. `C:\Users\froma\OneDrive\Desktop\` — check for .blend files
4. `C:\EnvironmentPortfolio\` — check for .blend files in the portfolio root
5. `C:\EnvironmentPortfolio\BS_GodFile\Exports\PortfolioStages\` — previous export stages
6. `C:\EnvironmentPortfolio\BS_GodFile\Content\Melodia\Characters\Melusina\` — current UE assets
7. Blender default save locations — `C:\Users\froma\Documents\` or Blender's temp

**The real V23 file** is likely:
- A .blend file larger than 1MB (the user mentioned ~73MB)
- Named something like `Melusina_v23.blend` or `melodia_v23.blend`
- In a Blender working directory, not the UE project

---

## Rebuild Plan

### Phase 1: Find the V23 Source (offline, no editor)

1. Search `C:\Users\froma\` recursively for `*.blend` files > 1MB
2. Search `C:\EnvironmentPortfolio\` recursively for `*.blend` files
3. Check Blender's recent files (if Blender is installed, check `%APPDATA%\Blender\`)
4. Check OneDrive sync locations
5. If the real .blend is found, note its path and size
6. If not found, ask the user where the V23 file is

### Phase 2: Verify Current UE State (offline)

1. List all files under `Content/Melodia/Characters/Melusina/`
2. Check what .uasset, .fbx, .png exist
3. Note which are modified (git) vs untracked
4. Identify the current import path (where did the current mesh come from?)

### Phase 3: Export from Blender (needs Blender, not UE)

1. Open the V23 .blend in Blender 5.2
2. Export as FBX with these settings (matching the UE import conventions):
   - Y-up (Blender default, UE expects this)
   - Forward: -Z forward (Blender default)
   - Apply Scalings: FBX All
   - Smoothing: Face
   - Include: Armature, Mesh, UVs, Materials, Textures
3. Export to a temp path, NOT directly into the Content/ tree
4. Name: `Melusina_v23_Export.fbx`

### Phase 4: Import into UE (needs editor)

**CAUTION (AGENTS.md):** Never run FBX import into a path that already holds an asset — it creates a redirector over the existing asset.

1. **Back up the current Melusina assets** — copy `Content/Melodia/Characters/Melusina/` to `CompatibilityLabs/Melusina_v22_backup_2026-08-28/`
2. **Import to a NEW path** — e.g., `Content/Melodia/Characters/Melusina/v23/`
3. Import settings:
   - Skeletal Mesh + Armature
   - Import Materials + Textures
   - Use the existing skeleton if compatible (or create new)
4. After import, verify:
   - Mesh renders correctly
   - Materials apply
   - Skeleton/skinning is correct
   - ABP_Melusina_Current can use the new mesh (re-target if needed)
5. Update ABP_Melusina_Current to point to the v23 mesh
6. Save all dirty packages

### Phase 5: Verify (needs PIE)

1. PIE with Melusina in the level
2. Confirm mesh renders, animations play, materials apply
3. Confirm no crash (the ACCESS_VIOLATION crash fix is already committed)
4. Check the rhythm battle — does Melusina's unique skill work with v23?

---

## Safety Rules (from AGENTS.md)

1. **Never** run `git clean -fd` — deletes untracked Content/ files permanently
2. **Never** run `git checkout -- .` — reverts all working changes
3. **Never** import FBX into a path that already holds an asset — creates a dead redirector
4. **Always** copy current assets to a backup before importing new ones
5. **Always** import to a new path, then update references
6. **One editor instance** — check `Get-Process UnrealEditor` and port 9316 before starting

---

## Next Action

The V23 .blend file must be found first. Run the filesystem search in Phase 1. If the file is on an external drive or cloud sync that's not mounted, the user needs to mount it.
