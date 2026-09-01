# Surreal Architecture — Geometry Nodes Taxonomy

**Date:** 2026-08-29  
**Scope:** `deploy/surreal_arch/melodia_gn/`  
**Status:** 232 builders (291 registrations, 1 duplicate `MEL_music_sheet_rail`), 268 curated presets across 89 builders, 15 categories — audited 2026-09-01

---

## Stats

| Metric | Count |
|--------|-------|
| Builder files | 51 |
| Registered builders | 232 (unique; 291 `register_builder` calls, 1 duplicate) |
| Builders with presets | 89 |
| Total curated presets | 268 |
| Categories | 15 |

---

## Category Map

| # | Category | Label | Builders | Presets |
|---|----------|-------|----------|---------|
| 1 | `primitives` | Primitives | 14 | 3 |
| 2 | `profiles` | Profiles | 8 | 3 |
| 3 | `math_attrs` | Math & Attributes | 8 | 0 |
| 4 | `structures` | Structures | 13 | 42 |
| 5 | `effects` | Magic Effects | 16 | 14 |
| 6 | `ornament` | Ornament | 9 | 9 |
| 7 | `filigree` | Filigree & Crests | 4 | 12 |
| 8 | `music` | Musical Notation | 61 | 183 |
| 9 | `castle` | Castle Kit | 22 | 6 |
| 10 | `operations` | Operations | 3 | 9 |
| 11 | `mesh_tools` | Mesh Tools | 14 | 9 |
| 12 | `set_dressing` | Set Dressing | 15 | 3 |
| 13 | `mother` | Faraway Mother | 16 | 0 |
| 14 | `white_current` | White Current | 6 | 0 |
| 15 | `god_molts` | God That Molts | 8 | 0 |

---

## Architecture

### Registry

```
GROUP_BUILDERS[tree_name] → callable
GROUP_METADATA[tree_name] → {label, description, category, builder, hidden, role}
```

### Presets

```
BUILDERS_PRESETS[builder_id] → {
    label: str,
    presets: {preset_name: {param: value}},
    preset_labels: {preset_name: human_name},
    preset_descriptions: {preset_name: one_liner},
}
```

### Categories

Defined in `core.py` as `CATEGORY_META`. Sorted by category order in the GN Stack UI.

---

## Builder Inventory by Category

### 1. Primitives (14 builders)

| Builder | Label | Description | Presets |
|---------|-------|-------------|---------|
| `MEL_circular_array` | Circular Array | Radial instance array with scale + Z offset | 0 |
| `MEL_linear_array` | Linear Array | Linear array with direction, spacing, taper | 0 |
| `MEL_grid_array` | Grid Array | 2D grid array with count + spacing on both axes | 0 |
| `MEL_bounding_box` | Bounding Box | Extract bounding box size and center | 0 |
| `MEL_instance_on_spline` | Instance on Spline | Instance geometry along a curve with spacing control | 0 |
| `MEL_spiral_array` | Spiral Array | Helical sweep along a spiral curve | 0 |
| `MEL_radial_array` | Radial Array | Arc-distributed radial array with angular offset tracking | 0 |
| `MEL_weighted_array` | Weighted Array | Poisson-disk random surface distribution | 0 |
| `MEL_curve_array` | Curve Array | Curve-aligned array with taper, tangent alignment | 0 |
| `MEL_gear` | Gear | Star gear — radial tooth blocks unioned into a disc | 0 |
| `MEL_stepped_pyramid` | Stepped Pyramid | Stacked shrinking cubes forming a stepped pyramid | 3 |
| `MEL_torus_cross` | Torus Cross | Two-torus gyroscope cross with toggle for rotated ring | 0 |
| `MEL_polyhedra_icosahedron` | Icosahedron Solid | 20-faced Platonic Icosahedron with wireframe mode | 0 |
| `MEL_polyhedra_dodecahedron` | Dodecahedron Solid | 12-faced Platonic Dodecahedron (icosa dual) | 0 |

---

### 2. Profiles (8 builders)

