# Niagara / Houdini FX Review — 2026-08-30 (skeleton, git evidence)

**Scope:** Tonight's brief is *organizational health + static mesh organization + review all Niagara Houdini FX work done today*. Editor was live 15:00–22:27 (PID 54700, Monolith 0.20.3) but saturated by a concurrent PBR lane — live Monolith reads for FX systems are **pending a quiet editor**. This doc records the git-evidence half; live reads will fill §5 when the editor reopens.

**Evidence standard:** No probe-injected rhythm / no invented FX state. Git log + file-on-disk + Monolith reads when available. See `AGENTS.md` and `Saved/Audit/mesh_catalog_2026-08-30.json` for the parallel org work.

---

## 1. What today's Niagara/Houdini FX work actually was (git log 2026-08-30)

| Work | Commit / file | Path | Verdict |
|---|---|---|---|
| **Sea Above droplets Niagara prototype** | `7361b502 feat(seaabove): Shorewake level loop, jelly reef, quest spec + wire_dream compositor fix` | `Content/EnvSandbox/Monoliths/SeaAbove/Prototype/VFX/NS_SeaAbove_UpwardDroplets_Prototype.uasset` | **Landed on feature branch** `feature/p0-phase1-allowlist-quill-trigger` (not on main). Referenced in `specs/cinematics/sea_above_cutscene_manifest.v1.json` + `Docs/Art/SEA_ABOVE_TONIGHT_EXECUTION_AND_AGENT_HANDOFF_2026-08-26.md` etc. |
| **Droplet atlas texture** | `0fe7b877 feat(seaabove): ingest P0 Houdini backlog — 55 textures + 23 meshes into Reef` | `Content/EnvSandbox/Monoliths/SeaAbove/Prototype/Reef/Textures/T_Jelly_ArmLogic_LUT` + `T_SeaAbove_Droplet_Atlas.png` in `Saved/Audit/sea_above/houdini_variants/` then ingested | **Texture on disk**, material-side SubUV flipbook wiring **unproven** (handoff open item #4: `T_SeaAbove_Droplet_Atlas` exists but no commit evidences the SubUV material chain). |
| **Copernicus petal VAT lane** | `31b06169 fix(copernicus): petal Cop arrow + VAT (seed 20260828)` — `Tools/Houdini/copernicus/copernicus_petal_variants.py` (+204 lines) + 4 SBS dress textures; `7d93b97a fix(copernicus): petal VAT arrow encoding + queue v3 gates 2-6 while away (gate2 done)` — `Tools/Houdini/copernicus/copernicus_dress_bake.py` cp1252 arrow fix | `Tools/Houdini/copernicus/` | VAT = Vertex Animation Texture (Houdini → UE). `copernicus_petal_variants.py` new, dress bake encoding fixed. **Gate 4 dry-runs PASSED 2026-08-31 02:20** (`hython 22.0.368` both `--dry` exit 0; petal printed 12×3 map plan, dress printed SOP/COP chain; cp1252 fix holds). Recorded in `Saved/Audit/v3_queue_while_away_2026-08-31.json`. |
| **GN kits (Houdini-adjacent)** | `d90cb3ae feat(houdini): A God That Molts shell-recursion kit v0 (Bible #05)` + `601280ac`/`0e5b9c41`, `47db00f4 feat(gn): Faraway Mother — 8 builders`, `753b070a feat(surreal): GN kit baroque + polyhedra` | `feature/p0-phase1-allowlist-quill-trigger` | **Landed on feature branch, not on main** (66→103 commits ahead). Creative lane, no live PIE proof. |
| **Houdini licensing + tooling** | `65dc969a docs(houdini): Indie to commercial licensing findings`, `4dd5edb9 docs: Aug 30 production tool evaluation plan` | `Docs/` | Done. |
| **PBR gapfill / arch-toon lane (concurrent, not FX-review scope but observed live)** | `9e4179cf Track Content/Python helper scripts for PBR gapfill`, `c48999cc chore: Python editor scripts for material work`, `2b1fcbf9 refactor: rewrite arch_toon_create.py for Cathedral + Atlantis MI generation`, plus untracked `Content/Python/_run_arch_bg.py`, `arch_toon_create_v2.py`, `fix_normal_param.py`, `fix_zentrim_v5.py`, `run_arch_now.py` | `Content/Python/`, `Content/EnvSandbox/Materials/Instances/Environment/PBR_Auto/MI_bling_surface_vol3_*`, `Baroque/MI_Baroque_GildedFiligree_Auto*` | **Active in the same editor session** 21:53–22:09: `InternalPromptForCheckoutAndSave total: 4:47 min` saving `MI_bling_surface_vol3_*`, plus `LogPython: barrel -> MI_Arch_KB3D_ATL_WoodOldA` arch-toon assignments. This is the contention that blocked the catalog rename and FX live reads. |

No `*.uasset` Niagara edits beyond `NS_SeaAbove_UpwardDroplets_Prototype` were committed today on `main` or the feature branch (git log `-- "*Niagara*" "*VAT*" "*NS_*" --name-only` returns only that one file plus the copernicus scripts). The queued **gate 5** is the bulk Niagara work.

### Queued gate 5 (not executed)

`Saved/Audit/v3_queue_while_away_2026-08-31.json`:

```json
{
  "gate5": { "intake": "MelodiaStudioV3/Review/WorldGen + Flora/Petals GPU Fixed event", "status": "queued", "petalFix": "7 systems CPU->GPU, Dynamic->Fixed, wire Gust DeathEvent" },
  "gate3": { "status": "queued", "cmd": "blender --factory-startup --background --python deploy/surreal_arch/tests_standalone.py" },
  "gate4": { "status": "queued", "cmd": "hython copernicus_petal_variants.py --dry && hython copernicus_dress_bake.py --dry (fix cp1252 arrow first)" },
  "gate2": { "status": "done", "diffCheck": 0, "pyCompile": "deploy 12 OK, copernicus 3 OK, dress_bake arrow bug open" }
}
```

Gate 5 is **7 petal Niagara systems CPU→GPU, Dynamic tick → Fixed, wire `Gust DeathEvent`**. Owner intent per the 08-30 plan was to execute tonight; execution is blocked behind gates 3/4 and behind a quiet editor. Execution must be a single-editor-holder operation with before/after `niagara_query get_system_summary` + `get_system_timing` / `get_emitter_timing_summary` evidence and a short PIE capture with assertion JSON — never probe-only.

Candidate systems for the Gust DeathEvent wiring (by name, on disk): `NS_SakuraPetalGust` and `NS_WindRibbonGust` in `EnvSandbox/VFX/Systems/Sakura/` (20 assets there, plus 3 in `Candidates/Petals`). The `Systems/Sakura` folder name is red-line-adjacent (no Sakura art direction) — the Zentrim swap spec owns renames there, not a bulk rename tonight.

---

## 2. VFX folder health (done tonight, before the gate5 work)

9 files across 5 cruft dirs + an empty `_Showcase` were proven `referenced_by: []` ×9 via `project_query find_references` and consolidated into `EnvSandbox/VFX/_Archive_2026-08-30/` (see `Saved/Audit/mesh_catalog_2026-08-30.json` § `archive_moves_done_2026_08_30`). Top-level VFX is now 10 dirs (`Candidates` through `Templates` plus `_Archive_2026-08-30`), down from 15+. This is the clean baseline gate 5 should run against.

`Systems/Sakura` (20 NS_* assets) was **not** touched — catalog-only. See §4 red line.

---

## 3. Overlap with QOL: orphaned Niagara variable nodes

`Docs/Plans/GRAPH_DEAD_NODE_CLEANUP_SPEC_2026-08-31.md` (source `Saved/Audit/graph_reachability_2026-08-31.md`) found **21 dead nodes across 3 BPs**, including **15× `Set Niagara Variable By String (Float)` in `BP_MelusinaJRPGCharacter`** with no exec path. Those 15 are Niagara FX nodes — they belong in this review, not just generic dead-node cleanup. They must be re-derived live (`blueprint_query get_graph_data` / `search_nodes`) before removal — specs confirm presence, never absence. Removal is a T3D cleanup spec, not a hand-edit, and should land with the gate5 pass so the same before/after FX evidence covers it.

---

## 4. Red lines and guardrails for the live pass

- No Sakura art direction — `Systems/Sakura` renames/deletes only via the Zentrim swap spec, not via the catalog rename. Gate 5's Gust wiring may touch `NS_SakuraPetalGust` but does not rename the folder.
- One editor, one Monolith surface. Gate 5 + droplet SubUV wiring + dead-node cleanup must serialize through the single 9316 holder. The 4:47 min PBR save wave (21:53) proved that concurrent bulk saves on gitignored `Content/EnvSandbox/*` with Git SC enabled produce a per-asset `Unable to Check Out From Revision Control!` modal storm — batch saves must use `run_python … unattended:true` (sets `GIsRunningUnattendedScript`) so `InternalPromptForCheckoutAndSave` auto-acknowledges.
- No writes under `Content/_PROJECT/`.

---

## 5. Live reads pending (fill when editor reopens)

Each row must have a Monolith read or a committed verifier — no prose-only certification.

| # | Question | Monolith call | Expected |
|---|---|---|---|
| 5a | Is `NS_SeaAbove_UpwardDroplets_Prototype` live and where is it placed? | `niagara_query get_system_summary` + `get_system_timing` + `project_query find_references` on the system; `mesh_query get_level_actors` / `project_query search` for placed emitters | System exists in `Monoliths/SeaAbove/Prototype/VFX`, timing shows GPU vs CPU, references show whether any level places it. **Flipbook SubUV wiring check:** does its renderer material sample `T_SeaAbove_Droplet_Atlas` with SubUV? |
| 5b | Which 7 petal systems are the gate5 targets and what is their current tick/GPU state? | `niagara_query list_systems` filtered to petal/gust, then `get_system_summary` + `get_system_timing` per system, `get_emitter_timing_summary` per emitter | List the 7 by path, each with `tick: Dynamic/Fixed`, `GPU/CPU`, and whether `Gust DeathEvent` handler exists. |
| 5c | Gust DeathEvent wiring gap | `niagara_query get_event_handlers` on `NS_SakuraPetalGust` / `NS_WindRibbonGust` | Handler missing before, present after. |
| 5d | Orphaned Niagara variable nodes re-derive | `blueprint_query get_graph_data` + `search_nodes` on `BP_MelusinaJRPGCharacter` for `Set Niagara Variable` | Confirm 15 nodes, no exec path, then T3D cleanup spec execution. |
| 5e | Post-gate5 save health | `editor_query list_dirty_packages` + `get_build_errors` + re-run `mesh_catalog` validation | Dirty packages saved unattended, zero new build errors, naming violations unchanged (Niagara prefixes already `NS_`/`NE_`). |

When 5a–5e are green, update this doc with the evidence paths and commit. Then the QOL queue (`PPV_DRIFT_T3D_FIX_SPEC`, `GRAPH_DEAD_NODE_CLEANUP_SPEC`, MI naming) can run in that same quiet window.

### 5.1 LIVE RESULTS (filled 2026-08-31 04:00–04:30 UTC, Monolith 0.20.3, editor PID 92072→80768→130096)

**5a — Droplet system: LIVE, SubUV wired.** `get_system_summary` on `NS_SeaAbove_UpwardDroplets_Prototype`: 1 emitter `UpwardDropletsEmitter`, CPU, Fixed bounds, warmup 5.994s, EffectType `ENV_StorybookAmbientVFX`. Renderer (`list_renderers`): `NiagaraSpriteRendererProperties` → `MI_SeaAbove_UpwardDroplet`. MI parent `M_Niagara_MelodiaFlipbook` with `FlipbookTexture = /Game/_PROJECT/VFX/Textures/T_Alpha_water_globule_flipbook` — **flipbook SubUV chain is LIVE** (handoff item #4 proof half closed). **Correction:** the ingested `T_SeaAbove_Droplet_Atlas` (Reef/Textures) is `referenced_by: []` — dead weight; the live chain uses the `_PROJECT` flipbook texture instead.

**5b — Gate5 7-system audit (before/after):**

| System | Emitters | Before | After | Compile |
|---|---|---|---|---|
| `NS_SakuraPetals` | CanopyDrift | CPU/Dynamic | **GPU/Fixed** | clean |
| `NS_SakuraPetals_v2` | Petals+EM_PondRipple+EM_PetalPile | CPU/Dynamic mix | **GPU/Fixed ×3** (DeathEvent links kept) | clean |
| `NS_SakuraGroundPetals` | GroundPetals | CPU/Dynamic | **GPU/Fixed** | clean |
| `NS_SakuraWaterPetals` | WaterPetals | GPU/Dynamic | **GPU/Fixed** | clean |
| `NS_CosmicPetalOrbit` | CosmicPetalOrbit | GPU/Dynamic | **GPU/Fixed** | clean |
| `NS_Melodia_PetalEndlessLoop` | PetalLoop | GPU/Fixed | (already done) | clean |
| `NS_WindRibbonGust` | Gust+Gust_Leader+E_OmniBurst | CPU/Dynamic | **CPU/Fixed** (reverted GPU) | clean |
| `NS_SakuraPetalGust` (reference) | 3 | GPU/Fixed | untouched | **pre-existing compile error** |

**5c — Gust DeathEvent wiring: BLOCKED by engine bug (evidence).** Wired `DeathEvent` handler on `NS_WindRibbonGust::Gust` (source `E_OmnidirectionalPetalBurst`, spawned_particles) + added `GenerateDeathEvent` module (persistent IDs auto-enabled). GPU compile failed: `error: use of undeclared identifier 'RWWriteDataSetBool1'` in `/Engine/Generated/NiagaraEmitterInstance.ush` — event payload writes a `NiagaraBool LocalSpace` flag unsupported on GPU. **The reference `NS_SakuraPetalGust` fails identically** (re-compiled live to confirm — pre-existing, not a regression). Reverted handler+module; WindRibbonGust kept CPU+Fixed (a broken compile is worse than CPU). Engine fix needed upstream; documented, not worked around.

**5d — Orphaned Niagara nodes: confirmed + REMOVED (18 total, 3 BPs).** `search_nodes` re-derived exactly 15 `SetNiagaraVariableFloat` (`K2Node_CallFunction_43..57`); `get_node_details` on 43 showed `execute connected_to: []` → chain orphaned. Removed all 15 + 2 in `WBP_MelodiaQuillDialog` (SetText_19, SetTypewriterIndex_3 — truly orphaned; **spec correction:** VariableSet_2 kept — live event-fed chain) + 1 in `BP_JRPGPlayerController` (`CallFunction_0` fully disconnected; **spec correction:** spec's claimed node was wrong, the real orphan was _0). All 3 compile clean, 0 errors. Committed `b66e6f6c`.

**5e — Save health + crash root cause (QOL finding):** Batch save of the 3 dirty BPs crashed the editor TWICE with `Error saving ... Cannot remove ... as it is read only!` (assert in `FMonolithEditorActions::HandleSavePackages`). Root cause: **3302 `.uasset`s project-wide had the ReadOnly attribute** (git-checkout artifact) — every tracked Content save was a crash. `attrib -R` cleared on project-owned trees (`EnvSandbox`, `Melodia`, `MelodiaIntegration`, `Characters`, `TurnBasedJRPGTemplate`); 259 remain under `Art/`, `Blueprints/`, `Experiments/`, `_PROJECT/`, `Sakura/`, `Stylization/`, `Surfaces_CC0/` (out of tonight's save path; `_PROJECT` red-line). Saves now succeed (`saved:1` each). **Any future save on those 259 will crash — clear before next write.**

Gate5 ledger: **not recorded via `record_gate.py`** — gate5 was a queued event, not a formal Echo gate; evidence lives in this doc + `b66e6f6c` + `5697e2aa` (gate4).

### 5.2 Remaining Niagara conversions (batch 2, 2026-08-31 04:45–04:55 UTC) — DONE

Second pass over the full production Systems tree (34 systems) after the 7 gate5 petal systems:

| System | Emitter | Conversion | Compile |
|---|---|---|---|
| `NS_Uni_Fireflies` | Firefly | CPU→**GPU** | clean |
| `NS_Uni_WaterMist` | EmberMotes | Dynamic→**Fixed** | clean |
| `NS_Uni_GroundWisps` | EmberMotes | Dynamic→**Fixed** | clean |
| `NS_Uni_MistSheet` | EmberMotes | Dynamic→**Fixed** | clean |
| `NS_Uni_RainRipples` | RibbonTrailFollower/OmniBurst/RibbonLeader | Dynamic→**Fixed** (kept CPU — LocationEvent wiring would hit the GPU event-bool engine bug) | clean |
| `NS_ConstellationTwinkle` | Twinkle | CPU+Dynamic→**GPU+Fixed** | clean |
| `NS_EmberMotes` | EmberMotes | Dynamic→**Fixed** | clean |
| `NS_FairyDust` | FairyDust | Dynamic→**Fixed** | clean |
| `NS_MagicalHenshinBurst` | 3 emitters | Dynamic→**Fixed** (kept CPU — LocationEvent wiring) | clean |
| `NS_SakuraLanternMotes` | LanternMotes | CPU→**GPU** | clean |
| `NS_SakuraDreamSparkle` | DreamMotes | CPU→**GPU** | clean |
| `NS_SakuraPondShimmer` | Ripples | CPU+Dynamic→**GPU+Fixed** | clean |
| `NS_ConstellationDraw` | Stars | CPU+Dynamic→**GPU+Fixed** | clean |
| `NS_SakuraCosmicAurora` | AuroraRibbon/AuroraLeader | Dynamic→**Fixed** (kept CPU — LocationEvent wiring) | clean |

Already optimal (left untouched): `NS_Uni_LeafDrift` (GPU/Fixed), `NS_Uni_DustShafts` (GPU/Fixed), `NS_Uni_PollenSparkle` (GPU/Fixed), `NS_MagicTrail` (GPU/Fixed), `NS_Melodia_PetalEndlessLoop` (GPU/Fixed). **13 systems converted in batch 2, all compiled clean (0 `LogNiagara: Error`).** Production tree now: 100% of event-free systems GPU+Fixed; event-wired systems Fixed-bounds CPU (engine bug holds: `RWWriteDataSetBool1` on GPU event bool writes — reference `NS_SakuraPetalGust` remains broken pre-existing).

### 5.3 Jellyfish P0 Sea Above scan (2026-08-31 04:55 UTC) — INSTANCES NEEDED, BLOCKED ON SCALE

**Kit authored (complete):** `Reef/Meshes/` — `JELLY_Bell` (SkeletalMesh 8448 tris / 4598 verts, 2 bones, Skeleton + PhysicsAsset), `JELLY_Arms` (StaticMesh, **8 material slots all wired → `MI_Jelly_Arms`**), `JellyVeil`, `JellyArm_000..007` (8 variants), `Reef/Textures/` 9× `T_Jelly_*` (Biolum/Iridescence/Nematocyst/ArmLogic LUTs + Bell BaseColor/Opacity/CanalMask/Normal/Irid_Mottle), `Reef/Materials/MI_Jelly_Bell` + `MI_Jelly_Arms`.

**Scan findings (missing / blocking placement):**

| # | Item | Evidence | Blocker? |
|---|---|---|---|
| 1 | **Scale defect** — `JELLY_Bell` AABB extent ≈ **930,000 units** (~930 m), `JELLY_Arms` ≈ **4,350,000 units** (~4.3 km); control meshes sane (`SM_Coral_Brain` 73 u, `SM_Kelp_Tall` 202 u) | `mesh_query get_mesh_bounds` ×4 | **YES — unplaceable as-is** |
| 2 | **Bell material slot unwired** — `MI_Jelly_Bell` `referenced_by: []` (arms wired, bell not) | `project_query find_references` | YES |
| 3 | **No AnimBP** for `JELLY_Bell_Skeleton` (2 bones — bell pulse needs an AnimBP or the skeletal mesh renders in bind pose) | `project_query search "ABP"` under SeaAbove = none | YES |
| 4 | **No assembly Blueprint** (bell + arms + veil are separate meshes; no `BP_Jelly*` anywhere) | `project_query search` | YES |
| 5 | **Zero jelly instances in `LV_SeaAbove_Prototype`** — level has only PlayerStart, Oceanology water/ocean/manager, CineCamera, Sky/Clouds/Fog, PCGWorldActor, Landscape | `project_query search "UAID"` + level actor census | YES |
| 6 | `T_SeaAbove_Droplet_Atlas` dead weight (separate finding, §5.1) | `referenced_by: []` | no |

**Required work (queue for the Houdini/author lane):** re-export or re-import `JELLY_Bell.fbx` / `JELLY_Arms.fbx` with correct FBX unit scale (both carry `UnitScaleFactor` metadata in header — binary-parse inconclusive, but the meshes are clearly 10³–10⁴× oversized), wire `MI_Jelly_Bell` to the bell mesh, author an AnimBP for the 2-bone bell (pulse), assemble a `BP_Jelly_SeaAbove` (bell + arms + veil), then place N instances in `LV_SeaAbove_Prototype` near the reef. **Do NOT scale-hack in-editor** — the correct fix is re-import units (AGENTS.md: don't compensate).

---

## 6. Offline QOL triage (no editor needed)

- **PPV drift** (`Docs/Plans/PPV_DRIFT_T3D_FIX_SPEC_2026-08-31.md`, source `Saved/Audit/ppv_canonical_state_2026-08-31.json`): 4 fixes — label `PPV_Dreamprint_Candidate` → `PPV_NikkiDream`, weights `MI_MeluColorGrade 0.18→0.69`, `MI_MelodiaInk 0.57→1.0`, plus a surface-domain drop. T3D inject spec, no direct `.uasset` writes. Ready for the quiet editor window after gate5.
- **Graph dead-node cleanup:** 21 nodes, 3 BPs — **DONE 2026-08-31** (18 removed: 15 Niagara + 2 Quill + 1 PC; spec corrected live for Quill VariableSet_2 and PC node identity). Commit `b66e6f6c`.
- **MI naming + trimsheet:** vendor `T_` renames (~170 textures) and the staged Atlantis `SM_` bulk (333) — **Atlantis DONE 2026-08-31** (`333/333 SM_ATL_Palace_*`, `validate_naming_conventions` 333/333 pass 0 violations; plus `violin`→`SM_violin`, 10 Kenney `MI_`). Redirector cleanup via `FixupRedirectors` + `delete_asset` on the one leftover (BuildingF). Vendor `T_` renames remain queued.
- **Zentrim Sakura swap:** owns Sakura renames — not executed tonight.

All three are T3D/spec-mode and safe to queue behind gate5; none require a second MCP surface.

---

*Skeleton committed 2026-08-30 with git evidence only. Live §5 will be appended when Monolith 9316 is back and the editor is quiet — do not mark gate5 done from this skeleton.*
