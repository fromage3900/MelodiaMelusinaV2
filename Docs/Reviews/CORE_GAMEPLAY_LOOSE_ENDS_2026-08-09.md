# Core gameplay loose ends — handoff sweep (2026-08-09)

**Scope:** remaining loose ends for the core gameplay loop, extracted from the
Claude/Cline/Kiro/DeepSeek handoffs and re-verified against the live editor this
session. Loop: Quill dialogue → allowlisted encounter → JRPG battle + rhythm →
typed result → resume → save/load.

**Handoffs reviewed:** CORE_SYSTEMS_HANDOFF_2026-08-09, SESSION_CLOSEOUT_2026-08-09,
CORE_LOOP_STATUS_AND_AGENT_PROMPTS_2026-08-07, WIRING_FINALIZATION_STATUS_2026-08-07,
SESSION_CLOSEOUT_2026-08-08, INTEGRATION_POLISH_HANDOFFS_2026-08-06,
CLINE_WIRING_EXECUTION_2026-08-06, KIRO_GAMEPLAY_SYSTEMS_ACCOUNTING_2026-08-01,
DEEPSEEK_B6_QUEST_CHAIN_2026-08-08, DEEPSEEK_SIR_RESCUE_2026-08-08,
PARALLEL_LANES_2026-08-08, ECHO_PIPELINE_2026-08-09.

**Rule applied:** a doc claim that conflicts with a live editor read is stale.
Two handoffs were wrong against the live asset this session; both are corrected
below with the live values.

---

## 1. Fixed this session (data, editor, verified readback)

| Item | Evidence |
|---|---|
| `StockSkillRhythmIds`: `BP_MelusinaPetalCadence_C → cadence_strike` | live CDO readback |
| `BP_MelodiaTravelVolume` created + placed in `L_MelusinaMorning` (exit → `L_Melodia_Dreamstate`, spawn tag `Arrive_FromDreamstate`) | disk reload readback |
| `Encounter_CrystalShard` added to `EncounterIds` | live CDO readback — **unblocks the echo quest chain 1→2→3 at the bridge** |
| `melodia_reward_solstice_drum` + `melodia_reward_dawn_veil` added to `DialogueRewardIds` | live CDO readback — SolsticeDrum/DawnVeil rewards no longer rejected |
| Live battle baselines re-exported; `UseSkillWithRhythm(currentSkill)` verified in the live graph | fingerprint + export |

---

## 2. Correction to a circulated claim

**`Encounter_CrystalShard` is in the allowlist (DeepSeek 08-08, Task 1) — FALSE
against the live CDO.** It was not there when read this session; the DeepSeek
"confirmed in the live CDO" claim is stale or was reverted. Now fixed (see §1).
Verify the runtime half next: exactly one actor tagged `Encounter_CrystalShard`
must exist in the loaded world, and `BattleController_ZenForest` must not create
a second battle authority (bridge requirement).

---

## 3. Remaining loose ends — core gameplay

### 3a. Runtime proofs owed (the four Echo gates — none has a ledger row)

1. **Rhythm→damage delta in PIE** (`runtime`). Campaign 1. Perfect-vs-Miss A/B,
   `MELODIA_RHYTHM session=` line must appear. The data blocker
   (`StockSkillRhythmIds`) is now fixed; the highway *rendering* is the cosmetic
   lane's job, but the session start + scalar latch can be proven without it.
2. **Result matrix** (`runtime`). Victory/Defeat/Fled/unavailable each
   resumes/aborts Quill exactly once. Closure wiring verified connected, never
   played.
3. **Save round trip + repeat consume** (`save_load`, `repeat_consume`). Full
   process restart on `MelodiaJRPGSlot0`; `melodia:stat:` idempotent per IntentId;
   no duplicate reward.
4. **Packaged launch** (`package_launch`). `Saved/StagedBuilds_20260730/` cooks
   clean; `BS_GodFile.exe` never walked Morning → Dreamstate → KaleidoNave
   outside the editor.
5. **Wallet restart-idempotence** (`_TASK_QUEUE` P0). Grant → full process exit →
   relaunch → same grant rejected. In-memory guards double-pay after relaunch.

### 3b. Data/content — open

