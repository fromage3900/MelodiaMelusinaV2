# Houdini Foundry Day — 2026-09-24 (college full-licence session)

**Front door:** [`/START_HERE_COLLEGE_HOUDINI_2026-09-24.md`](../../../START_HERE_COLLEGE_HOUDINI_2026-09-24.md).
**Status authority:** `CURRENT_STATE.md`. Nothing in this folder promotes a proof level; only evidence plus a `CURRENT_STATE.md` edit does.
**Status of this folder:** STAGED — every file describes work to run at college. Nothing here has run in Houdini or UE.

## What this day is for

Turn a day of full-licence Houdini into **durable, deterministic, verifiable** world-building capability. The measure is "reusable capability added", not "assets generated".

## Hierarchy (unchanged)

```text
Universe Foundry (mission compiler, Tools/universe_foundry.py)
    ↓ bounded mission/task
Hermes / specialist worker (Space Bunny)
    ↓
existing owner: World Compiler · Hython family · Houdini/HDA · UE (Monolith, one writer)
    ↓
evidence (bake_manifest.json + Saved/Audit/houdini_foundry/) → mission DAG
```

- **Houdini** generates and bakes offline content and fields.
- **World Compiler** compiles deterministic world content (`world_compiler_v1.0`, unchanged).
- **PCG** places. **Niagara** presents runtime particles. **Materials** consume approved data.
- **C++/existing gameplay** keeps authority. **Existing MPC writers stay the sole writers.**
- No new global environmental singleton, parallel compiler, runtime HDA cook or second source of runtime truth.

## Folder map

| File | Gate | Priority |
|---|---|---|
| [`00_INTAKE.md`](00_INTAKE.md) | — | audit: what exists, proof levels, stale docs, missing files |
| [`01_EXECUTION_ORDER.md`](01_EXECUTION_ORDER.md) | all | gate order, two-lane parallelism, stop conditions, fatigue-safe mode, acceptance tiers |
| [`02_HDA_ENGINE_PROOF.md`](02_HDA_ENGINE_PROOF.md) | 1 | **P0** custom HDA → Engine → UE cook/bake/save/reload/audit |
| [`03_CRYSTAL_CATHEDRAL_HDA.md`](03_CRYSTAL_CATHEDRAL_HDA.md) | 2 | **P0** regenerate + promote to `HDA_Melodia_CrystalCathedral`; optional song extension |
| [`04_FOUNDRY_FIELD_ATLAS.md`](04_FOUNDRY_FIELD_ATLAS.md) | 3 | **P0** `HDA_Foundry_FieldAtlas` spec |
| [`05_SEA_ABOVE_TILE_BAKE.md`](05_SEA_ABOVE_TILE_BAKE.md) | 4–5 | **P0** one tile → UE, then tiled bake |
| [`06_DEPOSITION_GLITTER.md`](06_DEPOSITION_GLITTER.md) | 6 | **P0** `HDA_Foundry_Deposition` / Glitter Pile |
| [`07_FLOW_VOLUME.md`](07_FLOW_VOLUME.md) | 7 | P1 `HDA_Foundry_FlowVolume` |
| [`08_VOLUMETRIC_ECOLOGY.md`](08_VOLUMETRIC_ECOLOGY.md) | 8 | P1 volume vocabulary + Sea Above fluid intelligence |
| [`09_COPERNICUS_FIELD_PIPELINE.md`](09_COPERNICUS_FIELD_PIPELINE.md) | 9 | P1 fields → existing 9-map contract |
| [`10_PDG_BAKE_FARM.md`](10_PDG_BAKE_FARM.md) | 10 | P0/P1 `TOP_Foundry_BakeFarm` |
| [`11_FARAWAY_MOTHER_VELLUM.md`](11_FARAWAY_MOTHER_VELLUM.md) | 11 | P1, only if P0 is healthy |
| [`12_UE_INTEGRATION_GATES.md`](12_UE_INTEGRATION_GATES.md) | 1,2,4,6 | shared UE bake/save/reload/audit procedure |
| [`13_END_OF_DAY_CLOSEOUT.md`](13_END_OF_DAY_CLOSEOUT.md) | end | commit, evidence, `CURRENT_STATE.md` update |

## Contracts shipped with this branch

| Path | Role |
|---|---|
| `specs/houdini_foundry/` | recipe / bake manifest / bake request schemas + FieldAtlas channel vocabulary |
| `recipes/houdini_foundry/` | staged recipes (HDA smoke, cathedral, Sea Above test tile, glitter) + first BakeFarm request |
| `Tools/Houdini/foundry/houdini_foundry.py` | `probe` · `validate` · `plan` · `verify` — offline, stdlib only |

## Paths every gate uses

| What | Where | Git |
|---|---|---|
| Bake outputs | `Saved/HoudiniFoundry/<recipe_id>_<seed>/[tiles/<tile_id>/]` | **not tracked** (`Saved/` ignored); large caches stay here or on the college scratch drive |
| Bake manifest | `Saved/HoudiniFoundry/<recipe_id>_<seed>/bake_manifest.json` | copy into evidence |
| Evidence | `Saved/Audit/houdini_foundry/<recipe_id>/` — manifest copy, probe JSON, logs, ≤ 1 MB previews | tracked with `git add -f` |
| HDAs | `hda/<Name>_<major.minor>.hda` | tracked (small binaries; not LFS — owner decides before a large one) |
| New Hython scripts | `Tools/Houdini/<family>/` | tracked with `git add -f` (see `Tools/*` rule) |
| UE assets | `/Game/Melodia/HoudiniFoundry/<Product>/` (new) or the existing prefix a recipe names | normal UE save; LFS |

## Artifact policy (from `.gitattributes`/`.gitignore` as they stand; both are owner-only files)

- **Track:** Python/Hython, HDAs, schemas, recipes, docs, manifests, hashes, small evidence, small representative previews.
- **Do not commit:** VDB sequences, FLIP/Vellum caches, `.bgeo.sc` caches, PDG intermediates, multi-GB EXR stacks. `.vdb`/`.hda`/`.hip`/`.bgeo*` are **not** LFS-routed today, so any large one would bloat plain git.
- **Where large outputs live:** the college machine's local scratch under `Saved/HoudiniFoundry/` during the day. Before leaving, copy the final baked products you want to keep (not caches) to the owner's transfer drive, and list them with sha256 in the manifest so they can be re-verified on the PC.
