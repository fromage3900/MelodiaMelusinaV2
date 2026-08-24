# Melodia Studio — QOL Closure & Long-Term Plan

**Date:** 2026-08-24 (final)
**Author:** Hermes Agent (C-authority per AGENTS.md)
**Scope:** Close all loose ends. Maximize Hermes skills as an environment-building daemon. Plan UE5 integration for long-term use.

---

## 1. QOL Pass — What Got Fixed

### 1.1 Dressing styles drift (resolved)
`_dressing_items()` in `studio_panel.py` listed 15 styles that don't exist in `terrain_dressing.py`. The dropdown showed 15 names, selecting any after "cathedral" silently fell back to `bare` because `plan_dressing()` got an unknown key and returned `[]`.

**Fix:** `_dressing_items()` now imports `terrain_dressing` live and reads `DRESSING_STYLES`. Single source of truth. Fallback to a minimal list if the import fails offline.

### 1.2 `dress_terrain` relative import (resolved)
`midi_bridge.dress_terrain` did `from . import terrain_dressing` — fails with `ImportError: attempted relative import with no known parent package` when called from a test runner or daemon that doesn't load melodia_studio as a package.

**Fix:** `try/except ImportError` with `importlib.util.spec_from_file_location` fallback to the absolute path in `walkable_tool_dir()`.

### 1.3 Added `STUDIO_OT_render_proof` operator
Renders the current `Terrain` mesh with camera/lights already placed. One click → `Saved/Audit/melodia_studio_render.png`.

### 1.4 Added `STUDIO_OT_batch_render` operator
Calls `Tools/midi_worldgen_daemon.py` as a subprocess. Runs the full scan → generate → render → ledger pipeline for all MIDI × all presets.

### 1.5 Added measured-readout grid
Panel now shows walkable fraction, connected-region fraction, height span, and prop count from the actual heightfield metrics — not aesthetic guesses.

### 1.6 Removed stale `_expand_worldgen.py` / `_assemble_ue_manifest.py`
These were deleted by another lane mid-session. References removed.

---

## 2. Live Status (verified)

