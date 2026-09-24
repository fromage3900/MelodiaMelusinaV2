# START HERE — College Houdini Foundry Day (2026-09-24)

For **Space Bunny + Hermes** on the college full-licence Houdini machine. This page assumes no prior chat context.
Detailed gate docs: [`Docs/Houdini/FoundryDay_2026-09-24/`](Docs/Houdini/FoundryDay_2026-09-24/README.md). Status authority: `CURRENT_STATE.md`.

## 1. Branch and base

- **Branch:** `prep/houdini-foundry-college-2026-09-24`
- **Base:** `origin/main` @ `cad8272cbb42775845db3e3e2600dd4e4d2d5d56`
- Nothing on this branch has run in Houdini or UE. Every recipe is `status: staged`.

## 2. Do not rebuild what exists (extend these)

| Need | Existing owner — extend it |
|---|---|
| HDA Engine smoke | `Content/Python/create_hda_arpeggio_stair.py` + `Docs/WorldGen/HOUDINI_ENGINE_SMOKE_SPEC_2026-08-27.md` |
| Cathedral | `Tools/Houdini/cathedral/build_fractal_cathedral.py` → `build_crystal_cathedral.py` (geometry authority); UE meshes `/Game/EnvSandbox/Meshes/Cathedral_Houdini/` |
| Song cathedral | `Content/Python/build_pcg_hero_resonance_cathedral.py` (6 stations C Dm F G Am E, 18 pads — already built) |
| World compile / placement | `Tools/world_compiler.py` + `Tools/world_compiler_ue_driver.py` (v1 unchanged) |
| Missions | `Tools/universe_foundry.py` (mission DAG shape) |
| Field baker pattern | `Tools/Houdini/vdm_fabric_mountains/faraway_static_field.py` |
| Texture maps | 9-map cymatic contract + `Content/Python/verify_tex_contract.py` |
| Niagara / MPC | canonical Niagara stack; sole MPC writers stay sole writers |
| Seeds / hashes | `resonant_world_generator.stable_int`, `universe_foundry.content_hash` (wrapped by `Tools/Houdini/foundry/houdini_foundry.py`) |

No second World Compiler, Foundry, Niagara framework, MPC writer, runtime HDA cook, or global environment singleton.

## 3. Gate 0 — first commands (PowerShell, repo root)

If the repo is **already cloned** on the college machine:

```powershell
git fetch origin
git switch prep/houdini-foundry-college-2026-09-24
git pull --ff-only
git status                      # must be clean
git rev-parse HEAD              # record it
```

If it is **not cloned** (the full repo is large, ~24 GB `.git` plus LFS). For Houdini-only work, skip LFS smudge and pull only what a gate needs:

```powershell
$env:GIT_LFS_SKIP_SMUDGE = "1"
git clone --branch prep/houdini-foundry-college-2026-09-24 https://github.com/fromage3900/MelodiaMelusinaV2.git
cd MelodiaMelusinaV2
Remove-Item Env:GIT_LFS_SKIP_SMUDGE
# UE work needs real content: git lfs pull  (or --include for the paths a gate touches)
```

Then point at Houdini and run the gate:

```powershell
$env:HOUDINI_HYTHON_EXE = "C:\Program Files\Side Effects Software\Houdini <college build>\bin\hython.exe"   # set to the real path
python Tools/Houdini/foundry/houdini_foundry.py probe --out Saved/Audit/houdini_foundry/probe_2026-09-24.json
python Tools/Houdini/foundry/test_houdini_foundry.py
python Tools/test_universe_foundry.py
python Tools/test_world_compiler.py
python Tools/Houdini/foundry/houdini_foundry.py validate recipes/houdini_foundry/*.json
```

