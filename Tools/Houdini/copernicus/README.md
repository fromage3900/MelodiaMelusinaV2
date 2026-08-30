# Melodia — Houdini Copernicus Pipeline (UE 5.8, Houdini 20.5+/22.0)

**Why this exists:** The current dress/terrain bake uses `Tools/Houdini/sea_above_reef/bake_rasterize_ao.py` — a custom `numpy+PIL` barycentric rasterizer that interpolates SOP VEX `thickness/curvature/AO` vertex attributes. It works and is deterministic (`SEED=20260828`), but it's **not** Copernicus, it bypasses Houdini's COP compositor, has no denoise, no deterministic COP caching, and no HDA async-cook path in UE. Infinity Nikki bar = versatile material setup + consistent bounced lighting + authored clipping; you don't get there with ad-hoc PIL.

This folder **replaces the PIL rasterizer with a true COP Network (Copernicus)** while keeping the same `SEED` + manifest discipline.

## Architecture

```
Owner FBX/USDZ (outside repo, hashed)
  │
  ├─ SOP Network (hython): boundary loops → tufts/plates → biharmonic capture
  │     dress_geometry_attrs.py (VEX: thickness/convex/concave, 3 attrs, OBJ vertex color R/G/B)
  │     dress_ao_vex.py (VEX: 64 rays, self-exclusion, vertex Ao)
  │
  ├─ COP Network (COPERNICUS — this folder):
  │     SOP Import COP → Labs Maps Baker COP → Attribute Interpolate COP (true barycentric, background 1.0)
  │       → Curvature directional COP → Thickness→AO composite → Denoise (OpenImageDenoise COP)
  │       → File Output COP (4K BC/N/ORM/Emissive/Mask, BC7/BC5, seed-locked)
  │     Manifest: seed, hython, COP version, file outputs, hash
  │
  └─ HDA: hda_melodia_lookdev.hda (async cook in UE via Houdini Engine FREE)
        params: Seed / Resolution / BakeSet / Denoise / ThicknessBias
        outputs: Nanite mesh + T_* + manifest (verify_tex_contract.py)
```

## What Copernicus buys you over PIL

| PIL rasterizer (current) | Copernicus COPs (this) |
|---|---|
| Python numpy loop, O(size²), no GPU | COP tiles + viewport feedback, GPU-accelerated |
| No denoise → AO speckles at 64 rays | OpenImageDenoise COP, 2s denoise |
| Background hard-coded 1.0, no control | Attribute Interpolate COP `background_value=1.0` explicit |
| Cannot author height→normal or curvature LUT in same network | Curvature/height→normal in same COP graph, WYSIWYG |
| No cache, re-rasterize every run | COP Cache COP, deterministic re-cook on `Seed` change only |

## Files in this folder

| File | Role |
|---|---|
| `copernicus_dress_bake.py` | Generates the `.hip` COP network Python (run `hython copernicus_dress_bake.py --hip melodia_dress_cop.hip`) |
| `hda_melodia_lookdev_spec.json` | HDA interface spec (parms, outputs, Unreal contract) |
| `melodia_dress_cop.hip.template.md` | Human-readable COP network walkthrough (node-by-node, matching `M_Master_Toon_Universal` Nikki lanes) |
| `copernicus_terrain_height_to_nanite.py` | Heightmap → Nanite mesh HDA generator (Gaea/World Machine → mesh, replaces Landscape) |
| `copernicus_fabric_sheen.py` | Velvet/silk sheen mask COP (Sheen for `T_FarawayMother_Gown/Mantle`) |

## Quick start (deterministic)

```bash
# 1. Generate COP HIP (Houdini 20.5+ or 22.0):
hython Tools/Houdini/copernicus/copernicus_dress_bake.py --seed 20260828 --size 1024

# 2. Open HIP, verify COP Output, click RENDER (File Output COP writes Saved/Audit/.../houdini_variants/)
# 3. Ingest into UE (existing flow — contract verified):
python Tools/ingest_sea_above_p0.py --verify

# 4. Assign in UE (Monolith live):
#    MI_Melusina_Dress_Shorewake (M_Master_Toon_Universal): BaseColor/Normal/Emissive/Roughness already wired 2026-08-29
```

## Seed discipline

All COPs that use RNG (Labs Baker jitter, denoise) have `Seed = 20260828` locked. Changing seed requires new manifest + QA renders (`DRESS_Neutral.png` / `DRESS_Transform.png` pattern). This matches the existing `reef_common.write_manifest(seed)` discipline.

## UE contract

Output `T_MelusinaC_DressShorewake_*` lands at `/Game/EnvSandbox/Textures/Melusina/`. Compression: BaseColor `BC7 sRGB`, Normal `BC5 linear (TC_Normalmap, WorldNormalMap)`, Roughness `BC4 linear (WorldSpecular)`, Mask `BC7 sRGB`. Verified by `Tools/verify_tex_contract.py` + `Saved/Audit/sea_above/houdini_variants/dress_*_manifest.json`.

## Related

- `Tools/Houdini/sea_above_reef/` — SOP/VEX/PIL lane being replaced (kept for rollback until COP proven)
- `Docs/Art/DRESS_HOUDINI_SETUP_REVIEW_2026-08-30.md` — gap audit (10 issues, weight lab dead-end)
- `Docs/Research/UE58_TOON_MATERIAL_INTAKE_INFINITY_NIKKI_2026-08-08.md` — Toon BSDF + 80 BytesPerPixel governance
