# Melusina Launch Intro — Marketing + Grief-Hook Scene Prep

**Date:** 2026-08-02
**Status:** Intro line WIRED in-game + rendered. Singing gate = model (parked). This doc is the
marketing/beat-sheet/scene prep along the approved wing.

---

## 1. Deliverables already done this session

| Deliverable | Location | State |
|---|---|---|
| Intro greeting WAV ("My name is Melusina, a traveling bard, residing at Castle | Frankenmelody�|pleasure to meet you.") | `Content\Melodia\Characters\Melusina\Audio\mel_intro_greeting.wav` (+ `.uasset` SoundWave | rendered |
| Intro statement + `$ Voice` wired as FIRST beat of `MelodiaMorningIntro` | `/Game/MelodiaIntegration/Narrative/MelodiaMorningIntro` | compiled (43→45 stmts), saved |z, 0 errored BP | OK |
| Verse propositions with the road and half-song | `melusina_bard_dialogue.json` | authored |

---

## 2. The grief hook (one-liner for marketing copy)

> **Melusina keeps arriving the day after the festival. The world has heard a better
> singer, and the one duet a partner who used to answer her. All she has left is the half-song
> it left ringing — and one bird she calls Sir Melodious, who flies off for snacks and
> always, impossibly, comes back.**

The grief is an **absence with a shape** (Decision 016): no corpse, no named loss. The
half-song is her grief, made audible. That's the hook — you feel a missing voice before you
know what it was.

---

## 3. Intro-scene beat sheet (for film / sequence / storyboard)

1. **Cold open — the empty perch.** Wide, candle-lit hall at dusk. Empty windowsill. A lute
   leans alone. (Voice Plays first Melusina line: *"The perch is empty again."*) Melodia's
   **intro greeting** has already landed, and now we re-frame it: the warm welcome hides the tub.
2. **The call-and-response rule taught.** Taps on glass — one for me, two for the wind. Establishes
   the game's core mechanic (call-and-response) as a **character rule**, not a tutorial.
3. **The half-song.** She hums two bars. No answer. A pause that is the real subject.
4. **Sir Melodious confirm.** One tap. Benign — he's just off feather for snacks. The absence
   breaks, and relief lands as comedy only after the tension.
5. **The dream signal.** Filtered, wrong: the bridge is gone. Catastrophe-read of a small
   absence. Cue the battle (vrhythm encounter).
6. **Reunion beat (voice only reaches Admiral later).** *"You were never too late."* The only
   name spoken in human language — feel-first, name-once.

Runtime target: ~90–120s. Emotional arc: empty → taught → ache → relief → dream-tension.

---

## 4. VCC / bank path to *singing* Melusina (with your SynthV licenses)

**Recommended µ vsynth: SynthV Studio Pro (installed) using Kasane Teto** as the source
voice, routed through **SVC (voice-conversion) to Melusina's timbre**:

- Teto = the highest-quality, most controllable of the three you own; best pitch/Vibrato range
  for LaraScar,bard phrasing. She gives clean, reliable sung progress with RegCompleteness.
- **Tsuina-chan** — seconds for agile ornamentation / fast melisma runs (wide pitch control).
- **Haruno / Harashibo** — best for the "celestial/public starry" answer-voice in the half-song
  duet (opposite instrument line).

**Workflow (days, not months):**
1. In SynthV Pro: enter Syllara lyrics that have under-Melodia melody; render clean piano-vocal
   stems off the /first tuning (Teto).
2. **SVC** that SynthV vocal to relic Melusina's timbre (we already have her anchor seed +
   an ONNX voice-converter chain from the Melusina TTS box). The room is good — SynthV holds
   the pitch,our SVC holds the timbre.
3. Master; drop into the half-song cue in UE.

This is the **creative-SVC route** and it's the one I recommend over retraining a baked VCV/UTAU
bank (months). Only build a hand-rec bit "Thousandetomuto plan" VCV/UTAU if Makkus sings ad, art-
direect listsynval becomes a marquee feature — say as later.

**Blender MCP:** not connected (refused; agent loop stopped). For building the intro-set
scene/environment you'd relaunch the geometry loop + Blender MCP addon, or I start the 9317
server if Blender is open.

---

## 5. To lock before I build the scene/sequence

- [ ] Grief-hook posture: **lost duet partner** (recommended) — confirm vs. "sacked Perille".
- [ ] Intro delivery: **fully voiced** (Melusina narrates) vs silent (text-only?) — recommended voiced.
- [ ] Which SynthV bank is your primary for the grate song: **Teto** (recommend) vs Tsuura vs Sora.