# Melodia Unified Terrain Handoff Contract

**Status:** CANONICAL DURABLE CONTRACT — the single cross-lane intake schema for
terrain authoring into UE 5.8 Mesh Terrain.

Three terrain-authoring lanes exist. They all target **UE 5.8 Mesh Terrain**
with a **100 cm/m import scale**, `classic_landscape_used: false`, and a
`/Game/` content namespace, but each kept its own handoff schema. This contract
locks one unified handoff document — `melodia.terrain_handoff.v1` —
that every lane emits as a sibling of its native handoff and that every intake
validates against.

A handoff that does not validate under the unified schema is **not UE-ready**.
A new lane handoff format without a converter in `Tools/terrain_handoff.py` is a
defect, not progress.

---

## 1. The three lanes

| Lane | Native handoff (authoritative for the lane) | Emitter | Unified sibling |
|---|---|---|---|
| **midi_voxel** | `ue_handoff/handoff_manifest.json` (`melodia_mesh_terrain_handoff`) | `Tools/BlenderAddons/melodia_studio/gaea_erosion_processor.py` → `build_mesh_terrain_handoff()` | `ue_handoff/terrain_handoff.json` |
| **audio_gn_5_2** | `Saved/AudioTerrain/*.audio_terrain_handoff.json` (`melodia.audio_terrain_ue_handoff.v1`) | `Tools/audio_terrain_pipeline.py` (Blender 5.2 GN `MEL_audio_spectrum_*`) | `Saved/AudioTerrain/*.terrain_handoff.json` |
| **gaea** | `Docs/WorldGen/GAEA_SETUP_*.json` (`melodia.gaea_setup.v1`) | contract-only (native export pending); convert with the CLI | `Saved/Audit/terrain_handoffs/*.terrain_handoff.json` |

Converters, validators and the CLI live in **`Tools/terrain_handoff.py`**
(schema `melodia.terrain_handoff.v1`). Lane docs keep their native schema as
authoritative; the unified sibling is the cross-lane index and intake surface.

## 2. Unified schema (`melodia.terrain_handoff.v1`)

| Field | Meaning | Notes |
|---|---|---|
| `schema` | `melodia.terrain_handoff.v1` | fixed |
| `handoff_id` | `lane:id` (e.g. `gaea:aurora_glacier`) | unique per generated document |
| `lane` | `midi_voxel` / `audio_gn_5_2` / `gaea` | defines source semantics |
| `source.kind` | `midi` / `audio_wav` / `gaea_graph` | input type |
| `source.preset` | preset id / builder id / `midi_preset` | lane-specific |
| `coordinate_system.unreal_scale_cm_per_meter` | **must be 100.0** | contract |
| `extent.width_m/depth_m/height_range_m/target_resolution/world_origin_m` | metric envelope | null until known |
| `artifacts.mesh_obj / heightfield_png16 / dressing_plan / handoff_manifest / masks / mesh_fbx / blend` | paths (repo-relative or absolute) | at least one required |
| `ue5_8.engine` | **must be `"5.8"`** | contract |
| `ue5_8.target` | **must be `"Mesh Terrain"`** | contract |
| `ue5_8.content_namespace` | **must start `/Game/`** | contract |
| `ue5_8.classic_landscape_used` | **must be `false`** | contract |
| `evidence.export_status / setup_status` | pending exports are exempt from strict file checks | see `--strict` |
| `provenance.generator_schema` | the native lane schema that produced it | traceability |

## 3. Mesh Terrain intake rule

A unified handoff is the intake token for `Tools/terrain_handoff.py` and any UE
intake. UE intake must refuse documents that fail `validate_handoff(..., strict_files=True)`.
Mesh Terrain is the only substrate; the four required engine plugins are
`MeshPartition`, `MeshTerrainMode`, `MeshPartitionWater`, `PCGMeshPartitionInterop`
(see `Docs/WorldGen/MESH_TERRAIN_GAEA_DEM_P0.md`).

## 4. GN terrain-builder roles (Blender 5.2)

| Builder | File in `deploy/surreal_arch/melodia_gn/` | Role |
|---|---|---|
| `MEL_audio_spectrum_terrain`, `MEL_audio_spectrum_towers`, `MEL_audio_radial_field` | `audio_terrain.py` | **audio_gn_5_2 lane** — WAV `Sample Sound Frequencies` displacement (offline authoring only) |
| `MEL_roll_walkable`, `MEL_staff_bridge`, `MEL_note_stair` | `music_terrain.py` | MIDI-shaped walkable terrain via GN (shares the music-as-key language) |
| `MEL_planetary_musical_terrain` | `planetary_terrain.py` | named-attribute planetary fields (`mel_height`, `mel_slope`, `mel_cavity`, `mel_shoreline`, `mel_biome`, `mel_traversal`) |
| `MEL_p4_weave_terrain` | `p4_weave_terrain.py` | experimental weave-floor terrain |
| `MEL_pcg_music_tags(_v2)`, `MEL_pcg_water_tags(_v2)`, `MEL_material_crosswalk(_v2)` | `pcg_integration.py` | **UE-side bridges** — tag PCG points from musical/water fields; not terrain shape |

None of these builders is a runtime authority. Blender audio sampling is an
authoring input; gameplay timing/rhythm authority stays in UE
(`LAPTOP_PROCEDURAL_LANE_2026-09-11.md` §4).

## 5. Non-negotiables

1. One intake schema: `melodia.terrain_handoff.v1`.
2. Every terrain lane emits a unified sibling; no new lane schema without a converter.
3. UE 5.8 Mesh Terrain only — `classic_landscape_used` stays `false`.
4. Import scale is 100 cm/m, always.
5. Runtime audio/rhythm authority stays in UE; GN/audio lanes are authoring input.
6. PCG reads the built Mesh Terrain partition, never a placeholder plane.
7. Strict validation exempts `pending_*` exports — a "pending" contract is a
   promise, not a claim of produced files.

## 6. Commands

```powershell
python Tools/terrain_handoff.py convert <native-lane-handoff.json> [--out-dir DIR]
python Tools/terrain_handoff.py convert-batch --dir Docs/WorldGen --out-dir Saved/Audit/terrain_handoffs
python Tools/terrain_handoff.py validate <terrain_handoff.json...> [--strict]
python Tools/test_terrain_handoff.py
```