# Melusina Performance Persona Bible v1 — 2026-09-08

> **Purpose:** define Melusina as a musical character-medium who can live inside Melodia and outside it through songs, performances, illustrations, short films, voice clips, and collaborations.
>
> **Status:** creative SSOT v1. This document records what is currently locked vs what should be auditioned. It does **not** replace gameplay/runtime authority.

---

## 1. Core thesis

Melusina is not only a protagonist who happens to sing.

**She is a living musical medium.**

Her defining fantasy:

> **Melusina's voice causes the world to remember that it is music.**

A Melusina performance should therefore never be only a singer in front of a background. Her songs leave visible structure behind: water becomes cymatics, ornament assembles from harmony, fabric traces musical curves, architecture resonates, flowers or light grow along phrasing, and places temporarily become musical.

The public-facing character goal is closer to a virtual musical persona than a conventional game mascot: she should be able to carry songs, visual performances, environments, outfits, instruments, and collaborations beyond the game while remaining recognizably Melusina.

---

## 2. Working public archetype

### Working title
**Melusina, the Living Refrain**

This is a working title, not locked marketing copy. It captures the idea that Melusina can recur across different songs, stages, outfits, and media while remaining one recognizable musical presence.

Alternative title lane:
- Singer of the Sea Above
- Resonance Maiden
- Living Refrain

### Character tone
Melusina should not be permanently solemn or untouchable.

Preferred emotional mix:
- gentle;
- curious;
- playful when music surprises her;
- romantic and strange;
- capable of melancholy without becoming defined only by sadness;
- delighted by the physical beauty of resonance.

The mythology may be enormous. **Melusina herself should still be lovable.**

---

## 3. Sir Melodious — resonance bond

### Current canon supplied by owner
Melusina is mechanically tethered to **Sir Melodious**.

When Sir Melodious is beyond the intended tether distance, **Melusina currently loses 50% of her damage output**.

Exact radius / falloff implementation remains tunable, but the relationship itself is important enough to become part of the character's musical identity rather than remaining a hidden combat modifier.

### Creative interpretation
Melusina can sing alone, but her full voice requires an **answering presence**.

Sir Melodious functions as:
- harmonic counterpart;
- anchor tone;
- counterpoint;
- witness / responder;
- stabilizing resonance partner.

This should be reciprocal in theme even if their gameplay modifiers are asymmetric. The bond should read as **harmony**, not "Melusina is incomplete because a man is nearby."

### Working resonance states

#### Full Harmony
Sir Melodious is in resonance range.
- 100% intended Melusina damage.
- fuller harmonic layers;
- complete cymatic forms;
- stronger paired / mirrored VFX;
- richer world response.

#### Fading Resonance
Intermediate / falloff range if the runtime later supports it.
- optional transitional state;
- thinner harmonics;
- less-complete geometric response;
- useful for communicating the tether before the hard threshold.

#### Unanswered Refrain
Working name for the out-of-range state.
- 50% damage under the current mechanic;
- Melusina is still fully playable and expressive;
- the visual/audio language becomes solitary rather than simply "bad";
- incomplete rings, partial rose-window assembly, single rather than paired spirals, exposed lead voice, less choir.

The important art rule is: **distance changes the music's character, not only a number.**

---

## 4. Voice identity

Melusina's voice should be recognizable before the listener sees her.

### Three-layer signature

1. **The Girl**
   - intimate lead;
   - soft consonants;
   - breath and humanity kept audible;
   - close, emotionally legible.

2. **The Reflection**
   - subtle delayed / pitch-shifted double;
   - water-reflection feeling;
   - can widen or destabilize with resonance state.

3. **The Choir Beneath the Water**
   - appears at emotional or harmonic peaks;
   - distant, impossible extra voices;
   - should feel like the environment joining the song rather than a generic choir pad.

### Existing voice assets / technical starting point

