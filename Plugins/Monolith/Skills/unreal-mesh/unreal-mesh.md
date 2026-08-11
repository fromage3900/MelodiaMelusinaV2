---
name: unreal-mesh
description: Use when working with Unreal Engine meshes, scene spatial queries, level blockout, actor manipulation, 3D awareness, horror spatial analysis, accessibility validation, GeometryScript mesh operations, lighting analysis, audio/acoustics, performance budgeting, decal/detail placement, level design (lights, volumes, sublevels, prefabs), tech art (import, LOD, texel density, collision), context-aware prop placement (surface scatter, disturbance, physics sleep), procedural geometry (furniture, structures, mazes, pipes, terrain), procedural town generation (buildings, facades, roofs, streets, city blocks, floor plans, spatial registry, foundations, balconies, fire escapes, room furnishing, debug views, validation), genre presets, encounter design, or hospice accessibility reports via Monolith MCP. Triggers on mesh, StaticMesh, SkeletalMesh, blockout, spatial, raycast, overlap, scene, actor, spawn, LOD, collision, UV, triangle, bounds, scan volume, scatter, navmesh, sightline, hiding, horror, tension, accessibility, wheelchair, lighting, dark, audio, acoustic, surface, footstep, reverb, performance, budget, draw call, decal, blood trail, light, volume, trigger, sublevel, prefab, spline, import, texel, instancing, HISM, material swap, parametric, structure, maze, pipe, terrain, fragment, preset, encounter, patrol, safe room, hospice report, prop kit, disturbance, town, city, block, building, facade, roof, street, floor plan, archetype, lot, foundation, balcony, porch, fire escape, ramp, railing, furnish, furniture, bookmark, section view, validate building.
---

# Unreal Mesh & Spatial Workflows

**242 Mesh actions** (197 core + 45 experimental town gen) via `mesh_query()`. Town gen requires `bEnableProceduralTownGen = true` (disabled by default, known geometry issues).

**Overhaul additions:** `create_blueprint_prefab`, proc mesh cache (`list_cached_meshes`/`clear_cache`/`validate_cache`/`get_cache_stats`), sweep thin walls (`wall_mode: "sweep"`), auto-collision on `save_handle`, floor snap (`snap_to_floor`), collision-aware scatter (`collision_mode`), trim frames (`add_trim: true`), proc mesh caching (`use_cache`/`auto_save`).

## World Outliner Organization (MANDATORY)

**Every spawned actor MUST be in an Outliner folder.** Always pass `folder` param. Defaults:

- Procedural gen: `/Procedural/{Type}` (Structure, Horror, Maze, Building, Pipes, Terrain)
- Town gen: `/Procedural/Town/{BuildingName|BlockName|Streets|Features|Furniture|Foundations|StreetFurniture}`
- Scatter: `/Scatter/{VolumeName}` (walls: `/Walls`, ceiling: `/Ceiling`), surfaces: `/Surface/{Name}`
- Lights: `/Lights` | Spawned: `/Spawned` | Prefabs: `/Prefabs` | Decals: `/Decals`
- Props: `/Props/Kits/{KitName}` | Storytelling: `/Storytelling/{Pattern}` | Path: `/PathProps`

## Discovery

```
monolith_discover({ namespace: "mesh" })
```

## Key Parameter Names

- `asset_path` -- mesh asset path | `actor_name` -- placed level actor
- `volume_name` -- BlockingVolume with Monolith.Blockout tag | `handle` -- GeometryScript mesh handle
- `building_id` / `room_id` / `block_id` -- spatial registry identifiers (town gen)

## Action Reference

### Mesh Inspection (12)

