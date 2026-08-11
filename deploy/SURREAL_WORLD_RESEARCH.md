# Surreal World — Research Notes (v0.1)

**Version:** 2.68.0  
**Package:** `deploy/surreal_world/`  
**Verify:** `deploy/_mcp_verify_world.py`

## Layer 2 compose pipeline

Topology-driven placement: plan mesh faces → buildings (area + vertex tags), boundary edges → walls, tagged verts → gates/towers.

| Tag | Compose role |
|-----|----------------|
| `is_keep` | large |
| `is_plaza` | monument |
| `is_sacred` | sacred |
| `is_gate` | gate |
| `is_corner_tower` | corner_tower |

## Compose modes

| Mode | Output | UE fit |
|------|--------|--------|
| `COLLECTION` (default) | `{Plan}_WorldRoot` + linked mesh instances | Modular manifest + HISM |
| `JOINED` (legacy) | Single `{Plan}_World` mesh | Blockout only |

## Instancing pattern (Blender → UE)

- Library pieces baked once in `SurrealArch_Library` (`_lib_*`)
- Compose uses **shared mesh data** + parent empty (wall stretch on empty `scale.x`)
- Per-instance metadata: `surreal_world_role`, `surreal_lib_piece`, `surreal_plan_face`
- Export: `{WorldRoot}.world.json` format `surreal_arch_world_v1`

### UE5 HISM reference

- Manifest lists transforms per role → import as Static Mesh Instances or Hierarchical Instanced Static Mesh
- Role → material hint map in `surreal_world/export.py` (`ROLE_UE_HINTS`)

## Compose styles

| Style | Keep | Gate | Sacred |
|-------|------|------|--------|
| WESTERN_CASTLE | KEEP | GATEHOUSE | CHAPEL |
| ZEN_SHRINE | TEAHOUSE | TORII | STONE_GARDEN |

## Plan typologies

- **Castle** — ward faces + corner towers + south gate
- **Zen Roji** — path strip + sacred courtyard (torii at entry)

## Research backlog (Phase 4+)

- GN terrain replacing bmesh sine noise (`terrain_gn.py`)
- Slope/aspect vegetation scatter rules
- WFC grid city plans for organic street networks
- Wave Function Collapse references: grid constraint propagation for plot assignment

## UE import — `resolved_compose_roles`

The `.world.json` `style_genome.resolved_compose_roles` block maps compose face roles to `_lib_*` pieces used at export time (OS style + genome overrides merged).

| Manifest role | UE usage |
|---------------|----------|
| `gate`, `sacred`, `large`, … | HISM group key / static mesh batch per role |
| `resolved_compose_roles[role]` | Library mesh path (`_lib_GB_ZEN_HONDEN` → import that kit FBX) |
| `instances[].role` | Per-instance placement; cross-check against resolved map |
| `hism_groups` | Pre-batched transforms per role for `UHierarchicalInstancedStaticMeshComponent` |

Import flow: read `resolved_compose_roles` → load each unique `_lib_*` mesh once → spawn HISM per role using `hism_groups` transforms and `ue_material_hint` from instances.

## References

- Blender Collection Instances + parent empty scaling for non-uniform wall modules
- Cistercian / Japanese roji path typology — sequential spaces before sacred courtyard
- UE World Partition: instance manifests as external spawn data
