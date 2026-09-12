# Melodia Backend Integration Plan — 2026-08-28

**Status:** planning/draft, offline, no editor
**Author:** Melusina (Hermes agent, no-editor lane)
**Live with:** Junie (Rider, editor lock) — this lane stays offline until she frees it
**Supersedes:** nothing — additive to `Docs/P0_CLOSEOUT_PLAN_2026-08-28.md` and the FGameplayTag
proof-of-concept already in `Source/BS_GodFile/MelodiaIntegration/`

---

## Purpose

This is the single plan for the backend side of BS_GodFile Melodia work — the C++ subsystems,
the T3D/Monolith text-injection pipeline, the Echo gate ledger, the Python contract tests, and
the two long-term scale items (StateTree quest/battle spine + native UEditorValidatorSubsystem).
It is written so that any agent — this lane or a future one — can pick it up and know exactly
what exists, what is planned, what is gated behind the editor lock, and what evidence counts.

It does **not** replace the P0 closeout. P0 is still open (8 active gates, see `AGENTS.md` and
`Docs/P0_TASK_LEDGER.json`). This plan is the path *through* P0 and *beyond* it into the two
long-term scale items.

---

## 1. What exists today (truth, not claims)

### Source (compiled, ready to package)

- `Source/BS_GodFile/MelodiaIntegration/` — the C++ bridge layer:
  - `MelodiaGameplayTags.h` + `MelodiaGameplayTags.cpp` — **new**, 18 tag categories, 80+ tags
    registered, `RegisterMelodiaGameplayTags()` ready for `FMelodiaCoreModule::StartupModule`.
    FGameplayTag migration status is tracked in the header's migration comment block:
    - [x] Infrastructure
    - [x] MelodiaWaterGameplaySubsystem (proof of concept)
    - [ ] MelodiaNarrativeSubsystem
    - [ ] MelodiaExternalJRPGBridgeSubsystem
    - [ ] MelodiaExplorationActors
    - [ ] MelodiaPCGWaterGameplayBridgeComponent
    - [ ] MelodiaPCGNarrativeChallengeBridgeComponent
    - [ ] MelodiaBattleMapConfig
    - [ ] All Blueprints (manual)
    - [ ] All Data Assets (manual)
  - `MelodiaWaterGameplayTypes.h` — `FName → FGameplayTag` in all structs
  - `MelodiaWaterGameplaySubsystem.h` + `.cpp` — `FName → FGameplayTag` in all public API;
    internal maps still use `FName` keys via `.GetTagName()` for performance
  - `MelodiaWaterGameplaySubsystem.cpp` — uses `FGameplayTag::IsValid()` in place of
    `IsNone()`, `.GetTagName()` for map lookups
  - Other modified subsystems (2026-08-27/28): `MelodiaAudioReactivePresentationSubsystem`,
    `MelodiaMusicClockSubsystem`, `MelodiaPCGNarrativeChallengeBridgeComponent`,
    `MelodiaPCGWaterGameplayBridgeComponent`, `MelodiaRhythmCombatSubsystem`,
    `MelodiaWaterGameplaySubsystem` (the water subsystem is the FGameplayTag migration proof-of-concept)
- `Source/BS_GodFile/MelodiaIntegration/Tests/MelodiaP0ContentQuestsTests.cpp` — native automation
  test for P0 content + quests

### Content authoring (committed, 2026-08-27, `f78f00f8`)

Four P0 scripts + manifests + spec package:
- `Content/MelodiaIntegration/Narrative/MelodiaQuillP0Playthrough.qsc`
- `Content/MelodiaIntegration/Narrative/MelodiaQuillWardrobeEquip.qsc`
- `Content/MelodiaIntegration/Narrative/MelodiaQuillChoralSheepRecruit.qsc`
- `Content/MelodiaIntegration/Narrative/MelodiaQuillSeaAboveCutscene.qsc`
- `specs/progression/melodia_p0_slice_quests.v1.json`
- `specs/wardrobe/wardrobe_equip_p0_manifest.v1.json`
- `specs/companions/choral_sheep_recruit_manifest.v1.json`
- `specs/cinematics/sea_above_cutscene_manifest.v1.json`

