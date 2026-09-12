# Horizon Eater + Faraway LOD Destruction — Overnight Weave (2026-09-02)

**Owners:** `specs/horizon_eater/` + `specs/faraway_lod_destruction/` (JSON source of truth)  
**Markdown readers:** this doc + the two `*_DESIGN.md` sisters  
**Levels:** `LV_SeaAbove_Prototype` (horizon kill A+B+C) + `LV_FarawayMother_Prototype` (fabric dissolution)  
**Bus:** one scalar — `MPC_Melodia_Palette.HorizonEatAmount 0..1` = `WorldField.Tension` = `WorldField.HorizonEat`  
**Writer:** `UMelodiaAudioReactivePresentationSubsystem` only (readers: MIs + `UMelodiaCymaticsSubsystem`)  
**Seeds:** `20260829` deterministic everywhere (matches Klein Veil + VDM + singing veil)  

---

## What was woven overnight

This is not two separate features. Faraway mountains **are** horizon geology — so Horizon Eater eating the horizon must also be Faraway LOD destroying at horizon distance. One scalar, two expressions.

| System | What the player sees | How it disappears | Who owns it |
|--------|---------------------|-------------------|------------|
| Horizon Eater kill A | Second ocean band (-50m plane) seen through real Oceanology water | SLW absorption extinction swallows false ocean; Biolum pulse becomes membrane reveal | Oceanology (`M_Water_Oceanology_Melodia_Inst` + `AOceanologyWaterVolume` + plane `MI_SeaAbove_FalseOcean_Clean`)
| Kill B | Above-water horizon line & sky | Height fog + cloud + haze volume densify to extinction | Fog/PPV/volume actors + cloud |
| Kill C | Distant terrain silhouette at horizon | HLOD LOD3 impostor dither-crumbles (Bayer+BlueNoise+TemporalAA) + PCG density cull + filter-flow advection | HLOD + PCGEx + Houdini `HDA_P3_HorizonMouthComposer` curves |
| Faraway LOD destruction | Fabric mountains (4 biomes, 120+ pts) | LOD0→LOD3 cross-fade: POM32→0, Toksvig 0→1, rim 1→1.8, WPO 1→0, dither clip `> Tension*Mask*HorizonEat` | Material functions `MF_LODDitheredDestruction` + `MF_FabricMountainWPO` + Niagara dust |

---

## How the two specs agree

```
HorizonEatAmount (MPC scalar, sole writer)
 ├──> Kill A: Absorption *= 1+HorizonEat*3, Biolum 0.35*(1-HorizonEat*0.9)
 ├──> Kill B: Fog density 0.04->0.18, PPV bloom 0.15->0.28
 ├──> Kill C: Dither threshold = Tension*Mask*lerp(1,HorizonEat,HorizonMask)
 └──> Faraway: DestructionAmount = HorizonEat*0.9 (coupled)
        ├──> WeaveRidge (T>0.60) threshold 0.35 dies first
        ├──> LaceCanopy 0.50 dies mid
        ├──> FrillValley 0.85 dies last (floor)
        └──> ResonantSeamWay |Chladni|<0.12 never dies (Wayfold seam)
```

At `HorizonEat 1.0`, only SeamWay Heart Gate + Wayfold pair remain — the seam that outlives the mountain, just as Klein Veil was the non-orientable seam that outlived fabric. Horizon Eater is the eater **of** the Faraway Mother's horizon; the Mother looks toward the same point (`MONOLITH_LEVEL_DESIGN_BIBLE` P3 pre-reveal reaction).

---

## Files shipped (this session)

