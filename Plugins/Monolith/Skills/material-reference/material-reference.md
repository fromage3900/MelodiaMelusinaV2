---
name: material-reference
description: Index of material reference documents. Provides quick-reference PBR rules, HLSL gotchas, and performance budgets. Points to detailed docs on demand. Use when creating, optimizing, or debugging materials.
type: skill
---

# Material Reference Library

## Quick Reference

- **Sampler limit:** 16 per material (use Shared:Wrap for more textures)
- **Instruction budgets:** Opaque < 150, Translucent < 200, Post-process < 100
- **GPU cost:** MAD=4 cycles, Division=20, Pow/Sin/Cos=16, Tan=52
- **Static switches:** Each doubles permutations. Max 6 per master material.
- **Rust is NOT metallic.** Iron oxide is dielectric (Metallic=0.0).
- **Non-metal BaseColor:** Never below sRGB 30, never above sRGB 240.
- **Wet surfaces (Lagarde):** Roughness * 0.3, BaseColor squared, saturation boost.
- **MaterialFloat = half.** Use it for platform portability in Custom HLSL.
- **clip() disabled on Nanite passes.** ddx/ddy return 0 in compute.
- **MPC limit:** 2 Material Parameter Collections per material.
- **CPD over DMI:** Custom Primitive Data keeps draw call batching; Dynamic Material Instances break it.
- **Alpha gotcha:** NEVER use BLEND_Translucent for RT alpha. Use BLEND_AlphaComposite.

## Reference Documents

Read these on demand when the topic is relevant:

| File | Content |
|------|---------|
| `Docs/references/materials/hlsl-custom-node-guide.md` | FMaterialPixelParameters/VertexParameters fields, View uniforms, helper functions, HLSL gotchas, common recipes (noise, fresnel, dissolve, triplanar, flow map) |
| `Docs/references/materials/pbr-values.md` | PBR values by category: metals, organics/horror (blood, bone, flesh), building materials, environment, corrosion. Key PBR rules |
| `Docs/references/materials/material-patterns.md` | Wet surface (Lagarde), subsurface blood/skin, dissolve, emissive pulse, damage overlay, decals, masked vs translucent, degradation, dark environment, hologram, POM |
| `Docs/references/materials/material-performance.md` | Instruction budgets, GPU cycle costs, sampler budget, static switch math, blend mode costs, CPD vs DMI, texture vs math tradeoffs, debugging tools |
| `Docs/references/materials/material-systems.md` | Master material architecture, MIC vs MID, MPC layout, material function libraries, material layers, static vs dynamic branch, debugging checklist |
| `Docs/references/materials/anti-tiling.md` | Iq's 2-sample offset (default technique), macro variation, detail overlay, hex tiling, FluidNinja texture recommendations, anti-tiling checklist |
