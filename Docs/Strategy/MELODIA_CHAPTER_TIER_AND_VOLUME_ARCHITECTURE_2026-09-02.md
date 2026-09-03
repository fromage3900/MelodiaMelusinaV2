# Melodia — Tiered Chapter & Volume Architecture

**Date:** 2026-09-02  
**Status:** CANONICAL CONTENT-STRUCTURE GUIDANCE  
**Companion:** `Docs/Strategy/MELODIA_ENDLESS_JOURNEY_NORTH_STAR_2026-09-02.md`

---

## 1. Why the chapter model changed

The previous front-facing docs described one identical six-phase loop for every Chapter. That loop remains a useful **P0 integration proof**, but it is too rigid to define a long-lived RPG.

Melodia now uses **tiered authored units**. Some Chapters are intimate and cheap; some are mechanical episodes; some are major arcs; rare Monolith Events earn reality-breaking payoffs. This preserves impact and prevents every content unit from requiring a new biome, boss, outfit ability, and subsystem.

---

## 2. Tier permissions

| Tier | Typical duration | New mechanical permission | Typical purpose |
|---|---:|---|---|
| Reverie / Interlude | 10–30 min | None; reuse existing systems | attachment, breathing room, Starskiff life, outfit/creature stories |
| Episode | 20–60 min | Variant or new application of an existing system | one memorable gameplay proposition |
| Chapter | 45–120+ min | One meaningful verb/extension at most | multi-episode arc, persistent state change |
| Movement | 3–6+ h | Existing systems recombine into a new grammar | major thematic act and worldview shift |
| Monolith Event | 20–60 min direct interaction | Prefer no new global subsystem | assumption-breaking culmination earned by prior content |
| Volume | elastic | no mandatory new permanent runtime | emotionally complete game-scale journey |

**Production rule:** the higher the narrative spectacle, the less new foundational code it should require.

---

## 3. Seven metadata fields for every Chapter

Every mainline Chapter should be legible through seven fields:

1. **Narrative Question** — what is emotionally/world-conceptually being asked?
2. **Mechanical Focus** — which existing verb or narrow extension carries play?
3. **Character Focus** — whose relationship changes?
4. **Location** — where does the chapter live?
5. **Visual Signature** — one image the player should remember years later.
6. **Persistent Change** — what durable fact survives the chapter?
7. **Exit Image** — the visual/emotional handoff into the next unit.

A Chapter that cannot answer these should not be promoted into the mainline plan.

---

## 4. Monolith pacing rule

Monoliths are **events, not routine bosses**.

A Monolith Event may invalidate exactly one assumption the player previously treated as fundamental.

Working escalation:

- Sea Above — **water may be anatomy**.
- Faraway Mother — **fabric may be landscape / draped anatomy**.
- God That Molts — **geology may be discarded biology**.
- Horizon Eater — **distance / adjacency may be feeding anatomy**.
- Later events must find a new category error rather than merely increasing physical size.

Do not place giant reveal after giant reveal. Preferred pacing alternates:

`intimate → curious → dangerous → intimate → weird → personal → Monolith → silence`.

The quiet aftermath is part of the payoff.

---

## 5. Volume I working 52-chapter grid

This is a **planning grid, not a requirement to ship exactly 52 units**. Numbers are useful for long-term placement and can be split/merged during production.

### Movement I — The First Answer (1–13)
1. The Empty Perch
2. The Quiet Chirp
3. A Note Answered
4. Morning After Silence
5. The Restless Echo
6. What the Echo Leaves Behind
7. The Resonant Weave
8. Harmony in Middle C
9. The Shore Before Evening
10. The False Ocean
11. Celestial Tide
12. Shorewake
13. The Sea Above / Starskiff Departure

### Movement II — The World Reads Back (14–26)
14. Blue Wake
15. The Lantern Mooring
16. Mara Elletra Vell
17. What Are You Wearing?
18. The Seam Map
19. The Hemlands
20. The Pleated Range
21. The Embroidered Basin
22. A Night of Repairs
23. The Veiled Mountains
24. Resonance in the Folds
25. The Far Horizon
26. The Blink

### Movement III — The Category Error (27–39)
27. After the Blink
28. The Amber Ravine
29. Iris Fen
30. Things That Curl When Warmed
31. Catalyze
32. A Useful Kind of Rot
33. The Same Pattern, Larger
34. The Molt Field
35. The Empty Carapace
36. Open Country
37. The Measure of Distance
38. Glasswing
39. The Horizon Eater

### Movement IV — The Shape We Choose (40–52)
40. Normal Water
41. The House of Measures
42. The Shape of a Door
43. Tide
44. Anchor
45. Bell
46. The Girl in Every Mirror
47. The Seam Oracle
48. Refuse the Measure
49. The Last Dress Appears
50. Pilgrimage Along the Hem
51. The World Turn
52. The First Time She Is Not Late

The exact names and placements beyond currently canonized content remain owner-editable. The architecture—not every title—is canonical.

---

## 6. Chapter-system relationship

A Chapter package may use only the systems it needs. It does **not** have to contain dialogue + music puzzle + combat + outfit reward + checkpoint in that exact order.

Examples:

- A Reverie may be `Quill + exploration + save` only.
- A creature Episode may be `world interaction + rhythm + consequence`, with zero battle.
- A combat Chapter may spend most of its time in Phoenix + MelodiaCore.
- A Starskiff Chapter may be vehicle traversal + party dialogue + environmental state.
- A Monolith Event may be authored world-state transitions and traversal with no conventional enemy HP.

The reusable contract is **state ownership and chapter packaging**, not identical moment-to-moment structure.

---

## 7. Reusable chapter package contract

Every durable Chapter should converge on the existing reusable validation architecture:

- `specs/progression/<chapter>.v1.json` — stable IDs, prerequisites, beats/objectives, route, checkpoints, source refs;
- optional pillar manifests (wardrobe, creatures, world state, encounter, audio, etc.);
- checked-in Quill source where narrative is required;
- explicit persistent facts and idempotent intent/reward IDs;
- offline contract tests;
- live/PIE proof where runtime behavior matters;
- restart/load proof for durable state;
- packaged proof before release promotion.

A Chapter is not production-complete because its assets exist. It is complete when its durable state and exit contract survive the runtime.

---

## 8. Long-term content economy

The goal is not 50 Chapters that each cost a new game.

Approximate healthy distribution for a 50+ chapter Volume:

- ~25–35% Reveries / Interludes;
- ~35–45% focused Episodes;
- ~15–25% major Chapters;
- only a handful of Monolith Events / final syntheses.

Reuse is a feature. Returning to changed places should be emotionally valuable, not read as content deficiency.

---

## 9. Anti-feature-creep rule

After the core runtime is locked, new Chapters should prefer:

1. **new authored content using existing verbs**;
2. **new combinations of existing verbs**;
3. **narrow chapter-local extensions**;
4. only then, with strong evidence, a new permanent subsystem.

If a planned Chapter requires a parallel combat authority, second save system, fifth wardrobe track, or another global UI writer, redesign the Chapter.

---

## 10. Volume completion rule

A Volume ending must stand on its own.

Future content may recognize the player's durable history, but it must not retroactively turn the ending into a cliffhanger that requires an update to become meaningful.

The desired long-term rhythm is:

`complete journey → live in the world → something new arrives → choose whether to journey again`.