| Path | What |
|------|------|
| `specs/horizon_eater/horizon_eater_spec.v1.json` | JSON SSOT — three kills, bus, Bell-as-horizon layout, PCGEx+Houdini+evidence contract |
| `specs/horizon_eater/HORIZON_EATER_DESIGN.md` | Reader design (kill A/B/C wiring, measure-then-place, Wayfold, how to run) |
| `specs/horizon_eater/horizon_eater_manifest.v1.json` | Generated offline (seed, bounds, zones, hash) — after `build_horizon_eater_ecosystem.py` |
| `specs/horizon_eater/horizon_eater_placements.v1.json` | Generated offline (per-point Tension/horizon_mask/destruction_t) |
| `specs/horizon_eater/horizon_mouth_hda_manifest.v1.json` | Generated after HDA scaffold dry-run |
| `specs/faraway_lod_destruction/faraway_lod_destruction_spec.v1.json` | JSON SSOT — 4 LOD tiers, 4 destruction ops, per-biome Tension gates, PCGEx+HLOD |
| `specs/faraway_lod_destruction/FARAWAY_LOD_DESTRUCTION_DESIGN.md` | Reader design (dither/WPO/POM-Toksvig-rim+Niagara, Tension table, HLOD) |
| `specs/faraway_lod_destruction/faraway_lod_destruction_manifest.v1.json` | Generated offline |
| `specs/faraway_lod_destruction/faraway_lod_destruction_placements.v1.json` | Generated offline with `destruction_t`/`will_destroy`/`lod_at_rest` per point |
| `Content/Python/add_horizon_eater_mpc_params.py` | Adds `HorizonEatAmount/DestructionAmount/HorizonTension/WorldHorizonEat` to MPC_Melodia_Palette (idempotent, headless) |
| `Content/Python/horizon_eater_prototype_build.py` | Editor audit + height-aware debug marker spawn into LV_SeaAbove_Prototype (idempotent) |
| `Content/Python/faraway_lod_destruction_build.py` | Editor audit + height-aware debug into LV_FarawayMother_Prototype (idempotent) |
| `Tools/PCG/build_horizon_eater_ecosystem.py` | Offline PCG hypothesis gen (filter corridor/horizon rim/wayfold/evidence, deterministic) |
| `Tools/PCG/build_faraway_lod_destruction_ecosystem.py` | Offline PCG with per-point `destruction_t` + biome kill threshold |
| `Tools/Houdini/horizon_eater/hda_horizon_mouth_composer.py` | HDA_P3_HorizonMouthComposer scaffold (hip template + bake stub) |
| `Docs/HORIZON_EATER_AND_FARAWAY_LOD_DESTRUCTION_2026-09-02.md` | This file (weave doc) |

---

## How to run (one-editor lock, sequential)

### Off-editor hypotheses (safe to run now, no UE needed)

```bat
.venv\Scripts\python.exe Tools/PCG/build_horizon_eater_ecosystem.py --seed 20260829
.venv\Scripts\python.exe Tools/PCG/build_faraway_lod_destruction_ecosystem.py --seed 20260829
.venv\Scripts\python.exe Tools/Houdini/horizon_eater/hda_horizon_mouth_composer.py --seed 20260829 --dry-run
```

Verify JSONs: `jq .zone_summaries specs/horizon_eater/horizon_eater_manifest.v1.json && jq .zone_summaries specs/faraway_lod_destruction/faraway_lod_destruction_manifest.v1.json`

### MPC scalar (editor must be CLOSED)

```bat
UnrealEditor-Cmd.exe BS_GodFile.uproject -ExecutePythonScript="Content/Python/add_horizon_eater_mpc_params.py"
```

Reopen, `Ctrl+Shift+F` -> `MPC_Melodia_Palette` should list `HorizonEatAmount` etc at 0.0 default.

### In-editor applys (editor OPEN, verify :9316)

```bat
curl http://localhost:9316/health
python Tools/ue_run_python.py --file Content/Python/horizon_eater_prototype_build.py
python Tools/ue_run_python.py --file Content/Python/faraway_lod_destruction_build.py
```

Do not run both applys concurrently (Monolith/UE single lock). Each is rerun-safe (label dedupe).

### Tuning (no code, live in editor)

