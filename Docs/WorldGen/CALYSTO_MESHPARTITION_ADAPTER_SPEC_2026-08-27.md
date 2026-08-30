# Calysto → MeshPartition Adapter Spec — BS_GodFile UE5.8

**Date:** 2026-08-27  
**Status:** Spec only (no runtime proof)  
**Engine:** UE 5.8 — **MeshTerrain-only, NO ALandscape (P0 forbids Landscape)**  
**Related:** `Docs/WorldGen/PROCEDURAL_ENVIRONMENT_BUILD_PLAN_GAEA2UNREAL_OCEANOLOGY_2026-08-25.md` · `Content/Python/pcg_scale_world_pipeline.py` · `Tools/WorldGen/ingest_gaea2unreal_mesh_terrain_handoff.py`  
**Pack:** Calysto World 2.0 (ex Massive World) — $119.99 Fab · 70× 4K heightmap biomes · PCG+World Partition stamps · `PCGWorldPartitionBuilder` `IterativeCellSize 25600` · RVT automaterial

---

## 1. Goal

Reuse Calysto biomes as **`VISUAL_GRAPH_BINDINGS` only** — visual dressing inside the existing `pcg_scale_world_pipeline.py` contract — without breaking the MeshTerrain substrate.

- Calysto heightmap stamps + masks are **source art**, not terrain actors. They feed the existing Gaea-style handoff (`heightmap + masks + manifest → OBJ → MeshPartition`), never `ALandscape`.
- Calysto PCG graphs become **one-graph-per-hero-slot bindings** referenced by `hero_slots_for_chunk()` / `reusable_graph_binding()`, not cloned per chunk.
- Calysto's `LandscapeGrassType` / Landscape automaterial / VHFM path is **out of scope**; port materials to MeshTerrain RVT/triplanar MIs.
- World Partition cell size is single source of truth: `WP_CELL_SIZE_CM = 25600` everywhere.

Non-goal: importing Calysto demo maps as Landscape levels. Those remain reference only.

---

## 2. Architecture

```text
Calysto stamp library (70 biomes, 4K PNG16 height + masks)
        |  Fab content: /Game/Calysto/.../Stamps/{Biome}/{height,flow,slope,albedo,water,shore}
        v
calysto_export_to_handoff()  [Python adapter, offline]
        |  reads PNG16 + JSON definition (ScaleX/Y, Height, Unit=meters) — same contract as
        |  ingest_gaea2unreal_mesh_terrain_handoff.py  (GAEA_VERSION pin, sha256, metric check)
        +--> ingest_gaea2unreal_mesh_terrain_handoff.build_handoff() reuse
        |       -> {setupId}_MeshTerrain_{res}.obj + handoff_manifest.json
        v
MeshPartition bridge (UE 5.8)
        |  WP map at /Game/_PROJECT/ResonantWorld/Offline/{World}/  — NO Landscape actor
        |  triplanar Substrate MI (M_Master_Toon_Landscape_HeightBlend child)
        |  Oceanology actor separate (water only, not ground)
        v
PCGVolume tier  (vs Calysto PCGVolume — see §4)
        |  partitioned=true, GridSize 25600, bound to chunk origin via component transform
        |  Data Layer routing: DL_Musical_HeroGameplay (no-HLOD) / DL_Musical_StaticArchitecture /
        |                      DL_Musical_BiomeDressing  →  HLOD_Musical_Static for static only
        v
PIE / save-reopen / 3x3 seam / nav / capture gates (§6)
```

Two PCGVolume families compared:

| Family | Terrain role | WP | HLOD | Data Layer |
|--------|-------------|----|------|------------|
| **MeshPartition terrain** | solid ground + collision (MeshTerrain) | partitioned cells 25600 | not PCG | none (partition actor) |
| **Calysto-derived PCGVolume** | dressing only (trees/rocks/route markers) | `Partitioned=true`, `Generation Grid Size 25600` | hero_interactive excluded | `DL_Musical_HeroGameplay` etc |

Calysto's stock `PCGWorldPartitionBuilder` remains the builder, but its `IterativeCellSize` is synced to the project's `DA_PCGHeroBuilderSettings` (§5). Never spawn a `Landscape` to satisfy Calysto's automaterial.

---

## 3. Mapping — Calysto biome → BIOME_BANDS → hero_slot

Project canonical bands (`pcg_scale_world_pipeline.BIOME_BANDS`):

