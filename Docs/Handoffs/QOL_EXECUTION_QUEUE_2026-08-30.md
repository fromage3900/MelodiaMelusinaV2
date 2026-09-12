# QOL Execution Queue — 2026-08-30 (offline triage, needs editor for T3D)

**Generated:** 2026-08-30 23:00 UTC, editor closed (PID 54700 exited 22:27, no crash)
**Sources:** `Docs/Plans/PPV_DRIFT_T3D_FIX_SPEC_2026-08-31.md` (`Saved/Audit/ppv_canonical_state_2026-08-31.json`), `Docs/Plans/GRAPH_DEAD_NODE_CLEANUP_SPEC_2026-08-31.md` (`Saved/Audit/graph_reachability_2026-08-31.md`), plus `PBR_GAPFILL_COMMIT_SPEC`, `ZENTRIM_SAKURA_SWAP_SPEC`, `ARCH_CATH_T3D_BATCH_SPEC`, `QUILL_INTERPRETER_COMMIT_SPEC` etc. authored 2026-08-30 14:00–16:00.
**Mode:** All specs are **T3D / spec-mode — no direct `.uasset` writes**. Execution requires a single live editor + Monolith 9316. This doc is offline triage only.

## 1. Ordered queue (lowest risk → highest churn)

| Order | Spec | Fixes | Risk | Blocker |
|---|---|---|---|---|
| **1** | **PPV drift** (`PPV_DRIFT_T3D_FIX_SPEC`) | 4: label `PPV_Dreamprint_Candidate`→`PPV_NikkiDream`, weights `MI_MeluColorGrade 0.18→0.69` / `MI_MelodiaInk 0.57→1.0`, replace `MI_StarryNight_VanGogh` (MD_SURFACE→MD_POST_PROCESS) with `MI_StarryNight_Hero` | Low — single actor, no gameplay code | Needs quiet editor (same modal-storm risk as mesh renames — batch save must be `unattended:true`) |
| **2** | **Dead-node cleanup** (`GRAPH_DEAD_NODE_CLEANUP_SPEC`) | 21 nodes: `BP_MelusinaJRPGCharacter` 15× Niagara `Set Variable By String (Float)`, `WBP_MelodiaQuillDialog` 5, `BP_JRPGPlayerController` 1 | Low — all `no_exec_path_from_event_entry`. The 15 Niagara nodes overlap tonight's FX review (§5e) — remove together with gate5 evidence | Re-derive live with `blueprint_query search_nodes` before removal; then compile + PIE smoke |
| **3** | **Atlantis SM_ bulk** (staged `Content/Python/org_atlantis_rename_2026-08-30.py`, `Docs/Art/MESH_NAMING_CONVENTION_2026-08-30.md`) | 333 `BldgLgPalace_A_KB3D_ATL_BldgLgPalace_A_*` → `SM_ATL_Palace_*` (0 collisions) + `violin`→`SM_violin` + 10 Kenney `MI_` | Medium — 333 redirectors, 333 dirty packages. Staged `unattended:true` to suppress checkout storm. | Editor contention (PBR lane caused 4:47 min wave 21:53) — run when quiet, verify with `validate_naming_conventions` after |
| **4** | **MI naming + trimsheet reconciliation** (`254beb3f` spec, `MI_NAMING_FIX` + Tilable/Trimsheet) | Vendor `T_` renames (~170 textures) + orphan MI archive | Medium — many packages but low reference risk | Chunk + save unattended |
| **5** | **Zentrim Sakura swap** (`ZENTRIM_SAKURA_SWAP_SPEC`, `ZENTRIM_TEXTURE_SWAP_COMMIT_SPEC`) | Sakura-named VFX/materials → Zentrim (owns the Sakura red line) | High — Sakura is a red-line art direction; spec is the only sanctioned path | Owner sign-off + no parallel material-master regenerates |
| **6** | **Arch/Cath T3D batch + Quill interpreter + PBR gapfill** (`ARCH_CATH_T3D_BATCH_SPEC`, `QUILL_INTERPRETER_COMMIT_SPEC`, `PBR_GAPFILL_COMMIT_SPEC`) | Cathedral/Atlantis MI generation, Quill interpreter wiring, PBR instance gapfill | High churn — these are the lanes that were actively saving (`MI_bling_surface_*`, `MI_Baroque_GildedFiligree_Auto*`, `MI_Arch_KB3D_ATL_*`) when this triage was written | Coordinate with the active PBR/arch lane — do not interleave bulk saves |