**The very first command after syncing is the `probe` line.** It runs hython under a hard 60 s timeout and kills it on a licence hang (lane law #1). It records Houdini version, licence category and `hserver -l`.

Record in `Saved/Audit/houdini_foundry/gate0_2026-09-24.json` (by hand or agent): HEAD SHA, Houdini build, licence line, UE version (if present), and the Houdini Engine plugin that UE loads vs `Plugins/HoudiniEngine/HoudiniEngine.uplugin` (**22.0.368 for UE 5.8**).

## 4. Houdini / Hython paths

- The repo's tools assume `C:\Program Files\Side Effects Software\Houdini 22.0.368\bin\hython.exe` (owner PC). **The college build may differ.** Always set `HOUDINI_HYTHON_EXE` (or `HFS`); do not edit tools to a new hardcoded path.
- `Content/Python/smoke_houdini_engine_pcg.py` hardcodes 22.0.368. Expect a hython FAIL line there on another build. Record it rather than patch mid-gate.
- Houdini is metres; UE is ×100 cm.

## 5. Hermes

- Launch the project's existing Hermes: `hermes --tui` from the repo root (see `START_HERE_TONIGHT_PI_HERMES_UNIVERSE_FOUNDRY.md` §1). On the owner PC its venv lives at `%LOCALAPPDATA%\hermes\hermes-agent\venv`. **No college-machine install is documented.** If `hermes` is not on PATH, run Space Bunny directly from this page instead of installing a different package.
- Operator instruction for Hermes: *"Read START_HERE_COLLEGE_HOUDINI_2026-09-24.md and Docs/Houdini/FoundryDay_2026-09-24/01_EXECUTION_ORDER.md. Execute gates in order. For each action report gate, recipe_id, owner, command, evidence path, PASS/HOLD. Never self-certify; `houdini_foundry.py verify` decides. Stop on any P0 stop condition."*

## 6. Execution order

| Gate | Work | Doc |
|---|---|---|
| 0 | repo + environment verification (§3) | this page |
| 1 | custom HDA → UE cook / bake / save / reload proof | `02_HDA_ENGINE_PROOF.md` |
| 2 | regenerate + promote Crystal Cathedral → `HDA_Melodia_CrystalCathedral` | `03_CRYSTAL_CATHEDRAL_HDA.md` |
| 3 | one FieldAtlas tile | `04_FOUNDRY_FIELD_ATLAS.md` |
| 4 | one Sea Above tile → UE | `05_SEA_ABOVE_TILE_BAKE.md` |
| 5 | launch tiled Sea Above bake (heavy lane) | `05_SEA_ABOVE_TILE_BAKE.md` |
| 6 | Glitter / Deposition proof while 5 runs | `06_DEPOSITION_GLITTER.md` |
| 7 | FlowVolume | `07_FLOW_VOLUME.md` |
| 8 | Volumetric Ecology (+ ocean intelligence) | `08_VOLUMETRIC_ECOLOGY.md` |
| 9 | Copernicus field integration | `09_COPERNICUS_FIELD_PIPELINE.md` |
| 10 | PDG / BakeFarm consolidation | `10_PDG_BAKE_FARM.md` |
| 11 | Faraway Mother / Vellum — only if P0 is healthy | `11_FARAWAY_MOTHER_VELLUM.md` |

Heavy bakes run beside interactive gates; never make Brennan watch a cook. Two-lane plan, fatigue-safe mode and acceptance tiers: `01_EXECUTION_ORDER.md`.

## 7. P0 stop conditions (HOLD and report)

1. `probe` not PASS / hython hangs → fix licence first.
2. College Houdini build ≠ Houdini Engine plugin build → install the matching SideFX plugin **outside the repo**, record both versions, and never hand-edit `Plugins/HoudiniEngine/`.
3. UE 5.8 / project cannot open → UE halves move to the owner PC; continue offline gates labelled SOURCE.
4. Any change needs a never-touch file (`.gitignore`, `.gitattributes`, `Config/Default*.ini`, `MF_MeshBlend_*`, `deploy/run_verify.ps1`) → ask.
5. A `deploy/*LOOP_STOP*` file exists → no writes under `/Game/EnvSandbox/`.
6. A second writer appears (second editor/Monolith, MPC write, PCG graph rewrite, live HDA overlay) → stop.
7. Same recipe gives different hashes → stop that product.
8. Anything would move the owner-authored Sea Above Landscape or `00_CANON/*` → stop.

## 8. Evidence destinations

| What | Where |
|---|---|
| Bake outputs (untracked) | `Saved/HoudiniFoundry/<recipe_id>_<seed>/[tiles/<tile_id>/]` |
| Bake manifest | `.../bake_manifest.json` (schema `melodia.houdini_foundry_bake_manifest.v1`) |
| Tracked evidence | `Saved/Audit/houdini_foundry/<recipe_id>/` — **needs `git add -f`** |
| HDAs | `hda/<Name>_<major.minor>.hda` |
| New Hython scripts | `Tools/Houdini/<family>/` — **needs `git add -f`** |
| UE assets | `/Game/Melodia/HoudiniFoundry/<Product>/` or the recipe's `ue_target.asset_path_prefix` |

## 9. Known risks

- **Plugin/build mismatch** (B1) and **UE/project availability** (B2) decide how much of Gate 1 can close at college.
- **`Tools/*` and `Saved/` are gitignored.** New scripts and evidence silently drop out of commits unless force-added. Check with `git status --ignored`.
- **`.hda`/`.vdb`/`.hip`/`.bgeo*` are not LFS-routed.** Keep committed binaries small, and leave caches off-repo.
- **`reef_common.py` is not in git.** Nine `sea_above_reef` scripts plus `copernicus_dress_bake.py` fail from a clean clone. None is on the P0 path.
- **`copernicus_cymatic_parallax.py` seeds with `hash()`**, so it is not reproducible across processes. Don't trust bit-identical regen; fixing it is ask-first.
- **"8 km" is Faraway Mother.** Sea Above bounds must be measured (Gate 4 step 1) before tiling.
- Apprentice-era limits (FBX/Alembic export blocked, watermarked renders) should not apply with the college licence. Re-probe export routes anyway and record which one cooked.

## 10. Git rules for the day

Commit only to this branch, in coherent per-gate commits, and push only with Brennan's OK. No merge to `main`, no rebase, no reset, no force-push, no history rewrite. Closeout: `13_END_OF_DAY_CLOSEOUT.md`.
