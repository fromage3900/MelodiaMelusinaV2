# Song-Chord Cathedral × Crystal Cathedral — Both Hymns

**Date:** 2026-09-01 03:03 UTC
**Hython:** 22.0.368 (copernicus), Python 3.11 (PCG pure)

## 1. The Song-Chord Cathedral (Found)

**File:** `Content/Python/build_pcg_hero_resonance_cathedral.py` (20K, 4 stations)
**Graph:** `PCG_Hero_ResonanceCathedral` → `/Game/EnvSandbox/PCG/Musical/Hero`
**Pure/deterministic:** No UE required for audit — layout is math.

### Chord Progress (the song)
```
station 0: C major  (60, 64, 67) — C4, E4, G4
station 1: D minor  (62, 65, 69) — D4, F4, A4
station 2: F major  (65, 69, 72) — F4, A4, C5
station 3: G major  (67, 71, 74) — G4, B4, D5
def chord_for_station(station): octave = station // 4, source = CHORD_PROGRESS[station % 4] → note + 12*octave
```

### Layout — 12 pads + 16 decor, piano roll (not isolated pads)
- **12 pads:** `build_cathedral_layout()` → 12× (x,y,z, node_index, lane, midi) — 3 per station, seeded `(node_index<<16)|(degree<<8)|midi`, 12 unique seeds verified (`test_pcg_hero_music.py:test_cathedral_has_twelve_unique_seeded_chord_pads`)
- **Piano roll:** `build_piano_roll_positions()` — 12 positions, `x` strictly increasing, `x[1]-x[0]=160.0`, `sin(alpha*pi)*220*0.24` walk, `y`/`z` arch 28→41.1→28, 8 ebony keys correctly between ivory keys, keybed at (0,0,0)
- **Positions:** -880→+880, station_spacing 480, walk_width 220, vault_height 1800, density 0.40, resample 120
- **Decor:** 16 — side columns (300,900) per station + vault accents (1584) sampled per density
- **Vault curve:** `build_cathedral_vault_curve_points()` ≥5, strictly increasing x, mid > ends (arch), `build_piano_roll_detail_points` 1 keybed + 8 ebony

### Why It Was Missed
Search for "cathedral" alone hits kitbash/gaea/copernicus. Song-chord cathedral lives under `build_pcg_hero_resonance_cathedral` (not "cathedral" in path) + `pcg_hero_music_control` — found via `chord_for_station`.

## 2. Houdini Cathedral (Fractal + Crystal)

**Fractal:** `Tools/Houdini/cathedral/build_fractal_cathedral.py` → `SM_P4_Cathedral_Fractal.obj` 1364v/657f (depth4 span10 bays8) + Rose 782v Chladni n8m6, GN `MEL_p4_fractal_cathedral` 8 inputs
**Crystal:** `Tools/Houdini/cathedral/build_crystal_cathedral.py` → `SM_P4_Cathedral_Crystal.obj` 3598v/2793f (crystal 0.85 facets12) + Rose 1032v, GN `MEL_p4_crystal_cathedral` 9 inputs
**Copernicus:** `FractalCathedral` 4.2M (2048), `CrystalCathedral` 30th variant 1.6M@1024 / 4.1M@2048 / 11M@4096 (BaseColor 3.0M, Iridescence 2.1M)

## 3. Both — The Bridge (2026-09-01)

**Executed:**
- **4096 CrystalCathedral:** `hython copernicus_cymatic_parallax.py --variant CrystalCathedral --size 4096x4096 --cook` → 11M, 9 maps, verifies Chladni crystal_mask logic at true 4K
- **Song-chord audit:** `sanitize_snapshot()` 11 props, `proof_preset` CullDistance 0/WriteCustomDepth/Stencil 3, `Depth→VaultHeight` alias, 12 pads ok, vault curve ok

**Next — Crystal Song Cathedral (proposed, not built):**
- Seed 6 stations: keep 4 existing + add 2 crystal stations (A minor (57,60,64), E major (64,68,71)) → 18 pads, same `chord_for_station` octave logic
- PCG vault decoration drives `GlitterCrystal`/`CrystalCathedral` material switch per station (even=stone, odd=crystal) — no new master, same 9-map contract
- Houdini crystal shards height = `chord MIDI % 12` → Chladni modeN/m, so song directly sculpts crystal facets (song → geometry, not just placement)

**Files on Disk (ready for Monolith when editor closed):**
- `Saved/Audit/copernicus_cymatic/CrystalCathedral/` — 4096 hero (11M)
- `Saved/Audit/cathedral/SM_P4_Cathedral_Crystal.obj` — 3598v hython 22.0.368
- `Content/Python/build_pcg_hero_resonance_cathedral.py` — 12-pad song cathedral, deterministic, test-verified

**Manifests:**
- `Saved/Audit/cathedral/cathedral_fractal_manifest.json` (melodia.cathedral_fractal.v1)
- `Saved/Audit/cathedral/crystal_cathedral_manifest.json` (melodia.cathedral_crystal.v1)
- `Saved/Audit/copernicus_cymatic_manifest.json` — 30 variants

## 4. Commands to Reproduce

```bash
# song-chord layout (pure python, no UE)
python -c "import sys; sys.path.insert(0,'Content/Python'); from build_pcg_hero_resonance_cathedral import build_cathedral_layout; print(build_cathedral_layout())"

# houdini fractal + crystal (hython)
hython Tools/Houdini/cathedral/build_fractal_cathedral.py --depth 4 --span 10 --height 20 --bays 8
hython Tools/Houdini/cathedral/build_crystal_cathedral.py --crystal 0.85 --facets 12

# copernicus 4096 crystal
hython Tools/Houdini/copernicus/copernicus_cymatic_parallax.py --variant CrystalCathedral --size 4096x4096 --cook

# PCG graph (requires editor + Monolith port 9316)
# import build_pcg_hero_resonance_cathedral as r; r.build_cathedral_layout()
# import audit_pcg_hero_resonance_cathedral; audit_pcg_hero_resonance_cathedral.audit()
```
