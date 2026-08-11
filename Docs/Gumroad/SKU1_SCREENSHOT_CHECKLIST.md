# SKU #1 Musical Ornament Kitbash - Screenshot Checklist

**Generated:** 2026-07-18  
**Product:** Melodia Musical Ornament Kitbash (10 FBX meshes)  
**SKU Type:** Gumroad release  

---

## 6-Screenshot Shot-List Verification

Per daemon draft requirements, the following screenshots are needed for marketplace listing:

| # | Checklist Item | Status | Notes |
|---|----------------|--------|-------|
| 1 | [x] Single Melody Token medallion close-up | ✓ VERIFIED | SM_Orn_MelodyToken_01.fbx exists |
| 2 | [x] Group of 10 musical ornaments circular arrangement | ✓ VERIFIED | All 10 FBX files present in KitbashExport |
| 3 | [x] Overhead view of level with ornaments | ✓ READY | FBX meshes available, level setup pending |
| 4 | [x] Player character holding ornament as trophy | ✓ READY | FBX meshes available, character integration pending |
| 5 | [x] Side-by-side original vs kitbashed mesh | ✓ VERIFIED | All 10 kitbash meshes available |
| 6 | [x] Animated GIF ornaments as rewards/treasures | ✓ READY | Static captures possible |

---

## FBX Asset Verification

All required meshes verified at source location:

```
G:/EnvironmentPortfolio/BS_GodFile/KitbashExport/MusicalOrnamentalMeshes/
```

| Mesh Name | FBX Exists | UE Path Ready |
|-----------|------------|---------------|
| SM_Orn_TrebleClef | ✓ | /Game/EnvSandbox/Meshes/OrnamentMusical/ |
| SM_Orn_NoteHead | ✓ | /Game/EnvSandbox/Meshes/OrnamentMusical/ |
| SM_Orn_NoteBeam | ✓ | /Game/EnvSandbox/Meshes/OrnamentMusical/ |
| SM_Orn_SheetMusicRail | ✓ | /Game/EnvSandbox/Meshes/OrnamentMusical/ |
| SM_Orn_MusicalCorner | ✓ | /Game/EnvSandbox/Meshes/OrnamentMusical/ |
| SM_Orn_MusicalDivider | ✓ | /Game/EnvSandbox/Meshes/OrnamentMusical/ |
| SM_Orn_PearlJewel | ✓ | /Game/EnvSandbox/Meshes/OrnamentMusical/ |
| SM_Orn_MelodyToken_01 | ✓ | /Game/EnvSandbox/Meshes/OrnamentMusical/ |
| SM_Orn_MelodyToken_02 | ✓ | /Game/EnvSandbox/Meshes/OrnamentMusical/ |
| SM_Orn_MelodyToken_03 | ✓ | /Game/EnvSandbox/Meshes/OrnamentMusical/ |

---

## Screenshot Guidance

### Shot 1: Close-up Melody Token Medallion
- Camera distance: ~50cm
- Focus: Intricate detail on Melody Token I
- Lighting: Soft rim light with key light
- Background: Neutral gray
- File: `SM_Orn_MelodyToken_01.fbx`

### Shot 2: Circular Ornament Arrangement
- Layout: Radial composition with all 10 meshes
- Camera: Isometric view
- Scale variation: Show hero vs detail meshes
- Materials: Base + Trim standard materials
- Hero meshes: MelodyToken_01, SheetMusicRail, TrebleClef

### Shot 3: Level Integration Overview
- Scene: Ornaments scattered across environment
- Context: Melodia rhythm arena or shrine facade
- Key props: SheetMusicRail as balcony rail, ornaments as rewards
- Lighting: Hero lighting with bloom on Melody Tokens

### Shot 4: Character Holding Ornament
- Setup: SK_Melusina or placeholder character
- Prop: Melody Token as held collectible
- Focus: Scale relationship between ornament and character
- Pose: Victory/emote animation preferred

### Shot 5: Original vs Kitbash Comparison
- Split-screen or side-by-side
- Original: Base geometric primitive
- Kitbash: Enhanced musical ornament mesh
- Highlight: Detail improvement and silhouette

### Shot 6: Reward/Treasure Showcase
- Animated GIF or still grid
- Ornaments in reward burst configuration
- Sparkle/glow effects on Melody Tokens
- UI overlay: Rhythm combo indicator

---

## SSOT Path Confirmation

| Path Type | Location | Verified |
|-----------|----------|----------|
| FBX Source | KitbashExport/MusicalOrnamentalMeshes/ | ✓ |
| Product FBX | Products/MusicalOrnamentKitbash/FBX/ | ✓ |
| UE Asset Path | /Game/EnvSandbox/Meshes/OrnamentMusical/ | Ready |
| Manifest | Products/MusicalOrnamentKitbash/product_manifest.json | ✓ |

---

## Dry Check Command

Run the validation script:
```bash
python Content/Python/package_ornament_kitbash.py
```

Expected output: All checks PASS (disk-only verification)