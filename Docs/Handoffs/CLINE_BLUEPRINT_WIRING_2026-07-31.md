# Handoff: Blueprint Wiring — for Cline

**Read `_AGENT_WORKING_AGREEMENT.md` first. It is binding, outranks every other agent doc in this
repo, and applies to you specifically.** Short version: do the job asked, ship it, stop. Never add a
mechanism that compensates for a problem — fix the cause. When told to remove something, delete it,
don't deprecate it. Don't re-verify what you're told about the project's own assets. A fix request is
not a review request.

**Also read the "Blueprint wiring: the verification loop is mandatory" section of that same file
before touching any graph.** It is not optional and it is not a suggestion — a failed
`compile_blueprint` or `assert_graph_matches` is a hard stop, not a "let me try something else"
trigger. That exact pattern — compensating instead of stopping — is what turned a three-line hair fix
into three days of work on this project. Don't repeat it.

## Project context, in one paragraph

Melodia (this repo) is a solo dev's UE 5.8 portfolio project and livelihood, currently in
foundation-closeout for the "First Dream" vertical slice. The native C++ is green and tested. What's
left is Blueprint wiring — connecting systems that already exist in code but aren't hooked up in the
editor. `Docs/BLUEPRINT_WIRING_CHECKLIST_2026-07-30.md` is the checklist. Item 1 (hair) is done —
**do not touch `UMelodiaHairComponent` again**, it's correct and PIE-verified.

## Your tools

Two Unreal MCP surfaces are live: `monolith` (namespace-dispatch, `blueprint_query`, ~114 Blueprint
actions, prefer this) and `it-is-unreal`/VibeUE (~150 flat tools, use when Monolith can't do
something). **Never run both against the same graph in one session.** A third, `ueblueprintmcp`, is
installed but disabled by default — leave it that way unless you hit something neither of the other
two can do, and say so before enabling it.

**Before touching any graph, prove the verification tool works:** call `get_graph_fingerprint` twice
on an untouched graph and once after a no-op resave. Require byte-identical hashes. If it's not
stable, stop and report — do not proceed to graph surgery on an unproven tool.

## Order of work

### 1. Config + actor-property writes (do first — no graph surgery, safest)

**Status 2026-07-31: config half DONE by opencode.** `TravelLevelIds` now contains
`melodia_integration_map` + `/Game/EnvSandbox/Environments/L_KaleidoNave`; `SocialStatIds` now
contains `melodia_harmony`. Readback-verified and saved; `list_dirty_packages` empty. **PlayerStart
tagging still pending** — see note below.

- ~~Allowlist `/Game/EnvSandbox/Environments/L_KaleidoNave` in
  `DA_MelodiaIntegrationConfig -> TravelLevelIds`.~~ DONE
- Tag KaleidoNave's PlayerStarts via `PlayerStartTag`/`Tags` — at minimum the one the
  merged Dreamstate content should arrive at. **Do not guess the tag value.** The spawn tag is
  consumed by `UMelodiaTravelSubsystem::PlacePawnAtSpawn` (matches `PlayerStartTag` OR `Tags`), and
  no dialogue currently emits `melodia:travel:` at all — so the arrival-tag value is an authoring
  decision that must match what the KaleidoNave dialogue will emit. The four PlayerStarts should be
  inventoried first (`mesh.get_level_actors` with class filter `PlayerStart`), and the arrival tag
  chosen against the actual merged content, not picked out of thin air.

  **Inventory result 2026-07-31 (opencode):** there are **two** PlayerStarts, not four — `NaveStart`
  (persistent level, loc `[200,0,760]`) and `Dreamstate_PlayerStart` (merged Dreamstate sublevel, loc
  `[9,10,741]`). Both have empty `PlayerStartTag` and empty `Tags`. `Dreamstate_PlayerStart` is the
  natural arrival target for merged content; the tag value it should carry is still an authoring
  decision gated on the KaleidoNave dialogue's travel notification.
