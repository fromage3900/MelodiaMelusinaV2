# Resonant World Asset Constellation — 2026-08-22

This pass turns the existing repository inventory into a deterministic, semantic
read model for a musical-voxel world chunk. It is the layer between the broad
asset atlas and any future Unreal PCG materialization.

## What it binds

For a `(seed, movement, chunk_x, chunk_y, archetype)` tuple,
`Content/Python/resonant_world_asset_constellation.py` selects and validates:

- terrain, structure, flora, ornament, material, water, VFX, wardrobe, music,
  character, population, quantum, and UI references;
- only project-backed `/Game` references are marked `runtime_ready`;
- manifest-only wardrobe, population, Niagara, and water records remain
  authoring/read-model references until their Unreal assets exist;
- archive, quarantine, deprecated, cache, build, and external-actor paths are
  excluded;
- Melusina hair is a water-shader reference, never a traversable water body.

The resulting magical moment is a world verb, not a loot table: Bloom opens a
petal memory, Weave lays a constellation hem, Conduct carries a tide chord,
Compose grows a living score, Drift reveals a ribbon mirage, and Resolve turns
beautiful dissonance into a survivable route.

## Styling and capability boundary

The read model deliberately keeps appearance separate from capability. A
wardrobe/archetype can supply the visual language and effect/scene-preview
surfaces; the resonant form and canonical traversal subsystem still own the
actual ability. The constellation does not equip a costume, grant a capability,
apply traversal, spawn an actor, award currency, or write a save.

## Quantum setup

Quantum is used only as a low-frequency preparation selector:

- exactly two movement candidates;
- preferred operation: `QuantumGameplay.WorldComposer.PickMovement`;
- preferred backend: Q# simulator, with a classical baseline fallback;
- winner, baseline winner, backend, and trace are persisted before any future
  authored PCG apply;
- never per-frame traversal, individual-voxel selection, input grading, or
  reward grants.

This is a selector contract, not a claim of quantum advantage or a quantum
voxel generator.

## Echo and PIE verification

Every constellation includes a verification snapshot. Echo remains authoritative
through `Saved/gate_ledger.json`; `python Tools/echo_run.py status` is the read
back of that ledger. PIE remains a separate editor-backed proof path through
`Tools/playtest_harness.py`. A green deterministic compiler test or constellation
read model is never reported as PIE proof.

Current reproducible checks:

```powershell
python Tools/test_echo_contract.py
python Tools/echo_run.py validate-spec specs/wardrobe_ch2_pipeline.json
python Tools/echo_run.py status
python Tools/playtest_harness.py preflight
python Tools/playtest_harness.py run --map L_KaleidoNave --backend auto
```

The last command requires one healthy Unreal editor/Monolith session. A HOLD or
transport failure does not write a pass row. World-specific PIE evidence is
currently `not_yet_observed` in the constellation snapshot.

## Webfront/lookdev review filenames

These existing project assets are the first visual review set for the webfront
lane; no `my-site-clean` files are changed by this pass:

| File | Intended movement | Look/material role |
|---|---|---|
| `Content/Melodia/_PROJECT/Meshes/RenderTerrains/SM_Terrain_SakuraDream.uasset` | `petal_cantata` | Sakura Dream terrain substrate |
| `Content/EnvSandbox/Meshes/Ornament/SM_Orn_RoseWindow_8Petal.uasset` | `petal_cantata` / `mirage_gala` | Baroque-petal musical ornament |
| `Content/EnvSandbox/PCG/Musical/MI_Piano_Ebony.uasset` | `cadence_cathedral` | dark key/voxel material accent |
| `Content/EnvSandbox/PCG/Musical/MI_Piano_Ivory.uasset` | `cadence_cathedral` | light key/voxel material accent |
| `Content/EnvSandbox/Materials/Instances/Water/v7/MI_WaterV7_SakuraPond.uasset` | `liquid_cathedral` | reflective water surface |
| `Content/EnvSandbox/Materials/Instances/Sakura/MI_Sakura_Blossom.uasset` | `petal_cantata` | blossom/petal surface polish |

The constellation can be queried without mutation:

```powershell
$env:PYTHONPATH = 'Content/Python'
python Content/Python/resonant_world_asset_constellation.py `
  --seed 3900 --movement petal_cantata --chunk-x 0 --chunk-y 0
```

MCP callers use `melodia_resonant_world_get_constellation` with the same
arguments. The contract is
`specs/resonant_world_asset_constellation.v1.json` and the MCP shape is
`melodia.resonant_world.constellation.v1`.
