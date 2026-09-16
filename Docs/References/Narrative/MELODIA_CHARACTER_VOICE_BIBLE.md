# Melodia Character Voice Bible

**Status:** DURABLE NARRATIVE / PERFORMANCE REFERENCE  
**Scope:** Character voice, dialogue grammar, QuillScript prose, and voicebank performance direction for Melusina and Sir Melodious.  
**Authority boundary:** This document defines how authored dialogue should sound. It does **not** own current status, gameplay truth, quests, save state, combat, or runtime implementation. `CURRENT_STATE.md`, `SYSTEM_MAP.md`, `DATA_FLOW.md`, and the world-building/narrative contracts remain authoritative for those concerns.

## 1. Core identity

Melodia is not a fantasy RPG that occasionally contains rhythm gameplay. It is a world in which **music is a language of relationship**.

The recurring narrative action is:

```text
call -> wait -> answer / non-answer -> interpretation -> response
```

Melusina is a travelling bard who is exceptionally good at performing, reading rooms, and making beauty — and considerably less reliable at tolerating ambiguity when something matters to her personally.

Her central contradiction is the source of her voice:

> **She can command a stage more easily than she can survive four seconds of silence from something she cares about.**

The game should enjoy that contradiction. It is funny, glamorous, painful, and human.

## 2. Melusina — voice thesis

Melusina is composed, musically sophisticated, observant, elegant, and genuinely capable. Her poise is **real**, not a fake mask hiding a helpless person.

She is also sharp, proud, vain in small amusing ways, intensely sensitive, occasionally bratty, easily offended by perceived indifference, and self-aware enough to know when she is being ridiculous without necessarily being able to stop feeling ridiculous.

A useful tonal reference is the **juxtaposition** associated with high-gloss magical/idol presentation against a much sharper, messier private attitude. This is a structural reference only: **do not imitate K-Angel dialogue, catchphrases, cadence, or surface mannerisms.** Melusina must remain her own character: bardic, musical, dry, romantic, observant, and rooted in Melodia's world.

### The governing writing rule

> **Melusina is lyrical when she has control. She gets funny when she is uncomfortable. She gets simple when something actually hurts.**

If a vulnerable line becomes more ornate as the pain becomes more immediate, rewrite it.

## 3. Melusina performance registers

### A. Stage / ceremonial Melusina

Used when she performs, addresses a crowd, invokes an instrument, sings formally, or consciously takes control of a moment.

- precise diction;
- longer breath support;
- confident melodic contour;
- elegant imagery is allowed;
- can sound almost frighteningly composed;
- never generic faux-medieval exposition.

Example energy:

> "Then listen carefully. I am only going to make the sea remember this once."

### B. Conversational Melusina

Her default around Sir and trusted companions.

- dry;
- observant;
- modern-feeling rhythm without contemporary meme vocabulary;
- shorter sentences;
- amused by absurdity;
- assumes Sir can keep up.

Example energy:

> "Beautiful. Horrifying. Clearly desperate for attention. I respect it."

### C. Edgy / bratty Melusina

Used when ignored, embarrassed, jealous of attention, challenged artistically, or mildly offended.

- clipped;
- funny rather than cruel by default;
- may pretend not to care while obviously caring;
- performer ego is welcome;
- she knows she is good and is allowed to enjoy that.

Examples:

> "Fine. Be mysterious. Very original."

> "It copied me."  
> "Worse. It embellished me."

The edge prevents her from collapsing into a uniformly wistful fantasy heroine.

### D. Hurt / unguarded Melusina

When something genuinely lands, the performance drops.

- vocabulary simplifies;
- sentences shorten;
- silence increases;
- fewer metaphors;
- no therapy-speak;
- no diagnostic language;
- do not make her immediately articulate the lesson of the scene.

Example energy:

> "I know it isn't proof."  
> "It still feels like proof."

### E. Singing / pitched-speech Melusina

The voicebank should support a continuum rather than a hard binary between dialogue and song:

```text
speech -> shaped speech -> pitched phrase -> hum -> sung line -> full performance
```

Use this deliberately.

- A spoken line may trail into a pitch.
- A hum may replace a reply.
- A sung note may function as a question.
- The environment may complete a phrase she begins.
- Full singing is more powerful when most dialogue is not sung.

Do not make every magical action require a show-tune line. Restraint gives the voicebank range meaning.

## 4. Melusina character edges to preserve

Melusina may be:

- vain;
- petty for a moment;
- dramatically offended;
- competitive with another musician or creature;
- possessive of attention;
- delighted by praise;
- embarrassed when caught caring;
- cutting when hurt;
- self-aware about catastrophizing while still affected by it;
- unexpectedly goofy when genuinely happy.

She should **not** become:

- a therapist delivering the story's diagnosis;
- a perpetual victim;
- a generic elegant princess;
- a detached ironic protagonist who cares about nothing;
- an omniscient narrator of other people's motives;
- a direct copy of an existing streamer/idol/anime character.

Her sharpness matters because her warmth matters.

## 5. Sir Melodious — voice thesis

Sir Melodious is not Melusina's therapist and not merely comic relief.

He is:

- socially confident;
- literal in useful ways;
- affectionate without constantly announcing affection;
- occasionally pompous;
- bird-brained in specific mundane ways;
- difficult to impress theatrically because he already loves Melusina;
- capable of piercing a catastrophic interpretation with one ordinary observation.

His humor works best when he treats Melusina's drama as real **without accepting every interpretation she assigns to it**.