6. **ZenForestTest encounter verify** — confirm exactly one
   `Encounter_CrystalShard`-tagged actor + bridge contract before claiming quest
   1 is reachable (actor existence is handoff-claimed, not session-verified).
7. **`BP_KaleidoNaveArrivalTrigger` is dead** (verified live): its
   `EventBeginPlay` custom event has no caller and all standard BeginPlay/Overlap
   event nodes are disabled. `MelodiaQuillSmoke` duplicates `MelodiaMorningIntro`
   (same encounter id, same `melodia_smoke_reward`, same flag) with consume-once
   guards making it redundant rather than corrupting. **Decision:** with the
   Morning path now working, retire the arrival trigger + Smoke beat or repoint
   it; do not leave two authored spines on one consume-once id.
8. **RhythmSkillId property** (owner-endorsed, from the core-4 review): make
   skills self-describing; keep the config map as warning fallback. Header change
   → closed-editor build.

### 3c. C++ fixes owed

9. **`CompleteQuest` consumes before broadcast** (`CORE_LOOP_STATUS` §2 item 2) —
   a rejected quest permanently burns its intent. Not confirmed fixed; verify
   ordering in `MelodiaNarrativeSubsystem.cpp` before touching.
10. **Stock `SaveGameToSlot` bypasses `IsSavingAllowed()`** — manual save during
    battle half-guarded (CORE_SYSTEMS_HANDOFF §6).
11. **`LoadCanonicalJRPGSlot` returns `bNarrativeRestored`** — caller cannot
    distinguish "refused" from "loaded, narrative degraded" (CORE_SYSTEMS_HANDOFF
    §6; may be C++ or BP API change).
12. **Hair AnimBP init order** (`Accessed None` ×2-3 per PIE start) — move
    `SetAnimationMode/SetAnimInstanceClass` into `BindToOwnerMesh()`. Known fix,
    not applied. Do NOT add an `IsValid` guard (freezes HeadTransform at
    identity).

### 3d. Design decisions (owner)

13. **No post-battle HP restore + no retry on defeat** — soft-lock vector in a
    20-minute slice. Absence in stock source, not a regression.
14. **`NotifyDeathRecovery` / `NotifyRetryRecovery` / `TrackRhythmSession`** have
    zero call sites — the recovery boundary exists and is never crossed.
15. **Persona UI has zero Blueprint callers** — no quest log, Harmony readout,
    objective or equipment UI bound (owner's UI lane, but it gates
    "quest state visible to the player").
16. **Duplicate content trees** — `_ThirdParty` orphan island (its own
    `BP_BattleController`), 33-asset untracked mirror with the *unfixed*
    shadowed `BP_MelodiaBattleUI`. Deletion needs owner sign-off (untracked =
    unrecoverable).

### 3e. Cleanup / tooling owed

17. **`bp_sweep` full project run** — died in the three-editor incident; scoped
    runs clean. Live assets have **zero** shadowed events; the 304 empty + 239
    dead nodes are dominated by template BPs and the mirror.
18. **17 dead nodes in live `BP_BattleUI`, 34 in `BP_JRPGPlayerController`** —
    accumulated during rhythm integration; cleanup, not gameplay-blocking.
19. **`Saved/T3D/rhythm_pipeline.json` (08-04) is stale and dangerous** — predates
    all current wiring; node ids inside are wrong. Do not plan from it.
20. **`bRelaxedAllowlistInEditor=true`** — run verification passes with it off;
    unregistered ids warn in editor, fail closed in Shipping.

---

## 4. Already correct — do not redo

- Battle-result exactly-once (`CompleteBattle` clears `PendingEncounterId`, sets
  `bBattleCompletionConsumed` before `ResumeQuillOnce`, `AddUnique`).
- `UseSkillWithRhythm` sequencing (montage notify reads the latched scalar).
- Lane input Q/W/O/P both key-down and key-up; `ShowRhythmGrade` signature.
- Sir recruitment chain (flag → strict `NotifySirRescued` → `AddPlayerUnit` →
  probe → unlock), idempotent.
- Quill dialogue context push/pop; travel clears input leaks.
- Traversal obeys `IsMovementAllowed()`; no ad-hoc input modes.
- `HandleQuillNotification` bind (the 08-07 `UFUNCTION` fix) — all seven verbs
  now actually arrive.
