# PCG Production Contract

**Status:** CANONICAL DURABLE PCG AUTHORING CONTRACT  
**Current status / priorities / blockers:** `CURRENT_STATE.md` only.

This page defines how Melodia uses Unreal Engine 5.8 PCG, editor Python, chapter-specific biome derivatives, and semantic material data without creating a second gameplay authority.

## 1. Ownership

```text
gameplay / narrative / music truth
  -> existing C++ / Blueprint owners
  -> authored PCG source data
  -> optional UE5.8 Python Data Processor enrichment (EDITOR ONLY)
  -> native PCG filtering / transforms / spawning
  -> per-instance custom data
  -> materials / Niagara visualize semantics
```

Rules:

- C++ / existing gameplay systems decide what is true.
- PCG owns procedural spatial assembly.
- Python may inspect, enrich, configure, validate, and batch-author PCG data in the editor.
- The PCG Python Data Processor is **not** a packaged runtime/gameplay authority.
- Materials, Niagara, audio, and TD consume semantic values; they do not redefine gameplay truth.
- Shared hero graphs are reusable sources. Chapter/world graphs should normally be derivatives or wrappers rather than destructive edits to the shared source.

World/chapter ownership remains defined by `Docs/WorldBuilding/WORLD_BUILDING_SOURCE_OF_TRUTH.md`.

## 2. Validated Resonance Ecology path

The reusable UE5.8 authoring path proven in PRs #196, #198, and #203 is:

```text
existing point source / authored biome graph
  -> PCGPythonDataProcessor
       Resonance       float 0..1
       EcologyClass    int32
       MaterialVariant int32
       ScaleBias       float
  -> existing native PCG graph logic
  -> PCGStaticMeshSpawner
  -> PCGInstanceDataPackerByAttribute packs Resonance
  -> per-instance custom float
  -> material / presentation response
```

Canonical implementation:

- `Content/Python/pcg/resonance_ecology_processor.py`
- `Content/Python/pcg/apply_resonance_to_sea_above.py`
- `Content/Python/pcg/test_resonance_ecology.py`
- `_DECISION_LOG.md` decision 057

The semantic vocabulary may grow only when a real production consumer needs it. Do not build a generalized ecology ontology in advance.

## 3. Metadata rules that must not regress

### Inherit source metadata

Do **not** construct output with a bare `PCGPointData` + `create_empty_metadata()`. Python may read those attributes back while downstream PCG still cannot access them.

Use the proven pattern:

```python
result.initialize_from_data(data)
metadata = result.mutable_metadata()
src_metadata = data.const_metadata()
point.initialize_metadata(metadata, point, src_metadata)
```

This is what makes attributes such as `Resonance` visible to native downstream PCG accessors and instance packers.

### Preserve upstream authoring

Semantic enrichment composes with the graph it enters.

- multiply/combine `ScaleBias` with existing point scale rather than replacing authored scale;
- do **not** repurpose `point.density` as Resonance — density is PCG's culling channel, while Resonance is a semantic attribute;
- preserve the tags returned by `get_typed_inputs_by_pin_label`; downstream selectors may depend on them;
- treat this processor as **point-data-only** unless the engine bridge gains a verified safe way to marshal other `PCGData` types.

### Select the real data pins

`PCGPythonDataProcessor` exposes control pins such as `Execution Dependency` / `Overrides`. `output_pins[0]` is not guaranteed to be the point-data output.

Find the data pin by label and exclude control pins. Wiring a spawner from a control pin can look connected while carrying no points.

### Configure the instance packer correctly

`instance_data_packer_parameters` is effectively read-only from Python. Set the spawner's `instance_data_packer_type` to `PCGInstanceDataPackerByAttribute` and then configure the created parameter object.

For `PCGAttributePropertyInputSelector`, the verified Python route is `import_text(...)`; `set_attribute_name` has value semantics and helper variants may return a base struct the packer array rejects.

### Disabled is not bypassed

Disabling a Python Data Processor is **not** a safe bypass: it emits nothing and can starve downstream spawners. Removal/rollback must reconnect the original upstream node directly to the downstream consumer.

`apply_resonance_to_sea_above.py` therefore supports insert/repair/remove rather than relying on node disable state.

## 4. Sea Above production pattern