| Action | Key Params | Purpose |
|--------|-----------|---------|
| `get_mesh_info` | `asset_path` | Tri/vert count, bounds, materials, LODs, collision, Nanite, vertex colors |
| `get_mesh_bounds` | `asset_path` | AABB, extent, sphere radius, volume, surface area |
| `get_mesh_materials` | `asset_path` | Per-section material paths + tri counts |
| `get_mesh_lods` | `asset_path` | Per-LOD tri/vert counts + screen sizes |
| `get_mesh_collision` | `asset_path` | Collision type, shape counts |
| `get_mesh_uvs` | `asset_path`, `lod_index`?, `uv_channel`? | UV channels, island count, overlap % |
| `analyze_skeletal_mesh` | `asset_path` | Bone weights, degenerate tris, LOD delta |
| `analyze_mesh_quality` | `asset_path` | Non-manifold, degenerate tris, loose verts, quality score |
| `compare_meshes` | `asset_path_a`, `asset_path_b` | Side-by-side delta with percentages |
| `get_vertex_data` | `asset_path`, `offset`?, `limit`? | Paginated vertex positions + normals (max 5000) |
| `search_meshes_by_size` | `min_bounds`, `max_bounds`, `category`? | Find meshes by dimension range |
| `get_mesh_catalog_stats` | -- | Total indexed meshes, category + size breakdown |

### Scene Manipulation (8)

| Action | Key Params | Purpose |
|--------|-----------|---------|
| `get_actor_info` | `actor_name` | Class, transform, mesh, materials, mobility, tags, components |
| `spawn_actor` | `class_or_mesh`, `location`, `rotation`?, `scale`?, `name`? | Spawn StaticMeshActor (path starts with `/`) or class |
| `move_actor` | `actor_name`, `location`?, `rotation`?, `scale`?, `relative`? | Set or offset transform |
| `duplicate_actor` | `actor_name`, `new_name`?, `offset`? | Clone with optional offset |
| `delete_actors` | `actor_names` | Delete placed actors (NOT asset files) |
| `group_actors` | `actor_names`, `group_name` | Move actors to folder |
| `set_actor_properties` | `actor_name`, `mobility`?, `simulate_physics`?, `tags`? | Mobility, physics, shadows, tags, mass |
| `batch_execute` | `actions` | Multiple actions in single undo transaction (cap 200) |

### Scene Spatial Queries (11)

| Action | Key Params | Purpose |
|--------|-----------|---------|
| `query_raycast` | `start`, `end`, `channel`? | Line trace -- hit actor, location, normal, distance |
| `query_multi_raycast` | `start`, `end`, `max_hits`? | Multi-hit trace sorted by distance |
| `query_radial_sweep` | `origin`, `radius`?, `ray_count`?, `vertical_angles`? | Sonar sweep (cap 512 rays) |
| `query_overlap` | `location`, `shape`, `extent` | Overlap test (box/sphere/capsule) |
| `query_nearest` | `location`, `class_filter`?, `tag_filter`?, `radius`? | Find nearest actors |
| `query_line_of_sight` | `from`, `to` | Visibility check -- bool + blocking actor |
| `get_actors_in_volume` | `volume_name` | All actors in a named volume |
| `get_scene_bounds` | `class_filter`? | World AABB enclosing all actors |
| `get_scene_statistics` | `region_min`?, `region_max`? | Actor counts, total tris, lights, navmesh status |
| `get_spatial_relationships` | `actor_name`, `radius`?, `limit`? | Neighbors with relationships (on_top_of, adjacent, near...) |
| `query_navmesh` | `start`, `end`, `agent_radius`? | Navigation path query |

### Level Blockout (15)

| Action | Key Params | Purpose |
|--------|-----------|---------|
| `get_blockout_volumes` | -- | List all Monolith.Blockout tagged volumes |
| `get_blockout_volume_info` | `volume_name` | Volume details, primitive list |
| `setup_blockout_volume` | `volume_name`, `room_type`, `tags`?, `density`? | Apply Monolith tags |
| `create_blockout_primitive` | `shape`, `location`, `scale`, `label`?, `volume_name`? | Spawn tagged primitive |
| `create_blockout_primitives_batch` | `primitives`, `volume_name`? | Batch placement (cap 200) |
| `create_blockout_grid` | `volume_name`, `cell_size` | Floor grid in volume |
| `match_asset_to_blockout` | `blockout_actor`, `tolerance_pct`?, `top_n`? | Size-matched assets from catalog |
| `match_all_in_volume` | `volume_name`, `tolerance_pct`?, `top_n`? | Batch match all primitives |
| `apply_replacement` | `replacements` | Atomic replace blockouts with real assets |
| `set_actor_tags` | `actor_tags` | Batch apply tags |
| `clear_blockout` | `volume_name`, `keep_tagged`? | Remove blockout primitives |
| `export_blockout_layout` / `import_blockout_layout` | `volume_name`, `layout_json`? | JSON import/export |
| `scan_volume` | `volume_name`, `ray_density`? | Daredevil scan -- walls, floor, ceiling, openings |
| `scatter_props` | `volume_name`, `asset_paths`, `count`, `min_spacing`?, `seed`? | Poisson disk scatter |

