# T3D Pattern Library — Materials Supplement (2026-08-14)

The Blueprint patterns live in the parent `T3D_Patterns/README.md` and `t3d.py`.
Material-graph work in this project is **builder-script driven** (Python +
Monolith `run_python`), because material graphs are too large and crash-prone
for T3D text injection. This folder documents the material blocks as
recreatable patterns.

## Patterns

| Pattern | Kind | How to rebuild |
|---|---|---|
| `nikki_feature_block.md` | Material graph block | `expand_nikki_features.py` (idempotent, tagged `NikkiFeat:`) |
| (root) `MESH_MATERIAL_ROUTING.md` | Mesh→material routing | the `route_*`/`fix_*`/`assign_*` scripts in `Content/Python/` |
| (root) `MATERIAL_SYSTEM_REBUILD_2026-08-14.md` | Full reconstruction | ordered script list in `Docs/Reconstruction/` |

## Why not raw .t3d for materials?

Material expressions in UE are graph nodes with native connections, not exec
pins like Blueprints. T3D material injection requires the whole graph to be
text-serializable and re-linked; the project's builders (`setup_master_*`,
`expand_*`) are proven, idempotent, and tag-scoped. Use them.
