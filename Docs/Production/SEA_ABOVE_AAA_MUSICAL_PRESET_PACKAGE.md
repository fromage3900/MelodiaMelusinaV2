# Sea Above AAA Musical Preset Package

This package applies the Blender 5.2 audio-terrain pipeline to the active Sea
Above prototype without changing production Water V10 assets or introducing a
second Unreal runtime music authority.

## Plan alignment

- The false-horizon terrain, Bell ribs, and membrane presets provide DCC source
  geometry for the isolated Sea Above namespace.
- They do not modify `M_Water_Master_Grand_v10_Upgrade`, integrated water
  instances, Niagara ownership, PCG authority, or P0 gameplay gates.
- Universal Musical Influence is exposed consistently as `Music Influence`,
  `Musical Amplitude`, `Musical Freq A`, and `Musical Freq B` on audio terrain,
  hero Baroque builders, and the upgraded greybox room.
- These controls are offline design/bake parameters. UE runtime response remains
  owned by the existing Melodia presentation subsystem and MPC.

## Review presets

### Audio terrain

- `SEA_ABOVE_FALSE_HORIZON`
- `SEA_ABOVE_BELL_RIBS`
- `SEA_ABOVE_MEMBRANE`

### Greybox rooms

- `SEA_ABOVE_REVEAL_GALLERY`
- `BELL_ANATOMY_CHAMBER`
- `FALSE_HORIZON_OBSERVATORY`

### Baroque heroes

- `HARPSICHORD_SEA_ABOVE_HERO`
- `VIOLIN_BELL_RELIQUARY`
- `ORGAN_ABYSSAL_CATHEDRAL`
- `LUTE_PELAGIC_VAULT`

All ten presets are discoverable through Melodia GN Stack preset search.

## Generated review package

Run:

```powershell
python Tools/stage_melodia_aaa_presets.py `
  --audio Content/Melodia/Characters/Metan/Audio/met_shop_open_01.wav `
  --output Saved/MelodiaPresetReview/Melodia_AAA_Preset_Review.blend `
  --export
```

The `.blend` contains:

- `00_STAGE`
- `01_AUDIO_TERRAIN`
- `02_GREYBOX_ROOMS`
- `03_BAROQUE_HEROES`
- `90_CAMERAS_LIGHTS`

Each preset object retains its builder ID, preset ID, serialized parameters,
and proposed UE destination as custom properties. Four review cameras isolate
the overview and the three scale families.

The sibling manifest records every preset and the UE export package. FBXs are
exported at world origin with modifiers evaluated, metres converted through the
standard Blender FBX scale settings, and SHA-256 hashes recorded.

## UE intake boundary

The exports are ready for Content Browser import review but are not silently
inserted into the live Sea Above map. Import selected approved meshes beneath:

`/Game/EnvSandbox/Monoliths/SeaAbove/Prototype/Terrain/AudioMusical/`

Use the false horizon and membrane as source geometry or Mesh Terrain inputs.
Keep water rendering on the clean Sea Above V10-derived instances and keep the
prototype membrane material separate from the water master, matching the P0
handoff.
