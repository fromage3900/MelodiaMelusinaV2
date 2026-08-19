# Session Handoff — 2026-08-19 (parallel day plan)

**Execute:** [`Docs/Handoffs/TODAY_2026-08-19_PARALLEL_PLAN.md`](Docs/Handoffs/TODAY_2026-08-19_PARALLEL_PLAN.md)

| Lane | Now | Work |
|---|---|---|
| **A (no editor)** | NOW | pull main → Nemotron Phase 0 → 1a smoke → T3 grep |
| **B (editor open)** | Background OC | 1b T1 Monolith → Phase 2 T1/T4/T5 × 3 models |
| **C (editor closed)** | Owner | Claireon worktree + build + connect |
| **D (new session)** | After Claireon | T8 context cost (Monolith vs Claireon, alternate sessions) + GH issue |
| **E (PIE window)** | When free | VS P0 real-key runtime gate |

Research: [`NEMOTRON_OPENCODE_UE_RESEARCH_2026-08-19.md`](Docs/Handoffs/NEMOTRON_OPENCODE_UE_RESEARCH_2026-08-19.md) · Spec: `specs/nemotron_experiment_harness.json` · T3 ground truth: `Saved/Audit/nemotron_harness_2026-08-19/ground_truth/T3_handle_quill_notification.json`

Applications today (parallel to A): **Digital Extremes** (Junior/Intermediate) + **Promethean AI**.

---

# Session Handoff — 2026-08-19 (Nemotron × OpenCode × Unreal research)

**Pick up:** [`Docs/Handoffs/NEMOTRON_OPENCODE_UE_RESEARCH_2026-08-19.md`](Docs/Handoffs/NEMOTRON_OPENCODE_UE_RESEARCH_2026-08-19.md)

