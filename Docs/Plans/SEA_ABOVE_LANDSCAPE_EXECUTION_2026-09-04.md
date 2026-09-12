# SeaAbove landscape execution goal

Status: active. This plan expands the owner's landscape/Gaea repair request and preserves the original PCG work. Houdini follows those priorities.

## Scope and assumptions

Target the existing Nikki landscape master and Glacier instance in SeaAbove. Preserve existing reusable material functions, the single audio writer, unrelated dirty packages, and authored gameplay. Infinity Nikki is visual inspiration, not evidence of its proprietary shader implementation. "Substance Painter Pro" means finishing our existing Substance-inspired triplanar function, not claiming an Adobe product or exact implementation.

Primary evidence: live UE 5.8 graphs and compiled instances; Gaea export contract/data; official Epic, QuadSpinner and Adobe documentation; original graphics research and mathematical references; first-party Infinity Nikki imagery. Record assumptions, contradictions, costs and provenance. The update_plan tool is unavailable in this session; this file tracks the research and execution plan.

## Ordered work

1. **Saved; reload/visual verification pending — Recover and finish UV repair.** Reapplied the UV repair after relaunch. EditorAssetLibrary.save_loaded_asset returned true for both master and Glacier instance; disk timestamps and master size changed. Separate Gaea whole-landscape coordinates are present; detailed normal coordinates retained. No bulk saves. Full export orientation and visual verification remain part of step 3.
2. **IN PROGRESS — Discovery and evidence synthesis.** Initial primary-source research and existing triplanar script inspection complete; reconcile findings with live functions next. Maintain a claim/gap ledger, follow up on consequential uncertainty, produce a cited design deliverable.
3. **Pending — Gaea input contract.** Import true Snow/Water/Rock weights with correct linear sampling; inspect orientation against terrain, map semantic roles explicitly, support non-square bounds and export alignment. Separate macro colour from tiled layer detail. Ensure PCG receives actual layer data, not a shader-only illusion.
4. **Pending — Finalize existing triplanar MF.** Independently control projection scale/offset/rotation, axis weights and blend sharpness; correctly transform and blend normals; provide albedo/roughness/normal parity; distinguish compile-time feature selection from optional runtime UV/triplanar transitions. Preserve existing function interfaces or migrate all affected callers deliberately.
5. **Pending — Snow and macro detail.** Research-backed slope/elevation/curvature/flow controls, snow coverage and breakup at distinct spatial scales, slope-aware detail and bounded SDF motifs. Use stable noise and derivative-aware filtering; no unmeasured raymarching requirement.
6. **Pending — Cymatics.** Reuse the existing MPC writer/read contract. Bound emissive, roughness, frost/crystal contours and optional displacement. Protect walkable collision, normals, temporal stability and world-space anchoring. Verify separate-frame response and a neutral baseline.
7. **Pending — Verification and delivery.** Compile representative variants; inspect close/far views, negative projection faces, snow transitions and Gaea landmarks; profile baseline versus enabled variants; record shader cost, actual frame measurements when available, artifact provenance and targeted save/reload evidence. Do not certify unavailable measurements.
8. **Pending — Resume original PCG plan.** Finish analysis-derived zones and authored-world-point relocation, navigation/pacing, existing-graph dressing, Nikki biomes/corridors and secret passages. Current eastern colonnade placement is preliminary, not final lookdev.

## Acceptance

- Gaea corners map to the intended UV corners and recognizable exported features align with terrain; no repeating whole-terrain colour/mask patterns.
- Macro data and detail scale operate independently. Actual exported weights replace substitutes with explicit semantic bindings.
- Triplanar normal orientation is correct on all six signed axis faces and transitions; runtime transitions have measured costs and optional static variants.
- Snow varies coherently with terrain at macro, meso and micro scales, without swimming, repetitive contour stripes or destroyed distant readability.
- Cymatic controls respond across frames, return to neutral, and do not establish another audio writer.
- Master, functions and instances compile, save and survive reload. All required unfinished items remain marked pending.

## Research-informed design decisions (not implementation claims)

### Gaea and snow