### Mesh Operations (12) -- `#if WITH_GEOMETRYSCRIPT`, handle-based

| Action | Key Params | Purpose |
|--------|-----------|---------|
| `create_handle` | `source`, `handle` | Load mesh into editable handle |
| `release_handle` / `list_handles` | `handle` | Free / list all handles |
| `save_handle` | `handle`, `target_path`, `overwrite`? | Commit to StaticMesh asset |
| `mesh_boolean` | `handle_a`, `handle_b`, `operation`, `result_handle` | Union/subtract/intersect |
| `mesh_simplify` | `handle`, `target_triangles`? | Reduce tri count |
| `mesh_remesh` | `handle`, `target_edge_length` | Isotropic remeshing |
| `generate_collision` / `generate_lods` | `handle`, method/count | Convex decomp / LOD chain |
| `fill_holes` / `mirror_mesh` | `handle`, `axis`? | Auto hole fill / mirror X/Y/Z |
| `compute_uvs` | `handle`, `method` | Auto-unwrap/box/planar/cylinder |

### Horror Spatial Analysis (8)

| Action | Key Params | Purpose |
|--------|-----------|---------|
| `analyze_sightlines` | `location`, `fov`?, `ray_count`? | Claustrophobia score, blocked % at 5/10/20m |
| `find_hiding_spots` | `region_min/max`, `viewpoints` | Grid-sample concealment |
| `find_ambush_points` | `path_points`, `lateral_range`? | Concealed positions with surprise angles |
| `analyze_choke_points` | `start`, `end` | Navmesh path width, flank possibility |
| `analyze_escape_routes` | `location`, `exit_tags`? | Paths to exits scored by threat exposure |
| `classify_zone_tension` | `location`, `radius`? | Calm/uneasy/tense/dread/panic composite |
| `analyze_pacing_curve` | `path_points` | Tension along path, scare point detection |
| `find_dead_ends` | `region_min/max`? | Navmesh flood-fill for single-exit regions |

### Accessibility Analysis (6) -- Serves the hospice mission

| Action | Key Params | Purpose |
|--------|-----------|---------|
| `validate_path_width` | `start`, `end`, `min_width`? | Wheelchair clearance (120cm default) |
| `validate_navigation_complexity` | `start`, `end` | Cognitive difficulty scoring |
| `analyze_visual_contrast` | `location`, `forward`? | WCAG-inspired contrast for interactables |
| `find_rest_points` | `start`, `end`, `max_gap`? | Safe room spacing along path |
| `validate_interactive_reach` | `region`, `tags`? | Height/distance/obstruction checks |
| `generate_accessibility_report` | `start`, `end`, `profile`? | Motor/vision/cognitive profile, A-F grade |

### Lighting Analysis (5)

| Action | Key Params | Purpose |
|--------|-----------|---------|
| `sample_light_levels` | `points`, `mode`? | Per-point luminance |
| `find_dark_corners` | `volume_name` or `region`, `threshold`? | Ortho capture + flood-fill dark zones |
| `analyze_light_transitions` | `path_points`, `sample_interval`? | Flag harsh bright->dark (>4:1 ratio) |
| `get_light_coverage` | `volume_name` | % lit/shadow/dark, light inventory |
| `suggest_light_placement` | `volume_name`, `mood`? | Inverse-square placement (horror_dim/safe_room/clinical) |

### Audio & Acoustics (14)

