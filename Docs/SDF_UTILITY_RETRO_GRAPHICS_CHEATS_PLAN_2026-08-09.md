# SDF Utility Toolkit — Retro Graphics Cheats and Blender-Reduction Plan

Date: 2026-08-09  
Scope: `M_SDF_UtilityToolkit` and project-owned utility material instances  
Compatibility baseline: existing V9/V10 water and Substrate Toon materials

## Intent

Expand the SDF utility material into a safe, reusable graphics-cheat toolkit for props, water dressing, effects cards, character accessories, and portfolio scenes. The aim is to solve small placement, animation, breakup, lighting, and distance-presentation problems in-material so the artist does not repeatedly return to Blender for a minor visual adjustment.

The toolkit must remain an art-direction layer, not a replacement for mesh transforms, collision, simulation, or authored geometry. Every new feature is additive, opt-in, bounded, and neutral at its default value.

## Current project truth

Master:

- `/Game/EnvSandbox/Materials/SDF/M_SDF_UtilityToolkit`

Existing instances:

- `/Game/EnvSandbox/Materials/SDF/Instances/MI_SDF_Utility_WPO`
- `/Game/EnvSandbox/Materials/SDF/Instances/MI_SDF_Utility_GradientNoise`
- `/Game/EnvSandbox/Materials/SDF/Instances/MI_SDF_Utility_N64PS1`

Existing capabilities already present:

- Substrate Toon BSDF output;
- base and accent tint controls;
- tilable utility-noise texture and noise shaping;
- gradient and band controls;
- height, normal, and roughness map inputs;
- posterized color steps;
- pulse-driven normal WPO;
- separate utility, color, and surface parameter groups.

The new layer must preserve all current parameter names and current instance values. Existing V9/V10 water materials and the Nikki hero material family are not to be reparented or graph-mutated by this plan.

## Design rules

1. One master, several focused instances. Keep the general toolkit stable and expose specialized presets for placement, retro surface, billboard/impostor, and water dressing.
2. Default-off means bit-for-bit intent preservation. New scalar strengths default to `0`, masks default to `0`, and new vectors default to identity/zero values.
3. Visual movement is separate from gameplay movement. WPO does not update collision, navigation, bounds, Niagara attachment transforms, sockets, buoyancy, or gameplay traces.
4. World-space placement is explicit. WPO translation uses centimeters and world axes, with an optional local-space variant only when the asset needs object-relative behavior.
5. Expensive tricks are tiered. Distance fields, scene texture reads, translucency, and per-pixel looping do not enter the base toolkit without a dedicated permutation or sibling material.
6. Text-injection scripts must be idempotent, asset-scoped, and validation-first. They may author project assets but must not edit Engine plugin content.
7. Every cheat must have a visible use case in a render review and a measurable cost in material stats.

## Priority roadmap

