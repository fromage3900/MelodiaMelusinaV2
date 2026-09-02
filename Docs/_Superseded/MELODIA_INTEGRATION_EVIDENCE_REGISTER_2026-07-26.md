# Melodia Integration Evidence Register

**Date:** 2026-07-26  
**Purpose:** distinguish proven state from plans, inference, and missing proof  
**Architecture:** `MELODIA_UE58_INTEGRATION_ARCHITECTURE_2026-07-26.md`

## Evidence grades

- **Runtime-proven:** observed interactively by a human or reproducible runtime
  capture.
- **Tool-proven:** direct editor/source/build query supports the bounded claim.
- **Compile-proven:** compilation/load succeeded; behavior remains unproven.
- **Planned:** acceptance criteria exist but have not passed.
- **Rejected:** evidence contradicts suitability for the selected role.

## Foundation register

| Claim | Grade | Evidence | Remaining proof |
|---|---|---|---|
| Standalone JRPG template functions in its original runtime | Runtime-proven | User completed battles and verified party, quest, turn, and UI behavior | Preserve a short capture/checklist if desired |
| Complete JRPG source has 412 content packages | Tool-proven | Isolated source inventory: 409 assets + 3 maps | None for package-count claim |
| JRPG Blueprints compile in UE5.8 | Compile-proven | 0 errors, 0 warnings, 0 load failures after seven package repairs | Repeat after any integration mutation |
| JRPG maps initialize in UE5.8 | Tool-proven | `MainMenu`, `Gameplay`, and `BattleMap` load and begin play unattended | Interactive flow |
| JRPG battle result is an asynchronous integration seam | Tool-proven | `BP_BattleBase.OnBattleOver(Result)` and `OnBattleRemoved` | Runtime callback-count observation |
| JRPG controller owns party/inventory/quests/input/battle state | Tool-proven | Live variables/functions on `BP_JRPGPlayerController` | Runtime mutation regression |
| JRPG save owns canonical gameplay state | Tool-proven | `BP_JRPGSaveGame` variables and load function | Interactive save/load and packaged build |
| JRPG save is ready for narrative persistence | Planned | No schema version or narrative record currently exposed | Design, migration, duplicate-reward tests |
| Conversation2D is a hard template dependency | Rejected | Complete UE5.8 lab has no reference and compiles without it; only two optional sample widgets carry the name, neither with `/Script/Conversation2D` serialized | Exclude the two sample widgets |

## Presentation register

| Claim | Grade | Evidence | Remaining proof |
|---|---|---|---|
| Production Melusina AnimBP is safe for isolated JRPG use | Rejected | Hard MelodiaCore/Kawaii/custom-version dependencies and UE5.8 Property Access assertion | None; use clean adapter |
| Clean lab AnimBP compiles | Compile-proven | 0 errors/warnings; validation clean | Runtime montage playback |
| Experimental swordsman adapter preserves JRPG inheritance | Tool-proven | Child of `BP_SwordsmanPlayerUnit`; validation clean | Disposable battle |
| Basic attack montage is compatible with Melusina skeleton | Tool-proven | Montage/sequence resolve to `SK_Melusina_Skeleton` | Visual playback |
| Attack has one authoritative impact | Tool-proven | `AM_Mocap_BasicAttack` has exactly one `BP_UseSkillN` notify at user-approved 4.5 s | Disposable battle telemetry |
| Attack resolves once and releases turn | Planned | Test specification exists | Interactive telemetry |
| Heal follows the same contract | Planned | Candidate assets identified | Only after attack passes |

## QuillScript register

| Claim | Grade | Evidence | Remaining proof |
|---|---|---|---|
| Quill 2.5 editor target builds in UE5.8 | Compile-proven | Source target build succeeds; runtime/editor DLLs produced | Rebuild after future edits |
| Both Quill modules load | Compile-proven | UE5.8 commandlet/module load | Interactive editor/runtime |
| Runtime plugin content compiles | Compile-proven | No runtime asset compile failures | Runtime playback |
| Full plugin Blueprint content is clean | Planned | `StatementBP` stale enum switch remains | Refresh/resave editor viewer |
| Dialogue/options/variables/labels work in UE5.8 | Planned | Source fixture and smoke spec created | Import and play |
| Async adapter callback can pause/resume once | Planned | Source API supports lifecycle/callback flow | Disposable adapter test |
| Unknown intents fail safely | Planned | Rejection contract specified | Runtime negative test |
| Quill can package for UE5.8 | Planned | No Development package yet | Cook/build/launch |
| Quill should own canonical save | Rejected | Own global/history state and slot helpers overlap JRPG save | Use versioned project record |

## ACFU register

| Claim | Grade | Evidence | Remaining proof |
|---|---|---|---|
| ACFU 4.2.3 is a broad action-RPG framework | Tool-proven | 46 declared source modules and overlapping public systems | None for architecture classification |
| ACFU is suitable as a small JRPG combat add-on | Rejected | Combat depends conceptually on controller/actions/targeting and duplicates RPG authorities | Reconsider only after explicit action-RPG pivot |
| ACFU UE5.8 compatibility is proven | Planned | Source targets 5.7; no isolated 5.8 build performed | Separate lab only if route changes |
| ACFU save/quest/dialogue should be cherry-picked | Rejected for current route | Directly duplicates selected JRPG and Quill concerns | No work while JRPG route active |

## MelodiaCore register

| Claim | Grade | Evidence | Remaining proof |
|---|---|---|---|
| MelodiaCore contains salvageable concepts and presentation hooks | Tool-proven | Source and prior integration reviews | Evaluate one bounded concept at a time |
| MelodiaCore is stable enough to own production gameplay | Rejected | User runtime observation; historical regressions; dependency-heavy AnimBP failure | Requires independent stabilization project before reconsideration |
| Existing presentation interfaces prove visible feedback | Rejected | Prior live inspection found zero implementers | Use JRPG-native presentation adapter |
| Rhythm should control base turn/damage flow | Rejected for MVP | Conflicts with deterministic stable authority and corrected scope | Optional bounded experiment after vertical loop |

## Scope register

| Requirement | Status | Authority |
|---|---|---|
| Portfolio-first render push | Active | `QUEUE.md`, `PROJECT_STATUS_2026-07-25.md` |
| Small authored fixed loop | Active | Integration architecture |
| VN/dialogue candidate | QuillScript, gated | Quill lab/spec |
| Turn-based battle | JRPG authority | JRPG lab/spec |
| Melusina character presentation | Adapter, gated | Character-skill slice |
| One outfit identity/affordance | Later vertical-loop proof | Integration architecture Phase 5 |
| Procedural roguelike MVP | Superseded | Historical plans only |
| ACFU action combat | Rejected for selected route | ACFU archive only |
| MelodiaCore gameplay authority | Rejected | Selective salvage only |

## Current blockers versus normal pending work

No architecture-research blocker currently prevents progress.

Normal pending evidence:

- human selection of the attack contact frame;
- interactive JRPG UE5.8 acceptance;
- interactive Quill import/playback;
- packaged Development builds;
- narrative save-schema design and migration;
- disposable integrated dialogue/battle slice.

None of these pending items authorize production mutation during portfolio
rendering.
