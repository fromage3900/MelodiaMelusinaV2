# Poitou P0 Golden Walk — Morning → House → Village → Canal

**Date:** 2026-10-21  
**Entry:** [POITOU_START_HERE.md](../../POITOU_START_HERE.md) · [House / terrain convergence plan](POITOU_MELUSINAS_MORNING_CONVERGENCE_2026-10-20.md)  
**Purpose:** an **8–12-minute, exploration-led, artist-approved playable opening** using existing Melodia systems. This is a bounded **experience script**, **not** a new level/quest/subsystem authority or a claim that these beats are already implemented.  
**Search:** `POITOU_P0_GOLDEN_WALK`, `Melusina Bedroom`, `Morning golden path`, `First Dream handoff`, `canal landing`.  
**Current technical evidence:** [CURRENT_STATE.md](../../CURRENT_STATE.md) exclusively; mark every new beat `PROPOSED` until proved in the live editor.

## Decision in one sentence

The player **wakes in a single handcrafted bedroom, finds an emotionally meaningful resonance cue, crosses a curated sliver of her house, steps into a real-feeling Poitou village, has one human encounter, and reaches a canal-side departure point**. Outside this path, Poitou can be a deep and evocative **backdrop** without being in the P0 playable envelope.

### Production constraint: two different proofs

1. **Experience P0 (this document):** one authored route, approximately ten minutes, strongest art/animation/audio and responsive interaction; no forced combat or new gameplay mechanic required before the village departure.
2. **Existing First Dream golden-run integration P0 (must remain intact):** [`specs/p0/core_p0_dream_golden_run.v1.json`](../../specs/p0/core_p0_dream_golden_run.v1.json). Canonical player route is Morning → `/Game/EnvSandbox/Environments/L_KaleidoNave`; the integration proof map `/Game/MelodiaIntegration/Maps/MelodiaIntegrationMap` is **not** the player route; encounter, Quill, save/restart and idempotency must still pass. The old standalone Dreamstate route is marked retired in that contract. **Do not replace or silently rewrite it with this scenic route.**

This creates one artistic promise and one engineering proof. A first beautiful ten-minute traversal does **not** certify combat/save/packaged proof; conversely a green integration map does **not** certify the experience.

## 0. Spatial budget and strict exclusions

```text
BEDROOM (one contained authored room)
  bed + desk/window + companion/perch focal point + resonant object
  [wake] → [notice] → [one response] → exit
                         │
                         ▼
HOUSE (one connected showcase route, not every room)
  landing/vestibule → oval salon (one interactable) → front doors
                         │
                         ▼
POITOU (one wayfinding corridor with a short optional side pocket)
  house terrace → stone lane/bridge → small village focal point
       → Petal Priestess/approved existing dialogue placement
       → pollarded-ash canal path → jetty/barque/exit framing
                         │
                         ▼
EXISTING FIRST DREAM HANDOFF / TESTED CONTINUATION
  hand to the currently approved authored route; preserve current map and
  Quill/encounter/checkpoint ownership — no new episode system.
```

**Hard route limits:**
- Bedroom: **1 playable room, 2 optional inspections, 1 mandatory cue**, and the exit. No multi-floor bedroom maze.
- House: **one vestibule/landing + one resonant salon + one exit**, optionally a glimpse of the Listening Tower, other rooms behind closed doors. The full house model can exist around it; don't require it all explorable.
- Village: **one principal street, one bridge or canal-side crossing, one NPC, one readable canal destination**. Up to **one** optional exploration pocket (e.g., market bench/garden nook); no sprawling open-town objectives.
- Mandatory player actions **at most three**: a companion/perch or meaningful object inspection, one resonance input, one existing dialogue/choice. Normal traversal/door use doesn't count.
- **No new combat, swimming, fishing, flight, traversal unlock, escort AI, second World Compiler, separate save authority, village economy, interiors for every home, or Sea Above assets.** Reserve Atlantean kitbash for Sea Above.
- The wider village may be seen but P0 edges are legible canals, hedges, walls, bridges, doors and gentle guidance—not a sudden invisible barrier in camera view.
- Doors must have clear affordances; no mandatory pixel-hunt, wait timer or punitive rhythm fail. Failed resonance input simply invites retry.

## 1. Moment-by-moment playable score (target 10:00, timing is a design target)