| Action | Key Params | Purpose |
|--------|-----------|---------|
| `get_audio_volumes` | -- | Enumerate AudioVolumes with reverb |
| `get_surface_materials` | `volume_name` or `region` | Physical material breakdown |
| `estimate_footstep_sound` | `location` | Surface type -> loudness factor (0-1) |
| `analyze_room_acoustics` | `volume_name` | Sabine RT60 reverb estimation |
| `analyze_sound_propagation` | `from`, `to` | Material-based occlusion, wall count, dB reduction |
| `find_loud_surfaces` | `volume_name` or `region` | Dangerous surfaces (metal, glass, gravel) |
| `find_sound_paths` | `from`, `to`, `max_bounces`? | Image-source reflection paths |
| `can_ai_hear_from` | `ai_location`, `player_location` | Monster hearing detection |
| `get_stealth_map` | `volume_name`, `grid_size`? | Per-cell loudness + detection radius heatmap |
| `find_quiet_path` | `start`, `end` | Navmesh path preferring quiet surfaces |
| `suggest_audio_volumes` | `volume_name` | Auto-suggest reverb from room materials |
| `create_audio_volume` | `volume_name`, `reverb_preset` | Spawn AudioVolume |
| `set_surface_type` | `actor_name`, `surface_type` | Set physical material override |
| `create_surface_datatable` | `template`? | Bootstrap acoustic system (12 horror surfaces) |

### Performance Analysis (5)

| Action | Key Params | Purpose |
|--------|-----------|---------|
| `get_region_performance` | `region_min`, `region_max` | Tri count, draw calls, lights, shadow casters |
| `estimate_placement_cost` | `assets` (array) | Pre-spawn budgeting |
| `find_overdraw_hotspots` | `viewpoint`, `fov`? | Translucent screen-space overlap |
| `analyze_shadow_cost` | `region_min`, `region_max` | Flag small props casting shadows pointlessly |
| `get_triangle_budget` | `viewpoint`, `fov`?, `budget`? | Frustum-culled LOD-aware count vs budget |

### Decal & Detail (4)

| Action | Key Params | Purpose |
|--------|-----------|---------|
| `place_decals` | `material`, `locations` or `region`+`count` | Surface-aligned decals, Poisson scatter |
| `place_along_path` | `path_points`, `pattern`? | Blood trails, footprints, drag marks |
| `analyze_prop_density` | `volume_name`, `target_density`? | Grid-cell density vs target |
| `place_storytelling_scene` | `location`, `pattern`, `intensity`? | 5 horror presets (violence/abandoned/dragged/medical/corruption) |

### Level Design (9)

| Action | Key Params | Purpose |
|--------|-----------|---------|
| `place_light` | `type`, `location`, `intensity`?, `color`? | Spawn point/spot/rect/directional |
| `set_light_properties` | `actor_name`, properties... | Modify existing light |
| `set_actor_material` | `actor_name`, `material`, `slot`? | Assign material |
| `swap_material_in_level` | `source_material`, `target_material` | Bulk replace material |
| `find_replace_mesh` | `source_mesh`, `target_mesh` | Swap all instances |
| `set_lod_screen_sizes` | `asset_path`, `screen_sizes` | LOD transition thresholds |
| `find_instancing_candidates` | `min_count`? | Find repeated meshes for HISM |
| `convert_to_hism` | `mesh`, `actors` | Convert to HISM |
| `get_actor_component_properties` | `actor_name`, `component_class`? | Read UPROPERTYs |

### Volumes & Properties (7)

| Action | Key Params | Purpose |
|--------|-----------|---------|
| `spawn_volume` | `type`, `location`, `extent` | Trigger/kill/pain/blocking/audio/post_process |
| `get_actor_properties` | `actor_name`, `properties`? | Read via reflection |
| `copy_actor_properties` | `source_actor`, `target_actors` | Copy settings |
| `build_navmesh` | -- | Trigger navmesh rebuild |
| `select_actors` | `actor_names`, `mode`? | Editor selection + camera focus |
| `snap_to_surface` | `actor_names`, `direction`? | Trace + normal alignment |
| `set_collision_preset` | `actor_name`, `preset` | Set collision profile |

### Horror Intelligence (4)

