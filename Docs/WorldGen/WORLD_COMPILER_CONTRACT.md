# World Compiler Contract

> **Agent entry:** use [`Docs/Production/AGENT_PRODUCTION_PLAYBOOK.md`](../Production/AGENT_PRODUCTION_PLAYBOOK.md) to route work into this contract. `CURRENT_STATE.md` remains status authority. This contract owns compiled-world interfaces; it is not a second status surface.

**Status:** CANONICAL DATA CONTRACT (undated; supersedes the dated scaffold)  
**Extracted from:** [`Docs/Houdini/MELODIA_WORLD_COMPILER_TOMORROW_SCAFFOLD_2026-08-30.md`](../Houdini/MELODIA_WORLD_COMPILER_TOMORROW_SCAFFOLD_2026-08-30.md) ("extract the stable contracts into an undated canonical doc later"), [`specs/resonant_world_manifest.v1.json`](../../specs/resonant_world_manifest.v1.json), [`Docs/WorldGen/TERRAIN_HANDOFF_CONTRACT.md`](TERRAIN_HANDOFF_CONTRACT.md), [`Docs/Production/PCG/README.md`](../Production/PCG/README.md), and the Muse flower-field brief (2026-09-16).  
**Authority above this page:** [`Docs/WorldBuilding/WORLD_BUILDING_SOURCE_OF_TRUTH.md`](../WorldBuilding/WORLD_BUILDING_SOURCE_OF_TRUTH.md). Status of any compiled world is recorded only in [`CURRENT_STATE.md`](../../CURRENT_STATE.md).

> **Houdini authors impossible evidence. Unreal decides when the player experiences it.**  
> C++ decides what is true. PCG places. Materials read. TouchDesigner performs. The compiler is content over that stack, never a new authority.

---

## 1. Definition

The World Compiler is a **deterministic, offline compiler** that turns a small **recipe** (seed + musical identity + place + palette) into a validated **bundle** of point fields, dressing tables, FX anchors, signal bindings, and optional chapter scaffolding that the existing Unreal owners consume.

It is a *unification*, not a new system. Every stage is an existing module with a stable entry point:

| Stage | Owner module (reused, not rewritten) | Output |
|---|---|---|
| `identity` | `Content/Python/resonant_world_generator.py` (`WorldConfig.from_seed`, `chunk_manifest`, `stable_int`) | world config, chunk manifest, `stable_seed` per chunk |
| `terrain` (optional) | `Tools/terrain_handoff.py` (`melodia.terrain_handoff.v1`) | validated Mesh Terrain handoff reference |
| `ecology` | **new** in `Tools/world_compiler.py` | `points.csv` (plant field), `fx_anchors.csv` (Niagara anchors) |
| `dressing` | `Content/Python/resonant_world_asset_constellation.py` + recipe `species[]` | `dressing_table.json` (species -> mesh/MI/band MI) |
| `signal` | contract check only, against `specs/niagara_mpc_bindings.json` and the MPC pair | `signal_bindings.json` |
| `chapter` (optional) | `Tools/scaffold_chapter.py` | chapter folder reference |
| `bundle` | **new** bundle writer + `Tools/evidence_envelope.py` | `manifest.json`, `evidence_envelope.json` |

Determinism rule: the same recipe (byte-identical) compiled by the same compiler version produces byte-identical `points.csv`, `fx_anchors.csv`, `dressing_table.json`, `signal_bindings.json`, and the same `manifest.sha256`. Timestamps live only in `evidence_envelope.json`.

### 1.1 What the compiler owns and does not own

| Owns | Never owns |
|---|---|
| identity derivation from seed (`stable_int(seed, *parts)`, NMS-style sub-seeding) | actors, level saves, external-actor packages |
| point fields and their attribute vocabulary | PCG graph *structure* (edges, nodes) |
| species / band dressing tables | material masters, MPC parameters, MPC writes |
| FX anchor positions and user-parameter values | Niagara system graphs |
| signal *binding checks* (which lane feeds which parameter) | the audio writer, the cymatics writer, a second MPC |
| chapter scaffold *request* | quest truth, save data, combat, rewards |

### 1.2 The three systems from the 08-30 scaffold, as compiler stages