| ID / target window | Place, staging and purpose | Required **player verb** | Emotional / visual payoff | Implementation owner + exact pass |
|---|---|---|---|---|
| **M00 · 0:00–0:40** | **Wake** — controlled bedside camera; hush, light through one stained-glass window | Move/look after a short playable intro; optional skip | Pastel watercolor dawn resolves into a calm room; Melusina is grounded | Existing player/camera/input + level sequence only if verified; **PASS**: camera releases, no stuck cursor/input after skip |
| **M01 · 0:40–1:45** | **Notice** — strong visual line from bed to empty perch/companion token and desk/window | Approach and inspect **one** focal point; other desk/window inspections optional | A short musical motif suggests something missing, but avoids a long expository cutscene | Existing `AMelodiaExplorationPoint` is a candidate one-shot tracker; verify current narrative intent before deciding whether Sir is briefly present or absent; **PASS**: fires once, remains legible without UI spam |
| **M02 · 1:45–2:45** | **First resonance** — instrument, small music-box, or window chime (choose **one** existing compatible actor) | Perform one forgiving musical response | Crystal/ink ripple in tabletop or glass; the house audibly answers | Existing music/Quill interaction + material/Niagara presentation; **PASS**: exactly one accepted event and one audiovisual response; second activation doesn't duplicate state |
| **M03 · 2:45–3:20** | **Threshold** — bedroom door opens to the larger house | Approach/use door | First reveal of curving pink architecture and roof-lit interior | Existing transition/door actor; **PASS**: collision, correct spawn/facing, input returned, no duplicated pawn. Map split decided only after live audit |
| **M04 · 3:20–4:35** | **The house hums** — a curved landing and **one** oval salon; frame grand staircase without requiring upstairs | Walk through salon; optional linger at centerpiece | Scalloped roof language seen from inside, faint acoustic call-and-response, daylight drawing eye to entrance | Luna stages already-owned `MEL_mh_*` / Paris kit; no extra mechanic; **PASS**: readable route, no snagged furniture/stair collision; house identity clear without FX |
| **M05 · 4:35–5:10** | **Open the front door** — purposeful pause before exterior reveal | Use exit | Dramatic change in scale: tiny home → flat waterways, stone village, pollarded ash and morning mist | Existing level/sublevel transition and PPV; **PASS**: no black-void/frame pop, normal control, stable toon/watercolor treatment |
| **M06 · 5:10–6:35** | **Village orientation** — terrace, short stone lane, one bridge crossing or canal bend; village background lives beyond playable route | Follow visual landmarks; optional 20-second garden/market nook | House roof recedes behind, local limestone/wood/water own the color story | Existing Poitou Houdini/UE staging and PCG; **PASS**: 3 naïve testers independently reach visible landmark without minimap dependency; no water fallthrough |
| **M07 · 6:35–7:55** | **One conversation** — approved existing Petal Priestess (or same canonical Morning Quill interaction located to suit final story), no new NPC system | Initiate **one** Quill choice, then exit dialogue | A grounded human connection and one clear next-place cue; warmth, no lore dump | Quill / `UMelodiaNarrativeSubsystem` / UI Bridge; **PASS**: choice responsive, one intent/flag transaction, movement returns, no replay reward |
| **M08 · 7:55–9:20** | **Follow the water** — short, guided canal edge among pollarded ash to landing/barque; musical ecology visibly but subtly responds | Walk the canal; optionally inspect one lookout | The whole Poitou horizon opens; soft cymatic response on water links the house's music to place | Existing water/PCG/musical materials and Niagara/MPC sole writers; **PASS**: walkable edge, no forced swimming, camera sees clear destination and house/village recall |
| **M09 · 9:20–10:00** | **Departure / checkpoint handoff** — at the landing, an existing trigger or Quill beat points to the approved First Dream continuation | Confirm proceed | Ending image: boat, canal reflection, glimpse back toward house; next chapter promise | Preserve currently approved golden-run transition and save/quest authority; **PASS**: no new quest IDs guessed, no invented checkpoint, transition target and persistence explicitly confirmed by test |

**Pacing flex:** a fresh player might spend 8–12 minutes. Reserve extra time for looking, not added mandatory interactions. If P0 is too long, cut optional inspections and the second house linger before cutting the wake, house reveal or canal arrival.

### What the player should remember

1. *Melusina is a person with a private life*, not a menu/quest dispenser.
2. *Her home physically answers music* through a single comprehensible interaction.
3. *Poitou is a believable French wetland village* rather than another isolated fantasy art set.
4. *There is an invitation beyond the village*—delivered by a natural path and existing narrative contract.

## 2. Room versus level streaming — decide with real evidence