| Action | Key Params | Purpose |
|--------|-----------|---------|
| `predict_player_paths` | `start`, `end`, `strategies`? | 4 strategies: shortest/safest/curious/cautious |
| `evaluate_spawn_point` | `location`, `player_paths`? | Spawn quality score (S-F grade) |
| `suggest_scare_positions` | `path_points` | Optimal scripted event positions |
| `evaluate_encounter_pacing` | `encounters`, `path_points` | Spacing/intensity/rest analysis |

### Tech Art Pipeline (7)

| Action | Key Params | Purpose |
|--------|-----------|---------|
| `import_mesh` | `file_path`, `save_path` | FBX/glTF import |
| `fix_mesh_quality` | `asset_path`, `ops`? | GeometryScript repair |
| `auto_generate_lods` | `asset_path`, `lod_count`? | One-shot LOD chain |
| `analyze_texel_density` | `asset_path` or `region` | UV area x texture res = texels/cm |
| `analyze_material_cost_in_region` | `region` or `actors` | Shader complexity per mesh |
| `set_mesh_collision` | `asset_path`, `type`?, `auto_convex`? | Write collision |
| `analyze_lightmap_density` | `region` or `actors` | Lightmap resolution + UV density |

### Advanced Level Design (8)

| Action | Key Params | Purpose |
|--------|-----------|---------|
| `manage_sublevel` | `action`, `sublevel`? | Create/add/remove/move_actors_to |
| `place_blueprint_actor` | `blueprint`, `location`, `properties`? | Spawn BP with property values |
| `place_spline` | `points`, `mesh`? | Spline actor with mesh segments |
| `create_prefab` / `spawn_prefab` | `actors` / `prefab`, `location` | Level Instance creation + placement |
| `randomize_transforms` | `actor_names`, ranges... | Batch random offset/rotation/scale |
| `get_level_actors` | filters... | Filtered actor enumeration |
| `measure_distance` | `from`, `to`, `mode`? | Euclidean/horizontal/navmesh |

### Context-Aware Props (8)

| Action | Key Params | Purpose |
|--------|-----------|---------|
| `scatter_on_surface` | `surface_actor`, `assets`, `count` | Props ON shelves/tables |
| `set_room_disturbance` | `volume_name`, `level` | Orderly/slightly_messy/ransacked/abandoned |
| `configure_physics_props` | `actor_names`, `sleep`? | SimulatePhysics + sleep state |
| `settle_props` | `actor_names`, `seed`? | Trace-snap with random tilt |
| `create_prop_kit` / `place_prop_kit` | kit JSON | Themed prop group authoring + placement |
| `scatter_on_walls` | `volume_name`, `assets`, `count` | Horizontal trace wall placement |
| `scatter_on_ceiling` | `volume_name`, `assets`, `count` | Upward trace ceiling placement |

### Procedural Geometry (8) -- GeometryScript, handle pool

| Action | Key Params | Purpose |
|--------|-----------|---------|
| `create_parametric_mesh` | `type`, `params` | 15 furniture types (chair->bathtub) |
| `create_horror_prop` | `type`, `params`, `seed`? | 7 horror types (barricade->vent_grate) |
| `create_structure` | `type`, `params` | Room/corridor/L/T-junction with openings |
| `create_building_shell` | `floors`, `footprint` | Multi-story from 2D polygon |
| `create_maze` | `algorithm`, `grid_size`, `seed`? | 3 algorithms + layout JSON |
| `create_pipe_network` | `path_points`, `radius`? | Swept polygon with ball joints |
| `create_fragments` | `source_handle`, `count`?, `seed`? | Plane-slice mesh fragmentation |
| `create_terrain_patch` | `size`, `noise`? | Perlin noise heightmap mesh |

### Procedural Town Generation (46) -- EXPERIMENTAL

Layered pipeline: floor plans -> grid geometry -> facades -> roofs -> streets -> spatial registry -> volumes -> furnishing.

**SP1 Grid Building (2):** `create_building_from_grid` (grid->geometry, `omit_exterior_walls` for facade), `create_grid_from_rooms` (room rects->grid)

**SP2 Floor Plans (3):** `generate_floor_plan` (archetype+footprint->grid/rooms/doors), `list_building_archetypes`, `get_building_archetype`

**SP3 Facades (3):** `generate_facade` (exterior faces->windows/doors/trim), `list_facade_styles`, `apply_horror_damage`

