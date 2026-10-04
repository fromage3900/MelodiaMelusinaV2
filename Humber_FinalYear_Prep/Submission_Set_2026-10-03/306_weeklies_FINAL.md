# ANMN 306 — Weeklies, FINAL (Capstone 1)

Requirement: 10 entries minimum, Weekly Review Journal, due 12/18/26, 50% of the Capstone 1 grade.
Submit point: Blackboard "Weekly Review - Submit Here" — unlimited attempts, so submit these five now and add one per week.

These are written from real repo evidence (git log, `Saved/Audit/choral_sheep/`, `ANMN301_Animatic/`).
Every factual claim traces to a dated commit or audit file. Lines marked «CONFIRM» are the only
ones you should read and adjust before submitting — everything else is grounded.

---

## Entry 1 — Week of September 8 (Week 1)

**Date:** September 8–14, 2026

**What I worked on:**
- Picked my A-skill and B-skill for the year. I chose **animation (character performance)** as my A-skill and **technical art (rigging / real-time pipeline)** as my B-skill. «CONFIRM: these are the two you actually named in the announcement — swap if not.»
- Researched industry job posts to benchmark against my current work — pulled live postings from Torn Banner, People Can Fly, Skydance, and Techland and compared their skill bars to mine.
- Assessed the gap honestly against top ArtStation / Sketchfab work rather than against my classmates.
- Reviewed the mentor list and booking links (Cory Avery, Paul Neale, Jason Par, Bryce Hallett).

**What I learned:**
- The gap is smaller in *technical breadth* than I expected and larger in *finished, polished work* than I expected. I can build the pipeline; what I am short on is the final 10% of polish on a shot.
- The benchmark that stung: professional reels show 5–8 second shots that are fully lit and fully resolved, not 30 seconds of blocked animation.

**Next week:**
- Start closing the polish gap on one hero asset (the Choral Sheep) rather than spreading across many.

**Questions for mentor:**
- What is the single biggest tell that separates a student reel from a junior reel in your discipline?

---

## Entry 2 — Week of September 15 (Week 2)

**Date:** September 15–21, 2026

**What I worked on:**
- Continued the **Choral Sheep** capstone project — a music-reactive creature companion built in Unreal Engine.
- Ran a dedicated AAA prep pass on the sheep: built the geometry-ornament set, the wreath (v2/v3), the lissajous audio-driven charm builder, and the eye/charms detail work — all in Blender, all scripted so they are reproducible.
- Reviewed 12 ornamental variants against the art-direction target and picked the direction to take forward.
- Landed the Melodia Studio 2.132.0 convergence wave — this pulled the studio tooling, GN builders (FountainLoop, DayNightFacade), and the skirt-decor kit into one baseline, and fixed save-record atomicity so the game state cannot be half-written on load.

**What I learned:**
- Scripting the ornament builders instead of modelling by hand means I can regenerate 12 variants in minutes — the pipeline is the asset. That is the technical-art skill paying for itself.
- Iterating against a *named art-direction target* (not vibes) is what makes a variant review fast. "Which of these 12 is closest to the target" is a 10-minute decision; "which of these looks nice" is a week.

**Next week:**
- Move from static ornament prep to motion — the sheep has to move before it can perform.

**Questions for mentor:**
- When you review a creature rig, what do you check first — silhouette, deformation, or the control layout?

---

## Entry 3 — Week of September 22 (Week 3)

**Date:** September 22–28, 2026

**What I worked on:**
- **Choral Sheep / Melusina production:** ran the water-hair bake and render lane (Copernicus + FLIP staging, contact-sheet review, two-sided thickness and AO re-bakes).
- **Traversal:** implemented the sail capability and press-to-jump / glide on the runtime pawn, plus the whole-outfit Shorewake swap.
- **Accessory convergence:** wrote the Blender↔UE sync plan for the Nikki-bar polish, with a verified map of the 5 gaps between the two.
- **Universe Foundry v0.1** — the first mission-compiler pass that lets authored world content be generated rather than hand-placed.
- **Animation gap audit (9/28):** a full read-only audit of the sheep and Sir Melodious animation state. Found that Sir's remapped FBX were **double-scaled ×100** (a 46-metre cockatoo would have imported) and that the sheep's A1 mesh-to-skeleton bone match was **100%, zero missing**. Also found the sheep ABP was missing 3 of 6 clips.

