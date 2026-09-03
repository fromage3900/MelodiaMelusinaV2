# Blender 5.2 Audio Terrain Pipeline

Melodia Studio now includes three native Blender 5.2 Geometry Nodes builders:

- `MEL_audio_spectrum_terrain` — continuous frequency-displaced terrain;
- `MEL_audio_spectrum_towers` — frequency-bin mesh cities, walls, and reefs;
- `MEL_audio_radial_field` — concentric arena and Monolith pulse terrain.

Each builder uses Blender 5.2's `Sample Sound Frequencies` node and stores
`audio_amplitude` (plus `frequency_hz` where applicable) for downstream
materials, baking, and Unreal export. This is an offline authoring lane. Unreal's
existing rhythm/audio subsystem remains runtime authority.

## Interactive use

Open Blender 5.2, select or create a mesh, then open **Melodia GN Stack** in the
sidebar. Search for `audio`. Add one of the three builders and choose one of its
three curated presets. Assign a sound to the modifier's `Sound` input and set
`Time` to inspect or keyframe a sample.

The nine initial presets cover small Monolith fields, walkable highlands,
bass-focused canyons/fortresses, choir-scale cities/craters, and large
continent/wall/Horizon Eater stress-test configurations.

## Large-scale batch generation

```powershell
python Tools/audio_terrain_pipeline.py `
  --audio Imports/Audio/song_a.wav Imports/Audio/song_b.wav `
  --times 0 5 15 30 60 `
  --output Saved/AudioTerrain
```

The controller launches Blender 5.2 headlessly once per source. Each resulting
editable `.blend` contains all three builders, all three presets per builder,
and every requested time sample. The output directory receives
`audio_terrain_batch_manifest.json` for orchestration and later UE intake.

For tiled Unreal handoff, add a grid and FBX export:

```powershell
python Tools/audio_terrain_pipeline.py `
  --audio Imports/Audio/song_a.wav `
  --builders MEL_audio_spectrum_terrain `
  --presets FULL_SONG_CONTINENT `
  --times 0 15 30 45 `
  --tile-grid 8 8 --tile-size 256 --export-fbx `
  --output Saved/AudioTerrain/Continent
```

Frequency coverage is deterministically partitioned across tile X. Tile Y
extends the field spatially. Every `.blend` receives a sibling
`.audio_terrain_handoff.json` containing tile coordinates, world origins,
frequency bands, named attributes, FBX paths, byte sizes, SHA-256 hashes, and
the recommended Unreal content root.

Validate the handoff outside Unreal:

```powershell
python Content/Python/import_audio_terrain_handoff.py `
  Saved/AudioTerrain/Continent/AudioTerrain_song_a.audio_terrain_handoff.json
```

Inside Unreal's Python environment, add `--apply` to batch-import the verified
FBXs into deterministic builder/preset/time folders under
`/Game/Melodia/World/AudioTerrain`. The importer refuses schema, path, byte-size,
hash, or duplicate-tile failures before touching the Content Browser.

Use `--dry-run` to validate the job matrix without launching Blender.

Three scale profiles make repeatable runs easy:

- `--profile preview`: one 128 m tile, one time sample, editable `.blend`;
- `--profile region`: 4×4 256 m tiles, three time samples, terrain + radial FBX;
- `--profile continent`: 16×16 512 m tiles, four time samples, terrain FBX.

Profiles deliberately expand to deterministic ordinary arguments and are
recorded in the batch manifest. Run `--dry-run` first for region/continent jobs.

## Scale-up path

1. Use low-resolution presets for composition and frequency-range selection.
2. Promote selected songs/presets to the continent, megaspectrum, or Horizon
   Eater configurations.
3. Split long songs into explicit time samples or orchestrated batches.
4. Bake only approved fields; retain the editable GN source `.blend`.
5. Export geometry and named attributes through the existing Melodia Studio UE
   handoff rather than introducing a second runtime audio authority.
