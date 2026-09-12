# Melodia Convergence Closeout and P0 Plan — 2026-08-24

## Executive status

The offline convergence phase is complete and committed in reviewable follow-up batches. It produced reproducible authority, experience-contract, test-truth, and publication-claims tooling without modifying production C++, Unreal packages, canonical Quill content, or stock JRPG gameplay.

The project is not at P0 exit yet. Four historical integration completion gates are recorded as
passing, but eight current P0 gates remain open/failing/on HOLD. The August 24 NPC/quest audit
also found a malformed authored flag intent, duplicate quest mutation paths, non-atomic reward
ordering, and missing restart-safe checkpoint/encounter state. These are shipping blockers, not
reasons to build another system.

The fastest route is therefore convergence and proof, not another feature tranche.

## Committed closeout batches

- `5040dc64` — First Dream Persona/Infinity-Nikki-lens experience contract producer, tests, and deterministic JSON evidence.
- `961cc186` — publication-safe gameplay claims validator and tests.
- `127ca9e6` — non-UE gate truth auditor, regenerated 124-file inventory, report, and deterministic JSON evidence.
- `f9fcb4d1` — deterministic 1,270-node gameplay authority atlas, tests, canonical August 24 report/evidence, and removal of the accidental August 23 duplicate.
- `9a40d2ff` — this convergence closeout and shortest P0 plan.
- `70212962` — fail-closed Windows hook, narrow generated-evidence boundary, index-safe Git health audit, and nested-checkout containment.
- `2b69ce13` — correct dotted Monolith namespace/action/params routing plus canonical CDO `asset_path` reads and regression coverage.
- `78ecff15` — correct `project_query` routing and fail-closed action-payload evidence handling.
- `263c046f` — earlier preservation checkpoint that already contains the public reports, systems case-study, claims JSON, and Geometry Nodes/TouchDesigner/worldgen prompt packet. It also contains unrelated preservation work and is not represented as an isolated convergence commit.

The closeout and Git/MCP commits are local on `main` and have not been pushed. Unrelated dirty
`.uasset`, plugin, Blender, Gaea, and worldgen changes remain preserved and were not included.

## Verification completed

- Authority atlas: 6/6 tests passed at the `f9fcb4d1` commit baseline; two runs produced identical JSON and Markdown. JSON SHA-256: `7A82678CC6126F50566243CC957A42C862FA46CFEDDD6CF887A441D261CC8A80`.
- Experience contract: 15/15 tests passed; repeat output was byte-identical. JSON SHA-256: `F8BF10456879DCF1D852079C54F166E3BD0E0CFF52DFF2CFF10EB79382258575`.
- Non-UE gate auditor: 7/7 tests passed; repeat output was byte-identical and the inventory reconciles 124/124.
- Publication validator: 6/6 tests passed and the committed claims packet validates.
- Scoped staged-file whitespace and safety checks passed before each commit.

Post-closeout verification then observed another active task add `Tools/BlenderAddons/melodia_showroom/_debug_scene.py` between the atlas test's two builds. That live-worktree rerun therefore finished 5/6 with only the byte-identity assertion failing. The committed evidence remains valid for its frozen commit baseline; it must be regenerated once more after all Tools writers stop before being called current-worktree evidence.

The repository pre-commit hook is repaired at `70212962`. It runs under Git for Windows, fails
closed if required POSIX validators are unavailable, permits only the three named canonical audit
JSON files under `Saved/`, and passed both the installed positive path and an isolated protected-
file negative fixture. The health auditor no longer refreshes or locks the index.

## Test truth discovered

- The shared offline contract runner is 19/20, not green.
- GMM unittest discovery runs 268 tests and reports 6 errors.
- The auditor records 31 weak-oracle findings.
- Unsafe/editor/network candidates remained on HOLD and were not launched.
- Static, offline, source-built, and runtime claims remain separate.

These are audit findings, not newly introduced regressions. The audit did not modify failing production fixtures or weaken their assertions.

## Current P0 truth

Ledger-backed historical passes:

- `runtime` — real keyboard input, recorded 2026-08-13.
- `save_load` — canonical stock-JRPG save across process restart, recorded 2026-08-14.
- `repeat_consume` — authored Quill replay remains exactly once, recorded 2026-08-14.
- `package_launch` — Development package launched outside the editor, recorded 2026-08-14.

Still open or not current enough for P0 exit:

