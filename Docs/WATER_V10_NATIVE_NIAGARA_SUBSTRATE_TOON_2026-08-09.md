# UE 5.8 Water v10 — Native Water, Niagara, and detailed Substrate toon integration

## Status

The native C++ contract and full non-unity build are implemented. `NiagaraFluids` is enabled in `BS_GodFile.uproject`, but the editor must be restarted once before editor assets can be created or compiled. The current editor process has no observed automation port, so no `.uasset` graph mutation or portfolio render is claimed complete.

## Architecture

Gameplay emits one normalized `FMelodiaWaterContactEvent`. The interaction subsystem converts it into a typed `FMelodiaWaterFluidImpulse` and a typed `FMelodiaWaterSample`. Consumers remain independent:

```text
Melusina / prop
    -> UMelodiaWaterInteractionSubsystem
        -> native Water query + baked shallow-water query
        -> UMelodiaWaterNativeSimulationComponent
            -> authored ShallowWaterSim / WaveFoam / force components
        -> UMelodiaWaterNiagaraBridgeComponent
            -> NDC_MelodiaWaterContact
            -> pooled ripple/splash systems
        -> UMelodiaWaterRippleMaterialBridgeComponent
            -> native Water surface MIDs
            -> Substrate toon parameter contract
        -> native Water underwater post process
        -> audio/profile consumers
```

The native Water stack is the authority for body identity, zone identity, surface queries, baked simulation data, underwater activation, and promoted shallow-water interaction. The custom CPU fluid zone remains available only as a comparison/replay harness.

## Detailed Substrate toon family

The target family is additive and rollback-safe:

- `MF_WaterNativeInteraction_v10` — compatibility function that normalizes native Water data and the analytic v9 fallback.
- `M_Water_Master_Grand_v10_Substrate` — project-owned Substrate master; v9 remains unchanged.
- `M_Water_Underwater_Post_v10` — Water Body-owned post-process material with the same inert-at-zero blend contract.
- `MI_WaterV10_*` — profile-driven instances for calm, bioluminescent, and hero FLIP tiers.

### Native interaction function

`MF_WaterNativeInteraction_v10` should expose these inputs and outputs:

| Input | Purpose | Guard |
| --- | --- | --- |
| `NativeShallowWaterHeight` | Baked/native height contribution | Clamp to `WaterWPOClamp` |
| `NativeShallowWaterVelocity` | Flow, foam, and glow driver | Normalize with epsilon |
| `NativeShallowWaterNormal` | Native normal contribution | Blend only when valid |
| `WaterBodyIndex` / `WaterZoneIndex` | Routing/debug identity | No direct color dependence |
| v9 ripple centers/impulses | Analytic rollback/fallback | Used when native data is invalid |
| `WaterNoiseTiling/Contrast/Speed` | Repeatable surface breakup | Keep texture sample count bounded |
| `WaterWPOAmplitude/Clamp` | Stylized deformation | Opt-in and clamped |
| `RetroQuantizationSteps/DitherStrength` | N64/PS1-inspired mode | Opt-in per instance |

The native/fallback blend should be a clear validity gate, not a sum of two full simulations. The intended pattern is:

```text
NativeValid = bUsesNativeWater && NativeSampleValid
Height = lerp(AnalyticV9Height, NativeHeight, NativeValid)
Velocity = lerp(AnalyticV9Velocity, NativeVelocity, NativeValid)
Normal = normalize(lerp(AnalyticV9Normal, NativeNormal, NativeValid))
WPO = clamp(Height * WaterWPOAmplitude, -WaterWPOClamp, WaterWPOClamp)
```

### Substrate toon shading stack

The graph should keep geometry, stylization, and emission separate:

1. Base surface: a Substrate Slab/BSDF receives the water palette, native/fallback normal, artist roughness, and bounded specular band. The physical inputs stay stable while toon controls shape the stylized response.
2. Light banding: calculate a soft quantized `NdotL` mask using `ToonLightBands` and `ToonShadowSoftness`. Use it to blend `ToonShadowTint` to `ToonHighlightTint`; keep the transition soft enough to avoid temporal shimmer.
3. Rim: derive a view-facing rim from `1 - saturate(NdotV)` and multiply by `ToonRimStrength`, depth/shore masks, and profile tint. Rim is an accent, never the base lighting term.
4. Specular band: use `ToonSpecularBand` as a threshold over the native/fallback flow-aligned highlight. A low roughness surface can still use a restrained band so the water does not turn into a permanent mirror.
5. Foam: combine native crest/shore data, proximity contact, ripple energy, and a tilable breakup mask. Keep foam in a separate emissive/coat contribution so it does not corrupt the water body’s base color.
6. Bioluminescence: use velocity magnitude plus ripple impulse as a shear proxy, pass it through a threshold and short decay envelope, then feed cyan/green emission. Keep `WaterBioluminescenceWeight` profile-controlled.
7. Retro lane: quantize only the selected color/emission paths and optionally dither. Do not quantize the normal or WPO unless the instance explicitly opts into the N64/PS1 look.
8. WPO: use native height plus analytic fallback, with a project clamp and no gameplay dependency. Collision and water queries remain owned by Water.