| 08-30 system | Compiler form | Status |
|---|---|---|
| `MIDI_WORLD_GRAMMAR` | `recipe.motif` input: a `melodia_roll_field_v1` path or a phrase manifest handled by `resonant_world_phrase_bridge.py`; the `ecology` stage may read `bar/beat/pitch` to bias band phase | MIDI ecology only — not Jev, not PhraseBus OSC (`Tools/phrase_bridge/` + `UMelodiaPhraseBusSubsystem` `RecvFrom` on `:9000`) |
| `MONOLITH_INFLUENCE` | optional `recipe.influence[]` fields (`monolith_id`, `influence`, `anatomy_role`, `foreshadow_level`) copied onto points as attributes | schema only; no deformation |
| `REGION_HISTORY` | `melodia_region_history_v1` event list, passed through to the bundle untouched | schema only |

---

## 2. Recipe (`world_recipe.v1`)

Schema: [`specs/schemas/world_recipe.v1.schema.json`](../../specs/schemas/world_recipe.v1.schema.json). Recipes live under `recipes/`. A recipe is small, human-readable, and never contains workstation paths.

```json
{
  "schema": "melodia.world_recipe.v1",
  "recipe_id": "morning_rainbow_bloom",
  "world_seed": 3900,
  "identity": {"mode_id": "ionian", "root_pitch_class": 0, "bpm": 96, "movement_id": "petal_cantata"},
    "place": {
    "level": "/Game/Melodia/Levels/Opening/L_MelusinaMorning",
    "anchor_cm": [-2300.0, 1442.0, 0.0],
    "up_axis_offset_cm": 8.0,
    "clearance": {
      "circles": [{"label": "pond", "center_cm": [-950.0, 2300.0], "radius_cm": 260.0}],
      "capsules": [{"label": "wake_path", "a_cm": [1435.0, 2321.0], "b_cm": [-888.0, 2140.0], "radius_cm": 110.0}]
    }
  },
  "field": {"kind": "radial_bands", "band_count": 7, "inner_radius_cm": 200.0, "band_width_cm": 250.0,
            "sector_deg": [0.0, 360.0], "density_per_m2": 3.5, "phyllotaxis_angle_rad": 2.399963,
            "chladni": {"modes": [[2,3],[3,4],[4,5],[5,6],[6,7],[7,8],[8,9]], "threshold": 0.35}},
  "species": [ {"species_id": "speedtree_meadow", "ground_labels": ["BrushifyIsland_"],
                "band_mi_prefix": "/Game/EnvSandbox/Materials/Instances/Flora/Rainbow/MI_RainbowSpeedTree_", "weight": 1.0} ],
  "palette": {"bands": [{"label": "B0_Red", "tint": [1.0, 0.18, 0.22]}, "..."]},
  "fx": {"pack": "specs/niagara/morning_hero_fx_pack.v1.json", "anchors_per_band": {"petal": 1, "pollen": 1}, "mist_anchors": 2, "windfront_anchors": 1},
  "signal": {"source_mpc": "/Game/Melodia/_PROJECT/04_Materials/MPC_Melodia_Palette", "driver_mpc": "/Game/Melodia/Cymatics/MPC_Cymatics_Driver",
             "lanes": ["Cymatic_EmissiveScale", "Cymatic_IridescenceShift", "Cymatic_BeatPulse", "Cymatic_WindDirX", "Cymatic_WindDirY", "Cymatic_WindStrength"]},
  "terrain": null,
  "chapter": null,
  "muse": {"brief": "Docs/Handoffs/MUSE_LIVING_FLOWER_FIELD_TECHNICAL_BRIEF_2026-09-16.md", "restraint": "hue travel <= 0.5 weight"}
}
```

Rules:

- `world_seed` is the only entropy. Every derived value is `stable_int(world_seed, recipe_id, stage, ...)`.
- `place.anchor_cm` is the field origin in level space. Bands are measured from it.
- `clearance` masks are honoured by **both** plant points and FX anchors. Circles remove points inside; capsules remove points within `radius_cm` of the segment.
- `field.kind` is `radial_bands` in v1. Other kinds (`chunk_grid`, `path_ribbon`) are additive schema versions, not edits to v1.
- `species[].band_mi_prefix + palette.bands[b].label` must resolve to an existing MI in the UE lane; the compiler only writes the *path string*.
- `terrain.kind: "ground_probe"` makes placement **height-aware and ground-aware**: `world_compiler_ue.py probe_ground` line-traces a `probe_step_cm` grid inside `probe_radius_cm` and writes `recipes/ground/<recipe_id>_ground_probe.json`; the ecology stage then keeps only cells whose hit z lies in `walkable_z_cm` (excluding `exclude_actor_classes`), and writes the hit z (+`up_axis_offset_cm`) into `Position`. The UE template graph additionally projects onto world geometry (World Ray Hit + Projection), so the count gate uses a 95 % survival tolerance in this mode. `field.sector_deg [center, half_width]` restricts the phyllotaxis sweep to the arc where ground exists. Live Morning placement is **not** a bedroom-floor arc — see the geometry rule below.

**Live Morning geometry (`recipes/morning_rainbow_bloom.v1.json`, close-out 2026-09-19 PASS):**

| Band | Plantable ground | Never plant |
|---|---|---|
| Flowers (`speedtree_meadow`) | `BrushifyIsland_*` only | bedroom / `SM_classic_arch_*` / `Sphere3D` / `WC_DellFloor` / Landscape |
| Dressing (`brushify_overgrowth` / `brushify_roots` / `brushify_bush`) | `WC_EscherWalk_*` plus island skirts | a second meadow, Engine cubes, Houdini as live player geo |

The recipe keepout includes `bedroom_keepout` (center ~`[900, 2300]`, radius 1100 cm), pond water, bed, sheep rest, and wake-path capsules. Do not invent a new meadow. Compile stays CLI: `python Tools/world_compiler.py compile recipes/morning_rainbow_bloom.v1.json` then `python Tools/world_compiler_ue_driver.py Saved/WorldCompiler/morning_rainbow_bloom_3900 --skip-scaffold --fx --lookdev`.

**Historical 09-17 probe (do not follow):** a 2.6 km grid found no dell floor; the pond centroid `(-950, 2300)` sits over open water / void, and the only nearby hit then was the bedroom floor (`SM_classic_arch_24..27`). That probe predates BrushifyIsland targeting and the bedroom keepout. Agents that still arc seven bands across the bedroom are following this stale note.

---

## 3. Bundle (`world_compiler_bundle.v1`)

Schema: [`specs/schemas/world_compiler_bundle.v1.schema.json`](../../specs/schemas/world_compiler_bundle.v1.schema.json). Output root: `Saved/WorldCompiler/<recipe_id>_<world_seed>/`.

| File | Contents |
|---|---|
| `manifest.json` | recipe echo, compiler version, per-stage `status`, per-band counts, `sha256` of every table, `place`, resolved species table reference |
| `points.csv` | one row per plant instance (see Â§4) |
| `fx_anchors.csv` | one row per Niagara anchor (see Â§5) |
| `dressing_table.json` | species -> mesh, per-band MI path, packer attribute list |
| `signal_bindings.json` | which MPC lane feeds which material/Niagara parameter; `check` result per lane |
| `evidence_envelope.json` | `melodia.evidence_envelope.v1`, `kind: static`, produced by `Tools/evidence_envelope.py` |
| `identity.json` | `resonant_world_generator` chunk manifest for the anchor chunk |
| `terrain.json` / `chapter.json` | only when the stage ran |

`manifest.status` follows the 08-30 fail-closed convention: `PASS | FAIL | SKIPPED | EXPECTED_FAIL`. A stage that did not run is `SKIPPED`, never omitted. The bundle supersedes `melodia_world_compiler_output_v0`.

---

## 4. Point-field attribute contract (`points.csv`)

Column order is fixed; the UE `Load Data Table` node maps columns to a `FWorldCompilerPoint` row struct by name.