**Status:** authored but **inert** — no `.uasset` compiled, and every new ID is outside
`DA_MelodiaIntegrationConfig` (27 IDs missing). The working tree already has the two authoring
defect fixes (QSC diffs, uncommitted): `flags.` → `flag.` prefix, duplicate reward grants removed.

### Contract tests (offline, always runnable)

- `Content/Python/Tests/test_p0_quests_and_content_contract.py` — 8/8 PASS ✅
- `Content/Python/Tests/test_qsc_allowlist_contract.py` — 3/4 PASS, 1 expected FAIL (27 missing IDs)
- `Content/Python/Tests/test_sea_above_t3d_contract.py` — 4/4 PASS ✅
- `Content/Python/Tests/test_melusina_systems_contract.py` — 4/4 PASS ✅
- `Tools/test_melodia_progression_contract.py` — 6/6 PASS ✅
- `Tools/test_echo_contract.py` — 77/77 PASS ✅

### Editor tooling (Monolith on :9316, editor required)

- `Tools/t3d_blueprint_injector.py` — batch Blueprint subgraph injection via T3D
- `Tools/t3d_material_curve_injector.py` — material curves/scalars/colors/textures via Monolith
- `Tools/bp_regression_checker.py` — graph fingerprint + baseline comparison
- `Tools/bp_live_path.py`, `Tools/bp_sweep.py`, `Tools/ui_style_audit.py` — verification tools
- `Tools/echo_run.py` — Echo pipeline runner (author → spec_validate → inject → compile →
  static_gates → runtime_gates → record → promote)
- `Tools/project_state.py` — derived project state + doc staleness radar

### Skills (this repo, `.claude/skills/`)

- `melodia-p0-loop` — the P0 verification loop runbook
- `melodia-ui-artist` — UI audit/style/apply runbook (token SSOT, Quill WBP chain, editor workflow)
- `melodia-backend` — **new this session**, the no-editor C++/T3D/contract-test runbook (see the
  skill created alongside this doc)

### Gate ledger

- `Saved/gate_ledger.json` — 44 rows; `battle_integration_map` + `hud_single_writer` both PASS
  (recorded 2026-08-28 04:27 UTC, backdated to the 08-27 live PIE)
- `Saved/gate_ledger_report.md` — regenerated 2026-08-28 04:27 UTC; `battle_integration_map` and
  `hud_single_writer` both PASS

### The 8 active P0 gates (from `AGENTS.md` + `Docs/P0_TASK_LEDGER.json`)

| Gate | Status | Notes |
|------|--------|-------|
| `rhythm_owner` | open | exactly one execution path into stock JRPG damage; load-bearing presentation/reactivity callers allowed |
| `hud_single_writer` | pass_pending_owner_decision | runtime widget identity proven; two vestigial vars await owner retire/keep call |
| `rhythm_grade_to_result` | open | real-key timing grade changes stock JRPG result; Quill resumes once |
| `wardrobe_equip_roundtrip` | open | equip → save → restart → load → correct outfit + materials |
| `wardrobe_gameplay_hook` | open | one outfit → one observable capability (Glide) |
| `music_world_key` | open | one Piano phrase → one idempotent typed world result → visibly opens one route |
| `static_gates` | fail | full blueprint/UI/material chain not rerun; two material drifts against 2026-08-07 baseline |
| `battle_integration_map` | pass | all four terminal outcomes, Quill resumes exactly once each (08-27 live PIE) |

Historical passes (bounded, not current certification): `runtime` (08-13), `save_load` (08-14),
`repeat_consume` (08-14), `package_launch` (08-14).

---

## 2. The critical path through P0

The 08-27 content commit is decorative until the allowlist and compiled assets exist. The
sequenced path (from `Docs/P0_CLOSEOUT_PLAN_2026-08-28.md`, §3):

### Phase 0 — Hygiene (no editor, done this session)

- [x] 4 zero-byte root files gone (prior session)
- [x] `BS_GodFile.uproject` clean — only HoudiniEngine enable, no BOM/reindent (this session)
- [x] QSC authoring defects fixed in working tree (this session)
- [x] `Saved/gate_ledger.json` + `Saved/gate_ledger_report.md` synced to 08-27 handoff (this session)
- [x] `Docs/Handoffs/P0_ALLOWLIST_DELTA_FOR_RIDER_2026-08-28.md` + `.json` written (this session)

