# Horizon-Eater / Faraway-LOD Ecosystem Build Handoff — 2026-09-02

**Repo:** `C:/EnvironmentPortfolio/BS_GodFile` · **Date:** 2026-09-02 · **Seed:** `20260829` · **Count:** 120 points/group
**Mode:** offline-safe pure-Python, deterministic, no UE editing performed.

## What ran (both exit 0)

```bat
.venv\Scripts\python.exe Tools/PCG/build_horizon_eater_ecosystem.py --seed 20260829 --n 120
.venv\Scripts\python.exe Tools/PCG/build_faraway_lod_destruction_ecosystem.py --seed 20260829 --n 120
```

Validated both output manifests (valid JSON, hashed, `tools/PCG` builders) and both design docs (section headers present):
- `specs/horizon_eater/horizon_eater_manifest.v1.json`
- `specs/faraway_lod_destruction/faraway_lod_destruction_manifest.v1.json`
- `specs/horizon_eater/HORIZON_EATER_DESIGN.md` — kills present: Kill A (Oceanology SLW absorption), Kill B (Volumetric haze), Kill C (LOD3 impostor crumble + PCG filter-flow cull)
- `specs/faraway_lod_destruction/FARAWAY_LOD_DESTRUCTION_DESIGN.md` — the four destruction operators incl. dithered-opacity kill, WPO fade, POM→Toksvig→Rim preservation

## Group summary (point_count / avg_tension)

**Horizon Eater** (`horizon_eater_manifest.v1.json`):
| group | point_count | avg_tension |
|---|---|---|
| FilterCorridor | 120 | 0.9182 |
| HorizonRim (mouth-card group) | 120 | 0.7864 |
| WayfoldPair | 120 | 0.0949 |
| DistanceEvidence | 120 | 0.9289 |

**Faraway LOD Destruction** (`faraway_lod_destruction_manifest.v1.json`):
| group | point_count | avg_tension |
|---|---|---|
| WeaveRidge | 120 | 0.8543 |
| LaceCanopy | 120 | 0.6971 |
| FrillValley | 120 | 0.3922 |
| ResonantSeamWay | 120 | 0.2642 |

## Placement rules (must hold in-editor)

- **Height-aware placement:** every point is raycast onto `CanonicalLandscape` at placement time. Never floating, never buried; **no new Landscape** is created — all points ride the existing canonical terrain.

## Single MPC writer

- `Content/Python/add_horizon_eater_mpc_params.py` defines the one parameter the write path uses: **`HorizonEatAmount`** (alias) → **`Tension`** on **`MPC_Melodia_Palette`**. Both ecosystems drive off this single shared bus; no secondary MPC writes.
- (Analogous `add_tension_mpc_params.py` exists as a fallback for the shared Tension contract.)

## Exact next in-editor step to place these

1. Headless (MPC params must exist before the builds run):
   ```bat
   UnrealEditor-Cmd.exe BS_GodFile.uproject -ExecutePythonScript="Content/Python/add_horizon_eater_mpc_params.py"
   ```
2. In-editor placement builds (consume the manifests above):
   ```bat
   python Tools/ue_run_python.py --file Content/Python/horizon_eater_prototype_build.py
   python Tools/ue_run_python.py --file Content/Python/faraway_lod_destruction_build.py
   ```
   Each `*.py` raycasts the manifest point-groups onto `CanonicalLandscape` and instantiates the per-group material instances listed in the manifests.

## Files created / regenerated
- **Created:** this handoff doc (only new tracked file; no existing tracked file modified).
- **Regenerated outputs (permitted):** the two manifest + placement JSONs under `specs/horizon_eater/` and `specs/faraway_lod_destruction/`.

## Evidence
Offline manifests hashed. In-engine proof still pending = the next-in-editor step above (4 HDR captures, Tension 0/0.5/1.0 + Wayfold, per `FARAWAY_LOD_DESTRUCTION_DESIGN.md` §9).