| Builder | Label | Description | Presets |
|---------|-------|-------------|---------|
| `MEL_column` | Column | Parametric column with optional fluting and capital/base caps | 3 |
| `MEL_baluster` | Baluster | Classic baluster profile revolved from curve cross-section | 0 |
| `MEL_post` | Post | Square post with chamfer edges and optional cap | 0 |
| `MEL_rail` | Rail | Rail sweep — rectangle profile extruded along a curve | 0 |
| `MEL_star_finial` | Star Finial | Decorative star-shaped crown finial for tower/column tops | 0 |
| `MEL_lissajous` | Lissajous Curve | Lissajous curve for decorative arches | 0 |
| `MEL_baluster_collar` | Baluster with Collar | Baluster shaft with stepped collar rings unioned in | 0 |
| `MEL_egg_dart_rail` | Egg and Dart Rail | Classical egg-and-dart ornament rail swept along a curve | 0 |

---

### 3. Math & Attributes (8 builders)

| Builder | Label | Description | Presets |
|---------|-------|-------------|---------|
| `MEL_add_geometry` | Add (Union) | Boolean union — merge two geometry inputs | 0 |
| `MEL_subtract_geometry` | Subtract (Difference) | Boolean difference — subtract B from A | 0 |
| `MEL_power_scale` | Power Scale | Exponential power falloff scale along an axis for tapering | 0 |
| `MEL_exponent_blend` | Exponent Blend | Blend between two position sets using exponent curve | 0 |
| `MEL_store_named_attr` | Store Named Attribute | Store a named float/vector attribute on geometry | 0 |
| `MEL_attribute_math` | Attribute Math | Read named attribute, apply math op, store result back | 0 |
| `MEL_attr_ramp_mix` | Attribute Ramp Mix | Three-stop Start/Middle/End ramp blend | 0 |
| `MEL_attr_vector_rotate` | Attribute Vector Rotate | Rotate a named vector attribute around Z and store result | 0 |

---

### 4. Structures (13 builders)

| Builder | Label | Description | Presets |
|---------|-------|-------------|---------|
| `MEL_gazebo` | Gazebo | Full gazebo — columns, beam ring, conical roof, star finial | 3 |
| `MEL_arch` | Arch | Simple arch structure — column pair with arc span | 0 |
| `MEL_portico` | Portico | Portico assembly — column grid with triangular pediment gable | 0 |
| `MEL_greybox_room_kit` | Greybox Room Kit | Hollow greybox room with wall thickness and optional ceiling | 3 |
| `MEL_greybox_corridor` | Greybox Corridor | Tileable hollow hall with length, width, height, thickness | 3 |
| `MEL_greybox_junction` | Greybox Junction | T or X corridor join via boolean union of hollow halls | 3 |
| `MEL_greybox_openings` | Greybox Openings | Door and window boxes boolean-cut from incoming geometry | 3 |
| `MEL_greybox_composer` | Greybox Composer | Join selected room, corridor, and junction groups | 0 |
| `MEL_nikki_bloom_pavilion` | Nikki Bloom Pavilion | Infinity Nikki floral canopy with heart token filigree | 3 |
| `MEL_nikki_wardrobe_nook` | Nikki Wardrobe Nook | Garment nook with rods, mirror & token pedestal | 3 |
| `MEL_nikki_podium_runway` | Nikki Podium Runway | Runway podium with lights & sakura petal fall | 3 |
| `MEL_music_room_shell` | Music Room Shell | Greybox hollow room with openings and optional dado staff band | 3 |
| `MEL_pergola_walkway` | Pergola Walkway | Garden pergola — twin post lines, top beams and cross rafters | 0 |

---

### 5. Magic Effects (16 builders)

