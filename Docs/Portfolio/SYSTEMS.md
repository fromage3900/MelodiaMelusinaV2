# Systems — Technical Breakdown

> For interviews. What I built, why, and how it works. Every system below is shipped code in a solo-developed rhythm-JRPG prototype (Unreal Engine 5.8 + Blender 5.2). ~130 GB, 13,000+ files, 60+ Geometry Nodes builders, full C++ UE integration.

---

## 1. Melodia GN — 60+ Procedural Builders

**Path:** `deploy/surreal_arch/melodia_gn/`
**Scale:** 63 Python files, ~33,560 lines

### Problem
Hand-modeling surreal architecture (crystal cathedrals, cymatic organ pipes, impossible Escher staircases) is slow and unrepeatable. We needed a procedural system where a designer picks an archetype and gets a fully-formed, walkable, music-reactive structure — no manual modeling.

### Architecture
Functional (not class-based). Each module exports `build_*()` functions. A central router (`melodia_gn_route.py`) maps 40+ architecture types to builder functions via an `ARCH_TO_GN` dispatch table.

```
ARCH_TYPE → should_use_melodia_gn() → try_apply_melodia_gn()
                                        → _collection_for_arch_type() → collection
                                        → create/attach GN modifier
                                        → bind music props (BeatPulse, Bass, etc.)
```

### Builder Categories

| Category | Files | Examples |
|----------|-------|----------|
| Musical | `music.py` (859L), `music_aaa.py`, `music_harps_real.py`, `music_heroes.py`, `music_instruments.py`, `music_terrain.py` | Note heads, treble clefs, staves, harmonic drivers, phrase builders |
| Castle | `castle.py`, `recursive_castle.py`, `castle_extras.py` | Tower, gatehouse, keep, crenellation, buttress, spiral stairs |
| Ornament | `ornament.py`, `ornament_extras.py` | Vine, radial, frame, panel, grid |
| Garment | `garment_audio_drape.py`, `garment_loom.py`, `garment_tension_folds.py`, `garment_xpbd_drape.py` | Audio-reactive fabric, loom weaving, tension folds, XPBD simulation |
| Mother | `mother.py`, `mother_v3.py`, `mother_tapestry_wall.py` | Faraway Mother fabric mountains |
| P4 Series | `p4_crystal_cathedral.py`, `p4_cymatic_organ_pipes.py`, `p4_fractal_cathedral.py`, `p4_molten_shell_city.py`, `p4_resonance_harp_array.py`, `p4_tapestry_citadel.py`, `p4_weave_terrain.py` | Crystal cathedral, cymatic organ pipes, fractal cathedral, molten shell city |
| Terrain | `planetary_terrain.py`, `audio_terrain.py` (236L), `music_terrain.py` | Planetary-scale, audio-reactive terrain |
| Escher | `escher_belvedere.py`, `escher_penrose_stairs.py`, `escher_waterfall.py` | Impossible geometry |
| Effects | `ribbon.py`, `water.py`, `white_current.py`, `effects.py` | Fluid, ribbon, particle effects |

### Key Technical Decisions
- **Blender 5.x remap table** (`NODE_REMAP_52`): 10+ node renames handled transparently so builders work across Blender 5.0–5.2.
- **Safe node creation** (`safe_node`, `require_node`): missing nodes raise rather than silently passthrough — prevents "perfectly wired graph that produces nothing."
- **Music props binding**: every builder exposes `BeatPulse`, `BassIntensity`, `BeatPhase` as interface sockets so structures react to music without per-frame scripting.
- **Collection routing**: `_collection_for_arch_type()` routes to dedicated collections (`MusicalGN_Editable`, `OrnamentGN_Editable`, etc.) so the Outliner stays organized at scale.

---

## 2. MIDI→World Pipeline

**Path:** `Tools/BlenderAddons/melodia_studio/`
**Scale:** ~6,722 lines across 20+ modules

### Problem
How do you generate a game world from a song? Not a visualization — an actual walkable terrain where the score IS the landscape. The v3 mapping (time→X, pitch-class→Y) produced a 64×11 ribbon that was unplayable. We needed terrain a character can actually traverse.

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