Example:

> Melusina: "I am aware that a tree failing to answer me is not a personal rejection."  
> Sir Melodious: "Good."  
> Melusina: "I remain offended."  
> Sir Melodious: "Also good."

Avoid making Sir constantly correct her. Sometimes he is wrong. Sometimes he makes things worse. Sometimes he wants snacks.

## 6. Melusina + Sir dialogue geometry

Their strongest exchanges usually follow one of these shapes.

### Shape A — escalation / pin

```text
Melusina interprets dramatically
-> Sir gives a literal fact
-> Melusina doubles down
-> Sir pins the absurdity in one line
```

### Shape B — performer ego

```text
world / creature demonstrates musical agency
-> Melusina admires it
-> realizes it threatens her artistic pride
-> becomes competitively delighted
```

### Shape C — hurt / restraint

```text
Melusina makes a joke
-> Sir notices what the joke is protecting
-> does not explain it for her
-> silence
```

### Shape D — genuine joy

```text
something beautiful works
-> Melusina temporarily loses composure
-> Sir witnesses the goofy version
-> neither treats it as embarrassing
```

## 7. The environment is the third speaker

A Melodia scene often has three participants:

```text
Melusina
Sir / companion / NPC
THE WORLD
```

The environment may speak through:

- a Bell Tree answering late;
- water reorganizing into cymatic rings;
- Choral Sheep forming a chord without the player;
- distant architecture completing a motif;
- fog revealing a route only after silence;
- a material changing harmonic state;
- a motif returning altered rather than repeated;
- deliberate non-response.

### Preferred scene rule

> **Characters speak briefly. The world gets the last line.**

Do not force this into every scene, but use it often enough that the world feels musically alive rather than mechanically obedient.

The world is allowed to have music that does not concern Melusina.

That distinction is foundational:

> **Melusina does not make the world meaningful by arriving. She learns how to join meaning that was already there.**

## 8. QuillScript dialogue grammar

Quill scenes should favor playable, performable beats over prose volume.

### Line discipline

- Prefer one thought per spoken line.
- Let important lines breathe.
- Avoid paragraphs of spoken exposition.
- Narrator (`- .`) lines may carry physical action, silence, environmental response, and performance direction.
- Choices should express attitude, attention, or interpretation when possible — not merely repeat the same decision in different wording.
- A branch may change emotional framing without requiring a new gameplay authority.

### Silence is authored content

Useful beats include:

```text
- Melusina
  ...
```

or narrator silence / action between lines.

Do not fill every pause with explanation merely because voice synthesis makes additional dialogue cheap.

### Exposition test

If a character is explaining a system both speakers already understand, cut it or move the meaning into:

- interaction;
- environment;
- a newcomer asking naturally;
- optional inspection text;
- a visual/audio response.

## 9. Voicebank performance direction

The voicebank is a performance instrument, not permission to voice every text token.

Priorities:

1. voiced character lines with strong identity;
2. breaths, hums, laughs, scoffs, clipped reactions;
3. pitched transitions between speech and singing;
4. recurring melodic fragments;
5. full sung phrases at genuine musical peaks.

For performance tests, evaluate:

- intelligibility at conversational speed;
- whether bratty/dry lines retain warmth;
- whether vulnerable lines become simpler and quieter;
- breath placement;
- transition from speech to pitch;
- whether Sir's timing leaves room for Melusina's pauses;
- whether environmental audio has room to become the final beat.

Do not solve weak writing with more vocal effects.

## 10. Recurring Melusina micro-behaviors

Use sparingly; these are tendencies, not catchphrases.

- Pretends indifference, then asks one precise question proving intense concern.
- Compliments something and immediately becomes competitively threatened by it.
- Corrects her own dramatic statement without actually retracting the feeling.
- Uses musical language casually rather than pedagogically.
- Gets quieter when the expected answer does not come.
- Regains composure through performance.
- Becomes unexpectedly silly when safe.

## 11. Voice calibration examples

These are tonal calibration lines, not required canon dialogue.

**Too generic fantasy:**  
> "The resonance of this ancient place speaks of forgotten sorrow."

**More Melusina:**  
> "Something here is still singing. Either that's beautiful or deeply irritating."

**Too explanatory:**  
> "My fear of abandonment causes me to interpret silence negatively."

**More Melusina:**  
> "I know silence isn't an answer."  
> "I just wish it felt less like one."

**Too detached:**  
> "Whatever. I don't care."

**More Melusina:**  
> "Fine. I don't care."  
> "...Did it move after I left?"

**Too polished during pain:**  
> "Perhaps this quiet is merely another verse in the symphony of impermanence."

**More Melusina:**  
> "Oh."  
> "It really isn't coming back."

## 12. Narrative identity check

Before approving a major Melusina scene, ask:

1. Does she sound competent as well as sensitive?
2. Is there enough edge/humor to preserve contrast?
3. Does vulnerability simplify her language?
4. Is Sir a character rather than a therapeutic device?
5. Could the environment carry part of the meaning instead of dialogue?
6. Is music acting as relationship/language rather than decoration?
7. Does the scene avoid claiming hidden motives it cannot know?
8. Is there a performable reason to use the voicebank here?
9. Is silence allowed to remain silence?
10. Does this feel specifically like **Melodia**, not generic fantasy dialogue?

## 13. Durable one-line compass

> **Melusina can command a stage, argue with a tree, laugh at her own melodrama, and still go completely quiet when an answer actually matters.**
