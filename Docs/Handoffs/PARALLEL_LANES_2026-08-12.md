# Parallel agent lanes — 2026-08-12 evening (post rhythm + Quill locks)

**Supersedes for new work:** [PARALLEL_LANES_2026-08-08.md](PARALLEL_LANES_2026-08-08.md) (keep for history; do not start A1 “observe rhythm” from that file).

**Living board:** [PIE_RUNTIME_NOTES_2026-08-12.md](PIE_RUNTIME_NOTES_2026-08-12.md)  
**Locks (do not reopen):** [RHYTHM…](RHYTHM_GAME_LOCKED_2026-08-12.md) · [QUILL…](QUILLSCRIPT_LOCKED_2026-08-12.md)  
**Paste-ready sessions:** [PARALLEL_SESSIONS_2026-08-12.md](PARALLEL_SESSIONS_2026-08-12.md)  
**Repo tip:** `main` @ `2e3c893d` · PC root `C:\EnvironmentPortfolio\BS_GodFile` · remote `MelodiaMelusinaV2`

---

## Hard rules (read before claiming a lane)

1. **One Unreal Editor.** `Get-Process UnrealEditor` → exactly one PID. Port **9316** → one Monolith. Three editors crashed the project on 2026-08-08.
2. **Owner locks are ground truth.** Rhythm **WORKED**. QuillScript **WORKED**. Do not “re-verify” or “fix highway/Quill” as P0.
3. **Done = ledger or named evidence path.** Prose “done” without `Saved/gate_ledger.json` row or an audit JSON under `Saved/Audit/` is not done for gate work.
4. **No force-push / no `git checkout -- .` / no deletes without owner sign-off.** Soft-ref Quill assets look orphaned to hard-ref tools (Decision 049).
5. **Claim your lane** in the claim table below (or `_TASK_QUEUE.md`) before writing contended files.

---

## What’s already green (do not steal cycles)

| Item | State |
|------|--------|
| PRs #4 + #6 | Squash-merged |
| Closed-editor build after pull | PASS |
| Rhythm game / highway | **OWNER LOCK WORKED** |
| QuillScript / WillScript | **OWNER LOCK WORKED** |
| `static_gates` | PASS (`0e34eaed`) |
| Melodia Studio 5.2 / Review_Queue populate | Landed earlier same day |
| Melodia Studio GN Stack sections + RQ parity | **B0/B1 DONE** (`12/12`, `165`) — cockpit is start-here |

---

## Contended resources

| Group | Resource | Concurrency |
|-------|----------|-------------|
| **A** | UE editor + Monolith `:9316` | **ONE lane at a time** |
| **B** | Blender 5.2 + Melodia Studio | parallel (one Blender each) |
| **C** | Website / git (no editor) | parallel; coordinate PRs |
| **D** | Tools / docs / specs (no editor) | fully parallel |
| **E** | Materials / PCG audits (read-heavy; editor only if A free) | prefer no-editor |

Before any **A** lane: confirm no other agent holds the editor.

---

## GROUP A — UE editor (serialize)

### A1 — Stock battle path (P0) — **OWNER HOLDS / highest priority when editor free**
**Goal:** Morning → KaleidoNave stock encounter actually starts and ends.  
**Route:** `L_MelusinaMorning` → **KaleidoNave** (no live `L_Melodia_Dreamstate`).  
**Encounter:** tag `melodia_smoke_encounter` + `BP_BattleController` + `StartBattle` contract.  
**UI truth:** harness looked for `BP_BattleUI` (MISSING). Live sibling: `Content/MelodiaIntegration/UI/BP_MelodiaBattleUI.uasset`.  
**Deliverable:** PIE evidence (frames or log) that battle starts; note exact fail point if not.  
**Gate / evidence:** `Saved/Audit/battle_path_<stamp>/` + board update on PIE notes.  
**Do not:** reopen Quill/rhythm locks; do not delete content trees.

### A2 — RestoreParty / recovery log
**Depends on:** A1 reaching battle-end (or force a controlled battle-over).  
**Goal:** Log line `MELODIA_RECOVERY restored N…` (or documented no-controller warning).  
**Code already on main:** PR #6 wiring via `BP_BattleController`.  
**Deliverable:** excerpt from editor log + audit JSON.  
**Do not:** re-implement RestoreParty; only exercise and evidence.