### v4 Serpentine Fold (the fix)
- **v3**: time→X, pitch-class→Y → 64-beat song = 64×11 ribbon (not walkable)
- **v4**: **serpentine fold** wraps timeline across 2D plane → 64-beat song = ~8×8 ground
- Fold modes: `serpentine_xy` (boustrophedon/back-and-forth) and `spiral_xy` (inward spiral, finale at center)

### Core Modules

| Module | Lines | Role |
|--------|-------|------|
| `studio_panel.py` | 1313 | N-panel UI |
| `midi_bridge.py` | 444 | MIDI parse, 20+ presets, `generate_world()` |
| `walkable_world.py` | 411 | v4 walkable terrain, fold modes, walkability metrics |
| `terrain_dressing.py` | 455 | Musical-role props + 5 magic systems |
| `tandem_bridge.py` | 523 | Terrain ↔ surreal city snap (field-wins principle) |
| `ancient_cultures.py` | 355 | 12 instrument presets from real ancient traditions |
| `world_streaming.py` | 139 | Chunked LOD world (16×16 chunks) |
| `core/field.py` | 136 | **Single source of truth**: `build_field()` |

### Musical Theory → Spatial Mapping

| Musical Parameter | Spatial Effect |
|-------------------|----------------|
| Note onset (time) | X position (via fold) |
| Note pitch | Height (elevation) |
| Note velocity | Block type + color (AuraColor) |
| Beat grid | Cave layer (underground) |
| Chord changes | Terrain chunk boundaries |
| Meter (3/4, 4/4, 6/8) | `chunk_beats` in presets |

### Ancient Cultures Presets
12 deeply-researched presets: Ur Lyre (~2550 BCE), Hurrian Hymn (~1400 BCE), Egypt Harp, Greek Aulos, Guqin, Sho, Siku, etc. Each maps `chunk_beats` = meter, `surface_height_divisor` = register/attack.

### Key Technical Decisions
- **Single source of truth**: `core/field.py` → `build_field()` is called by 6+ modules. No duplicate MIDI parsing.
- **Field-wins snap**: Terrain height dictates building Z. The 2D surreal plan snaps onto the musical heightfield via `surface_height_at()`.
- **Walkability metrics**: `walkability(field, max_step)` returns cells, footprint, coverage, aspect ratio, walkable_fraction. `largest_connected_region()` finds the biggest reachable area.
- **16 dressing recipes**: bare, verdant, crystalline, cathedral, full_bloom, waltz_garden, ballad_plaza, etc.

---

## 3. Kawaii / Brutalist GN Frameworks

**Paths:** `Tools/BlenderAddons/blender_kawaii_gn/`, `Tools/BlenderAddons/blender_brutalist_gn/`
**Scale:** Kawaii ~3,584 lines; Brutalist ~800+ lines

### Problem
Two distinct visual styles needed procedural pipelines: cute/chibi assets (Kawaii) and monolithic concrete architecture (Brutalist). Both needed a framework where adding a new generator is one decorator, not a new system.

### Architecture (Kawaii)
Class-based. `KawaiiGNBase` + `@register_generator` decorator → `KAWAII_GN_REGISTRY`.

```python
@register_generator
class KawaiiBricksGN(KawaiiGNBase):
    category = "architecture"
    generator_id = "kawaii_bricks_gn"
    # ...
```

### Kawaii Generators (20+)

| Category | Examples |
|----------|----------|
| architecture | Bricks, walls, pillars, foundations |
| characters | Chibi characters |
| decorations | Basic + advanced decor |
| effects | Kawaii VFX |
| food | Food items, ice cream |
| furniture | Cute furniture |
| nature | Plants, trees |
| plushies | Plush toys (basic + advanced) |
| props | General props |
| greybox | Blockout tools |

### Material Generator
- **8 curated pastel palettes**: `pastel_pink`, `pastel_blue`, `pastel_lavender`, `pastel_mint`, `pastel_peach`, `pastel_yellow`, `pastel_lilac`, `rainbow`
- Each palette: `primary`, `secondary`, `accent`, `dark` RGBA tuples
- `create_pastel_material()` — PBR with subsurface scattering
- `create_plushie_fabric()` — fuzzy shader with fuzziness parameter