**Design requirement:** bedroom behaves like a self-contained room. **Not automatically a new `.umap`.** The repo already uses `/Game/Melodia/Levels/Opening/L_MelusinaMorning` for the player opening and World Atlas ID `melusinas_morning`. A stand-alone bedroom level is allowed later **only if** it beats in-map isolation/streaming on input handoff, load behavior and scene ownership.

**Safe first implementation:** stage the room as an isolated interior slice or approved sublevel arrangement, build the house route and village entrance against current Morning ownership, and test door transition with the current player controller. Before inventing `L_MelusinasBedroom` or `L_MelusinasHouse`, document actual existing map/world-partition/portal setup and save restore edge cases. One canonical player route with no duplicate Morning maps.

**Conflicting historical documents:** [Dreamstate prologue](../MELODIA_DREAMSTATE_PROLOGUE.md), `Content/Python/setup_melodia_opening_levels.py`, `verify_melodia_opening_levels.py`, and `UMelodiaOpeningFlowSubsystem` still contain an older bedroom → Dreamstate → Zen Forest story/transition design. The more recent `specs/p0/core_p0_dream_golden_run.v1.json` explicitly retires stand-alone Dreamstate and tests Morning → KaleidoNave. **Sol must inventory actual BP/level bindings and reconcile that drift in a separate bounded task before changing travel BPs or persistent phases.** Do not run older setup scripts on the live modified map to “sync” it blindly.

**Sir Melodious continuity decision (owner):** older opening designs both depict an **empty perch/absence** and use `Morning_SirMelodious_STATIC_INTRO` with a reunion/departure beat. Use a deliberately ambiguous visual cue until the present narrative makes his exact physical state unambiguous; preserve the existing character/animation authority.

## 3. Level-design wayfinding rules

- Establish **one visual landmark per leg**: bedroom stained glass → house oval salon/stair → entrance-door glow → village bridge/canal → jetty.
- Turn corners only where the next landmark is revealed; no more than one short optional fork, with a visible return.
- Use sound to orient: chime of house draws the player through; village ambience opens outside; water motif leads toward landing. No navigation-only new music subsystem.
- Gate complexity by **physical composition**, not complicated quest logic. Nearby paths that cannot be traversed are framed as private gardens, water channels or closed buildings—no unexplained locked doors.
- Keep the first wide Poitou vista as a **reward** for leaving home; bedroom sees only a partial framed glimpse.
- Route must remain legible with every shimmer/glow effect temporarily disabled (color, value, architecture and composition do the work).
- One **hero camera** at bedroom window, one at door/terrace reveal, one at canal departure. Do not block movement for the sake of a shot.

## 4. Exact existing-system reuse / forbidden rebuilds

| Player-facing action | Candidate existing implementation | Rule |
|---|---|---|
| Notice one bedroom object | `AMelodiaExplorationPoint` → `UMelodiaOpeningFlowSubsystem::NotifyExplorationPointVisited` | One-shot point IDs **exist in source**, but confirm active runtime status and Quill narrative convergence; this subsystem is not a new independent quest owner |
| Use resonance | Existing Quill/musical interaction or instrument capability, typed notifications | No new timing engine; first cue must be forgiving and accessible |
| Speak with someone | Morning `Petal Priestess` Quill dialogue and `UMelodiaNarrativeSubsystem` | Preserve first-echo choice/intent semantics; don't add story flags by guessing names |
| Place house and landscape | `MEL_mh_*` house GN, completed Paris variants, approved Tripo hero meshes; Houdini Poitou input → World Compiler / UE PCG | Build once, instance/reuse, preserve single authoritative house/terrain work |
| Activate VFX and toon look | Existing `MF_NikkiDreamGrade`, project toon/ink materials, established Niagara/MPC writer paths | Watercolor FX are presentation, not mission state; verify original ink PPV assumptions live |
| Enter/leave physical space | Existing opening/transition BPs, map controller, portal contract | Never silently rewrite the retired Dreamstate/Zen transit into a new travel implementation |
| Save/restart/continue | Canonical JRPG SaveGame + Narrative Record; `specs/p0/core_p0_dream_golden_run.v1.json` | The **integration golden run** certifies idempotency and restart, not a lookdev-only PIE capture |

## 5. Build in five bounded passes

**PASS A — Route-only clay, no mechanics (Luna + owner)**  
Use the current live Poitou / House geometry and mark **start, focal points, 3 transitions, and jetty**. Keep walls/houses/PCG lookdev stable. Block any optional side quests and unreachable roads through believable set geography. Deliver annotated overhead 1-page map + walking video. Gate: 3 testers find jetty with no quest HUD.