| Builder | Label | Description | Presets |
|---------|-------|-------------|---------|
| `MEL_effect_displace` | Displace Effect | Noise-based vertex displacement via Set Position + Noise Texture | 0 |
| `MEL_effect_wave` | Wave Effect | Sine wave displacement along an axis, with normal-space toggle | 3 |
| `MEL_effect_cast` | Cast Effect | Pull mesh toward sphere or cylinder | 0 |
| `MEL_effect_wireframe` | Wireframe Effect | Wireframe overlay — edges to curves swept with circle profile | 0 |
| `MEL_effect_smooth` | Smooth Effect | Geometry smoothing via Blur Attribute node | 0 |
| `MEL_effect_magic` | Magic Distortion | Combined magical distortion — 8 params, 10 presets | 3 |
| `MEL_water_gerstner` | Gerstner Waves | Multi-layer Gerstner wave displacement — wind direction, speed, amplitude | 5 |
| `MEL_water_ripples` | Water Ripples | Expanding ripple rings from an impact point with per-ring decay | 0 |
| `MEL_water_foam` | Water Foam | Foam patch instances with lifetime — velocity-threshold wake | 0 |
| `MEL_water_current_markers` | Current Markers | Flow-direction arrow instances with current_dir attribute | 0 |
| `MEL_env_waterfall_pool` | Waterfall Pool | Pool, cascade sheet and splash ring with water attribute contract | 0 |
| `MEL_ribbon_curve` | Ribbon Curve | Sine centerline ribbon strip — width, amplitude, frequency, twist | 3 |
| `MEL_lissajous_ribbon` | Lissajous Ribbon | Lissajous figure ribbon — sin/cos cross path with frequency ratio | 0 |
| `MEL_closed_ribbon` | Closed Ribbon | Seamless circular ribbon loop for UI borders and decorative rings | 0 |
| `MEL_vortex_twist` | Vortex Twist | Twist displacement around the Z axis with stored per-vertex twist angle | 0 |
| `MEL_radial_wave` | Radial Wave | Concentric radial ripple displacement along face normals | 0 |

---

### 6. Ornament (9 builders)

| Builder | Label | Description | Presets |
|---------|-------|-------------|---------|
| `MEL_ornament_vine` | Ornament Vine (Art Nouveau) | Art Nouveau vine — sinusoidal S-curve sweep with power-tapered thickness | 3 |
| `MEL_ornament_radial` | Ornament Radial (Gothic) | Gothic radial — circular spoke array with concentric rings | 3 |
| `MEL_ornament_grid` | Ornament Grid (Arabesque) | Arabesque geometric grid — cells with edge power falloff | 0 |
| `MEL_ornament_frame` | Ornament Frame | Rectangular picture frame — bounding-box edges with corner taper | 3 |
| `MEL_ornament_panel` | Ornament Panel (Composite) | Composite panel — interior ornament + frame, material zone attribute | 0 |
| `MEL_decorative_rosette` | Decorative Rosette | Multi-petaled radial ornamental rosette motif with central dome | 0 |
| `MEL_ornament_rosette_sixpetal` | Ornament Rosette Sixpetal | Six-petal (or N-petal) rosette — radial petal ellipses around a domed center | 0 |
| `MEL_ornament_scallop_band` | Ornament Scallop Band | Scallop band — repeated semicircular arcs instanced along a baseline | 0 |
| `MEL_ornament_keyhole_frame` | Ornament Keyhole Frame | Keyhole frame — rounded rectangle outline with a circular ring on top | 0 |

---

### 7. Filigree & Crests (4 builders)

| Builder | Label | Description | Presets |
|---------|-------|-------------|---------|
| `MEL_filigree_spiral` | Filigree Spiral | Art Nouveau parametric logarithmic filigree scroll curve | 3 |
| `MEL_filigree_corner_volute` | Filigree Corner Volute | Corner volute — Archimedean spiral arm with a taper and finial dot | 3 |
| `MEL_filigree_finial_cross` | Filigree Finial Cross | Finial cross — bar-and-ball cross with four domed tips | 3 |
| `MEL_filigree_wreath_ring` | Filigree Wreath Ring | Wreath ring — torus band ringed with tilted laurel leaves | 3 |

---

### 8. Musical Notation (61 builders)