### Kindchenschema Scaling
```python
def kindchenschema_scale(cuteness):
    c = max(0.0, min(1.0, cuteness))
    return (1.0 + c * 0.35, 1.0 - c * 0.15)  # head_scale, body_scale
```
A scene-level `cuteness_level` (0–1) drives Roundness on ALL generators simultaneously via `apply_scene_cuteness_to_object()`.

### Brutalist GN
`BrutalistGNBase` + `@register_generator` → `BRUTALIST_GN_REGISTRY`.

| Class | Description |
|-------|-------------|
| `BrutalistTowerBlockGN` | Massive residential tower with repetitive windows |
| `BrutalistMonumentGN` | Oversized civic monument with taper |
| `BrutalistComplexGN` | Multi-structure complexes |
| `BrutalistWallGN` | Fortification walls |
| `BrutalistDetailsGN` | Surface detail panels |

Parameters (typical): Width, Depth, Floors, Floor Height, Window Spacing, Taper — all exposed as GN interface sockets.

### Key Technical Decisions
- **Registry pattern**: `@register_generator` auto-registers into a dict. Adding a generator = one class + one decorator. No central switch statement.
- **Scene-level cuteness**: one slider drives every modifier on every object. No per-object tweaking.
- **Blender 5.x interface safety**: `ensure_geometry_interface(tree, with_input)` handles the fact that new groups ship without default I/O in 5.x.

---

## 4. FACS Face Rig

**Path:** `Tools/build_melusina_face_rig.py`
**Scale:** 340 lines

### Problem
Melusina needs to emote and lip-sync. Hand-keying 68 facial morph targets per line of dialogue is impossible. We needed a FACS-driven system where high-level emotions and phonemes drive the low-level morphs automatically.

### Architecture

```
Emotion presets (additive)
    ↓
FACS Action Units (46 AUs)
    ↓
68 morph targets on SK_Melusina_V2_Body
    ↓
15 visemes for lip-sync
    ↓
Blink timer (~2 per 7s, randomized)
```

### FACS Curve Map
The 68 morph targets map to FACS Action Units:

| FACS AU | Morph Targets | Emotion |
|---------|---------------|---------|
| AU1 | innerBrowRaiserL/R | surprise, sadness |
| AU2 | outerBrowRaiserL/R | surprise |
| AU4 | browLowererL/R | anger, concentration |
| AU5 | upperLidRaiserL/R | surprise, fear |
| AU6 | cheekRaiserL/R | joy (Duchenne smile) |
| AU7 | lidTightenerL/R | anger, pain |
| AU9 | noseWrinklerL/R | disgust |
| AU10 | upperLipRaiserL/R | disgust |
| AU12 | lipCornerPullerL/R | joy |
| AU15 | lipCornerDepressorL/R | sadness |
| AU17 | chinRaiser | pride, anger |
| AU20 | lipStretcherL/R | fear |
| AU23 | lipTightener | anger, tension |
| AU25 | lipsPart | surprise, jaw drop |
| AU26 | jawDrop | surprise, yawn |
| AU28 | lipsSuck | thought, uncertainty |
| AU43/45 | eyesCloseL/R | blink |

### 15 Visemes
Phoneme → morph target mapping: `aa`, `ee`, `ih`, `oh`, `oo`, `th`, `ch`, `sh`, `mm`, `nn`, `ll`, `rr`, `ff`, `vv`, `bp`.

### Emotion Presets (additive)
`neutral`, `joy`, `anger`, `surprise`, `sadness`, `fear`, `disgust` — each a dict of FACS weights (0–1) applied on top of base animation.

### Pipeline Steps
1. Verify 68 FACS morph targets exist on the live mesh
2. Create Control Rig for face
3. Add FACS curve drivers to Control Rig
4. Wire viseme curves (15 phonemes → FACS)
5. Wire emotion layer (additive FACS)
6. Add blink timer (randomized, ~2 per 7s)
7. Compile ABP
8. Save ABP

