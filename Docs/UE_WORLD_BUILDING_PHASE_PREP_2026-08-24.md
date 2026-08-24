# UE World-Building Phase Prep — 2026-08-24

## Goal
Produce the first UE5 world-building artifacts from Melodia musical data:
heightfield import, landscape material setup, and props/PCG placement
driven by Blender-generated terrain + dressing data.

## Current commit
`b8f5b10f` — docs: review and expand Melodia Melusina pipeline

## Available inputs

### Gaea CLI
- Gaea 1: `C:\Program Files\QuadSpinner\Gaea\Gaea.Build.exe`
- Gaea 2: `C:\Program Files\QuadSpinner\Gaea 2\Gaea.BuildManager.exe`

### MIDI assets
- `Content/MelodiaIntegration/MIDI/128BPMarpeggiomelody.mid` — 192 notes
- `Content/MelodiaIntegration/MIDI/128BPMarpeggiomelody_beatgrid.mid` — 64 notes

### Blender outputs
- `Tools/BlenderAddons/melodia_studio/` — presets, dressing, walkability
- `Tools/BlenderAddons/melodia_showroom/` — render pipeline
- No existing heightfield exports in `Saved/Audit/` yet

### UE runtime
- `Source/BS_GodFile/MelodiaIntegration/MelodiaPCGWaterGameplayBridgeComponent.cpp/.h`
- `Source/BS_GodFile/MelodiaIntegration/MelodiaPCGNarrativeChallengeBridgeComponent.cpp/.h`
- `Plugins/PCGExtendedToolkit` referenced in `Docs/Integrations/MELODIA_EXTERNAL_ADAPTER_LEDGER.md`

---

## Today's phase — Landscape bootstrap

### Step 1: Export heightfield from Blender
- Run `melodia_studio` generate for `waltz_garden` preset
- Export 16-bit PNG heightfield from the v4 walkable field
- Save to `Saved/Audit/heightfield_<preset>_<date>.png`
- Evidence: file exists, dimensions match preset footprint

### Step 2: Author minimal Gaea graph
- Open Gaea 1 or 2
- Create graph: Heightmap -> Erosion -> Sediment -> Flow -> Splat
- Input: exported heightfield PNG
- Output: eroded heightfield + flow/curvature masks
- Export heightfield as 16-bit PNG/TIFF
- Evidence: `Saved/Audit/gaea_<preset>_<date>.png`

### Step 3: UE Landscape import
- Create new level or use protected test level
- Import heightfield as UE Landscape
- Apply material: `M_Master_Toon_Landscape_HeightBlend` from `Content/EnvSandbox/Materials/`
- Evidence: landscape appears in editor, matches heightfield dimensions

### Step 4: PCG placement from dressing plan
- Export dressing plan from `melodia_studio` as JSON
- Place props via PCG using existing `PCG_*` framework
- Target: 100-500 props first, validate placement and collision
- Evidence: prop count, no overlap, no floating props

### Step 5: Capture evidence
- Screenshot from approved capture level or new test level
- Save to `Saved/Audit/world_build_<preset>_<date>/`
- Record: heightfield SHA, prop count, render time

---

## Out of scope for today
- Full Gaea erosion graph polish
- Geometry-Nodes scatter at 10k+ density
- UE5 PCG final pipeline
- Oceanology plugin
- Protected maps: `L_WP_SakuraDream`, RenderTests sources

---

## Evidence checklist

| Step | Evidence | Location |
|---|---|---|
| Heightfield export | PNG file + dimensions | `Saved/Audit/heightfield_*.png` |
| Gaea output | PNG/TIFF + CLI log | `Saved/Audit/gaea_*.png` |
| UE landscape | Editor screenshot | `Saved/Audit/world_build_*/` |
| PCG props | JSON plan + count | `Saved/Audit/pcg_plan_*.json` |
| Final capture | Screenshot + metadata | `Saved/Audit/world_build_*_<date>/` |

---

## Files to create/modify

- `Saved/Audit/heightfield_<preset>_<date>.png`
- `Saved/Audit/gaea_<preset>_<date>.png`
- `Saved/Audit/world_build_<preset>_<date>/`
- `Content/MelodiaIntegration/ResonantWorld/OfflineWorldGen/<preset>_<date>/` (optional)
