# 2026-08-31 — Toolchain Trench Sweep II Integration Tests

**Project:** Melodia Melusina / UE5.8  
**Research:** `Docs/Research/EMERGING_3D_TOOLCHAIN_TRENCH_SWEEP_02_2026-08-30.md`  
**Relationship to primary plan:** supplement to `TOOLCHAIN_INTEGRATION_SPIKE_PLAN_2026-08-31.md`; do not attempt every test in one day.

---

# Objective

Convert the second deep-trench software survey into **small Melodia-shaped experiments** with explicit stop conditions.

The goal is not to acquire software. The goal is to discover whether any of these tools remove one of five expensive production bottlenecks:

1. wardrobe fitting / skinning / cloth iteration;
2. environmental interaction fields;
3. non-heightfield world geometry;
4. motion acquisition / animation blocking;
5. source-data capture / material reference.

---

# Test discipline

For each candidate record:

```text
Tool / version:
Exact UE compatibility:
License / source availability:
Install/setup minutes:
Benchmark task:
Baseline workflow:
Hands-on minutes:
Export / bake path:
Runtime dependency left behind:
Result quality:
Failure modes:
Decision: ADOPT / PARK / REJECT / WATCH
Next action:
```

Stop immediately if:
- the exact required UE version cannot be supported safely;
- the exporter destroys critical UV/material/skeleton data;
- the plugin wants to become a new authority for a system already owned elsewhere;
- the first useful result takes longer than the baseline workflow without a major quality gain.

---

# Test 01 — MetaTailor garment conform / skin transfer

**Question:** can MetaTailor collapse the boring middle of Melusina outfit production?

Inputs:
- canonical Melusina skeletal body;
- one existing donor garment that currently requires fitting/weight work;
- 10 representative animation poses.

Steps:
1. import/send Melusina body;
2. import donor garment;
3. auto-fit / layer / relax garment;
4. generate provisional rig/weights;
5. return/export for Unreal;
6. test shoulder, elbow, waist, hip and crouch poses;
7. run Houdini deformation/intersection audit if available;
8. measure manual correction time.

Pass if:
- provisional fit and weights are materially faster than manual transfer;
- UVs/material boundaries survive;
- skeleton remains compatible;
- hero cleanup is local rather than complete rework.

Reject if it merely creates a differently broken garment.

---

# Test 02 — Chaos Outfit Asset on custom hero

**Question:** can UE5.8 Outfit Assets be useful as a Melodia wardrobe **assembly/data container** without adopting the MetaHuman body stack?

Use a disposable project/branch.

Steps:
1. enable Chaos Cloth Asset / Chaos Outfit Asset dependencies;
2. create a simple two-piece outfit asset;
3. test with a non-MetaHuman skeletal character/proxy;
4. inspect Dataflow organization;
5. verify simulation/render mesh ownership;
6. test assignment/rebuild workflow;
7. explicitly determine which resizing features are MetaHuman-dependent.

Pass if the asset/container architecture is reusable for custom heroes.

If not, document useful design patterns and reject direct integration.

---

# Test 03 — FluidNinja LIVE-2 P3 filter field

**Question:** does a local GPU simulation field make Horizon Eater substantially more convincing than authored vectors alone?

Sandbox map only.

Target scene:
- flat/grass test patch;
- player;
- directional filter spline;
- pollen Niagara;
- fog/mist presentation;
- one material/foliage response.

Compare:
A. FluidNinja local field;
B. Houdini-authored/static vector field;
C. direct Niagara directional force.

Measure:
- GPU time;
- memory;
- setup time;
- visual coherence;
- art-direction speed;
- whether multiple systems can share the same perceived flow.

Pass only if A produces meaningfully richer local response at sane cost.

Do not connect it to Oceanology water authority.

---

# Test 04 — Advanced Environment Interaction P2 contact evidence

**Question:** can persistent GPU contact history cheaply create biological evidence?

Prototype:
- one reactive membrane/ground patch;
- player foot contact;
- one Ebenezer-sized proxy contact;
- material darkening/indentation;
- optional Niagara spores emitted from recent contact.

Compare to a minimal project-owned render-target/RVT implementation.

Pass if it saves significant implementation time and remains easy to query/control.

---

# Test 05 — VectorayGen vs Houdini vector field

Create one P3 feeding-current field around simple filter geometry.

Deliver exactly the same target output from:
- VectorayGen;
- Houdini;
- hand-authored Niagara vector logic.

Score:
- setup minutes;
- art direction;
- geometry awareness;
- export friction;
- reuse across Niagara/materials.

Potential result:
VectorayGen becomes sketching tool; Houdini remains authoritative for world-derived fields.

---

# Test 06 — GeoGen vs Gaea vs World Creator

Same brief for all available tools:

> Serene chalk/highland steppe with believable erosion and one broad basin suitable for later Horizon Eater anatomical reinterpretation.

Timebox each to 20 minutes.

Export:
- height/terrain data;
- at least three useful masks;
- screenshot from same broad camera angle.

Keep the fastest tool whose output actually survives Houdini mutation.

Do not keep three terrain thumbnailers.

---