| Priority | Cheat | UE implementation | Default | Main value | Risk / guardrail |
|---|---|---|---:|---|---|
| P0 | Literal XYZ WPO offset | Add world-space `float3` translation into the existing WPO sum | `(0,0,0)` | Move a visible mesh without Blender | Visual only; document centimeters and bounds limits |
| P0 | WPO axis mask | Multiply XYZ offset by an exposed mask | `(1,1,1)` | Lock movement to a plane or single axis | Keep mask separate from offset for predictable instances |
| P0 | Silhouette inflate/deflate | Vertex normal offset in world space | `0` | Thicken petals, cards, shells, foam rims | Clamp amplitude; avoid collision mismatch and shadow swimming |
| P0 | Utility-noise tiling | Preserve existing tiling and add independent UV scale | `1` | Reuse one texture across many scales | Sample utility noise only; do not silently rescale authored maps |
| P1 | UV scroll and wobble | Add time-driven offset to utility-noise coordinates | `0` | Water shimmer, magic drift, fake texture animation | Keep wobble on the utility branch, not base color/normal by default |
| P1 | Grid / vertex snap | Quantize world or local vertex position and blend toward it | `0` | PS1-style faceting and deliberate low-poly motion | Bounded grid size; never force snap on hero skin or water collision |
| P1 | Vertex jitter / breathing | Clamped world-space noise or sine WPO | `0` | Animate foliage, cloth tips, magic props, coral | Max amplitude and frequency caps; avoid camera-visible high-frequency shimmer |
| P1 | Normal quantization | Blend authored normal toward stepped/faceted normal | `0` | N64/PS1-inspired hard lighting response | Keep a clean bypass to the original normal sample |
| P1 | Palette quantization | Existing posterization plus optional dither threshold | `0` | Nikki-inspired controlled palette families | Apply before Substrate Toon; no global scene color mutation |
| P1 | Distance fog / palette fade | Camera-distance mask drives fog color, desaturation, or tint | `0` | Hide LOD, streaming, and far-clipping seams | Use as a material accent; do not double-apply world fog blindly |
| P2 | Ordered / hashed dither | Screen or world-grid threshold for masked fades and palette transitions | `0` | Retro dissolve, LOD fade, stippled water sparkle | Separate masked sibling if the base opaque shader becomes too costly |
| P2 | Scanlines / CRT hint | Screen-space stripe mask with scale and speed | `0` | Portfolio retro presentation and stylized screens | Portfolio/hero preset only; never force on ordinary environment assets |
| P2 | Fake rim / fresnel shell | Fresnel and view-normal mask into emissive or tint | `0` | Readable silhouettes and magical edges | Keep energy bounded to avoid bloom blowout |
| P2 | Fake caustics | Scrolling projected/world mask into emissive or base tint | `0` | Water-facing props, pools, underwater architecture | Use a lightweight texture branch; native Water remains authoritative |
| P2 | Contact band | Vertex AO, distance-field AO, or optional decal-driven darkening | `0` | Grounding without extra geometry | Distance-field path must be an optional sibling/permutation |
| P3 | Camera-facing billboard | Axis-locked or full camera-facing vertex rotation | Off | 2.5D foliage, distant charms, spell cards | Dedicated translucent/masked family; keep out of the opaque SDF default |
| P3 | Impostor view blend | Baked view atlas / UE Impostor Baker material | Off | Remove repeated Blender LOD work | Use for distant assets and foliage, not gameplay-critical silhouettes |
| P3 | Flipbook / sprite sheet | UV atlas animation for glows, bubbles, sparks, foam cards | Off | Cheap animated detail without mesh edits | Niagara/card material family, not the universal opaque master |

## P0 implementation: literal 3-axis mesh movement

Add a single placement block before the existing final WPO output:

```text
World-space offset = UtilityWPOOffsetXYZ * UtilityWPOAxisMask
Silhouette offset  = VertexNormalWS * UtilitySilhouetteExpand
Retro motion       = existing pulse WPO + optional jitter/snap
Final WPO          = existing WPO + World-space offset + Silhouette offset + Retro motion
```

Recommended parameters:

- `UtilityWPOOffsetXYZ` — vector parameter, centimeters, default `(0,0,0)`;
- `UtilityWPOAxisMask` — vector parameter, default `(1,1,1)`;
- `UtilityWPOOffsetSpace` — scalar or static switch, default world space; add local space only if a real asset requires it;
- `UtilitySilhouetteExpand` — scalar, default `0`, clamped to a conservative project range;
- `UtilityWPOClamp` — scalar safety limit, default appropriate to the asset family.

The placement block should be one clearly named comment region and one additive sum. Do not bury it inside the existing pulse chain. That makes instance debugging, rollback, and graph review straightforward.

Operational rule: use this for visual nudges, floating offsets, waterline cheats, shell thickness, and small alignment corrections. If the object needs collision, physics, socket alignment, or persistent world placement, change the Blueprint/component transform instead.

## P1 implementation: animation and texture cheats

### Utility UV animation

Keep `UtilityNoiseTiling` as the existing coarse scale control. Add:

- `UtilityUVScrollXY` — vector, default `(0,0)`;
- `UtilityUVWobbleStrength` — scalar, default `0`;
- `UtilityUVWobbleScale` — scalar, default `1`;
- `UtilityUVWobbleSpeed` — scalar, default `0`;
- `UtilityNoiseRotation` — scalar, default `0`, only if a material instance needs directional breakup.