The repo already documents:
- an **Adachi-Rei-inspired artificial singing-bank research lane**;
- surviving Melusina CV/VCV material and OpenUtau/TuneLab routes;
- **CosyVoice 3** spoken Melusina voice using an anchor seed, with default/gentle/whisper/nordic profiles;
- Japanese spoken voice-conversion proof;
- existing OpenUtau singing material used for lip-sync source;
- DiffSVC / DiffSinger work as optional later routes.

For tomorrow, **do not retrain anything unless an existing asset is actually broken.** First prove what the already-built voice system can do.

Relevant existing docs:
- `Docs/Research/MELUSINA_SINGS_DIFFSVC_PLAN_2026-08-11.md`
- `Docs/Research/MELUSINA_BILINGUAL_VOICE_INTAKE_2026-08-11.md`
- `Docs/Handoffs/MELODIA_VOICE_QUILLSCRIPT_HANDOFF_2026-08-01.md`

---

## 5. Signature visual law

Every public Melusina performance gets **one visible physical law of music**.

Examples:
- a note makes water rings become ornament;
- a held vowel assembles a rose window;
- garment ribbons trace Lissajous figures;
- harmony changes the material state of a cathedral;
- rhythmic accents grow light/flowers along architectural seams;
- Sir Melodious entering range completes a previously broken cymatic structure.

Avoid generic "music particles" as the only response.

The music should leave **compositionally meaningful structure** behind.

---

## 6. Signature instrument lane

### Working concept: The Glassheart

A ceremonial hybrid of:
- conductor's baton;
- tuning fork;
- string instrument;
- sceptre.

At rest it is a compact iconic object.

During performance, translucent strings or harmonic rails extend from it into the stage/environment. Melusina does not merely play the instrument: **the room becomes its resonating body.**

This is a working concept to audition against the existing twelve-instrument canon before locking anything.

---

## 7. Signature stage concept

### The remembered chapel

A small impossible performance space:
- still black-violet water, ankle deep;
- a broken rose window floating without a wall;
- moon reflection below Melusina;
- no visible audience;
- the world starts almost empty.

Performance progression:
1. first note creates one ring;
2. ring reaches a rose-window shard;
3. phrase lights / moves the shard;
4. additional musical layers reconstruct more of the space;
5. Sir Melodious' presence may complete paired structures / harmony;
6. the final cadence lets the remembered architecture dissolve again.

This establishes a reusable Melusina rule:

> **Every song can temporarily sing a world into existence.**

That makes new environment art naturally double as performance media.

---

## 8. First-song lane

### Working title: **Where the Water Remembers**

Theme:
- trying to remember somewhere that no longer exists;
- memory made temporarily physical through song;
- intimate rather than lore-expository.

Possible structure:
- quiet lead voice + bell/piano;
- Reflection enters;
- environment begins responding;
- Sir Melodious / answering harmony arrives;
- Choir Beneath the Water blooms at climax;
- rose window / remembered stage completes;
- arrangement falls back to exposed lead;
- one final ripple.

This is an experiment title/concept, not a requirement to finish a full song tomorrow.

---

## 9. Melusina as a shareable medium

Preferred artifact types:
- 10–20 second performance postcards;
- 30–90 second song sketches;
- looping in-engine live portraits;
- instrument demonstrations;
- outfit-specific song performances;
- environment performances ("stages sung into existence");
- lyric / voice snippets;
- short visualizers;
- eventual full songs / music videos;
- collaborative songs or alternate producers using a stable Melusina voice/persona package.

The long-term success test is not "did we make a lot of content?"

It is:

> **Can someone encounter a Melusina song or performance outside the game and immediately feel that it belongs to her?**

---

## 10. Creative guardrails

- Do not turn Melusina into a generic idol.
- Do not make generated imagery the primary authorship layer.
- Preserve hand-painted / sculpted / authored visual identity.
- AI and automation should remove production friction, not decide her taste.
- Do not retrain/rebuild voice infrastructure when an existing bank can already produce the test.
- Do not let technical spectacle overwhelm the emotional performance.
- Sir Melodious should deepen Melusina's identity through reciprocity, not erase her agency.
- Prefer one memorable musical law per performance over ten simultaneous VFX systems.