- **Research DONE:** Nemotron model lineup, OpenCode integration (Ultra broken via NIM #34026),
  Unreal public evidence (ACE runtime NPC; no OpenCode+Monolith public example yet).
- **Experiments DESIGNED:** Tasks 4–7 (harness compare, long-context, MCP surface, background agent).
- **Spec:** `specs/nemotron_experiment_harness.json`
- **Tonight:** Phase 0–2 — OpenRouter smoke, then T1/T4/T5 on Claude vs Nemotron Super.
- **Do not use Nemotron Ultra via NIM in OpenCode** until #34026 fixed; OpenRouter only.

---

# Session Handoff — 2026-08-12 ~23:36 ET (UE idle apply)

Owner released A1. **T1/T2/T3 landed** in PID **38184**. Evidence: [`Saved/Audit/ue_idle_apply_2026-08-12.md`](Saved/Audit/ue_idle_apply_2026-08-12.md).

- `MI_ZenTrim_Base4K` on wand + StreetLamp. Magicians skipped.
- Cathedral **41/41** under `/Game/EnvSandbox/Meshes/Cathedral/`. KaleidoNave folder `CathedralKit_Review` (8 pieces, Y=4500) **unsaved**.
- Geometry Cache `/Game/Cinematics/MelusinaWaterHair/GC_MelusinaHairFlip_v22`. Do not replace `SK_MelusinaHair`.
- Save KaleidoNave if the strip should persist. Socket a new cine GC actor to head.

---

# Session Handoff — 2026-08-12 ~23:20 ET (Website Overhaul & Security)

**Pick up:** [`Docs/Handoffs/SESSION_HANDOFF_2026-08-12_WEBSITE_OVERHAUL.md`](Docs/Handoffs/SESSION_HANDOFF_2026-08-12_WEBSITE_OVERHAUL.md)

- **Website Overhaul & Security:** 100% AI purge, meta CSP headers, 232 hex errors resolved (0 token errors), Figma UI suite integrated (15 icons, combat cards, swatch boards, mobile viewport frame), Vite MPA config + TS modules (`src/ts/`).
- **Gates:** `npm run verify:all` **PASSED** (0 errors, 0 facts issues).

---

# Session Handoff — 2026-08-12 ~22:53 ET (live 5.2 MCP)

Blender **5.2** PID **27644**, MCP **9876** connected. v22 open. **Not saved.**

- Health: `builders=165 menu=165 sections=12/12 section_trees=165` presets 24/0 orphans.
- Smoke: `MEL_effect_magic` LIQUID applied (`MEL_Smoke_EffectMagic_LIQUID` cube — undo before plates).
- Hair tune: `drip_inside_domain=true`. Domain moved ΔZ **-1.34**. Strand.002 is CURVES (script patched). **0 `.bobj`** — bake still owner step.
- **GN background:** `GN_BG_Prototype` 15 builders (frame rebuilt as plane). **Not saved.**
- **Flip bake:** 480 `.bobj` frames 1–240. Alembic `Exports/MelusinaWaterHair/GC_MelusinaHairFlip_v22.abc` (1–96). Import as Geometry Cache cine actor when A1 idle.

---

# Session Handoff — 2026-08-12 ~20:40 ET (tonight continuation)

**Pick up:** [`Docs/Handoffs/TONIGHT_CONTINUATION_HANDOFF_2026-08-12.md`](Docs/Handoffs/TONIGHT_CONTINUATION_HANDOFF_2026-08-12.md)

- Handpainted hunt **done** (1208 hits). Komikaze stills are not albedo.
- P0 umaps exist. Cathedral kit = 41 FBX, **0** uassets. No vow-cross mesh.
- `assign_hero_zentrim.py` disk inventory written. `--apply` waits — UnrealEditor **PID 38184** (A1).
- Flip cache still **0 `.bobj`**. Alembic helper: `Tools/export_melusina_hair_flip_alembic.py`.
- D1: `playtest_harness.py` now tries `BP_MelodiaBattleUI` first.
- Blender MCP **down**. Loop PID **26352** — do not start a second.
- Do not save v22 without `MELODIA_ALLOW_STAGE_SAVE=1`. Rhythm + Quill still LOCKED WORKED.

---

# Session Handoff — 2026-08-12 evening (Blender Melodia Studio)

**Blender start-here:** [`Docs/BLENDER_MELODIA_COCKPIT.md`](Docs/BLENDER_MELODIA_COCKPIT.md)

- **B0/B1/B3 DONE.** Live v22 Health: `sections=12/12 section_trees=165`. `RQ_MEL_*=165`. Audits under `Saved/Audit/melodia_studio_*_2026-08-12_1948.md`.
- **Do not** click **Sync & Reload** until the next 5.2 restart (old operator crashed the GUI; timer fix is on disk + AppData).
- After restart: **N → BlenderMCP → Connect** on **9876** (not Live Bridge).
- Stage: `G:\EnvironmentPortfolio\BS_GodFile\Melodia_Portfolio_Stage_v22_ZenRebuild_WIP.blend`. No agent save without `MELODIA_ALLOW_STAGE_SAVE=1`.
- Still open on Blender: **B2** website plate dry-run (git push off).
- Builder click: `mel_gn.stack_add` no longer requires `Object.mel_gn_stack` (modifier still applies).

---

# Session Handoff — 2026-08-12 evening (RHYTHM + QUILL LOCKED)

```
✧ RHYTHM + QUILLSCRIPT WORKED — tell the whole family ✧
```

**Rhythm lock:** [`Docs/Handoffs/RHYTHM_GAME_LOCKED_2026-08-12.md`](Docs/Handoffs/RHYTHM_GAME_LOCKED_2026-08-12.md)  
**Quill lock:** [`Docs/Handoffs/QUILLSCRIPT_LOCKED_2026-08-12.md`](Docs/Handoffs/QUILLSCRIPT_LOCKED_2026-08-12.md)  
**PIE board (living):** [`Docs/Handoffs/PIE_RUNTIME_NOTES_2026-08-12.md`](Docs/Handoffs/PIE_RUNTIME_NOTES_2026-08-12.md).  
**Parallel spawns:** [`Docs/Handoffs/PARALLEL_LANES_2026-08-12.md`](Docs/Handoffs/PARALLEL_LANES_2026-08-12.md) · paste prompts [`PARALLEL_SESSIONS_2026-08-12.md`](Docs/Handoffs/PARALLEL_SESSIONS_2026-08-12.md).

- **Owner LOCK:** Rhythm game **WORKED** · QuillScript / WillScript **WORKED** (owner “yes”). Do not reopen either.
- **Merge / pull DONE.** #4 + #6 squash-merged; `main` @ `2e3c893d`; closed-editor build PASS.
- **Still open:** P0 stock battles (Morning → KaleidoNave / collider); formal `record_gate.py runtime` packaging; `MELODIA_RECOVERY…`.
- **`static_gates` PASS** (`0e34eaed`). Playable levels on `main` (`43d0a9ae`).

---

# Session Handoff — 2026-08-12 (source-control hardening + lane dispatch)

**Session type:** repo/backup audit, gitignore fix, agent handoffs. **No editor or UE writes.**
**Repo:** `main` @ `43d0a9ae`, tracking `v2/main`. **Two writers active this session** (this lane
+ Muse). Read `Docs/Reports/BACKUP_SYNC_AUDIT_2026-08-12.md` first.

## What changed

- **`43d0a9ae` — the playable route levels are now under version control.** `L_MelusinaMorning`
  and `L_KaleidoNave` had **no history at all**; the `Content/*` blanket in `.gitignore` never had
  a matching un-ignore. KaleidoNave is the only level in which a battle has ever started. Also
  tracked: `Content/Melodia/{Levels,PCG}/**`, `Content/EnvSandbox/{Environments,PCG}/**` —
  214 files, ~48 MB LFS. Bulk EnvSandbox art (~4.6 GB) stays ignored on purpose; the reasoning is
  written into `.gitignore` so a future cleanup does not undo it.
- **`0e34eaed` (Muse lane) — `static_gates` moved from FAIL to PASSING.** 12 material drifts
  accepted, graph_reachability/bp_sweep scoped to shipped defects.
- **LFS budget funded** — ~$10 ≈ 50 GB as of today. The 512 MB per-change CI gate still applies.

## Two corrections to earlier docs on this date

1. **`BP_BattleController` and `BP_BattleUI` were always tracked** (`.gitignore:128-134`). The
   first version of the backup audit said otherwise; that came from a `git check-ignore` against a
   path missing the `/Battle/` segment. No asset was ever at risk.
2. **`SK_Melusina` needed nothing.** One live mesh, at `Content/Characters/Melusina/`, already
   tracked. The `Content/Art/` and `Content/Melodia/Characters/` copies are stale leftovers.

## Gates

`runtime` **fail** (honest) · `static_gates` **pass** (new today) · `save_load`,
`repeat_consume`, `package_launch` **open**. 13 earlier gates pass. `release_tag.yml` correctly
refuses to cut a release until the four completion gates have rows.

**The `runtime` gate needs the editor and real Q/W/O/P keys through `BP_BattleUI::OnKeyDown`.**
No agent lane can close it. Everything dispatched below exists to shorten that editor session.

## Active lanes

| Lane | Handoff | Owns |
|---|---|---|
| **Muse** (WSL2, host) | `Docs/Handoffs/MUSE_HANDOFF_2026-08-12.md` | Code edits. M1 wire `RestorePartyAfterBattle` (zero callers today — the real gap), M2 `lane_dispatcher.py` queue, M3 memory index, M4 split AGENTS.md, M5 commit 13 loose `surreal_arch` modules |
| **DeepSeek** (cloud, read-only) | `Docs/Handoffs/DEEPSEEK_HANDOFF_2026-08-12.md` | Verdicts only. D1 save idempotency, D2 result matrix, D3 input-path chain for `MELODIA_RHYTHM session=`, D4 Q/W/O/P ergonomics |

Lane separation table is in the DeepSeek handoff §"Lane separation". Muse owns `Source/**` and
`Tools/**`; DeepSeek writes new `Docs/Reports/*_VERDICT_*.md` files only.

## Open owner decisions

1. **Rotate the Figma API key** — public on v2, doc redacted in `87b2938d`, live key still valid.
   Carried from 08-11, still open.
2. **Four `WP/` portfolio levels are G:-only** — BaroqueGrotto, CosmicOrrery, SakuraDream,
   SpaceCathedral. No version history, no C: copy. Cheap to promote now the budget is funded;
   needs a call on whether they are current or superseded.
3. **`G:` has 2.1 GB free of 1 TB.** The next mirror pass will fail partway.
4. **Two Quaternius animation dependencies are absent** from every C: and G: copy searched and
   from the tracked tree. These appear genuinely lost.

## Working-tree leftovers (not committed)

13 new + 3 modified `deploy/surreal_arch/melodia_gn/` Python modules (Muse M5), `.agents/`, and
~15 root scratch scripts (`check_bp*.py`, `fix_rhythm*.py`, `pie_*.py`, `pie_smoke_*.json`) —
session debris, propose a `.gitignore` line rather than deleting.

---

# Previous session (2026-08-11) — agent infrastructure, intake, repo v2, UI fix

**Session type:** Multi-agent infra expansion + read-only intake + repo migration + editor fix
**Project phase:** UE 5.8 production JRPG + QuillScript integration

---

# Evening fold-in (2026-08-11, git reconciliation + cloud-research fold-in)

Full record: `Docs/Handoffs/CLOUD_RESEARCH_FOLD_IN_2026-08-11.md` — read that first.

- **Git:** `main` @ `69f76813`, 4 ahead of `v2/main`, 0 behind. Working tree clean of real changes.
  14 MeshBlend LFS pointers were cosmetic-only (identical OIDs) — un-staged, never committed.
  3 nebula LFS blobs still pending push to v2 (`Blue_Nebula_8`, `Purple_Nebula_6/7`).
- **Committed this session:** `69f76813` — tool hardening (input-node ENTRYISH, AssetRegistry
  discovery, canonical live-path, named-graph reachability) across bp_live_path/bp_sweep/echo_run/
  graph_reachability/ui_lint. Addresses several `ENVIRONMENT_BUILD_VALIDATION_2026-08-11.md`
  static-gate findings (AMBIGUOUS on canonical path, input-chain dead islands).
- **Cloud-research lanes folded in:** SuperGrok planning docs (recreated in `Docs/PhoneOps/` by
  Cursor iOS), 6-lane intake fan-out (`Saved/Intake/`), jcode study + acceptance
  (`Docs/Reports/`), cathedral rig correction (**target v22, NOT FinalUERig43**), setup validation.
- **Loose ends recorded (§3 of fold-in):** `lane_dispatcher.py` reads the wrong queue
  (`NEXT_ACTIONS.md` is platform, not gameplay); `Saved/memory_index.json` stale; `dispatch_report.md`
  never generated; **Figma key rotation required by owner**; AGENTS.md >32 KB subagent cap;
  video_review_lane free-tier vision 402s; Q/W/O/P 6-key hand-shift → test in Campaign 1.
- **Branches:** all `origin/*` = website repo (not v2). `recovery/melodia-main-sync-20260811` is a
  STALE cold snapshot (would revert quarantine + delete .jcode/.opencode) — keep as backup, never
  merge. `fix-melodiacore-source` already merged via PR #54. Surreal slices = loop spam, #80 open.
- **Ledger unchanged:** `runtime` = FAIL honest, three gates OPEN. No row written by this pass.

## Agent infrastructure (new, all committed to v2)

- **Model fleet (9 MCP servers in root `.mcp.json` + 11-model router fleet in `Tools/model_router.py`):** fixed `kimi-k3-free`
  (host is `api.tokenrouter.com/v1`, NOT the dead `tokenrouter.ai`), fixed stale slug
  `deepseek/deepseek-v4` → `deepseek/deepseek-v4-flash`, added Mistral Medium 3.5, Grok 4.5,
  Grok 4.20 multi-agent, Meta Muse Spark 1.2 (age-confirm blocked), Nemotron Ultra free
  (1M ctx), gpt-oss-20b free. `Saved/router_ledger.jsonl` tracks per-model cost.
- **Tools (5 new in `Tools/`, .gitignore carve-out):** `model_router.py` (7 task classes
  + `deep` for slow-strong Kimi; keys read from .mcp.json at runtime; UTF-8 stdout fixed),
  `playtest_harness.py` (real-input runtime gate: slate-sendinput / pie-inject-input /
  probe backends, `record pass|fail` writes gate_ledger rows), `video_review_lane.py`
  (free Nemotron VL vision review — paid-model image input 402s on the free-tier key),
  `memory_index.py` (730-file keyword index), `lane_dispatcher.py` (queue→lane, READ
  ONLY; CAVEAT: currently routes against NEXT_ACTIONS.md which is the platform queue —
  gameplay queue lives in `_VERTICAL_SLICE_SCOPE.md`/handoffs; fix before relying on it).
- **New agent hosts:** Muse Code (Meta, WSL2, v0.1.0, API key auth via
  `~/.config/muse/auth.json` schema `{schema_version, providers.meta.{mechanism,api_key,
  obtained_via}}`, smoke test PASSED, reads AGENTS.md + .mcp.json). Junie CLI v26.8.3
  BYOK OpenRouter configured (`~/.junie/config.json`); **headless non-interactive is
  broken on Windows** (readPipedInput IOException "Incorrect function") — interactive only.
- **Free-tier reality:** OpenRouter key is free tier — paid-model daily quota exhausts
  mid-day (Grok/DeepSeek/Mistral 402); TokenRouter (kimi) drops out sporadically. Free
  models unaffected. Plan paid work early in the day or add credits.

## Read-only intake fan-out (6 lanes, ~$0.0014 total)

All reports + cross-lane synthesis: `Saved/Intake/INTAKE_SYNTHESIS_2026-08-11.md`.
Consensus: (1) runtime gate is THE blocker (probe-only = HOLD; real keys never tested
through BP_BattleUI::OnKeyDown); (2) queue-authority mismatch; (3) HUD dual-writer
fix compiled but never observed in PIE — **superseded 2026-08-12: owner confirmed rhythm
highway WORKED in live PIE** (`Docs/Handoffs/RHYTHM_GAME_LOCKED_2026-08-12.md`); (4) don't
push GitHub before Content/LFS secured (partially superseded — v2 push happened below);
(5) best single finding: Q/W/O/P has a 6-key W→O hand shift (spatial playability risk for
dense notes).

## Repo: v2 canonical

`v2` remote = `github.com/fromage3900/MelodiaMelusinaV2` (fresh 4-commit history +
lane's follow-ups; old `origin` is the website repo — leave it). My commits:
`87b2938d` (tools + Figma key redaction), `2770c0e9` (UI transparency audit).
**SECURITY:** Figma API key was public on v2 in `Docs/Reviews/MCP_SURFACE_SCAN_2026-08-03.md`
— redacted in the doc; **OWNER MUST ROTATE the live key at figma.com** and update root
`.mcp.json`/`.opencode.json`. OpenRouter/TokenRouter/Muse keys verified NOT in v2.
Pushes intermittently blocked by GitHub connectivity — retry; commit is safe locally.
Content/ stays untracked (no LFS) — v2 is asset-light by design.

## Closeout source verdicts (`Docs/Handoffs/CLOSEOUT_SOURCE_VERDICTS_2026-08-11.md`)

- **Step 3 (damage-scalar sequencing): PASS by design.** FinishSession latches
  PendingDamageMultiplier → OnRhythmComplete.Broadcast → deferred InvokeStockUseSkill →
  montage notify (0.5s) reads latched scalar. The old 2.5s gap applied only to the
  replaced parallel-start pattern. A/B meaningful.
- **Step 5 (RestorePartyAfterBattle): spelling RESOLVED; call site on open PRs.**
  Live reflection confirmed stock `S_PlayerUnitData` really spells `curentMP`. Library
  match is correct. Wiring is **not on main yet** — prefer [PR #1](https://github.com/fromage3900/MelodiaMelusinaV2/pull/1)
  (world-iterates `BP_BattleController`). [PR #2](https://github.com/fromage3900/MelodiaMelusinaV2/pull/2)
  passes `ActiveBattleActor` (tagged encounter) and is the wrong target for the library.
- **UI transparency audit: FIXED.** `WBP_Battle_Rhythm` JudgementText/ComboText/
  ClockSourceText were authored A=0 and nothing ever set their color → grade/combo/clock
  text permanently invisible. Fixed to opaque white (flat rgba JSON write shape — the
  import-text shape does NOT persist; this was the line-228 quirk), compiled, saved,
  readback verified. Flags: `RhythmPrompt` Collapsed by default (verify shown on rhythm
  start); `WBP_MelodiaRhythmHighway` = duplicate-tree candidate for closeout Step 9.

## Next work (per CORE_GAMEPLAY_CLOSEOUT_PLAN_2026-08-11.md)

Four gates: `runtime`, `save_load`, `repeat_consume`, `package_launch` (runtime FAIL row
is honest). Campaign 1 (real-input rhythm→damage A/B) maps exactly onto
`playtest_harness.py` (slate-sendinput, assertion JSON next to frames, `record pass`).
One editor + Monolith 9316 are up now. Editor was restarted mid-session (two-instance
violation observed at 15:02 — resolved by owner closing one).

---

# Session Handoff - 2026-08-08 (prep for P0 work)

**Session type:** Closed-editor prep: TD preservation, gate trust, git organization
**Project phase:** UE 5.8 production JRPG + QuillScript integration

## Mid-session update (2026-08-08, editor live) — verified wiring findings

The editor is up (Monolith 9316 live). Live-graph audits moved three P0 items to DONE and resolved
one decision:

- **B3 (rhythm cluster) — DONE in live.** `Use Skill with Rhythm`(194) wired: UseMP(115).then ->
  node -> HideSkillActionButtons(110), StockSkill <- Get currentSkill(116). Double-fire
  StartSession/Branch/UseSkill cluster absent. Damage latch (Get/Clear Pending Damage Multiplier)
  wired. Audit: `Docs/T3D_Patterns/wiring/verify_battle_closure.py` — 10/10 invariants PASS.
- **B4 (battle-result closure) — DONE in live.** Switch on E_BattleResult -> Sequence_3/4/5 ->
  CompleteBattle(45/49/51) + PlayerWon(204)/EnemyWon(205)/Keys(99) legs; Keys(99) on the Fled leg
  is the authored design (dead-unit rewards). Nothing dangles.
- **B7 (grade display) — DONE in live.** `ShowRhythmGrade` function graph implemented (4 nodes:
  Entry -> ToText -> SetText on RhythmGradeText TextBlock), exact C++-expected signature.
- **Sir departure — RESOLVED (option a).** Compiled MorningIntro script is the departure
  authority (`melodia:battle:melodia_smoke_encounter`, then typed result branches, then
  `melodia:flag:melodia_smoke_complete`, `$ End`). No travel / BeginWindowDeparture path exists.
  `HandleMorningIntroEnded` + `Begin Window Departure` verified disconnected — safe to delete via
  `Docs/T3D_Patterns/wiring/sir_cleanup.py` (dry-run verified).
- **Wiring audit committed:** `Exports/bp_battlecontroller_eventgraph_live.json` is the fresh
  evidence source; the older `_postfix.json` export is stale (predates the sequence fan-out).
- **Material baseline:** 2 impressionist assets drifted (metadata-only, node counts identical);
  accepted via `--update`, re-committed. Gate: 55 clean.
- **Orphans noted (cleanup candidates):** Get currentBattle (VariableGet_1), Get currentSkill
  (VariableGet_97) in BP_BattleController.

Remaining editor-session work (in order): run the fixed PIE smoke gate on the authored loop
(L_MelusinaMorning route), save-chain fixes, input parity, packaged-build launch.

---

# Session Handoff - 2026-08-08 (prep for P0 work)

**Session type:** Closed-editor prep: TD preservation, gate trust, git organization
**Project phase:** UE 5.8 production JRPG + QuillScript integration

## Verified state (2026-08-08, before editor relaunch)

- **TouchDesigner preserved (A0 done, commit `4f0d1ede`).** The live project was saved
  (`C:\EnvironmentPortfolio\_TouchDesigner\grandmaster_melodia\grandmaster_melodia7.9.toe`) and
  exported to tracked, diffable `.tdn` files:
  `_TouchDesigner/grandmaster_melodia/networks/{project1_full,osc,audio,postfx}.tdn`
  (project1_full = 2.68 MB, full embed incl. DAT code). Canonical
  `grandmaster_melodia.toe` in the repo refreshed from the live save (706,876 B, was 07-24 stale).
  Embody scope was claimed and released; no peer sessions present.
- **Build state: all C++ current.** DLLs compiled 2026-08-08 01:49
  (`UnrealEditor-MelodiaCore.dll`, `UnrealEditor-BS_GodFile.dll`,
  `UnrealEditor-MonolithBlueprint.dll`). UBT reports "Target is up to date" — includes the
  Sir-rescue fix, the UE→TD reactivity edge + heartbeat, and atomic T3D injection.
- **Verification gates fixed and TRUSTED (the ok:true-with-errors false positive is gone):**
  - `Tools/pie_smoke_runner.py` — `ok` now mirrors the server rule
    (`MonolithEditorActions.cpp` #3): active-bucket `must_absent` hits fail; `missing_must_present`
    fails; teardown exempt. Report includes `ok_reason`, `must_absent_hits`, `missing_must_present`.
  - `Tools/regression_suite.py` — fixed the `int + dict` poll crash (grouped_counts is
    bucket→category→pattern) and applied the same ok rule.
  - Both committed: `a0e2b00b` (tools tracking + smoke runner), `0a2e688a` (regression suite).
- **Pipeline core now versioned** (`a0e2b00b`): mcp_client, t3d_* injectors, nl_to_blueprint,
  bp_regression_checker, continuous_loop, pie_smoke_runner, regression_suite, graph_reachability,
  ui_lint, record_gate — previously untracked under `Tools/*`.
- **Git: main is clean of tracked dirt.** 15 commits since `ba8a6f41` (9-way logical split of the
  dirty tree + TD preservation + gate fixes + tool tracking). `.mcp.json` untracked (API keys);
  `CompatibilityLabs/Snapshot_2026-08-06/` (2.6 GB) and `PR_DRAFT/` remain untracked by policy.
  Push to `origin` still blocked (network).
- **Known TD content errors (pre-existing, not blocking):** `shrine_mesh` FBX unreadable
  (g:\...\SM_Orn_RoseWindow_8Petal.fbx missing); render-mat tangent warnings on
  `magical_visuals/main_render`.

## Relaunch sequence (today)

1. Launch exactly one UE 5.8 editor with `-unattended` (known modal/hang history).
2. Confirm Monolith `9316` reachable, `list_errored_blueprints` + dirty packages clean.
3. Run `python Docs/T3D_Baseline/verify_baseline.py` (expect 55 clean).
4. Then the P0 gates in dependency order (B4 closure → B3 rhythm cluster → B7 grade display →
   Sir departure → save chain → input parity → packaged-build launch), each claimed only with a
   capture artifact from the fixed smoke runner.

---

# Session Handoff - 2026-08-07

**Session type:** Integration pipeline research and PC restart closeout  
**Primary track:** Text injection pipeline first; then Blueprint wiring and runtime proof  
**Project phase:** UE 5.8 production JRPG + QuillScript integration  

## Session Result

This session was research-only for project content and editor assets. No Blueprint, C++, Quill,
map, material, Niagara, or save asset was intentionally changed.

The repository was studied across:

- Monolith, UEBlueprintMCP, UnrealMCP, it-is-unreal, Ollama, and project MCP configuration
- Local model availability and current model-calling scripts
- Monolith Blueprint/T3D implementation and verification source
- TurnBasedJRPGTemplate battle contracts
- MelodiaCore authority boundaries and quarantined systems
- QuillScript notification, interpreter, widget, and persistence contracts
- Existing runtime, PIE, screenshot, and gate-recording workflows

The central finding is unchanged: the project has enough editor capability, but the shared text
injection path is not yet a safe production tool. Agents are failing because the repository mixes
incompatible MCP contracts, stale examples, transport-level success with operation success, and
Blueprint graph writes without mandatory readback.

## Editor Shutdown State

- The older Unreal Editor PID `7204` was terminated.
- Its visible window remained as an OS ghost after the process exited; `EndTask` and
  `DestroyWindow` were rejected by Windows because the owner was already gone.
- The newer editor process also disappeared during the shutdown sequence.
- Final check: no trusted live Unreal editor and no active Monolith `9316` or UEBlueprintMCP
  `55558` listener. Treat the editor as fully stopped.
- Do not trust any older handoff that says the editor is currently open or that a live MCP call is
  available.

After reboot, launch exactly one UE 5.8 editor with `-unattended`. Confirm the process and ports
before any write. The known startup modal/hang history is documented in `CURRENT_STATE.md`; the
unattended flag is required for unattended recovery.

## MCP Inventory

### Monolith

- Config: `.mcp.json`, command `Plugins/Monolith/Binaries/monolith_proxy.exe`
- Live transport: HTTP JSON-RPC at `http://127.0.0.1:9316/mcp`
- In-process with Unreal Editor
- Current source/docs describe roughly 1400 in-tree actions, including Blueprint, editor, project,
  source, material, UI, animation, Niagara, and capture actions
- Blueprint surface includes `export_graph`, `get_graph_fingerprint`, `assert_graph_matches`,
  `add_node`, `add_nodes_bulk`, `connect_pins`, `connect_pins_bulk`, `batch_execute`,
  `set_pin_default`, `set_node_property`, `compile_blueprint`, `validate_blueprint`, and
  `save_asset`
- It is the only inspected surface that currently provides the complete graph readback and
  fingerprint/assertion primitives needed for a safe wiring transaction
- `project_query:export_asset_text` is read-only asset-text export; it is not an arbitrary text
  import endpoint

### UEBlueprintMCP

- Config: `.mcp.json`, Python stdio server
- Python bridge connects to the Unreal plugin at TCP port `55558`
- README claims 60+ commands, persistent connection, validation, and auto-save
- Strong node-operation surface: find nodes, inspect pins, add nodes, connect pins, dispatchers,
  UMG, Enhanced Input, compile, and viewport/editor actions
- No inspected equivalent of Monolith's semantic graph fingerprint and assertion contract
- Current repository wiring docs call this the only valid Blueprint writer, but that claim conflicts
  with the actual Monolith source and the older Monolith verification procedure. Resolve this
  policy before asking agents to mutate graphs.

### UnrealMCP

- Plugin source binds its legacy socket bridge to port `55557`
- `.mcp.json` does not configure it as the active Blueprint server
- Do not assume it is the same service as UEBlueprintMCP `55558`
- The port mismatch is a live configuration drift item, not a reason to add a third graph writer

### it-is-unreal

- Configured as HTTP MCP at `http://127.0.0.1:8088/mcp`
- Keep for general editor, asset, level, and runtime queries only
- Do not use it as the authoritative Blueprint graph writer or verifier

### Ollama and other MCP entries

- Ollama host: `http://localhost:11434`
- Ollama MCP is configured in `.mcp.json`, `.opencode.json`, and `.claude.json`
- OpenCode and Claude project configs currently expose different server sets from `.mcp.json`;
  agents do not receive a uniform UE tool surface
- `cpp-compile-feedback` and Blender MCP entries are present in `.mcp.json` but are not part of the
  first Blueprint text-injection milestone
- `deepseek-v4` and `kimi-k3` cloud MCP entries exist in `.mcp.json`
- Cloud API credentials are exposed in the repository configuration/history. Do not use those
  entries until the owner rotates the credentials. Do not copy or print the values.

## Local Models Confirmed

`ollama list` confirmed only these installed models at the end of this session:

| Model | Size | Context | Relevant use |
|---|---:|---:|---|
| `deepseek-r1:14b` | 9.0 GB | 131072 | Complex graph reasoning, contract analysis, patch planning |
| `qwen2.5-coder:7b` | 4.7 GB | 32768 | JSON/spec generation, Python/C++ tool work, schema transformation |

Important drift:

- Older handoffs claim `qwen3:8b` was installed and verified, but it was absent from the current
  `ollama list`.
- `Tools/nl_to_blueprint.py` hardcodes `qwen3:8b`, so its default local path is currently stale.
- `nl_to_blueprint.py` also references cloud `deepseek/deepseek-v4`, uses an environment key, and
  does not enforce a successful result.

Recommended model role, once the pipeline exists:

1. Use DeepSeek locally for graph-context interpretation and patch planning.
2. Use Qwen Coder locally for strict JSON transformation, schema repair, and tool code generation.
3. Require both models to emit a versioned patch/spec only. Neither model should call an editor
   mutation directly.
4. Validate the generated patch deterministically before any MCP write.

## Text Injection Findings

### Current tool is not literal T3D injection

`Tools/t3d_blueprint_injector.py` is a small Python wrapper around
`blueprint_query:build_blueprint_from_spec`.

It currently:

- Is library-only and has no usable CLI
- Sends a hardcoded Monolith URL
- Emits unsupported `type: "function_call"` in its helper methods
- Does not handle JSON-RPC errors or MCP `isError`
- Does not inspect the nested compile result
- Does not save
- Does not export/read back
- Does not fingerprint or assert
- Cannot reference existing graph nodes in the builder's local ID map
- Cannot safely connect the injected subgraph to existing stock nodes
- Cannot roll back a partially applied transaction

The name should be split into two concepts:

- **Blueprint graph patching:** structured JSON operations against an existing graph
- **Literal T3D text import:** a separate native import action, if raw editor text is truly needed

### `build_blueprint_from_spec` limitations

Source: `Plugins/Monolith/Source/MonolithBlueprint/Private/MonolithBlueprintBuildActions.cpp`.

- It loads an existing Blueprint; it does not create a new parent/class despite broad documentation
  claims.
- Its `IdMap` contains only nodes created in that request. Existing nodes cannot be referenced.
- It copies only a limited set of node fields. Delegate-specific fields, function reference fields,
  titles, and several node properties are not forwarded.
- Pin defaults are read with `TryGetStringField`, so numeric/boolean JSON values are not accepted as
  typed defaults.
- Duplicate spec IDs overwrite the previous ID mapping.
- Re-running a request is not idempotent and generally creates duplicate nodes.
- The transaction is ended even after partial errors; it is not a rollback transaction.
- Auto-compile uses the outer action result. The compiler action returns an outer success envelope
  while compiler failure is represented in the nested `compile_result.success`; callers must inspect
  the nested result and `error_count`.
- It does not save the asset.

### Native T3D support is narrower than documentation implies

`copy_nodes` uses Unreal's `ExportNodesToText` and `ImportNodesFromText`, but:

- It copies selected nodes between graphs rather than accepting arbitrary caller-provided T3D text
- Internal links are preserved
- External links are dropped
- Imported IDs change
- It does not compile or save
- `project_query:export_asset_text` is read-only

If raw text injection is required, implement a separate native action around
`FEdGraphUtilities::ImportNodesFromText` with explicit target graph, imported-node mapping,
connection policy, compile, save, and readback. Do not pretend the current JSON builder is that tool.

### Existing verification is useful but not yet composed

Monolith already has the primitives for:

```text
export_graph
-> get_graph_fingerprint
-> mutate
-> compile_blueprint
-> assert_graph_matches
-> get_graph_fingerprint
-> save_asset
-> export_graph/readback
```

The missing work is a single agent-facing operation that enforces this sequence and fails closed.

Required behavior for the future composite operation:

- Explicit target asset and graph
- Explicit expected pre-edit fingerprint
- Full pre-edit export, including hidden pins
- Existing-node references resolved from live node IDs/GUIDs
- New-node references scoped to the current patch
- Deterministic duplicate-ID rejection
- Dry-run schema/pin/class validation
- One asset per transaction
- Stop on any operation failure
- Compile and inspect nested compiler status/error count
- Assert intended nodes, edges, defaults, and forbidden old nodes
- Save the exact target asset
- Re-export and compare post-save state
- Return a structured evidence manifest

## Current Wrapper Defects

### `Tools/mcp_client.py`

- Hardcoded URL instead of honoring configured `MONOLITH_URL`
- Fixed JSON-RPC request ID
- Does not inspect `result.isError`
- Returns only the first text content item
- `discover()` first tries an unsupported raw `monolith_discover` method and its fallback is not
  the live namespace action catalog

### `Tools/nl_to_blueprint.py`

- Reads `graph_data` but does not include it in the model prompt
- Tells the model to emit `function_class`, while the builder forwards `target_class`
- Has no JSON schema validation or patch preflight
- Does not support existing-node references
- Returns success after injection/compile failures in several paths
- Does not save, assert, fingerprint, or perform independent readback
- Uses unavailable `qwen3:8b` by default

### Documentation drift

The following sources disagree and must be reconciled before the next agent session:

- `AGENTS.md` examples use an incorrect spec wrapper and an incorrect `expected_fingerprint`
  assertion shape
- `Docs/BLUEPRINT_WIRING_SKILL_2026-08-07.md` says UEBlueprintMCP is the only Blueprint writer
- `Plugins/Monolith/Docs/MONOLITH_GUIDE.md` and live Monolith source provide a full Blueprint write
  and verification surface
- Older handoffs use stale parameter names and direct ad-hoc calls
- Monolith documentation often says UE 5.7 while this project runs UE 5.8

Do not let a model choose between these documents. Establish one project policy and link it from
`AGENTS.md`, the wiring skill, the contract, and the session template.

## Runtime Integration Contract

The production text path remains:

```text
.qsc source
-> QuillScript asset/interpreter
-> UMelodiaNarrativeSubsystem
-> allowlisted typed intent
-> stock JRPG / project travel / Persona adapter
-> typed result
-> Quill Restore()
-> Quill Next()
```

### QuillScript source

- Source path: `Content/MelodiaIntegration/Narrative/*.qsc`
- Compile helper: `Content/Python/compile_melodia_quill_battle.py`
- Native editor seam: `UMelodiaNarrativeSubsystem::CompileQuillSource`
- Stable notification verbs are battle, quest, flag, travel, reward, stat, and item
- IDs must be checked against `DA_MelodiaIntegrationConfig` before runtime
- Persistent authored variables use the `melodia_` prefix
- `melodia:item:give` is still a logging stub and must not be authored as a real inventory grant

### Authoritative battle path

```text
Quill Notify
-> UMelodiaNarrativeSubsystem::StartBattle
-> OnBattleRequested
-> UMelodiaExternalJRPGBridgeSubsystem
-> exactly one tagged stock battle actor
-> reflected StartBattle/offLevelBattleData/OnBattleOver contract
-> typed EMelodiaBattleResult
-> CompleteBattle
-> one Restore()
-> one Next()
```

Do not inject another battle starter or another resume path.

Safe observer hooks:

- `OnBattleRequested`: presentation/input observation only
- `OnJRPGBattleStarted`: presentation/diagnostics only
- `OnJRPGBattleEnded`: raw result observation only; do not call `CompleteBattle`
- `OnBattleCompleted`: cleanup/results presentation only; do not resume Quill again
- `OnBattleAborted`: cleanup and failure UI only; do not fabricate a result

Do not use the MelodiaCore legacy `UMelodiaBattleSession` as the Quill/stock-JRPG bridge. Do not
put project encounter IDs, Quill parsing, canonical saves, project rewards, or stock JRPG
reflection into MelodiaCore. MelodiaCore remains presentation/neutral capability code here.

### Quill hooks that are not safe assumptions

- `OnResumed` and `BeforeResume` are declared but not broadcast/called by the current Quill runtime
- `OnScriptPlay` is safe for capturing the active interpreter, not for forcing UI/input or advancing
  dialogue
- Never restore a live widget/typewriter/battle state; resume at authored boundaries

## Loose Ends To Carry Forward

### P0: text pipeline

1. Ratify the single graph-authoring authority. Recommended direction: a shared project wrapper
   uses Monolith for graph export/fingerprint/assert/readback, with an explicit exception path for
   operations only UEBlueprintMCP can express. No agent should make raw ad-hoc graph calls.
2. Build the wrapper in stages: read-only preflight, dry-run patch validation, one-asset apply,
   compile/assert/save/readback, then literal T3D import only if required.
3. Add existing-node references and a patch-to-live-node mapping.
4. Make failures fail closed; never treat MCP transport success, outer action success, or a printed
   node count as graph success.
5. Persist raw request/response evidence, before/after exports, fingerprints, compile output,
   assertion output, save result, and dirty/error state under `Saved/T3D/`.
6. Replace stale `t3d_blueprint_injector.py` and `nl_to_blueprint.py` paths only after the wrapper
   has a disposable Blueprint proof.

### P0: runtime proof

The authoritative current state says the gameplay is not yet playable and the following remain
runtime-unproven:

- Dialogue visible and input/focus ownership
- Exactly one battle request
- Victory, defeat, fled, and unavailable result matrix
- Exactly one Quill restore/next
- Canonical save creation and process-restart load
- Narrative flag/reward persistence and idempotence
- Load with Quill unavailable
- Interpreter invalidation during terminal result
- Manual save blocked during active battle
- Main Menu New Game/Continue/Load
- Instantiated stock battle widget identity
- Development-package launch outside the editor

### Conflicting status claims to resolve by live readback

- `_SESSION_HANDOFF.md` previously called save creation/slot naming fixed; the full runtime
  save/restart gate was still owed.
- `PROJECT_SCOPE_AND_WORKFLOW_PLAN_2026-08-06.md` still describes the old save defects.
- `_TASK_QUEUE.md` says the rhythm StartSession/SubmitRatedInput nodes are absent, while
  `INTEGRATION_POLISH_HANDOFFS_2026-08-06.md` says parts of that lane are built.
- Older handoffs claim dialogue/battle success, while `CURRENT_STATE.md` records the owner's later
  live result that dialogue is not visible and battle is non-functional.
- Treat live owner-confirmed runtime behavior as truth; re-export the current graph before deciding
  which static claim is stale.

### P1/P2 integration loose ends

- Live Coding/build path remains blocked; use a closed-editor UE 5.8 `-NoUBA` build until repaired
- Battle UI has multiple possible owners and a documented path mismatch; identify the instantiated
  stock widget and choose one Melodia overlay owner
- Verify input-context push/pop balance and interaction blocking, not just consumer presence
- Verify all active travel routes use the authority and that tagged PlayerStart placement succeeds
- Melody Token pickup/HUD lane remains in progress
- Co-op conditional bonus remains unwired
- Rhythm chart/skill mapping and rhythm-to-stock timing remain disputed until live graph readback
- Packaged Development traversal remains open
- Owner must rotate exposed cloud MCP credentials

### Explicitly do not reopen in the next pipeline session

- Portfolio material/PCG cleanup
- Legacy MelodiaCore battle/save lane
- Quarantined orphaned-script reconstructions
- Website/render capture work unrelated to the text-injection proof
- New gameplay mechanics before the bridge and evidence loop are proven

## Files and Worktree

Intentional file change in this closeout:

- `_SESSION_HANDOFF.md`

No gameplay/editor asset was changed by this session. The repository was already dirty with many
parallel-agent changes before this session; do not revert, reset, or clean unrelated work.

## Next Session MUST Start With

1. Relaunch exactly one UE 5.8 editor with `-unattended`; confirm one process and live ports `9316`
   and `55558`. Do not mutate if either server is unavailable or a second editor is present.
2. Read this handoff, `AGENTS.md`, `CURRENT_STATE.md`,
   `Docs/BLUEPRINT_WIRING_SKILL_2026-08-07.md`, and
   `Docs/BLUEPRINT_WIRING_CONTRACT_2026-08-07.md`. Reconcile the conflicting writer policy before
   using any existing wiring command.
3. Run read-only preflight: editor status, errored Blueprints, dirty packages, exact graph list,
   and live action schemas. Preserve raw responses.
4. Select one disposable or duplicated Blueprint for the injection proof. Export the full target
   graph with hidden pins and record `topology` fingerprint twice, then no-op save and fingerprint
   again. Stop if the hash is not byte-stable.
5. Implement/test the shared wrapper's read-only and dry-run phases before any production graph
   write. The first write must be one asset, one patch, one compile/assert/save/readback manifest.
6. Only after the tool proof passes, target the smallest real integration seam. Do not begin with
   the entire battle controller or a generated multi-agent batch.
7. Record each live result in `Saved/gate_ledger.json`; static graph presence is never a runtime
   completion claim.

## Definition Of Done For The Next Pipeline Session

The session is not complete until one controlled Blueprint patch has:

- A saved pre-edit export and stable baseline fingerprint
- A validated patch with explicit existing-node references
- Compile result with zero errors and understood warnings
- Reachability and intended-edge assertion with `matched: true`
- Exact asset save result and clean package readback
- Post-save export/fingerprint matching the asserted state
- A complete evidence manifest in `Saved/T3D/`