The largest category. All builders produce musical geometry — instruments, notation, staffs, and walkable music-themed architecture.

#### Notation Core (14 builders)

| Builder | Label | Presets |
|---------|-------|---------|
| `MEL_music_note_head` | Music Note Head | 3 |
| `MEL_music_treble_clef` | Music Treble Clef | 3 |
| `MEL_music_bass_clef` | Music Bass Clef | 3 |
| `MEL_music_staff` | Music Staff | 3 |
| `MEL_music_harmonic` | Music Harmonic Driver | 3 |
| `MEL_music_phrase` | Music Phrase (Composite) | 3 |
| `MEL_music_sheet_rail` | Sheet Music Rail | 3 |
| `MEL_music_beam_cluster` | Music Beam Cluster | 3 |
| `MEL_music_chord_stack` | Music Chord Stack | 3 |
| `MEL_music_triplet_note` | Music Triplet Note | 3 |
| `MEL_music_fermata` | Music Fermata | 3 |
| `MEL_music_repeat_bar` | Music Repeat Bar | 3 |
| `MEL_music_time_signature` | Music Time Signature | 3 |
| `MEL_music_stand` | Music Stand | 3 |

#### Instruments — Tuned Plates (7 builders)

| Builder | Label | Presets |
|---------|-------|---------|
| `MEL_music_celesta` | Music Celesta | 3 |
| `MEL_music_glockenspiel` | Music Glockenspiel (GN Twin) | 3 |
| `MEL_music_kalimba` | Music Kalimba | 3 |
| `MEL_music_timpani` | Music Timpani | 3 |
| `MEL_music_tubular_bells` | Music Tubular Bells | 3 |
| `MEL_music_dulcimer` | Music Dulcimer | 3 |
| `MEL_music_bamboo_chimes` | Music Bamboo Chimes | 3 |

#### Instruments — Strings (9 builders)

| Builder | Label | Presets |
|---------|-------|---------|
| `MEL_music_harp` | Music Harp | 3 |
| `MEL_music_harp_v2` | Music Harp v2 (Parabolic) | 3 |
| `MEL_music_lissajous_harp` | Lissajous Harp | 3 |
| `MEL_music_piano_roll` | Music Piano Roll | 3 |
| `MEL_music_waveform_wall` | Waveform Wall | 3 |
| `MEL_music_waveform_wall_v2` | Waveform Wall v2 | 3 |
| `MEL_harp_concert_real` | Concert Harp (Real) | 0 |
| `MEL_harp_ur_lyre` | Lyre of Ur (Ancient) | 0 |
| `MEL_harp_kora` | Kora (Mande) | 0 |

#### Instruments — Winds & Percussion (8 builders)

| Builder | Label | Presets |
|---------|-------|---------|
| `MEL_brass_pipe` | Brass Pipe | 2 |
| `MEL_reed_body` | Reed Body | 0 |
| `MEL_bell_chime` | Bell/Chime | 3 |
| `MEL_church_bell` | Church Bell | 3 |
| `MEL_singing_bowl` | Singing Bowl | 3 |
| `MEL_tuning_fork` | Tuning Fork | 3 |
| `MEL_music_tuning_fork` | Tuning Fork Column | 3 |
| `MEL_violin_bow` | Violin Bow | 0 |

#### Instruments — Baroque Kit (4 builders)

| Builder | Label | Presets |
|---------|-------|---------|
| `MEL_music_baroque_harpsichord` | Music Baroque Harpsichord | 3 |
| `MEL_music_baroque_violin` | Music Baroque Violin | 3 |
| `MEL_music_baroque_organ` | Music Baroque Organ (Walkable) | 3 |
| `MEL_music_baroque_lute` | Music Baroque Lute | 3 |

#### Music-Themed Architecture (10 builders)

