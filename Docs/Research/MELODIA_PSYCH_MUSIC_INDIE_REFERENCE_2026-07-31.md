# Melodia — Psych/Music Indie Design Reference + Psych-Horror Integration

**Date:** 2026-07-31
**Status:** Reference material, locked. Decision 033. **Not scope.** No code changed for this doc.
**Anchor:** `Docs/MELODIA_IDENTITY_AND_LOOP_2026-07-30.md` (thesis: *Melodia is music you cannot fail at*; Resonance as the universal verb) and Decisions 016/017 (rhythm expressive not evaluative; Resonance as *the* combat decision).
**Companion:** [`MELODIA_BARD_GRIEF_HOOK_2026-07-31.md`](MELODIA_BARD_GRIEF_HOOK_2026-07-31.md) — the author's lived material (grief, abandonment, BPD, OCD, isolation, being behind) metaphorized into Melusina the travelling bard; Sir alive-and-retrievable, reunion ending.

---

## 1. How to use this doc

Every entry ends with **Take / Reject** and a **landing system** — an existing Melodia system, never a
new one. If an idea has no existing landing system, it is rejected or parked, per the working
agreement (no compensating mechanisms, no scope creep).

Guardrails that govern every entry:
- **Decision 009/011:** the stock JRPG controller owns turns, damage, and results. Presentation may
  *show* anything; it may not *decide* anything.
- **Decision 012/016:** musical time is presentation-only, and rhythm never gates, blocks, or reduces
  an outcome. No "MISS", ever.
- **Decision 033:** horror is a *tonal register* and *reference vocabulary*, not a mechanics mandate.
  No sanity meters, no jump-scare systems, no new subsystems.

---

## 2. Music-indie reference

### 2.1 OMORI (OMOCAT, 2020; RPG Maker MV, solo dev, 1M+ Steam, ~6-year dev)

**The thing everyone cites:** emotion as the *entire* combat layer, not a flourish. Four states
(Happy/Angry/Sad/Afraid) in a rock-paper-scissors cycle; each modifies stats, accuracy, and available
skills; states **spread between party members** (contagion); enemies carry emotional states too, so
reading the emotional flow of a battle matters as much as tracking HP. Sad is a *defense* state —
a sad character is "differently oriented toward the world: less aggressive, more durable", which
matches the psychological research on affect-as-information.

**The structural things most summaries miss:**
- **Dual world as dissociative structure:** HEADSPACE (saturated, bright, pastel) vs Faraway
  (near-monochrome). Same narrative told from inside and outside a dissociative state. Colour alone
  tells the player which register they are in — no text required.
- **Mechanic-as-metaphor:** every system serves the story. The emotion triangle maps to real
  emotional dynamics; suppressing emotion to maintain the dream world is literally what the combat
  system does.
- **Silence as design:** long featureless walks, menus that hang a beat too long. Designed
  discomfort, not absence.
- **Unreliable narrator is an information-architecture problem:** what the player sees vs what is
  true must be tracked at the narrative level for the entire game.
- **No easy catharsis:** grief is not resolved cleanly — which is closer to how grief works.

**Take for Melodia:**
- Decision 016 and 017 *are* OMORI's structure already. Resonance (applied by Petal Cadence,
  exploited by Skybound Refrain) is the "one status axis carrying the game" — same shape, expressed
  as *music answering music*.
- **Dream vs waking colour language is already in the DNA:** `Docs/MELODIA_DREAMSTATE_PROLOGUE.md`
  and the Identity doc describe exactly this. If it is not yet a hard, documented palette split
  (saturated dream / muted morning), make it one before commissioning art — OMORI's own guide calls
  this a pre-art hard constraint.
- **Silence as design** → `Docs/MELODIA_DREAMSTATE_PROLOGUE.md` + `UMelodiaPacingSubsystem`.
  Pacing authority already exists (Decision 031); "hold the beat" is an authored profile value, not
  new code.
- **Emotional contagion** → parked. Melodia's party is effectively Sir-answers-Melusina (the
  "answering voice" rule). If a real second resonance relationship ever exists, re-read OMORI's
  contagion before designing it.

**Reject for Melodia:**
- The emotion *triangle* as a combat stat layer. Decision 017 deliberately scoped Resonance as ONE
  axis, and the working agreement says prove one fun decision before a second.

