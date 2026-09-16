# Melodia Stabilization — Execution Plan (2026-09-14, updated in-depth)

Owner intent: #201 superseded by merged #213 (main @ fe4dcc04). PR #214 (codex/stabilization-20260913 @ b3527f10, Echo Static Gates GREEN) carries the guard + ledger + scaffold + UI inventory + narrow 52-package identity closure. This plan lands it, then clears the remainder. I execute; owner decides where marked OWNER.

## 0. Ground rules (binding, every phase)
- Never push to main, force-push, or rewrite history. All work in isolated worktrees; never checkout/reset/stash in the busy main tree at C:/EnvironmentPortfolio/BS_GodFile (dirty sheep/hair/wardrobe/player work stays in place, untouched).
- Protected files (.gitignore, .gitattributes, Config/DefaultEngine.ini, Config/DefaultGame.ini, MF_MeshBlend_*, deploy/run_verify.ps1) need explicit owner sign-off per change; commits touching them use `SKIP_PROTECTION=1` with the approval cited in the message. Pre-commit hook rule 6 is the enforcer.
- Never commit personal/school/career docs. Deleting assets is RED: ask first, receipt before prune.
- Prove C++ with closed-editor Build.bat (Live Coding lies); prove gameplay with PIE in MelodiaIntegrationMap, additive fixtures only, single editor on port 9316, one MCP surface.
- Done per item = merged PR with CI green, or a written owner-decision list, plus one updated row in CURRENT_STATE.md. Report 3 lines per item.
- Remote ops always `git -c http.version=HTTP/1.1`; LFS budget gate must pass before push.