Sea Above established the chapter-specific derivative pattern:

- style root: `/Game/EnvSandbox/PCG/Styles/SeaAbove`;
- shared musical hero graphs under `/Game/EnvSandbox/PCG/Musical/Hero` remain reusable source authority;
- Sea Above variants keep their generators, splines, raycast grounding, transforms, and mesh choices;
- semantic enrichment is spliced immediately before the relevant `StaticMeshSpawner` rather than replacing the graph;
- `Resonance` is packed into per-instance custom data so materials can respond without Python writing directly to the generated ISM after the fact.

Live proof from #203 on `PCG_East_PhyllotaxisCourtyard`:

- 140 generated instances;
- 1 per-instance custom float;
- `Resonance` range 0.030–0.925;
- instance count unchanged from the pre-enrichment baseline.

The generic fix in #198 was also live-verified with 6,835 instances carrying native packed `Resonance` custom data, with no Python post-pass mutating ISM custom data.

Commit `6d9bb2b1` / PR #213 later reconciled Sea Above PCG style assets plus the `LV_SeaAbove_Prototype` external actors onto current `main`, including the Phyllotaxis Courtyard and Xylophone Trail style graphs. Treat editor-only success as incomplete until the intended `.uasset` and World Partition external-actor packages are actually tracked.

## 5. Validation contract

For a new semantic PCG workflow, prove the chain in increasing strength:

1. **Offline semantics** — deterministic pure-Python tests for derivation rules.
2. **Editor graph** — processor executes and native PCG can read the metadata.
3. **Spawner** — native `PCGInstanceDataPackerByAttribute` produces the expected custom-data count/range.
4. **Visual consumer** — a material or other presentation consumer visibly reads the packed value.
5. **Production derivative** — one real chapter graph preserves its authored count/composition while carrying the new semantics.
6. **Persistence/provenance** — intended PCG graph and external-actor packages are tracked on `main`.

Do not call a workflow reusable merely because the Python script prints the expected values.

PCG generation is asynchronous. Do not assume a `generate()` call has completed before reading generated instance counts in the same editor call; use a real completion/readback boundary.

## 6. Scale and performance rule

Use the Python Data Processor for **authoring-time semantic enrichment of bounded production graphs**, not as a universal high-volume compute layer.

For very dense ecologies (roughly 100k+ points or anything shown by profiling to be Python-bound), prefer native/GPU PCG or precomputed/baked data. Preserve the same semantic contract at the consumer boundary rather than moving gameplay truth into Python.

## 7. Existing reusable PCG stacks

### Expanded Zen/Sakura stack

- `Content/Python/setup_pcg_universal.py` builds the expanded universal graph set.
- `Content/Python/setup_pcg_zen_sakura.py` applies the layered Zen/Sakura stack end to end on `L_Template` or an explicit `--level`.
- Generated layers include Meadow Bloom, Blossom Path, Lantern Grove, Garden Ruins, Sakura Petal Drift, and Zen Moss Groundcover.
- Verification outputs include:
  - `Saved/Audit/pcg_universal_build.json`
  - `Saved/Audit/pcg_universal_audit.json`
  - `Saved/Audit/pcg_zen_sakura_apply.json`

### Supporting references

- `PCG_REFINEMENT_REPORT.md`
- `Docs/PCG_PORTFOLIO_PLAN.md`
- `Content/Python/pcg_portfolio_standards.py`
- `Content/Python/pcg_graph_builder.py`
- `Docs/Production/PCG/SAKURA_WATER_PCG_EXPANSION_REVIEW.md`

These references may describe older experiments; this contract owns the durable Python→PCG semantic-enrichment rules above.

## 8. Musical-biome derivative rule (2026-10-03)

A further musical biome is a chapter-specific derivative of a shared `/Game/EnvSandbox/PCG/Musical/Hero` graph, never a rewrite of the hero source. Enrich with the existing `Resonance` / `EcologyClass` / `MaterialVariant` / `ScaleBias` contract (§2–§3); Houdini Foundry field data enters only as authored point attributes or PCG-sampled textures through `world_compiler_points` / `pcg_graph` consumers (`specs/houdini_foundry/README.md`). New biome eligibility ids must not collide with existing `EcologyClass` semantics. Prove per §5 on one bounded graph before calling the biome reusable.
