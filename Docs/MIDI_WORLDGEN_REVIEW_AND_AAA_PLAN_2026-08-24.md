# MIDI World-Gen — Work Review and AAA Level Plan

**Date:** 2026-08-24
**Scope:** Melodia Studio MIDI sync, walkable terrain mapping, dressing and
magical systems, render verification.
**Baseline:** moved 4x during this work (`0de0e3c6` → `df404e84` → `c66c531f`);
other lanes committing live. Nothing here was staged or committed.

---

## 1. What was actually wrong

Every item below was found by reading code or measuring output, not inferred.

| ID | Defect | Evidence | Status |
|---|---|---|---|
| D1 | `STUDIO_ROOT` resolved to `Tools/Tools/MelodiaProceduralStudio` | one `..` too few in `studio_panel.py` | FIXED |
| D2 | `from midi_voxel_v3 import ...` with that dir never on `sys.path` | "Load MIDI" could never have worked | FIXED |
| D3 | Terrain mesh built with **no material**; `AuraColor` computed then discarded | scenes rendered as blank charcoal frame | FIXED |
| D4 | Camera at `(0,-4,2)` with **no rotation** on terrain spanning x 0..64 | pointed down −Z at empty space | FIXED |
| D5 | Lights sized for a 3-unit subject on a 64-unit terrain | 300–800 W at ±3 units | FIXED |
| D6 | v3 mapping is a **ribbon**: `Y = pitch % 12` can never exceed 12 | measured 64×11×3, aspect 5.8:1 | FIXED (v4) |
| D7 | Preset `surface_height_divisor` / `cave_height_divisor` ignored | `generate()` hardcodes `vel // 32`, `vel // 40` | **OPEN** |
| D8 | Melusina floated above terrain | placed at bbox top, not local column: **3.0 units** off | FIXED (v5) |
| D9 | Eye-level cameras sat below the surface | same bbox-vs-local-height error | FIXED (v5) |
| D10 | `chime_pillar` placed 0 props | no cell ever tagged `ridge` | FIXED |
| D11 | Dressing jitter pushed props over empty cells | 4 props off-grid | FIXED |
| D12 | `surface_height_at` used `round()` not `floor()` | coords at `*.5` resolved to wrong column | FIXED |
| D13 | Dressing budget exceeded by one per kind | `max(1, …)` overrode the cap; 15 > 12 | FIXED |

### Correction to an earlier claim

I stated `midi_voxel_v3.py` was missing from the repo. **That was wrong** — it
is at `Tools/midi_to_voxel/midi_voxel_v3.py`, and it works:

```
192 melody notes + 64 beat notes -> 346 voxels -> 2,768 verts / 1,540 faces
stone 19 | wood 112 | crystal 53 | gold 34 | void 128
```

The parser was never the problem. The presentation layer was.

### Vision hallucination — process note

One vision read of `full_bloom__eye_level.png` described "silver hair, a glowing
cyan scythe, mossy rocks." A second read of the **same file** reported "no
humanoid character present." Both cannot be true. Neither was used as evidence.

Placement claims in this document come from `verify_v5_placement.py`, which
measures scene units and frustum coordinates. **Do not accept vision output as
proof of geometry state.**

---

## 2. Measured results

### Terrain mapping: v3 → v4

| | footprint | aspect | height | walkable | connected |
|---|---|---|---|---|---|
| v3 (ribbon) | 64 × 11 | 5.80 | 3 | n/a | n/a |
| walkable_valley | 15 × 16 | 1.07 | 4 | 100% | 100% |
| walkable_highlands | 15 × 16 | 1.07 | 8 | 100% | 100% |
| walkable_plaza | 20 × 20 | 1.00 | 4 | 100% | 100% |
| walkable_canyon | 13 × 14 | 1.08 | 8 | 91.2% | 100% |

v4 changes the **mapping only**; `midi_voxel_v3.py` is untouched:

1. **Serpentine fold** — timeline wraps boustrophedon across a 2D plane.
2. **Real elevation** — full pitch, not pitch-class, drives height.
3. **Ground fill** — solid columns to bedrock; nothing to fall through.
4. **Slope limiting** — neighbour deltas clamped to `max_slope`.

### v5 placement verification

`verify_v5_placement.py`, terrain `walkable_highlands`, style `full_bloom`:

```
melusina  STANDING        gap to ground 0.086   (v4 floated by 3.0)
camera    ABOVE_SURFACE   1.7 above local ground
props     ON_SURFACE      max error 0 / mean 0.0  (57 props)
framing   IN_FRAME        23% width x 43% height, 16/16 corners in front
```

### Dressing and magic

| style | props | magic systems |
|---|---|---|
| bare | 0 | 0 |
| verdant | 35 | 2 |
| crystalline | 23 | 6 |
| cathedral | 34 | 3 |
| full_bloom | 57 | 9 |

Prop kinds are score-driven: `resonance_crystal` on peaks, `chime_pillar` on
ridges, `moss_cluster` in valleys, `songstone` on paths, `note_bloom` on slopes.
Magic systems: `aurora_veil` (volume), `motif_wisps` (particles),
`cadence_pool` (water), `harmonic_rings` (emissive geometry),
`ground_glow` (underlight).

### Test suite

```
python -B -m unittest discover -s Tools/BlenderAddons/melodia_studio/tests
Ran 42 tests -- OK (expected failures=1)   exit 0
```

The one expected failure is **D7**, documented in its docstring rather than
hidden: fixing it means editing the shared voxel tool other lanes may use.

### Render sets

