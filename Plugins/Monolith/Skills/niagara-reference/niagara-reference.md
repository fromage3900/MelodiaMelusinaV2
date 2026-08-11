---
name: niagara-reference
description: Index of Niagara VFX reference documents. Provides quick-reference sim rules, particle budgets, and gotchas. Points to detailed docs on demand. Use when creating, optimizing, or debugging Niagara effects.
type: skill
---

# Niagara Reference Library

## Quick Reference

- **CPU sim:** < 100 particles. **GPU sim:** > 1,000 particles. Test in between.
- **Module execution order matters:** Position -> SolveForcesAndVelocity -> Collision/Readers -> Visual
- **ALWAYS set fixed bounds.** #1 Niagara optimization. GPU REQUIRES them.
- **Events are CPU only.** GPU alternative: Attribute Reader.
- **Light Renderer is CPU only.** GPU alternative: Component Renderer + PointLight.
- **Map For node: GPU only.** Does NOT work on CPU.
- **Skeletal Mesh GPU sampling: D3D12 only.** Crashes on Vulkan.
- **Attribute Reader:** Source emitter must execute BEFORE reader (top-to-bottom order).
- **1 emitter x 1,000 particles > 10 emitters x 100 particles.** GPU sim has fixed overhead.
- **Lightweight emitters (UE 5.4+):** Zero tick cost for simple ambient effects.
- **Additive materials don't need sorting.** Set sort to None for free perf.
- **Dynamic Parameters:** 4 slots x 4 channels = 16 floats for material communication.
- **Data Channel Write: CPU only.** GPU can only read.
- **No spaces in parameter names.** Breaks HLSL and scripting.

## Reference Documents

Read these on demand when the topic is relevant:

| File | Content |
|------|---------|
| `Docs/references/niagara/niagara-architecture.md` | CPU vs GPU decision tree, Lightweight emitters, lifecycle patterns, parent-child communication (events, attribute reader, data channels), data interfaces, system archetypes, warm-up/pooling |
| `Docs/references/niagara/niagara-effect-recipes.md` | Fire (5 emitters), blood splatter (5 emitters), smoke, muzzle flash, sparks, explosions (8 emitters), dust/debris, rain, magic/energy. Each with emitter layout, sim type, modules, materials |
| `Docs/references/niagara/niagara-performance.md` | Particle count budgets, fixed bounds, emitter count impact, overdraw reduction, sort mode costs, mesh vs sprite, shader budget, scalability integration, collision costs |
| `Docs/references/niagara/niagara-gotchas.md` | Module order, GPU limitations, attribute reader ordering, Map For CPU bug, static switch permutations, deterministic random, warm-up spikes, parameter naming |
| `Docs/references/niagara/niagara-material-integration.md` | Particle Color, blend modes, Dynamic Parameters (4x4 slots), Sub-UV/flipbook, soft particles, distortion/heat haze, camera facing modes, usage flags |