**Do not run 3–6 concurrently with the active PBR/arch lane.** Observed 2026-08-30: that lane held the single editor for a 4:47 min save wave and continuous `LogPython` arch-toon assignments. Two bulk-save lanes on one editor lose work (AGENTS.md 3-editor incident precedent). Queue 1→2 first (small, fast), then 3, then 5/6 when the lane is quiet.

## 2. Per-spec offline verdict

### PPV drift — READY
- Spec is complete and ordered (5 steps: label → 2 weights → replace → compile). Canonical stack is `MI_MelodiaInk 1.0`, `MI_MeluColorGrade 0.69`, `MI_StarryNight_Hero 1.0` on `PPV_NikkiDream`.
- No new files, no `.gitignore` changes, no never-touch paths.
- Execution: `python Tools/t3d_inject.py` or live Monolith, then `melodia_material_get_compile_stats` verify.
- Pre-condition: editor quiet (otherwise the post-fix save triggers the same checkout-modal batch).

### Dead-node cleanup — READY (with live re-derive)
- 15 Niagara nodes in `BP_MelusinaJRPGCharacter` are the FX-review overlap — this spec should execute in the same quiet window as gate5 so the Niagara before/after evidence is coherent.
- `WBP_MelodiaQuillDialog` 5 nodes may have been superseded by `WBP_MelodiaQuill*` widgets (`quill_ui_widgets_commit_spec`) — verify the new dialog still functions in PIE after removal.
- `BP_JRPGPlayerController` 1 node is lowest risk.
- Offline check: specs are `remove_dead_nodes` with `no_exec_path_from_event_entry` — safe to remove; no hand-edit.

### Atlantis bulk — STAGED, NOT EXECUTED
- Tonight's VFX archive (`_Archive_2026-08-30`, 9 files zero refs) already landed and is verified — this is the clean baseline for the bulk rename.
- Script `Content/Python/org_atlantis_rename_2026-08-30.py` queued once at 21:59 but editor was mid-PBR wave → backed off. Commit `38039f91` contains the script + `MESH_NAMING_CONVENTION` + `mesh_catalog` JSON.

### MI naming / trimsheet, Zentrim, Arch/Cath, Quill, PBR gapfill — TRIAGED, NOT QUEUED TONIGHT
- All authored 2026-08-30 14:00–16:00 and committed in `40c90f17`/`9e4179cf` docs batches.
- Offline verdict: specs are well-formed; execution is high-churn and collides with the live PBR/arch lane. Park behind 1→3.

## 3. Execution guardrails (from tonight's live observation)

- **Single editor, single 9316 listener.** Verified 15:00–22:27. Re-verify with `Get-Process UnrealEditor` + `netstat :9316` before any T3D.
- **Batch saves must be `unattended:true`.** `Content/EnvSandbox/*` is gitignored (`.gitignore:183`) + Git SC enabled → `InternalPromptForCheckoutAndSave` spawns one `Unable to Check Out From Revision Control!` modal per dirty gitignored package. Observed 4:47 min for ~250 PBR MIs. `GIsRunningUnattendedScript` suppresses it.
- **Verify per batch.** `validate_naming_conventions` after renames, `blueprint_query get_graph_data` after dead-node removal, `melodia_material_get_compile_stats` after PPV fix. A silent no-op and a wrong-actor move look identical.
- **No `Content/_PROJECT/` writes** — catalog-only.

## 4. Handoff

Build lane owns all T3D execution in the next quiet editor window, order 1→6 above. This doc + `Docs/Handoffs/NIAGARA_HOUDINI_FX_REVIEW_2026-08-30.md` (§5 pending live reads) + `Saved/Audit/mesh_catalog_2026-08-30.json` are the evidence for that window. No ledger row is claimed from this offline triage.

*Committed offline 2026-08-30 — live execution still requires `Tools/echo_run.py record` rows and a re-opened editor.*
