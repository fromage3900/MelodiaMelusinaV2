# 00 — Repository intake (read-only audit, 2026-09-24)

| | |
|---|---|
| **Purpose** | What already exists, what it proves, and what is stale, so the college session extends instead of rebuilding. |
| **Authority** | Reference only. `CURRENT_STATE.md` is the status authority; this page records the audit that fed the gates. |
| **Base** | Branch `prep/houdini-foundry-college-2026-09-24` cut from `origin/main` @ **`cad8272cbb42775845db3e3e2600dd4e4d2d5d56`** ("docs: Melusina handpaint ladder closeout 2026-09-24 (#320)"). Working tree clean at cut; no other branch ancestry. |
| **Executed here** | Offline only: `Tools/test_universe_foundry.py` (7/7 OK), `Tools/test_world_compiler.py` (ALL PASS), `Tools/Houdini/foundry/test_houdini_foundry.py` (10/10 OK). **No Houdini, Hython, Houdini Engine or UE was run in the audit.** |

## 1. Canonical docs inspected

`CURRENT_STATE.md` (Houdini/Hython/Copernicus lane table, Sea Above boundary, Universe Foundry row) ·
`CLAUDE.md` · `SYSTEM_MAP.md`/`DATA_FLOW.md` (routing only) · `Docs/Production/AGENT_PRODUCTION_PLAYBOOK.md` §3 ·
`Docs/Production/CANONICAL_PROJECT_PIPELINE_2026-09-08.md` · `Docs/Production/UNIVERSE_FOUNDRY_CONTRACT.md` ·
`START_HERE_TONIGHT_PI_HERMES_UNIVERSE_FOUNDRY.md` · `Docs/WorldGen/WORLD_COMPILER_CONTRACT.md` ·
`Docs/WorldGen/HOUDINI_ENGINE_SMOKE_SPEC_2026-08-27.md` · `Docs/WorldGen/TERRAIN_HANDOFF_CONTRACT.md` ·
`Docs/Production/HOUDINI_CREATIVE_PIPELINE_REFERENCE_2026-08-28.md` · `hda/README.md` ·
`Tools/Houdini/copernicus/README.md` · `Saved/Audit/cathedral/*` · `Saved/Audit/hython_monolith_bridge_report.json` ·
`Docs/Evidence/SEA_ABOVE_LEVEL_ORGANIZATION_2026-09-01.json` · `specs/schemas/world_recipe.v1.schema.json`,
`world_compiler_point_row.v1.json` · `specs/universe/*` · `specs/niagara_mpc_bindings.json`.

Source read: `Tools/world_compiler.py`, `Tools/universe_foundry.py`, `Content/Python/resonant_world_generator.py`
(`stable_int`), `Tools/Houdini/cathedral/*.py`, `deploy/surreal_arch/melodia_gn/p4_*_cathedral.py`,
`Content/Python/build_pcg_hero_resonance_cathedral.py`, `Content/Python/create_hda_arpeggio_stair.py`,
`Content/Python/smoke_houdini_engine_pcg.py`, `deploy/houdini_mcp_server.py`,
`Tools/Houdini/copernicus/copernicus_cymatic_parallax.py`, `Tools/Houdini/vdm_fabric_mountains/faraway_static_field.py`.

## 2. Systems discovered and their real proof level

