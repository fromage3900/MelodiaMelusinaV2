# Melusina Virtual Songstress — Day 1 Plan — 2026-09-08

> **Goal:** make the first tiny artifact where Melusina feels like a musical character-medium rather than only a game character.
>
> **Target duration:** one focused session.
>
> **Do not rebuild the voice stack. Do not build a whole music video.**

Companion creative SSOT:
`Docs/Music/MELUSINA_PERFORMANCE_PERSONA_BIBLE_2026-09-08.md`

---

## Definition of done

By the end of the session, produce **one 10–20 second Melusina performance postcard** containing:

1. one original musical phrase;
2. one usable Melusina singing render from the existing singing bank / OpenUtau lane;
3. optional spoken pickup or whisper from the existing CosyVoice Melusina voice;
4. one visible music→world response;
5. one visible or audible Sir Melodious resonance-state change;
6. one clean camera;
7. one captured video or MRQ proof;
8. provenance notes so the test is reproducible.

This is a character-media proof, not a finished release.

---

## Phase 0 — verify what already exists (20–30 min)

### Singing
Locate the exact Adachi-Rei-style Melusina bank currently being used.

Known repo references suggest:
- OpenUtau is already installed / previously used;
- Melusina JA VCV material exists;
- `studio/tracks/frost-rave/` has been used as a singing/lip-sync source;
- TuneLab/UTAU compatibility work exists.

Do not assume the August research doc's "blocked" state is current until the workstation is checked.

### Spoken voice
Verify the current CosyVoice server / asset.

Existing documentation points to:
- Fun-CosyVoice3-0.5B;
- anchor-seeded Melusina voice;
- default / gentle / whisper / nordic profiles;
- a previously working HTTP synthesis path;
- Japanese VC proof.

Render one line as a smoke test.

Suggested line:
> "Can you hear it answering?"

If the user meant a different "cozy voice TTC/TTS" asset than the documented CosyVoice system, record the exact tool/model/path before proceeding.

### Output
Record in session notes:
- singing bank path;
- singing renderer/version;
- CosyVoice path/profile;
- sample rate;
- one known-good output filename from each lane.

---

## Phase 1 — compose the micro-phrase (30–45 min)

Do **8 bars maximum**.

Working emotional arc:

**alone → searching → answer → bloom**

Keep it simple enough that the voice can carry identity.

Suggested harmonic behavior:
- exposed opening note / dyad;
- sparse bell or piano;
- one motif repeated with changed harmony;
- Sir Melodious answer enters near the midpoint;
- final phrase resolves with richer harmony.

No full song arrangement.

### Lyric seed
Use only if it helps; rewrite freely:

> Where the water remembers,  
> answer me once more.

Two lines are enough.

---

## Phase 2 — render Melusina's voice (30–60 min)

### Preferred first route
Use the existing artificial/Adachi-Rei-style bank in OpenUtau/TuneLab if it renders cleanly today.

Reason:
- it is already part of Melusina's authored voice lineage;
- it gives the first artifact a distinctive synthetic identity;
- it avoids spending Day 1 on training.

### Optional layer
Use CosyVoice for:
- a whispered pickup;
- breath;
- spoken pre-roll;
- ending phrase.

Do **not** attempt to force spoken TTS into the main sung line if the existing singing bank already works.

### Signature processing test
Create three buses/layers:

1. **Girl** — dry/intimate lead.
2. **Reflection** — subtle delayed/pitch-shifted double.
3. **Choir Beneath the Water** — only at the bloom.

Save both:
- dry voice;
- processed performance stem.

---

## Phase 3 — prototype the Sir Melodious tether as art (30–60 min)

The gameplay fact already exists:
**Melusina loses 50% damage when Sir Melodious is beyond the tether distance.**

Tomorrow's goal is to make that mechanic perceptible without a HUD explanation.

### Minimum prototype
Use two visual/audio states:

#### Unanswered Refrain
- Sir Melodious outside resonance range;
- exposed Melusina lead;
- one incomplete cymatic ring / broken paired form;
- restrained emission / world response.

#### Full Harmony
- Sir Melodious enters range or his answering phrase appears;
- harmonic layer enters;
- second ring / paired spiral appears;
- cymatic or architectural form completes;
- light/material response blooms.

Do not rewrite the combat mechanic tomorrow unless the runtime radius itself is broken.

---

## Phase 4 — performance postcard scene (60–90 min)

Use an existing clean stage or a minimal new staging setup.

**Do not build a new environment.**

Preferred ingredients:
- Melusina;
- shallow reflective water or a simple dark reflective plane;
- one rose-window / ornament element already in the project;
- one moon/key light;
- one music-reactive material/VFX response;
- Sir Melodious represented by his actual character if ready, otherwise by an authored off-camera answer / light cue for this prototype.

Camera:
- one shot;
- 50–85 mm;
- restrained movement or locked composition;
- close enough to read Melusina's face/body performance;
- no edit montage.

The artifact should survive with the effects turned off. The performance comes first.

---

## Phase 5 — animation / face (30–60 min)

Reuse existing systems before authoring anything large.

Available pipeline references:
- FACS builder;
- existing mocap library;
- OpenUtau singing as lip-sync source;
- existing retargeting workflow.

For Day 1:
- one breathing/idle or restrained gesture;
- eyes directed toward the perceived answer;
- one small facial change at Full Harmony;
- lip sync if the current automation is cooperative.

A tiny convincing reaction is worth more than a complex dance.

---

## Phase 6 — capture and review (20–30 min)

Capture a 10–20 second proof.

Preferred:
- UE5.8 MRQ if the scene is already in Unreal;
- otherwise the fastest existing proven capture lane.

Save:
- master video;
- clean audio stem;
- voice stem;
- source project / sequence name;
- one representative still for later review.

### Review questions
1. Do I recognize Melusina from the voice alone?
2. Does the world visibly respond to music?
3. Can I feel the difference when Sir Melodious answers?
4. Does Melusina feel like a person rather than an effects carrier?
5. Would I want to watch another 20 seconds?
6. Is there one image/sound I remember afterward?

If 4/6 are clearly yes, Day 1 succeeded.

---

## Optional only if energy remains

- try a second CosyVoice profile;
- render an alternate final note;
- test one bilingual phrase;
- make a clean thumbnail still;
- save a reusable performance-sequence template.

Do **not**:
- train DiffSVC;
- rebuild DiffSinger;
- redesign the character;
- invent a new shader framework;
- build the full chapel;
- make a 3-minute song;
- add a new website page.

---

## Tomorrow's first commandment

**Use what summer already built.**

The entire point of the production system is that the first Melusina performance should begin with music and art, not another infrastructure week.
