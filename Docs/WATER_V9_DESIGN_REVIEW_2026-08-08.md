# Water v9 design review

Water v9 is a preserved-v7 extension. The original master remains the rollback and comparison baseline; v9 adds new function-family seams instead of turning the existing water graph into a single opaque monolith.

## Delivered

- `M_Water_Master_Grand_v9` with ripple height in World Position Offset, ripple normal blending, proximity-aware foam, and stress-gated bioluminescence.
- `MF_WaterRippleField_v9` with three parameterized sources, analytic ripple normal, and height output.
- `MF_WaterProximityFoam_v9` with distance-field/artist-mask/crest/ripple inputs and anti-tiling deterministic breakup.
- `MF_WaterBioluminescence_v9` with a mechanosensitive visual proxy: stress threshold, sparse cell variation, short decay, and blue/cyan/green palette controls.
- `M_Water_Underwater_Post_v9` plus a zero-strength default instance.
- Five water v9 presentation instances: CalmPond, BiolumGrotto, RiverClear, OceanPreview, and CinematicHero.
- Water audio routing: class, spatial attenuation, eight-voice concurrency, three validated Sound Cues, and Hearing perception bindings.
- Runtime integration source: native Water Body sample/query, pooled Niagara contact bridge, camera-manager underwater post bridge, and a three-slot v9 ripple/bioluminescence material bridge. These compile against the UE 5.8 game target and are designed to be attached to authored water actors without reparenting the v7 character hair material.
- Tier-2 reference source: an opt-in bounded Shallow Water-style height-field component with fixed stepping, radial impulses, Water Body filtering, and material telemetry. It is a profiling/correctness path until a Niagara Fluids asset earns promotion.

## Important engine constraint

The v7 graph had an islanded SceneDepth path. Activating it on the opaque SingleLayerWater master caused UE 5.8 to reject the material: only transparent or post-process materials can read SceneDepth. v9 therefore uses DistanceToNearestSurface plus artist and wave proxies for opaque-safe proximity foam. The separate underwater post-process is the correct place for screen-space depth logic.

## Portfolio read

The current material-grid renderer is useful for compile and family coverage, but the default preview lighting is too broad and the water planes/spheres read nearly white. Volta's delegated Material Render Studio pass should replace that capture setup with the professional neutral studio background before portfolio review. The v9 grid paths are recorded in `water_v9_manifest.json` for re-rendering through that pipeline.

## Next production seam

The runtime controller seam now exists in `UMelodiaWaterRippleMaterialBridgeComponent`; the first native Water Body query auto-attaches it and the bridge can write through the Water Body component's managed material instances. `UMelodiaWaterFluidZoneComponent` provides the first measurable tier-2 reference for impulse propagation, but is intentionally opt-in. Validate the three-slot writes and zone response on the authored Celestial Pond and hero-water actors in an interaction replay, then pair that pass with dedicated splash/shore-break source waves. Static/custom water surfaces still need explicit attachment. The shader side and gameplay event contract are ready; the current audio layer is intentionally a safe scaffold until the project has the right source recordings.