# Test 07 — Rokoko Vision 3 -> Cascadeur -> UE

Record a short physical performance:
- inspect;
- react;
- brace;
- recover.

Pipeline:
video -> Vision -> Cascadeur -> UE IK Retarget.

Measure total time to a usable gameplay/cinematic blockout versus direct keyframing.

Pass if body mechanics arrive faster even if fingers/face need replacement.

---

# Test 08 — RealityScan source-data loop

Capture one ordinary real object/material with strong natural irregularity:
- bark;
- stone;
- cloth fold;
- weathered wood;
- eroded concrete.

Pipeline:
RealityScan -> Houdini cleanup/analysis -> Copernicus/Substance stylization -> UE preview.

Question:
Does scanning give us useful structural/material truth faster than sourcing photos or building irregularity from zero?

Do not judge success by photorealism.

---

# Test 09 — Gaussian reference workflow

Optional if capture data is available.

Reality/video -> compatible splat reconstruction -> SuperSplat.

Test:
- cleanup;
- LOD streaming;
- walk mode;
- browser share;
- collision/proxy usefulness.

Pass condition is **reference/review utility**, not gameplay import.

---

# Test 10 — Errant Biomes vs UE PCG

Use existing SpeedTree assets.

Inputs:
- three plant species/variants;
- `moisture` mask;
- `wind_exposure` mask;
- `monolith_proximity` mask.

Build same biome in:
- current UE PCG workflow;
- Errant Biomes trial if available.

Evaluate:
- authoring time;
- debugging clarity;
- regeneration time;
- manual art direction;
- World Partition behavior;
- whether Houdini masks enter cleanly.

Adopt only if it improves daily environment iteration substantially.

---

# Test 11 — Voxel Plugin 2 / UE Mesh Terrain decision note

Do not force Voxel Plugin into UE5.8 if unsupported.

Instead record a capability matrix:

| Requirement | UE5.8 Mesh Terrain | Voxel Plugin 2 | Houdini static/state meshes |
| --- | --- | --- | --- |
| caves/overhangs | | | |
| PCG metadata | | | |
| runtime edits | | | |
| deterministic bake | | | |
| World Partition fit | | | |
| production maturity | | | |
| source-control friendliness | | | |

Only schedule a Voxel Plugin hands-on test when exact version compatibility is solved.

---

# Test 12 — InstaMAT / ArmorPaint / Material Maker triage

Do not learn three material tools.

Use one small ornate prop and compare only unique value:
- InstaMAT: parameterized procedural material + UE synchronization;
- ArmorPaint: GPU ray-traced bake + paint loop;
- Material Maker: fast portable/open procedural texture graph.

Baseline: Substance + Copernicus + current bake path.

Any candidate that cannot beat the baseline in one clearly defined category is parked.

---

# Test 13 — Style3D compatibility gate

No hands-on integration until vendor/source confirms project UE support.

Record:
- current supported UE versions;
- source availability;
- runtime packaging constraints;
- licensing;
- multilayer solver limitations;
- expected comparison against Chaos Cloth.

If UE5.8 becomes supported, test exactly one layered coat/skirt assembly.

---

# Test 14 — low-level GPU research notebook

**Not tomorrow unless Tier-S work is complete.**

Pick either NVIDIA Warp or Taichi, not both.

Implement one toy `FilterFlow` simulation:
- 100k–1M particles or samples;
- attraction toward curved target;
- obstacle SDF;
- export vector/velocity field.

Goal is to measure how quickly custom physics ideas can become bakeable data.

No game runtime integration.

---

# Test 15 — renderer frontier reading spike

No engine fork.

Create a one-page technical note after reading/running samples for:
- Slang;
- RTXNS;
- OpenUSD/Hydra 2/MaterialX;
- Hydra Merlin;
- RTX Mega Geometry.

Question:
Which technology changes a real Melodia decision in the next 12 months?

If answer is "none," keep WATCH status.

---

# Suggested execution order

### Highest production leverage
1. MetaTailor
2. Copernicus (from primary plan)
3. FluidNinja LIVE-2 or Advanced Environment Interaction
4. Unreal MCP (from primary plan)
5. IlluGen / VectorayGen
6. Rokoko Vision + Cascadeur

### High environment leverage
7. RealityScan
8. GeoGen/Gaea/World Creator comparison
9. Errant Biomes comparison
10. Mesh Terrain / Voxel capability matrix

### Only after above
11. material-editor alternatives
12. Gaussian reference stack
13. low-level GPU frameworks
14. neural/render research

---

# Desired end-of-day output

Do not end tomorrow with "everything seems cool."

End with something like:

```text
ADOPT
- MetaTailor for provisional outfit fitting
- Copernicus for anatomy-derived texture families
- IlluGen for VFX texture iteration

PARK
- FluidNinja until performance/UE5.8 build is stable
- Errant Biomes until PCG authoring becomes a bottleneck

REJECT
- Material tool X because Substance/COPs are faster

WATCH
- Chaos Outfit custom-character path
- Style3D UE5.8 support
- Voxel Plugin 2
- RTXNS / Slang / Mega Geometry
```

The actual decisions must come from measured tests, not this example.