The time/noise operation should affect only `UtilityNoiseTexture` coordinates. Authored height, normal, and roughness maps keep their current UV contract unless a separate parameter group explicitly opts them into motion.

### Vertex animation

Add a bounded utility motion node driven by object/world position and the existing Time node:

- `UtilityWPOJitterAmplitude` — default `0`;
- `UtilityWPOJitterFrequency` — default `1`;
- `UtilityWPOJitterSpeed` — default `0`;
- `UtilityWPOJitterAxisMask` — default `(0,0,0)` or `(1,1,1)` with amplitude `0`;
- `UtilityWPOUseVertexColor` — optional later switch, only if the project has a documented vertex-color convention.

This covers moving waterline debris, hovering charms, soft coral sway, and magic props without returning to Blender. It should use a stable object/world seed so neighboring meshes do not move in lockstep.

## P1 retro surface block

Add the surface block between the current final color interpolation and `SubstrateToonBSDF_1.BaseColor`, and add the normal block between the current normal sample and `SubstrateToonBSDF_1.Normal`.

Recommended parameters:

- `RetroColorSteps` and `RetroPosterizeStrength` — preserve current controls;
- `RetroDitherStrength` — default `0`;
- `RetroDitherScale` — default `1`;
- `RetroNormalQuantizationStrength` — default `0`;
- `RetroNormalSteps` — default `4`;
- `RetroFogStrength` — default `0`;
- `RetroFogStart` / `RetroFogEnd` — safe scene-distance defaults;
- `RetroFogColor` — neutral project fog color;
- `RetroRimStrength` — default `0`;
- `RetroRimPower` — default `4`.

The important split is that posterization, dither, normal quantization, rim, and fog are independent. That lets an artist make a PS1-like prop, an N64-like water shrine, or a clean Nikki hero prop without inheriting every retro artifact.

## Historical cheats translated to UE

### 1. Baked backgrounds and layered depth

Use authored cards, matte planes, depth layers, and light-weight foreground geometry for distant vistas or storybook spaces. In UE, combine camera-facing cards, decals, Niagara sprites, and depth-faded layers rather than modeling every distant object.

Best use: sky islands, distant architecture, underwater ruins, and portfolio backdrops.

Do not use it where gameplay navigation or camera freedom requires true geometry.

### 2. Billboards and impostors

