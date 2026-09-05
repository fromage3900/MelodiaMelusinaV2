# Melodia Geometry Nodes — Complete Reference
> Study notes for college. Covers every GN system in the studio: architecture, pipelines, data flow, and the musical theory that drives it all.

---

## Table of Contents

1. [System Map](#1-system-map)
2. [Melodia GN — Primary Authority](#2-melodia-gn--primary-authority)
3. [Kawaii GN — Cute/Chibi Assets](#3-kawaii-gn--cutechibi-assets)
4. [Brutalist GN — Monolithic Architecture](#4-brutalist-gn--monolithic-architecture)
5. [Melodia Studio — MIDI-Driven World Gen](#5-melodia-studio--midi-driven-world-gen)
6. [Resonant World Studio — Voxel Legacy](#6-resonant-world-studio--voxel-legacy)
7. [Supporting Addons](#7-supporting-addons)
8. [Musical Theory → Spatial Mapping](#8-musical-theory--spatial-mapping)
9. [Key Architecture Patterns](#9-key-architecture-patterns)
10. [Audio-Reactive Pipeline](#10-audio-reactive-pipeline)
11. [File Reference Index](#11-file-reference-index)

---

## 1. System Map

```
BS_GodFile/
├── deploy/surreal_arch/
│   ├── melodia_gn/              ← 60+ builders (PRIMARY GN AUTHORITY)
│   │   ├── core.py              ← safe_node, link_sockets, Blender 5.x remap
│   │   ├── music.py             ← note heads, clefs, staves, phrases
│   │   ├── audio_terrain.py     ← Blender 5.2 Sample Sound Frequencies
│   │   ├── castle.py            ← towers, keeps, buttresses, spiral stairs
│   │   ├── ornament.py          ← vines, radials, frames, panels
│   │   ├── garment_*.py         ← audio drape, loom, tension folds, XPBD
│   │   ├── mother*.py           ← Faraway Mother fabric mountains
│   │   ├── music_*.py           ← instrument + terrain builders
│   │   ├── p4_*.py              ← cathedral, organ pipes, crystal, weave
│   │   └── ... (60+ more)
│   └── melodia_gn_route.py      ← ARCH_TO_GN routing, 40+ arch types
│
├── Tools/BlenderAddons/
│   ├── melodia_studio/           ← MIDI → World (LARGEST ADDON)
│   │   ├── studio_panel.py       ← N-panel UI (1313L)
│   │   ├── midi_bridge.py        ← MIDI parse, presets, generate_world
│   │   ├── walkable_world.py     ← v4 serpentine/spiral fold, walkability
│   │   ├── core/field.py         ← SINGLE SOURCE OF TRUTH: MIDI→heightfield
│   │   ├── terrain_dressing.py   ← musical-role props + magic systems
│   │   ├── tandem_bridge.py      ← terrain ↔ surreal city snap
│   │   ├── world_streaming.py    ← chunked LOD world
│   │   ├── ancient_cultures.py   ← 12 instrument presets
│   │   └── ...
│   │
│   ├── blender_kawaii_gn/        ← cute/chibi procedural
│   │   ├── core/gn_framework.py  ← KawaiiGNBase + registry
│   │   ├── core/node_builder.py  ← safe_link, mesh_input resolution
│   │   ├── core/material_generator.py ← 8 pastel palettes, plushie shader
│   │   ├── generators/           ← 20+ generators (arch, char, food, nature...)
│   │   └── ui/panel_main.py      ← cuteness slider, theme picker
│   │
│   ├── blender_brutalist_gn/     ← monolithic concrete
│   │   ├── core/gn_framework.py  ← BrutalistGNBase + registry
│   │   └── generators/           ← tower, monument, complex, wall, details
│   │
│   ├── resonant_world_studio/    ← voxel legacy
│   │   ├── build.py              ← OBJ import, AuraColor material
│   │   ├── bridge.py, ops.py, panel.py
│   │
│   ├── melodia_aura/             ← 6 aura presets (fire/ice/lightning/healing/dark/holy)
│   ├── melodia_showroom/         ← multi-render AAA
│   ├── melodia_stage/            ← 3-point lighting + camera
│   ├── melodia_pose_audit/       ← bone validation
│   └── GenesisCore/              ← MCP client for AI providers
│
└── studio/                       ← MUSIC SIDE
    ├── tracks/frost-rave/        ← UNDERTOW rave pack (MIDI + USTX)
    ├── ustx/                     ← OpenUtau projects
    └── voice-tests/              ← TTS line tests
```

---

## 2. Melodia GN — Primary Authority

**Path:** `deploy/surreal_arch/melodia_gn/`
**Role:** 60+ builder modules. The backbone of surreal architecture generation.
**Framework:** Functional (not class-based). Each module exports `build_*()` functions.

### Core Utilities (`core.py` — 1288 lines)

| Function | Purpose |
|----------|---------|
| `safe_node(tree, bl_idname, loc)` | Create node with Blender 5.x `NODE_REMAP_52` fallback |
| `require_node(tree, bl_idname, loc, *aliases)` | Create or raise — missing nodes must not silently passthrough |
| `link_sockets(tree, from_sock, to_sock)` | Safe link creation |
| `new_geometry_tree(name)` | Create tree with Group Input/Output |
| `add_float_param(tree, name, default, min, max)` | Add interface socket |
| `label_tree(ng, name)` | Color + label for visual identification |
| `sweep_profile(...)` | Extrude profile along path |
| `input_geometry_with_default(...)` | Geometry input with fallback |

**Blender 5.x Compatibility:**
```python
NODE_REMAP_52 = {
    "GeometryNodeCube": "GeometryNodeMeshCube",
    "GeometryNodeUVSphere": "GeometryNodeMeshUVSphere",
    "GeometryNodeSeparateXYZ": "ShaderNodeSeparateXYZ",
    "ShaderNodeTime": "GeometryNodeInputSceneTime",
    # ... 10+ remaps
}
```

### Builder Categories

| Category | Files | Examples |
|----------|-------|----------|
| **Musical** | `music.py`, `music_aaa.py`, `music_harps_real.py`, `music_heroes.py`, `music_instruments.py`, `music_terrain.py` | Note heads, treble clefs, staves, harmonic drivers, phrase builders, instrument geometry |
| **Castle** | `castle.py`, `recursive_castle.py`, `castle_extras.py` | Tower, gatehouse, keep, crenellation, buttress, curtain wall, spiral stairs, machicolations |
| **Ornament** | `ornament.py`, `ornament_extras.py` | Vine, radial, frame, panel, grid |
| **Structures** | `structures.py` | Gazebo, portico, arch |
| **Escher** | `escher_belvedere.py`, `escher_penrose_stairs.py`, `escher_waterfall.py` | Impossible geometry |
| **Garment** | `garment_audio_drape.py`, `garment_loom.py`, `garment_tension_folds.py`, `garment_xpbd_drape.py` | Audio-reactive fabric, loom weaving, tension folds, XPBD simulation |
| **Mother** | `mother.py`, `mother_v3.py`, `mother_tapestry_wall.py` | Faraway Mother fabric mountain systems |
| **P4 Series** | `p4_crystal_cathedral.py`, `p4_cymatic_organ_pipes.py`, `p4_fractal_cathedral.py`, `p4_molten_shell_city.py`, `p4_resonance_harp_array.py`, `p4_tapestry_citadel.py`, `p4_weave_terrain.py` | Crystal cathedral, cymatic organ pipes, fractal cathedral, molten shell city, resonance harp array, tapestry citadel, weave terrain |
| **Terrain** | `planetary_terrain.py`, `audio_terrain.py`, `music_terrain.py` | Planetary-scale, audio-reactive, musical terrain |
| **Effects** | `ribbon.py`, `water.py`, `white_current.py`, `effects.py` | Fluid, ribbon, particle effects |
| **Other** | `sky_observatory.py`, `nikki_quarter.py`, `polyhedra_gn.py`, `set_dressing.py`, `bake.py`, `pcg_integration.py` | Observatory, Infinity Nikki quarter, polyhedra, set dressing, bake-to-UE, PCG |

### Routing (`melodia_gn_route.py`)

```python
ARCH_TO_GN = {
    "GAZEBO": ("structures.build_gazebo", "MEL_gazebo"),
    "MELODIA_NOTE_HEAD": ("music.build_music_note_head", "MEL_music_note_head"),
    "CASTLE_TOWER": ("castle.build_castle_tower", "MEL_castle_tower"),
    # ... 40+ entries
}
```

**Decision flow:**
1. `should_use_melodia_gn(arch_type, prefer=True)` → checks `ARCH_TO_GN` or prefix match
2. `try_apply_melodia_gn(obj, props, monolith)` → creates/attaches GN modifier, binds music props
3. `_collection_for_arch_type(arch_type)` → routes to correct collection (`MusicalGN_Editable`, `OrnamentGN_Editable`, etc.)

---

## 3. Kawaii GN — Cute/Chibi Assets

**Path:** `Tools/BlenderAddons/blender_kawaii_gn/`
**Framework:** Class-based. `KawaiiGNBase` + `@register_generator` decorator → `KAWAII_GN_REGISTRY`.

### Framework (`core/gn_framework.py`)

```python
class KawaiiGNBase:
    category: str = "base"
    generator_id: str = "base"
    generator_name: str = "Base Generator"
    uses_input_geometry: bool = False
    _node_tree: Optional[bpy.types.GeometryNodeTree] = None

    @classmethod
    def get_node_tree(cls): ...  # Cache or build
    @classmethod
    def build_node_tree(cls, tree): ...  # Override
    @classmethod
    def create_object(cls, name): ...  # Create mesh + GN modifier
    @classmethod
    def apply_to_object(cls, obj): ...  # Add modifier to existing
```

**Key features:**
- `ensure_geometry_interface(tree, with_input)` — Blender 5.x leaves new groups without default I/O
- `kindchenschema_scale(cuteness)` — head/body scale from 0-1 cuteness
- `apply_scene_cuteness_to_object(obj, cuteness)` — drives all GN modifiers from scene
- `ensure_roundness_parameter(tree)` — every tree exposes Roundness

### Generators (20+)

| Category | Files | Examples |
|----------|-------|----------|
| architecture | `kawaii_architecture.py` | Bricks, walls, pillars, foundations |
| characters | `kawaii_characters.py` | Chibi characters |
| decorations | `kawaii_decorations.py`, `kawaii_decorations_advanced.py` | Basic + advanced decor |
| effects | `kawaii_effects.py` | Kawaii VFX |
| food | `kawaii_food.py`, `kawaii_food_advanced.py`, `kawaii_ice_cream.py` | Food items |
| furniture | `kawaii_furniture.py` | Cute furniture |
| greybox | `kawaii_greybox.py` | Blockout tools |
| nature | `kawaii_nature.py`, `kawaii_nature_advanced.py` | Plants, trees |
| plushies | `kawaii_plushies.py`, `kawaii_plushies_advanced.py` | Plush toys |
| props | `kawaii_props.py` | General props |

### Material Generator (`core/material_generator.py`)

**8 curated pastel palettes:**
- `pastel_pink`, `pastel_blue`, `pastel_lavender`, `pastel_mint`, `pastel_peach`, `pastel_yellow`, `pastel_lilac`, `rainbow`

Each palette: `primary`, `secondary`, `accent`, `dark` RGBA tuples.

**Material types:**
- `create_pastel_material()` — PBR with subsurface scattering
- `create_plushie_fabric()` — fuzzy shader with fuzziness parameter

### UI (`ui/panel_main.py`)

**Scene properties:**
- `cuteness_level` (0-1) — drives Roundness on all generators
- `pastel_theme` — enum of 8 palettes
- `plushie_fabric_style` — pastel vs plushie_fabric
- `export_lod` / `export_lod_ratio` — UE5 LOD chain generation

---

## 4. Brutalist GN — Monolithic Architecture

**Path:** `Tools/BlenderAddons/blender_brutalist_gn/`
**Framework:** `BrutalistGNBase` + `@register_generator` → `BRUTALIST_GN_REGISTRY`.

### Generators

| Class | Description |
|-------|-------------|
| `BrutalistTowerBlockGN` | Massive residential tower with repetitive windows |
| `BrutalistMonumentGN` | Oversized civic monument with taper |
| `BrutalistComplexGN` | Multi-structure complexes |
| `BrutalistWallGN` | Fortification walls |
| `BrutalistDetailsGN` | Surface detail panels |

**Parameters (typical):** Width, Depth, Floors, Floor Height, Window Spacing, Taper — all exposed as GN interface sockets.

---

## 5. Melodia Studio — MIDI-Driven World Gen

**Path:** `Tools/BlenderAddons/melodia_studio/`
**Role:** The largest single addon. MIDI → parse → heightfield → voxels → OBJ → Blender mesh.
**Philosophy:** Musical structure becomes spatial structure. The score IS the world.

### Architecture

```
MIDI File
    ↓
midi_bridge.parse_midi() → tracks, ticks_per_beat
    ↓
walkable_world.build_heightfield() → {(x,y): (height, velocity)}
    ↓
    ├── fill_gaps() → close single-cell holes
    ├── limit_slope() → clamp neighbour deltas
    └── walkability() → metrics dict
    ↓
terrain_dressing.plan_dressing() → prop placement plan
    ↓
studio_panel → Blender mesh with AuraColor vertex colors
    ↓
tandem_bridge → snap surreal city to terrain heightfield
```

### Core Modules

#### `midi_bridge.py` (444 lines)

**Presets (20+):** Each maps musical parameters to spatial:
- `chunk_beats` — how much song time per world chunk
- `surface_height_divisor` — lower = taller terrain
- `cave_height_divisor` — lower = deeper caves
- `use_beatgrid` — layer percussion as cave system
- `aura_emission` — glow intensity

**Key functions:**
- `load_voxel_module()` — imports `midi_voxel_v3` from `Tools/midi_to_voxel/`
- `generate_world(midi_path, preset_id, out_obj)` — parse → voxels → OBJ
- `dress_terrain(terrain_obj, obj_path, style_id, seed, budget, midi_path)` — plan dressing
- `discover_midi(extra_dirs)` — find all `.mid` files in project
- `beatgrid_for(melody_path)` — find matching `_beatgrid` file

#### `walkable_world.py` (411 lines)

**v4 mapping (the fix for v3's "wall" problem):**
- v3: time→X, pitch-class→Y → 64-beat song = 64×11 ribbon (not walkable)
- v4: **serpentine fold** wraps timeline across 2D plane → 64-beat song = ~8×8 ground

**Fold modes:**
- `serpentine_xy(index, grid_w)` — boustrophedon (back-and-forth)
- `spiral_xy(index, grid_w)` — inward spiral (finale at center)

**Pipeline:**
```python
def build_heightfield(notes, cells_per_beat, height_scale, plateau_radius, tpb, fold):
    # 1. Map each note to (x, y) via fold
    # 2. Full pitch (not pitch-class) drives height
    # 3. Stamp soft plateau around each note
    # 4. Return {(x,y): (height, velocity)}
```

**Walkability metrics:**
- `walkability(field, max_step)` — cells, footprint, coverage, aspect ratio, walkable_fraction
- `largest_connected_region(field, max_step)` — biggest reachable area

#### `core/field.py` (136 lines) — SINGLE SOURCE OF TRUTH

```python
def build_field(midi_path, preset_id="walkable_valley", source="walkable"):
    # 1. Parse MIDI
    # 2. Merge beatgrid if present (+36 semitones)
    # 3. build_heightfield() → fill_gaps() → limit_slope()
    # 4. walkability() + largest_connected_region()
    # 5. Return {ok, field, grid_w, preset, metrics, notes}
```

Used by 6+ modules: `roll_field`, `smooth_terrain`, `tandem_bridge`, `studio_panel`, `midi_bridge`, `world_streaming`.

#### `terrain_dressing.py` (455 lines)

**Dressing kinds (musical roles):**

| Kind | Trigger | Density | Color | Description |
|------|---------|---------|-------|-------------|
| `resonance_crystal` | peak (high velocity) | 0.28 | blue | Grows on loud notes |
| `chime_pillar` | ridge (sustained) | 0.16 | gold | Tall verticals on ridgelines |
| `moss_cluster` | valley (low) | 0.42 | green | Fills flat walkable areas |
| `songstone` | path (traversable) | 0.22 | purple | Along walkable routes |
| `note_bloom` | slope (movement) | 0.34 | pink | Flowers on transitions |

**Magic systems:**

| System | Kind | Description |
|--------|------|-------------|
| `aurora_veil` | volume | Sky curtain keyed to tonal centre |
| `motif_wisps` | particles | Drifting motes following melody |
| `cadence_pool` | water | Reflective water in lowest basin |
| `harmonic_rings` | rings | Concentric rings on strongest chord |
| `ground_glow` | underlight | Light seeping between voxels |

**Dressing styles (16 recipes):** bare, verdant, crystalline, cathedral, full_bloom, waltz_garden, ballad_plaza, toccata_surface, lullaby_cave, fugue_maze, nocturne_reflection, pavane_grotto, saltarello_ledges, madrigal_canopy, chaconne_weave, aria_mist.

#### `tandem_bridge.py` (523 lines)

**Field-wins principle:** Terrain height dictates building Z. The 2D surreal plan (flat at Z=0) is snapped onto the musical heightfield.

```python
MELODIA_TO_SURREAL = {
    "walkable_valley":     ("WESTERN_CASTLE",      "castle",      "verdant"),
    "walkable_highlands":  ("GOTHIC_NAVE_CROSSING", "castle",     "crystalline"),
    "walkable_canyon":     ("BRUTALIST_PLAZA",     "motte_bailey", "cathedral"),
    # ... 15+ pairings
}
```

#### `world_streaming.py` (139 lines)

Chunked world generation:
- 16×16 chunks
- LOD levels (full, half, quarter)
- View-distance culling
- Seamless chunk edge stitching

#### `ancient_cultures.py` (355 lines)

12 deeply-researched presets, each from a real ancient instrument tradition:

| Preset | Culture | Instrument | Era |
|--------|---------|------------|-----|
| `ur_lyre` | Sumer | Silver Lyre of Ur | Early Dynastic III (~2550 BCE) |
| `hurrian_hymn` | Hurrian | H6 tablet | Late Bronze Age (~1400 BCE) |
| `egypt_harp` | Egypt | Bow harp | New Kingdom (18th Dynasty) |
| `greek_aulos` | Greece | Aulos | Archaic/Classical |
| `guqin_seclusion` | China | Guqin | Zhou/Tang literati |
| `sho_gagaku` | Japan | Sho | Gagaku (Tang-derived) |
| `siku_andes` | Andes | Siku | Pre-Columbian |
| ... | ... | ... | ... |

Each preset: `chunk_beats` = meter, `surface_height_divisor` = register/attack, `use_beatgrid` = drone/percussion split.

---

## 6. Resonant World Studio — Voxel Legacy

**Path:** `Tools/BlenderAddons/resonant_world_studio/`

| Module | Role |
|--------|------|
| `build.py` (376L) | Blender scene construction — terrain from OBJ with AuraColor vertex colors |
| `bridge.py` | Connection layer to voxel generator |
| `ops.py` | Operators |
| `panel.py` | UI panel |

**Key function:** `terrain_from_obj(obj_path)` — reads `v x y z r g b` OBJ into mesh with AuraColor attribute + aura material (emission driven by vertex color luminance).

---

## 7. Supporting Addons

### Melodia Aura (`melodia_aura/`)
6 aura presets as particle systems:

| Preset | Color | Emission | Speed | Turbulence |
|--------|-------|----------|-------|------------|
| fire | orange | 8.0 | 1.5 | 2.0 |
| ice | cyan | 5.0 | 0.7 | 0.8 |
| lightning | white | 12.0 | 3.0 | 4.0 |
| healing | green | 4.0 | 0.5 | 0.3 |
| dark | purple | 6.0 | 1.0 | 1.5 |
| holy | gold | 7.0 | 0.8 | 0.5 |

### Melodia Showroom (`melodia_showroom/`)
Multi-render AAA system with debug scene tools, showroom bridge with presets, test suite.

### Melodia Stage (`melodia_stage/`)
Three-point lighting (key/fill/rim) + camera composition:
- Key: 800 energy, area light, 45° up-right-front
- Fill: 300 energy, softer, opposite side
- Rim: 500 energy, spot, behind subject
- Portrait lens: 85mm

### Melodia Pose Audit (`melodia_pose_audit/`)
Pose validation — checks bone positions against reference.

### GenesisCore (`GenesisCore/`)
MCP client for AI providers (Claude, DeepSeek, Ollama, OpenAI, OpenRouter, SiliconFlow). Server with tool packages for materials, modifiers, objects, assets.

---

## 8. Musical Theory → Spatial Mapping

The core insight driving Melodia Studio: **musical structure becomes spatial structure**.

### Mapping Rules

| Musical Parameter | Spatial Effect |
|-------------------|----------------|
| Note onset (time) | X position (via fold) |
| Note pitch | Height (elevation) |
| Note velocity | Block type + color |
| Pitch range | Height span |
| Beat grid | Cave layer (underground) |
| Chord changes | Terrain chunk boundaries |
| Meter (3/4, 4/4, 6/8) | `chunk_beats` in presets |
| Instrument register | Surface vs cave emphasis |
| Sustained notes | Plateau radius |
| Staccato/attack | Slope steepness |

### Preset Examples

| Preset | chunk_beats | surface_div | cave_div | Musical Logic |
|--------|-------------|-------------|----------|---------------|
| `resonant_default` | 4 | 32 | 40 | Balanced 4/4 |
| `cathedral_wide` | 8 | 20 | 50 | 8-beat phrases stretch time |
| `waltz_corridors` | 3 | 26 | 34 | Triple-meter waltz |
| `toccata_spires` | 2 | 18 | 28 | Rapid-fire 2-beat chunks |
| `lullaby_undergrowth` | 8 | 36 | 14 | Slow phrases, dominant caves |
| `fugue_labyrinth` | 4 | 28 | 18 | Contrapuntal interweaving |

### Ancient Cultures Mapping

| Culture | chunk_beats | Logic |
|---------|-------------|-------|
| Lyre of Ur | 4 | Stately heptatonic hymns |
| Hurrian Hymn | 5 | Descending refrain → stepped plateaus |
| Greek Aulos | 3 | Trochee rhythm → switchback ravines |
| Guqin | 8 | Sparse breathing → long level ledges |
| Sho | 7 | Cluster chords → tiered temple plateaus |
| Siku | 5 | Hocketing → stepped agriculture bands |

---

## 9. Key Architecture Patterns

### Registry Pattern (Kawaii GN, Brutalist GN)
```python
@register_generator
class KawaiiBricksGN(KawaiiGNBase):
    category = "architecture"
    generator_id = "kawaii_bricks_gn"
    # ...
```

### Base Class + Override (All GN frameworks)
```python
class KawaiiGNBase:
    @classmethod
    def build_node_tree(cls, tree):
        cls.add_parameters(tree, input_node, output_node)
        cls.build_geometry(tree, input_node, output_node)
```

### Single Source of Truth (Melodia Studio)
`core/field.py` → `build_field()` is the one function all 6+ modules call for MIDI→heightfield.

### Safe Node Creation (Melodia GN)
```python
def safe_node(tree, bl_idname, loc, fallback_callable=None):
    resolved = _resolve_bl_idname(bl_idname)  # Blender 5.x remap
    try:
        return tree.nodes.new(resolved)
    except Exception:
        # Try original, then fallback, then None
```

### Field-Wins Snap (Tandem Bridge)
Terrain height dictates building Z. 2D surreal plan snapped to heightfield via `surface_height_at()`.

### Kindchenschema Scaling (Kawaii GN)
```python
def kindchenschema_scale(cuteness):
    c = max(0.0, min(1.0, cuteness))
    return (1.0 + c * 0.35, 1.0 - c * 0.15)  # head_scale, body_scale
```

### Scene-Level Cuteness (Kawaii GN)
```python
def apply_scene_cuteness_to_object(obj, cuteness):
    for mod in obj.modifiers:
        if mod.type == 'NODES':
            for item in mod.node_group.interface.items_tree:
                if item.name in ('Cuteness', 'Roundness', 'Chibi'):
                    mod[item.identifier] = cuteness
```

---

## 10. Audio-Reactive Pipeline

### Blender 5.2 Native (`audio_terrain.py`)

Uses `GeometryNodeSampleSoundFrequencies` — first-class GN node in Blender 5.2.

**Inputs:** Sound data-block, Time (seconds), Low/High Hz, FFT Size, Window function
**Output:** Amplitude (float) → drive any GN field

**Workflow:**
1. Drop audio into VSE
2. GN picks strip directly
3. FFT analysis → amplitude per Hz band
4. Drive geometry displacement, emission, etc.

**For UE export (GN is Blender-only):**
- Option A: Store Named Attribute → Alembic/USD with animated vertex attributes
- Option B: Bake bands to 1px-per-band image sequence → Curve Atlas texture → UE Material

### Research Tools (from `BLENDER_AUDIO_GEOMETRY_NODES_PIPELINE_2026-09-02.md`)

| Tool | Type | Best For |
|------|------|----------|
| **Sample Sound Frequencies** | Blender 5.2 native | Live GN authoring, scrub-safe |
| **Sound Nodes** (negdo) | Addon | Spectrogram → Chladni plates, chromagram → wardrobe hue |
| **Sound Reaktor** (Inoshiro) | Addon (Pro) | SciPy bake replacement, 50-200x faster than native |
| **AudVis** (example-sk) | Addon | Real-time + MIDI + scriptable, live playtest |
| **Animation Nodes** | Legacy reference | Sound Spectrum as field of N bins |

### Integration Contracts

**SpeedTree semantic bridge** (9 fields):
`melodia_moisture, melodia_slope, melodia_wind_exposure, melodia_soil_depth, melodia_monolith_proximity, melodia_molt_age, melodia_filter_flow, melodia_tension, melodia_ecological_density`

**World Field Bus** (minimum shared contract):
`WorldField.FilterFlow / Tension / Moisture / Contact / Residue / Reaction / AnchorStability / Resonance`

**Cymatic pattern publishers:**
`ModeN / ModeM` → `WorldField.Resonance`
`SampleCymaticAmplitude` → `WorldField.Tension`

---

## 11. File Reference Index

### Melodia GN (60+ builders)

| File | Lines | Purpose |
|------|-------|---------|
| `core.py` | 1288 | Safe node creation, linking, Blender 5.x remap |
| `music.py` | 859 | Note heads, clefs, staves, phrases |
| `audio_terrain.py` | 236 | Blender 5.2 Sample Sound Frequencies |
| `castle.py` | — | Tower, gatehouse, keep, crenellation |
| `recursive_castle.py` | — | Recursive castle generation |
| `ornament.py` | — | Vine, radial, frame, panel |
| `garment_audio_drape.py` | — | Audio-reactive fabric drape |
| `garment_loom.py` | — | Loom weaving |
| `garment_tension_folds.py` | — | Tension fold simulation |
| `garment_xpbd_drape.py` | — | XPBD cloth simulation |
| `mother.py` / `mother_v3.py` | — | Faraway Mother fabric mountains |
| `music_terrain.py` | — | Musical terrain builder |
| `music_aaa.py` | — | AAA musical geometry |
| `music_harps_real.py` | — | Realistic harp geometry |
| `music_heroes.py` | — | Hero instrument builders |
| `music_instruments.py` | — | Instrument builders |
| `p4_crystal_cathedral.py` | — | Crystal cathedral |
| `p4_cymatic_organ_pipes.py` | — | Cymatic organ pipes |
| `p4_fractal_cathedral.py` | — | Fractal cathedral |
| `p4_molten_shell_city.py` | — | Molten shell city |
| `p4_resonance_harp_array.py` | — | Resonance harp array |
| `p4_tapestry_citadel.py` | — | Tapestry citadel |
| `p4_weave_terrain.py` | — | Weave terrain |
| `planetary_terrain.py` | — | Planetary-scale terrain |
| `polyhedra_gn.py` | — | Polyhedral geometry |
| `ribbon.py` | — | Ribbon effects |
| `water.py` | — | Water effects |
| `white_current.py` | — | White current effects |
| `effects.py` | — | General effects |
| `sky_observatory.py` | — | Celestial observatory |
| `nikki_quarter.py` | — | Infinity Nikki quarter |
| `set_dressing.py` | — | Set dressing placement |
| `bake.py` | — | Bake-to-UE pipeline |
| `pcg_integration.py` | — | PCG integration for UE |
| `structures.py` | — | Gazebo, portico, arch |
| `escher_belvedere.py` | — | Escher belvedere |
| `escher_penrose_stairs.py` | — | Penrose stairs |
| `escher_waterfall.py` | — | Impossible waterfall |
| `filigree.py` | — | Filigree details |
| `god_molts.py` | — | God molt effects |
| `infinity_nikki_kit.py` | — | Nikki kit |
| `melodia_kit_v2/v3/v4.py` | — | Kit versions |
| `melodia_kit_baroque.py` | — | Baroque kit |
| `math_ops.py` | — | Math operations |
| `mesh_tools.py` | — | Mesh tools |
| `notation_extras.py` | — | Notation extras |
| `operations.py` | — | Operations |
| `presets.py` | — | Presets |
| `primitives.py` | — | Primitives |
| `profiles.py` | — | Profiles |
| `stack.py` | — | Stack operations |
| `logging.py` | — | Logging |
| `aaa_quality.py` | — | AAA quality |
| `env_extras.py` | — | Environment extras |
| `geometry_extras.py` | — | Geometry extras |
| `chimes_gn.py` | — | Chimes |

### Melodia Studio

| File | Lines | Purpose |
|------|-------|---------|
| `studio_panel.py` | 1313 | N-panel UI |
| `midi_bridge.py` | 444 | MIDI parse, presets, generate |
| `walkable_world.py` | 411 | v4 walkable terrain |
| `terrain_dressing.py` | 455 | Dressing + magic systems |
| `tandem_bridge.py` | 523 | Terrain ↔ city snap |
| `ancient_cultures.py` | 355 | 12 instrument presets |
| `world_streaming.py` | 139 | Chunked LOD world |
| `core/field.py` | 136 | SINGLE SOURCE OF TRUTH |
| `gaea_panel.py` | — | Gaea UI |
| `gaea_terrain_io.py` | — | Gaea import/export |
| `gaea_erosion_processor.py` | — | Erosion processing |
| `smooth_terrain.py` | — | Smoothing |
| `roll_field.py` | — | Field rolling |
| `sheep_bake_prep.py` | — | Sheep bake prep |
| `sheep_shapekeys.py` | — | Sheep shapekeys |
| `sheep_shine.py` | — | Sheep shine |
| `atmosphere.py` | — | Atmosphere |
| `export_choral_sheep.py` | — | Sheep export |
| `melodia_chrome.py` | — | Chrome utilities |
| `addon_utils.py` | — | Addon utilities |
| `preview_choral_flock.py` | — | Flock preview |
| `musical_structure.py` | — | Musical structure |
| `_batch_remaining_presets.py` | — | Batch presets |

### Kawaii GN

| File | Lines | Purpose |
|------|-------|---------|
| `core/gn_framework.py` | 243 | KawaiiGNBase + registry |
| `core/node_builder.py` | 160 | Safe link, mesh input |
| `core/material_generator.py` | 261 | 8 palettes, plushie shader |
| `core/operators.py` | 223 | Generate + UE5 export |
| `ui/panel_main.py` | 130 | Cuteness slider, theme |
| `utils/animation.py` | — | Animation utils |
| `utils/instancer.py` | — | Instancer utils |
| `generators/kawaii_architecture.py` | 210 | Bricks, walls, pillars |
| `generators/kawaii_characters.py` | — | Chibi characters |
| `generators/kawaii_decorations.py` | — | Decorations |
| `generators/kawaii_decorations_advanced.py` | — | Advanced decorations |
| `generators/kawaii_effects.py` | — | VFX |
| `generators/kawaii_food.py` | — | Food |
| `generators/kawaii_food_advanced.py` | — | Advanced food |
| `generators/kawaii_furniture.py` | — | Furniture |
| `generators/kawaii_greybox.py` | — | Greybox |
| `generators/kawaii_ice_cream.py` | — | Ice cream |
| `generators/kawaii_nature.py` | — | Nature |
| `generators/kawaii_nature_advanced.py` | — | Advanced nature |
| `generators/kawaii_plushies.py` | — | Plushies |
| `generators/kawaii_plushies_advanced.py` | — | Advanced plushies |
| `generators/kawaii_props.py` | — | Props |

### Brutalist GN

| File | Purpose |
|------|---------|
| `core/gn_framework.py` | BrutalistGNBase + registry |
| `core/operators.py` | Operators |
| `generators/structures.py` | Tower, monument |
| `generators/complexes.py` | Complexes |
| `generators/walls.py` | Walls |
| `generators/details.py` | Surface details |
| `ui/panel_main.py` | UI |
| `utils/export.py` | Export utils |

---

## Glossary

| Term | Definition |
|------|------------|
| **AuraColor** | Vertex color attribute storing note velocity → drives material emission |
| **Beatgrid** | Secondary MIDI file (`*_beatgrid.mid`) storing percussion → cave layer |
| **Boustrophedon** | Serpentine fold — back-and-forth like ox plowing fields |
| **Chunk** | World segment = `chunk_beats` beats of song time |
| **Field** | `{(x,y): (height, velocity)}` — the heightfield |
| **Fold** | How 1D timeline wraps to 2D plane (serpentine or spiral) |
| **GN** | Geometry Nodes — Blender's procedural geometry system |
| **Kindchenschema** | "Baby schema" — cuteness proportions (big head, small body) |
| **LOD** | Level of Detail — lower poly for distant objects |
| **MIDI** | Musical Instrument Digital Interface — note events, not audio |
| **MPC** | Material Parameter Collection (UE) |
| **PCG** | Procedural Content Generation (UE) |
| **Plateau radius** | Soft area around each note so it's standable, not a spike |
| **Serpentine** | See Boustrophedon |
| **Slope limiting** | Clamping neighbour height deltas so terrain is climbable |
| **Surface divisor** | Lower = taller terrain (velocity // divisor = height) |
| **TPB** | Ticks Per Beat — MIDI time resolution |
| **Tandem** | Terrain + city combined generation |
| **Voxel** | Volume pixel — 3D grid cell |
| **Walkability** | Fraction of edges traversable without exceeding max_step |

---

*Generated 2026-09-03 from BS_GodFile + studio filesystem. For college reference.*
