# World-compiler use cases — 2026-09

Six Melodia-flavoured jobs for `surreal_arch_world_v1`. Architecture: [`REALTIME_CONVERGED_PIPELINE.md`](REALTIME_CONVERGED_PIPELINE.md). Status/evidence: [`CURRENT_STATE.md`](../../CURRENT_STATE.md) only.

None of these is live-proven by this scaffold. Success criteria are what a later UE session must capture.

| ID | Use case | Entry points | Success |
|---|---|---|---|
| A | **Sea Above / `L_MelusinaMorning` set-dress refresh from a Blender plan, no editor restart** | `deploy/surreal_world/export.py` → `{WorldRoot}.world.json`; `deploy/realtime_world_conductor.py --watch`; dirty file `Saved/Audit/realtime_dirty_*.world.json`; `Content/Python/import_world_manifest.py --apply`; maps `/Game/Melodia/Levels/Opening/L_MelusinaMorning` and `/Game/EnvSandbox/Monoliths/SeaAbove/Prototype/LV_SeaAbove_Prototype`. Do not tidy `MelodiaIntegrationMap`. | Conductor reports dirty HISM groups only; `--apply` in a running editor updates those groups; PIE still shows the existing Resonance Ecology graph (`PCG_East_PhyllotaxisCourtyard`) and frozen PPV. Receipt in `Saved/Audit/`. |
| B | **Zen shrine / castle surreal plan → HISM import with `ROLE_UE_HINTS`** | Blender `surreal_architecture_gen.py` + `ZEN_SHRINE` / `WESTERN_CASTLE`; `ROLE_UE_HINTS` in `deploy/surreal_world/export.py` and `Config/material_hints.json`; WIA `import_world_manifest.py`. | One HISM component per `(role, lib)`; sacred/gate materials resolve to Zen MI paths for `ZEN_SHRINE`; instance count matches Blender `surreal_instance_count`. |
| C | **Houdini Copernicus terrain / cymatic maps → Nanite + MPC-driven materials** | `Tools/Houdini/copernicus/copernicus_terrain_height_to_nanite.py`; `copernicus_cymatic_parallax.py`; `Plugins/HoudiniEngine`; `MPC_Melodia_Palette` / `MPC_Cymatics_Driver`; master `M_Master_Toon_Landscape_HeightBlend`. | Seeded maps on disk; mesh under `/Game/EnvSandbox/Meshes/Terrain/`; materials consume existing MPC lanes. **Live UE HDA cook remains unproven** until that receipt exists. |
| D | **PCGEx scatter kits for foliage/props from manifest collections** | Manifest `collections` + optional `scatter_kits`; `Content/Python/setup_pcg_universal.py`; `Plugins/PCGExtendedToolkit`; Sea Above `Content/Python/pcg/apply_resonance_to_sea_above.py`. | Named collection drives one existing graph; instance custom data still packs Resonance; no new scatter framework. |
| E | **Lookdev stage variants (day / night / vapor) as material/PPV packs, no new geometry** | Manifest `stages[]`; frozen `PPV_NikkiDream`; `Content/Python/lookdev_capture.py`; `Content/Python/assign_toon_profiles.py`; `Content/Python/setup_master_universal.py`. | Switching `stages[].id` changes PPV/MPC/MI only; HISM transforms unchanged; `lookdev_capture.py` A/B stills in `Saved/Audit/`. |
| F | **Agent/MCP greybox → hero mesh promotion** | Greybox: `Content/Python/setup_pcg_greybox.py` / Melodia Studio greybox kits; Monolith `mesh_query` / `editor_query`; importer fills `static_mesh_path` on the same instance `id`. | Stable instance `id` survives the swap; greybox mesh path is replaced, transform/role/lib stay; conductor hashes the group dirty and reimports that group only. |

Run the offline conductor against the v2 fixture anytime:

```text
python deploy/realtime_world_conductor.py --once --manifest deploy/fixtures/surreal_arch_world_v2_sector.world.json
python deploy/test_realtime_world_conductor.py
```