| System | Proof level on `main` | Extend this — do not rebuild |
|---|---|---|
| Hython 22.0.368 | **Healthy on the owner PC** (`hython_monolith_bridge_report.json`: `hou_available`, 22.0.368, Py 3.13.10) | `Tools/Houdini/*` families |
| Houdini Engine plugin | **Present + preflight only.** `Plugins/HoudiniEngine/HoudiniEngine.uplugin` 22.0.368 / UE 5.8, enabled in `.uproject`. `smoke_houdini_engine_pcg.py` checks files exist — it never cooks. **No receipt of a custom HDA cooked/baked in UE.** | `create_hda_arpeggio_stair.py` + smoke spec §4–6 |
| Custom HDAs | **None tracked.** `hda/` holds only `README.md`. Only SideFX example HDAs under `Plugins/HoudiniEngine/Content/` | regenerate ArpeggioStair headlessly |
| Crystal/Fractal Cathedral | **Source proven.** Pure numpy scripts (no `hou` calls), deterministic (`random.Random(20260901)`), write OBJ + manifest. Manifests tracked; **OBJs not tracked**. 8 UE meshes tracked under `/Game/EnvSandbox/Meshes/Cathedral_Houdini/` | `build_fractal_cathedral.py` → `build_crystal_cathedral.py` |
| Cathedral GN twin | **Interface stub.** `MEL_p4_crystal_cathedral` declares 9 inputs then links Geometry in → out; builds no geometry | the Hython source is authority, not the GN twin |
| Song-chord cathedral | **Source/test proven, 6 stations/18 pads** (C Dm F G Am E) in `build_pcg_hero_resonance_cathedral.py` (2026-09-20). PCG placement, not geometry | `chord_for_station`, `CHORD_PROGRESS` |
| World Compiler | **Live proven (scoped) on `L_MelusinaMorning`.** `world_compiler_v1.0`, `field.kind` = `radial_bands` only; `chunk_grid` reserved as an additive version | recipe + `world_compiler.py` + `world_compiler_ue_driver.py` |
| Universe Foundry | **Source/tool proven.** Faraway Mother genome only; no Sea Above genome | mission DAG task shape (`universe_mission.v1`) |
| Faraway static field | **Source only** — first Hython-compatible field baker (RGBA: Tension / ResonanceBase / Moisture / SeamMask + hashes) | pattern for FieldAtlas manifests |
| Copernicus / cymatic maps | **Offline assets.** `copernicus_cymatic_parallax.py` is pure numpy (the name is historical); 9-map contract (BaseColor, Normal, Roughness, Metallic, Height, ORM, Emissive, Iridescence, Opacity). Real COP networks: `copernicus_dress_bake.py`, `copernicus_terrain_height_to_nanite.py` | the 9-map contract + `Content/Python/verify_tex_contract.py` |
| Sea Above | **Live proven (scoped):** 1 of 9 Resonance Ecology graphs; owner-authored Landscape + cathedral placement are canonical (`00_CANON/Landscape` 132, `00_CANON/Cathedral` 68 actors) | existing PCG graphs + `apply_resonance_to_sea_above.py` |
| Niagara / MPC | **Live proven (scoped).** Sole writers: `UMelodiaAudioReactivePresentationSubsystem` → `MPC_Melodia_Palette`; `UMelodiaCymaticsWriterSubsystem` → `MPC_Cymatics_Driver`. WC FX anchors → `NiagaraActor`s with pack User names | `fx_anchors.csv` contract, canonical effect types |
| Houdini MCP server | Read tools free; mutate tools gated by `Tools/mcp_policy.py`. Choral/groom-specific | read-only `list_hips` / `inspect_hip` |

## 3. Contradictions and stale docs