| Builder | Label | Presets |
|---------|-------|---------|
| `MEL_music_jingle_tower` | Music Jingle Tower | 3 |
| `MEL_music_boss_gate` | Music Boss Gate | 3 |
| `MEL_music_victory_plaza` | Music Victory Plaza | 3 |
| `MEL_music_lullaby_nook` | Music Lullaby Nook | 3 |
| `MEL_music_metronome_pillar` | Metronome Pillar | 3 |
| `MEL_music_soundhole_rosette` | Soundhole Rosette | 3 |
| `MEL_music_frequency_ribcage` | Frequency Ribcage | 3 |
| `MEL_music_harmonograph` | Harmonograph Tracery | 3 |
| `MEL_music_key_unit` | Music Key Unit | 3 |
| `MEL_music_room_shell` | Music Room Shell | 3 |

#### Chimes & Special (9 builders)

| Builder | Label | Presets |
|---------|-------|---------|
| `MEL_chime_tube` | Chime Tube (Tuned) | 0 |
| `MEL_chime_field_scatter` | Chime Field Scatter | 0 |
| `MEL_chime_mark_tree` | Mark Tree Curtain | 0 |
| `MEL_chime_carillon_tier` | Carillon Ring Tier | 0 |
| `MEL_chime_aeolian_wall` | Aeolian Harp Wall | 0 |
| `MEL_music_vinyl_disc` | Vinyl Disc | 3 |
| `MEL_imm_piano_keys` | Piano Key Row (IMM) | 0 |
| `MEL_wind_siku` | Siku (Andes) | 0 |
| `MEL_staff_bridge` | Staff Bridge | 0 |

---

### 9. Castle Kit (22 builders)

| Builder | Label | Presets |
|---------|-------|---------|
| `MEL_castle_crenellation` | Castle Crenellation | 0 |
| `MEL_castle_wall_segment` | Castle Wall Segment | 0 |
| `MEL_castle_tower` | Castle Tower | 3 |
| `MEL_castle_gatehouse` | Castle Gatehouse | 0 |
| `MEL_castle_gothic_window` | Castle Gothic Window | 3 |
| `MEL_castle_buttress` | Castle Buttress | 0 |
| `MEL_castle_keep` | Castle Keep | 0 |
| `MEL_castle_curtain_wall` | Castle Curtain Wall | 0 |
| `MEL_castle_machicolations` | Castle Machicolations | 0 |
| `MEL_castle_spiral_stairs` | Castle Spiral Stairs | 0 |
| `MEL_castle_assembler` | Castle Full Assembler | 3 |
| `MEL_castle_drawbridge` | Castle Drawbridge | 0 |
| `MEL_castle_corner_bastion` | Castle Corner Bastion | 0 |
| `MEL_castle_corner_turret` | Castle Corner Turret | 0 |
| `MEL_castle_portcullis` | Castle Portcullis | 0 |
| `MEL_castle_arrow_slit` | Castle Arrow-Slit Wall | 0 |
| `MEL_castle_hoarding` | Castle Hoarding | 0 |
| `MEL_castle_siege_tower` | Castle Siege Tower | 0 |
| `MEL_castle_barbican` | Castle Barbican | 0 |
| `MEL_pergola_walkway` | Pergola Walkway | 0 |
| `MEL_recursive_castle_spire` | Recursive Castle Spire | 3 |
| `MEL_endless_escher_bridge` | Endless Escher Bridge | 0 |

---

### 10. Operations (3 builders)

| Builder | Label | Presets |
|---------|-------|---------|
| `MEL_op_iterate` | Iterate + Power Falloff | 3 |
| `MEL_op_bounded` | Bounded Auto-Fit | 3 |
| `MEL_op_power_clamp` | Clamped Power Scale | 3 |

---

### 11. Mesh Tools (14 builders)