| column | type | meaning | source |
|---|---|---|---|
| `point_id` | int | stable per (recipe, seed, index) | ecology |
| `x`, `y`, `z` | float cm | level-space position (`z` = anchor z + `up_axis_offset_cm`; UE lane may re-project to ground) | ecology |
| `yaw` | float deg | deterministic | ecology |
| `scale` | float | 0.5..1.1 default range | ecology |
| `species_id` | string | recipe `species[].species_id` | dressing |
| `variant_id` | int | per-species variant bucket | ecology |
| `band` | int | 0..band_count-1 (ROYGBIV) | ecology |
| `mode_n`, `mode_m` | int | Chladni mode of the band | ecology |
| `cluster_id` | int | phyllotaxis arm bucket | ecology |
| `hue_seed` | float 0..1 | per-instance hue phase, feeds `MF_MelodiaWindHueReveal.PerInstanceHueSeed` | ecology |
| `wind_phase` | float 0..1 | bend phase offset | ecology |
| `wind_response` | float 0..1 | bend amplitude ceiling | ecology |
| `sparkle_response` | float 0..1 | sparkle ceiling | ecology |
| `hero_weight` | float 0..1 | 1 near authored moments, 0 in the envelope | ecology |
| `height_class` | int 0..2 | low/mid/tall | ecology |
| `density_class` | int 0..2 | sparse/normal/dense | ecology |
| `Resonance` | float 0..1 | Resonance Ecology field (`Content/Python/pcg/resonance_ecology_processor.derive`) | identity + band |
| `EcologyClass` | int 0..2 | Resonance Ecology class | identity |
| `MaterialVariant` | int | == `band`; index into the band MI list | band |
| `ScaleBias` | float | Resonance Ecology scale bias | ecology |
| `mesh` | string | soft object path of the species mesh for this `variant_id` (`species.meshes[variant_id % n]`, e.g. `/Game/EnvSandbox/Meshes/Environment/flower_redA/StaticMeshes/flower_redA.flower_redA`) | dressing |
| `material` | string | soft object path of the band MI | dressing |
| `StemMaterial` | string | soft object path for material slot 0 (stem/leaf); empty for single-slot meshes | dressing |
| `Position`, `Rotation`, `Scale3D` | Vector / Rotator / Vector | struct-typed mirrors of `x,y,z` / `yaw` / `scale` so `Load Data Table` maps them straight to `$Position/$Rotation/$Scale` | ecology |

**Column naming rule:** UE `FName` comparison is case-insensitive, so no two columns may differ only by case. (`Scale` vs `scale` aliased in the DataTable on 09-17 and every instance landed at the origin; hence `Scale3D`.) `test_world_compiler.py` enforces this.

**Mesh scale finding (09-17):** `/Game/EnvSandbox/Meshes/SurrealFlora/Petal_*` are pieces of the GhostLotus landmark (box extent ~83 x 73 x 122 **m**, pivots baked thousands of cm off-origin). They are hero set pieces, not ground flora. The Morning recipe uses the nine `Environment/flower_{red,purple,yellow}{A,B,C}` meshes (8-15 cm extents) at `scale_range [1.8, 3.2]` so blooms read at ~30-60 cm under the band MIs.

**Material slot finding (09-17):** the flower kit has two slots (0 = stem/leaf `MI_Flat_grass`, 1 = petal colour). `PCGMeshSelectorByAttribute.MaterialOverrideAttributes` is **positional** (index == slot), so a single `material` entry tints the stems and leaves the petals on their baked colour — the field read as mixed noise. The manifest now emits `ue_lane.material_override_attributes = ["StemMaterial", "material"]` whenever a species declares `stem_material`, and the count step finds the band MI on whichever slot carries it.

**Row-struct drift:** the CSV importer silently drops columns the row struct lacks (log only: `Cannot find Property for column`). `step_table` reads every column back and reports `missing_columns`; the driver then runs `reset_table` -> `ensure_struct` -> `table` so a column-contract change never ships a half-filled table.

The UE spawner uses `PCGMeshSelectorByAttribute` on `mesh` with material override by attribute on `[StemMaterial, material]`, so the template graph is **fully data-driven** (one spawner, no per-species branches). It packs `hue_seed, Resonance, wind_response` (and optionally `sparkle_response`) as per-instance custom data via `PCGInstanceDataPackerByAttribute`; the shared material reads them as instance custom data, so **no unique MI per instance**.

Row struct: `/Game/Melodia/WorldCompiler/S_WorldCompilerPoint` (User Defined Struct, created once via Monolith `blueprint.create_user_defined_struct` from [`specs/schemas/world_compiler_point_row.v1.json`](../../specs/schemas/world_compiler_point_row.v1.json)). DataTable CSV import treats the first column as the row name, so the UE lane prepends a `---` column (`p<point_id>`).