1. **`hda/README.md`** says open `hda/ArpeggioStair_1.0.hda` and reports "Smoke → PASS". The `.hda` is not in git, and that PASS is a file-existence preflight, not a cook.
2. **`WORLD_COMPILER_CONTRACT.md`** links `Docs/Houdini/MELODIA_WORLD_COMPILER_TOMORROW_SCAFFOLD_2026-08-30.md`, which does not exist.
3. **`Tools/Houdini/copernicus/README.md`** cites `Tools/verify_tex_contract.py` (actually `Content/Python/verify_tex_contract.py`) and `Tools/ingest_sea_above_p0.py` (absent).
4. **Houdini lane law #1** relies on `Tools/Houdini/sea_above_reef/probe_hython_license.ps1`, which is not in git. `houdini_foundry.py probe` replaces it (subprocess timeout + kill).
5. **`reef_common.py` is missing.** 10 tracked Python scripts (9 in `sea_above_reef/` plus `copernicus_dress_bake.py`) import it; it is swallowed by the `Tools/*` ignore rule and exists only on the owner's disk. Those scripts fail from a clean clone.
6. **`copernicus_cymatic_parallax.py` is not reproducible across processes.** It seeds with Python `hash(variant_name)`, which is salted per process (`PYTHONHASHSEED`). Also, its manifest on `main` lists 1 variant while the docs say 30 (each run overwrites it). Treat 4K "hero" regenerations as non-bit-identical until the seed uses `stable_int`.
7. **`song_chord_cathedral_both_2026-09-01.md`** calls the 6-station Am/E extension "proposed, not built". It is built (18 pads, 2026-09-20).
8. **Cathedral counts differ by bay count:** the docstring says "1364 verts, 8 bays"; the tracked manifest is 6-bay (2706 v / 2101 f); the review says 3598 v (8-bay). All are consistent only if `bays` is pinned — the recipe pins it.
9. **Cathedral knobs are not all real:** `SEED` is hardcoded (no `--seed`), rose modes are hardcoded n=8/m=6 (the GN twin exposes them as inputs), there are **no geometry groups**, and crystal UVs are all (0,0).
10. **"8 km" is Faraway Mother, not Sea Above.** `LV_FarawayMother_Prototype` is 8 × 8 km (`BOUNDS_EXTENT_UU=800000`). Measured Sea Above: 11 bounded PCG volumes, largest 83 × 15 × 17 m; nav bounds 60 × 80 m. Any "tiled Sea Above" plan must start from measured bounds.
11. **Terrain contract vs Sea Above:** `TERRAIN_HANDOFF_CONTRACT.md` requires Mesh Terrain (`classic_landscape_used: false`), but Sea Above's canonical ground is an owner-authored Landscape. So FieldAtlas is supplemental data read *from* it, never a terrain handoff *into* it.
12. **`CURRENT_STATE.md` §4** still lists "Universe Foundry expansion" as parked under the 2026-09-22 showcase override. That override was for 09-22; the owner's 09-24 instruction scopes this prep.
13. **`CLAUDE.md`** says "do not create handoff/plan files"; this pack exists by explicit owner request (precedent: `START_HERE_TONIGHT_PI_HERMES_UNIVERSE_FOUNDRY.md`). Delete or fold it into `CURRENT_STATE.md` after the session.
14. **Git hygiene traps** (protected files; owner decides): `.vdb`, `.hda`, `.hip`, `.bgeo*` are not in `.gitattributes` LFS rules (`Reef/Volumes/*.vdb` ≈1.1 MB are plain git); `.obj/.png/.exr/.fbx` are LFS. `Saved/` is ignored and `!Saved/Audit/` cannot re-include under an ignored parent, so new evidence needs `git add -f`. `Tools/*` is ignored with per-file allowlisting, so new tools also need `git add -f`.

## 4. Missing files/assets that cannot be reconstructed from Git

| Item | Reconstructable? |
|---|---|
| `Tools/Houdini/sea_above_reef/reef_common.py` | **No** — owner PC only. Blocks 10 scripts, including the real COP dress bake (not on the P0 path). |
| `Tools/Houdini/sea_above_reef/probe_hython_license.ps1` | No, but superseded by `houdini_foundry.py probe`. |
| `hda/ArpeggioStair_1.0.hda` | Yes — `hython Content/Python/create_hda_arpeggio_stair.py` (needs a licence that writes commercial `.hda`, not Apprentice `.hdanc`). |
| Cathedral OBJs (`Saved/Audit/cathedral/*.obj`) | Yes — deterministic numpy; verify counts against the tracked manifests. |
| Copernicus 4K cymatic outputs | Yes, but **not bit-identical** (see §3.6). |
| Sea Above landscape world bounds | Needs a live editor read (not in any tracked evidence). |
| Hermes venv on the college machine | Unknown. Only the owner PC path is recorded (`%LOCALAPPDATA%\hermes\hermes-agent\venv`). |
| `Plugins/HoudiniEngine/Binaries/` | Gitignored. It must be installed or built per machine for that machine's Houdini build. |

## 5. P0 blockers (carried into `01_EXECUTION_ORDER.md` stop conditions)

- **B1 — Houdini build vs plugin build.** The tracked plugin is 22.0.368 for UE 5.8. If the college Houdini is a different build, Houdini Engine will not connect until a matching plugin is installed. Gate 0 decides.
- **B2 — UE 5.8 + project availability at college.** The repo `.git` is ~24 GB with LFS content. If UE/the project cannot open there, Gate 1's UE half moves to the owner PC, and the college day produces HDA + Hython outputs only.
- **B3 — Licence.** The college full licence must show in `hserver -l` and must author commercial `.hda`.
- **B4 — `Tools/*` ignore.** Any new script not force-added is lost at commit time.