### 2.2 Crypt of the NecroDancer (Brace Yourself Games, 2015)

**The real lesson is not the rhythm — it is the fairness design.** Ryan Clark's stated goal was a
"fair roguelike" in the Spelunky sense: when you die, you can only blame yourself. His rhythm
system went out of its way to *reduce* beat accuracy requirements: an **auto-calibration system
bends the rules in the player's favour** (never more than ½ beat from true), and — critically —
**never tells the player they are wrong**. The "beat you feel" is the beat the game accepts.

**Take for Melodia:**
- This is the concrete, cited model for Decision 016 ("no miss penalty, ever"). NecroDancer bends
  the rules to give the player benefit of the doubt; Melodia's no-miss decision is the same
  philosophy taken to its conclusion — timing that lands well *adds*, timing that does not is
  simply quieter.
- **"Never tell the player they are wrong"** is the direct antecedent of the battle UI rule (no
  "MISS", no red timing bar, no broken combo). Worth a line in `MELODIA_RHYTHM_TIMING_SLICE.md` if
  it is not already there.

**Reject for Melodia:**
- Rhythm as *input requirement* (the dance-pad/beat-locked movement). Melodia's rhythm layer is
  presentation and flourish, explicitly non-mandatory (Decision 016).

### 2.3 Undertale (Toby Fox, 2015)

Music as worldbuilding + morality + battle-as-dialogue. Toby Fox scored it himself and the
soundtrack *is* the emotional spine. Academic read (ludomusicology): music functions in narrative
as Emotive / Informative / Descriptive / Guiding / Temporal / Rhetorical classes — Undertale
runs all six.

**Take for Melodia:**
- **Battle-as-dialogue is Melodia's fusion already:** QuillScript dialogue ⇄ JRPG battle via
  allowlisted `melodia:` intents. Undertale is the proof that a JRPG fight can *be* a
  conversation. The typed result (victory/defeat/flee) resuming QuillScript is the direct descendant.
- **Melody-as-signature:** every character/place having a musical identity the player learns to
  recognise — Melodia already has the audio-reactive MPC + `UMelodiaMusicClockSubsystem` publishing
  `BeatPhase` project-wide (Decision 015). Music as *place-identity* is a zero-mechanic win for the
  KaleidoNave/morning/dream-state route.

**Reject:** Undertale's moral-route split (pacifist/genocide) — not Melodia's tone or loop.

### 2.4 The music-indie spectrum (for tonal reference)

| Game | Music role | Take for Melodia | Reject |
|---|---|---|---|
| **Sayonara Wild Hearts** | Playable pop album; short, stylish, movement-as-emotion | The "one evening, album-shaped arc" pacing ideal for the dream-state prologue | — |
| **Wandersong** | Singing as interaction, problem-solving, emotional language | The Resonance verb (call-and-response) is *already* this shape in three contexts (battle/dialogue/exploration, Identity doc §2) | — |
| **Gris / Oxenfree** | Soundtrack as narrative voice / emotional transport | Tonal: quiet, mournful score as *the* voice of the morning register | — |
| **Chicory** | Score + creative identity, not rhythm | Proves a "music-adjacent" game can be cozy + emotionally heavy at once — Melodia's exact register | — |
| **Thumper / Just Shapes & Beats** | Rhythm as pressure / obstacle course | — | **Anti-pattern.** The exact opposite of Melodia's thesis. If a reviewer ever suggests "more Thumper", that is a tone violation, not a pacing note. |

---

## 3. Psychological-horror reference (deeper dive)

The project already has a horror-adjacent register (dream-state prologue, the unsettling undercurrent
of the opening). This section gives that register a researched vocabulary. Per Decision 033, horror
here means **tonal register and reference vocabulary on existing systems** — not mechanics.

### 3.1 Silent Hill 2 (Team Silent, 2001) — the world as a reflection of internal state

**Techniques with direct transfer:**
- **Fog as visibility-as-vulnerability.** The fog is not decoration: it limits vision, forcing the
  player to rely on sound and intuition, and isolates them. (Originally a PS1 technical limit, then
  made into *the* iconic design choice.)
- **The radio static mechanic.** An audio-only early-warning signal — sound tells the player danger
  is near *before* visuals confirm it.
