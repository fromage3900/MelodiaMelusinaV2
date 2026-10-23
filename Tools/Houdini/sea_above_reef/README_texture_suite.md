# Sea Above Reef Texture Suite — runbook

Part of `Docs/Handoffs/HOUDINI_SEA_ABOVE_P0_AND_AAA_POLISH_PLAN_2026-08-28.md` (§3A).

## Status

- Texture suite: **committed, deterministic, not yet cooked** — the agent console wedged
  (hython hang 2026-08-28) and the Blender MCP bridge was down, so no PNGs exist yet.
  Nothing is claimed as cooked until `reef_texture_ingest_manifest.json` exists with
  `tileable_pass == files`.
- Hython mesh builder: **queued behind the license verdict** (see below).
- `probe_hython_license.ps1` exists so no future console gets wedged by a bare hython call.

## Cook the texture suite (no Houdini needed, no editor needed)

```powershell
python Tools/Houdini/sea_above_reef/tilable_sand_suite.py
python Tools/Houdini/sea_above_reef/tilable_shell_masks.py
python Tools/Houdini/sea_above_reef/underwater_clutter_atlas.py
python Tools/Houdini/sea_above_reef/ingest_reef_textures.py --include-sheets
```

Outputs land in `Saved/Audit/sea_above/houdini_variants/`:

| File | Kind | UE import |
|---|---|---|
| `T_SeaAbove_Sand_Albedo` | sRGB colour | sRGB=true, World |
| `T_SeaAbove_Sand_Height/Normal/WetMask/RippleMask` | data | sRGB=false, World |
| `T_SeaAbove_Caustics` | data | sRGB=false, Effects; 2-copy panner blend |
| `T_SeaAbove_ShellMask_Nautilus/Scallop/Conch/SandDollar` | data masks | sRGB=false, World |
| `T_SeaAbove_Clutter_Atlas` | RGBA decal atlas | sRGB=true, Effects |
| `T_SeaAbove_ClutterFloor_Mask` | data | sRGB=false, World |
| `_ShellMasks_ContactSheet`, `_Clutter_Sprites_ContactSheet` | QA only | do not import |

Plus per-suite manifests (`sand_suite_manifest.json`, `shell_masks_manifest.json`,
`clutter_atlas_manifest.json`) and the combined verifier `reef_texture_ingest_manifest.json`.

The ingest run is the proof: every tiling target must report `tileable=True` (edge seam
metric under 3 levels). A `SEAM` line means regenerate or investigate — never hand-wave it.

## Blender fallback (if Pillow is unavailable in the console)

```powershell
blender --background --python Tools/Houdini/sea_above_reef/tilable_sand_suite.py
```

The bpy path saves via Non-Color pass-through with a vertical-flip correction so values
match the PIL path byte-for-byte. The shell-mask and clutter scripts require Pillow
(vector motif drawing) and will say so if run under Blender.

## Clutter meshes (hython) — COOKED 2026-08-28

```powershell
Tools/Houdini/sea_above_reef/probe_hython_license.ps1     # verdict first, isolated probes
hython Tools/Houdini/sea_above_reef/build_clutter_meshes.py
```

**Verified pipeline facts (all evidence-driven this session):**
- hython 22.0.368 imports `hou` headless; license server answers; **no Engine license**
  (`Used Licenses: None`) → HDA-in-UE stays parked.
- **FBX ROP export is Apprentice-blocked** ("FBX export is not supported in Houdini Apprentice").
- **Alembic ROP export is Apprentice-blocked too** ("only supported in Houdini Core and FX") —
  which also means the groom lane's "real ABC via hython" was never actually cooked.
- The working export path is the **File SOP in write mode**: `filemode` menu tokens are
  `('auto','read','write','none')` — index `3` is "No Operation" (caught by evidence probe
  `probe_file_write.py`); use the `"write"` token. Writes both `.obj` (UE-native import today)
  and `.bgeo.sc` (readable in UE later via a Houdini Engine license).
- Geometry is built in **Python SOPs** (hou.Geometry API). H22 does **not** prebind `geo` —
  use `geo = hou.pwd().geometry()`. Tubes are built in code (rings + caps); the Sweep SOP
  produced 0 prims headless and was replaced.

**Outputs** (`Saved/Audit/sea_above/meshes/`, seed 20260828):
| Mesh | Contents |
|---|---|
| `SM_Clutter_PebbleSet.obj/.bgeo.sc` | 14 non-overlapping squashed UV spheres (170 KB obj) |
| `SM_Clutter_Starfish.obj/.bgeo.sc` | 5-arm star profile, polyextrude puff |
| `SM_Clutter_SpiralShell.obj/.bgeo.sc` | log-spiral tube, 610 prims |
| `SM_Clutter_SeaWeed.obj/.bgeo.sc` | sway-curved tapered tube, 200 prims |
| `clutter_mesh_manifest.json` | seeds, formats, UE import notes |

**UE import:** `.obj` at 100× scale (Houdini metres → UE cm), Nanite on, assign `MI_SeaAbove_*`
instances. The `.bgeo.sc` copies are for the Engine-licensed import path later.

## Determinism contract

- Suite seed: `20260828` (per-script `--seed` override). Call order is part of the seed
  contract — do not parallelise cooks from one process.
- Every output file is hashed into its manifest; the ingest re-derives everything.
- Manifests are outputs, never inputs (AGENTS.md rule 12).