Recommended parameter groups:

- `Native`: `WaterBodyIndex`, `WaterZoneIndex`, `NativeShallowWaterHeight`, `NativeShallowWaterVelocity`, `NativeShallowWaterNormal`.
- `Toon`: `ToonLightBands`, `ToonShadowSoftness`, `ToonRimStrength`, `ToonSpecularBand`, `ToonShadowTint`, `ToonHighlightTint`.
- `Surface`: `SurfaceRoughness`, `SurfaceMetallic`, `SurfaceSubsurfaceWeight`.
- `Motion`: `WaterNoiseTiling`, `WaterNoiseContrast`, `WaterNoiseSpeed`, `WaterWPOAmplitude`, `WaterWPOClamp`.
- `Retro`: `RetroQuantizationSteps`, `RetroDitherStrength`.
- `Bioluminescence`: `WaterBioluminescenceWeight`, `WaterShearThreshold`, `WaterFlashDecay`, `WaterBioluminescenceTint`.

This keeps the material family composable with the existing SDF and character toon families without reparenting the universal character master or making water-specific effects leak into Melusina’s dry-material lane.

## Niagara and force routing

The bridge writes the bounded fields in `NDC_MelodiaWaterContact` and applies a per-second budget. Rare hero events can still spawn pooled systems directly. The zone Blueprint owns the engine-specific binding from `RouteImpulseToNativeWater` to the authored shallow-water dynamic/impulse components; that binding is intentionally explicit because the engine example components are Blueprint assets, not stable C++ force APIs.

Tier guidance:

- Tier 0/1 for ordinary traversal and distant water.
- Tier 2 for promoted pools, wakes, and character interaction spaces.
- Tier 3 for localized hero splashes or portfolio shots.
- Tier 4 only for cinematic/portfolio capture with a measured budget.

## Text injection pipeline

`Tools/water_v10_text_injector.py` is the guarded bridge for editor-authoring parameter values and profile references. It validates required assets, rejects unknown parameter names, writes only project-owned instances/profiles, requests material compilation, and returns a JSON report. It must run only after one editor restart with a live automation port. It does not mutate opaque graphs or engine plugin content; the Substrate graph itself should be authored through the editor/Monolith material workflow and then read back for validation.

## Validation gates

1. Rebuild/UHT: `WaterBuild_20260809h.log` succeeded and linked `Binaries/Win64/BS_GodFile.exe`.
2. Editor restart: required after enabling NiagaraFluids.
3. Asset gate: create/read back the profile, NDC, native interaction function, Substrate master, underwater material, and three v10 instances.
4. Query replay: body/zone identity, wave-inclusive state, baked provider, entry/exit hysteresis.
5. Force replay: contact/impulse/dynamic routing, native caps, no duplicate event.
6. Niagara: NDC field schema, Water Data Interface binding, pooled contacts, CPU/GPU compile behavior.
7. Material: native/fallback blend, foam, WPO clamp, toon bands, Substrate compile, no invalid scene-depth dependency on the opaque surface.
8. Underwater: Water Body-owned activation and clean teardown on body exit/map transition.
9. Performance: `stat water`, `stat Niagara`, GPU timings, and Unreal Insights for each promoted tier.
10. Portfolio: render every v10 family member through Material Render Studio only after the editor replay is observed.

## Research basis

- [Epic Water System](https://dev.epicgames.com/documentation/unreal-engine/water-system-in-unreal-engine)
- [Epic Niagara Fluids](https://dev.epicgames.com/documentation/unreal-engine/niagara-fluids-in-unreal-engine?lang=en-US)
- [Epic Fluid Simulation Overview](https://dev.epicgames.com/documentation/en-us/unreal-engine/fluid-simulation-in-unreal-engine---overview)
- [Epic Niagara Water Data Interface](https://dev.epicgames.com/documentation/unreal-engine/API/Plugins/Water/UNiagaraDataInterfaceWater)
- [Epic Water Debugging and Scalability](https://dev.epicgames.com/documentation/en-us/unreal-engine/water-debugging-and-scalability-options-in-unreal-engine)
