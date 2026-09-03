# Material Maker community conventions (audit)

Reference audit for `MM_Master_SurrealAnimatedPBR_*` graph family. Sources: official MM examples, docs, materialmaker.org library patterns.

## Official references studied

| Asset | Path | Patterns adopted |
|-------|------|------------------|
| stone_wall.ptex | `material_maker/examples/stone_wall.ptex` | Height → `normal_map` → Material port 4; warp + colorize chains; ORM wiring ports 0/1/2/5/6 |
| load_effect.ptex | `material_maker/examples/load_effect.ptex` | `$time` in parameter strings; `remote` + `widgets[].type=named_parameter`; kaleidoscope + transform2 |
| doc_tools.ptex | `material_maker/examples/doc_tools.ptex` | Nested `type: graph` subgraphs; remote inside subgraphs |
| brick_rotated.ptex | `material_maker/examples/brick_rotated.ptex` | Bricks + normal_map + Material |

## Remote node (`type: "remote"`)

- `widgets[]` entries: `named_parameter`, `linked_control`, `config_control`
- Named params: `{ "name": "AnimSpeed", "label": "...", "type": "named_parameter", "min": 0, "max": 2, "step": 0.01, "default": 0.15 }`
- Referenced in expressions as `$AnimSpeed` (see load_effect `$ratio`)
- `parameters` dict holds current values keyed by widget name
- Rail at top of graph (negative Y); all artist floats live here

## Comment node (`type: "comment"`)

- `title`, `text`, `size: {x, y}`, optional `color`
- Lane headers: `title: "08 | Nikki Rim & Glow"`, `text: "[lane:08]"`
- Tint: lavender `(0.45, 0.35, 0.55, 1)` cute lanes; violet `(0.28, 0.12, 0.38, 1)` witch lane 22

## Buffer discipline

- `buffer` before `warp`, multi-sample filters while editing
- `normal_map`: enable buffer while editing; `param2: 0` (buffer off) for export quality ([normal map docs](https://rodzill4.github.io/material-maker/doc/node_filter_normal_map.html))

## Material node constraint

- **One Material node per `.ptex`** — Static (`type: "material"`) and Dynamic (`type: "material_dynamic"`) are separate project files

## Export node (`type: "export"`)

- `suffix`: `$project_emission_$resolution` (supports `$node`, `$project`, `$idx`, `$resolution`)
- `size`: power-of-two exponent (11 = 2048)
- `format`: 0=PNG, 3=EXR

## Animation

- Static export: patch `$BakeTime` on Remote; expressions use `fract($BakeTime * $AnimSpeed + $AnimOffset)`
- Dynamic export: same expressions with `$time` instead of `$BakeTime`
- Batch CLI has no `--animate`; frame loop is external (`batch_mm_surreal_convert.py`)

## Configuration presets (manual in MM UI)

After opening generated graph, optional Remote config widgets for: `NeutralBatch`, `NikkiHero`, `MadokaNeon`, `IttoBold`, `CelestialDeep`, `SakuraDream`. Named scalar defaults are set in builder; presets are tuned interactively per [remote docs](https://rodzill4.github.io/material-maker/doc/remote_nodes.html).

## Subgraph hierarchy

Builder uses **flat graph + comment lanes** (same readability as subgraphs, fewer deserialize edge cases). Lane IDs match [`master_graph_lanes.py`](../../Content/Python/master_graph_lanes.py).