### Phase 1 — Make the authored content real (editor, Junie's queue)

- [ ] **Extend `DA_MelodiaIntegrationConfig`** with the 27-ID delta (5 QuestIds, 13 NarrativeFlagIds,
  5 DialogueRewardIds, 2 SocialStatIds, 1 TravelLevelIds). Read truth with
  `blueprint_query get_cdo_properties`, not `melodia_config_get_allowlist`.
- [ ] **Compile the 5 `.qsc` → `.uasset`** (4 P0 + `MelodiaQuillHarmonyAwakening`). Confirm each
  loads via `unreal.load_asset`.
- [ ] **Verify offline:** `test_qsc_allowlist_contract` 4/4 PASS.

### Phase 2 — Live-prove the four pillars (editor + PIE)

- [ ] P0 Playthrough — victory branch end-to-end; verify atomic commit order, Quill resumes once.
- [ ] Wardrobe equip → `wardrobe_equip_roundtrip` — equip, canonical save, **full process restart**,
  load, confirm outfit + materials restore.
- [ ] Glide → `wardrobe_gameplay_hook` — one equipped item, one observable capability.
- [ ] Choral Sheep — script-side proof only (companion `PRESENTATION_ONLY` until mesh is skinned).
- [ ] Sea Above — travel, membrane pulse, droplets (requires `LV_SeaAbove_Prototype` in `TravelLevelIds`).

### Phase 3 — The remaining rhythm gates

- [ ] `rhythm_owner`: prove at runtime that exactly one path reaches stock damage — confirm battle UI
  calls `UseSkillWithRhythm`, not stock `UseSkill`.
- [ ] `rhythm_grade_to_result`: real-key timing changes a stock result, progression never blocks,
  Quill resumes once.
- [ ] `music_world_key`: attach `UMelodiaPCGNarrativeChallengeBridgeComponent` to a host actor in a
  level, prove one Piano phrase commits one idempotent typed result and visibly opens a route.

### Phase 4 — Closeout

- [ ] Owner decision: retire the two vestigial `melodiaBattleUI` / `MelodiaUI` vars → `hud_single_writer`
  fully closed.
- [ ] Owner decision on the two material drifts → re-freeze or revert → rerun full static chain with
  editor up → `static_gates`.
- [ ] Fix `LiveResultsWidgetPath` by mirroring the `MelodiaBattleWidgetPath` backfill in `Initialize()`;
  bundle with any other C++ change so the closed-editor rebuild is paid once.
- [ ] Repackage and rerun `package_launch` against current content (standing pass is 08-14 baseline,
  150+ commits stale).
- [ ] Full 20–30 minute golden run, then record the ledger rows.

---

## 3. Text-injection pipeline at scale (the "monoliths" piece)

### What "text injection" means here

The T3D/Monolith pipeline is the project's declarative content-authoring path: a JSON spec is read
by a Python harness, injected into the running editor via Monolith JSON-RPC, compiled, fingerprinted,
asserted, and promoted. The canonical sequence (from `AGENTS.md` § T3D Wiring Pipeline and
`Docs/Production/T3D_MONOLITH_REFERENCE.md`):

```
Spec Change → T3D Inject → Compile → Fingerprint → Regression Test → Promote
```

Echo orchestration (added 2026-08-09) layers an evidence ledger on top: agents author content,
gates score it, nothing is believed without a ledger row. The Echo manifest is
`specs/echo_pipeline.json`; the runner is `Tools/echo_run.py`.

### What exists today

- Toon profile specs: `specs/toon_profiles/tp_melusina.json` (and others)
- Niagara MPC binding specs: `specs/niagara_mpc_bindings.json`
- Material-curve injector: `Tools/t3d_material_curve_injector.py` with `apply_toon_profile_spec()`
- Blueprint injector: `Tools/t3d_blueprint_injector.py` with `T3DBlueprintInjector.inject_into()`
- Material inject demo: `Tools/t3d_material_inject_demo.py` (read/verify/all CLI)
- CI gates: `ci_gates.json` (graph fingerprint exact_match, blueprint_compile 0_errors,
  material_compile 0_errors, shader_instructions max_150, triangle_budget max_250k,
  pie_smoke 0_crashes, animation_delta threshold_0.05, accessibility pass)

