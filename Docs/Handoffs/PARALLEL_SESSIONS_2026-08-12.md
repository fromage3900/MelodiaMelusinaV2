# Parallel sessions — paste-ready agent prompts (2026-08-12 evening)

Each block is a **standalone session start**. Copy one block into a new agent chat.
Read locks first. Claim the lane in [PARALLEL_LANES_2026-08-12.md](PARALLEL_LANES_2026-08-12.md).

**Repo:** `C:\EnvironmentPortfolio\BS_GodFile` · `main` @ `2e3c893d`  
**Board:** [PIE_RUNTIME_NOTES_2026-08-12.md](PIE_RUNTIME_NOTES_2026-08-12.md)  
**Locks:** Rhythm WORKED · Quill WORKED — do not reopen.

---

## Session D1 — Fix playtest_harness BattleUI paths (no editor)

```text
Lane D1 from Docs/Handoffs/PARALLEL_LANES_2026-08-12.md.
Repo: C:\EnvironmentPortfolio\BS_GodFile.
Do NOT open Unreal Editor.
Owner locks: rhythm + QuillScript WORKED — ignore those.
Task: Update Tools/playtest_harness.py BP_TRIES so check-wiring finds the live UI.
On disk: Content/MelodiaIntegration/UI/BP_MelodiaBattleUI.uasset
(legacy /Game/.../BP_BattleUI paths returned MISSING).
Also check JRPG template UI under Content/TurnBasedJRPGTemplate/Blueprints/UI/.
Deliverable: patched BP_TRIES + short note in Saved/Audit/harness_battleui_paths_<stamp>.md
Hand off to lane A3. Do not claim runtime gate.
```

---

## Session D2 — Battle path static audit (no editor)

```text
Lane D2 from Docs/Handoffs/PARALLEL_LANES_2026-08-12.md.
Repo: C:\EnvironmentPortfolio\BS_GodFile. No Unreal Editor.
P0: stock battles still broken on Morning → KaleidoNave / melodia_smoke_encounter.
Use Tools (scan_battle_controller.py, bp_live_path.py, Exports JSON, .umap inventory)
to produce Saved/Audit/battle_static_<stamp>.json:
- encounter tag presence
- BP_BattleController placement
- BP_MelodiaBattleUI vs BP_BattleUI LIVE path
- allowlist / StartBattle contract notes
Do not delete assets. Do not reopen Quill/rhythm locks.
```

---

## Session D3 — Stale doc sweep (no editor)

```text
Lane D3 from Docs/Handoffs/PARALLEL_LANES_2026-08-12.md.
Repo: C:\EnvironmentPortfolio\BS_GodFile. Docs only.
Grep for stale claims: "highway unverified", "WillScript verify owed", "Quill should work",
"PRs #4/#6 still open", "never observed in PIE" for highway.
Add forward pointers to:
  Docs/Handoffs/RHYTHM_GAME_LOCKED_2026-08-12.md
  Docs/Handoffs/QUILLSCRIPT_LOCKED_2026-08-12.md
  Docs/Handoffs/PARALLEL_LANES_2026-08-12.md
Do not rewrite old dated history blocks; mark STALE → see lock.
Do not commit unless owner asks.
```

---

## Session D4 — Echo / QuillSmoke spec validate (no editor)

```text
Lane D4 from Docs/Handoffs/PARALLEL_LANES_2026-08-12.md.
Repo: C:\EnvironmentPortfolio\BS_GodFile.
Run: python Tools/echo_run.py validate-spec Content/MelodiaIntegration/Narrative/MelodiaQuillSmoke.qsc --live-allowlist
Capture stdout to Saved/Audit/quill_smoke_validate_<stamp>.txt
Quill is OWNER LOCKED WORKED — this is packaging hygiene, not re-proof.
Report pass/fail only. No editor.
```

---

## Session A1 — Stock battle path (EDITOR — exclusive)

```text
Lane A1 from Docs/Handoffs/PARALLEL_LANES_2026-08-12.md. EDITOR EXCLUSIVE.
Before start: Get-Process UnrealEditor → exactly one PID; Monolith :9316 up.
If another agent holds the editor, STOP and wait.
Repo: C:\EnvironmentPortfolio\BS_GodFile. Board: Docs/Handoffs/PIE_RUNTIME_NOTES_2026-08-12.md
LOCKED — do not work: rhythm highway, QuillScript “does it work”.
P0 goal: make/prove stock battle on route Morning → KaleidoNave.
Encounter: melodia_smoke_encounter + BP_BattleController + StartBattle.
UI: BP_MelodiaBattleUI (not missing BP_BattleUI legacy path).
Idle WalkForward previously never set bIsMoving — prefer Quill notify path MelodiaQuillSmoke
melodia:battle:melodia_smoke_encounter if volume walk fails.
Deliverable: Saved/Audit/battle_path_<stamp>/ with log excerpts + frames if any.
Update PIE board with exact fail point or success. Hand A2 if battle-end reachable.
```

---

## Session A2 — MELODIA_RECOVERY evidence (EDITOR — after A1)

```text
Lane A2 from Docs/Handoffs/PARALLEL_LANES_2026-08-12.md. EDITOR EXCLUSIVE.
Requires A1 battle-end (or controlled battle-over).
Goal: capture log MELODIA_RECOVERY restored N… (PR #6 already on main).
Do not reimplement RestoreParty. Evidence only under Saved/Audit/recovery_<stamp>/.
Update PIE board. Then free the editor.
```

---

## Session A3 — Formal runtime harness (EDITOR — after D1 + A1)