| Builder | Label | Presets |
|---------|-------|---------|
| `MEL_bevel_profile` | Bevel Profile | 0 |
| `MEL_weighted_bevel` | Weighted Bevel | 3 |
| `MEL_auto_bevel` | Auto Bevel (Ease) | 3 |
| `MEL_curvature_bevel` | Curvature Bevel | 3 |
| `MEL_multi_bevel` | Multi Bevel | 0 |
| `MEL_inset_faces` | Inset Faces | 0 |
| `MEL_poke_faces` | Poke Faces | 0 |
| `MEL_subdivision_surface` | Subdivision Surface | 0 |
| `MEL_remesh_dual` | Remesh Dual | 0 |
| `MEL_smooth_laplacian` | Smooth Laplacian | 0 |
| `MEL_shell_thicken` | Shell Thicken | 0 |
| `MEL_symmetry_weld` | Symmetry Weld | 0 |
| `MEL_vertex_relax` | Vertex Cluster Relax | 0 |
| `MEL_edge_ring_inset` | Edge Ring Inset | 0 |

---

### 12. Set Dressing (15 builders)

| Builder | Label | Presets |
|---------|-------|---------|
| `MEL_env_lily_pond` | Lily Pond | 0 |
| `MEL_env_stepping_stones` | Stepping Stones | 0 |
| `MEL_env_reeds_patch` | Reeds Patch | 0 |
| `MEL_env_buoy_line` | Buoy Line | 0 |
| `MEL_env_market_stall` | Market Stall | 0 |
| `MEL_env_campfire_ring` | Campfire Ring | 0 |
| `MEL_env_village_well` | Village Well | 0 |
| `MEL_env_lantern_post` | Lantern Post | 0 |
| `MEL_env_hedgerow` | Hedgerow | 0 |
| `MEL_env_waterfall_pool` | Waterfall Pool | 0 |
| `MEL_pcg_water_tags` | PCG Water Tags | 0 |
| `MEL_pcg_water_tags_v2` | PCG Water Tags v2 | 3 |
| `MEL_pcg_music_tags` | PCG Music Tags | 0 |
| `MEL_pcg_music_tags_v2` | PCG Music Tags v2 | 0 |
| `MEL_material_crosswalk` | Material Crosswalk | 0 |

---

### 13. Faraway Mother (16 builders)

| Builder | Label | Description | Presets |
|---------|-------|-------------|---------|
| `MEL_mother_head_silhouette` | Head Silhouette | Faraway Mother head/veil silhouette — cliff-scale face as terrain | 0 |
| `MEL_mother_hair_cascade` | Hair Cascade | Veil-hair waterfall — fabric-textured hair as drapery | 0 |
| `MEL_mother_valley_depression` | Valley Depression | Lap-valley basin — body impression as explorable valley | 0 |
| `MEL_mother_fog_volume` | Fog Volume | Breath-fog volumetrics above valley | 0 |
| `MEL_mother_fabric_ridge` | Fabric Ridge | Dress-fold ridge — seam-driven strata | 0 |
| `MEL_mother_shoulder_fold` | Shoulder Fold | Shoulder drape overhang | 0 |
| `MEL_mother_heart_gate` | Heart Gate | Chest heart-gate arch — passage through torso | 0 |
| `MEL_mother_moonlight_rig` | Moonlight Rig | Moonlight projection rig for silhouette | 0 |
| `MEL_mother_walkway_straight` | Walkway Straight | Flat walkway with fold displacement | 0 |
| `MEL_mother_walkway_curved` | Walkway Curved | Curved path walkway with banking | 0 |
| `MEL_mother_frill_rock` | Frill Rock | Frilled rock/lace-edge boulders | 0 |
| `MEL_mother_frill_arch` | Frill Arch | Frill-lace archway | 0 |
| `MEL_mother_lace_tree` | Lace Tree | Filigree lace tree — delicate branch lattice | 0 |
| `MEL_mother_pearl_bush` | Pearl Bush | Pearl-cluster bush scatter | 0 |
| `MEL_mother_silk_vine` | Silk Vine | Silk vine drape along surfaces | 0 |
| `MEL_mother_brocade_flower` | Brocade Flower | Embroidered brocade flower scatter | 0 |

---

### 14. White Current (6 builders)

