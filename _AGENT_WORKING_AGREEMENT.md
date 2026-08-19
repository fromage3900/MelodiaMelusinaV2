# Agent Working Agreement

**This is binding. It outranks every other agent doc in this repo.**

This project is a working portfolio and a livelihood. It is not a sandbox for demonstrating
technique. When the owner asks an agent to do something, it is because they want the task done —
not because they want an analysis, a framework, or a conversation about it.

---

## The five rules

### 1. Do the job asked. Ship it. Stop.

The request is the scope. Not the request plus what you noticed on the way.

If you finish early, stop. Finishing early is the goal, not an invitation to keep going.

### 2. Never add a mechanism to compensate for a problem. Fix the problem or say you can't.

If your fix introduces a new property, flag, branch, or corrective step whose only purpose is to
cancel out something else's behaviour, **the fix is wrong**. Delete the cause instead.

Compensation layers compound. Three of them and nobody can tell what the code does any more.

### 3. When told to stop or remove something, remove it. Fully. Immediately.

"Kill it" means delete it. Not deprecate it, not gate it behind a flag, not leave a stub with a
comment. Delete it and rebuild.

### 4. Do not investigate what you have already been told.

The owner knows their own assets, rig, and files. If they say "the bones are correct" or "I fixed
the origin", that is ground truth. Do not go verify it. Do not read logs to check. Act on it.

### 5. A fix request is not a review request.

Reviews, audits, refactors and "while I was in there" cleanups happen only when explicitly asked
for. If you spot something real while fixing, note it in **one sentence** at the end and move on.

---

## Stop conditions — you are scope-creeping if any of these are true

- You are on your third tool call and have not yet changed the thing you were asked to change.
- You are reading logs, parsing assets, or enumerating files to confirm something the owner stated.
- You are writing a comparison table, a ranking, or a "recommended order" for a one-line fix.
- You are proposing a design where the ask was a repair.
- You are explaining *why* something broke at greater length than the fix itself.
- Your answer contains the phrase "before I do that, let me check…" for a task that is already clear.

When one of these is true: stop, make the change, build it, report in three lines.

---

## Code smells this project has already been burned by

Each of these appeared in `UMelodiaHairComponent` and cost roughly three days:

| Smell | What it actually was |
|---|---|
| A tunable corrective transform applied at runtime | Cancelling out a snap the same function had just performed |
| A `bForce…` bool that makes another property apply anyway | An override for a guard that existed for a good reason |
| A branch concluding "touch nothing", followed by code that touches it | Two authors disagreeing inside one function |
| A one-tick defer to dodge an initialisation race | Ordering bug papered over instead of fixed |
| Runtime-only correction invisible in the viewport | Guarantees the bug only appears on Play, where it is hardest to diagnose |

**The eventual fix was three lines: snap the mesh to the head bone.** Everything above was
scaffolding built to avoid doing that.

---

## What "done" looks like

1. The change is made.
2. It builds.
3. You said what you changed, in a few lines.

Not: what you considered, what you ruled out, what you noticed nearby, what you recommend next.

If the change genuinely cannot be made — missing information, blocked by something real — say so in
one or two sentences and stop. Do not substitute investigation for the blocked work.

---

## Blueprint wiring: the verification loop is mandatory, not optional

This applies to every agent, every tier, no exceptions: if you are adding, removing, or rewiring
nodes in a Blueprint graph through Monolith, VibeUE, or UEBlueprintMCP, you follow this loop —
documented in full at `Plugins/Monolith/Docs/MONOLITH_GUIDE.md` Recipe 15:

```
export_graph            -> save it: rollback record AND assertion baseline
get_graph_fingerprint   -> before
<mutate>
compile_blueprint       -> not clean? STOP.
assert_graph_matches    -> matched:false? STOP.
get_graph_fingerprint   -> after; record both
save_asset
```

**"Not clean" or "matched:false" is a hard stop, not a retry trigger.** Do not attempt a second fix
without checking in. Trying a different approach on a graph you have not confirmed the state of is
exactly the compounding-fix pattern that turned a three-line hair fix into three days — see the
worked example above. Report what failed and what you saved (the `export_graph` payload is your
rollback record); do not iterate blind.

**Before any of the above, on a fresh session:** call `get_graph_fingerprint` twice on an untouched
graph and once after a no-op resave. Require byte-identical hashes. If it is not stable, stop and
report — do not proceed to graph surgery on an unproven assertion tool.

**One asset per transaction.** Never mutate a second Blueprint before asserting the first landed.

This is not extra ceremony. It is what makes autonomous wiring safe to hand off unsupervised, which
is the entire point of having it.

---

## Escalation is a failure mode, not thoroughness

A simple request that becomes a multi-stage engagement has failed, even if every stage was
individually competent. Cost is measured in the owner's time and attention, not in tokens or tool
calls.

The correct response to "just fix X" is a fixed X.

---

## P0 Finalization rules (2026-08-17) — binding while P0 is open

1. **Ship the task asked, then stop.** Scope is the queue row, nothing else. No "while I was in
   here" work. Finishing early is the goal.
2. **No compensation layers.** A fix that adds a property, flag, branch, or corrective step whose
   only purpose is to cancel another system's behaviour is wrong. Delete the cause.
3. **No new BP authorities or systems during P0.** The integration foundation is closed. Nothing
   new is introduced until the Core P0 golden run is accepted.
4. **One editor. Always.** Verify `Get-Process UnrealEditor` and one listener on 9316 before any
   editor work. Never start a second editor or second MCP surface.
5. **Ledger or it did not happen.** A task is done only when a ledger row or a `Saved/` evidence
   envelope exists. Prose in a session log is not evidence.
6. **Never destructive.** No `git clean`, no `git checkout -- .`, no `delete_asset` on work you did
   not create. No commits or pushes unless the owner asks.
7. **Fail = record and stop, never mask.** A golden-run failure is captured with evidence and
   reported. Gameplay BPs are never edited to hide a route failure (contract
   `forbidden_shortcuts`).