**SP4 Roofs (1):** `generate_roof` (gable/hip/flat/shed/gambrel)

**SP5 City Blocks (4):** `create_city_block` (full pipeline), `create_lot_layout`, `create_street`, `place_street_furniture`

**SP6 Spatial Registry (10):** `register_building`, `register_room`, `register_street_furniture`, `query_room_at`, `query_adjacent_rooms`, `query_rooms_by_filter`, `query_building_exits`, `path_between_rooms`, `save_block_descriptor`, `load_block_descriptor`

**SP7 Auto-Volumes (3):** `auto_volumes_for_building`, `auto_volumes_for_block`, `spawn_nav_link`

**SP8a Terrain+Foundations (5):** `sample_terrain_grid`, `analyze_building_site`, `create_foundation` (slab/piers/stepped/stilts/basement), `create_retaining_wall`, `place_building_on_terrain`

**SP8b Architectural Features (5):** `create_balcony`, `create_porch`, `create_fire_escape`, `create_ramp_connector` (ADA-compliant), `create_railing` -- all accept `building_context` for auto-orientation, emit `wall_openings`

**SP9 Debug Views (6):** `toggle_section_view`, `toggle_ceiling_visibility`, `capture_floor_plan`, `highlight_room`, `save_camera_bookmark`, `load_camera_bookmark`

**SP10 Furnishing (3):** `furnish_room`, `furnish_building`, `list_furniture_presets`

**Validation (1):** `validate_building` -- capsule sweep, BFS connectivity, stair angles, window raycasts

### Genre Presets (8)

| Action | Key Params | Purpose |
|--------|-----------|---------|
| `list/create_storytelling_patterns` | `name`, `elements` | Horror/fantasy/sci-fi storytelling |
| `list/create_acoustic_profiles` | `name`, `surfaces` | Genre-specific acoustics |
| `create_tension_profile` | `name`, `weights` | Tension factor weights |
| `list_genre_presets` | -- | Browse preset packs |
| `export/import_genre_preset` | `path`, `merge_mode`? | Bundle/load preset packs |

### Encounter Design (8)

| Action | Key Params | Purpose |
|--------|-----------|---------|
| `design_encounter` | `region`, `archetype`? | Capstone: spawn+patrol+exits+sightlines |
| `suggest_patrol_route` | `path_points`, `archetype` | Stalker/patrol/ambusher routes |
| `analyze_ai_territory` | `region` | Hiding/patrol/ambush heatmap |
| `evaluate_safe_room` | `volume_name` | Defensibility + hospice amenity scoring |
| `analyze_level_pacing_structure` | `path_points` | Macro tension->release mapping |
| `generate_scare_sequence` | `path_points`, `style`? | slow_burn/escalating/relentless/single_peak |
| `validate_horror_intensity` | `path_points` | Hospice intensity cap audit |
| `generate_hospice_report` | `start`, `end`, `profile`? | 5-section accessibility audit, A-F grade |

### Quality & Polish (9)

| Action | Key Params | Purpose |
|--------|-----------|---------|
| `validate_naming_conventions` | `path`? | Flag assets missing SM_/M_/T_ prefixes |
| `batch_rename_assets` | `pattern`, `replacement` | Find/replace with reference fixup |
| `generate_proxy_mesh` | `actors` | Merge meshes into simplified proxy |
| `setup_hlod` | `layer_type`, `cell_size`? | Configure HLOD layers |
| `analyze_texture_budget` | -- | Streaming pool usage + top textures |
| `analyze_framing` | `viewpoint` | Rule-of-thirds composition scoring |
| `evaluate_monster_reveal` | `monster_location`, `player_location` | Silhouette/distance/backlight scoring |
| `analyze_co_op_balance` | `player_positions` | Coverage blind spots (P3 placeholder) |
| `integration_hooks_stub` | `hook_type` | AI Director/GAS/telemetry stubs |

## Blockout Tag Convention

