# Niagara / Houdini FX Review — 2026-08-30 (skeleton, git evidence)

**Scope:** Tonight's brief is *organizational health + static mesh organization + review all Niagara Houdini FX work done today*. Editor was live 15:00–22:27 (PID 54700, Monolith 0.20.3) but saturated by a concurrent PBR lane — live Monolith reads for FX systems are **pending a quiet editor**. This doc records the git-evidence half; live reads will fill §5 when the editor reopens.

**Evidence standard:** No probe-injected rhythm / no invented FX state. Git log + file-on-disk + Monolith reads when available. See `AGENTS.md` and `Saved/Audit/mesh_catalog_2026-08-30.json` for the parallel org work.

---

## 1. What today's Niagara/Houdini FX work actually was (git log 2026-08-30)

| Work | Commit / file | Path | Verdict |
|---|---|---|---|
| **Sea Above droplets Niagara prototype** | `7361b502 feat(seaabove): Shorewake level loop, jelly reef, quest spec + wire_dream compositor fix` | `Content/EnvSandbox/Monoliths/SeaAbove/Prototype/VFX/NS_SeaAbove_UpwardDroplets_Prototype.uasset` | **Landed on feature branch** `feature/p0-phase1-allowlist-quill-trigger` (not on main). Referenced in `specs/cinematics/sea_above_cutscene_manifest.v1.json` + `Docs/Art/SEA_ABOVE_TONIGHT_EXECUTION_AND_AGENT_HANDOFF_2026-08-26.md` etc. |
| **Droplet atlas texture** | `0fe7b877 feat(seaabove): ingest P0 Houdini backlog — 55 textures + 23 meshes into Reef` | `Content/EnvSandbox/Monoliths/SeaAbove/Prototype/Reef/Textures/T_Jelly_ArmLogic_LUT` + `T_SeaAbove_Droplet_Atlas.png` in `Saved/Audit/sea_above/houdini_variants/` then ingested | **Texture on disk**, material-side SubUV flipbook wiring **unproven** (handoff open item #4: `T_SeaAbove_Droplet_Atlas` exists but no commit evidences the SubUV material chain). |
| **Copernicus petal VAT lane** | `31b06169 fix(copernicus): petal Cop arrow + VAT (seed 20260828)` — `Tools/Houdini/copernicus/copernicus_petal_variants.py` (+204 lines) + 4 SBS dress textures; `7d93b97a fix(copernicus): petal VAT arrow encoding + queue v3 gates 2-6 while away (gate2 done)` — `Tools/Houdini/copernicus/copernicus_dress_bake.py` cp1252 arrow fix | `Tools/Houdini/copernicus/` | VAT = Vertex Animation Texture (Houdini → UE). `copernicus_petal_variants.py` new, dress bake encoding fixed. **Gate 4 dry-runs (`hython … --dry`) still queued** in `Saved/Audit/v3_queue_while_away_2026-08-31.json`. |
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

---

## 6. Offline QOL triage (no editor needed)

- **PPV drift** (`Docs/Plans/PPV_DRIFT_T3D_FIX_SPEC_2026-08-31.md`, source `Saved/Audit/ppv_canonical_state_2026-08-31.json`): 4 fixes — label `PPV_Dreamprint_Candidate` → `PPV_NikkiDream`, weights `MI_MeluColorGrade 0.18→0.69`, `MI_MelodiaInk 0.57→1.0`, plus a surface-domain drop. T3D inject spec, no direct `.uasset` writes. Ready for the quiet editor window after gate5.
- **Graph dead-node cleanup:** 21 nodes, 3 BPs — the 15 Niagara nodes above plus 5 in `WBP_MelodiaQuillDialog` and 1 in `BP_JRPGPlayerController`. T3D cleanup spec, ready.
- **MI naming + trimsheet:** vendor `T_` renames (~170 textures) and the staged Atlantis `SM_` bulk (333) are the same execution pattern — chunk, `unattended:true`, verify via `validate_naming_conventions`.
- **Zentrim Sakura swap:** owns Sakura renames — not executed tonight.

All three are T3D/spec-mode and safe to queue behind gate5; none require a second MCP surface.

---

*Skeleton committed 2026-08-30 with git evidence only. Live §5 will be appended when Monolith 9316 is back and the editor is quiet — do not mark gate5 done from this skeleton.*
