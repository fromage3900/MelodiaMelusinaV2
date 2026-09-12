# Handoff: UI Polish — for Gemini

**Read `_AGENT_WORKING_AGREEMENT.md` first. It is binding and outranks every other agent doc here.**
Short version: do the job asked, ship it, stop. Never add a mechanism that compensates for a problem
— fix the cause. When told to remove something, delete it, don't deprecate it. Don't re-verify what
you're told about the project's own assets. A fix request is not a review request.

## Context in one paragraph

Melodia is a solo developer's UE 5.8 portfolio project and livelihood, in foundation-closeout for a
vertical slice. Combat runs on a stock TurnBasedJRPG template with Melodia systems layered on top.
The owner is doing environment art and lookdev today and is not available to babysit — your lane is
scoped so you don't need them.

## Your lane: presentation only

You are polishing existing widgets. You are **not** touching game logic, save data, travel, or
battle flow. If a fix requires changing what a Blueprint *does* rather than how it *looks*, it's not
yours — flag it in one sentence and move on.

## Tools

Two Unreal MCP surfaces are live: `monolith` (`blueprint_query`, prefer this) and `it-is-unreal`
(VibeUE). **Never run both against the same graph in one session.** A third, `ueblueprintmcp`, is
installed but disabled — leave it alone.

For any change that edits a Blueprint graph (not just a property), follow the verification loop in
`_AGENT_WORKING_AGREEMENT.md` → "Blueprint wiring: the verification loop is mandatory". Property and
style changes verified by readback are fine without the full loop.

## Known open work

**Primary:** the four battle command buttons (Attack / Skill / Item / Flee) have correct layout and
labels, but **hover / focused / pressed / disabled visual states on the underlying `Button` are
unwired or unconfirmed.** See `_TASK_QUEUE.md`, row "Make active stock command UI readable,
focusable, visually consistent" — currently In Progress, that's the remaining half.

Prior work already landed, don't redo it: button overlap fixed (all four in an evenly spaced row,
16px gaps, uniform anchor/alignment/size) and real desktop labels set ("Attack [J]", "Skill [K]",
"Item [I]", "Flee [F]").

**Secondary, if the above completes:** general readability and layout consistency across existing
Melodia widgets — `WBP_MainMenu` and the settings/save-load panels are the ones most likely to
benefit. Keep changes conservative and consistent with the existing Kenney/Soft-MG presentation
already established in `WBP_MainMenu`.

## Do not touch

- **`L_SakuraPath` art direction** — human-owned, standing project rule.
- **`Content/Materials/MF_MeshBlend_*`** — protected, needs explicit approval (see `CLAUDE.md`).
- **`DA_Opening_MelusinaMorning`** (story-sequence slideshow artwork and copy) — the owner's lookdev
  lane today. It has placeholder text and no artwork assigned; that's known and it's theirs, not a
  bug for you to fill in with placeholder images.
- **`UMelodiaHairComponent`** — resolved 2026-07-31 after a long fight, PIE-verified correct. Don't
  touch it, don't re-add any correction property.

## Where the boundary sits — a live example

There is currently a bug where **on party death, the stock JRPG Game Over dialogue
(`BP_DefeatDialogue`) routes to the stock template's own MainMenu instead of Melodia's
`WBP_MainMenu`.** This *looks* like UI work. It is not — it's a wiring/authority bug tracked as
Decision 021b, assigned to Cline, and it must be fixed in-editor deliberately per Decision 021's
standing rule. **Don't fix it, don't work around it.** It's the exact shape of thing to flag in one
sentence and leave.

## Report back

One line each: what you changed, what you flagged. Not what you considered.