---

## 5. FX anchor contract (`fx_anchors.csv`)

| column | type | meaning |
|---|---|---|
| `anchor_id` | string | `fx_<kind>_<band>_<n>` |
| `fx_kind` | enum | `petal`, `pollen`, `mist`, `windfront` |
| `band` | int | -1 for band-less anchors |
| `x`, `y`, `z` | float cm | level-space |
| `hue_seed` | float | band hue phase |
| `spawn_multiplier` | float | CSV artist ceiling. The UE lane writes pack User names: `User.PetalSpawnMultiplier` / `User.MoteSpawnMultiplier` / `User.MistDensity` / `User.WindFrontVisible`. Never a generic `SpawnMultiplier`. |
| `bounds_cm` | float | fixed bounds the UE lane applies (300..500) |
| `system` | string | NS asset path from the FX pack |
| `material_instance` | string | MI path the UE lane forges (`MI_Morning_<Kind>_B<band>`) |

Anchors respect the same clearance masks as points. The UE lane places `NiagaraActor`s tagged `WorldCompiler.<compile_id>` and deletes prior-tagged actors before re-placing. Niagara never goes through PCG spawners in v1. `step_fx_place` writes those pack User names from the CSV column; do not bind `SpawnMultiplier`.

---

## 6. UE lane (editor only)

The compiler never imports `unreal`. `Content/Python/world_compiler_ue.py` is the *consumer* and runs only inside the editor (Monolith `editor.run_python` or `UnrealEditor-Cmd`).

### 6.0 Spatial preflight (required)

Any World Compiler, PCG, or Monolith **spatial** edit (points, volumes, dressing, lookdev cameras, actor moves, graph generate, island/walk placement) requires the existing scene-context cycle in the **already-open** editor **before** the first mutation and **after** the change. This is not a new framework.

```text
CURRENT_STATE + this contract
  -> scene_context_cycle.begin()
  -> inspect packet + live editor
  -> bounded WC/PCG/Monolith change
  -> scene_context_cycle.end()
  -> falsify route / silhouette / PCG / scale
  -> owner judges viewport
```

| Tool | Role |
|---|---|
| [`Content/Python/scene_context_snapshot.py`](../../Content/Python/scene_context_snapshot.py) | one compact live 3D packet |
| [`Content/Python/scene_context_cycle.py`](../../Content/Python/scene_context_cycle.py) | `begin()` / `end()` before/after + `scene_context_diff.json` |

Packets land under `Saved/Audit/SceneContext/<LevelName>/` and are **ephemeral evidence**, not status. One editor, one writer: Monolith **`127.0.0.1:9316`** only. A second editor logs to `Saved/Logs/BS_GodFile_2.log`. Skip-scaffold / `--fx` / `--lookdev` close-out still counts as a spatial edit: run the cycle around the driver, do not invent a second spatial AI.

1. Fill `points.csv` into DataTable `/Game/Melodia/WorldCompiler/DT_<recipe_id>_Points` (row struct `S_WorldCompilerPoint`) with `DataTableFunctionLibrary.fill_data_table_from_csv_string`. The template graph's `Load Data Table` node points at that fixed asset path; the compiler never sets graph parameters, it only replaces rows. (`PCGGraphInstance` parameter overrides are not Python-settable in 5.8; the fixed path is the honest design.)
2. Verify/forge band MIs (`MI_RainbowPetal_B0..B6`, parent `M_Master_Toon_Universal`, only `BaseTint` differs). Never edit the parent. When `palette.wind` is set, also forge the wind hue-reveal family (`MI_RainbowPetal_Wind_B0..B6`, parent `M_MelodiaPlant_Wind` -- the Muse-brief plant master that already calls `MF_MelodiaWindHueReveal` and reads `MPC_Melodia_Palette.WindDirX/WindDirY/WindStrength`). `palette.active_lane` chooses which family the `material` column names; the compiler never edits either parent and never writes a collection parameter. Signal chain verified live 09-17: palette lanes declared (source), `UMelodiaCymaticsWriterSubsystem` forwards `Cymatic_WindDirX/Y/WindStrength`, driver lanes declared. Wind A/B (`Saved/Audit/Screens/world_compiler_morning_wind_*`): undriven == natural albedo, driven east vs north differ; the reveal is subtle at the MF's 0.5 weight under night lighting -- owner judges weight at PIE.
3. Place **one** bounded `PCGVolume` (label `WC_<recipe_id>_Field`, tag `WorldCompiler.<compile_id>`) at `place.anchor_cm`, scaled to the outer radius, with the template graph `PCG_WorldCompiler_PointField`. The `template_scaffold` step builds and wires that graph and **verifies every edge by reading the pins back** (`edges_verified` in the step record); anything unverified is written to `owner_todo`. Root cause of the 09-15 "silent `add_edge` no-op": the graph Output node's *input* pin is labelled `Out` (it mirrors the graph output), not `In`; `add_edge(..., out_node, "In")` returns True and creates nothing. Read the label, never guess it. Re-running deletes tagged actors first.
4. Generate; poll across frames until `generated` is true and ISM instance counts are stable; read per-band counts (ISM components grouped by material); save with `unattended`; reload the level; recount.
5. `--fx`: forge FX MIs, place tagged `NiagaraActor`s from `fx_anchors.csv`.
6. Write `Saved/Audit/world_compiler_<recipe_id>_proof_<date>.json`.