```text
("stone_court", "moss_rim", "blue_void", "crystal_meadow", "wind_shelf")
```

Hero slots (`VISUAL_GRAPH_BINDINGS` keys):

```text
ResonanceCathedral, ArpeggioBridge, BellTreeGarden, XylophoneTrail, CrystalHarpGrove
```

`biome_band_for_chunk()` and `hero_slots_for_chunk()` remain the authority; Calysto names are inputs to `calysto_biome_to_band()`, never new band values.

### Example table (tune per art direction; mapping is data, not code fork)

| Calysto biome (stamp folder) | Example stamp | → BIOME_BAND | hero_slot assignment (via `hero_slots_for_chunk` override or sparse cadence) | Notes |
|---|---|---|---|---|
| `Temperate_Forest` | `forest_height_4k_07` | `moss_rim` | `BellTreeGarden` | tree scattering via `PCG_Hero_BellTreeGarden` |
| `Alpine_Rock` | `alpine_height_4k_12` | `stone_court` | `ResonanceCathedral` | proof center (0,0) stays `stone_court` |
| `Crystal_Cave` | `crystal_height_4k_03` | `crystal_meadow` | `CrystalHarpGrove` (+ water graph) | triggers `WATER_INTERACTIVE_GRAPH_PATH` placements |
| `Desert_Canyon` | `canyon_height_4k_22` | `wind_shelf` | `ArpeggioBridge` | traversal landmark |
| `Void_Lake` | `lake_height_4k_01` | `blue_void` | `XylophoneTrail` | walkable instrument on shore mask |
| `Mixed / unmapped` | — | `stable_chunk_seed % len(BIOME_BANDS)` fallback | sparse cadence (token %23) | never invent a new band |

Rules:

- One Calysto biome → exactly one `BIOME_BAND`. Unlisted biomes use the deterministic fallback, not a new string.
- Hero slot density unchanged: proof triad at (0,0)/(1,0)/(-1,0)/(0,1)/(1,1) fixed; elsewhere `token % 23` sparse.
- `shared_border_signature` and `border_anchor_layout` unchanged — Calysto stamps do not own seam signatures.

---

## 4. PCG plumbing

### 4.1 Calysto PCGVolume settings (adapted)

| Property | Value | Reason |
|---|---|---|
| `Generation Grid Size` | `25600` (= `WP_CELL_SIZE_CM`) | 1 PCG cell = 1 WP cell; single source of truth |
| `Is Partitioned` | `true` | WP streaming owns lifetime |
| `Partitioned` builder | `PCGWorldPartitionBuilder` via `DA_PCGHeroBuilderSettings` | `IterativeCellSize 25600`, `bIterativeCellLoading true` |
| `bOneComponentAtATime` | `true` | matches `ensure_builder_settings_asset()` |
| HLOD | `hero_interactive` tier: `ExcludeFromHLOD=true`, `NoMerging=true` (`DL_Musical_HeroGameplay`); `classic_architecture`/`biome_dressing`: HLOD true → `HLOD_Musical_Static` | preserves `ChunkManifest.hlod_layer_assignments` |
| Seed | `stable_chunk_seed(world_seed, chunk_x, chunk_y)` | deterministic per chunk, not random |
| Origin | PCGVolume component transform = `chunk_origin_cm(chunk_x, chunk_y)` | `reusable_graph_binding` — no graph cloning |

### 4.2 Exclusion — PCGEx spline, not Landscape grass

Calysto's `LandscapeGrassType` exclusion is **not used**. Route/water exclusion uses the project's PCGEx contract:

- `PCGExSampleNearestSpline` → `PathDist` attribute → filter `PathDist < 700cm` (≈ seam_buffer + corridor) → cull or offset.
- Water mask from handoff (`water_mask`, `shore_mask`) → density mask on dressing graphs.
- Keep `hero_interactive` on CPU, `Partitioned=false` for that tier (see `scale_contract().pcg_generation_tiers`); dressing tiers may be GPU after profile.

### 4.3 RVT automaterial port

Calysto RVT automaterial targets Landscape layers. For MeshTerrain:

- Bake Calysto layer logic to **Substrate MI functions** driven by Gaea/Calysto slope/curvature/flow masks (world-aligned triplanar, not Landscape UVs).
- Use RVT **to mesh** (mesh RVT write) if needed, not Landscape RVT. Isolated MI per world; do not edit the shared master.

---