- `rhythm_owner` — listed in the current P0 live-gate set.
- `hud_single_writer` — source is converged on `UMelodiaUIBridgeSubsystem`; runtime widget identity and one-writer proof remain open.
- `rhythm_grade_to_result` — a real-key timing grade must demonstrably change the stock JRPG result while Quill resumes once.
- `wardrobe_equip_roundtrip` — equip, canonical save, process restart, load, correct outfit and materials.
- `wardrobe_gameplay_hook` — one outfit must provide one observable capability; Glide is the locked first-slice choice.
- `music_world_key` — one played phrase must commit one typed world result and visibly open one route.
- `static_gates` — latest ledger standing is FAIL because two material baselines drifted.
- `battle_integration_map` — latest row is FAIL/HOLD because the August 22 run proved idle map health but did not rerun StartBattle, rhythm, terminal result, and Quill resume.

The nine economy/song/HUD/dungeon/enemy/quest items are now classified in
`Docs/P0_TASK_LEDGER.json` as deferred post-P0 expansion. They remain preserved, but cannot
replace the active convergence and proof gates.

### NPC and quest audit blockers

- `Tools/test_melodia_first_dream_route_contract.py` currently fails because
  `MelodiaQuillHarmonyAwakening.qsc` emits `melodia:flag:<id>` while the runtime requires
  `melodia:flag:<id>:<bool>`.
- `UMelodiaNPCInteractionComponent` can bypass Quill/Narrative and mutate Persona plus the
  quarantined `AMelodiaQuestManagerBase`; `UMelodiaOpeningFlowSubsystem` still reaches that legacy
  authority.
- Reward IDs are consumed before downstream grant/equip acknowledgement, and Persona can mark a
  quest complete before its reward succeeds.
- `ScriptCheckpoint` has no production writer. Pending encounter/completion-guard state is
  transient, so mid-encounter restart cannot yet meet the save contract.
- Current Persona MCP reads expose allowlists/content definitions, not canonical runtime NPC and
  quest state. They are useful diagnostics, not gate oracles.

Execution and evidence requirements are consolidated in
[`../P0_CLOSEOUT_TEST_PLAYBOOK_2026-08-24.md`](../P0_CLOSEOUT_TEST_PLAYBOOK_2026-08-24.md).

## Shortest credible P0 critical path

```mermaid
flowchart LR
    A[Fix malformed authored intent] --> B[Converge NPC and quest mutation]
    B --> C[Atomic reward plus restart state]
    C --> D[Freeze baseline and pass static chain]
    D --> E[UI writer plus four battle outcomes]
    E --> F[Wardrobe Glide plus music route]
    F --> G[Fresh-slot and Continue]
    G --> H[Development package proof]
    H --> I[P0 accepted; freeze evidence]
```

### Step 0 — Make narrative and quest truth green

- Fix the malformed canonical QSC notification and its materialization contract; do not weaken
  the failing route test.
- Remove the direct Persona/legacy QuestManager mutation fallback from the shipping NPC path.
- Make quest completion and reward/equipment grant one acknowledged atomic transaction.
- Persist a stable dialogue checkpoint and encounter command/outcome, or explicitly prohibit
  saving while an encounter is pending.
- Align First Dream design IDs with the authored Smoke aliases and represent unavailable.

Exit: all offline route/progression/chapter/experience tests are green and one runtime snapshot
contract can expose canonical NPC/quest/intent/reward/checkpoint state without mutation.

### Step 1 — Freeze and reconcile proof

- Pause worldgen, economy, companion, calendar, styling-contest, shop, and new-system work on the shipping branch.
- Use one editor and one integration owner.
- Decide whether each of the two material baseline changes is intended. Promote intended baselines through the existing gate; repair unintended drift at its source. Do not waive the gate.
- Rerun the closed-editor build and static chain. No gameplay edits occur until that chain is clean or has one explicitly owned blocker.

Exit: a stable build/input baseline and a green static chain, or one documented owner decision that names the exact remaining blocker.

### Step 2 — Close battle presentation and rhythm together

- Identify the actually instantiated stock battle widget at runtime.
- Enforce `UMelodiaUIBridgeSubsystem` as the sole Melodia presentation writer while stock `BP_BattleUI` retains stock command input.
- Remove automatic shipping-path creation/calls from the retired overlay or competing writer only after reference evidence.
- Use real Q/W/O/P input. Demonstrate one miss and one stronger grade changing degree of success, never progression access.
- Capture victory, defeat, fled, and unavailable as typed outcomes; verify Quill resumes or aborts exactly once.

