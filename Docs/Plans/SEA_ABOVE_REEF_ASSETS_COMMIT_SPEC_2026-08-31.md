# Sea Above Reef Assets Commit Spec — 2026-08-31

**Scope:** 80+ newly added Sea Above reef assets (meshes, materials, textures) in Content/EnvSandbox/Monoliths/SeaAbove/Prototype/Reef/

## Files to Commit

### Meshes (15)
- SM_Clutter_PebbleSet, SM_Clutter_SeaWeed, SM_Clutter_SpiralShell, SM_Clutter_Starfish
- SM_Coral_Brain, SM_Coral_Fan, SM_Coral_ReefCluster, SM_Coral_Staghorn, SM_Coral_Table, SM_Coral_TubeSponges
- SM_DrownedOrgan, SM_Flora_Chime, SM_Flora_Fern, SM_Flora_Reed
- SM_Island_A, SM_Island_B, SM_Island_C
- SM_Kelp_Cluster, SM_Kelp_Mid, SM_Kelp_Tall
- SM_Leviathan, SM_RockChunk_L, SM_RockChunk_M

### Materials (6)
- MI_SeaAbove_Cloth_Shroud, MI_SeaAbove_CoralSkin, MI_SeaAbove_CoralSkin_2S
- MI_SeaAbove_Kelp, MI_SeaAbove_Sand, MI_SeaAbove_WetRock

### Textures (55+)
- T_DressShorewake_ScaleMask, T_DressShorewake_ScaleShimmer
- T_Jelly_ArmLogic_LUT, T_Jelly_Bell_BaseColor, T_Jelly_Bell_CanalMask, T_Jelly_Bell_Irid_Mottle, T_Jelly_Bell_Normal, T_Jelly_Bell_Opacity
- T_Jelly_Biolum_LUT, T_Jelly_Iridescence_LUT, T_Jelly_Nematocyst_Glints
- T_Leviathan_Bone_BaseColor, T_Leviathan_Bone_Normal, T_Leviathan_Bone_Roughness
- T_Organ_Pipe_BaseColor, T_Organ_Pipe_Emissive, T_Organ_Pipe_Normal
- T_SeaAbove_BarnacleCrust_Mask, T_SeaAbove_Caustics, T_SeaAbove_ClutterFloor_Mask
- T_SeaAbove_Clutter_Atlas + 12 clutter variants (BarnacleCluster, BottleShard, Bubbles, ClamPair, CoralTwig, Driftwood, Pebbles, Scallop, SeaGlass, SeaweedSprig, SpiralShell, Starfish)
- T_SeaAbove_CoralSkin_Albedo, T_SeaAbove_CoralSkin_EmissiveMask, T_SeaAbove_CoralSkin_Normal
- T_SeaAbove_Droplet_Atlas, T_SeaAbove_Foam_Mask, T_SeaAbove_KelpSway_LUT
- T_SeaAbove_Membrane_Reveal, T_SeaAbove_Membrane_Ripple_N, T_SeaAbove_PulseBand_LUT
- T_SeaAbove_Sand_Albedo, T_SeaAbove_Sand_Height, T_SeaAbove_Sand_Normal, T_SeaAbove_Sand_RippleMask, T_SeaAbove_Sand_WetMask
- T_SeaAbove_Sediment_Ramp
- T_SeaAbove_ShellMask_Conch, T_SeaAbove_ShellMask_Nautilus, T_SeaAbove_ShellMask_SandDollar, T_SeaAbove_ShellMask_Scallop
- T_SeaAbove_WetRock_Albedo, T_SeaAbove_WetRock_Normal, T_SeaAbove_WetRock_Wetline

## Justification

- All assets are authored (not generated)
- Part of Sea Above reef biome (P0 content)
- Complements existing Sea Above reef materialization scripts
- Referenced by seaabove_reef_shadowdream_mis.json audit

## Commit Message

```
feat(seaabove): add reef biome assets (15 meshes, 6 materials, 55+ textures)
```

## Safety

- All files are newly added (A status in git status)
- No existing tracked files modified
- No CLAUDE.md never-touch conflicts
- LFS tracking for .uassets is configured

## Command

```bash
git add Content/EnvSandbox/Monoliths/SeaAbove/Prototype/Reef/
git commit -m "feat(seaabove): add reef biome assets (15 meshes, 6 materials, 55+ textures)"
```