```text
Lane A3 from Docs/Handoffs/PARALLEL_LANES_2026-08-12.md. EDITOR EXCLUSIVE.
Preconditions: D1 harness path fix merged/applied; A1 battle/rhythm skill reachable.
Campaign: Docs/ECHO/campaign_01_rhythm_damage_delta.md
Run playtest_harness with FULL map path and real keys (not probe-only).
A/B: rhythm on vs melodia.Rhythm.Disable 1 (Decision 024).
Then record_gate.py runtime pass|fail with JSON beside frames.
Owner rhythm LOCK ≠ ledger row. Do not fake a pass from probe.
```

---

## Session A4 — Content tree triage (read-first; editor only if needed)

```text
Lane A4 from Docs/Handoffs/PARALLEL_LANES_2026-08-12.md.
Prefer no editor. Map LIVE vs ORPHAN battle UI / _ThirdParty / MelodiaIntegration mirrors
using bp_live_path.py. Soft refs (Quill) always look empty — Decision 049.
Deliverable: docs matrix + explicit owner questions before ANY delete.
No deletes in this session.
```

---

## Session B0 — GN Stack sections fix (Blender) — DONE

```text
DONE 2026-08-12 19:48. Saved/Audit/melodia_studio_sections_2026-08-12_1948.md
Health: sections=12/12 section_trees=165. Do not re-run Sync & Reload on an old session.
```

## Session B1 — Review_Queue ↔ Studio sections parity (Blender) — DONE

```text
DONE 2026-08-12 19:48. Saved/Audit/melodia_studio_parity_2026-08-12_1948.md
RQ_MEL_*=165 matches Studio. Never save stage without MELODIA_ALLOW_STAGE_SAVE=1.
```

---

## Session B2 — Website plate dry-run (Blender or tools)

```text
Lane B2 from Docs/Handoffs/PARALLEL_LANES_2026-08-12.md.
Website root: my-site-clean via Tools/melodia_website_root.py
stage_publish: git push OFF by default. Dry-run only unless owner says push.
Deliverable: Saved/Audit/site_publish_dry_<stamp>.json
```

---

## Session C1 — Optional PR triage (cloud/git)

```text
Lane C1 from Docs/Handoffs/PARALLEL_LANES_2026-08-12.md. No editor.
Repo MelodiaMelusinaV2. Triage draft PRs #3 and #5 only.
Squash-only merges; do not self-approve as sole reviewer if policy blocks — use owner/admin path.
Do not open gameplay PRs that fight A1. Report status table only unless owner says merge.
```

---

## Session E1 — Materials audit (no master rewrite)

```text
Lane E1 from Docs/Handoffs/PARALLEL_LANES_2026-08-12.md.
No gameplay editor. Follow .kiro/specs/material-library-improvements/ and BACKLOG Next #1.
Audit Universal A/B/C, landscape Nikki scale, water param groups — no master rewrites.
Deliverable: Docs/Reports or Saved/Audit note. Do not touch BP_Battle* or Quill.
```

---

## Session E2 — Baroque PCG *Ex (art lane)

```text
Lane E2 from Docs/Handoffs/PARALLEL_LANES_2026-08-12.md.
PCG Baroque *Ex spline unblock (CorniceEx pattern; BalconyEx / NaveVaultEx).
Prefer docs + graph work that does not need the gameplay Unreal session.
If editor required, wait until Group A releases the slot.
```

---

## Session T1 — ZenTrim hero assign (editor already open — do not spawn)

```text
Lane T1 from Docs/Handoffs/TONIGHT_CONTINUATION_HANDOFF_2026-08-12.md.
UnrealEditor PID 38184 is A1 — do NOT start a second editor.
If A1 has released the slot, in that same editor run:
  py Content/Python/assign_hero_zentrim.py --apply
Creates MI_ZenTrim_Base4K, assigns slot 0 on SM_Retopo_wand + SM_SM_StreetLamp.
Do not assign Magicians T_Lantern. Do not use T_Hatch_Cross. Skip cross (no mesh).
Evidence: Saved/Audit/hero_zentrim_assign.json
```

---

## Session T2 — Cathedral kit import (A idle only)

```text
Lane T2. One UnrealEditor. Import KitbashExport/CathedralKit/*.fbx (41 files)
into /Game/EnvSandbox/Meshes/Cathedral/. Place in L_KaleidoNave.
Inventory: Saved/Audit/p0_level_mesh_gaps_2026-08-12.md
Do not resurrect L_Melodia_Dreamstate. Do not reopen rhythm/Quill.
```

---

## Session T3 — Water-hair Layer C bake (Blender 5.2)

```text
Lane T3 from Saved/Audit/water_hair_layer_c_runbook_2026-08-12.md.
Owner must restart Blender 5.2 first. N → BlenderMCP → Connect 9876.
Do not replace SK_MelusinaHair. Do not save v22 without MELODIA_ALLOW_STAGE_SAVE=1.
1) exec tune_melusina_hair_drip.py
2) Flip bake 1–96 @ 72 into KitbashExport/flip_cache_melusina_waterhair
3) exec export_melusina_hair_flip_alembic.py
Expect ~96 .bobj then GC_MelusinaHairFlip_v22.abc
```

---

## Coordinator sticky (owner / lead agent)

```text
You are the parallel coordinator for Melodia 2026-08-12 evening.
Authority: Docs/Handoffs/PARALLEL_LANES_2026-08-12.md + PARALLEL_SESSIONS_2026-08-12.md
Locks: rhythm WORKED, Quill WORKED — protect them.
Spawn order: D1 D2 D3 D4 C1 E1 B1 in parallel; A1 when editor free; A2→A3 after.
Update the claim table when agents start/finish. Block any second UnrealEditor.
Summarize blockers to the owner in ≤10 lines when asked.
```
