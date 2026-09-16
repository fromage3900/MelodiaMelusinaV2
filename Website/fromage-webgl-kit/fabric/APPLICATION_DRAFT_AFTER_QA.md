# Three.js Fabric Technical Artist Consultant — Application Draft After QA

**Listing:** Three.js Technical Artist Consultant  
**Checked:** 2026-09-10  
**Listing state at check:** fewer than 5 proposals, 0 interviewing; hourly $30–$300; 1–3 months; mandatory CLO 3D + Three.js + Blender.  
**Status:** DRAFT / DO NOT SUBMIT UNTIL EVIDENCE LINKS ARE CHOSEN

The buyer is asking for consulting/strategy rather than production. The application should therefore demonstrate judgment, pipeline literacy, and the ability to evaluate visual/material work—not promise a giant finished garment system before contact.

## Best positioning

Lead with the intersection of:

```text
CLO garment experience
+ Blender cleanup / realtime asset preparation
+ Three.js material / PBR inspection
+ realtime technical-art judgment
```

Do not lead with generic frontend development.

## Draft proposal

Hi — this is unusually close to the kind of technical-art pipeline I work in.

I work across realtime 3D asset preparation, material/lookdev systems and browser-side Three.js presentation, and I have hands-on experience with both CLO 3D and Blender. I also maintain an interactive Three.js material/asset inspection system that I use to compare PBR response, texture channels, lighting and realtime presentation rather than judging garment assets only inside the DCC.

For your fabric pipeline, I’d separate the problem into three layers:

1. **physical/source capture** — decide what data is genuinely measured from each swatch versus artist-authored;
2. **asset/material generation** — build repeatable base-color, normal, roughness, height/displacement and related resources with a clear validation standard;
3. **Three.js validation** — evaluate the material under controlled lighting/cameras and realistic browser performance constraints before declaring it production-ready.

A major thing I would avoid is treating “photoreal fabric” as just a texture-generation problem. Geometry scale, weave/stitch frequency, grazing-angle response, normal strength, roughness range, lighting/exposure and the chosen Three.js material model all interact. I’d also keep measured data clearly separated from artistic approximation so the pipeline does not accidentally claim physical accuracy it cannot reproduce.

I can also help define a practical review rubric for the artists/modelers you hire: geometry density, UV quality, material-slot count, texture conventions, silhouette, fabric response under neutral/grazing light, GLB delivery quality and browser performance.

Relevant proof:

- **Live Interactive Three.js Fabric Material Lab:** https://anyone-accessing-leaves-glasgow.trycloudflare.com/tools/fromage-webgl-kit/prototypes/fabric-material-lab/
- **PBR Shader & Organza Sheen Breakdowns:** https://anyone-accessing-leaves-glasgow.trycloudflare.com/wix/shader-breakdowns.html
- **35 Master Material & Garment Breakdown Plates:** https://anyone-accessing-leaves-glasgow.trycloudflare.com/wix/melusina-final-renders.html

I’d start by looking at one representative swatch + one target garment and defining the acceptance criteria before recommending a large automated pipeline. That usually reveals very quickly which parts should be measured, procedurally generated, artist-authored, or simply parameterized at runtime.

## Questions to ask in the proposal / first call

1. What does “reproduce real fabric accurately” mean for the product: perceptually convincing ecommerce imagery, close photographic matching, or a measured physical reproduction target?
2. What source data do you currently have for each swatch—controlled photography/scans, manufacturer maps, measured color values, weave dimensions, or informal reference photos?
3. What is the final runtime target: vanilla Three.js, React Three Fiber, desktop/mobile ecommerce, fixed hardware, or another environment? What are the expected GLB/texture/performance budgets?

## Short technical answer if asked about the automated swatch pipeline

A sensible first architecture would be:

```text
controlled swatch capture
→ color-normalized crop / tiling candidate
→ base-color cleanup
→ height / structure inference or authored weave source
→ normal generation
→ roughness candidate generation
→ optional displacement / fiber masks
→ scale metadata
→ texture packaging
→ Three.js validation scene
→ human QA / approval
```

The automation should generate **candidates and metadata**, not silently declare physical correctness. A controlled validation scene and human approval should remain the truth gate.

## What we can say truthfully after current evidence QA

- hands-on CLO 3D experience;
- Blender garment/asset preparation experience;
- Three.js realtime material/asset presentation experience;
- PBR texture/resource organization;
- normal/roughness/metal/AO inspection workflows;
- authored realtime lighting for material evaluation;
- ability to design an automated candidate-generation + human-validation pipeline;
- ability to define review criteria for outsourced 3D/material work.

## What not to claim

- measured BRDF/fiber-scattering expertise unless separately demonstrated;
- colorimetric accuracy without calibrated capture/measurement;
- an already-complete automated physical swatch scanner;
- a production-ready one-click fabric digitization system;
- CLO specialization beyond actual shown experience;
- exact physical reproduction from arbitrary photos.

## Minimal gate before submission

The application can be submitted before the full knitwear configurator exists if all of these are true:

1. one existing Three.js material viewer is runtime-checked;
2. commercial-safe evidence/provenance is chosen;
3. at least one genuine CLO/Blender artifact or screenshot can support the software claim;
4. the listing is still open/current;
5. the proposal links point to evidence we can explain confidently.

Do not wait for an entire ecommerce configurator merely to answer a consulting listing.

## Next single action

Runtime-check the existing material viewer and select one clean CLO/Blender artifact for the proposal evidence set.