## 1. Current verified baseline (do not re-prove, reuse)
- main = fe4dcc04 (Merge #213: rhythm HUD tokens, 2 Quill widgets, qsc allowlist test update, zero-neutral skiff hull dials, Sea Above prototype actors + 2 PCG styles; 68 files, no docs/Saved).
- #214 = b3527f10 on codex/stabilization-20260913: guard `Tools/guard_collapsed_paths.py`, `Docs/Evidence/BRANCH_LEDGER_2026-09-13.json` (58 live + 3 stale cached refs; 22 merged-equivalent / 36 unique-work), chapter scaffold + 4-beat `03_tide_listening`, UI inventory (144 widgets / 955 styled in CURRENT_STATE §3), narrow closure (52 LFS packages: 7 frozen PPV + MPC_Ink/Palette + ET_Melodia_CharacterFX + 3 WaveHarp_R07 + exact recursive deps; exact-file .gitignore exceptions, no wholesale Cinematics unignore). Closed-editor UE5.8 build 460/460. Echo Static Gates SUCCESS on b3527f10.
- Open PRs: #214 CLEAN/MERGEABLE, #145 CLEAN, #144 CLEAN, #205 + #194 DIRTY/CONFLICTING.
- Known reds deliberately retained: full QSC contract FAILS on 3 pre-existing SkiffDeparture IDs (quest.shorewake.passage, flag.shorewake.passage, reward.skiff_passage) absent from the DA; collapse/scaffold regressions 2/2 PASS; offline contracts 22/22 PASS.
- Main-tree dirty: sheep retarget/ABP/hair/wardrobe/player edits (cleanup/pbr-twin-landing-2026-09-10) — preserve, never touch from other worktrees.
- Editor: closed at last check (no UnrealEditor process; :9316 SYN_SENT only = no listener). G: dry-run receipt: 119.75 GiB / 55,549 files + descriptor to G:/BS_GodFile_Mirror/20260913, zero failures. Real mirror NOT run.

## 2. Phase A — Land #214 (no new scope)
1. Re-verify #214 tip: `git -C <stab-worktree> status` clean; `gh pr view 214 --json mergeable,mergeStateStatus`; `gh run list --branch codex/stabilization-20260913` all success. If main moved since, rebase in the worktree only (`git fetch origin && git rebase origin/main`), resolve DU deletions by taking upstream deletion and re-homing additions; never merge main into the branch.
2. Confirm the staged closure is exactly the approved set: 52/52 LFS pointers (`git diff origin/main..HEAD --name-only`), `.gitignore` adds exact files only, CURRENT_STATE row present. MF_MeshBlend_Activator_Index_0 rides as a recursive dep — call it out in the PR body as the protected-file exception already approved 2026-09-14.
3. Hand owner the merge: report diff shape (+52 assets LFS, .gitignore +107 lines exceptions-only, CURRENT_STATE row) and the exact merge command for THEIR hand (or --admin bypass note if protection is unsatisfiable: single-collaborator self-approval is blocked by GitHub). I do not merge.
4. Post-merge: fetch, verify each landed path on main via `gh api .../contents/<path>` (frozen PPV ×7, ET, 3 WaveHarp, guard, scaffold, ledger), record tip SHA. If verification fails, report, do not re-push.

## 3. Phase B — Branch archaeology closeout (OWNER decisions)
1. Publish the ledger as the decision instrument (already on #214). For each of the 36 unique-work branches: file list + reconcile-or-close recommendation. For 22 merged-equivalent: content proof (`diff --name-status origin/main <branch> | grep '^A'` empty + subject match) + close recommendation.
2. Do NOT close anything myself. Deliver the list; owner marks close/reconcile. On approval: close via `gh pr close` / `git push --delete` only the approved refs, with a prune receipt in Docs/Audits/ (branch + tip SHA + proof). Stale cached refs: `git remote prune origin` after confirming via `ls-remote`.
3. CI guard (on #214): `Tools/guard_collapsed_paths.py` fails any PR re-adding paths deleted by 08a608bc, renames included, on every PR. Verify green on #214; do not weaken it.

## 4. Phase C — SkiffDeparture allowlist gap (3 failing IDs)
1. In a fresh isolated worktree (never the busy tree), read live DA truth via reflection (`get_cdo_properties` on DA_MelodiaIntegrationConfig), not the stale helper. Confirm absence of quest.shorewake.passage / flag.shorewake.passage / reward.skiff_passage.
2. OWNER choice, two paths: (a) add the 3 IDs to the DA in-editor + recompile affected .qsc + rerun `test_qsc_allowlist_contract` to green; (b) rule them retired and rewrite the 02_shorewake_calling beats to already-allowlisted IDs. I will not substitute unrelated IDs silently — (b) changes chapter meaning and needs owner word.
3. Execute the chosen path through the editor (single owner lane, PIE in MelodiaIntegrationMap additive-only), then commit test + DA-adjacent source proof. Evidence: unittest PASS + ledger row only if a gate is claimed (prose is not a row).

## 5. Phase D — UI staleness (melodia-ui-artist skill, editor-gated)
1. Reference is the tokenized rhythm HUD. P0-visible candidates already listed: BP_MelodiaBattleUI RhythmGradeText/SongPickLabel white; stock BP_BattleUI KeyboardLegend #F2D69E; WBP_MainMenu near-palette text; WBP_MenuButton label #F2D69E. Rest in CURRENT_STATE §3 (incl. Defeat near-black, Victory zero-alpha — check runtime bindings first; white image tints/transparent shadows are NOT auto-defects).
2. Take the single editor lane only when no other session owns it (verify: one UnrealEditor process, one :9316 listener, `list_dirty_packages` + `list_errored_blueprints` clean before editing). Fix P0-visible widgets only; everything else stays a listed row, not a drive-by redesign. No hand-edits to .uasset — editor path only.
3. Proof: before/after audit diff + PIE screenshot pair with assertion JSON beside the frames (frames without a report are not evidence).

## 6. Phase E — G: saved-state mirror (real run, last)
1. Preconditions, all verified in-session before the run: source saved + editor CLOSED (temp Oceanology/Claireon junctions already removed from the worktree; confirm absent), dry-run log re-run fresh (`Tools/mirror_saved_project.ps1` default dry-run), owner approves the summary.
2. Scope: Content/ (incl. Frozen + Cinematics R07 only), Config/, Source/, Plugins/*/Source, Saved/Audit, Chapters/, specs/, Tools, design tokens. Exclude Intermediate/, DerivedDataCache/, Binaries/, Blender autosaves. Destination G:/BS_GodFile_Mirror/20260913 (new dated folder; older mirror preserved). robocopy /MIR with dry-run log first, show summary, then real run only on approval.
3. Post-run: record byte/file counts + zero-failure line into CURRENT_STATE G: row. The mirror reflects the saved local tree including uncommitted assets — never present it as "equals main."

## 7. Phase F — Chapters: prove the example (no framework essays)
1. Import `03_tide_listening` (4 beats) per the scaffold runbook; prove in MelodiaIntegrationMap PIE: both choices, revisit idempotency (ConsumedIntentIds no-op on replay), save → full restart → load round-trip. Additive fixtures only.
2. Record evidence JSON beside any frames + the harness that produced both. No gate claimed without a `Saved/gate_ledger.json` row via the Echo record path.

## 8. Execution order + stop rules
Order: A (hand over merge) → B (owner list) + C (owner choice) in parallel-readiness, D when editor lane is free, F after C, E last (stable saved source). Stop and report after each phase; never chain a state-changing git command behind a `cd`; verify branch pointer immediately before every commit (another lane may move it); if a push is rejected as behind, diagnose via reflog, push to a fresh allowed-prefix ref, never force.

## 9. Acceptance
Each of branches / identity / chapters / UI / G-mirror ends as: merged PR with CI green, or a signed owner-decision list, plus one CURRENT_STATE.md row. Final report: 3 lines per item, with SHAs, counts, and what remains open. Personal/school docs never committed; sheep-tree work never touched; main never pushed by me.
