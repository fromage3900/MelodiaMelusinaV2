# Bedrock lane handoffs — ledger + gate work

Copy-pasteable prompts for the now-working Bedrock models, aimed at the three open
completion gates. Verified live 2026-08-14: `cpp` 5/5 PASS, `deep` 4/4 PASS.

**Default model: `qwen.qwen3-coder-next`** (bedrock-mantle). Set `AWS_PROFILE=bedrock`
before any of these. A real run of Lane 4 on 2026-08-14 found **no ledger/prose
contradictions** — and typo'd a year (`20206-08-13`) while reasoning past it, which is
the concrete reason the "model output is never evidence" rule below is not boilerplate.

## The constraint that shapes every prompt here

`Tools/model_router.py chat <class>` is a **single-shot text call**. These models have
**no tools, no filesystem, no editor, no repo access**. They cannot read a file, run a
gate, or write a ledger row.

So every lane below is *reasoning over context you paste in*, producing text you then act
on. Do not write a prompt that assumes the model can look something up — it will invent
the answer. That failure already cost this project once: a dump-based conclusion that
`StockSkillRhythmIds` had no entry, when it had one the whole time (`AGENTS.md` rule 20).

**Nothing these models produce is evidence.** A gate closes when `record_gate.py` writes a
row backed by a real run. Model output is a plan, a review, or a draft — never a pass.

## Usage

```bash
AWS_PROFILE=bedrock python Tools/model_router.py chat <class> --prompt "..." --json
```

Paste file contents into the prompt. Cost is recorded per call in
`Saved/router_ledger.jsonl`; check with `python Tools/model_router.py cost`.

---

## Lane 1 — `save_load` gate design (`deep` → kimi-k2-thinking)

The next completion gate. Long, stateful, spans C++ and Blueprint — which is what
`kimi-k2-thinking` is for.

```
You are reviewing a UE 5.8 save/load implementation for a gate that requires a canonical
BP_JRPGSaveGame slot to survive a FULL PROCESS RESTART (not just a level reload).

Context I am pasting: <paste MelodiaNarrativeSubsystem.h/.cpp save-related sections, the
BP_JRPGSaveGame variable list, and any SaveGame call sites>

Produce, in this order:
1. The exact write path: what is serialized, when, and by whom.
2. Every place state could be held in memory and never written.
3. A concrete restart test procedure with observable pass/fail assertions -- what a human
   must see on screen or in the log for each step.
4. The three most likely reasons this fails on a real restart, ranked, with the specific
   symptom each produces.

Do not assume anything not present in the pasted text. Where you need a fact I did not
give you, say "NEED: <the fact>" instead of guessing.
```

## Lane 2 — `repeat_consume` idempotence (`cpp` → qwen3-coder-next)

`melodia:stat:` is idempotent per **IntentId**, not per StatId — recorded in
`FMelodiaNarrativeRecord::ConsumedIntentIds`. The gate is that a flag and a reward restore
without duplication.

```
Review this UE 5.8 C++ for idempotence bugs. The contract: melodia:stat: intents must be
consumed exactly once per IntentId, tracked in FMelodiaNarrativeRecord::ConsumedIntentIds,
and must survive a save/load round trip so replaying an authored beat after a reload is a
no-op.

<paste HandleQuillNotification + the ConsumedIntentIds read/write sites>

Identify, with the specific line for each:
1. Any path that awards before recording consumption (crash window = double award).
2. Any path where ConsumedIntentIds is written but not serialized.
3. Whether the check is per-IntentId or accidentally per-StatId.
4. Container/lookup issues -- case sensitivity, whitespace, FName vs FString comparison.

For each finding give the exact input sequence that triggers the double-consume. If the
code is correct, say so plainly rather than inventing a problem.
```

## Lane 3 — `package_launch` failure triage (`cpp`)

Cook and package failures are long log-reading tasks, ideal for a cheap coder model.

```
This is a UE 5.8 Development package/cook log. Find the FIRST real error -- not the first
line containing the word "error", which in UE cook logs is usually a warning cascade from
an earlier root cause.

<paste the last ~400 lines of the cook log>

Return:
1. The root-cause line, quoted, with its line number.
2. What it actually means, in one sentence.
3. The fix, specific to the asset or setting named.
4. Which later errors are downstream noise from it.

Known landmine in this project: an overlong serialized name once caused cook exit 25
(PCGEx_PathTesselate, invalid name at index 411). If you see something similar, say so.
```

## Lane 4 — ledger honesty audit (`audit`)

The recurring failure this repo has paid for repeatedly: prose asserting a state the
ledger contradicts.

```
You are auditing consistency between an evidence ledger and project prose.

LEDGER (authoritative): <paste `python Tools/record_gate.py --list` output>
PROSE: <paste the top section of _TASK_QUEUE.md and AGENTS.md "Next work, in order">

Report ONLY contradictions -- a gate the ledger says passed but the prose calls open, or
vice versa. For each: quote both sides, and state which is authoritative and why.

Rules:
- The ledger wins. Always.
- "Structure verified" is NOT "runtime verified". Flag anywhere prose collapses the two.
- Do not suggest improvements or restructuring. Contradictions only.
```

## Lane 5 — fresh-eyes verification (`review`)

Run this **against another model's output**, before acting on it. Cheap, and it catches
the confident-but-wrong answers that have burned this project.

```
Another model produced the analysis below. Your job is to find where it is wrong or
overconfident -- not to agree with it.

<paste the other model's output>

For each claim, mark one of:
  SUPPORTED  -- the pasted context proves it
  UNSUPPORTED -- plausible but not proven by what was given
  CONTRADICTED -- the context actually shows otherwise

End with the single claim that would be most expensive to act on if wrong.
```

---

## Model selection

| Class | Model | Use for |
|---|---|---|
| `cpp` | `qwen.qwen3-coder-next` | C++/Blueprint review, log triage. Cheapest good coder. |
| `cpp` (2nd) | `qwen.qwen3-coder-480b-a35b-instruct` | Same, when the 30B-class answer looks thin |
| `deep` | `moonshotai.kimi-k2-thinking` | Long multi-step reasoning, save/load design |
| `audit` | local Ollama first, then free tiers | Contradiction hunting. **Slow first call** — Ollama cold-starts; use `cpp` if you want fast turnaround |
| `review` | `grok-4.5` / Bedrock tail | Fresh-eyes verification of another model's output |

**Claude on Mantle is not wired yet** — `anthropic.claude-*` rejects `/v1/chat/completions`
and needs `/v1/responses`. Left unwired rather than half-wired.

## Cost

At the measured ~745K tokens/month these lanes are **well under $1/month**. The $200 of
credits is roughly two years. Do not pick a worse model to save money here; pick the one
that gets the answer right the first time. The budget alarm
(`melodia-monthly-guard`, $25/mo) will tell you long before anything matters.
