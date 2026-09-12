# Melodia Identity in Mechanics + Loop Closeout — 2026-07-30

**Companion to:** `Docs/FOUNDATION_CLOSEOUT_DECISIONS_2026-07-30.md` (Decisions 016–021 now logged)

---

## 1. What actually remains for the Persona-lite loop

Smaller than it looks. The vertical slice needs **one turn** of the loop, not a repeating one.

| Gap | Cost | Notes |
| --- | --- | --- |
| Nothing writes `SocialStats` | 1 intent + 1 Quill choice | Decision 018. This is the wire that closes the loop. |
| No *visible* stat gate | 1 quest prerequisite + 1 UI line | A currency the player cannot see spent is not a currency. |
| Nothing advances `PhaseIndex` | 1 call at the bed | One dream = one phase. |
| Resonance is invisible | Battle UI work | Decision 017 corollary — highest-value UI task in the slice. |
| Save round trip unproven | Testing | Still the gate for everything. |

`BondRanks` stays reserved and unused — correct for the slice.

**What is deliberately NOT needed:** a calendar, time-of-day, scheduling, activity menus, or a
repeating day. Persona's loop repeats because time is scarce and you choose what to spend it on.
Melodia's slice is a single dream. The *schema* supports repetition (`PhaseIndex`); the *content*
does not need to yet, and building it would break the stop rule.

---

## 2. Ingraining Melodia's identity into the mechanics

Identity does not come from more systems. It comes from **one idea repeated in every context**.

### The thesis, now that Decision 016 is locked

> **Melodia is music you cannot fail at.**

The no-miss decision is not a concession to accessibility — it is the game's argument. Lean all the
way in: the battle UI never shows "MISS", never shows a red timing bar, never shows a broken combo.
Timing that lands well *adds*. Timing that does not is simply quieter. A player who cannot read
rhythm should finish the game and never know they were being timed.

### Resonance as the universal verb

You already have the mechanic. Make it the whole vocabulary — same shape, three contexts:

| Context | Mark set by | Answered by |
| --- | --- | --- |
| **Battle** | Petal Cadence | Skybound Refrain (bonus) |
| **Dialogue** | Sir says something | A Quill choice that echoes it (stat gain) |
| **Exploration** | A place that is listening | Arriving with the right quest/phase (marker resolves) |

One word — *resonance* — describing call-and-response in combat, conversation, and place. That is
what identity in mechanics actually means, and it costs almost nothing because all three seams
already exist (`Resonance` buff, allowlisted intents, `IsGatedContentAvailable`).

### Sir is the answering voice — make it a rule

Design rule, worth writing down: **Sir's skills always key off Melusina's marks; they never stand
alone.** He is not a second damage dealer, he is the response. This is why the co-op skill pair
already feels right, and it gives every future Sir skill an obvious shape. It also means party
composition carries narrative meaning without a single line of dialogue.

### Musical time as diegetic time

You now have a music clock and `PhaseIndex`. Name the structure musically in player-facing text —
a dream is a **movement**, its phases are **bars**. Zero code, immediate identity.

### Name the social stats musically

Not Courage/Charm/Knowledge. Something like **Harmony**, **Tempo**, **Timbre**. Costs one line of
data, and changes how the entire Persona layer reads. Do this before content is authored against
the IDs, not after — stat IDs go in the save record.

---

## 3. The open-source resources — verdicts

Assessed against where you actually are: foundation stage, save round trip unproven, one rhythm
profile unauthored, and a full system drive.

| Resource | Verdict | Why |
| --- | --- | --- |
| **unDAW** | **Study, do not adopt** | Its own README: *"many features included in the repo that just don't work, either because they were never finished or because I didn't maintain them."* Targets 5.4+. More importantly it is a **competing musical-time authority** — exactly what Decision 012 just consolidated. Read it for how it drives the MetaSound Builder subsystem; take nothing wholesale. |
| **Quartz Music System (landreville)** | **Mine for API ideas** | Closest in spirit — small, additive, subdivision scheduling. But you already built `UMelodiaMusicClockSubsystem`. Adopting it would re-create the many-clocks problem. Steal the quantized-scheduling node shape if it is better than yours. |
| **UE-Midi-Parser** | **Skip** | `HarmonixMidi`'s `UMidiFile` already parses MIDI, is engine-maintained, and is already a dependency of your build. Strictly redundant. |
| **Metasound-Nodes (hg42)** | **Maybe, later** | Custom MetaSound nodes are additive and sandboxed — genuinely low risk. But nothing is blocked on them today. Revisit during the sound-design pass. |
| **Maximilian** | **Skip** | See below. |
| **Tonic** | **Skip** | See below. |

### Why Maximilian and Tonic are the clearest "no"

**MetaSound is already a full procedural synthesis system**, built into the engine, sample-accurate,
and natively integrated with Quartz and Harmonix. Bolting in a foreign C++ synthesis library means:

- no Quartz sample-accurate scheduling (the thing you just standardised on);
- a second audio graph outside MetaSound, which is the same second-authority mistake in a new domain;
- a licensing review you do not need;
- and worse engine integration than the tool already shipping in your editor.

If you want algorithmic melody generation for songcraft, the correct path is a MetaSound graph
driven by the music clock — not a third-party DSP library.

### A caution about that list

The citations attached to it do not support its claims — a Reddit thread about **C++ build systems**
is cited for Tonic, and a LinkedIn post for the MetaSound nodes. That is the signature of a
generated list with fabricated sources. The repos may well be real (unDAW verifiably is), but treat
every entry as unverified until you have opened it yourself. Worth knowing given the morning you
have already had with confident-sounding technical narratives.

---

## 4. Immediate next actions

1. Test the current build in PIE: route, one battle, hair on `head_x`, full body visible.
2. Prove the save round trip **including one social stat**.
3. Wire Decision 018: one `melodia:stat:<id>` intent + one Quill choice.
4. Make Resonance visible in the battle UI (Decision 017 corollary).
5. Clean the three content leaks in Decision 021 — deliberately, in-editor, one at a time.
6. Update `melodia_rules.json` `grade_multipliers` to reflect Decision 016, or mark that block
   explicitly historical so it is never ported into stock content.

---

## 5. Research reference (locked 2026-07-31, Decision 033)

The OMORI-informed decisions above (016/017) and this doc's thesis now trace back to a single cited
reference: [`Docs/Research/MELODIA_PSYCH_MUSIC_INDIE_REFERENCE_2026-07-31.md`](Research/MELODIA_PSYCH_MUSIC_INDIE_REFERENCE_2026-07-31.md).
It records OMORI, NecroDancer (the "never tell the player they were wrong" fairness model), Undertale,
and the psychological-horror vocabulary (SH2 fog/radio-static, Amnesia's sanity-as-placebo, Layers of
Fear's environment-as-unreliable-narrator, DDLC's facade-crack) — each with a Take/Reject verdict and
a landing system, and an explicit anti-patterns list. Horror is **tonal register only**; nothing in
that doc creates a mechanic or expands scope.

**Narrative hook companion (2026-07-31):** [`Research/MELODIA_BARD_GRIEF_HOOK_2026-07-31.md`](Research/MELODIA_BARD_GRIEF_HOOK_2026-07-31.md)
turns the author's lived material (grief, lived abandonment, BPD, OCD, isolation, feeling-behind)
into Melusina the travelling bard's story — the Resonance verb *is* the metaphor (a mark set, an
answer awaited), Sir Melodious is alive (flew off for snacks, retrievable), the heavy wound is a
past duet-partner, and the ending register is reunion. Feel-first, named once, per Decision 033.