### What "at scale" means

The P0 content pillar is four scripts + one config edit. "At scale" is the point where the same
pipeline authors whole families — multiple toon profiles, multiple Niagara systems, multiple
material instances, multiple Blueprint fixtures — in one batch, with one fingerprint baseline and
one regression pass. The project already has the pieces; the scale-up is about:
1. **Batch specs** — one spec file per family, not per asset, with a manifest that lists the asset
   paths and the expected post-inject state.
2. **One baseline, many assertions** — `bp_regression_checker.py` compares fingerprints; at scale
   you want one pre-inject baseline and one post-inject assertion per family, not per asset.
3. **Echo ledger rows per family** — each family gets a gate-id and a `record <id> pass|fail` row.
   The Echo contract says a lane is "done" only when the gate it claims has a ledger row.

### The gap to fill

The pipeline works for one-off toon profiles and material instances. To scale to "monoliths"
(multiple families authored in one batch), the missing pieces are:
- A batch spec format that lists multiple asset paths + per-asset expected state (a manifest, not a
  flat spec)
- A batch injector that walks the manifest, injects each asset, compiles, fingerprints, asserts
- A batch verifier that runs the full static chain (graph reachability + bp_live_path + bp_sweep +
  ui_style_audit + material baseline) against the post-inject tree
- An Echo record step that writes one row per family, not per asset

None of these require new C++. They're Python harnesses built on top of the existing Monolith
actions and the existing `Tools/` scripts. The editor lock is the only contended resource — the
harnesses are editor-bound, not this lane's concern until Junie frees it.

### A batch spec sketch (for the doc, not yet implemented)

```json
{
  "batch_id": "batch.toon_profiles.v1",
  "manifest_version": "1.0",
  "families": [
    {
      "family_id": "family.melusina_toon",
      "asset_paths": [
        "/Game/EnvSandbox/Materials/ToonProfiles/TP_Melusina",
        "/Game/EnvSandbox/Materials/ToonProfiles/TP_Melusina_Alpha"
      ],
      "spec_paths": [
        "specs/toon_profiles/tp_melusina.json",
        "specs/toon_profiles/tp_melusina_alpha.json"
      ],
      "expected": {
        "compile": "0_errors",
        "fingerprint": "<per-asset, recorded pre-inject>",
        "material_compile": "0_errors"
      }
    }
  ]
}
```

This is a planning sketch. The real format will be driven by what `bp_regression_checker.py` and
`t3d_blueprint_injector.py` already accept — don't invent a new contract until you've read those.

---

## 4. StateTree quest/battle spine (long-term scale item 1)

### Motivation

The current quest/battle state is distributed:
- `FMelodiaNarrativeRecord` holds Flags, ActiveQuestIds, CompletedQuestIds, ConsumedIntentIds,
  ConsumedRewardIds, ScriptCheckpoint
- `BP_BattleController` drives battle phase via if-chains
- QuillScript branches on `melodia_battle_result`

StateTree consolidates this into a single, visual, deterministic state machine with sub-frame
response and an editor debugger. The tree becomes the one-writer authority, so duplicate reward/
flag grants become structurally impossible rather than caught by a contract test.

### Constraints (from AGENTS.md — do not violate)

- **QuillScript owns narrative.** StateTree does not replace QuillScript. It orchestrates the
  *side effects* of narrative beats (quest completion, reward grant, flag set, checkpoint) that
  QuillScript already triggers via the seven verb notifications.
- **`UMelodiaNarrativeSubsystem` is only the narrow Quill bridge.** StateTree does not invent a
  parallel narrative authority.
- **`BP_BattleController` lookup path for `RestorePartyAfterBattle` is already wired** on `main`
  via `6715d51`. StateTree drives the same battle controller, not a replacement.
- **The rhythm seam stays single-path.** `UseSkillWithRhythm → ApplyRhythmAttackScalar() →
  InvokeStockUseSkill`, scalar folded into attacker stats **before** dispatch. StateTree does not
  move damage calculation into Blueprint.

