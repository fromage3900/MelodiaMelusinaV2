# Houdini VDM Fabric Mountain — Scaffolding
**Date:** 2026-09-02 | **Status:** Scaffold — bake path, not yet cooked | **Engine:** Houdini 22.0.368 + UE 5.8 (WPO/Nanite)

## Why VDMs for Faraway Mother
Heightmaps fail for fabric: they displace only +Z (no overhangs, no drape). Faraway Mother's ridges are **folded cloth** — 3D overhangs, undercuts, self-occlusion. Vector Displacement Maps store XYZ offset per texel (RGB = XYZ vector in tangent space), capturing true 3D drape that heightmaps cannot.

## Pipeline

```
Fabric sim (Vellum) or procedural fold (VEX)
  → SOP rest position (Attribute Create rest, rest2)
  → Labs Maps Baker (vector mode) — bakes rest→deformed delta as RGB
  → COP VDM — 32-bit float, 4K, RGB = XYZ offset, A = mask
  → File Output — T_FarawayMother_Fabric_VDM_[a/b/c].exr (32f, no compression)
  → UE: Material World Position Offset (WPO) via Custom UV + Tessellation or Nanite displacement
```

## Houdini Baking (SOP)

```python
# In SOP network:
# 1. Create rest attribute on base plane (10m × 10m, 200×200 quads)
# 2. VEX fold: @P += sin(@P.x*foldFreq) * foldDepth * @N + noise
#    or Vellum Drape: wire solver with pin on ridge line
# 3. Labs Maps Baker:
#    - High: deformed fabric (with folds)
#    - Low: base plane (rest)
#    - Mode: Vector Displacement
#    - Resolution: 4096
#    - Output: T_VDM_FabricMountain_A (RGB=XYZ, A=mask)
```

## UE Material (WPO)

```hlsl
// In M_Master_FarawayMother_Fabric (or M_Master_Toon_Universal with WPO enable)
// Sample VDM: VDM_X = TextureSample(VDM, UV).r * VDM_Scale.x
//            VDM_Y = TextureSample(VDM, UV).g * VDM_Scale.y
//            VDM_Z = TextureSample(VDM, UV).b * VDM_Scale.z
// Transform tangent → world: offset = VDM_X * Tangent + VDM_Y * Bitangent + VDM_Z * Normal
// World Position Offset = offset * Mask * LOD_Fade (0 at LOD2/3, 1.0 at LOD0)
// Requires: Tessellation or Nanite with WPO enabled, Dither crossfade handled by LOD system
```

## Files Scaffolded

- `Tools/Houdini/vdm_fabric_mountains/vdm_fabric_baker.py` — SOP VDM baker (template, seed-locked)
- `Tools/Houdini/vdm_fabric_mountains/README.md` — this doc
- `Content/Python/build_faraway_vdm_mountains.py` — UE importer + height-aware placer for VDM meshes
- `specs/vdm/faraway_mother_vdm_manifest.v1.json` — manifest (seed, resolution, files, hash)

## Seed Discipline
`SEED=20260829` for all VDM bakes (matching Copernicus). Changing seed requires new manifest + QA renders.

## Integration with Existing
- **Heightmap base:** Gaea `LiquidCathedral` or Heightfield COP provides terrain base (Z only)
- **VDM overlay:** Fabric ridges add XYZ detail on top (WPO), masked to ridge areas via vertex color height_mask
- **Perceptual LOD:** VDM WPO fades 1.0→0.0 LOD0→LOD2 (POM32→0, Toksvig 0→1.0), so distant vista is macro normal + rim bloom, not displaced
- **Cymatic:** Chladni (3,5) jacquard drives VDM fold frequency via `foldFreq = baseFreq + BassIntensity * 2.0`

## Unexpanded Systems Wiring (for final P2)

| System | Status | Faraway Wiring |
|--------|--------|----------------|
| `MelodiaVegetationGrowthSubsystem` | SCAFFOLDED | Kelp/coral on VDM folds via PCGEx (SpeedTree plant authority) |
| `MelodiaDressingSubsystem` | SCAFFOLDED | Hero props/debris in valley (dressing pass) |
| `MelodiaCaptureRenderSubsystem` | SCAFFOLDED | 4-view HDR lookdev evidence for VDM fabrics (automated) |
| `Water/Oceanology` | PRESENT | Moon haze volume + hair cascade flow (SLW absorption, not height fog) |
| `Magpie` Seam | WATCH→Scaffold | Simulation truth ↔ visual truth for fabric wind (read-only seam) |
| Neural Shaders | WATCH | Material onnx for silk sheen (needs material NN, present onnx is text-embedding only) |

## Next Steps
1. Run `hython Tools/Houdini/vdm_fabric_mountains/vdm_fabric_baker.py --seed 20260829 --res 4096` → `Saved/Audit/vdm_fabric/` (4K EXR, 32f)
2. Import via `Content/Python/build_faraway_vdm_mountains.py --import` → `Content/EnvSandbox/Meshes/FarawayMother/VDM/` + `T_VDM_*` → `/Game/EnvSandbox/Textures/FarawayMother/VDM/`
3. Assign to `MI_FarawayMother_CelestialSilk_LOD0` WPO slot, verify in PIE (LOD0 crevices, LOD3 flat, no popping via Bayer dither)
4. Wire audio: `MelodiaCymaticsSubsystem` Bass→foldFreq, BeatPulse→WPO scale pulse

## Evidence
- Manifest `faraway_mother_vdm_manifest.v1.json` (hash, seed, files)
- PIE capture `Saved/Audit/faraway_vdm_*.mp4` + `*.json` (LOD0 POM32 vs LOD3 impostor, dither proof)
- gate_ledger row `faraway_mother_vdm`
