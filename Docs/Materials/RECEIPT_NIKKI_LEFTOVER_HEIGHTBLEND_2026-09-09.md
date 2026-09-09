# Receipt - Nikki leftover validate + HeightBlend reparent list - 2026-09-09

**Status:** DOC list + validate checklist (parents not inventable without editor Asset Registry)  
**Owner lane:** Melodia study bot (per MATERIALS_WIRING_FLIPBOOK_CLEANUP + New Bot split)  
**Index:** [Docs/Materials/README.md](README.md) · **Labels:** [LABEL_MAP_2026-09-09.md](LABEL_MAP_2026-09-09.md)  
**Authority:** `/Game/EnvSandbox/Materials/Masters/M_Master_Nikki_Landscape` (**SHIP**)  
**Legacy:** `/Game/EnvSandbox/Materials/Masters/M_Master_Toon_Landscape_HeightBlend` (**LEGACY**)  
**Source:** `Saved/Audit/landscape_authority_convergence_2026-09-03.json` + on-disk MI inventory 2026-09-09

## A) Fresh validate checklist (OPEN — editor)

Run **`validate_material` only** on Nikki master (NO `recompile_material`, NO `save_packages`). Owner Ctrl+S if anything intentional.

| Check | Result |
|-------|--------|
| `validate_material` `/Game/EnvSandbox/Materials/Masters/M_Master_Nikki_Landscape` | **OPEN** — hard errors: ___ / warnings: ___ |
| Parent of `MI_Glacier_Landscape_Layered` still Nikki | **OPEN** (contract says yes as of 2026-09-04) |
| Sea Above / Glacier PIE reads Nikki parent | **OPEN** (owner) |
| Scratch `/Game/.../_Scratch/M_Master_Nikki_Landscape` ignored | SCRATCH — not authority |

## B) Reparent progress (from convergence audit — do not invent names)

| Bucket | Count / note |
|--------|----------------|
| **DONE** | **19/37** core landscape/Gaea MIs reparented to Nikki (incl. **`MI_Glacier_Landscape_Layered`**) |
| **DEFERRED** | Remaining **~18** showcase/test MIs — audit did **not** name them; fill via editor parent query below |
| HeightBlend master quarantine | **not_completed** until all consumers reparented (owner review) |

## C) Candidate MI inventory (filesystem — parents UNKNOWN until editor)

Paths under `Content/` as of 2026-09-09. **Parent column stays OPEN** until Asset Registry / Monolith read-back. Do not guess.

### Likely core / still in play