### Proposed quest StateTree (per quest chapter)

Each quest gets one `UStateTree` asset. The four P0 quests + `quest.harmony_awakening` are the
first five:

| Quest | StateTree asset (proposed path) | Completion flag | Reward |
|-------|----------------------------------|-----------------|--------|
| `quest.first_dream` | `/Game/MelodiaIntegration/StateTrees/ST_Quest_FirstDream` | `flag.first_dream.quest.completed` | `reward.first_resonance_echo` |
| `quest.wardrobe.equip_outfit` | `/Game/MelodiaIntegration/StateTrees/ST_Quest_WardrobeEquip` | `flag.wardrobe.equip_completed` | `reward.wardrobe.first_outfit` |
| `quest.companion.choral_sheep` | `/Game/MelodiaIntegration/StateTrees/ST_Quest_ChoralSheep` | `flag.companion.choral_sheep_completed` | `reward.companion.choral_sheep` |
| `quest.cutscene.sea_above` | `/Game/MelodiaIntegration/StateTrees/ST_Quest_SeaAbove` | `flag.cutscene.sea_above_completed` | `reward.cutscene.sea_above_memory` |
| `quest.harmony_awakening` | `/Game/MelodiaIntegration/StateTrees/ST_Quest_HarmonyAwakening` | `quest.harmony_awakening.completed` | `reward.harmony_awakening` |

**State flow (all quests):**
```
Idle → Active → Completed → Rewarded
```

- `Idle`: no active quest, entry condition is `ActiveQuestIds` contains the quest id
- `Active`: quest is in progress, driven by QuillScript beats (the seven verb notifications flow
  into `UMelodiaNarrativeSubsystem` → `FMelodiaNarrativeRecord`)
- `Completed`: `CommitQuestCompletion` called exactly once (the existing atomic transaction from
  P0-NARR-01 at `3912f570`); the tree's leaf task is `FStateTreeTask_MelodiaCompleteQuest`
- `Rewarded`: reward id recorded in `ConsumedRewardIds`, flag set in `Flags`, checkpoint recorded

**Enter conditions** read `FMelodiaNarrativeRecord` — same fields the Python contract tests already
assert. The tree does not introduce new state; it *presents* the existing record as a visual state
machine.

### Proposed battle StateTree

| State | Responsibility |
|-------|----------------|
| `Intro` | battle UI appears, encounter configured, Quill paused |
| `PlayerTurn` | player command input (Attack/Skill/Item/Flee), rhythm-timed if applicable |
| `EnemyTurn` | enemy action, mana drain, etc. |
| `Resolution` | damage applied, HP checked, typed result determined (victory/defeat/fled/unavailable) |
| `Outro` | Quill resumes exactly once, branch-conditional on typed result; `RestorePartyAfterBattle` called |

**Grade/scalar as a parameter:** the rhythm timing grade becomes a StateTree parameter passed into
the `Resolution` state, not a branching side-effect in Blueprint. This is what makes
`rhythm_grade_to_result` provable — the grade is an explicit tree input, and the result is an
explicit tree output.

### Integration with the existing P0-NARR-01 atomic commit

The victory branch proven on 2026-08-27 committed, in order:
1. `melodia:quest:melodia_q_echo_01`
2. `melodia:reward:melodia_smoke_reward`
3. `melodia:flag:melodia_smoke_complete:true`
4. `Script 'MelodiaQuillSmoke' ended`

A StateTree quest spine must reproduce this exact order — the tree's `Completed → Rewarded` leaf
calls the same `CommitQuestCompletion` atomic transaction. If the tree produces a different order,
it is a defect, not an improvement.

### Risks (flag before implementing)

1. **Save/load compatibility:** `FMelodiaNarrativeRecord` is the SaveGame bridge. If StateTree
   instance data does not serialize into the same record, the restart-safe save gate breaks.
2. **Blueprint user-defined enums:** `D_DamageType` is still a Python landmine. Any StateTree task
   that touches a skill must be reachable from C++ or `blueprint_query`, never `run_python`.
3. **Live Coding limits:** any StateTree C++ task class is a header change → full closed-editor
   rebuild, always.