Template graph (scaffolded by `world_compiler_ue.py template_scaffold`, edge-verified, tracked on `main`):

```text
Load Data Table (DT_<recipe_id>_Points; row struct S_WorldCompilerPoint)
  attribute mapping: Position -> $Position, Rotation -> $Rotation, Scale3D -> $Scale (all other columns become attributes)
  -> Static Mesh Spawner
       MeshSelector  = PCGMeshSelectorByAttribute (attribute: mesh; material overrides by attribute: [StemMaterial, material] == slots [0, 1])
       InstancePacker = PCGInstanceDataPackerByAttribute (hue_seed, Resonance, wind_response, sparkle_response)
       componentless (FastGeo) OFF until the 5.8 soft-release popping bug is fixed
  -> Output
```

Nothing else. Species and band selection live in the table, not in the graph.

### 6.1 Editor front door (bookmark, not a second compiler)

`UWorldRecipe` (`Source/BS_GodFile/MelodiaIntegration/WorldRecipe.h`) is a **game-module** `UPrimaryDataAsset` bookmark: `RecipeId`, `WorldSeed`, repo-relative `RecipeRelPath`, level soft path, last bundle/proof paths. It does not compile. JSON under `recipes/` remains canonical. Do not put this type in MelodiaCore.

`EUW_WorldCompiler` (`/Game/Melodia/WorldCompiler/EUW_WorldCompiler`) plus `Content/Python/world_compiler_panel.py` **Apply / Cleanup / Capture / status** only. Compile remains `Tools/world_compiler.py` and `Tools/world_compiler_ue_driver.py`.

Lookdev cameras live on `recipe.lookdev.cameras[]` only (not on the DataAsset). Lane steps `lookdev_cameras` / `lookdev_capture` spawn tagged `WC_Lookdev_*` actors (`WorldCompiler.lookdev`) and write `Saved/Audit/Screens/wc_<recipe>_<name>_<date>.png` with the frozen PPV stack unchanged. Houdini OBJ/HDA overlays (`Houdini_RainbowBloom_3900`, `HoudiniEngine_RainbowBloom_3900`) are hidden; the PCG ISM field is the only visible chorus.

Driver: `python Tools/world_compiler_ue_driver.py Saved/WorldCompiler/morning_rainbow_bloom_3900 --lookdev`.

---

## 7. Evidence ladder for a compiled world

Mirrors [`Docs/Production/PCG/README.md`](../Production/PCG/README.md) Â§5. A compiled world is only as proven as the highest rung with evidence on `main`.