- HorizonEat: MPC `HorizonEatAmount 0->1` slider (or C++ `UMelodiaAudioReactivePresentationSubsystem::Publish` driven by Tension/rhythm). Watch SLW false-ocean band vanish, fog densify, distant HLOD stipple.
- Faraway destruction: MI `DestructionAmount` on any `MI_T_FarawayMother_*` instance (0..1). Watch ridges dither first, valley last, SeamWay persist.
- Coupling: set `DestructionAmount = HorizonEatAmount*0.9` for far horizon coupling (or let Tension rise independently for local dread).

### Evidence

Offline: `Saved/Audit/horizon_eater/` + `Saved/Audit/faraway_lod_destruction/` (hashes, seed).  
In-engine: 4 HDR captures via `UMelodiaCaptureRenderSubsystem` (present, needs `Build.bat` if edited) — Shot A pristine, B half, C eaten+membrane, D corridor top-down.  
Ledger: `Saved/gate_ledger.json` rows `horizon_eater_prototype` + `faraway_lod_destruction`.

---

## Guardrails (do NOT break)

- **Single writer:** `UMelodiaAudioReactivePresentationSubsystem` only touches `MPC_Melodia_Palette` / `NPC_Melodia_Palette`. Cymatics + MIs are read-only. Adding a second MPC writer is a defect.
- **No new masters:** destruction is `MF_LODDitheredDestruction` + `MF_FabricMountainWPO` + `MF_ToksvigAntiAlias` functions + shared `T_BayerDither_8x8 / T_BlueNoise_64x64 / T_Iridescence_LUT` — not new `M_Master_*`.
- **No new Landscape:** Nanite `SM_FarawayMother_FabricRidge` stays; all placements height-aware raycast `Visibility 50000->-50000`, `OffsetAboveSurface 35cm`.
- **HLOD reuse:** `HLOD_FarawayMother_Instanced/Merged` — eaten variants reuse bounds, impostor alpha -> 0.
- **Height fog second:** fix belief that height fog is primary for sub-surface horizon — it is not. SLW is primary per `SEA_ABOVE_SECOND_OCEAN_LAYOUT` §3.
- **Shared textures:** promote from `Saved/Audit/lookdev/optical_lods/shared/` to `/Game/EnvSandbox/Textures/Copernicus/Shared/` — do not regenerate.
- **One Wayfold truth:** UE `BP_WayfoldPair` owns crossing/streaming; Houdini only authors locators/curves.

---

## Cross-refs

- Faraway Mother build: `Docs/Art/FARAWAY_MOTHER_FABRIC_MOUNTAIN_BUILD_2026-09-02.md` + `Docs/PCG/FARAWAY_MOTHER_PCG_SYSTEM_ARCHITECTURE.md` + `specs/pcg/faraway_mother_pcg_manifest.v1.json`
- Sea Above horizon: `Docs/Art/SEA_ABOVE_SECOND_OCEAN_LAYOUT_AND_CAMERA_PLAN_2026-08-29.md` + `SEA_ABOVE_TONIGHT_EXECUTION_AND_AGENT_HANDOFF_2026-08-26.md` + `P0_MATERIAL_SEA_ABOVE_GATE_2026-08-27`
- Late monolith escalation: `Docs/Houdini/LATE_MONOLITH_VISUAL_ESCALATION_BIBLE_2026-08-29.md` + `Docs/Monoliths/P3_HORIZON_EATER_PLAN_2026-08-29.md` + `Docs/Houdini/MARA_P0_P3_HOUDINI_EXECUTION_PLAN_2026-08-29.md #9`
- LOD precedent: `specs/lookdev/optical_lod_manifest.v1.json` + `specs/lookdev/optical_material_instances.v1.json`
- Klein Veil seam precedent: `specs/klein_veil/klein_veil_manifest.v1.json` + `Docs/KLEIN_VEIL_SING_2026-09-02.md`
- Emerging toolchain SSOT: `Docs/Research/EMERGING_TOOLCHAIN_MASTER_INDEX_2026-08-31.md`