### A3 — Formal `runtime` harness packaging
**Depends on:** A1 path reachable enough for real keys (or document HOLD with reason).  
**Goal:** `python Tools/playtest_harness.py run --map /Game/EnvSandbox/Environments/L_KaleidoNave --backend auto` with **real** Q/W/O/P (not probe-only), assertion JSON beside frames, then `record_gate.py runtime pass|fail`.  
**Also:** point harness paths at `BP_MelodiaBattleUI` (text fix can start in **D1** before editor).  
**Campaign:** `Docs/ECHO/campaign_01_rhythm_damage_delta.md` (A/B = rhythm on vs `melodia.Rhythm.Disable 1`).  
**Do not:** treat owner rhythm lock as substitute for ledger row.

### A4 — Duplicate battle UI / content-tree triage (editor optional; prefer read-first)
**Goal:** Map LIVE vs orphan `BP_BattleUI` / `_ThirdParty` / mirror trees with `bp_live_path.py`.  
**Deliverable:** written matrix + owner ask before any delete.  
**Do not:** delete untracked mirrors.

---

## GROUP B — Blender / Melodia Studio (parallel with A if different machine; else when A idle)

**Full Blender session pack:** [BLENDER_MELODIA_STUDIO_HANDOFFS_2026-08-12.md](BLENDER_MELODIA_STUDIO_HANDOFFS_2026-08-12.md)

### B0 — GN Stack sections fix (P0 Studio UX) — **DONE** 2026-08-12 19:48
**Evidence:** `Saved/Audit/melodia_studio_sections_2026-08-12_1948.md` — `sections=12/12 section_trees=165`.  
**Do not** click Sync & Reload until the next Blender restart (old operator crashed 5.2; timer fix is on disk).

### B1 — Melodia Studio health + GN Review_Queue parity — **DONE** 2026-08-12 19:48
**Evidence:** `Saved/Audit/melodia_studio_parity_2026-08-12_1948.md` — `RQ_MEL_*=165` matches Studio.

### B2 — Website plate publish dry-run
**Goal:** N-panel Render/Upload dry path to `my-site-clean`; git push **OFF** by default.  
**Tools:** `Tools/melodia_website_root.py`, `deploy/surreal_arch/stage_publish.py`.  
**Deliverable:** dry-run JSON under `Saved/Audit/`.

### B3 — Cockpit doc smoke list — **DONE**
Cockpit header is the Blender start-here (v22 path, MCP vs LiveLink, Health line, GN Stack smoke).

---

## GROUP C — Git / cloud / phone (no editor)

### C1 — Optional PRs #3 / #5
Triage draft PRs; squash-only; do not touch gameplay critical path without owner.

### C2 — Commit doc locks + this parallel pack
Stage handoff/doc updates only (no secrets, no giant blends). Owner must ask for commit/push.

### C3 — PhoneOps hygiene
Keep `Docs/PhoneOps/BACKLOG.md` aligned with this file’s Now list.

---

## GROUP D — Tools / specs (fully parallel, no editor)

### D1 — Fix `playtest_harness` BattleUI paths
**File:** `Tools/playtest_harness.py` (`BP_TRIES`).  
**Change:** include `/Game/MelodiaIntegration/UI/BP_MelodiaBattleUI` (and any live JRPG UI path).  
**Deliverable:** `check-wiring` → not MISSING when editor up later.  
**Hand off to A3.**

### D2 — Battle-path static audit (no PIE)
Inventory KaleidoNave encounter tag, controller placement, allowlist entries via existing Tools (`scan_battle_controller.py`, `bp_live_path.py`, exports). Write `Saved/Audit/battle_static_<stamp>.json`.

### D3 — Docs / DOC_INDEX / stale “highway unverified” sweep
Grep and patch remaining stale claims that contradict rhythm/Quill locks (do not rewrite history sections; add “stale → see lock” notes).

### D4 — Echo / campaign prep
Ensure `echo_run.py validate-spec` on `MelodiaQuillSmoke.qsc` still green; refresh campaign precondition notes only if needed.

---

