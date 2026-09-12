# Sea Above — PCG Heatmap Dress Plan (2026-09-03)

**Goal tonight: dress LV_SeaAbove_Prototype as a final playable map using real
terrain heatmaps + the gameplay path, not a bounding-box scatter.**

## Ground truth (sampled live 2026-09-03, editor on :9316)

| Layer | Value |
|---|---|
| Landscape bounds | ±250,000 uu (500 km canvas) |
| Height range | -54,902 .. +69,586 uu (124.5k relief) |
| Sea surface (play) | Z ≈ 13,455 (OceanologyManager 13,350 + water 105) |
| Submerged cells | 43.2% (691/1600) |
| Above-sea cells | 56.8% (909/1600) |
| Mean slope | 17.3° · >30° = 15.3% · >45° = 2.8% |
| Heatmap file | `Saved/Audit/sea_above_terrain_heatmap.json` (1600 pts) |
| Layers npz | `Saved/Audit/sea_above_layers.npz` (Z, SLOPE, ASPECT, COAST) |

The old `singing_water_veil_pcg.v1.json` was generated against a **fake flat
landscape** (stand-in `landscape_height_cm` = 13405 + small Chladni swell). Its
102 points at ±150 km ignore the real relief and the real loop. Keep its zone
language (SheetVeil/SingingFall/HearthPool/TideSeam + Chladni modes), re-ground
it on the sampled heightfield.

## The gameplay loop (anchors measured live)

```
PlayerStart (0,0,13175)
  → ArrivalTrigger (-145,470,10202)
  → QuillTrigger (-910,500,13145)
  → [MusicKey corridor — 24 PCGHeroMusicNode in 2 tiers: 12 @Z -45.3k, 12 @Z -14.6k]
  → StarskiffDock (-5099,5821,6270) / Starskiff MK2 (-800,1200,10535)
```

Path-falloff PCGs already authored: EntryToQuill, QuillToMusicKey,
MusicKeyToStarskiffDock. Cathedral + Colonnade PCGs live at Z -29k/-15.7k
(drowned strata). Palace kitbash (55 SMA) sits on the sea surface at Z 13455
(above-sea palace, floats on water — by design, not a defect).

## World reading (fiction-locked)

- The sea at 13,455 is the **walk/play surface** (palace, skiff, quill).
- Beneath it: a **drowned mountain sea** — canyon floors to -54k, islands
  piercing to +69k (909 cells above water = archipelago).
- The 24 music nodes are the drowned cathedral's two tiers — they are the
  vertical mystery under the player's feet.
- Pink flag: PlayerStart stands at Z 13,175 over terrain -8,073. Acceptable
  only if the play surface is the water sheet; verify in PIE. **If the player
  falls through water → the canyon floor is the failsafe, so never dress the
  sea-floor directly under the spawn as walkable land.**

## PCG heatmap approach (this is the update)

Five heatmap layers sampled from the real heightfield, each mapped to a
placement authority:

| Heatmap | Source | Drives |
|---|---|---|
| H1 Depth band | Z vs 13455 | Zone selection (above-sea / submerged / abyss) |
| H2 Slope | gradient | Rock piles & coral on steep; calm pools on flats |
| H3 Coast proximity | signed distance to Z=13455 | TideSeam ring, foam builders, shore flora |
| H4 Path falloff | distance to loop polyline (PlayerStart→Quill→MusicKey→Dock) | Density multiplier — dense near path, sparse far |
| H5 Resonance | Chladni mode field (existing veil contract) | Which veil builder + chladni_val per point |

**Density rule:** `density = base_zone_density × path_falloff × slope_gate`.
Path falloff is a 3-segment polyline with 1.0 inside 5k uu, decaying to 0.15
beyond 60k uu. This keeps the dressed density where the player actually walks,
and leaves the far archipelago as vista, not clutter.

## Zone → mesh mapping (real inventory, verified on disk)

| Zone | Condition | Builders (real assets) | MI |
|---|---|---|---|
| PalaceCourt (above sea, near path) | Z ≥ 13455, pathF ≥ 0.5, slope < 25° | SM_ATL_Palace_* (already placed 55) → **do not duplicate; only ADD companions: benches/trees at gaps** | existing |
| TideSeam (intertidal ring) | \|Z-13455\| < 3000, near coast | SM_RockChunk_L/M, SM_Coral_ReefCluster, SM_Flora_Reed | MI_SeaAbove_WetRock / CoralSkin |
| ReefGarden (submerged slope) | 0 < Z < 13455, slope < 40° | SM_Coral_Brain/Fan/Staghorn/Table/TubeSponges, SM_Clutter_Starfish/SpiralShell/PebbleSet, SM_Kelp_Mid/Tall | MI_SeaAbove_CoralSkin, MI_SeaAbove_Kelp |
| AbyssFloor (deep, far path) | Z < 0, slope < 40° | SM_RockChunk_L, SM_Clutter_SeaWeed, SM_DrownedOrgan (sparse) | MI_SeaAbove_Sand / WetRock |
| CathedralTier (music-node strata) | near node tiers Z≈-45k / -14.6k | JELLY_Cathedral_* parts + Jelly_Cathedral_01 BP (only 1 placed → add halo) | MI_Jelly_Bell/Arms |
| VeilWater (sea surface dressing) | Z ≈ 13455 ± 200, pathF high | **MEL_water_veil_* meshes DO NOT EXIST** → replace with SM_Flora_Chime + Niagara Drops (notes) or omit meshes; keep Chladni mode field for textures/MPC only | MI_SeaAbove_SurfaceOcean |

## What gets built/placed tonight

1. `Tools/PCG/build_sea_above_heatmap_dress.py` — offline generator, consumes
   `Saved/Audit/sea_above_layers.npz` + anchors, emits
   `specs/water_veil/sea_above_heatmap_dress.v1.json` (~160-240 height-aware
   points: TideSeam ~60, ReefGarden ~80, Abyss ~40, Cathedral halo ~24, PalAcc ~12)
2. Editor lane (Monolith, real line-trace) applies each point: raycast Z, snap
   clearance, assign MI. **No floating pieces** (BS_GodFile #2).
3. Verify: counts per zone, all placements within landscape bounds, Z snapped
   (|placed_Z - raycast_Z| < clearance), no duplicates of palace kit.

## Anti-duplication / contracts

- Extends PRESENT: PCG + toolkit, Oceanology water, existing veil zone language.
- No new landscape (CanonicalLandscape — labelled "Landscape" in the level; the
  only one, preserved).
- No new material masters — reuse MI_SeaAbove_* family (21 MIs verified).
- Music nodes untouched (24, 2 tiers, deliberate); only a Jelly halo added.
- Single writer: this dresses static mesh actors via Monolith editor lane only;
  no PCG graph mutation from Python (PCG spawner props unreadable — skill
  finding).
- Old veil plan (`singing_water_veil_pcg.v1.json`) stays as historical artifact;
  the new manifest supersedes it. Its textures/MIs remain valid.

## Evidence

- `Saved/Audit/sea_above_terrain_heatmap.json` + `sea_above_layers.npz` (sampled).
- `Saved/Audit/sea_above_dress_report.json` (after apply: counts, Z deltas).
- gate row: `sea_above_dressed_map` in `Saved/gate_ledger.json` when verified.