| set | frames | location |
|---|---|---|
| v3 matrix | 30 | `Saved/Audit/midi_matrix/` + `matrix_ledger.json` |
| v4 walkable | 24 | `Saved/Audit/midi_walkable/` + `walkable_ledger.json` |
| v5 dressed | 20 | `Saved/Audit/midi_v5/` + `v5_ledger.json` |

(74 frames total, all on `G:`.)

---

## 3. Files

**New, offline-safe (no bpy):**
```
Tools/BlenderAddons/melodia_studio/midi_bridge.py
Tools/BlenderAddons/melodia_studio/walkable_world.py
Tools/BlenderAddons/melodia_studio/terrain_dressing.py
Tools/BlenderAddons/melodia_studio/tests/test_midi_bridge.py
Tools/BlenderAddons/melodia_studio/tests/test_terrain_dressing.py
Tools/MelodiaProceduralStudio/midi_presets.json
```

**New, Blender-side:**
```
Tools/MelodiaProceduralStudio/v5_build.py
Tools/MelodiaProceduralStudio/v5_dress.py
Tools/MelodiaProceduralStudio/render_v5_matrix.py
Tools/MelodiaProceduralStudio/render_midi_matrix.py
Tools/MelodiaProceduralStudio/render_walkable.py
Tools/MelodiaProceduralStudio/verify_v5_placement.py
Tools/MelodiaProceduralStudio/aaa_scene_builder.py
Tools/MelodiaProceduralStudio/build_melusina_asset.py
```

**Rewritten:** `melodia_studio/studio_panel.py`, `melodia_studio/__init__.py`

**Untouched:** `Tools/midi_to_voxel/*`, all `GeneratedScenes/*/scene.blend`
(SHA-verified identical to `scene_PRE_AAA.blend` backups), every `.uasset`.

---

## 4. Honest state of the visuals

The pipeline is **correct** but the images are **not yet portfolio-grade**.

A blunt vision rating of a v3 frame was *2/10 — "terrain fills ~10–15% of
vertical height, lighting not dramatic, colors not glowing, blocks look
random."* v4 fixed the silhouette and v5 added dressing, but the core look is
still **untextured voxel cubes with flat EEVEE shading**.

What is genuinely proven:
- Music → walkable geometry, measured traversable.
- Velocity → colour, sampled by a real shader.
- Character and camera correctly seated on terrain, verified numerically.
- Score-driven prop and FX placement, deterministic and budgeted.

What is **not** proven:
- That any of this looks AAA. It does not yet.
- Anything in-engine. Nothing has entered UE5.

---

## 5. Forward plan — AAA MIDI game levels

### Phase 1 — Material and lighting quality (biggest visual payoff)
1. **PBR terrain materials** per block tier, replacing flat Principled: real
   albedo/roughness/normal, triplanar so voxels need no UV unwrap.
2. **Compositor pass** — bloom/glare on emissive props. Emission currently has
   nothing blooming it, which is why crystals read matte.
3. **Volumetric fog** with light shafts; `aurora_veil` exists but is thin.
4. **Contact shadows + AO** to seat props into the ground visually.
5. Gate: side-by-side against a reference frame, owner judgement.

### Phase 2 — Gaea landscape integration
`Gaea.Build.exe` is installed (`C:\Program Files\QuadSpinner\Gaea\`) and is
headless-capable; Gaea 2 also present.
1. Export the v4 heightfield as a 16-bit heightmap (the fold makes this
   possible — a 64×11 ribbon was not erodible).
2. Gaea graph: erosion, sediment, flow maps, texture splat.
3. Re-import as displaced landscape; keep voxels as hero silhouette or discard.
4. Gate: erosion visibly follows the melody's ridgelines.

### Phase 3 — Scattering at density
1. Geometry-Nodes scatter driven by the tag map (peak/ridge/valley/path/slope),
   replacing per-object instancing — current cap is 57 props.
2. Density masks from Gaea flow/curvature.
3. LOD + instancing budget for UE.
4. Gate: 10k+ instances holding interactive frame rate.

### Phase 4 — UE5 level pipeline
1. Heightmap → UE Landscape; splat maps → Landscape layers.
2. Props → PCG (project already uses `PCG_*` assets) rather than baked FBX.
3. Playable collision proven with a pawn, not inferred from `walkable_fraction`.
4. Gate: **walk the level in PIE**, real input, per the project's runtime
   evidence standard — a probe is not play evidence.

### Phase 5 — Musical gameplay
1. Beat-synced level events (`harmonic_rings` pulsing on the beat).
2. Music-as-key traversal: a phrase opens a route (the world puzzle in
   `AGENTS.md` is **not yet built**).
3. Wire to `MelodiaNarrativeSubsystem` via the existing typed bridge — no new
   authority.

### Ordering constraint
Phase 1 is cheap and highest-visible-return. Phase 2 requires Phase 1's
material work to be meaningful. **Phase 4 requires the change freeze to lift**
(`.umap`/`.uasset` writes) and must respect the convergence plan's authority
rules.

---

## 6. Open decisions for the owner

1. **D7** — fix the ignored height divisors? Requires editing
   `Tools/midi_to_voxel/midi_voxel_v3.py`, which other lanes may consume.
2. **Freeze** — the convergence plan says "Never run Blender." Blender was run
   here on explicit owner instruction. Confirm whether that stands for Phase 1.
3. **Scope** — polish these 3 MIDI scenes, or batch-apply to all 37 generated
   scenes?
4. **Gaea version** — Gaea 1 (`Gaea.Build.exe`, known CLI) or Gaea 2
   (`Gaea.BuildManager.exe`, CLI contract unverified)?
5. **`abyss_caves`** — keep as a duplicate preset until D7 is fixed, or remove?
