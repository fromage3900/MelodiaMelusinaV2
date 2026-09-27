# 03 — Gate 2 (P0): regenerate and promote the Crystal Cathedral → `HDA_Melodia_CrystalCathedral`

| | |
|---|---|
| **Purpose** | Turn the existing Hython cathedral into a clean, parameterised HDA **without rewriting the cathedral**. |
| **Authority** | `Tools/Houdini/cathedral/build_fractal_cathedral.py` + `build_crystal_cathedral.py` are the geometry authority. The GN twin `MEL_p4_crystal_cathedral` is an interface stub (Geometry in → out) and is not an authority. UE meshes under `/Game/EnvSandbox/Meshes/Cathedral_Houdini/` are the runtime assets. Sea Above's `00_CANON/Cathedral` placement is owner-authored. |
| **Inputs** | `recipes/houdini_foundry/crystal_cathedral_6bay_harmony.v1.json`; tracked manifests `Saved/Audit/cathedral/{crystal_cathedral,cathedral_fractal}_manifest.json`. |
| **Outputs** | Regenerated OBJs + manifest; `hda/HDA_Melodia_CrystalCathedral_1.0.hda`; parity report; optional new UE mesh under `/Game/Melodia/HoudiniFoundry/Cathedral/`. |
| **Evidence** | `Saved/Audit/houdini_foundry/crystal_cathedral_6bay_harmony/` |
| **Status** | Source proven (numpy, deterministic `random.Random(20260901)`). OBJs untracked. HDA does not exist. Groups do not exist. |

## Step A — regenerate first (proves the source still reproduces)

```powershell
python Tools/Houdini/foundry/houdini_foundry.py validate recipes/houdini_foundry/crystal_cathedral_6bay_harmony.v1.json
python Tools/Houdini/cathedral/build_crystal_cathedral.py --depth 4 --span 10 --height 20 --tracery 0.85 --bays 6 --crystal 0.85 --facets 12
```

It runs in plain Python or hython (numpy only). Compare to the tracked manifest: **2706 v / 2101 f** (nave) and **1032 v / 290 f** (rose). The script overwrites `Saved/Audit/cathedral/crystal_cathedral_manifest.json`, so diff it with `git diff` and restore it if the numbers match (they are identical by design). Record OBJ sha256 twice (two runs) to prove determinism.

## Step B — promote to HDA (Python SOP wraps the existing functions)

Build `HDA_Melodia_CrystalCathedral` as **one Python SOP** that imports `build_fractal_cathedral` / `build_crystal_cathedral` from the repo and emits their verts/faces. Do not rebuild the arch in VEX today; parity with the source is the P0.

1. `node = hou.pwd(); geo = node.geometry()` (H22 does not prebind `geo`).
2. Add the repo root to `sys.path` from an HDA parm `RepoRoot` (default `$HIP/..`; never hardcode a drive).
3. Call the builders with parm values and write points/polys + `uv`.
4. Refactor the scripts **minimally** to expose the knobs they fake today, keeping the CLI defaults byte-identical:
   - `--seed` (replaces hardcoded `SEED`; default 20260901),
   - `--rose-n/--rose-m` (default 8/6; replaces hardcoded `n,m=8,6`),
   - return a per-face **group label** alongside faces.
   Re-run Step A after the refactor: hashes must still match.

### Exposed parameters

| HDA parm | Source arg | Exists today? |
|---|---|---|
| `Seed` | `SEED` const | refactor (A4) |
| `BayCount` | `--bays` | yes |
| `ArchSpan` | `--span` | yes |
| `VaultHeight` | `--height` | yes |
| `RecursionDepth` | `--depth` | yes |
| `TraceryDensity` | `--tracery` | yes |
| `CrystalDensity` | `--crystal` | yes |
| `FacetCount` | `--facets` | yes |
| `CrystalHeight` | multiplier on `h` in `build_crystal_cathedral` | new, default 1.0 = identical |
| `CrystalJitter` | the ±0.3 / ±0.5 jitter ranges | new, default 1.0 = identical |
| `RoseModeN`, `RoseModeM` | hardcoded 8/6 | refactor (A4) |
| `SongInfluence` | — | new, default 0 (off) |
| `ResonanceStrength` | — | new, default 0 (off) |

### Geometry groups (proposed — none exist today)

`cathedral_floor`, `cathedral_arch` (nave shell), `cathedral_rib`, `cathedral_buttress` (reserved; the source makes no buttress geometry, only pinnacle positions), `cathedral_pinnacle`, `cathedral_crystal` (rib shards), `cathedral_rose`, `cathedral_trim` (reserved). Emit only groups that have faces; record which were emitted in the manifest. Groups become UE material slots via `unreal_material` per group only if the owner wants slots. Default is one slot, matching today's meshes.

### Parity check (required)

Cook the HDA with defaults, export OBJ via **File SOP `filemode="write"`** (never index 3), and compare vert/face counts to Step A. The HDA must be `bays=6 → 2706/2101`. Save a parity JSON in evidence.

## Step C — UE (only after Gate 1 is green)

Import or bake to `/Game/Melodia/HoudiniFoundry/Cathedral/SM_Cathedral_Crystal_HDA_6Bays` (new name; **do not overwrite** the existing `SM_P4_*` assets, which Sea Above references). Follow `12_UE_INTEGRATION_GATES.md`. Swapping placed Sea Above instances is ask-first.

## Song cathedral extension (optional, off by default)

The musical cathedral already exists as PCG placement: `Content/Python/build_pcg_hero_resonance_cathedral.py`, `CHORD_PROGRESS` = **C, Dm, F, G, Am, E**, six stations, 18 chord tones. Geometry can *listen* to it, but must never require it.

| Musical input | Geometry behaviour | Default |
|---|---|---|
| pitch class (`midi % 12`) of each station's chord tones | Chladni `RoseModeN/M` per station (e.g. N = 1 + pc_root % 12, M = 1 + pc_third % 12, clamped 1..12) | off |
| interval (third quality: 3 vs 4 semitones) | facet count per bay (minor → FacetCount−2, major → FacetCount) | off |
| chord/station index 0..5 | architectural density: bay shard count ×(1 + 0.15·station) | off |
| resonance 0..1 (`ResonanceStrength`) | crystal height gain + point attrs `emissive_weight`, `sparkle_weight` for material/Niagara consumers | 0 |

Implementation: a small pure function `song_modulation(station, chord) -> dict`. It imports `CHORD_PROGRESS`/`chord_for_station` read-only from the PCG script, so there is no second chord table. `SongInfluence=0` must hash-match the non-song cook. The per-station bay mapping is 1 bay ↔ 1 station when `BayCount=6`; for other bay counts use `station = bay % 6`.

## Done when

Minimum: Step A reproduces the manifest counts twice with identical hashes. Strong: Step B HDA parity PASS + manifest. Exceptional: song-modulated variant (owner picks it from a contact sheet) + UE bake per `12`.