## 5. World Partition settings sync

Single asset: `DA_PCGHeroBuilderSettings` at `BUILDER_SETTINGS_PATH = /Game/EnvSandbox/PCG/Musical/Hero/DA_PCGHeroBuilderSettings`

```text
DA_PCGHeroBuilderSettings:
  bIterativeCellLoading = true
  IterativeCellSize     = 25600
  bOneComponentAtATime  = true
  bLoadEditorOnlyDataLayers = true
  bLoadActivatedRuntimeDataLayers = true
  Graphs = HERO_GRAPH_PATHS (+ Calysto-derived bindings appended via reusable_graph_binding)
  DataLayers = (DL_Musical_HeroGameplay, DL_Musical_StaticArchitecture, DL_Musical_BiomeDressing)
  HLOD = HLOD_Musical_Static (static tiers only)
```

Managed by `pcg_scale_world_pipeline.ensure_builder_settings_asset(unreal)` — Calysto sync must call it, not duplicate it. Validate with `validate_chunk_manifest` / `validate_grid` (border signature + anchor checks).

---

## 6. Python adapter pseudocode

```python
CALYSTO_BIOME_TO_BAND: dict[str, str] = {
    "Temperate_Forest": "moss_rim", "Alpine_Rock": "stone_court",
    "Crystal_Cave": "crystal_meadow", "Desert_Canyon": "wind_shelf",
    "Void_Lake": "blue_void",
}
BIOME_BANDS = ("stone_court","moss_rim","blue_void","crystal_meadow","wind_shelf")

def calysto_biome_to_band(biomeName: str) -> str:
    """Map Calysto stamp biome folder to canonical BIOME_BAND. Fallback is deterministic hash, never a new band."""
    band = CALYSTO_BIOME_TO_BAND.get(str(biomeName))
    if band in BIOME_BANDS:
        return band
    # deterministic fallback so unmapped biomes don't fork the contract
    h = int(hashlib.sha256(biomeName.encode()).hexdigest()[:8], 16)
    return BIOME_BANDS[h % len(BIOME_BANDS)]

def calysto_export_to_handoff(calystoExportDir: Path, outputRoot: Path, setupId: str) -> Path:
    """Convert one Calysto 4K stamp export to MeshTerrain handoff via the Gaea adapter contract."""
    heightmap = next(Path(calystoExportDir).glob("*height*.png"))  # 16-bit gray, non-interlaced
    definition = Path(calystoExportDir) / "definition.json"  # ScaleX/Y, Height, Unit=meters, Resolution
    # Reuse pinned adapter — validates Gaea 2.2.3.2 version, metric, resolution vs IHDR, sha256
    from Tools.WorldGen.ingest_gaea2unreal_mesh_terrain_handoff import build_handoff
    manifest = build_handoff(
        input_dir=Path(calystoExportDir), heightmap=heightmap,
        definition_path=definition, output_root=outputRoot,
        setup_id=setupId, gaea_version="2.2.3.2", target_resolution=None,
    )
    # annotate manifest with Calysto provenance (visual binding only)
    data = json.loads(Path(manifest).read_text())
    data["source"]["calysto_biome"] = calystoExportDir.name
    data["source"]["calysto_band"] = calysto_biome_to_band(calystoExportDir.name)
    data["ue"]["classic_landscape_used"] = False
    Path(manifest).write_text(json.dumps(data, indent=2), encoding="utf-8")
    return Path(manifest)

def sync_calypso_pcg_volumes(unreal, worldSeed: int, chunkCoords: list[tuple[int,int]]):
    """Ensure PCGVolumes per chunk reference reusable graphs, synced WP/HLOD/DataLayers."""
    from Content.Python.pcg_scale_world_pipeline import (
        WP_CELL_SIZE_CM, stable_chunk_seed, chunk_origin_cm,
        hero_slots_for_chunk, reusable_graph_binding, ensure_builder_settings_asset,
    )
    ensure_builder_settings_asset(unreal)  # syncs DA_PCGHeroBuilderSettings IterativeCellSize 25600
    for (cx, cy) in chunkCoords:
        origin = chunk_origin_cm(cx, cy)
        slots = hero_slots_for_chunk(worldSeed, cx, cy)  # Calysto biomes feed band/slot mapping above
        for slot in slots:
            binding = reusable_graph_binding(slot)  # {"graph": PCG_Hero_..., "profile": DA_Hero_...}
            vol = unreal.EditorAssetLibrary.load_asset(f"/Game/_PROJECT/ResonantWorld/PCGVolumes/PCGVolume_{cx}_{cy}_{slot}")
            # set partitioned, grid size, transform=origin, graph=binding["graph"], seed=stable_chunk_seed(...)
            vol.set_editor_property("IsPartitioned", True)
            # GenerationGridSize / bPartitioned names vary 5.6→5.8 — try aliases, report missing
            vol.set_editor_property("GenerationGridSize", WP_CELL_SIZE_CM)
```