| Component | Repo path | AppLive path | Live? |
|---|---|---|---|
| `melodia_studio` addon | `Tools/BlenderAddons/melodia_studio/` | `%APPDATA%\Blender Foundation\Blender\5.2\scripts\addons\melodia_studio\` | YES |
| `resonant_world_studio` addon | `Tools/BlenderAddons/resonant_world_studio/` | junction → repo | YES |
| `surreal_arch` GN builders | `deploy/surreal_arch/melodia_gn/` | `%APPDATA%\Blender Foundation\Blender\5.2\scripts\addons\surreal_arch\melodia_gn\` | YES |
| MIDI World-Gen Daemon | `Tools/midi_worldgen_daemon.py` | N/A (headless) | Cron `9b3c980831ce` every 2h |
| Render wrapper | `Tools/_daemon_render_wrapper.py` | N/A | Called by daemon |
| Portfolio banner | `Tools/gen_resonant_banner.py` | N/A | Called by daemon |

**Verification:** 85 unit tests pass (53 bridge + 32 dressing). All 25 GN builders verified in Blender 5.2.

---

## 3. Hermes-as-Daemon Architecture

### 3.1 What we built

```
┌─────────────────────────────────────────────────────────────────┐
│  Hermes Cron (every 2h)                                         │
│  Job 9b3c980831ce: "Run MIDI World-Gen Daemon"                 │
│                                                                 │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │  midi_worldgen_daemon.py  (pure Python, no GUI)         │   │
│  │  1. Scan MIDI directories                               │   │
│  │  2. For each (MIDI, preset):                           │   │
│  │     a. Build heightfield → OBJ                          │   │
│  │     b. Plan dressing + magic                            │   │
│  │     c. Write job JSON                                   │   │
│  │     d. Spawn: blender --background --python wrapper     │   │
│  │  3. Append to ledger                                    │   │
│  │  4. Regenerate portfolio banner                         │   │
│  └─────────────────────────────────────────────────────────┘   │
│                           │                                     │
│                           ▼                                     │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │  _daemon_render_wrapper.py  (runs INSIDE Blender)       │   │
│  │  1. Read job JSON                                       │   │
│  │  2. Import OBJ → terrain mesh                           │   │
│  │  3. AuraColor material                                  │   │
│  │  4. Instance dressing props                             │   │
│  │  5. World + lights + camera                             │   │
│  │  6. Render PNG                                          │   │
│  └─────────────────────────────────────────────────────────┘   │
│                                                                 │
│  Outputs:                                                       │
│  - G:\EnvironmentPortfolio\BS_GodFile\Saved\Audit\...           │
│    midi_worldgen_daemon\ledger.json                             │
│    midi_worldgen_daemon\renders\*.png                           │
│    midi_worldgen_daemon\banner.svg                              │
└─────────────────────────────────────────────────────────────────┘
```

### 3.2 What Hermes skills can still do

| Skill | Application | Status |
|---|---|---|
| `systematic-debugging` | Diagnose any terrain/render defect before fixing | Active |
| `plan` | Document any multi-step build before executing | Used this session |
| `test-driven-development` | Write failing tests before building any new feature | 85 tests guard the pipeline |
| `melodia-creative-tools` | Core Blender addon + world-gen patterns | Loaded on every cron fire |
| `blender-addon-development` | Junction-based deployment, bl_info conventions | All 3 addons deployed |
| `portfolio-professionalization` | Honest, numbers-first public copy | Banner uses real metrics |
| `cronjob` | Schedule any recurring task | Daemon runs every 2h |
| `delegate_task` | Parallelize independent work | Could parallelize renders |

### 3.3 Skill-triggered lanes still available

| Lane | Trigger | What it does |
|---|---|---|
| **AAA GN builders** | "Build fantasy architecture in Blender" | 25 working GN groups, 3 new bells added |
| **TouchDesigner lookdev** | "Create audiovisual sanctuary" | Bounded, deterministic, MIDI-reactive |
| **Offline worldgen** | "Research packet + deterministic JSON" | District grammar, GN handoff schemas |
| **Portfolio site** | "Professionalize my repo surfaces" | Honest copy, anti-hype guardrails |

---

## 4. Long-Term Plan — UE5 Integration

**Constraint:** The convergence plan currently forbids `.umap`/`.uasset` writes and "Never run Unreal, Monolith, PIE." This plan assumes that freeze lifts for Phase 4.

### Phase A — Export Pipeline (freeze can stay)
1. Heightfield → 16-bit PNG/TIFF heightmap (Gaea-compatible)
2. Splat maps from `classify_cells()` tags (peak/ridge/valley/path/slope)
3. Prop manifests (position, rotation, scale, kit ID) as JSON
4. PCG-ready CSVs for UE5.3+ PCG graph consumption
5. Output: `Content/GeneratedScenes/<name>/export/` with all assets

### Phase B — Gaea Integration (headless, no freeze conflict)
1. `Gaea.Build.exe` CLI verification (known CLI, installed)
2. Heightmap → Gaea graph: erosion, sediment, flow, curvature
3. Re-import displaced landscape
4. Keep voxels as hero silhouette or discard
5. Gate: erosion visibly follows the melody's ridgelines

### Phase C — UE5 Landscape (requires freeze lift)
1. Heightmap → `ULandscape` via `LandscapeImportHelper`
2. Splat maps → `ULandscapeLayerInfoObject` + weight-blended materials
3. Props → `PCGComponent` (project already uses `PCG_*` assets)
4. Collision: simple per-poly for hero meshes, landscape heightfield for ground
5. Gate: **walk the level in PIE with real input**

### Phase D — Real-Time Musical Reactivity (future)
1. `ULandscapeSubsystem` reads MIDI tempo/pitch via the existing typed bridge
2. Material parameter collections driven by beat phase
3. `UMelodiaNarrativeSubsystem` world-state boundary respected
4. No new gameplay authority — JRPG owns combat/save

---

## 5. Loose Ends — What's Still Open

| ID | Issue | Severity | Owner decision |
|---|---|---|---|
| D7 | Preset height divisors ignored (`vel // 32` hardcoded) | Medium | Fix `midi_voxel_v3.generate()`? |
| D14 | 20 v5 renders need visual validation | Low | Owner eyes |
| D16 | 37 GeneratedScenes carry same broken material/camera/light defects | Medium | Batch-fix all 37? |
| D17 | Only 1 MIDI has real substance (192 notes); 19 are 1-12 note jingles | High | Source more MIDI? |
| — | `MEL_music_piano_roll` evaluates to empty mesh in headless | Low | Debug offline |
| — | `surreal_arch` in AppData is a stale copy, not a junction | Medium | Other lanes overwrite? |
| — | No notification channel on the cron job | Low | Wire Telegram/Discord? |
| — | v18 scene has 23M tris dominated by 3 ultra-high-poly meshes | Medium | LOD pass? |

---

## 6. Verification Checklist

```
1  git log --oneline -3 && git status --porcelain | wc -l
2  python -B -m unittest discover -s Tools/BlenderAddons/melodia_studio/tests
      expect: 53 tests, OK (expected failures=1)
3  python -B -m unittest discover -s Tools/BlenderAddons/melodia_studio/tests -p test_terrain_dressing.py
      expect: 32 tests, OK
4  python -B Tools/BlenderAddons/melodia_studio/walkable_world.py
      expect: 5 presets, all aspect < 1.1, walk >= 0.91
5  blender --background --factory-startup --python Tools/verify_musical_gn.py
      expect: 25/25 builders OK
6  blender --background --factory-startup --python Tools/test_resonant_world_studio.py
      expect: PASS (STANDING/ABOVE_SURFACE/ON_SURFACE/IN_FRAME)
7  python -B Tools/midi_worldgen_daemon.py
      expect: renders + ledger, 0 errors
8  cronjob list → midi-worldgen-daemon enabled, every 2h
```

---

## 7. Honest State

**What works:**
- Music → walkable terrain, measured traversable (100% in most presets)
- Velocity → colour, sampled by a real shader
- Character + camera correctly seated on terrain (numerically verified)
- Score-driven prop + FX placement, deterministic and budgeted
- 25 GN builders, all render-proofed
- Automated daemon scanning every 2h, ledger growing

**What doesn't:**
- Images are blocky voxels, not AAA landscapes
- No in-engine proof (PIE forbidden)
- 37 GeneratedScenes share broken presentation layers
- 19 of 20 MIDI files are too short for meaningful terrain variety

**What the daemon actually produces:** portfolio evidence (PNG + metrics ledger), not playable levels. Closing that gap requires the freeze lifting and Phase C.