### Key Technical Decisions
- **Additive emotion layer**: emotions are additive offsets on top of base facial animation, so surprise + joy blend naturally.
- **ARKit compatibility**: 52 of 103 morph targets are inert ARKit keys (bit-identical to Basis); the 68 real ones are FACS-driven.
- **Monolith MCP integration**: uses `anim("add_curve", ...)` and `bp("compile_blueprint", ...)` via the Monolith bridge — no raw `.uasset` binary editing.

---

## 5. Mocap Pipeline (Rokoko → UE Retarget)

**Path:** `Content/Python/import_rokoko_mocap.py`
**Scale:** 185 lines (import) + `Tools/animation_import_pipeline/` (~2,174 lines for MUAL-2)

### Problem
Rokoko SmartSuit Pro II exports FBX with Rokoko's skeleton. Melusina has a custom 465-bone skeleton. We needed a one-click pipeline: drop FBX in Inbox → import → retarget → save on Melusina. No manual skeleton mapping.

### Architecture

```
Rokoko FBX (CharacterRef profile)
    ↓
Imports/Mocap/Rokoko/Inbox/*.fbx
    ↓
import_source_anim() → A_Src_Rokoko_<name> on SK_MocapSource
    ↓
retarget_clip() → RTG_Mocap_to_Melusina_Current → A_Mocap_Rokoko_<name>
    ↓
SK_Melusina (V2 mesh, leader pose, zero re-retargeting)
```

### Bone-Name Gate
FBX must match `SK_MocapSource_Skeleton`. Export from Rokoko using the CharacterRef profile built from `SK_MocapSource`. If bones differ, import still lands but retarget quality degrades.

### Canonical Retargeter
`RTG_Mocap_to_Melusina_Current` → `IK_Melusina_Body_Current` (root_x, 19 chains). Both V1 and V2 meshes bind `SK_Melusina_Skeleton`, so output clips play on V2 via leader pose with zero re-retargeting.

### Headless Batch
`Tools/run_headless_mocap_retarget.ps1` runs full retarget of everything already imported as `A_Src_*` with the editor closed. Report lands at `Saved/Melodia/rokoko_import_report.json`.

### MUAL-2 (Melusina Universal Animation Library v2)
The broader animation import pipeline (~2,174 lines):

| Module | Lines | Role |
|--------|-------|------|
| `manifest_v2.py` | 274 | v2 sidecar contract, deterministic clip IDs |
| `pipeline.py` | 295 | CLI for MUAL-2 (offline + UE commands) |
| `import_chain.py` | 281 | Import + retarget chain |
| `live_promotion.py` | 381 | Live promotion to state machine/blendspace |
| `registry.py` | 198 | Clip catalog + registry writes |
| `promotion.py` | 177 | Promotion plan builder |
| `validate_source.py` | 150 | Source FBX validation |
| `acceptance.py` | 120 | Acceptance criteria |
| `foot_contact_audit.py` | 194 | Foot contact audit |

### Key Technical Decisions
- **Two-lane design**: Lane A (Rokoko/Cascadeur/Blender hand-keyed) and Lane B (foreign/Quaternius). Each has different validation rules.
- **v2 sidecar contract**: deterministic clip IDs via SHA1, strict schema validation, legacy sidecars are catalogued but never silently upgraded.
- **Fail-closed**: UE commands fail closed when editor/MCP bridge is unavailable. A foreign clip can never be promoted by accidentally invoking a legacy direct retargeter.

---

## 6. Audio-Reactive UE Subsystem

**Path:** `Source/BS_GodFile/MelodiaIntegration/MelodiaAudioReactivePresentationSubsystem.{h,cpp}`
**Scale:** 503 lines (93 header + 410 implementation)

### Problem
The world needs to react to music — materials pulse, particles emit, water glows, the UI breathes. But Niagara can't read a Material Parameter Collection, Oceanology's master is plugin-owned and can't be edited, and we had six+ Niagara systems reading constant 0 because nothing wrote the parameter collection they all consumed.

### Architecture

