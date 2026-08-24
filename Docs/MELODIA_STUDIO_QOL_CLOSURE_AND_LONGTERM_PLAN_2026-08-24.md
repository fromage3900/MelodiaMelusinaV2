# Melodia Studio — QOL Closure & Long-Term Plan

**Date:** 2026-08-24
**Status:** `SOURCE_BUILT_LIVE_PENDING`
**Author:** Project tooling audit
**Scope:** Contained, post-P0 environment tooling and a long-term UE5 integration plan. This document does not authorize shipping-path world generation, UE asset writes, or a new gameplay authority.

The original version overstated local process state as durable proof. This revision keeps offline and Blender/runtime evidence separate. Machine-local addon deployment and scheduler state must be revalidated on the machine that will run them.

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

### 1.5 Added generated-report readout
The panel displays values parsed from the generation report. Prop and magic values are deterministic plan counts; they are not proof that Blender instances exist in the scene. Dedicated walkability, connected-region, and live-scene fields remain open UI work.

### 1.6 Removed stale `_expand_worldgen.py` / `_assemble_ue_manifest.py`
These were deleted by another lane mid-session. References removed.

---

## 2. Evidence status

| Component | Repository evidence | Current proof tier |
|---|---|---|
| `melodia_studio` addon | `Tools/BlenderAddons/melodia_studio/` | `VERIFIED_OFFLINE` for 53 Python tests; Blender UI revalidation pending |
| `resonant_world_studio` addon | `Tools/BlenderAddons/resonant_world_studio/` | `SOURCE_BUILT_LIVE_PENDING` |
| `surreal_arch` GN builders | `deploy/surreal_arch/melodia_gn/` | `SOURCE_BUILT_LIVE_PENDING`; the prior 25/25 report used a weak oracle and is retired |
| MIDI World-Gen Daemon | `Tools/midi_worldgen_daemon.py` | `VERIFIED_OFFLINE` for its verdict contracts; headless Blender run pending |
| Render wrapper | `Tools/_daemon_render_wrapper.py` | `SOURCE_BUILT_LIVE_PENDING` |
| Portfolio banner | `Tools/gen_resonant_banner.py` | `VERIFIED_OFFLINE` only when its generated SVG/JSON command succeeds |

**Repeatable offline result:** 53 tests total pass with one expected failure: 21 MIDI bridge tests plus 32 terrain-dressing tests. These counts are subsets of the same 53-test run, not 85 tests. The Blender GN and render commands remain live-evidence gates.

---

## 3. Optional daemon architecture

### 3.1 What we built

```
┌─────────────────────────────────────────────────────────────────┐
│  Optional external scheduler (machine-local, not repo proof)    │
│  Must capture the process exit code and prevent overlap         │
│                                                                 │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │  midi_worldgen_daemon.py  (Python coordinator)          │   │
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
│  - <repo>\Saved\Audit\...                                   │
│    midi_worldgen_daemon\ledger.json                             │
│    midi_worldgen_daemon\renders\*.png                           │
│    midi_worldgen_daemon\banner\*.svg                           │
└─────────────────────────────────────────────────────────────────┘
```

### 3.2 Workflow capabilities

| Skill | Application | Status |
|---|---|---|
| `systematic-debugging` | Diagnose any terrain/render defect before fixing | Active |
| `plan` | Document any multi-step build before executing | Used this session |
| `test-driven-development` | Write failing tests before building any new feature | 53 offline addon tests plus fail-closed oracle tests |
| `melodia-creative-tools` | Core Blender addon + world-gen patterns | Workflow guidance; not a runtime dependency |
| `blender-addon-development` | Junction-based deployment, bl_info conventions | Machine-local deployment must be revalidated |
| `portfolio-professionalization` | Honest, numbers-first public copy | Banner uses real metrics |
| external scheduler | Optionally schedule a recurring task | Machine-local setup; not a repository invariant |
| `delegate_task` | Parallelize independent work | Could parallelize renders |

### 3.3 Skill-triggered lanes still available

| Lane | Trigger | What it does |
|---|---|---|
| **AAA GN builders** | "Build fantasy architecture in Blender" | 25 registered builders; geometry-quality revalidation pending |
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
| — | A prior local observation found a stale AppData copy | Medium | Revalidate deployment on the execution machine |
| — | Optional scheduler notification policy is undefined | Low | Decide only if scheduling is re-enabled |
| — | v18 scene has 23M tris dominated by 3 ultra-high-poly meshes | Medium | LOD pass? |
| — | `A_MannFix_Walk.uasset` was bundled into a Studio tooling commit | High | Keep/delete decision and UE asset proof; do not call it Studio verification |

---

## 6. Verification Checklist

```
1  git log --oneline -3 && git status --porcelain | wc -l
2  python -B -m unittest discover -s Tools/BlenderAddons/melodia_studio/tests
      expect: 53 tests total, OK (expected failures=1)
3  python -B -m unittest discover -s Tools/BlenderAddons/melodia_studio/tests -p test_terrain_dressing.py
      expect: 32 tests, OK
4  python -B Tools/BlenderAddons/melodia_studio/walkable_world.py
      expect: 5 presets, all aspect < 1.1, walk >= 0.91
5  blender --background --factory-startup --python Tools/verify_musical_gn.py
      expect: nonzero exit for empty geometry, NaNs, duplicate inputs, or zero-area faces
6  blender --background --factory-startup --python Tools/test_resonant_world_studio.py
      expect: PASS plus a fresh render path, byte count, and SHA-256
7  python -B Tools/midi_worldgen_daemon.py
      expect: ignored Saved/Audit renders + atomic ledger, hashes, 0 errors, exit 0
8  If scheduled: verify the external scheduler separately and record its current evidence
```

---

## 7. Honest State

**What works:**
- Music → walkable terrain, measured traversable (100% in most presets)
- Velocity → colour, sampled by a real shader
- Character/camera seating has source assertions; fresh Blender proof is pending
- Score-driven prop + FX plans are deterministic and budgeted; Blender instancing remains live-pending
- 25 GN builders are registered; the strengthened verifier must be rerun in Blender
- The daemon now fails closed, serializes overlapping runs, and writes ignored audit output by default

**What doesn't:**
- Images are blocky voxels, not AAA landscapes
- No in-engine proof (PIE forbidden)
- 37 GeneratedScenes share broken presentation layers
- 19 of 20 MIDI files are too short for meaningful terrain variety

**What the daemon actually produces:** portfolio evidence (PNG + metrics ledger), not playable levels. Closing that gap requires the freeze lifting and Phase C.

## 8. P0 containment

This tooling is post-P0 and cannot close gameplay, save/load, NPC, quest, or encounter gates. It must not run automatically on the shipping branch while the convergence freeze is active. Geometry or render artifacts are presentation evidence only; they do not prove UE runtime behavior. P0 remains owned by QuillScript, the Narrative boundary, the typed JRPG bridge, and stock JRPG combat/save authorities.