1. **Offline** â€” `Tools/test_world_compiler.py` passes: schema, determinism (two runs, identical SHA), band counts equal the manifest, clearance masks honoured.
2. **Editor graph** â€” DataTable imports; template graph reads it without edits.
3. **Spawner counts** â€” per-band instance counts > 0 and equal after save + reload.
4. **Visual consumer** â€” the band MIs visibly read `hue_seed` / `Cymatic_Wind*` (PIE still at the trove's low-dolly framing).
5. **Reload** â€” level reopened, counts identical.
6. **Tracked** â€” DataTable, template graph, band MIs, and the level's external actors are on `main`.

Record the rung reached in `CURRENT_STATE.md` Â§2 ("Resonant World generator + World Compiler" row). Never write "LIVE PROVEN" from an offline run.

---

## 8. Stop rules (inherited verbatim)

From [`WORLD_BUILDING_SOURCE_OF_TRUTH.md`](../WorldBuilding/WORLD_BUILDING_SOURCE_OF_TRUTH.md) Â§5 â€” before extending the compiler, ask:

1. Does current C++ / Blueprint architecture already own this truth?
2. Is this a presentation consumer instead of a new authority?
3. Does the chapter add **data** (Quill, allowlist preview, meshes, outfits, songs, PCG) rather than a subsystem?
4. For Sheep / cymatics: does it obey Board 06 + the Nikki Cymatics material path?
5. For TD: does it reuse OSC `:9000` / existing semantic music architecture?
6. Is laptop Geometry Nodes work being deliberately promoted rather than blindly merged?

Hard no's: no second combat authority; no second SaveGame authority; no second HUD writer; no fifth wardrobe track; no fourth rhythm path; TouchDesigner must not own save/rewards/quest/recruitment/traversal/combat outcomes; `melodia:item:` remains a logging stub.

Compiler-specific hard no's:

- no `import unreal` in `Tools/world_compiler.py`
- no PCG edge/node edits from Python
- no writes to `MPC_Melodia_Palette` or `MPC_Cymatics_Driver` (the palette writer and `UMelodiaCymaticsWriterSubsystem` are the only writers)
- no new material master per effect; band MIs share one parent, FX MIs share the four hero parents
- no uniform density: `hero_weight` and `density_class` exist so the compiler produces an envelope around authored moments, never a carpet
- no bedroom / Sphere3D / `WC_DellFloor` meadow; flowers stay on `BrushifyIsland_*`, dressing on `WC_EscherWalk_*` plus island skirts
- no skipping `scene_context_cycle.begin/end` around spatial WC/PCG/Monolith edits; no second Monolith / second editor
- no generic Niagara `SpawnMultiplier`; WC FX writes pack User names only
- no Jev compile / MCP actor moves; PhraseBus is `RecvFrom` transport on `:9000`, not a second compiler

---

## 9. Expansion path (data, not code)

Same CLI, different recipe: a Sea Above chunk (`field.kind: chunk_grid`, hierarchical PCG grids 51200 / 25600 / 12800), a Shorewake chapter package via the `chapter` stage, Melusina outfit voicing per movement via `resonant_world_wardrobe_bridge.py`. Each is a new `field.kind` schema version and a recipe file; none is a compiler rewrite.

### 9.1 Detail families (landed: `melody_glitter`, 2026-09-23)

A second MI family inside one recipe needs no graph or authority change:

- Species-level `band_mi_prefix` wins over the `palette.active_lane` prefix (flowers already carry the wind prefix verbatim, dressing carries none, so legacy output is byte-identical).
- Species-level `scale_range` overrides `field.scale_range` (pin the field value on existing species when introducing this).
- `palette.glitter` (schema-optional, mirrors `palette.wind`) emits `dressing_table.glitter_lane`; the UE `glitter_materials` step forges one MI per band (tint params + optional scalar overrides, parent graph untouched).
- Detail MIs share one existing parent and differ only in tint/scalars — never a new master per effect.
- **Warm the mesh:** a never-before-generated species mesh is still compiling on first generate (`Waiting for static meshes to be ready`) and the selector silently falls back per-point — always generate twice and recount per MI family before capturing.
- Fairy dust + trails (landed 2026-09-27, Jev `F_FAIRY_TRAILS_COMPILER` 0.95): species-level `pitch_deg`/`pitch_jitter_deg` write flat-lay angles into the point `Rotation` column (90 = lying flat); `field.trail_arcs` emits deliberate spill arcs (`cluster_id` >= 900 marks trail rows; same ground + clearance filters, no chladni thinning); `palette.glitter.brightness_steps` forges one MI per band per step (1.0 keeps the canonical name, others `_L<pct>` with pre-scaled tints) for per-point glint variance. All three keys absent = byte-identical legacy output. No baked pile meshes (Jev killed the bake 0.0: Hython absent, Engine license failed 09-24).
