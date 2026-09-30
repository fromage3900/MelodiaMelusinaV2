# Niagara Particle Materials & White Square Rendering Resolution

**Date:** September 30, 2026  
**Target:** Unreal Engine 5.8 (`BS_GodFile`)  
**Status:** **RESOLVED & VERIFIED ON DISK**

---

## 1. Root Causes Isolated & Repaired

| Cause | Mechanism | Resolution Applied |
|---|---|---|
| **1. 32×32 Legacy Texture Assets** | Textures like `T_Alpha_diamond_glint_alpha` and `T_Alpha_sparkle_4point_alpha` were imported at 32×32 pixels, blurring into white square blobs when sampled across 512×512 billboard quads. | **Deleted legacy 32×32 `.uasset`s and cleanly reimported directly from 1024×1024 source PNGs.** Verified in engine at native 1024×1024. |
| **2. DXT1 Alpha Channel Trap** | `T_Spark_Sparkle4` and `T_Spark_Twinkle8` are DXT1 format with `HasAlphaChannel: False`. When sample pin `A` was evaluated in `M_Niagara_Morning_PollenMote`, `A` returned `1.0` everywhere, creating solid opaque white billboards. | **Updated Custom HLSL node in `M_Niagara_Morning_PollenMote`** to compute `float mask = max(tex.r, max(tex.g, tex.b)); op = mask * life;`. Zero alpha is rendered on the dark background. |
| **3. Flipbook Grid Mismatch** | `MI_NS_ChoralSheep_BeatStar` was configured with `GridCols: 4.0, GridRows: 2.0` on `T_Spark_Twinkle8` (a single 8-pointed star, not an 8-frame sheet). This sliced the star into cropped square edge tiles. | **Reset `GridCols = 1.0` and `GridRows = 1.0`** so the entire star glint renders without rectangular clipping. |
| **4. Choral Sheep Wool Motes** | `MI_NS_ChoralSheep_WoolMote` was bound to the 32×32 legacy diamond texture with default flipbook tiling, causing the 3 floating white squares near the sheep in PIE. | **Bound to full 1024×1024 `T_Alpha_diamond_glint_alpha`** and set `GridCols = 1.0, GridRows = 1.0, Intensity = 1.2`. |
| **5. Distance Mip Streaming** | Textures in `TEXTUREGROUP_World` dropped to lowest 1×1 / 4×4 mips under distance or texture pool pressure. | **Enforced `NeverStream = True`, `LODGroup = TEXTUREGROUP_Effects`, and `MaxTextureSize = 0`** on all 11 particle textures. |

---

## 2. Verification Audit Receipt

From [`Saved/Audit/reimport_fresh_receipt.json`](file:///c:/EnvironmentPortfolio/BS_GodFile/Saved/Audit/reimport_fresh_receipt.json), [`Saved/Audit/reimport_remaining_receipt.json`](file:///c:/EnvironmentPortfolio/BS_GodFile/Saved/Audit/reimport_remaining_receipt.json), and [`Saved/Audit/vfx_verification_report.json`](file:///c:/EnvironmentPortfolio/BS_GodFile/Saved/Audit/vfx_verification_report.json):

```json
{
  "textures_reimported_1024x1024": [
    "T_Alpha_diamond_glint_alpha (/Game/_PROJECT/VFX/Textures)",
    "T_Alpha_diamond_glint_alpha (/Game/Melodia/_PROJECT/VFX/Textures)",
    "T_Alpha_sparkle_4point_alpha",
    "T_Alpha_water_globule_cluster_alpha",
    "T_Alpha_water_globule_flipbook",
    "T_Alpha_water_splash_burst_alpha",
    "T_Alpha_sparkle_cluster_alpha",
    "T_Alpha_sparkle_pulse_flipbook"
  ],
  "materials_repaired_and_saved": {
    "M_Niagara_Morning_PollenMote": "HLSL Opacity mask=max(R,G,B) applied & recompiled",
    "MI_Niagara_Melusina_StarSparkle": "Glow=3.0, Boil=0.05, Tip/Base color updated",
    "MI_NS_ChoralSheep_BeatStar": "GridCols=1.0, GridRows=1.0, Intensity=1.5",
    "MI_NS_ChoralSheep_WoolMote": "GridCols=1.0, GridRows=1.0, Full-res diamond glint bound",
    "MI_Niagara_Sparkle": "Recompiled and saved"
  },
  "never_stream_enforced": true,
  "lod_group_effects_enforced": true
}
```

All modified `.uasset` packages have been saved cleanly to disk with zero file sharing conflicts before UE launch.