```
MelodiaAudioComponent (Quartz clock)
    ↓
MelodiaAudioReactivePresentationSubsystem (GameInstanceSubsystem)
    ↓ (tick, ~128 BPM fallback)
    ├── MPC_Melodia_Palette (materials)
    │   ├── BeatPulse, BeatPhase, BeatIntensity
    │   ├── BassIntensity, MidIntensity, TrebleIntensity
    │   └── ComboNormalized, VictoryPulse, EnemyTension
    ├── NPC_Melodia_Palette (Niagara FX)
    │   └── 64 parameters, 6+ NS_ consumers
    └── Oceanology drive (dynamic MIDs)
        ├── BeatPulse → PhaseGLow / HighlightBoost
        ├── Bass/Combat → ScatterBoost
        └── ImpactPulse → DeepScatteringColor shift
```

### Key Technical Decisions
- **Single writer contract**: This subsystem is the SOLE writer of `MPC_Melodia_Palette`. `UMelodiaCymaticsSubsystem` is read-only. No second writer, no new audio authority.
- **Niagara twin**: `NPC_Melodia_Palette` is the Niagara-side twin of the MPC. Niagara cannot sample an MPC, so the beat namespace is published twice.
- **Oceanology drive**: Oceanology's master (`M_Oceanology`) is plugin-owned and must never be edited. Material instances can't add collection samples. Solution: this subsystem creates one dynamic material instance per ocean surface component and writes 106 verified parameters by name. No Oceanology headers included — actor class matched by name so the file stays buildable with the plugin disabled.
- **Fallback BPM**: `LastKnownBPM = 128.0f` seeded at source music's tempo, overwritten every tick from the music clock's real tempo once musical time is live.
- **Battle context**: `PushBattleInputContext()` / `PopBattleInputContext()` route input through `UMelodiaInputContextSubsystem` so battle and exploration don't fight.
- **CPU profiling**: `TRACE_CPUPROFILER_EVENT_SCOPE(Melodia_DriveOceanBeatValues)` for immediate visualization in Unreal Insights.

---

## 7. Cymatic Fabric System

**Path:** `Source/BS_GodFile/MelodiaIntegration/MelodiaCymaticsSubsystem.{h,cpp}` + `MelodiaCymaticsWriterSubsystem.{h,cpp}`
**Scale:** 316 lines (65+91+55+105)

### Problem
We wanted fabric that doesn't just wave in the wind — it should vibrate like a Chladni plate, forming standing-wave patterns driven by the music. The pattern should be visible in the material (WPO, iridescence, emissive) and readable by Niagara for particle placement.

### Architecture

```
MPC_Melodia_Palette (BeatPulse, BassIntensity)
    ↓
UMelodiaCymaticsSubsystem (READ-ONLY sampler)
    ↓
Chladni standing-wave plate:
  amp = cos(n·π·u)·cos(m·π·v) − cos(m·π·u)·cos(n·π·v)
    ↓
ModeN = clamp(2 + floor(Bass * 6), 1, 8)
ModeM = clamp(3 + floor(BeatPulse * 5), 1, 8)
    ↓
WorldFieldBus.PublishResonance(ModeN, ModeM, TensionAtCenter, BeatPulse)
    ↓
UMelodiaCymaticsWriterSubsystem (SOLE writer of MPC_Cymatics_Driver)
    ↓
Materials (WPO, iridescence, emissive) + Niagara particle placement
```

### Key Technical Decisions
- **Read-only contract**: `UMelodiaCymaticsSubsystem` never writes the MPC. `IsReadOnlyByContract()` returns `true`. This is enforced, not convention.
- **Chladni formula**: `amp = cos(n·π·u)·cos(m·π·v) − cos(m·π·u)·cos(n·π·v)` where mode indices (n,m) are driven by audio bands. Bass pushes radial mode, beat pulse modulates cross mode.
- **WorldFieldBus**: Publishes `Resonance` (ModeN, ModeM, Tension, BeatPulse) and `Tension` (Chladni amplitude at plate center). Consumers sample this read-only contract.
- **Writer/subscriber split**: `UMelodiaCymaticsWriterSubsystem` is the sole writer of `MPC_Cymatics_Driver` (Cymatic_BeatPulse, Bass, EmissiveScale, IridescenceShift, UVDistortion). The sampler and writer stay coherent by mirroring the same mode calculation.
- **GN integration**: In Blender, `mother_tapestry_wall.py` and `p4_cymatic_organ_pipes.py` sample cymatic Height for displacement. The UE subsystem is the runtime counterpart.