Close together: `rhythm_owner`, `hud_single_writer`, `rhythm_grade_to_result`, and a current `battle_integration_map` row.

### Step 3 — Close the outfit verb

- Use only `UMelodiaWardrobeSubsystem` and the existing traversal-capability provider.
- Replace any whole-`FMelodiaNarrativeRecord` restoration on equip with the narrow transaction during the post-audit implementation lane.
- Preview one resonant accessory, equip it, unlock only Glide, cross one previously visible blocked route, save, restart, and reload.
- Verify correct outfit, materials, capability, route state, and no duplicated command/reward.

Close together: `wardrobe_equip_roundtrip` and `wardrobe_gameplay_hook`.

### Step 4 — Close music as a world key

- Route one existing Piano phrase completion through the existing typed Narrative seam.
- Commit one idempotent world challenge result.
- Open one visible world object or route. Do not send music into combat/damage and do not introduce a new puzzle authority.

Close: `music_world_key`.

### Step 5 — One final acceptance run

- Play the 20–30 minute sequence: Morning Preparation → wardrobe preview/equip → musical expedition → Glide payoff → stock JRPG encounter → evening relationship consequence → canonical save.
- Run Fresh Slot and Continue/restart paths.
- Confirm the Sir and Priestess choices have distinct mechanical and evening effects.
- Confirm miss-grade recovery, all four battle terminal outcomes, exactly-once reward/intent behavior, and no duplicate UI writer.
- Build and launch the Development package after the shipping baseline is frozen.
- Record gates only from the captured live/package evidence.

P0 exits when the new convergence gates are recorded, the latest package reflects the accepted baseline, and no competing authority auto-creates on the shipping path.

## Long-term development plan after P0

### Phase 1 — Authority convergence

- Add the types-only `MelodiaContracts` module: day phase, preparation choice, typed world result, typed battle result, commit disposition, and versioned save fragment.
- Keep QuillScript absolute narrative authority and the stock JRPG template absolute combat/party/inventory/save authority.
- Put every raw stock-JRPG reflection call behind `UMelodiaExternalJRPGBridgeSubsystem` and validate the reflected schema at startup.
- Disable and then retire competing MelodiaCore battle/save/party/opening-flow authorities after consumer and Blueprint-reference evidence.
- Replace Persona widget scans with immutable presentation read models routed through the UI bridge.

### Phase 2 — Finish the First Dream slice

- Implement the exact three-phase day projection without a full calendar.
- Give Sir one transparent single-encounter rhythm-grace effect and Priestess one Harmony/world-reading effect.
- Preserve one preparation slot, one resonant accessory, one Glide route, one stock encounter, and one evening consequence.
- Make every progression command atomic, idempotent, and restart-safe.

### Phase 3 — Expand one proven loop dimension at a time

- Persona dimension: add one additional scarce activity only after the first relationship consequence is measurable and replay-safe.
- Infinity-Nikki dimension: add the next outfit capability only after acquisition → preview → equip → world verb → payoff → save/reload is proven for Glide.
- World dimension: add authored districts and landmarks as content consumers of stable verbs, never as new progression authorities.
- Combat dimension: add skills and encounter content through stock JRPG ownership; rhythm remains a modifier, not a second combat executor.

### Phase 4 — Production hardening

- Replace weak marker/zero-assertion test oracles and repair the 19/20 contract failure and six GMM discovery errors by ownership category.
- Require artifact hashes and parallel-safe evidence writes before accepting overnight automation output.
- Maintain one writer per UI surface, one capability provider, stable command IDs, and one canonical save fragment.
- Re-run compile, PIE, restart, and packaged golden-run tiers for every promoted vertical-slice milestone.

## Scope guardrails

Until P0 is accepted:

- No new combat, quest, save, HUD, wardrobe, progression, or orchestration subsystem.
- No full calendar, styling contest, gacha expansion, additional currency economy, companion roster, or procedural runtime progression.
- No portfolio claim may describe design intent or source presence as runtime completion.
- No gate closes from probe calls, marker text, screenshots without assertion reports, or zero-test success.

The design target is not feature parity with Persona or Infinity Nikki. The target is their useful discipline: one scarce relationship choice whose consequences persist, and one visible outfit-derived world verb whose payoff is readable.