- **The town adapts to the protagonist's psyche.** Environment, monsters, and even other characters
  are projections of guilt/repression, not independent threats. Grief, guilt, mental illness, and
  the blurring of reality are depicted via the *place*, not exposition.
- **Combat is deliberately unskilled** (clunky, scarce resources) — reinforcing that the protagonist
  is an everyman, not a soldier. Vulnerability is mechanical honesty.

**Take for Melodia:**
- **Audio-first warning → `UMelodiaMusicClockSubsystem` + audio authority.** Melodia already has the
  audio-reactive MPC and musical-time authority (Decision 015). An *authored* sub-audible cue or
  harmonic shift when an encounter is armed is presentation-only, legal under 009/012, and is the
  direct descendant of the radio static.
- **Environment-as-psychological-projection → the dream-state structure.** The dream world IS the
  internal state made place. This is already the prologue's premise; SH2 is the reference for doing
  it *restrained* — the place does the telling, no narrator explains it.
- **Fog as wayfinding pressure → KaleidoNave.** The four-PlayerStart map (travel authority's
  original motivation) could use visibility/fog to make *arriving at the right place* a felt
  tension rather than a UI decision. Presentation/look-dev, not a mechanic.

**Reject:** combat that is intentionally bad. Melodia's JRPG battle is stock-authority and should
feel fair (NecroDancer's fairness philosophy, §2.2). Vulnerability lives in atmosphere, not in
clunky controls.

### 3.2 Amnesia: The Dark Descent (Frictional, 2010) — the sanity meter that is a lie

**The single most useful design fact in this research:** Thomas Grip has confirmed the sanity
meter **is a placebo**. Its mechanical consequences are almost nil; its *perceived* consequences
drive the fear. It exists to "trick players into scaring themselves." The original darkness-as-enemy
mechanic was scrapped because mixing an aesthetically meaningful element (darkness) with a mechanic
ruined the mood — so they made the *mental state* the vessel instead.

**Take for Melodia:**
- **Presentation-first psychological feedback is a validated technique, not a hack.** Melodia already
  applies the identical pattern: `UMelodiaMusicClockSubsystem::HasMusicalTime()` degrades to
  presentation-only; the rhythm layer shows but never decides. The Amnesia example licenses doing
  the same for *atmosphere* — a "dream integrity" register that is readout only.
- **Darkness-as-enemy is a warning, not a technique:** when a beautiful, mood-critical element
  (Melodia's light, its music, its colour) gets forced into a mechanical role, the mood dies. That
  is the *reason* Decisions 016/017 keep rhythm out of the result path. Cite this when anyone
  proposes gating on mood.

**Reject:** an actual sanity/dream-integrity meter with mechanical teeth. That is a new system and a
Decision 033 violation.

### 3.3 SOMA (Frictional, 2015) — existential dread with no monster

The scariest moments have no enemies: they come from questions about identity and consciousness.
Dread lingers because the *question* persists, not because a threat does. Also notable: SOMA ships a
**"Safe Mode"** that removes enemy threats while preserving puzzles and story — the horror is
voluntary.

**Take for Melodia:**
- **Questions, not threats, carry the heavy beats.** Sir and Melusina's relationship is the emotional
  centre; the uncomfortable beats should be *dialogue and silence*, resolved through QuillScript
  choices — which the allowlisted-intent system already supports.
- **Safe-mode precedent** is the same spirit as Decision 016 (never gate a player out of content they
  paid for emotionally). Melodia's version is already structural: nothing is mandatory, nothing
  penalises a missed timing.

### 3.4 Layers of Fear (Bloober, 2016) — the environment as unreliable narrator

Rooms change when you look away. The environment itself lies. No monsters — the *place* is the
horror, and the protagonist's fractured mind is the excuse.

**Take for Melodia:**
- **One authored "not quite the same" return is high-value, low-cost.** The post-battle return path
  (battle ends → QuillScript resumes → exploration) is the natural seam: an authored, alternate
  state of a place the player already knows. This is *content*, not a system — QuillScript can drive
  a "the place you came back to is subtly different" beat with zero new code.
- **The unreliable narrator is an information-architecture discipline** (OMORI's point too): if the
  dream state lies, the record of what the player has been told must be tracked — `FMelodiaNarrativeRecord`
  is exactly the versioned place for that discipline.

**Reject:** runtime environment-mutation systems (rooms changing while the player watches). That is a
mechanics project, not a tonal one, and it fights the look-dev.

### 3.5 Doki Doki Literature Club (Team Salvato, 2017) — the facade cracking

A wolf in sheep's clothing: a cutesy dating sim that becomes horror through **subversion of genre
expectations, fourth-wall manipulation, and simulated data corruption** — never jump scares. The
cheerful facade cracking is the horror.

**Take for Melodia:**
- **The "cute on top, heavy underneath" register is Melodia's own.** The Identity doc already pairs
  a saturated, inviting world with melancholy. DDLC is the proof that the *contrast* is the
  mechanism — the opening's cuteness is not decoration, it is the setup.
- **Subversion is cheapest at genre seams.** Melodia's seam is the morning-into-battle transition
  (L_MelusinaMorning → JRPG battle with Melusina). An authored tonal *crack* at that seam — the
  music changes register before the battle does — is the DDLC move, done with the audio authority
  Melodia already owns.

**Reject:** fourth-wall breaking and file/asset manipulation. That is DDLC's signature but it is a
different product, and Melodia's own boundary (`README.md`: don't automate the Sakura art direction)
argues against meta-theatre aimed at the player's filesystem.

### 3.6 The rest of the field (reference table)

| Game | Technique | Take / Reject for Melodia |
|---|---|---|
| **Pathologic** (Ice-Pick Lodge) | Obscurity and unfair busywork as *the* theme; hopelessness as content | **Reject.** Fights the cozy/no-fail identity (Decision 016) directly. |
| **Iron Lung** | Minimalist confinement, audio-only dread, tiny budget | **Take as budgeting proof:** a single room + an audio cue beats a set piece. Melodia's morning-to-dream ratio should be small-and-mighty, not dense. |
| **Signalis** | Fragmented narrative, unreliable memory, symbolic imagery | **Take as dream-state reference:** fragment, don't explain. The prologue should withhold. |
| **MADiSON / Visage / Amnesia: Bunker** | Sustained psychological assault, no comfort zones | **Reject.** No comfort zones is the opposite of Melodia's thesis (music you cannot fail at). Melodia's heaviness is *relief-delayed*, not relief-denied. |
| **Fatal Frame II** | Melancholy tone, intimate confrontation, loss as fuel | **Take as tonal target** for the Sir/Melusina beats — the horror is *sorrow*, not threat. |
| **Slay the Princess** | Choice-driven narrative manipulation | **Take narrowly:** the player's own interpretation reshapes the story — a precedent for QuillScript choices having real emotional weight. |
| **The Mortuary Assistant / Closing Shift** | Routine disrupted → horror in the mundane | **Take narrowly:** the morning register (routine) is the *setup* for the dream register (disruption). |

---

## 4. Direct integration map — into the systems that already exist

Every row: existing Melodia system + technique + concrete, authored-first application. Nothing here
requires a new subsystem, a new mechanic, or a code change beyond (where noted) presentation wiring
in the next closed-editor window.

| # | Existing system | Psych/music technique | Concrete application | Guardrail |
|---|---|---|---|---|
| 1 | `UMelodiaPacingSubsystem` (Decision 031) | OMORI silence-as-design; NecroDancer fairness | Author the first `UMelodiaPacingProfile`: a *held-beat* value for the morning register and a *stutter* value for the dream register. Pacing is the cheapest way to change psychological register. | Still falls back to authored defaults on false return (Decision 031). Tonal only. |
| 2 | `UMelodiaMusicClockSubsystem` + audio authority (Decisions 012/015) | SH2 radio-static; Undertale place-identity; DDLC genre-seam crack | Authored harmonic shift / sub-audible cue when an encounter is armed, and a musical-register change at the morning→battle seam. Presentation-only. | Must never route into damage/turns/results (009/011/012). |
| 3 | `FMelodiaNarrativeRecord` v2 (Decision 013) | OMORI/SH2 unreliable-narrator discipline; Signalis fragmentation | The dream state *withholds* — the record tracks what the player has actually been told, so authored contradictions are intentional, not bugs. | Never add a second persistence store (Decision 013). |
| 4 | QuillScript allowlisted intents | SOMA questions-not-threats; Slay the Princess choice-weight | The heavy beats (Sir/Melusina) are dialogue-and-silence choices, resolved through the existing allowlist; the reward/flags intents give them *felt* consequence. | Intents stay allowlisted; no new intent families without review (AGENTS.md contract). |
| 5 | `Docs/MELODIA_DREAMSTATE_PROLOGUE.md` + the opening seam | OMORI dual-world colour; DDLC facade-crack; SH2 projection | Make the saturated/muted palette split a hard, pre-art constraint; the dream register is the internal state made place, and the morning→battle seam is where the facade cracks. | Content/look-dev. `L_SakuraPath` art direction stays human-owned (README). |
| 6 | KaleidoNave + travel authority (Decision 023) | SH2 fog-as-visibility | Visibility/fog as wayfinding tension on the four-PlayerStart map — arriving at the *right* place is felt, not menu-driven. | Look-dev/presentation. TravelTo logic untouched. |
| 7 | Battle result matrix → QuillScript resume | NecroDancer fairness; Amnesia placebo | The no-miss/no-penalty result flow already *is* the technique. Keep the "never tell the player they were wrong" discipline in the battle UI. | The 5 runtime gates in `LOWER_TIER_FOUNDATION_LOCK_2026-07-29.md` must close before any new presentation. |
| 8 | VRM4U / NPC rigs + voice (VOICEVOX) | Fatal Frame II sorrow; Wandersong singing | Emotional beats carried by *voice and stillness* — the answering-voice rule (Sir's skills key off Melusina's marks) is the mechanical expression of the same idea. | Presentation. Stock battle authority untouched (Decision 009). |

**Parked (no landing system yet, do not force):** emotional contagion between party members,
runtime environment-mutation, choice-driven story reshaping, multi-axis emotional combat.

---

## 5. Anti-patterns — what would break Melodia

1. **Thumper-ising the rhythm layer** (rhythm as pressure) — direct thesis violation (Decision 016).
2. **A sanity/dream-integrity meter with mechanical teeth** — new system, Decision 033 violation.
3. **Making combat intentionally bad/clunky** (SH2's honesty) — fights NecroDancer-fairness.
4. **Denying relief / no comfort zones** (MADiSON/Visage) — Melodia's heaviness is relief-delayed,
   not relief-denied.
5. **Fourth-wall/file manipulation meta-horror** (DDLC) — different product, and fights the
   portfolio's craft-forward identity.
6. **Any horror that gates outcomes** — every Decision 009/011/012/016 rule exists to prevent this.

---

## 6. Sources

- OMORI (2020, OMOCAT): Game Journal analysis (gamejournal.it), Neurolaunch "Omori Emotions",
  Younis & Fedtke (2024) on trauma in environmental design (Sage), SDLC Corp design breakdown.
- Crypt of the NecroDancer (2014): Ryan Clark, "Game Design Deep Dive: Finding the beat" (Game
  Developer/Gamasutra); Wikipedia.
- Undertale (2015): Megan Franklin, "Songs of the Underground" (U. Kentucky ludomusicology thesis).
- Silent Hill 2 (2001): Simply Put Psych / Press Start analyses; Game Voyage; Minimap remake review.
- Amnesia: The Dark Descent (2010): Thomas Grip, "Game Design Deep Dive: Amnesia's Sanity Meter"
  (Game Developer); ScreenRant on the placebo; Amnesia Wiki.
- SOMA (2015): Frictional Games; BlackHawkGames; safe-mode documentation.
- Layers of Fear (2016): Bloober Team interview (Game Developer).
- DDLC (2017, Team Salvato): Dark Skies; Press Start (U. Glasgow) "Doki Doki Subversion Club".
- Pathologic, Iron Lung, Signalis, Visage, MADiSON, Slay the Princess, Fatal Frame II, The
  Mortuary Assistant, The Closing Shift: ScreenRant genre-subversion roundup; Horror Games Realm
  indie-psych lists.
- Ludomusicology: music-narrative function classes (Emotive/Informative/Descriptive/Guiding/
  Temporal/Rhetorical) from Tekrø & the "Interplay Between Music and Storytelling" study.

*Compiled 2026-07-31 by the parallel research lane. Web citations above; exact URLs in the search
session. Treat dates/facts as gathered from the cited sources, not re-verified against the games
themselves.*