---

## 8. Animation Import Pipeline

**Path:** `Tools/animation_import_pipeline/`
**Scale:** ~2,174 lines across 10 modules

### Problem
We had 87+ Cascadeur-animated FBX files, 30+ Rokoko mocap clips, hand-keyed Blender animations, and foreign assets from Quaternius. Each had different skeletons, scales, naming conventions, and root motion types. We needed a unified pipeline that validates, catalogs, retargets, and promotes clips without human error.

### Architecture

```
FBX + sidecar (.manifest.json)
    ↓
validate_source.py → unit guard (cm header, no dotted ARP names)
    ↓
manifest_v2.py → load_as_v2() → validate_v2()
    ↓
registry.py → catalog() → write_registry()
    ↓
import_chain.py → import + retarget
    ↓
promotion.py → build_plan()
    ↓
live_promotion.py → promote to state machine / blendspace / montage
    ↓
acceptance.py → acceptance criteria
foot_contact_audit.py → foot contact audit
```

### v2 Sidecar Contract
```json
{
  "schema_version": 2,
  "source_type": "cascadeur|blender|rokoko|foreign|ue_source",
  "status": "canonical|manual_required|blocked|legacy|promoted",
  "root_motion": "in_place|root",
  "consumers": ["blendspace", "state_machine", "montage", "additive_layer", "pose_search"],
  "contexts": ["locomotion", "battle", "cinematic", "additive", "emote", "dialogue", "exploration"]
}
```

### Deterministic Clip IDs
```python
def deterministic_clip_id(source_type, source_name, clip_name):
    source = _slug(source_type).upper()
    clip = _slug(clip_name).upper()
    digest = hashlib.sha1(f"{source}:{clip}:{source_name}".encode()).hexdigest()[:8]
    return f"MUAL_{source}_{clip}_{digest}"
```
Readable, path-independent, deterministic. Registry, JSON schema, and Unreal asset names share one portable identifier alphabet.

### Key Technical Decisions
- **Fail-closed**: Offline commands are authoritative for classification and preflight. UE commands fail closed when editor/MCP bridge is unavailable.
- **Legacy sidecars**: Can be read for cataloguing but never silently upgraded to canonical. Callers must use `to_v2_manifest()` then pass through v2 preflight.
- **Unit guard**: `preflight_fbx()` checks centimeter header, no dotted ARP names, skeleton validity. Foreign clips that fail are `blocked`, not promoted.
- **Promotion plan**: `build_plan()` computes the cheapest path from imported clip → state machine / blendspace / montage / additive layer. No manual wiring.
- **Foot contact audit**: `foot_contact_audit.py` validates that locomotion clips have proper foot contacts (no sliding).

---

## Cross-Cutting Technical Decisions

| Decision | Where | Why |
|----------|-------|-----|
| **Single source of Truth** | `core/field.py` (MIDI), `MPC_Melodia_Palette` (audio) | Prevents parallel-authority defects. One function/asset owns the data; everyone else reads. |
| **Single writer** | Audio-reactive subsystem, Cymatics writer | Two writers to the same parameter = race condition + silent bugs. Enforced by contract. |
| **Fail-closed** | Animation import, T3D injection | A foreign clip can never be promoted by accident. Missing editor = no promotion. |
| **Deterministic IDs** | MUAL-2 clip IDs, GN collection names | Path-independent, portable across clones. No "works on my machine." |
| **Read-only contracts** | Cymatics subsystem, WorldFieldBus | Presentation systems read; they never write. Prevents feedback loops. |
| **Blender 5.x remap** | `NODE_REMAP_52` in `core.py` | 10+ node renames handled transparently. Builders work across 5.0–5.2. |
| **Monolith MCP bridge** | Face rig, animation import | No raw `.uasset` binary editing. All editor mutations go through one serialized holder. |
| **CPU profiling** | `TRACE_CPUPROFILER_EVENT_SCOPE` | Every performance-critical tick loop is instrumented for Unreal Insights. |

---

*Last updated: 2026-09-03*