Use camera-facing cards for small distant props and a view-blended impostor for larger assets. UE’s Impostor Baker supports full-sphere and upper-hemisphere captures and a billboard-style LOD workflow, so distant assets can be authored once and reused instead of repeatedly remodeled in Blender. See [Epic’s Impostor Baker documentation](https://dev.epicgames.com/documentation/en-us/unreal-engine/impostor-baker-plugin).

Plan: create a project-owned `M_SDF_ImpostorRetro` sibling material and a small set of distance-based instances. Do not add billboard rotation logic to the universal opaque SDF master.

### 3. Vertex lighting, vertex color, and fake lightmaps

Old hardware often pushed cheap lighting and blended precomputed values instead of evaluating expensive per-pixel effects everywhere. A project equivalent is a controlled tint/AO/emissive layer driven by vertex color, baked masks, lightmap UVs, or authored textures. A historical GDC archive describes the limitation of vertex lighting on large flat surfaces and the use of blended lightmap-style values as a practical approximation: [GDM July 1998 archive](https://media.gdcvault.com/GD_Mag_Archives/GDM_July_1998.pdf).

Plan: add optional `UtilityBakeMask` and `UtilityBakeTint` inputs only to a later sibling or a documented parameter group. Avoid making vertex color a hidden dependency of the base SDF toolkit.

### 4. Distance fog and depth haze

Cheap distance fog was used to hide far clipping and streaming boundaries while also creating atmospheric depth. The technique remains useful as a controlled material fade for stylized scenes; [Game Developer’s GDC graphics wrap-up](https://www.gamedeveloper.com/art/gdc-wrap-up-graphics-at-gdc) discusses depth fog/EXP2 fog as a low-cost approximation, while [this atmospheric fog reference](https://www.gamedeveloper.com/programming/atmospheric-scattering-and-volumetric-fog-algorithm-part-1) covers simple distance fog and depth-faded particle/billboard techniques.

Plan: use fog as a late color/emissive modulation, keep it opt-in, and coordinate its color with the scene’s Exponential Height Fog. It should conceal a transition, not fight the world’s physically based fog.

### 5. Quantized palettes and dither

Use palette steps for controlled banding, then optionally add a screen/world-grid threshold so transitions look intentional rather than like a smooth modern gradient. This is especially useful for stylized water highlights, shrine materials, and low-resolution portfolio captures.

Plan: make dither independent from posterization. Use a stable grid/hash, not a rapidly changing random value. Add a masked/LOD sibling if the opaque path becomes too expensive.

### 6. Affine-style UV drift and texture swim

Use a restrained UV wobble or view-biased distortion on the utility noise branch to evoke old-console texture behavior and to animate water, glow cards, and magical surfaces. This is an art-direction approximation rather than a claim that the engine should reproduce a hardware rasterizer bug exactly.

Plan: limit it to the utility texture, expose strength/scale/speed, and preserve authored texture UVs by default.

### 7. Wobbling vertices and vertex-shader animation

Texture- or math-driven vertex motion can provide stylized motion without CPU animation or new mesh edits. The GDC session [The Illusion of Motion: Making Magic with Textures in the Vertex Shader](https://www.gdcvault.com/play/1024032/The-Illusion-of-Motion-Making) is a useful reference for this class of technique.

Plan: use the existing pulse WPO as the first additive lane, then add seeded jitter and axis masks. Clamp the total offset and expose a “hero-safe” instance preset.

### 8. Fake contact shadows and AO bands

Use a small local darkening band, distance-field mask, decal, or mesh-distance-field contribution to ground props without adding geometry. [Ambient Occlusion Fields and Decals in Infamous 2](https://www.gdcvault.com/play/1015532/Ambient-Occlusion-Fields-and-Decals) is a useful reference for hybrid precomputed/dynamic contact shading.

Plan: keep distance-field reads out of the cheapest base instance. Make a `MI_SDF_Utility_Contact` or sibling material for assets that benefit from it.

### 9. Soft particles and depth-faded cards

Use depth fade to hide hard intersections on foam, bubbles, dust, magic sprites, and underwater cards. A GDC-era volumetric-fog reference discusses vertex-interpolated approximations and soft-particle/depth-fade methods: [GDC 2001 realtime volumetric fog notes](https://jcabs-rumblings.com/GDC2001.html).

Plan: use this in Niagara/card materials, not the opaque SDF master. It is a major Blender-reduction tool for water dressing.

### 10. Animated sprite sheets and layered 2.5D effects

Build flipbooks for bubbles, glints, ripples, fish schools, magic motes, and caustics. Layered sprites can sell density and motion at a fraction of the geometry cost.

Plan: create shared Niagara-compatible material families with a common palette contract. Feed water intensity, immersion, and reaction color through the existing profile-driven runtime instead of duplicating bespoke material logic.

## Proposed instance family

Keep the current three instances intact, then add project-owned variants only after the master graph is validated:

- `MI_SDF_Utility_3AxisWPO` — placement and silhouette controls, retro cheats off;
- `MI_SDF_Utility_RetroArcade` — grid snap, quantized normals, palette, dither, and optional fog;
- `MI_SDF_Utility_WaterDressing` — utility UV motion, fake caustics, rim, and bounded WPO;
- `MI_SDF_Utility_ImpostorRetro` — separate billboard/impostor path for distant assets;
- `MI_SDF_Utility_ContactCheat` — optional distance-field/decal contact shading;
- `MI_SDF_Utility_CardFX` — masked/translucent sibling for flipbooks and depth-faded effects.

The existing `MI_SDF_Utility_WPO`, `MI_SDF_Utility_GradientNoise`, and `MI_SDF_Utility_N64PS1` remain regression fixtures. Their current values must be captured before graph changes and re-read after compilation.

## Text-injection implementation order

1. Export the current master graph, parameter list, instance overrides, stats, and validation result to a dated audit JSON.
2. Add the P0 placement block idempotently to `M_SDF_UtilityToolkit`.
3. Compile and validate the master; verify all three existing instances still compile.
4. Add P1 UV motion, jitter, grid snap, and normal quantization behind zero/default controls.
5. Compile and compare instruction counts. If the base shader grows beyond the agreed budget, move the expensive block to a sibling master instead of adding a hidden permutation.
6. Create the focused instances only after the master is clean.
7. Use the Material Render Studio to capture the same mesh under neutral, placement, retro, water-dressing, and contact presets.
8. Perform a visual review against V9/V10 water states and the Nikki hero material family.

The injection script must:

- use `unreal.MaterialEditingLibrary` and an explicit asset allow-list;
- be rerunnable without duplicate parameters or nodes;
- use named comment regions and stable descriptions;
- save only project-owned assets;
- report every created/updated node and parameter;
- fail closed if the parent material, parameter name, or expected connection is missing;
- validate compilation and emit before/after stats.

## Validation gates

### Graph and compatibility

- `M_SDF_UtilityToolkit` compiles with zero errors;
- all existing utility instances compile;
- `M_Toon_SDF`, `M_Master_SDF_Toon`, and the Nikki hero material family are unchanged;
- current maps, normal maps, roughness maps, utility tiling, gradient, band, and pulse controls remain connected;
- no duplicate material parameters are introduced;
- new WPO controls are neutral at defaults.

### Visual matrix

Capture the same mesh and camera through Material Render Studio:

1. neutral baseline;
2. XYZ offset X/Y/Z independently;
3. axis-mask combinations;
4. silhouette expand;
5. utility-noise tiling and UV wobble;
6. vertex jitter and pulse;
7. grid snap and normal quantization;
8. palette steps with dither off/on;
9. distance fog and palette fade;
10. water-dressing caustic/rim preset;
11. contact cheat preset;
12. existing V9/V10 water baseline and underwater state.

### Runtime safety

- WPO does not change collision or gameplay traces;
- material bounds remain conservative enough for the maximum offset;
- no shadow swimming or temporal instability at the approved settings;
- no unexpected translucency or scene-texture dependency in opaque presets;
- Niagara/card siblings use depth fade and remain within their event budgets;
- packaged cook resolves all new instances and textures through soft references.

## Recommended first implementation slice

Implement only these five controls first:

- `UtilityWPOOffsetXYZ`;
- `UtilityWPOAxisMask`;
- `UtilitySilhouetteExpand`;
- `UtilityUVWobbleStrength`;
- `UtilityWPOJitterAmplitude`.

This gives the biggest reduction in Blender round-trips with the lowest graph risk. After a clean compile and render review, add grid snap, normal quantization, palette dither, fog, and the sibling billboard/card families.

## Research references

- [Epic Games — Impostor Baker Plugin](https://dev.epicgames.com/documentation/en-us/unreal-engine/impostor-baker-plugin)
- [Game Developer — GDC wrap-up: graphics at GDC](https://www.gamedeveloper.com/art/gdc-wrap-up-graphics-at-gdc)
- [Game Developer — Atmospheric scattering and volumetric fog](https://www.gamedeveloper.com/programming/atmospheric-scattering-and-volumetric-fog-algorithm-part-1)
- [GDC Vault — Advanced Visual Effects for 2D Games](https://www.gdcvault.com/play/1022426/Advanced-Visual-Effects-for-2D)
- [GDC Vault — Ambient Occlusion Fields and Decals in Infamous 2](https://www.gdcvault.com/play/1015532/Ambient-Occlusion-Fields-and-Decals)
- [GDM July 1998 archive](https://media.gdcvault.com/GD_Mag_Archives/GDM_July_1998.pdf)
- [GDC Vault — The Illusion of Motion: Making Magic with Textures in the Vertex Shader](https://www.gdcvault.com/play/1024032/The-Illusion-of-Motion-Making)
- [GDC 2001 realtime volumetric fog notes](https://jcabs-rumblings.com/GDC2001.html)