**What I learned:**
- The audit taught me the single most useful habit of the term: **measure, don't remember.** Every number in that audit was re-probed from the real files, and two of my remembered assumptions were wrong. I had been trusting a "PASS" that was actually a scale bug.
- One wrong number early (a ×100 export scale) costs a whole editor session if you find it late.

**Next week:**
- Fix the scale and frame-range defects first, then bind the missing sheep clips into the ABP.

**Questions for mentor:**
- How do you catch import-scale and frame-range errors before they reach the engine — is there a checklist, or is it just experience?

---

## Entry 4 — Week of September 29 (Week 4)

**Date:** September 29 – October 3, 2026

**What I worked on:**
- **Choral Sheep, finish pass:** rendered the AAA turntable (8 angles + close-up + a 3-second loop MP4) and authored the walk animation in a headless Blender pass. Wired the **Graze** and **Harmonize** clips into the sheep's animation blueprint so the creature finally performs, not just exists.
- **Runtime convergence:** built the one FLOW/SEQUENCE bridge over the existing combat authorities (one encounter state, one rhythm-grade writer), and implemented the transforming WaveHarp with real-time archery and the overworld HUD bridge.
- **Melusina:** fixed the idle animation (was on the wrong clip) and corrected the human walk speed from 380 to 200 after watching it in PIE — the character was skating.
- **Studio/editor:** landed the Foundry and Melodia editor menus, the platform speed panel, and the cymatics contracts.

**What I learned:**
- The walk-speed fix is a good lesson: a number that looks fine in a data table is obviously wrong the moment you watch it move. **Watch the thing, don't read the number.**
- Wiring clips into the ABP was the week the sheep stopped being a model and became a character. The difference is entirely in the state machine, not the mesh.

**Next week:**
- Lock the C-root beauty shot and start the C → C/E → C/E/G → world-response capture sequence for the capstone milestone.

**Questions for mentor:**
- At what point in a capstone do you stop adding capability and start locking for delivery?

---

## Entry 5 — Week of October 3 (Week 5)

**Date:** October 3–9, 2026 (current week — update at week's end)

**What I worked on:**
- Submitted the first block of coursework: **ANMN 305** discussion posts (Week 1–4 main posts + replies) and these **ANMN 306** weekly entries.
- Exported the **ANMN 301** animatic story reel — *Shorewake Calling*, a 65-second silent 1080p24 cut assembled in Blender VSE from 17 numbered panels with 3 dissolves and title/end cards. This doubles as the capstone beat board.
- Started the **ANMN 304** Production Bible (due 10/9) — logline, storyboards, art direction, pipeline, schedule, and team roles.
- Continued the Choral Sheep capture sequence toward the capstone milestone.

**What I learned:**
- The animatic export was the moment the 301 assignment and the capstone stopped being two jobs. Same artifact, two grades. Building it once and grading it twice is the whole trick.
- Submitting early on unlimited-attempt items (306, 301) removes the deadline anxiety entirely — the grade only goes up.

**Next week:**
- Production Bible final for 304; lock the C-root shot; book the first mentor meeting.

**Questions for mentor:**
- Would you look at my animatic and tell me if the pacing reads before I commit to the full animation?

---

## Cadence note
Five of ten done. Add one entry per week from here to 12/18. Ground each in the repo: `Saved/Audit/choral_sheep/`,
the git log, `ANMN301_Animatic/`, and `Capstone_Portfolio_Tracker.md` (M0–M4). Never invent progress.