4. **One-writer violation risk:** if the tree and QuillScript both write the same flag/reward,
   you've re-introduced the duplicate-grant bug the tree was meant to prevent. The tree must be the
   *only* writer of quest completion side effects; QuillScript triggers the beat, the tree executes
   the side effect.

### Implementation sequence (draft)

1. Define `FStateTreeTask_MelodiaCompleteQuest` C++ task (inherits `FStateTreeTaskBase`)
2. Define `UStateTree` assets for the five quests (editor, Junie's lock)
3. Wire `UMelodiaNarrativeSubsystem` to drive the quest trees from the seven verb notifications
4. Define battle `UStateTree` asset + `FStateTreeTask_MelodiaBattleResolution` C++ task
5. Wire `BP_BattleController` to drive the battle tree instead of its if-chains
6. Verify: each quest tree reproduces the 08-27 atomic commit order; battle tree reproduces the
   four terminal outcomes with Quill resuming once each
7. Record the ledger rows

---

## 5. Native UEditorValidatorSubsystem (long-term scale item 2)

### Motivation

The Python contract tests catch drift *after* the fact — after the asset is saved, after the script
is compiled, after the content is committed. A `UEditorValidatorSubsystem` fires on **every asset
save**, so the class of bug that shipped on 2026-08-27 (four scripts against rejected IDs) becomes
impossible to land in the first place.

### Constraints

- Editor-only: validators run in the editor, not in a cooked build. They gate authoring, not runtime.
- A bad asset can still be cooked if it slips through before the validator is registered.
- Do not weaken a validator to make it green — same rule as the Python tests (fix authority seams,
  never repair assertions).
- The Python tests remain the offline CI mirror — the native validator is the on-save guard, the
  Python test is the reproducible CI assertion. Both must agree.

### Proposed validators (port from existing Python where possible)

| Validator class | Source port | What it guards | Asset filter |
|-----------------|-------------|----------------|--------------|
| `UMelodiaQscAllowlistValidator` | `test_qsc_allowlist_contract.py` `test_every_gated_id_is_allowlisted` | Every `$ Notify melodia:` gated id exists in `DA_MelodiaIntegrationConfig` | `*.qsc` under `Content/MelodiaIntegration/Narrative/` |
| `UMelodiaQuestManifestValidator` | `test_p0_quests_and_content_contract.py` quest manifest checks | Quest spec IDs resolve to existing scripts + flags/rewards in allowlist | `specs/progression/*.v1.json` |
| `UMelodiaUITokenValidator` | `Tools/ui_style_audit.py` token coverage | Widget colors/fonts are within token set, no hardcoded off-palette values | `*.uasset` WBP under `Content/Melodia/UI/` |
| `UMelodiaToonMasterValidator` | `bp_sweep` material checks + `t3d_dashboard` | Toon master instances have valid inputs, correct parent, no broken references | `*.uasset` MI under `Content/EnvSandbox/Materials/Instances/` |

### Implementation shape

```cpp
// Source/BS_GodFile/MelodiaIntegration/MelodiaEditorValidatorSubsystem.h
#pragma once
#include "CoreMinimal.h"
#include "EditorValidatorSubsystem.h"
#include "MelodiaEditorValidatorSubsystem.generated.h"

UCLASS()
class BS_GODFILE_API UMelodiaEditorValidatorSubsystem : public UEditorValidatorSubsystem
{
    GENERATED_BODY()
public:
    virtual bool CanValidateAsset_Implementation(const UObject* Object) const override;
    virtual FEasiValidationResult ValidateLoadedAsset_Implementation(
        const UObject* Object, bool bShowMessages) const override;
};
```

Each validator is a separate method or helper class called from `ValidateLoadedAsset_Implementation`,
filtering by asset class/path in `CanValidateAsset_Implementation`. Return
`FEasiValidationResult` with the appropriate severity (Error for gating defects like an
unallowlisted ID, Warning for near-misses like a token within Δ0.05).

Register in `FMelodiaCoreModule::StartupModule`:
```cpp
void FMelodiaCoreModule::StartupModule()
{
    // ... existing registration ...
    RegisterMelodiaGameplayTags();
    // Validator registered implicitly by being a UEditorValidatorSubsystem child
}
```

### Risks

1. **Editor-only:** validators do not run in cooked builds. They gate authoring, not runtime.
2. **False positives:** a validator that rejects a valid asset blocks the author. Start with
   Warnings for near-misses, Errors only for gating defects (unallowlisted ID, broken reference).
3. **Performance:** validators run on every save. Keep them cheap — read the asset bytes or CDO
   properties, do not open the full graph.
4. **Alignment with Python tests:** if the validator and the Python test disagree, the validator is
   wrong (or the test is). Fix the validator, not the test.

---

## 6. UE 5.8 + Rider workflow (long-term scale)

### The two lanes

| Lane | Tool | Holds | Does |
|------|------|-------|------|
| Editor/C++ | Rider (OpenCode, `bedrock-mantle/qwen.qwen3-coder-next`) | editor lock for PIE/CDO/T3D | header + source edits, Blueprint reads via `blueprint_query`, PIE, T3D injection |
| No-editor | this lane (Solar Pro 4, offline) | nothing | full closed-editor builds, contract tests, docs, skills, git review, planning |

### Live Coding limits (AGENTS.md #15/#21/#22)

- `.cpp`-only edits hot-patch fine via `editor_query live_compile`.
- **Any header change** — new class, new `UFUNCTION`, new `UPROPERTY`, new forward-declared enum —
  **needs a full closed-editor UBT rebuild**. Live Coding `trigger_build` reports
  `patch_applied=true` but ends in `compile_log: 'Live coding failed'` for header changes.
- A file existing is not a file compiling. Before planning around C++ another lane left behind,
  build it.
- Live Coding cannot introduce new imports. If a change calls a symbol the compiled binary never
  imported, it fails with no useful message in the editor log.

### Reading truth (AGENTS.md #18/#20/#24)

- `melodia_config_get_allowlist` (MCP) returns **stale fixture data** — use
  `blueprint_query get_cdo_properties` for config truth.
- A dump cannot prove absence — to establish something is missing, read it through reflection
  (`get_cdo_properties`), not a text search.
- `bRelaxedAllowlistInEditor = true` on `DA_MelodiaIntegrationConfig` lets unregistered narrative
  ids pass with a warning in every non-shipping build; it fails closed only in `UE_BUILD_SHIPPING`.
  Run a verification pass with it off.

### T3D injection workflow (AGENTS.md § Apply workflow, melodia-ui-artist §4)

```
export_graph            -> save it: rollback record AND assertion baseline
get_graph_fingerprint   -> before
<mutate via blueprint_query/ui_query>
compile_blueprint       -> not clean? STOP.
assert_graph_matches    -> matched:false? STOP.
get_graph_fingerprint   -> after; record both
save_asset              -> then re-read live state to confirm (mtime <10min + re-read)
```

Compile order trap: `compile_blueprint` WIPES CDO overrides set before it. Order is always
`compile -> set_cdo_property -> save`. Never compile between set and save.

### Rider as the C++ lane

- Rider is the primary C++ editor. The Rider lane does header + source edits; this no-editor lane
  does the offline build + contract tests + docs.
- When Rider holds the editor for PIE/CDO/T3D, this lane stays strictly offline — builds, tests,
  inventory, docs.
- Rider's model is `bedrock-mantle/qwen.qwen3-coder-next` (long C++, verified working 2026-08-14).
  The Rider lane's `build` agent mode is `primary` (edit: ask, bash: allow); the `plan` agent mode
  is `primary` (edit: deny, bash: ask).

### Single-editor rule (AGENTS.md #7/#17)

- Check `Get-Process UnrealEditor` and that port 9316 has exactly one listener before any editor
  work. Another MCP server does not help — Monolith runs in-process, so a second surface is a
  second writer on the same lock. Decision 025 forbids two MCP surfaces on one graph; this is the
  same hazard one level up.
- `MODAL_OPEN` in the log is not a hang — a modal dialog blocks the game thread, Monolith goes
  silent, Windows reports "Not Responding". Grep for it before concluding the editor is dead.

---

## 7. Git hygiene for backend work

### Before every commit

1. `git status --porcelain` — identify modified/untracked.
2. `git diff --stat` — confirm the churn is the change you intended, not a BOM/reindent artifact.
3. `git diff <file>` — read the diff, not the file.
4. Check for destructive git commands in the diff/log — `git checkout -- .`, `git clean -fd` are
   catastrophic here (AGENTS.md § Never Run These).

### Commit discipline

- One small, verifiable change per session (AGENTS.md #4). Do not `git add -A`.
- Commit messages: `class(short): what` — e.g. `feat(melodia): extend allowlist CDO with 27 P0 IDs`,
  `fix(qsc): flags. prefix typo + duplicate reward grant`.
- Never push to `legacy-melodia`. Upstream is `MelodiaMelusinaV2` on GitHub.

### Risk flags to watch in git review

- Untracked `.uasset` / `.fbx` / `.qsc` — may be new content that needs to be tracked or
  intentionally ignored.
- Modified `.uasset` with no corresponding commit — may be editor work another lane landed without
  committing.
- Stale fixture data in `Fixtures/Blueprints/` — if a fixture drifts from the live asset, the MCP
  tool that reads it lies (e.g. `melodia_config_get_allowlist`).

---

## 8. Evidence standard (the contract every lane must honor)

1. A gate is certified only when `record_gate.py <id> pass` has a ledger row. Prose in a session
   log is not a ledger row.
2. Probe-injected calls are not play evidence — they prove the native seam responds when invoked,
   not that a player pressing keys sees a highway.
3. Frames without a report are not evidence. PNG captures with no accompanying JSON assertion report
   and no committed verifier cannot be re-checked.
4. The committed harness must be the harness that ran. Fix the probe, then rerun. Never paper over it.
5. A committed export is an output, not an input. Verifiers re-derive from the live graph every run;
   do not assert against a stored export (the one exception is `bp_regression_checker.py`, whose
   baseline is tracked at `Docs/T3D_Baseline/bp_fingerprints.json` and hard-fails when missing).

---

## 9. Sequence (what this lane does next, no editor)

1. **Keep reviewing git** — `git status`, `git diff --stat`, `git log --oneline -30` every cycle,
   flag anything risky.
2. **Keep running the contract tests** — `test_p0_quests_and_content_contract` (8/8) and
   `test_qsc_allowlist_contract` (3/4, 1 expected FAIL) every cycle, confirm no regression.
3. **Keep the ledger honest** — if the handoff or the ledger drifts, write the row.
4. **Write the long-term docs** — this plan, the StateTree plan, the validator plan, the
   UE5.8+Rider workflow doc, the monolith/text-injection scale-up doc, the enemy-battle repeat-test
   plan, the UI long-term cleanup inventory.
5. **Create skills** — `melodia-backend` (done), plus any new skill a repeated workflow calls for.
6. **Stop when the editor frees up** — hand off to Junie for the editor-bound work, then resume
   offline when she's done.

---

## 10. File map

| File | Purpose |
|------|---------|
| `Docs/Backend/MELODIA_BACKEND_INTEGRATION_PLAN_2026-08-28.md` | **this file** — single plan for backend work |
| `Docs/Backend/STATE_TREE_QUEST_BATTLE_SPINE_PLAN_2026-08-28.md` | StateTree quest/battle spine detail |
| `Docs/Backend/NATIVE_EDITOR_VALIDATOR_PLAN_2026-08-28.md` | UEditorValidatorSubsystem detail |
| `Docs/Backend/UE58_RIDER_WORKFLOW_LONG_TERM_2026-08-28.md` | UE 5.8 + Rider workflow doc |
| `Docs/Backend/MONOLITH_TEXT_INJECTION_SCALE_UP_2026-08-28.md` | T3D/Monolith batch scale-up doc |
| `Docs/Backend/UI_LONG_TERM_CLEANUP_INVENTORY_2026-08-28.md` | UI asset inventory + gaps |
| `Docs/Handoffs/ENEMY_BATTLE_REPEAT_TEST_PLAN_2026-08-28.md` | Enemy-battle repeat-test plan |
| `.claude/skills/melodia-backend/SKILL.md` | No-editor C++/T3D/contract-test runbook |