| Path | Suspected role | Parent |
|------|----------------|--------|
| `/Game/Gaea/Glacier/Materials/MI_Glacier_Landscape_Layered` | Sea Above / Gaea — **DONE → Nikki** | Nikki (audit) |
| `/Game/EnvSandbox/Materials/Instances/Landscape/MI_Landscape_CliffGrass` | core landscape | OPEN |
| `/Game/EnvSandbox/Materials/Instances/Landscape/MI_Landscape_CarvedRock` | core | OPEN |
| `/Game/EnvSandbox/Materials/Instances/Landscape/MI_Landscape_CoastalCliff` | core | OPEN |
| `/Game/EnvSandbox/Materials/Instances/Landscape/MI_Landscape_DesertArid` | core | OPEN |
| `/Game/EnvSandbox/Materials/Instances/Landscape/MI_Landscape_ForestFloor` | core | OPEN |
| `/Game/EnvSandbox/Materials/Instances/Landscape/MI_Landscape_Meadow` | core | OPEN |
| `/Game/EnvSandbox/Materials/Instances/Landscape/MI_Landscape_NikkiDream` | Nikki lookdev | OPEN |
| `/Game/EnvSandbox/Materials/Instances/Landscape/MI_Landscape_PondBank` | core | OPEN |
| `/Game/EnvSandbox/Materials/Instances/Landscape/MI_Landscape_SakuraGarden` | core | OPEN |
| `/Game/EnvSandbox/Materials/Instances/Landscape/MI_Landscape_SnowAlpine` | core | OPEN |
| `/Game/EnvSandbox/Materials/Instances/Landscape/MI_Landscape_UrbanCobble` | core | OPEN |
| `/Game/EnvSandbox/Materials/Instances/Landscape/MI_Landscape_VolcanicRock` | core | OPEN |
| `/Game/EnvSandbox/Materials/Instances/Landscape/MI_Landscape_WetlandMud` | core | OPEN |
| `/Game/EnvSandbox/Materials/Instances/Landscape/MI_Landscape_WitchGarden` | core | OPEN |
| `/Game/EnvSandbox/Materials/Instances/Landscape/MI_Landscape_Grass_Tilable_R090_Tile6` | tiled grass | OPEN |
| `/Game/EnvSandbox/Materials/Instances/Sakura/MI_SakuraLandscape` | Sakura | OPEN |
| `/Game/EnvSandbox/Materials/Masters/MI_SakuraLandscape` | **misplaced in Masters/** — move-to-Instances path hygiene | OPEN |

### Explicit HeightBlend-named / LEGACY-family (high priority to confirm)

| Path | Note | Parent |
|------|------|--------|
| `/Game/EnvSandbox/Materials/Instances/MI_Master_Toon_Landscape_HeightBlend_Inst` | HeightBlend Inst | OPEN |
| `/Game/EnvSandbox/Materials/Instances/MelusinaReal/M_Master_Toon_Landscape_HeightBlend/MI_M_Master_Toon_Landscape_HeightBlend_Grass` | folder implies HeightBlend | OPEN |
| `.../MI_M_Master_Toon_Landscape_HeightBlend_LandscapeGrayscale` | same | OPEN |
| `.../MI_M_Master_Toon_Landscape_HeightBlend_Soil` | same | OPEN |
| `/Game/EnvSandbox/Materials/SDF/Instances/MI_Landscape_HeightBlend` | SDF HeightBlend MI | OPEN |
| `/Game/EnvSandbox/Materials/SDF/Instances/MI_AdvancedLandscape_HeightBlend` | SDF advanced | OPEN |
| `/Game/EnvSandbox/Materials/SDF/Instances/MI_Landscape_LayerBlend` | older blend | OPEN |
| `/Game/EnvSandbox/Materials/SDF/Instances/MI_HybridLandscape_MooaToonSDF` | hybrid | OPEN |
| `/Game/EnvSandbox/Materials/SDF/Instances/MI_Landscape_Quad_GeometryFake` | fake geo | OPEN |

### Showcase / test (likely the deferred ~18)

| Path | Note | Parent |
|------|------|--------|
| `/Game/EnvSandbox/Materials/Instances/Showcase2026_06_27/Landscape/MI_Showcase2_Landscape_Baseline` | showcase | OPEN |
| `.../MI_Showcase2_Landscape_MacroVariation` | showcase | OPEN |
| `.../MI_Showcase2_Landscape_RealNormals` | showcase | OPEN |
| `/Game/EnvSandbox/Materials/Validation/MI_Landscape_CymaticsFull` | validation | OPEN |
| `/Game/EnvSandbox/Materials/Validation/MI_Landscape_CymaticsHalf` | validation | OPEN |
| `/Game/EnvSandbox/Materials/_Scratch/MI_NikkiLandscape_Test` | **SCRATCH** | ignore |

### Other / triage

| Path | Note |
|------|------|
| Impressionist / Stylized / PBR_Auto / Melusina grayscale landscape MIs | Not in 37-core claim; label separately if they still parent HeightBlend |

## D) LEGACY masters (from LABEL_MAP — retire after consumers clear)

- `M_Master_Toon_Landscape_HeightBlend` (+ Inst)
- `M_Landscape_HeightBlend`
- `M_AdvancedLandscape_HeightBlend`
- `M_Landscape_LayerBlend`

## E) Editor fill-in procedure (New Bot or Melodia bot when :9316 up)

1. Asset Registry filter: MaterialInstanceConstant whose parent soft-path contains `Landscape_HeightBlend` OR equals HeightBlend master paths above.
2. For each hit: record path → current parent → action (`reparent→Nikki` / `defer showcase` / `LEGACY keep until…`).
3. `validate_material` Nikki master only; paste hard-error count into section A.
4. Owner Ctrl+S after any intentional reparent. **Never** Monolith `save_packages` / `recompile_material`.

## Hard rules

- Docs-first; no Content binaries in this PR.
- No invented parent assignments.
- One concern per PR off **main**.
