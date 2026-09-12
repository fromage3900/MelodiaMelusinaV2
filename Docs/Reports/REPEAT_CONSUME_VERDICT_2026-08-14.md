# `repeat_consume` — source verdict, 2026-08-14

**VERDICT: PASS on source — the idempotence contract is correctly implemented. The gate is
open for lack of a runtime row, not for lack of a fix.**

Produced by Bedrock Lane 2 (`cpp` → `qwen.qwen3-coder-next`, $0.0033, `AWS_PROFILE=bedrock`)
**and then verified line-by-line against the source**, because the model's headline finding
was wrong. See §3 — that verification is the point of this document.

---

## 1. The contract, and where each half lives

`melodia:stat:` intents are consumed **once per `IntentId`**, not per `StatId`, and the
record must survive a save/load round trip.

| Element | Location | State |
|---|---|---|
| `ConsumeOnce(TArray<FName>&, FName, FString&)` | `MelodiaNarrativeSubsystem.cpp:114-122` | Checks `Contains` **before** `Add`. Correct. |
| `ConsumedIntentIds` | `MelodiaNarrativeTypes.h:109` | `UPROPERTY(... SaveGame ...)` — **serialized** |
| `ConsumedRewardIds` | `MelodiaNarrativeTypes.h:116` | `UPROPERTY(... SaveGame ...)` — **serialized** |
| Social-stat key | `MelodiaNarrativeSubsystem.cpp:262` | `social-stat:<IntentId>` — keyed on **IntentId** |
| Reward consume | `MelodiaNarrativeSubsystem.cpp:242` | `ConsumeOnce(ConsumedRewardIds, RewardId, …)` |
| Quest guard | `MelodiaNarrativeSubsystem.cpp:164-167` | `Contains` rejects a genuine repeat **before any work** |

## 2. The four questions, answered

**1. Any path that awards before recording consumption?**
`GrantDialogueReward` and `GrantDialogueSocialStat` both consume **before** broadcasting —
no window. `HandleQuestNotification` broadcasts before recording, **deliberately** — see §3.

**2. Any path where `ConsumedIntentIds` is written but not serialized?**
No. Both consume arrays are `SaveGame`-flagged, and
`MelodiaIntegrationTests.cpp:180,211` already assert the round trip.

**3. Per-IntentId or accidentally per-StatId?**
**Per-IntentId**, correctly. `social-stat:<IntentId>` means two different dialogue beats may
each award Harmony +1, while replaying either beat after resume/load is a no-op — which is
the authored intent, stated in the comment at `.cpp:259-261`.

**4. Container/lookup issues?**
Keys are `FName` throughout, compared via `TArray<FName>::Contains`. `FName` comparison is
case-insensitive in UE, which for an idempotence guard **fails safe** — a case variant is
treated as the same intent and rejected, rather than slipping through as a second award.

## 3. The model's headline finding is wrong, and the code says so in advance

Lane 2 reported as its #1 issue: *"Award before consumption (crash window for double award)"*
at `HandleQuestNotification`, because `OnQuestRequested.Broadcast(QuestId)` (`.cpp:169`)
precedes `ConsumedIntentIds.Add(...)` (`.cpp:188`).

That ordering is deliberate and the reasoning is in the file at `.cpp:171-178`:

> *"Consume only if a listener actually moved the quest. … Consuming before the broadcast
> burned the intent anyway, and because `ConsumedIntentIds` is SaveGame-flagged the burn
> survived reloads — the quest could never be accepted later even once its prerequisite
> was met."*

A quest with an unmet prerequisite is Locked, so Persona no-ops. Consume-first permanently
burns that intent across reloads and the quest becomes unacceptable forever. The current
order fixes a real shipped bug. **Applying the model's "fix" would reintroduce it.**

The repeat case is still guarded: `.cpp:164` rejects a duplicate before any work, and the
`bQuestIsActive == bQuestWasActive` check at `.cpp:180` leaves the intent unconsumed when no
transition occurred, so it can be retried.

This is `AGENTS.md` rule 20 in the wild — the same failure mode as the `StockSkillRhythmIds`
incident. The model also self-corrected twice mid-answer ("Wait — it **is** here!"), which is
why the Bedrock handoff's "model output is never evidence" line is not boilerplate.

## 4. What actually closes the gate

Nothing in C++. `repeat_consume` needs a **real run**:

1. Replay the same authored beat twice in one session → second occurrence is a no-op.
2. Save → **fully exit the editor** → relaunch → load → replay → still a no-op.
3. Confirm no duplicate reward and no duplicate dialogue award.
4. `python Tools/record_gate.py repeat_consume pass --note "<evidence>"`.

Step 2 is the one that has never been exercised. An in-memory guard that double-pays after
relaunch is exactly what this gate exists to catch — and the source says that guard is
serialized, so the expectation is a pass.

## 5. Incidental fix

`Saved/router_ledger.jsonl` had two JSON objects concatenated on one line, which made
`model_router.py cost` crash with `JSONDecodeError: Extra data`. Repaired in place (3 rows
recovered; backup at `router_ledger.jsonl.bak_20260814`). The writer at
`model_router.py:436` does append `\n`, so the likely cause is **two parallel lanes appending
at once** — plausible in this project. Left the reader strict on purpose: a lenient parser
would hide the next occurrence instead of surfacing it.
