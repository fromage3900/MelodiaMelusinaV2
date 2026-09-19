# surreal_arch_world_v1 — TD Pipeline Contract

**Version:** 2.68.0  
**Producer:** Blender addon `surreal_arch.export_world_ue`  
**Consumer:** [`Content/Python/import_world_manifest.py`](../Content/Python/import_world_manifest.py)

## Purpose

Modular world export for UE5 **Hierarchical Instanced Static Mesh (HISM)** placement. Each manifest entry is one placed instance with role, library source, transform, and material hint.

## File naming

| Artifact | Pattern | Example |
|----------|---------|---------|
| Manifest | `{WorldRoot}.world.json` | `SurrealPlan_Castle_WorldRoot.world.json` |
| Role FBX (optional) | `WorldExport/World_{role}.fbx` | `WorldExport/World_wall.fbx` |

## Top-level schema

```json
{
  "format": "surreal_arch_world_v1",
  "schema_version": 1,
  "coordinate_system": "blender_z_up",
  "style": "WESTERN_CASTLE",
  "plan": "SurrealPlan_Castle",
  "world_root": "SurrealPlan_Castle_WorldRoot",
  "compose_mode": "COLLECTION",
  "instance_count": 20,
  "instances": [ "...InstanceEntry..." ],
  "hism_groups": [ "...HISMGroup..." ],
  "collections": [ "SurrealPlan_Castle_Composed" ]
}
```

## Instance entry

| Field | Type | Required | Notes |
|-------|------|----------|-------|
| `role` | string | yes | `large`, `medium`, `small`, `wall`, `corner_tower`, `gate`, `monument`, `sacred`, `joined_mesh` |
| `lib` | string | yes | Library object name e.g. `_lib_KEEP` |
| `object` | string | yes | Blender instance mesh name |
| `plan_face` | int | no | Source plan face index; `-1` if N/A |
| `transform` | float[4][4] | yes | `matrix_world` row-major (Blender convention) |
| `ue_material_hint` | string | yes | Logical slot name → project MI path via `ROLE_UE_HINTS` |
| `static_mesh_path` | string | no | UE asset path after FBX import (filled by importer) |
| `lod_group` | string | no | UE LOD group name |
| `stream_priority` | int | no | Stream band. Convention: 0 hero, 1 near HISM, 2 scatter, 3 far |
| `gameplay_tags` | string[] | no | Authored tags (`WP_PrimaryRoute`, …) |
| `id` | string | no (required by GMM apply-gate at schema_version ≥ 2) | Stable instance id |
| `sector_id` | string | no | Sector tile id (schema_version 2) |
| `biome_tags` | string[] | no | Biome / music-field tags (schema_version 2) |
| `payload_class` | string | no | `hero` / `hism` / `scatter` / `impostor` (schema_version 2) |

## Optional schema_version 2 root fields

All omitted on v1 files. `additionalProperties` stays false — add keys to `Config/world_schema.json`, do not smuggle.

| Field | Type | Notes |
|-------|------|-------|
| `seed` | int | Deterministic sector/biome seed |
| `sector_id` | string | This file's chunk id |
| `parent_world_root` | string | Parent `world_root` when this file is a tile |
| `biome_tags` | string[] | Authored biome tags |
| `stages` | object[] | Lookdev packs (`id` day/night/vapor + PPV/MPC/material paths). No geometry regen |
| `tiles` | object[] | Child `{sector_id, manifest_path}` sector files |
| `scatter_kits` | object[] | `collections` → PCGEx / `setup_pcg_universal` graph |
| `payload_rules` | object | Unload distances in metres |
| `style_genome` | object | Already emitted by `export.py`; now schema-legal |

Realtime conductor: [`deploy/realtime_world_conductor.py`](realtime_world_conductor.py). Pipeline: [`Docs/WorldGen/REALTIME_CONVERGED_PIPELINE.md`](../Docs/WorldGen/REALTIME_CONVERGED_PIPELINE.md).

## HISM group (derived)

Grouped by `(role, lib)` for instancing. Importer creates one HISM component per group.

| Field | Type | Notes |
|-------|------|-------|
| `role` | string | Compose role |
| `lib` | string | Library piece |
| `ue_material_hint` | string | Material for all instances in group |
| `static_mesh_path` | string | Shared mesh asset |
| `instance_count` | int | Number of transforms |
| `transforms` | float[4][4][] | Instance transforms |

## ROLE_UE_HINTS → project paths

Defined in [`deploy/surreal_world/export.py`](surreal_world/export.py). Maps compose roles to EnvSandbox material instances:

| Role | UE material path |
|------|------------------|
| `large` | `/Game/EnvSandbox/Materials/Instances/Environment/Stylized/MI_Show_StoneCliff` |
| `medium` | `/Game/EnvSandbox/Materials/Instances/Environment/Stylized/MI_Show_Default` |
| `small` | `/Game/EnvSandbox/Materials/Instances/Environment/Stylized/MI_Show_Default` |
| `wall` | `/Game/EnvSandbox/Materials/Instances/Environment/Stylized/MI_Trimsheet_HeavyWear` |
| `corner_tower` | `/Game/EnvSandbox/Materials/Instances/Environment/Stylized/MI_Show_StoneCliff` |
| `gate` | `/Game/EnvSandbox/Materials/Instances/Environment/Stylized/MI_Show_ContactRimHero` |
| `monument` | `/Game/EnvSandbox/Materials/Instances/Environment/Stylized/MI_Show_StoneCliff` |
| `sacred` | `/Game/EnvSandbox/Materials/Instances/Environment/Zen/MI_Zen_Karesansui` |

ZEN_SHRINE style overrides sacred/gate roles to Zen MI paths at export time.

## UE5 HISM import strategy

1. **Import role FBX** (optional batch) into `/Game/EnvSandbox/WorldImport/{WorldRoot}/`
2. **Parse manifest** — validate `format` + `schema_version`
3. **Build HISM groups** — one component per `(role, lib)` with shared static mesh
4. **Apply transforms** — convert Blender Z-up matrix to UE coordinate frame in importer
5. **Assign materials** — lookup `ue_material_hint` → loaded `UMaterialInterface`

Headless entry:

```python
import import_world_manifest
import_world_manifest.import_manifest(r"G:\...\SurrealPlan_Castle_WorldRoot.world.json")
```

## TD sign-off checklist

- [ ] Transform convention documented and tested (single known-good instance)
- [ ] Role → static mesh mapping verified for castle + zen roji
- [ ] HISM group counts match Blender `surreal_instance_count`
- [ ] Material hints resolve to existing MI assets in project
- [ ] Recompose → re-export produces stable instance IDs (± tag edits)

## Version history

| schema_version | Changes |
|----------------|---------|
| 1 | Initial: instances, hism_groups, ROLE_UE_HINTS paths |
| 2 | Optional realtime / NMS-scale fields (`seed`, `sector_id`, `biome_tags`, `stages`, `tiles`, `scatter_kits`, `payload_rules`, instance `id` / `payload_class`). Format stays `surreal_arch_world_v1`. v1 files remain valid. |