## GROUP E — Materials / PCG / art (read-heavy)

### E1 — Material library audit (no master rewrite)
Per BACKLOG Next #1 — Kiro specs under `.kiro/specs/material-library-improvements/`.

### E2 — Baroque PCG `*Ex` spline unblock
Docs-only or graph work that does **not** require the gameplay editor session.

---

## GROUP T — Tonight portfolio / Studio / P0 art (closed-editor done; live gated)

**Handoff:** [TONIGHT_CONTINUATION_HANDOFF_2026-08-12.md](TONIGHT_CONTINUATION_HANDOFF_2026-08-12.md)

### T1 — ZenTrim on hero meshes
**Done (apply 23:28):** `MI_ZenTrim_Base4K` created and assigned slot 0 on wand + StreetLamp. Magicians skipped. Evidence: `Saved/Audit/hero_zentrim_assign.json` + `Saved/Audit/ue_idle_apply_2026-08-12.md`.

### T2 — Four P0 level mesh gaps
**Done (import 23:35):** 41/41 `SM_Cathedral_*` uassets in `/Game/EnvSandbox/Meshes/Cathedral/`. 8-piece `CathedralKit_Review` strip spawned in `L_KaleidoNave` at Y=4500 — **umap not saved**. Evidence: `Saved/Audit/cathedral_fbx_import.json`.

### T3 — Water-hair Layer C
**Done (GC import 23:28):** `/Game/Cinematics/MelusinaWaterHair/GC_MelusinaHairFlip_v22` is a GeometryCache. Leave `SK_MelusinaHair` + `MI_Melusina_WaterHair` + `ABP_Melusina_WaterHair` as gameplay. Socket a new cine actor to head.

### T4 — Lean vow-cross FBX
**Blocked** on v22. Never `T_Hatch_Cross`.

---

## Claim table (edit when you start / finish)

| Lane | Agent / model | Status | Started | Evidence path |
|------|---------------|--------|---------|---------------|
| A1 Battle path | | open | | |
| A2 Recovery log | | blocked on A1 | | |
| A3 Runtime harness | | blocked on A1 (D1 done) | | |
| A4 Content triage | | open | | |
| B0 Studio sections fix | | **DONE** | 19:48 | `Saved/Audit/melodia_studio_sections_2026-08-12_1948.md` |
| B1 RQ ↔ sections parity | | **DONE** | 19:48 | `Saved/Audit/melodia_studio_parity_2026-08-12_1948.md` |
| B2 Plate dry-run | | open | | |
| B3 Cockpit docs | | **DONE** | | cockpit |
| C1 PR triage | | open | | |
| C2 Doc commit | | owner-gated | | |
| D1 Harness paths | parent | **done** 20:40 | `Saved/Audit/harness_battleui_paths_2026-08-12.md` |
| D2 Battle static | | open | | |
| D3 Stale-doc sweep | | open | | |
| D4 Echo prep | | open | | |
| E1 Materials | | open | | |
| E2 PCG Ex | | open | | |
| T1 ZenTrim heroes | parent | **applied** 23:28 | `Saved/Audit/hero_zentrim_assign.json` |
| T2 P0 mesh gaps | parent | **41/41 imported** 23:35; KaleidoNave strip unsaved | `Saved/Audit/cathedral_fbx_import.json` |
| T3 Water-hair C | parent | **GC imported** 23:28 | `Saved/Audit/hair_flip_geometry_cache_import.json` |
| T4 Cross FBX | | blocked on 5.2 | | |

---

## Suggested spawn order (max parallelism)

```text
NOW (parallel):  B0 + D1 + D2 + D3 + D4 + C1 + E1
EDITOR SLOT:     A1 → A2 → A3 (after D1 lands)
BLENDER NEXT:    B1 parity → B2 plates → B3 docs
WHEN A IDLE:     A4
OWNER:           C2 commit when pack looks good
```

---

## Anti-goals

- Re-proving rhythm highway or Quill “from scratch”
- Second UnrealEditor / second Monolith
- Probe-only `runtime` pass claims
- Deleting `_ThirdParty` or Quill soft-ref assets without owner
- Saving portfolio stage blends without `MELODIA_ALLOW_STAGE_SAVE=1`