| Builder | Label | Description | Presets |
|---------|-------|-------------|---------|
| `MEL_white_seam_spline` | Seam Spline | White Current seam spline | 0 |
| `MEL_eel_silhouette` | Eel Silhouette | Eel silhouette curve | 0 |
| `MEL_water_network` | Water Network | Water network graph | 0 |
| `MEL_moonlit_surf` | Moonlit Surf | Moonlit surf line | 0 |
| `MEL_white_haze_volume` | White Haze Volume | Volumetric haze | 0 |
| `MEL_white_current_field` | White Current Field | Flow field driver | 0 |

---

### 15. God That Molts (8 builders)

| Builder | Label | Description | Presets |
|---------|-------|-------------|---------|
| `MEL_shell_cephalon` | Shell Cephalon | Trilobite cephalon shell plate | 0 |
| `MEL_shell_thorax` | Shell Thorax | Segmented thorax plates | 0 |
| `MEL_shell_pygidium` | Shell Pygidium | Tail shell plate | 0 |
| `MEL_shell_interior` | Shell Interior | Interior carapace volume | 0 |
| `MEL_fracture_seam` | Fracture Seam | Molt fracture-line seam | 0 |
| `MEL_shell_growth_rings` | Growth Rings | Concentric growth-ring displacement | 0 |
| `MEL_shell_iridescence` | Shell Iridescence | Pearlescent shell surface | 0 |
| `MEL_molt_volume` | Molt Volume | Full molt volume proxy | 0 |

---

## Uncategorized (8 builders)

These have no category assignment in `register_builder()`:

| Builder | Label | Presets |
|---------|-------|---------|
| `MEL_escher_belvedere` | Escher Belvedere Loggia | 3 |
| `MEL_escher_penrose_stairs` | Escher Penrose Stairs | 3 |
| `MEL_escher_waterfall` | Escher Waterfall | 3 |
| `MEL_sky_observatory` | Celestial Dream Observatory | 3 |
| `MEL_nikki_quarter` | Nikki Flora Quarter | 3 |
| `MEL_roll_walkable` | Roll Walkable Field | 0 |
| `MEL_edge_band_weight` | Edge Band Weight | 0 |
| `MEL_math_gothic_cathedral` | Math Gothic Cathedral | 0 |

---

## Preset System

### How Presets Work

1. Each builder creates a Geometry Nodes group with named input sockets
2. `BUILDERS_PRESETS` maps builder IDs to curated parameter sets
3. Preset keys match the **exact** socket names (e.g. `"Base Width"`, not `"base_width"`)
4. The GN Stack UI exposes presets as dropdown buttons

### Accessor API

```python
from deploy.surreal_arch.melodia_gn.presets import (
    builders_with_presets,   # list[str]
    preset_names,            # builder_id → list[str]
    preset_param_sets,       # builder_id → list[dict]
    export_builder_preset,   # (builder_id, preset_name) → dict
    export_all_presets_json, # path → str
    audit_presets,           # → dict report
)
```

### Adding a New Preset

1. Find the builder's `register_builder()` call to get its input socket names
2. Add an entry to `BUILDERS_PRESETS[builder_id]["presets"]`
3. Optionally add `preset_labels` and `preset_descriptions`
4. Test: `python -c "from deploy.surreal_arch.melodia_gn.presets import audit_presets; print(audit_presets())"`

---

## File Map