Adapter lives at `Tools/WorldGen/calysto_meshpartition_adapter.py` (proposed). No Landscape actor created.

---

## 7. Validation checklist

| # | Check | Command / evidence | Pass |
|---|---|---|---|
| 1 | Handoff manifest | `handoff_manifest.json` has `schema melodia.gaea2unreal_mesh_terrain_handoff.v1`, `classic_landscape_used false`, sha256 per channel | file exists |
| 2 | MeshPartition | `Saved/Audit/meshpartition_report.json` — triangle count, bounds, material, saved map; no `ALandscape` in map | registry query OK, `bp_sweep` clean |
| 3 | Heatmap | Gaea/Calysto slope+flow → Substrate MI triplanar blend visible in editor viewport | screenshot with MI params |
| 4 | Nav | `UNavigationSystemV1` builds on MeshTerrain collision; PCG dressing has collision off or nav-excluded | `Build Navigation` no errors |
| 5 | 3×3 seam | `write_grid_report(radius=1)` then `validate_grid()` — `shared_border_signature` + `border_anchor_layout` match on all east/north seams | `errors == []` |
| 6 | Exclusion | `PCGExSampleNearestSpline PathDist 700cm` cull verified — no rocks/flowers on route spline or below water mask | PCG point count report |
| 7 | Data Layer | `DL_Musical_HeroGameplay` actors `exclude_from_hlod true`, `gameplay_data_layer` correct, HLOD only on static | `validate_chunk_manifest` + outliner |
| 8 | PIE | 1-chunk PIE and 3×3 streaming PIE — no Landscape actor, no ensures, water not duplicating collision | log + `Saved/Echo/state.txt` |
| 9 | Save/reopen | map survives save, close, reopen, PIE re-run | manifest re-hash matches |

---

## 8. Risks

| Risk | Impact | Mitigation |
|---|---|---|
| **5.6 vs 5.8 build** — Calysto 2.0 ships for 5.6; PCG API drifts (node names, `PCGWorldPartitionBuilder` props, `GenerationGridSize` alias) | graphs fail to load/cook | Test in **copy project** on 5.8 first; use `ensure_builder_settings_asset` alias probing; check Qwerty Discord + `pcg_scale_world_pipeline` as SSOT for prop names |
| **Landscape automaterial port** — Calysto RVT + `LandscapeGrassType` are Landscape-only | buying automaterial for nothing | Treat Calysto as **stamp/mask source**; port to MeshTerrain triplanar MIs + RVT-to-mesh; budget material rewrite days, not toggle |
| **Fab cache stale build** — launcher caches 5.5 build then "updates" to 5.6; Qwerty notes this explicitly | wrong engine binary, silent fail | After purchase, **clear Fab/Epic launcher cache** and install directly for 5.8 (no cross-version upgrade); record engine version in manifest |
| 5.8 PCGEx / World Partition churn | builder settings silently ignored | adapter reports `missing_expected_properties`; offline `validate_grid` gates promotion |

---

## 9. Rollout plan

1. **SakuraDream first** (isolated proof, dry, no Oceanology). One Calysto biome → one band → one hero slot → 1-chunk MeshPartition map → checklist §7.1–7.9 on that map only. Keep `Sakura Terrace` as name if it matches the shipped map; otherwise `SakuraDream` is the adapter's first consumer.
2. **Liquid Cathedral second** — reuse proven adapter + add Oceanology water + shore mask blend. Objective is the existing P0 A–H gate for the cathedral slice.
3. Do not fan out to `Cadence Crystal Ridge` / `Fugue Grotto` until SakuraDream 3×3 seam + PIE gates pass. No Landscape fallback allowed to "unblock" a gate.

---

*Spec file: `Docs/WorldGen/CALYSTO_MESHPARTITION_ADAPTER_SPEC_2026-08-27.md` — under 300 lines by contract.*