- ~~Add a social stat ID (e.g. `melodia_harmony`) to `SocialStatIds`.~~ DONE
- Verify each by readback (`get_cdo_properties`, `get_component_details`,
  `mesh.get_actor_properties`) — these are data writes, no fingerprint/assert loop needed for these
  specifically. Config readback already done and recorded in `_ROADBLOCKS_2026-07-31.md`.

### 2. STOP — two bugs found today, fix or understand them before routing anything to KaleidoNave

The owner merged Dreamstate mechanics into KaleidoNave for traversal consistency. Two problems came
with that merge:

**Bug A — the merged Dreamstate BPs are placed in KaleidoNave but don't function.** Placement
survived the merge; behavior didn't. Likely causes to check, in order of likelihood:
- BeginPlay logic in the Dreamstate BPs that referenced the old standalone map by name or assumed a
  GameMode that KaleidoNave doesn't use.
- Trigger volumes that lost their bindings when moved/duplicated into the new level.
- A Level Blueprint reference that didn't carry over on the merge.

Use `export_graph` on the relevant BPs *as placed in KaleidoNave* to see current state. If the old
standalone Dreamstate map still exists, diff against what those same BPs did there — that's your
fastest path to the actual cause.

**Bug B — on party death, the stock TurnBasedJRPG template's own menu fires instead of
`WBP_MainMenu`.** This is very likely a fourth instance of a pattern already tracked three times in
this project (`_DECISION_LOG.md` Decision 021: stock-template defaults that should have been
replaced by Melodia's own systems, still live). Filed as candidate `021b` — find the Blueprint that
actually owns the Game Over → menu transition (search for the stock result-matrix Blueprint, or
whatever `BP_BattleController` calls on party wipe) before touching anything. Once you've found the
specific asset, that's what completes Decision 021b's entry.

**Do not proceed to item 3 below (the `Open Level` swap) until both of these are fixed, or you've
written down a specific reason you're deferring them.** Routing travel to a level that doesn't work
on arrival isn't progress.

### 3. Replace `Open Level` nodes with `TravelTo` (first real graph surgery)

`UMelodiaTravelSubsystem` is the single travel authority (Decision 023) — allowlist validation,
spawn-tag placement, input-context clear on arrival. Any direct `OpenLevel` call bypasses all of
that. Full loop, from `MONOLITH_GUIDE.md` Recipe 15 — follow it exactly:

```
export_graph            -> save this. Rollback record AND assertion baseline.
get_graph_fingerprint    -> before
<mutate: add TravelTo call, remove OpenLevel>
compile_blueprint        -> not clean? STOP. Report, don't retry blind.
assert_graph_matches     -> spec.forbidden_nodes: [{class: K2Node_CallFunction, function: OpenLevel}]
                          -> matched:false? STOP.
get_graph_fingerprint    -> after; record both
save_asset
```

One asset per transaction — don't touch a second Blueprint before the first is asserted clean.

### 4. Input contexts (six widgets — the riskiest step, do it slowly)

`UMelodiaInputContextSubsystem` is the single input/focus authority. Six widgets need
Push/PopContext wired on their open/close paths, per the checklist's §3. **Do exactly one widget,
fully, PIE-verify it (cursor appears/disappears correctly, movement gates correctly), before
touching the other five.** This is explicitly called out because a batched destructive graph edit
across six assets on an unproven pattern is how a small mistake becomes six small mistakes.

### 5. Rhythm wiring

Quartz clock start + one `RecordInputNow()` call at skill confirm. Verify with
`melodia.Rhythm.Disable 1` in console — output must be bit-identical with the flag on vs off
(Decision 016: rhythm is cosmetic/expressive only, it never gates an outcome, and if disabling it
changes anything you've built the wrong thing).

## Not yours

- **Item 5b** (naming the Quill social-stat intent) — persisted in save records forever once
  written, that's a human naming decision.
- **Item 5c** (binding Quill dialogue to ZenForest NPCs) — blocked on an unresolved Decision 021
  content leak in `ZenForestTest.umap`; that cleanup is explicitly human, in-editor, deliberate, per
  the decision itself. Don't script around it.
- Content: the story-sequence slideshow's artwork/copy (`DA_Opening_MelusinaMorning`) is the owner's
  lookdev lane, not code work.

## Report back

One line each: what you fixed, what you deferred and why. Not what you considered, not a design
doc — the working agreement means brief and factual.

---

# ADDENDUM 2026-07-31 — answers to your scope question

Your live-graph read was correct and it changed the plan. Answers below; **Decision 028** in
`_DECISION_LOG.md` is the authoritative record.

## Your open question: A or B → **B.**

Swap `_10` (`ChangeMapForBattle`) and `_46` (`ChangeMap`). **Leave `_30` and `_52` — the two
`currentMap` save/load legs — on stock `OpenLevel`.**

Three reasons:

1. **Domain.** Decision 009 gives the stock JRPG controller save authority. `_30`/`_52` restore a
   destination from `currentMap` in the save record. Gating those behind Melodia's *authored-travel*
   allowlist makes Melodia's config the gate on stock save-restore — a second authority reaching
   into a domain 009 already assigned. Authored travel (a designer picked this destination) and
   save-restore travel (replay a state that was already valid) are different questions.
2. **Failure mode.** `TravelTo` returning false is a silent no-op. Under A, the player hits Continue
   and nothing happens. That's the worst possible failure on the primary re-entry path of a
   portfolio piece.
3. **A's completeness is false anyway.** MelodiaCore holds **seven** more direct `OpenLevel` calls
   (`OrreryMainMenuGameMode.cpp:380,388,397,422,449`, `MelodiaSirMelodiousIntroActor.cpp:205`,
   `MelodiaOpeningPortal.cpp:45`) that `TravelTo` structurally cannot reach — it lives in the game
   module, MelodiaCore is a plugin. Picking A to "finish the job" wouldn't finish it.

**Stated cost of B, so it's not a hidden gap:** save-restore travel does not get spawn-tag placement
or the input-context clear. Real, accepted, filed. Unifying `_30`/`_52` later means: enumerate every
reachable `currentMap` value → allowlist them all → verify nothing hard-fails → *then* swap. Its own
task, not this one.

## Your other items — agreed, with two corrections

- **Item 1 (fix `blueprint_path`→`asset_path` in your commands doc) — yes, do it.** Your doc, your
  fix.
- **Item 2 (tag `Dreamstate_PlayerStart`) — yes, proceed.**
- **Item 3 (per-leg rebuild) — yes, but only `_10` and `_46` per Decision 028.** Your read that this
  is a node rebuild rather than a retarget is correct — static `UGameplayStatics::OpenLevel` vs.
  instance `TravelTo` off a subsystem getter is a different node shape entirely. Branch on the bool
  return and log on false, as you proposed.
- **Item 4 (`BP_DefeatDialogue` re-file) — correct, and you already updated Decision 021b with the
  traced asset. Keep it a separate transaction**, exactly as you said. Do not let it ride along in
  the item-3 graph edit.
- **Item 5 (`MelodiaOpeningPortal.cpp:45`) — CORRECTION: not a quick fix, and not yours.** That file
  is in MelodiaCore, a plugin; `UMelodiaTravelSubsystem` is in the `BS_GodFile` game module. Routing
  it through `TravelTo` would invert the plugin→game dependency. It needs a design decision (move
  the subsystem into MelodiaCore, or expose an interface it can call) — **do not add a
  `MelodiaCore.Build.cs` dependency on `BS_GodFile` to make it compile.** Filed in `_TASK_QUEUE.md`
  as "Travel authority cannot reach MelodiaCore". My earlier claim that `MelodiaSaveSlotLibrary` was
  "the last direct `OpenLevel`" was wrong — it was the last one *in the game module*. That comment
  is now corrected in source.
- **Item 6 (four review findings) — agreed: log as follow-ups, don't fold into item 3.** Add them to
  `_TASK_QUEUE.md` as their own rows so they're visible rather than living in a report.

## One process note

You asked before acting on a scope question with real consequences, and you traced
`BP_DefeatDialogue` to a specific asset instead of guessing. That's exactly right — keep doing that.
The working agreement's "do the job and stop" is about *unrequested expansion*, not about
suppressing a question when the answer genuinely changes what gets built.
