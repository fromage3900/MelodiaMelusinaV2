# Houdini Foundry Day — 2026-09-24 (college full-licence session)

**Front door:** [`/START_HERE_COLLEGE_HOUDINI_2026-09-24.md`](../../../START_HERE_COLLEGE_HOUDINI_2026-09-24.md).
**Status authority:** `CURRENT_STATE.md`. Nothing in this folder promotes a proof level; only evidence plus a `CURRENT_STATE.md` edit does.
**Status of this folder:** STAGED — every file describes work to run at college. Nothing here has run in Houdini or UE.

## 2026-10-06 update — AnimationDoctor lab day (current priority)

**Today's override:** use the college full Education licence first as a **KineFX animation diagnostics lab**, while Brennan handles hero-render framing and presentation work. The original Foundry world-building gates below remain valid backlog; they are not promoted or marked complete by this update.

### Mission

Build a reusable, non-destructive `HDA_Melodia_AnimationDoctor` that answers: **what is wrong with a runtime animation, on which joints/frames, and is the fault in source motion, rest pose/skeleton, retarget assumptions, root motion, contact, or UE presentation?** Houdini diagnoses and optionally produces deterministic corrected exports; **UE 5.8 and the canonical Melusina skeleton remain runtime authority.** Do not create a second animation pipeline or replace UE's IK Retargeter.

### First specimen — isolated Melusina/Shinbi recovery lane

Use the animation/retarget payload identified in source commit `6ca411e1d5` as the bounded test set, without treating its divergent cleanup branch as authority:

- `A_Shin_Idle`
- `A_Shin_Idle_pose`
- `A_Shin_Idle_stand`
- `A_Shin_Cast`
- canonical Melusina target skeleton / current runtime retarget assumptions

The GitHub reconciliation audit found the runtime UE binaries in that source lane do not overlap later `main` changes; `BS_GodFile.uproject` and `CURRENT_STATE.md` do, so neither may be restored from the old source commit. Work from current canonical `main`/SSD state and treat old history as specimen/reference only.

### AnimationDoctor stages

| Stage | Measure / visualize | Default behavior |
|---|---|---|
| REST | hierarchy, names, parents, rest transforms, joint orientation, bone length, scale, coordinate basis | flag only; no silent correction |
| ROOT | trajectory, XY/Z displacement, rotation, discontinuities, floating/reference-pose jumps | visualize; optional normalization disabled by default |
| CONTACT | foot height + velocity + stable-frame windows; sliding while planted | emit contact intervals/markers and slip metrics |
| JOINT HEALTH | angular velocity, transform discontinuities, extreme rotations/scales | rank worst joints and frames |
| RETARGET | source vs target vs retarget-result pose/trajectory differences | viewport overlay/comparison |
| EXPORT | deterministic corrected clip when evidence justifies it | new output only; never overwrite source |

Design contact analysis so the same architecture can later accept hands, hooves and weapon grips. Prefer machine-readable attributes/report data alongside viewport evidence.

### Required viewport/evidence

Show source skeleton, target skeleton, root trail, contact markers and problem-joint markers together clearly enough that a bad retarget assumption is visually obvious. For each Shinbi clip, retain a small diagnostic report plus representative captures under `Saved/Audit/houdini_foundry/animation_doctor/<clip>/`. Large caches/intermediates stay under `Saved/HoudiniFoundry/` or college scratch and are never committed.

### Second specimen — Choral Sheep

Only after the Melusina diagnostic foundation works, run the same analyzer against Choral Sheep. Evaluate hoof-contact detection and locomotion phase analysis first; then test deterministic phase offsets, speed variation, and bounded head/ear/tail secondary variation. This is the bridge to Jev-directed flock variants and realtime cymatics presentation, **not permission to build a parallel flock/runtime authority**.

### Division of labor for the lab session

- **Muse Spark / technical worker:** build and validate the bounded KineFX diagnostic network, metrics, reports and evidence. Do not redesign runtime architecture and do not auto-fix ambiguous failures.
- **Brennan:** hero-render framing, lighting/composition and visual judgment; review diagnostic evidence at explicit gates rather than watching cooks.
- **UE follow-up:** only after evidence identifies a specific failure, make the smallest surgical UE-side retarget/runtime repair and prove it in PIE/packaged presentation.

### Today is successful when

1. At least one Shinbi → Melusina clip produces an interpretable AnimationDoctor report and viewport proof.
2. The report localizes the failure category and worst joints/frames instead of merely saying the animation looks wrong.
3. Source assets remain untouched and no competing canonical animation path is introduced.
4. If time permits, Choral Sheep proves the same diagnostic architecture can detect hoof contacts/phase without committing a full flock rewrite.
5. Separately, the presentation lane leaves the lab with 2–3 portfolio-grade hero frames; rendering does not block the diagnostic worker.

**Stop condition:** if the proposed fix requires changing canonical skeleton authority, rewriting the UE animation architecture, restoring stale `CURRENT_STATE.md`/`.uproject` state, or mass-exporting corrected clips before diagnosis is proven, stop at evidence and defer the runtime decision.

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
| HDAs | `hda/<Name>_<major.minor>.hda` | tracked through Git LFS on this branch; project-authored `hda/**` only |
| New Hython scripts | `Tools/Houdini/<family>/` | tracked with `git add -f` (see `Tools/*` rule) |
| UE assets | `/Game/Melodia/HoudiniFoundry/<Product>/` (new) or the existing prefix a recipe names | normal UE save; LFS |

## Artifact policy (from `.gitattributes`/`.gitignore` as they stand; both are owner-only files)

- **Track:** Python/Hython, HDAs, schemas, recipes, docs, manifests, hashes, small evidence, small representative previews.
- **Do not commit:** VDB sequences, FLIP/Vellum caches, `.bgeo.sc` caches, PDG intermediates, multi-GB EXR stacks. New project-authored `hda/**` files are LFS-routed; existing/legacy `.vdb`, `.hip*`, vendor `.hda`, and `.bgeo*` are not blanket-migrated and must not be added casually.
- **Where large outputs live:** the college machine's local scratch under `Saved/HoudiniFoundry/` during the day. Before leaving, copy the final baked products you want to keep (not caches) to the owner's transfer drive, and list them with sha256 in the manifest so they can be re-verified on the PC.
