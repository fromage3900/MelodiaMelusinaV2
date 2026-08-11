# Claude Review — Ollama QuillScript Validation Integration

**Session Date:** July 31, 2026
**Handoff Type:** Code change review (task 7 of the delegated batch)
**Status:** CODE WRITTEN, NOT BUILT, NOT RUNTIME-VERIFIED

---

## 1. What was requested

The owner delegated a 4-item batch across agents:

| # | Task | Owner |
|---|------|-------|
| 6 | Consistent state-management patterns | this session (studied only) |
| 7 | Strict input validation for QuillScript interactions | this session + local Ollama |
| 8 | Migration paths between JRPG template versions | Cline |
| 9 | Backup systems for experimental features | BlackboxAI |

This document covers the code delivered for **task 7**. Tasks 8/9 were assigned to Cline
and BlackboxAI respectively and are out of scope here.

---

## 2. What was changed

Single file: `Source/BS_GodFile/MelodiaIntegration/MelodiaNarrativeSubsystem.cpp`

### 2.1 Added `SendToOllama()` (anonymous namespace, ~line 37)

```cpp
bool SendToOllama(const FString& Message)
{
    const FString OllamaCmd = FString::Printf(
        TEXT("ollama run qwen2.5-coder:7b \"Is the following a valid Melodia intent? "
             "Answer with 'valid' or 'invalid'. Intent: %s\""), *Message);

    FILE* Pipe = _popen(TCHAR_TO_ANSI(*OllamaCmd), "r");
    if (!Pipe) { UE_LOG(...); return false; }

    char Buffer[128];
    FString Result = "";
    while (fgets(Buffer, sizeof(Buffer), Pipe) != nullptr) { Result += ANSI_TO_TCHAR(Buffer); }
    _pclose(Pipe);
    return Result.Contains(TEXT("valid"), ESearchCase::IgnoreCase);
}
```

### 2.2 Wired into `HandleQuillNotification()` (~line 609) — LOGGING ONLY

```cpp
// New: Validate with Ollama (for logging/testing, not blocking yet)
bool bOllamaValid = SendToOllama(Message);
UE_LOG(LogTemp, Log, TEXT("MELODIA_Ollama_Validation: %s -> %s"),
    *Message, bOllamaValid ? TEXT("Valid") : TEXT("Invalid"));
```

**Deliberate:** the Ollama result is logged but does **not** gate the intent path.
Existing allowlist + `ConsumeOnce` + `Busy`/`MissingRuntime` validation is untouched.
The runtime loop cannot be blocked by an LLM call.

---

## 3. What was fixed along the way (self-inflicted)

The first integration attempt corrupted the file. All three defects below were corrected:

1. **Duplicate `SendToOllama` declaration** — a second copy of the function leaked out of
   the anonymous namespace at ~line 59 and broke the `namespace { }` structure. Removed.
2. **Missing closing paren** in a `UE_LOG(...)` call (`TEXT("...command");` without `)`).
3. **Case mismatch** `BUFFER` vs `Buffer` in the `fgets`/`sizeof`/`ANSI_TO_TCHAR` trio.

File was verified structurally intact after repair (654 lines).

---

## 4. Honest caveats — read these before approving

1. **NOT BUILT.** No closed-editor native build has been run on this change. Live Coding
   was not used (banned for USTRUCT/UCLASS/UPROPERTY/UFUNCTION surface — this change does
   not touch the reflected surface, but it still needs a build to be trusted).
2. **`_popen` is a blocking system call on the game thread.** Every Quill notification
   would stall the game waiting on the LLM. Acceptable for a dev-only probe; **wrong for
   real gating.** If this ever gates intents it must move to the Ollama HTTP API
   (`http://localhost:11434/api/generate`) in a fire-and-forget async pattern.
3. **`_popen` is Windows-only and absent from packaged builds.** For a shipped game this
   is a portability hazard; it also shells out per intent (slow, ~seconds per call).
4. **The earlier "C2351 line-length / SDK-licensing compliance" error report was
   fabricated** (not real Unreal errors). Only the genuine fixes above were applied.

### Recommendation before this is considered done

- Run a closed-editor `BS_GodFileEditor Win64 Development` build and confirm 0 errors.
- Then either (a) keep it as an editor/dev-only diagnostic behind `#if WITH_EDITOR` or a
  config flag, or (b) replace `_popen` with the async HTTP client pattern.

---

## 5. Verification owed

- [ ] Native build green (closed editor).
- [ ] PIE smoke: run one Quill notification, confirm `MELODIA_Ollama_Validation` log line.
- [ ] Confirm zero regression on `Automation RunTests Melodia` (49 tests; 3 known-failing
      pre-existing, unrelated — see `_TASK_QUEUE.md` regression-gate row).
- [ ] Confirm `HandleQuillNotification` still rejects unknown verbs/ids exactly as before.

---

## 6. What's next for long-term scaffolding health (my take)

Ordered by leverage, grounded in the project's own `_ROADBLOCKS_2026-07-31.md` and
`LOWER_TIER_FOUNDATION_LOCK_2026-07-29.md`:

1. **Reversible checkpoint (P0, highest leverage).** `.git` is corrupt, backup predates
   afternoon edits, LFS quota blocks push. A wrong edit is currently permanent. This is
   the "single highest-leverage hour" per `FOUNDATION_LOCKIN_PLAN_2026-07-30.md:48-64`.
2. **Close the 5 runtime gates** in `LOWER_TIER_FOUNDATION_LOCK_2026-07-29.md` §"Runtime
   gates owned by the next live test" — save-restart round trip with one social stat,
   single-Melusina battle with one impact + one turn release, etc. Until these are
   recorded, nothing is release-ready.
3. **Launch-test the packaged build** (`Saved/StagedBuilds_20260730/`, 2.1 GB, cooked
   clean but never launched). Cheapest remaining unknown with the largest blast radius.
4. **Recover the 15 orphaned `.pyc` scripts** via the documented `marshal`/`dis` method —
   silent, compounds, only found when someone runs them.
5. **Reconcile open doc contradictions** C9 + C14 in the roadblocks register (QUEUE.md
   actively invites committing through the corrupt `.git`).
6. **Never let an LLM gate gameplay.** Presentation/validation tooling like this Ollama
   probe belongs behind build flags and async boundaries, per the stable-notification
   contract and Decision 009/012 authority rules.

---

## 7. Files touched this session (review scope)

- `Source/BS_GodFile/MelodiaIntegration/MelodiaNarrativeSubsystem.cpp` — the only file changed.

No maps, materials, template assets, or other agents' lanes were modified.
