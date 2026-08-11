# Handoff: Persona-Lite Remaining Lanes — for Qwen / DeepSeek

**Read `_AGENT_WORKING_AGREEMENT.md` first. It is binding and outranks every other agent doc here.**
Short version: do the job asked, ship it, stop. Never add a mechanism that compensates for a problem
— fix the cause. When told to remove something, delete it, don't deprecate it. Don't re-verify what
you're told about the project's own assets. A fix request is not a review request.

## Context in one paragraph

Melodia is a solo developer's UE 5.8 portfolio project and livelihood, in foundation-closeout for
the "First Dream" vertical slice — a compact Persona-lite loop: conversation → traversal → one stock
JRPG encounter → typed result → narrative consequence → save. Combat runs on a stock TurnBasedJRPG
template (Decision 009: it owns turns, damage, results, inventory, save). Melodia systems layer on
top without taking those authorities. The owner is doing environment art today; your lane is scoped
to run without them.

## Coordination — read this before claiming anything

Two other agents are working in parallel:
- **Cline** — Blueprint wiring (travel, input contexts, rhythm, the KaleidoNave bugs).
- **Gemini** — UI polish (battle command button visual states).

**Check `_TASK_QUEUE.md` before claiming a row.** If it's claimed, pick something else. If Cline has
already run the `get_graph_fingerprint` stability check this session, don't repeat it — read their
session note first.

## Tools

Two Unreal MCP surfaces are live: `monolith` (`blueprint_query`, prefer this) and `it-is-unreal`
(VibeUE). **Never run both against the same graph in one session.** `ueblueprintmcp` is installed
but disabled — leave it. For any Blueprint graph edit, the verification loop in
`_AGENT_WORKING_AGREEMENT.md` is mandatory, not optional.

## Your lane

### 1. Skybound Refrain's conditional bonus (last co-op mechanic)

`BP_SirSkyboundRefrain` is a stock `BP_FocusAttack` child, mapped to Sir at level 1. It needs its
conditional bonus wired: **when `BP_Resonance` is present on the target, apply the bonus; when it
isn't, normal damage.** `BP_MelusinaPetalCadence` already applies Resonance through the stock
`ApplyBuffs` flow, so the buff exists and lands — you're reading it, not building it.

**Constraint (Decision 009):** this must go through stock battle authority. No custom damage
callback, no MelodiaCore combat controller, no parallel damage path. If you find yourself adding a
second thing that computes damage, stop — that's the exact violation that got a whole component trio
quarantined on 2026-07-30 (Decision 011).

**PIE test to close it:** Petal Cadence → Resonance applied → Skybound Refrain → bonus damage → turn
releases. Then Sir *without* Resonance → normal damage.

### 2. Sir's battle mesh, portrait, and skillAnimation

Sir has no visual identity in battle yet. Assign mesh, portrait, and the `skillAnimation` entry for
Skybound Refrain. Straightforward data assignment — verify by readback.

### 3. Save round trip across a full process restart — the standing gate

This gates everything downstream. The pieces are in place: `FMelodiaNarrativeRecord` is v2,
`SocialStats` is canonical and `SaveGame`-flagged, `MigrateRecord` handles versioning, and the
`melodia:stat:` intent is wired end-to-end in C++ (tested — `MelodiaIntegrationTests.cpp`,
`NarrativeRecord.SaveFlags` drives the record through a SaveGame-filtered archive).

What's unproven is the **runtime** round trip: set a social stat → save → **full process exit** →
relaunch → load → value intact. Not PIE-restart. Full process restart.

**Blocked on Cline** landing item 5a (adding a social stat ID like `melodia_harmony` to
`SocialStatIds` in `DA_MelodiaIntegrationConfig`). Don't duplicate that work — check the task queue,
wait for it, then run the test.

### 4. Quest-authority investigation — **investigate only, do not merge**

There are two quest authorities in this project:
- `UMelodiaPersonaSubsystem` (game module) — the modern Persona-lite owner.
- `MelodiaQuestManagerBase` (MelodiaCore, quarantined lane per Decision 020).

The second is **not** dead code. It's actively referenced by `MelodiaOpeningFlowSubsystem.cpp/h`,
`MelodiaSaveGame.h`, `MelodiaSaveGameSubsystem.cpp`, and `MelodiaNPCInteractionComponent.cpp/h` —
all live files sitting in the save and opening-flow critical path.

**Your deliverable is a report, not a merge.** Answer: is
`MelodiaOpeningFlowSubsystem`'s dependency on `MelodiaQuestManagerBase` load-bearing (e.g. save-file
back-compat, an existing save that would break) or is it safely repointable to
`UMelodiaPersonaSubsystem`? Cite file:line. **Do not change anything.** Merging blind here risks
save-file corruption, and Decision 020 explicitly chose guard-in-place over a bulk move after a
content scan proved `.umap`/`.uasset` files reference classes a C++-only grep called dead.

## Not yours

- Anything Cline or Gemini has claimed in `_TASK_QUEUE.md`.
- `UMelodiaHairComponent` — resolved and PIE-verified 2026-07-31, do not touch.
- Naming the Quill social-stat intent (persisted in saves forever — human decision).
- Binding Quill to ZenForest NPCs (blocked on a Decision 021 content leak, human/in-editor).
- The story-sequence slideshow's artwork and copy — owner's lookdev lane.

## Report back

One line each: what you completed, what you're blocked on, and for item 4, the finding with
file:line citations. Not a design document.