**PASS B — Physical transitions (Luna placement; Sol only if broken)**  
Bind bedroom exit → house → village → continuation using only **existing** state/transition actors; mark each source actor + destination path. Test gamepad/keyboard, input focus, possession, transition camera, collision. Gate: three consecutive full traversal attempts with no teleports to stale Zen/Dreamstate.

**PASS C — Two interaction moments (Luna; review owner)**  
First resonance at bedroom and one existing Quill NPC choice on village route. Audit Sir beat and older `OpeningFlow` before adapting. Gate: each fires exactly once; no doubled dialogue/reward; first interaction has visible response; no softlock.

**PASS D — Artistic polish (owner + Luna)**  
Use existing Tripo one-object hero assets for touchpoints: bedside, salon, doorway, canal landing. Poitou-specific stone/wood/moss; house rocaille ribbon/pink-blue; controlled toon edges, watercolor bloom and water response. Gate: three hero stills, one continuous ~10-min uninterrupted screen capture; emotion and wayfinding survive VFX-off pass.

**PASS E — Integration + proof (Sol / owner)**  
Keep First Dream golden run as independent full-stack QA: Morning → KaleidoNave → existing stock JRPG encounter → Quill consequence → canonical save → editor/process restart → Continue → reactivation/no duplicate side effects. Test real currently active travel, not historical docs. Gate: fresh-slot receipts and recorded per-phase pass/fail; do **not** call a screenshot or an IntegrationMap PIE run complete route proof.

## 6. Agent workload and stop conditions

| Agent | Job | Done means | Must NOT do |
|---|---|---|---|
| **Luna** | Capture current local/Perforce Poitou scene, construct 10-minute walk with BP placement and visual pacing, annotate actors/transitions, produce art/flow footage | Annotated route, three hero views, 10-minute continuous clip, visible open issues | Invent a new generic level generator, reauthor roof ribbons or master materials, save contested UE map |
| **Sol** | Inspect actual `OpeningFlow` vs GoldenRun route bindings, solve **one** proven input/travel/Quill/save issue at a time, run regression | For each fix: repro, minimal diff, verifier, fresh PIE log and status | New save system, silently rewrite quests, revive retired Dreamstate/Zen route, broad agent sweep |
| **Owner** | Decide Sir's initial presence, emotional beat timing, house reveal, and final French visual identity | Approve G1 silhouette, first resonance, entrance reveal and jetty exit | Wait for every village house/interior or Sea Above feature before playing |

**Budget discipline:** Codex only for a named failing boundary with an exact actor/path/log and pass/fail test. Visual changes and asset placement do not require Codex. Always one Unreal editor writer; no agent silently saves over a live level or WIP blend.

## 7. Evidence record: one run sheet, not another status authority

Keep a session-local receipt under `Saved/Audit/poitou_p0_walk/` (the owner may choose a Perforce evidence path) with:

```text
run_id, date, operator, UE build hash/editor PID, map path and starting save slot
M00–M09: PASS / FAIL / NOT_RUN, actual duration, actor name, evidence screenshot/log
input focus and spawn for each boundary; original/target actor and map
Quill intent & consumed IDs (as actually emitted), rhythm cue repeat count
terrain/World Compiler source bundle and recipe hash where used
stop reason / owner sign-off, 3 hero frames, uninterrupted walkthrough link
```

Use [CURRENT_STATE.md](../../CURRENT_STATE.md) for promoted current status and [World Atlas evidence rungs](../WorldAtlas/README.md) only after evidence actually exists. No fabricated in-editor proof.

## 8. Immediate first session (do this, nothing else)

1. Luna opens [`POITOU_START_HERE.md`](../../POITOU_START_HERE.md), this score and the existing convergence plan, then walks the **current local** room/house/village actors **read-only**. Record exact level, World Partition/sublevel status, Sir/Quill actor state and current transition BPs.
2. Owner chooses a **single canal-facing exit image** and reviews the **bedroom → house → village → jetty** annotated route.
3. Luna stages **M00/M03/M05/M08** (wake, two reveals, jetty) **as clay traversal only** and captures a continuous walkthrough. No fancy UI or new gameplay systems yet.
4. Sol receives **only** the first failing travel or input seam, if one is found, with a single screenshot/log and repro.
5. Only after that playtest passes, add M01/M02/M07 interactions and then the polish pass.

> **Lock:** A small, coherent journey that invites the player into the world. Not a fully accessible Poitou, not a completed mansion, not another technical framework.