| File | Role |
|------|------|
| `deploy/surreal_arch/melodia_gn/core.py` | Registry, categories, `register_builder()` |
| `deploy/surreal_arch/melodia_gn/presets.py` | `BUILDERS_PRESETS` dict (268 presets) |
| `deploy/surreal_arch/melodia_gn/__init__.py` | Module imports (registers all builders) |
| `deploy/surreal_arch/melodia_gn/stack.py` | GN Stack UI panel |
| `deploy/surreal_arch/melodia_gn/primitives.py` | 14 primitive builders |
| `deploy/surreal_arch/melodia_gn/profiles.py` | 8 profile builders |
| `deploy/surreal_arch/melodia_gn/structures.py` | 3 structure builders |
| `deploy/surreal_arch/melodia_gn/castle.py` | 13 castle builders |
| `deploy/surreal_arch/melodia_gn/castle_extras.py` | 7 castle extras |
| `deploy/surreal_arch/melodia_gn/effects.py` | 6 magic effect builders |
| `deploy/surreal_arch/melodia_gn/water.py` | 4 water builders |
| `deploy/surreal_arch/melodia_gn/ornament.py` | 5 ornament builders |
| `deploy/surreal_arch/melodia_gn/ornament_extras.py` | 6 ornament extras |
| `deploy/surreal_arch/melodia_gn/filigree.py` | 3 filigree builders |
| `deploy/surreal_arch/melodia_gn/music.py` | 6 music builders |
| `deploy/surreal_arch/melodia_gn/music_aaa.py` | 9 AAA music builders |
| `deploy/surreal_arch/melodia_gn/music_harps_real.py` | 5 realistic harp builders |
| `deploy/surreal_arch/melodia_gn/music_heroes.py` | 5 music hero builders |
| `deploy/surreal_arch/melodia_gn/music_instruments.py` | 6 instrument builders |
| `deploy/surreal_arch/melodia_gn/music_terrain.py` | 2 terrain builders |
| `deploy/surreal_arch/melodia_gn/melodia_kit_v2.py` | 5 v2 kit builders |
| `deploy/surreal_arch/melodia_gn/melodia_kit_v3.py` | 4 v3 kit builders |
| `deploy/surreal_arch/melodia_gn/melodia_kit_v4.py` | 4 v4 kit builders |
| `deploy/surreal_arch/melodia_gn/melodia_kit_baroque.py` | 4 baroque kit builders |
| `deploy/surreal_arch/melodia_gn/chimes_gn.py` | 5 chime builders |
| `deploy/surreal_arch/melodia_gn/notation_extras.py` | 8 notation extras |
| `deploy/surreal_arch/melodia_gn/math_ops.py` | 6 math/attribute builders |
| `deploy/surreal_arch/melodia_gn/operations.py` | 2 operation builders |
| `deploy/surreal_arch/melodia_gn/mesh_tools.py` | 10 mesh tool builders |
| `deploy/surreal_arch/melodia_gn/set_dressing.py` | 2 set dressing builders |
| `deploy/surreal_arch/melodia_gn/env_extras.py` | 10 environment extras |
| `deploy/surreal_arch/melodia_gn/geometry_extras.py` | 15 geometry extras |
| `deploy/surreal_arch/melodia_gn/polyhedra_gn.py` | 7 polyhedron builders |
| `deploy/surreal_arch/melodia_gn/recursive_castle.py` | 3 recursive castle builders |
| `deploy/surreal_arch/melodia_gn/escher_belvedere.py` | 1 Escher builder |
| `deploy/surreal_arch/melodia_gn/escher_penrose_stairs.py` | 1 Escher builder |
| `deploy/surreal_arch/melodia_gn/escher_waterfall.py` | 1 Escher builder |
| `deploy/surreal_arch/melodia_gn/sky_observatory.py` | 1 observatory builder |
| `deploy/surreal_arch/melodia_gn/nikki_quarter.py` | 1 Nikki builder |
| `deploy/surreal_arch/melodia_gn/infinity_nikki_kit.py` | 4 Nikki kit builders |
| `deploy/surreal_arch/melodia_gn/ribbon.py` | 4 ribbon builders |
| `deploy/surreal_arch/melodia_gn/pcg_integration.py` | 6 PCG integration builders |
| `deploy/surreal_arch/melodia_gn/aaa_quality.py` | Quality audit (no builders) |

---

## Git History

- `deploy/surreal_arch/melodia_gn/` — 51 Python files, 232 builders (15 categories)
- `deploy/surreal_arch/melodia_gn/presets.py` — 268 curated presets across 89 builders
- `deploy/surreal_arch/melodia_gn/core.py` — registry + 15 categories (added `mother`, `white_current`, `god_molts` 2026-09-01)