Gaea exports are the macro authority. Runtime detail must not warp their coordinates. The Gaea bridge supports explicit weightmap files and layer names: [QuadSpinner weightmap import](https://docs.gaea.app/guides/use-in/bridges/gaea2unreal/importing-weight-maps.html). Unreal's target layers are separate from simply sampling a mask in a shader: [Epic landscape materials](https://dev.epicgames.com/documentation/unreal-engine/landscape-materials-in-unreal-engine).

Proposed coverage refinement uses C in [0,1], geometric slope s, and zero-mean supplemental noise F:

    edgeBand = 4*C*(1-C)
    Cfinal = saturate(C + edgeBand*BreakupStrength*F)

Zero breakup reproduces C exactly; the transition-localized term avoids adding arbitrary snow islands. Keep independent exported SnowCoverage and SnowDepth where available. Existing exports must not be renamed into unavailable physical quantities. [Gaea Snow](https://docs.gaea.app/reference/nodes/simulate/snow.html) documents settling/melt behavior; shader refinement is artistic, not that simulation.

Use macro colour, meso breakup, and micro normal/roughness at independently controlled wavelengths. A proposed low-cost hierarchy is a small number of baked-noise samples; profiling chooses the budget. Domain warping applies only to supplemental detail. For snowline/shore/path distance d, smooth masks can use 1-smoothstep(-width,width,d); document signed-distance range in centimeters. A noise threshold is not automatically a true distance field.

### Triplanar Pro

The existing expand_landscape_triplanar_pro.py rotates position but computes weights from the unrotated normal; it only samples RGB. Finish that implementation, not a second competing function.

For projection-to-world rotation R, anchor o, physical repeat size s and geometric normal Ng:

    p = transpose(R)*(P-o)/s
    n = transpose(R)*Ng
    w = pow(abs(n), hardness); w /= max(sum(w), epsilon)

Rotate/mirror all material channels coherently; correctly reorient normals on all signed faces. Neutral normal input must return Ng, including blend regions. [Adobe Painter projection controls](https://experienceleague.adobe.com/en/docs/substance-3d-painter/using/painting/fill-projections/tri-planar-projection) establish the desired control vocabulary, not an exact implementation claim. Its plane weights use vertex normals, not the detail normal map. Separate texture-space rotation from the whole projection transform.

Optional runtime UV/triplanar transitions blend sampled outputs. Static variants remove unused branches. [Epic UE-296315](https://issues.unrealengine.com/issue/UE-296315) documents derivative artifacts for a dynamic UV Switch; its target fix is 6.0, so verify UE 5.8 behavior instead of assuming it fixed. Nominal samples per texture are 1 for UV, 3 for triplanar, 4 for an evaluated dual-path blend; these are not measured frame costs.

### Nikki reference and creative cymatics

[Epic's Infinity Nikki developer interview](https://www.unrealengine.com/developer-interviews/behind-the-scenes-of-infinity-nikki-tracing-a-glamorous-turn-to-an-unreal-open-world/) provides first-party imagery and technical context. Use its readable fantasy forms and material detail as visual direction. No claim is made that Nikki uses this snow math, Gaea, or cymatics.

Candidates for measured opt-in polish: frost-edge sparkle localized by signed distance; standing-wave crystal veins limited to exposed rock; shoreline resonance contours; subtle snow roughness response around authored musical landmarks. Reuse the project's existing Chladni mode convention and audio MPC parameters rather than replacing them with a second mode system.

Given a spatial mode phi bounded by 1 and envelope/influence in [0,1], displacement A*envelope*influence*phi is bounded by A. Prefer shading response first. Nodal bands derive from abs(phi), not its time-multiplied oscillation, avoiding terrain-wide flashes at temporal zero crossings. No new audio writer; no assumed collision deformation.

## Evidence gaps to close during execution

### Triplanar correction saved

Rock normal integration is now saved in the master and enabled on the Glacier instance. Rock_DetailWorldSizeCM=400 defines repeat size; Rock_TriplanarBlend=1 selects triplanar and can transition toward the existing UV-normal sample; bRockTriplanarNormals is the static feature selector. NormalWS converts to tangent space before blending and normalization, then feeds only Layer Rock. This does not replace macro colour coordinates. The instance reports compiled=true, but reported instruction/sample counts did not change; do not treat those stats as proof of the enabled landscape permutation's actual cost. The neutral sphere capture rendered but had poor framing, so six-face visual acceptance remains open. Script: wire_landscape_rock_triplanar_normal.py.

The existing function now also exposes optional NormalTex and NormalStrength inputs and a NormalWS output. NormalTex defaults to the project neutral normal; NormalStrength defaults to one. It uses UE's platform-aware UnpackNormalMap and common-space surface-gradient composition, with the same projection coordinates and weights as colour. Reference: [Mikkelsen 2020](https://jcgt.org/published/0009/03/04/). M_Triplanar_NormalProof consumes the actual NormalWS output with a rotated projection and reports compiled=true, 3 pixel texture samples and 271 pixel instructions. Function and proof material both saved successfully. This is compilation evidence only: signed-face lighting, neutral-normal visual parity, detail normal strength and final landscape wiring still need validation. Scripts: extend_landscape_triplanar_normals.py and validate_landscape_triplanar_normal.py.

Updated the existing MF_Triplanar_LandscapePro Custom expression in place: geometric normal now uses the same rotation as projection coordinates; degenerate axis/breakup weights fall back to geometric weights rather than black. Preserved the 11-input signature and explicit gradient sampling. The original builder now reads Content/Python/shaders/landscape_triplanar_pro.hlsl, preventing regeneration from restoring the older math. EditorAssetLibrary confirmed function save. Active caller compilation reports true for Nikki landscape, Nikki, and retiring Toon landscape. These compile reports do not prove the enabled triplanar permutations or signed-face normal tests; full normal-map output and runtime blending remain unfinished.

### Live update: Base layer and weight orientation

The previous inference that weightmaps never reached UE was incorrect: the Landscape Gaea component references all three staged W_Glacier files, and editor layer samples contain actual Base/Snow/Rock weights. Material texture assets and landscape weight storage are separate. A 16-point orientation diagnostic matches the normalized source weights with no flip (mean absolute error 0.000462); X/Y/both flipped alternatives give 0.0684/0.0914/0.1743. This is sampled evidence, not exhaustive orientation proof. Water coverage still needs a deliberately selected nonzero sample.

The shared master expected Ground whereas Gaea imported Base. Added Base to the live colour, normal and roughness blends while retaining Ground; wire readback verifies all three connections. Master saved through EditorAssetLibrary; Glacier compilation reports true. Existing Gaea mask modifier weights are zero, so substitute mask textures are inert. Do not multiply imported snow coverage by the same exported weightmap again and inadvertently square it.

Evidence: Saved/Audit/sea_above_layer_weight_probe.json, sea_above_weight_orientation.json, sea_above_base_binding.json. Reproducer: Tools/verify_sea_above_weight_orientation.py. Repair: Content/Python/fix_gaea_base_layer_binding.py.

- Gaea height/weight orientation alignment and full semantic weight import.
- Live function identity and callers, compared with the existing source script.
- UE-normal decoding and signed-axis tests in the actual function.
- Shader variants, GPU timings, displacement bounds and collision behavior.
- Reload-proof master/instance/function saves and controlled visual comparisons.

Research discovery used bounded primary-source searches in Gaea/Epic, Adobe/triplanar graphics, and snow/SDF/cymatics/Infinity Nikki lanes. The first pass stopped when each design family had primary support; live implementation questions above remain open and require targeted verification rather than more broad searching.

### Rock detail colour and normal proof progress

Added an independent Rock_DetailAlbedo texture to the existing rock triplanar call. The planar alternative shares the function's transformed XY coordinates, rotation, offset and 400cm repeat-size control; runtime projection interpolation occurs after sampling. The result modulates the unchanged Gaea macro colour around Rock_DetailAlbedoReference (linear 0.18 default). Rock_DetailAlbedoStrength=0 is identity and bRockDetailAlbedo=false excludes this optional path. Saved master; colour detail remains disabled pending texture-reference calibration and close/far comparison. Script: Content/Python/wire_landscape_rock_colour_detail.py. This is not yet full per-layer colour/roughness support.

Normal proof now uses the authored wet-rock normal and was saved. Neutral strength-one versus zero rendered comparison (ROI [100,160,410,350]) has mean RGB8 difference 0.0275 and maximum 2. Rock sphere and opposing cube captures show visible detail, but several cube faces are too dark to assess signed-face correctness; six-face acceptance remains open. Evidence: Saved/Audit/triplanar_neutral_comparison.json, triplanar_rock_sphere.png, triplanar_rock_cube_front.png, triplanar_rock_cube_back.png.

### Extended-layer normalization and snow breakup implementation

Live tracing found weighted extended-layer colour/normal sums were interpolated again by total coverage, applying weights twice. Added division by the unsaturated safe weight sum before coverage interpolation, plus final normal normalization. Saved and compiled master (reported 351 PS instructions before optional snow additions). Script: fix_landscape_extended_layer_normalization.py. Visual acceptance remains pending.

Added bSnowCoverageBreakup (default false), Snow_BreakupWorldSizeCM (600), Snow_BreakupStrength (0.15). Existing snow coverage feeds a two-octave quintic value-noise refinement in world XY; 4*C*(1-C) localizes changes to partial coverage, and derivative footprint fades undersampled octaves. No source-map coordinate warp or additional audio writer. This noise is not an SDF or physical snow simulation. Zero strength preserves original coverage exactly, including legacy values above one. Code: Content/Python/shaders/landscape_snow_breakup.hlsl; integration: wire_landscape_snow_breakup.py. Active unlit M_Snow_CoverageProof compiles (reported 171 PS instructions, zero texture samplers; engine reports three PS texture samples despite no explicit texture nodes, so do not infer actual sample cost). Saved proof capture: Saved/Audit/snow_coverage_proof.png. Landscape option remains disabled pending terrain comparison.

Current live Glacier readback reports bUseGaeaMasks=true (earlier notes said false); modifier weights remain zero. Reconcile instance state from live readback, not handoff assumptions.

### Bounded cymatics baseline repair

Live master applied CymaticsLandscapeAmount twice through multiply plus interpolation, and reduced original emissive even at zero beat. Replaced the final response with Baseline + saturate(SurfaceColor)*saturate(Beat)*saturate(Amount)*clamp(MaxEmission,0,10). New CymaticsLandscapeMaxEmission defaults 1. At current amount 0.15, added per-channel emission is bounded by 0.15; zero beat or amount returns the original baseline. Targeted save succeeded; compiled master reports 353 PS instructions. Source: Content/Python/fix_landscape_cymatics_response.py.

Confirmed existing sole driver writer in Source/BS_GodFile/MelodiaIntegration/MelodiaCymaticsWriterSubsystem.cpp. No MPC writes or new audio authority were introduced. Two separate editor-world readbacks returned pulse 0. Isolated proof materials render zero/half/full inputs in separate calls (Saved/Audit/cymatics_proof_*.png and cymatics_proof_pixels.json). These prove the shader response only; live audio-driven frame response remains unverified and requires the running gameplay/audio path. Spatial nodal/SDF response and roughness modulation remain unfinished.

### Nonzero water-layer verification

Selected an interior source pixel (162,32) with Water=255, mapped via landscape min/full extent to world XY (-169474.72467,-233894.94165). Live LandscapeComponent readback returns Water=0.4862745, Base=0.4941176, Rock=0.0196078, Snow=0. This confirms that the actual Water landscape layer contains nonzero imported data, independent of material texture slots. Source-normalized comparison recorded in Saved/Audit/sea_above_water_target.json. Earlier orientation diagnostic plus this targeted sample closes the missing nonzero-water check, but does not substitute for full colour/height landmark visual alignment.

### Actual terrain base-colour capture

Editor viewport is currently 0x0 and realtime=false, so viewport screenshots cannot provide reliable acceptance. A transient SceneCapture2D with landscape-only show list captured actual terrain BaseColor at 1024x1024, orthographic width 510000cm, location (0,0,180000), pitch -90. Capture actor destroyed in finally; no map save. Saved/Audit/sea_above_basecolour_landscape.png shows a single continuous macro pattern over the whole landscape; no obvious repeated tile blocks. This is base-colour-only evidence, not lit close/far material approval. Python Rotator positional constructor sets roll first here; use named pitch/yaw/roll arguments for future captures.

### Gaea snow signed-distance bake

Tools/build_gaea_snow_distance.py produces SnowEdge_DistanceCM.npy and T_Glacier_SnowEdge_SDF16.png under Saved/GaeaDerived/Glacier, with a source-hashed SnowEdge_contract.json. Raw export threshold 0.5; negative inside; planar Euclidean distance to opposite-class sample centers, not terrain geodesic distance. Pixel spacing derives from export contract (495.54cm), matching live landscape full extent. Encoded range +/-25000cm; measured quantization error <=0.382cm. Eight independently brute-force checked samples match EDT. Source resolution remains about 5m, so fine grain must come from separate detail. No Unreal texture imported or material enabled yet. This closes the mathematical bake step, not SDF shader integration or visual/performance acceptance.

### Snow SDF import and optional frost-band wiring

Imported T_Glacier_SnowEdge_SDF16; texture readback confirms 1009x1009, linear, clamp XY, R32_FLOAT, one mip. Used SingleFloat to preserve encoded distance precision; mip/streaming behavior and active cost still require evaluation. Added optional bSnowFrostDistanceBand (false), shared whole-landscape UV, distance range 25000cm, derivative-softened absolute-distance band width 1000cm, strength 0.2, roughness target 0.7. This modulates only roughness and leaves existing coverage/colour unchanged. Zero strength or static false gives original roughness. Saved master via targeted save. Script: wire_landscape_snow_sdf.py. Active shader permutation and terrain visual/performance acceptance are still pending; not enabled on Glacier.

### Active SDF shader proof

M_Snow_DistanceProof consumes the actual R32_FLOAT texture and exact master band code with RangeCM=25000, WidthCM=1000, Strength=1. Compiled=true; reports one sampler, one PS texture sample, 109 PS instructions. Saved/Audit/snow_distance_proof.png renders the continuous exported snow boundary and isolated island, rather than repeated stripes. This closes active band shader compilation/rendering; it does not measure incremental terrain GPU cost or validate final frost roughness under level lighting. Glacier remains disabled pending that acceptance.

### Musical hero graph placement inventory

Live authored point data confirms all three hero graphs use WORLD coordinates near the origin, independently of their large offset volumes. Cathedral: 90 authored points, bounds [-1080,-1080,-10]..[1080,3200,1620]. BellTreeGarden: 63, [-2210,-384,26]..[2210,309.693,1208]. XylophoneTrail: 84, [-4140,-470.451,95]..[4140,1011.680,726]. These are local-sized set pieces stored as world points, not map-scale scattering distributions. Full point/space/culling inventory saved in Saved/Audit/sea_above_hero_point_inventory.json. Next relocation must deliberately handle coordinate-space migration and graph callers, then derive destinations using the layout readers; resizing boxes alone cannot solve it. Current Colonnade live Z is 42144 (earlier evidence 41544); preserve current state until terrain recheck.

### Hero graph reuse constraint

Asset Registry confirms all three musical hero graphs are shared by other levels, including offline MIDI and dedicated proof maps; Cathedral and BellTree also feed DA_PCGHeroBuilderSettings. Full package referencers saved in Saved/Audit/sea_above_hero_graph_referencers.json. A global WORLD-to-LOCAL migration would change unrelated levels. SeaAbove relocation therefore requires a scoped graph instance override if supported, otherwise a derivative of the existing graph with explicit source provenance, rather than mutating canonical shared point settings. No shared graph changed.

### Scoped BellTree placement graph prepared

Prepared /Game/EnvSandbox/PCG/Styles/SeaAbove/PCG_SeaAbove_BellTreeGarden by duplicating the existing shared graph, preserving its topology and authored point transforms, and converting five CreatePoints groups (63 points) to LOCAL_COMPONENT. Original WORLD settings rechecked unchanged. Source provenance and unit-scale placement convention stored as asset metadata; targeted save succeeded. Not assigned to a volume or generated yet. Script: prepare_sea_above_belltree_graph.py. Eastern colonnade west-facing sightline reader reports 97,132cm mean clear distance over 24 rays, 100,000cm longest, claustrophobia score 3; placement still needs local ground and traversal validation.

### BellTree terrain footprint screening

Rejected first candidate (146000,-60000): five landscape-only collision samples span approximately 428cm elevation across the 44m-wide authored footprint. Scanned 16 nearby east-plateau candidate centers using the same five-point footprint, recording terrain heights and slopes in Saved/Audit/sea_above_belltree_candidates.json. This is placement screening only; route/nav and generated mesh grounding remain required.

### Eastern navigation coverage repair started

Route tests failed; live inventory showed the only nav bounds covered 60x80m near origin, despite built=true and 189 tiles. Added Nav_SeaAbove_EastPlateau through the supported AI action at (140000,-65000,41500), extents (6000,9000,6000), covering candidate and colonnade approaches. Build finished with zero remaining tasks. Targeted save of new actor returned true. Direct route still fails after build; endpoint projection/nav-generation diagnosis remains open. No claim of connected eastern traversal yet.

### Eastern route verified after navigation settled

Navmesh now reports 930 tiles, build complete and no dirty areas. All 18 sampled positions in the eastern corridor project successfully, including BellTree center at (140000,-70000,40466.883). Using projected endpoints gives a complete nonpartial 8045.20cm path to (140000,-62000,41318.471). validate_path_width passes 300cm requirement with minimum 724.40cm, average 759.11cm, zero pinch violations. The previous missing candidate projection was transient following the rebuild; no second bounds expansion was needed. Samples: Saved/Audit/sea_above_east_nav_samples.json. This verifies the local eastern approach only, not a connection back to arrival or final dressed traversal.
