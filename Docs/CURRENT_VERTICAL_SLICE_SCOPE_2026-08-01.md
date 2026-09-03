> # SUPERSEDED - do not plan against this file
>
> **The scope authority is [`_VERTICAL_SLICE_SCOPE.md`](../_VERTICAL_SLICE_SCOPE.md)**
> (named as such by `DOC_INDEX.md:92`, `_TASK_QUEUE.md`, `Docs/QUEUE.md` and both
> `.opencode` agents). This file is dated 2026-08-01 and its filename reads *newer* than
> the authority's, which is precisely why it is dangerous: it is older, and it is wrong.
>
> **The specific contradiction.** Below, under "Proven / current", this file states
> *"The integration battle path is player-proven"*. The owner's live verification on
> 2026-08-06 (`_VERTICAL_SLICE_SCOPE.md:45-50`) says the opposite: *"Quill dialogue is not
> visible, battle systems are non-functional, and the game is unplayable."* A later
> 2026-08-12 update restores rhythm and QuillScript only - **not** the battle path,
> save/load, or packaging.
>
> Kept for history: its loop description and the "music you cannot fail at" thesis are
> still the design intent and are quoted elsewhere. The **status claims are not current**.
>
> Banner added 2026-08-14.

# Current Vertical Slice Scope — 2026-08-01

## The actual shipping slice

**New Game → Morning → authored Quill beat → Dreamstate → one stock JRPG encounter → one typed result → return/exploration/save.**

The slice is exploration-forward, with dialogue at seams and presentation reinforcing the emotional arc. Its thesis is **music you cannot fail at**: rhythm and VFX may enrich a successful stock outcome but may never reduce, delay, or gate one.

## Proven / current

- New Game is player-proven and creates the canonical stock save before travelling to Morning.
- Morning Quill, native departure, Dreamstate traversal, and Zen Forest arrival are player-proven.
- The integration battle path is player-proven; stock JRPG retains commands, damage, target response, result, and turn release.
- The live Storybook Outline master is active on the showcase maps. Candidate grade/sky/Niagara assets are not promoted.

## Finish before expanding

1. Prove one complete terminal result with save/load persistence and no duplicated reward/UI/input.
2. Prove the full Result matrix separately: Victory, Defeat, Fled, and unavailable.
3. Wire and live-test one representative one-way stencil presentation response (the renderer setting and `SetReactiveStencil` build gate are now closed).
4. Resolve/diagnose the PPV screen-rectangle artifact with the PostProcessing-off test.
5. Approve candidate PPV/Niagara only through same-camera A/B and fixed-camera cost checks.
6. Launch-test the existing staged package before calling the slice portable; cook/package generation already succeeds.

## Explicitly deferred

- Recursive expedition/roguelike generation and its save schema.
- Broad Dissonance profiles, combat modifiers, and accessibility system expansion.
- New party/recruit systems, wardrobe progression, elements, toughness, and social-stat gates.
- A second rhythm, save, quest, travel, battle, or post-process authority.
- The 12-hour/four-movement outline remains a north-star reference, not a production task list.

## Emotional and visual guardrails

- Sir is alive, benignly absent, and retrievable.
- The past duet-partner remains fragmentary and absent.
- No animal harm, corpse/reveal, guilt framing, diagnosis text, grief meter, or punishment loop.
- Morning is warm/held; Dreamstate is strained but readable; Zen Forest offers hopeful answer/response.
