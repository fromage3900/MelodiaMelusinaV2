# DeepSeek API — Reimbursement Request (Prep Doc) — 2026-08-18

**Status**: PREP — complete the placeholders marked **[FILL]** before sending.
**Send to**: DeepSeek Platform billing/support (platform.deepseek.com → Billing
/ Support). See §Submission.

---

## 1. Request summary

**[FILL: Account email / API key suffix]**
requesting a credit/refund for inference tokens consumed by **failed and
redundant API calls** during an automated Unreal Engine editor scripting session
on **2026-08-17 20:00 – 2026-08-18 05:30 UTC** (approx.). The failures were
caused by script/runtime errors on the client side (an AI coding agent driving a
live UE 5.8 editor via remote Python execution), not by DeepSeek service
availability. The request is for the *wasted* portion of usage: calls that
returned errors, crashed mid-execution, or were immediately re-run due to agent
errors.

## 2. Incident description

An automated agent session performed material/graph authoring inside the UE 5.8
editor. The session generated an abnormally high volume of requests because of
a recurring failure loop:

1. Editor Python executions failing at runtime (attribute errors, API
   mismatches, serialization crashes) — each failed attempt still consumed the
   full request round-trip.
2. **Repeated full rebuilds** of the same material graph (3 consecutive failed
   attempts, then the successful one) — each attempt is a large token spike.
3. **Repeated 83-instance authoring passes** run twice due to a verifier bug.
4. **Repeated 424-texture imports** run three times (path + naming fixes).
5. **Multiple level load/save cycles across 9 levels** (config, apply, revert,
   verification) — each level operation is a large context payload.
6. Repeated shader-compile investigations (log greps, debug-dump reads,
   forced-dump experiments) after earlier "verify" steps incorrectly reported
   success.

All of this was single-session, low-value output; most of it was thrown away
(reverted or superseded).

## 3. Wasted-call inventory (evidence with timestamps, UTC)

Times from `Saved/Logs/BS_GodFile.log` on 2026-08-18 (UTC). Approximate — the
exact request count must be taken from the DeepSeek usage dashboard for the
range in §1.

| When (UTC) | Operation | Failure / waste | Evidence |
|---|---|---|---|
| 04:21:33–04:22:10 | Material polish script | JSON serialization crash after edits → full re-run | log L46205–L46239 |
| 04:34:34–04:35:00 | Scratch shader-dump lab + 41-input rebuild | Compile failures (undeclared identifiers) — the "clean" check had missed them | log; `Saved/ShaderDebugInfo/` |
| 04:35:00 / 04:35:09 / 04:35:24 | Ink master rebuild (3 attempts) | Stale module cache; `MaterialExpressionDot` missing; `SceneTextureId` int() — 3 full graph rebuilds | log L46946+ |
| 04:35:57 | Ink master rebuild (final) | Heavy but productive | — |
| 04:38:06–04:43 | Grade inputs | Connect-before-set bug → compile failure → full re-run | log; dump `2_165019fd422a61ab` |
| 04:45–04:52 | Verify + live-stack probes | Recompile/verify loops; async-compile races required re-checks | `Saved/Audit/dreamprint_*.json` |
| 05:00–05:07 | ZenForestTest + level probes | 4+ level loads, 2 audit scripts, 1 crashed texture audit | log; audits |
| 05:06 | Dream-candidate apply | 9 level loads + saves — later reverted (discarded) | `dream_candidate_ppv_apply.json` |
| 05:19–05:22 | Grade wiring fixes | 1 crashed run (lib.connect), proof-dump timing miss → 2nd read | logs, audits |
| 05:27 | PPV revert + verification | 9 level loads + saves + 9 read-backs (damage control) | `ppv_stack_revert_2026_08_18.json` |
| (earlier) | Atlantis authoring | 83-MI authoring pass re-run twice due to verifier bug; 424-texture import run 3× | `Saved/Audit/atlantis_*.json` |

## 4. Request

A credit/refund equal to the tokens consumed by the failed/redundant calls
above (items marked "waste" in the inventory). **[FILL: token totals + USD from
the usage dashboard for the date range]**.

## 5. [FILL] — what to confirm before sending

- [ ] API key / account identifier (suffix is enough)
- [ ] Exact date range: 2026-08-17 20:00 UTC → 2026-08-18 05:30 UTC
- [ ] Usage dashboard: request count + input/output tokens + billed amount for
      the range; compute the "wasted" share using the inventory above
- [ ] DeepSeek support address / form (platform billing page or
      support@deepseek.com — confirm current route)
- [ ] Attach: this doc, plus (optional) the log excerpt file and the
      `Saved/Audit/*.json` manifests referenced above

## 6. Submission

1. Fill §1 and §5.
2. Export the referenced audit JSONs and a log excerpt into one folder
   (e.g. `Docs/DeepSeekReimbursement/`).
3. Send via the DeepSeek platform support channel with subject:
   "Reimbursement request — failed API calls 2026-08-17/18 (agent scripting
   errors)".
4. Keep a copy of the sent version in `Docs/Handoffs/`.
