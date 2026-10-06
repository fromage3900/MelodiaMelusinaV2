# Horizon System Plan — Session 2026-10-05

## Status: IN PROGRESS

## What Was Done

### Phase 1-3: Houdini Foundry + Distant Terrain + Horizon Eater Graph
- **PCG Graph created**: `/Game/EnvSandbox/PCG/Styles/SeaAbove/PCG_HorizonEater_FilterFlow`
- **Nodes configured**:
  - `CreatePoints_3`: translation (200000, 0, 2520), bounds ±500/±100
  - `FilterDataByAttribute_0`: disabled
  - `TransformPoints_0`: default transform
  - `StaticMeshSpawner_0`: mesh = `/Engine/BasicShapes/Cube.Cube`
- **Edge added**: FilterDataByAttribute_0 → TransformPoints_0 (was missing)
- **Graph saved** via Monolith `run_python`

### Phase 4-7: Scripts Written
- `Content/Python/author_universal_nikki_tiers.py`
- `Content/Python/build_horizon_cloud_cards.py`
- `Content/Python/build_horizon_eater_filter_flow.py`
- `Content/Python/set_horizon_mpc_params.py`
- `Content/Python/setup_golden_hour_ppv.py`
- `Content/Python/stage_horizon_eater_teaser.py`
- `Content/Python/stage_horizon_pcg.py`

### Supporting Files
- `recipes/houdini_foundry/field_atlas_melusina_morning.v1.json`
- `specs/schemas/world_compiler_point_row.v2.json`
- `Tools/world_compiler.py` (modified)
- `CURRENT_STATE.md` (modified)

## What's Blocked

### PCG Generation Produces No Output
- **Symptom**: `comp.generate(True)` and `comp.generate_local(True)` both return but `TAGGED_DATA_LEN:0` persists
- **Root cause**: PCG graphs in UE 5.8 need to be cooked in the PCG editor UI; Python API can set parameters but cannot trigger a synchronous cook
- **Component state**: `IS_ACTIVE:True`, `GENERATED:False`, `TICKING:False`
- **Graph state**: All nodes configured correctly, edges connected, filter disabled

### Next Steps
1. **Open PCG graph in editor**: `/Game/EnvSandbox/PCG/Styles/SeaAbove/PCG_HorizonEater_FilterFlow`
2. **Click Generate** in PCG editor toolbar
3. **Verify points appear** in viewport
4. **If points appear**: Graph is fine; Python API just can't trigger cook
5. **If no points**: Check node configuration in editor

## Files to Commit
- `CURRENT_STATE.md`
- `Docs/Production/PCG/HORIZON_SYSTEM_PLAN_2026-10-04.md`
- `Content/Python/author_universal_nikki_tiers.py`
- `Content/Python/build_horizon_cloud_cards.py`
- `Content/Python/build_horizon_eater_filter_flow.py`
- `Content/Python/set_horizon_mpc_params.py`
- `Content/Python/setup_golden_hour_ppv.py`
- `Content/Python/stage_horizon_eater_teaser.py`
- `Content/Python/stage_horizon_pcg.py`
- `recipes/houdini_foundry/field_atlas_melusina_morning.v1.json`
- `specs/schemas/world_compiler_point_row.v2.json`
- `Tools/world_compiler.py`
- `Content/EnvSandbox/PCG/Styles/SeaAbove/PCG_HorizonEater_FilterFlow.uasset`
- `Content/EnvSandbox/PCG/Styles/SeaAbove/PCG_HorizonCloudCards.uasset`

## Notes
- PCG volume at (200000, 0, 2520) in L_MelusinaMorning
- Graph has 4 nodes, 3 edges (CreatePoints → Filter → Transform → Spawner)
- Filter is disabled; spawner uses Cube mesh for testing
- Component is active but not ticking