```
Monolith.Blockout                -- sentinel (required)
Monolith.Room:Kitchen            -- room type
Monolith.Tag:Furniture.Kitchen   -- asset matching tag
Monolith.Density:Normal          -- Sparse/Normal/Dense/Cluttered
Monolith.AllowPhysics            -- presence = true
Monolith.Owner:BV_Kitchen        -- on primitives, links to volume
Monolith.BlockoutPrimitive       -- marks as blockout primitive
Monolith.Label:Counter_North     -- human-readable label
```

## Typical Workflows

- **Blockout room:** `get_blockout_volumes -> scan_volume -> create_blockout_primitives_batch -> match_all_in_volume -> apply_replacement`
- **Inspect mesh:** `get_mesh_info -> analyze_mesh_quality -> compare_meshes`
- **Edit mesh (GS):** `create_handle -> [ops] -> save_handle -> release_handle`
- **Horror level:** `analyze_sightlines -> find_hiding_spots -> analyze_escape_routes -> classify_zone_tension -> analyze_pacing_curve`
- **Accessibility:** `generate_accessibility_report` (or individual `validate_` actions)
- **Audio design:** `create_surface_datatable -> get_surface_materials -> analyze_room_acoustics -> get_stealth_map -> can_ai_hear_from -> suggest_audio_volumes`
- **Lighting audit:** `get_light_coverage -> find_dark_corners -> analyze_light_transitions -> suggest_light_placement`
- **Performance:** `get_region_performance -> get_triangle_budget -> analyze_shadow_cost -> find_overdraw_hotspots`
- **Storytelling:** `place_storytelling_scene -> place_along_path -> scatter_props -> analyze_prop_density`
- **Scene overview:** `get_scene_statistics -> query_radial_sweep -> get_spatial_relationships`
- **Single building (town):** `list_building_archetypes -> generate_floor_plan -> create_building_from_grid -> generate_facade -> generate_roof -> register_building -> auto_volumes_for_building -> furnish_building -> validate_building`
- **City block (town):** `create_city_block` (all-in-one) OR step-by-step per lot + `create_street -> place_street_furniture -> auto_volumes_for_block -> save_block_descriptor`
- **Building on terrain:** `sample_terrain_grid -> analyze_building_site -> create_foundation -> place_building_on_terrain`
- **Debug building:** `toggle_section_view -> toggle_ceiling_visibility -> capture_floor_plan -> highlight_room`
- **Architectural details:** `create_balcony / create_porch / create_fire_escape / create_ramp_connector -> apply_horror_damage`

## AI Preview & Tech-Art Overlays (editor:: actions)

- `editor_query("capture_scene_preview", { asset_path, asset_type: "static_mesh" })` or `asset_type: "skeletal_mesh"` -- preview render of a mesh asset (skeletal-mesh variant accepts optional `animation_path` + `seek_time` for a posed frame).
- `editor_query("capture_with_overlay", { asset_path, mode })` -- single static-mesh capture under one of 5 engine debug-view modes: `wireframe`, `normals`, `uv_density`, `lightmap_density`, `shader_complexity`. Use for tech-art audits (texel density, UV stretch, complexity hotspots).

See `monolith_guide(section="recipes")` entry "Visual introspection -- going beyond thumbnails".

## Gotchas

- `spawn_actor` does NOT spawn `ABlockingVolume` -- use the editor
- `delete_actors` deletes placed actors, NOT asset files
- `batch_execute` rejects nesting, caps at 200
- `set_actor_properties`: Mobility must be "Movable" BEFORE enabling SimulatePhysics
- `query_radial_sweep`: `ray_count * vertical_angles <= 512`
- `search_meshes_by_size` requires `monolith_reindex()` first
- All spatial queries work in editor WITHOUT play session
- `query_` = active physics queries, `get_` = reads stored data
- `create_city_block` calls full pipeline internally -- use step-by-step for fine control
- `register_building`/`register_room` required before spatial registry queries return results
- `save/load_block_descriptor` persist to JSON, not uasset
- `create_ramp_connector` follows ADA slope by default -- override with `max_slope`
- `furnish_room` requires room to be registered first
- Stairwells need minimum 4x6 cells (24 grid cells) for switchback stairs at 270cm floor height
- Use `omit_exterior_walls: true` with `generate_facade` to avoid double walls
- Pass `building_context` to architectural features for auto-orientation
- Run `validate_building` after generation to verify playability
