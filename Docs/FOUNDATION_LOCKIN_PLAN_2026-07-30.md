# Foundation Lock-In Plan — 2026-07-30

**Purpose:** take the 2026-07-29/30 gameplay baseline from "verified once, live" to a
foundation that is safe to edit for months, and land rhythm as a *Harmonix-driven
presentation layer that the authored skills consume* — without reopening combat authority.

**Reads first:** `_DECISION_LOG.md` (001–011) · `Docs/LOWER_TIER_FOUNDATION_LOCK_2026-07-29.md` ·
`Docs/HARMONIX_MIDI_RHYTHM_CONTRACT_2026-07-29.md` · `_VERTICAL_SLICE_SCOPE.md`

---

## Part 0 — State of the handoffs (review)

### What Sol/GPT actually left green

| Area | State |
| --- | --- |
| Native foundation closeout | Additive only: bridge teardown unbind, traversal `EndPlay` glide restore, cached `MPC_Portfolio_Audio`, `MELODIA_FOUNDATION_STATE` diagnostics. Live Coding clean, 285/285 Python, scoped diff clean. |
| Co-op skills | `BP_MelusinaPetalCadence`, `BP_SirSkyboundRefrain`, `BP_Resonance` exist as true stock children under stock authority (Decision 009). |
| Hair | Bone analysis done (465 vs 148, zero shared). Native `head_x` fallback staged. |
| Front end | `WBP_MainMenu` compile-clean, New Game creates `MelusinaSlot0`, Continue correctly disabled with no slot. |
| Battle UI crash | Isolated to UMG compile of stock `BP_BattleUI` during `BP_BattleController` prep; restored from autosave; `AOrreryMainMenuGameMode` no longer `FClassFinder`s in its constructor. |

### What was correctly stopped

Cline's overnight `RhythmCombatComponent` / `RhythmInputComponent` / `RhythmCombatUI` trio
computed **its own damage multipliers and combo state from input accuracy**. That is a second
combat authority and a direct violation of Decision 009, authored the same day 009 was written.
Quarantined under Decision 011. That call was right — do not restore it. `RhythmBeatTracker`
survived, and Part 2 below folds it into the real clock rather than deleting it.

### The five things nobody has written down yet

These are the blockers to "foundational, long-term-editable." Each is expanded below.

1. **Harmonix is enabled but unreachable from code.** The plugin is on in `BS_GodFile.uproject:220`,
   but no game module lists a Harmonix dependency. The contract is currently unimplementable.
2. **Four competing beat clocks.** Nothing is authoritative and none of them is Harmonix.
3. **Shipping content lives in `/Game/Experiments/`.** The *playable* Melusina unit and three of
   her four skills are there.
4. **There is no working backup path.** The healthy git is a side directory; LFS quota blocks push.
5. **Cook exit 25 blocks every packaged build.** Nothing has been proven outside PIE.

---

## Part 1 — Structural foundation (do before any new content)

### 1.1 Restore a real version-control path — P0

Current state: `C:\EnvironmentPortfolio` is not a repo. `BS_GodFile\.git` is designated
unhealthy and must not be committed through. The healthy tree is
`.repo_recovery_20260727\.git`, and its push is blocked by GitHub LFS quota.

That means today there is **no routine, reversible checkpoint for gameplay work.** Every item
below is riskier than it needs to be until this is fixed. Options, cheapest first:

| Option | Cost | Result |
| --- | --- | --- |
| Local bare mirror on a second physical drive + scheduled `git push` to it | ~1 hour | Restores rollback and off-drive redundancy immediately. No quota, no vendor. |
| Raise/repair GitHub LFS budget | billing | Restores the intended remote. |
| Move `.uasset`/`.umap` LFS pointers to a self-hosted LFS or drop LFS for a subset | ~half day | Fixes quota permanently, migration is disruptive. |

**Recommendation:** do the local bare mirror this week regardless of which long-term remote wins.
It is the single highest-leverage hour in this plan — everything else assumes you can undo.

### 1.2 Promote shipping content out of `Experiments/` — P0, one-time

The active battle unit is `/Game/Experiments/MelodiaJRPG/BP_MelusinaSwordsman_Presentation`, and
`BP_MelusinaFocusAttack`, `BP_MelusinaTrueStrike`, `BP_MelusinaDoubleHit`, `BP_MelusinaPetalCadence`
sit beside it, while Sir's skills live at `/Game/MelodiaIntegration/Party/Skills/`. Two homes for
one concept. This gets more expensive every asset you add, and `Experiments/` is exactly the folder
a future cleanup pass deletes.

Target layout — one root, mirrored per character:

```
/Game/Melodia/
  Party/
    Melusina/{BP_Unit, Skills/, Buffs/}
    Sir/{BP_Unit, Skills/, Buffs/}
  Battle/{Overlay/, Encounters/}
  Audio/{BGM/, SFX/, MIDI/, Rhythm/}   <- contract already names Audio/MIDI/
  UI/
  Levels/Opening/
```

Do it with **Asset Actions → Rename** (leaves redirectors), never a file move, then run a fixup
pass in a separate session. Do it *before* the Harmonix work so the new rhythm profiles are born in
the right place.

### 1.3 Collapse the doc surface — P1

There are ~30 top-level `.md` at the project root plus `Docs/`. Several actively contradict.
Most importantly: **`CLAUDE.md` is auto-loaded into every agent session and it is stale.** It says
"Gameplay work is paused during this push" and "Portfolio-first stabilization (2026-07-26)" —
Decision 008 (07-29) reversed that. It also carries the full 5-agent ownership table that
Decision 002 retired. Every agent that starts on this project is being misinformed in its first
200 tokens.

Fix: rewrite `CLAUDE.md` to be a ~40-line pointer — current phase, the authority table, the
never-touch list, and links to `_DECISION_LOG.md` / `LOWER_TIER_FOUNDATION_LOCK`. Mark
`AGENTS.md`, `AGENT_BOUNDARIES.md`, `AGENT_OPERATING_MODEL.md`, `AGENT_OWNERSHIP.md`,
`CURRENT_STATE.md` as historical in a `Docs/_Archive/` folder.

### 1.4 Close the native gate that is still open — P0, 10 minutes

From the 07-29 handoff, still outstanding. Editor fully closed:

```bash
"C:/Program Files/Epic Games/UE_5.8/Engine/Build/BatchFiles/Build.bat" BS_GodFileEditor Win64 Development -Project="C:/EnvironmentPortfolio/BS_GodFile/BS_GodFile.uproject" -WaitMutex -NoHotReloadFromIDE
```

Then restart and confirm `MELODIA_FOUNDATION_STATE` appears via
`unreal.MelodiaPresentationDiagnosticsLibrary.log_gameplay_foundation_state(world)`.
This same build also bakes the staged hair `head_x` fix and the "hair only" one-tick deferral,
so it clears three queue items at once.

### 1.5 Cook exit 25 — P0 for "long-term use"

Nothing is proven outside PIE until this is fixed. An overlong or invalid serialized name is
almost always a deeply-nested asset path or an asset with an illegal character. Fastest attack:
run the cook with `-verbose`, take the last package logged before exit, and check its full path
length; `Experiments/MelodiaJRPG/...` nesting from 1.2 is a plausible contributor, so sequence
1.2 before the next cook attempt and re-test.

---

## Part 2 — One clock: Harmonix as the single musical-time authority

### 2.1 The actual problem

There are currently **four** independent notions of "the beat," and the one the game runs on is
the worst of them:

| Source | Location | Drives | Problem |
| --- | --- | --- | --- |
| Quartz battle clock | `MelodiaCore/MelodiaAudioComponent` (`GetSongBeatPosition`) | audio-reactive MPC | only runs if a battle clock was started |
| Wall-clock fallback | `MelodiaAudioReactivePresentationSubsystem.cpp:17`, `FallbackBeatsPerSecond = 2.0f` | audio-reactive MPC when Quartz is absent | **hardcoded 120 BPM** |
| `URhythmBeatTracker` | `MelodiaIntegration/RhythmBeatTracker.h` | nothing yet | accumulates `DeltaTime` into `TimeSinceLastBeat` — audibly drifts inside a minute |
| `MelodiaRhythmExecutionComponent` | MelodiaCore | legacy | quarantined lane, its own accumulator |

And the one authored MIDI in the project — `Content/MelodiaIntegration/MIDI/128BPMarpeggiomelody.mid` —
is **128 BPM**, against a 120 BPM fallback. Any visual "beat" you see today is guaranteed to be
wrong against any music you actually play. This is precisely the failure that makes rhythm
mechanics feel bad for reasons players can never articulate.

### 2.2 The fix: `UMelodiaMusicClockSubsystem`

Harmonix ships exactly the right primitive in UE 5.8: `UMusicClockComponent`
(`Engine/Plugins/Runtime/Harmonix/Source/HarmonixMetasound/Public/HarmonixMetasound/Components/MusicClockComponent.h`).
It reads tempo/bar/beat from an actual MetaSound music source or from a MIDI tempo map, exposes
`BeatEvent` / `BarEvent` / `SectionEvent`, conversion helpers (`MsToBeat`, `BeatToMs`,
`GetBeatInBarAtMs`), and — the important part — **three calibrated timebases**.

**Step 1 — make Harmonix reachable.** `Source/BS_GodFile/BS_GodFile.Build.cs` currently ends at
`MelodiaCore`. Add, guarded so a Harmonix-less checkout still builds:

```csharp
PublicDependencyModuleNames.AddRange(new string[] {
    "Harmonix",           // ECalibratedMusicTimebase, musical time primitives
    "HarmonixMidi",       // UMidiFile
    "HarmonixMetasound",  // UMusicClockComponent
});
```

**Step 2 — one subsystem owns musical time.** A world subsystem that holds/locates the single
`UMusicClockComponent`, and is the *only* thing in the project any presentation code asks about
the beat. It exposes read-only accessors and re-broadcasts `BeatEvent`/`BarEvent`. It never
touches damage, turns, party, inventory, or save — Decision 011 and the MIDI contract both hold.

**Step 3 — retire the other three.**
- `MelodiaAudioReactivePresentationSubsystem`: replace the `FallbackBeatsPerSecond` branch with a
  read from the subsystem; keep a fallback but source its BPM from the profile asset, never a
  literal.
- `URhythmBeatTracker`: keep the class and its `OnBeat`/`OnBar` pins (Blueprints may already
  reference them) but gut the `DeltaTime` accumulator and make it a thin forwarder over the
  subsystem. Same API, correct time.
- `MelodiaCore` Quartz path: leave it, but the subsystem prefers Harmonix when a clock exists.

### 2.3 The non-obvious detail that decides whether this feels good

`ECalibratedMusicTimebase` has three values, and using the wrong one is the difference between a
rhythm layer that feels tight and one that feels mushy:

| Timebase | Use it for |
| --- | --- |
| `AudioRenderTime` | queueing musical events, scheduling stems |
| `VideoRenderTime` | **visuals** — UI pulse, VFX, montage sync (Harmonix's own default) |
| `ExperiencedTime` | **scoring player input** — this is what the player actually hears and sees |

So: judge input against `ExperiencedTime`, draw the beat ring against `VideoRenderTime`. Expose
one user-facing **audio/visual offset calibration** slider that feeds Harmonix's calibration
(see 3.1) — every rhythm game ships one, and no one remembers to build it until players complain.

---

## Part 3 — Rhythm *inside* the skills, without owning combat

### 3.1 The shape

Decision 009 and the MIDI contract say the same thing from two directions: rhythm may decorate an
already-valid stock command, never issue one. So the integration is not a component bolted onto
the battle — it is **data hanging off each skill**, read by a presentation overlay.

```
UMusicClockComponent  (Harmonix — owns musical time)
        │
UMelodiaMusicClockSubsystem  (single accessor, re-broadcasts beat/bar)
        │
        ├─► MelodiaJRPGBattleOverlaySubsystem  ── UI ring / pulse   [VideoRenderTime]
        ├─► MelodiaAudioReactivePresentationSubsystem ── MPC visuals [VideoRenderTime]
        └─► UMelodiaJRPGPresentationRhythmComponent ── grades input  [ExperiencedTime]
                    │  (already exists, already presentation-only,
                    │   PresentationScalar is explicitly *not* a damage multiplier)
                    ▼
             FJRPGPresentationRhythmResult → VFX/SFX/anim intensity only

Stock BP_BattleSkillBase ── damage, targets, buffs, turn release ── UNTOUCHED
```

`UMelodiaJRPGPresentationRhythmComponent` was built for exactly this and is currently unused.
Its doc comment already states `PresentationScalar` is visual intensity, not a combat multiplier.
That is the seam. Wire it; don't write a new one.

### 3.2 `DA_MelodiaRhythmProfile` — the authoring unit

One data asset per skill, as the contract's "first proof asset" describes. Fields:

- `UMidiFile* Source` — the authored MIDI (tempo map + note lanes)
- `TSoftObjectPtr<UMetaSoundSource> MusicSource`
- `FName SkillId` — stable ID matching the stock skill, not a Blueprint path
- `FMelodiaRhythmWindows Windows` — reuse the existing struct from `MelodiaCoreRulesLibrary`
- `TSoftObjectPtr<UAnimMontage> Presentation` — e.g. `AM_Mocap_BasicAttack`
- Downbeat VFX / UI pulse / SFX stem rows
- `bool bRhythmOptional = true` — **hard requirement**, see 3.4

First asset, per the contract: `DA_MelodiaRhythmProfile_PetalSever`, one `.mid` at fixed BPM, one
bar, one obvious downbeat, no gameplay effect at all until the stock battle and the timing
presentation are both visually signed off.

### 3.3 Where the two authored skills land

| Skill | Rhythm reading | Stock behaviour if rhythm is off |
| --- | --- | --- |
| **Petal Cadence** (Melusina) | downbeat pulse on the petal VFX; UI ring during the cast; `Resonance` applied on the bar line | identical: moderate-MP opener, applies `Resonance`, one turn release |
| **Skybound Refrain** (Sir) | the "refrain" answers Petal Cadence's bar — pulse cadence inherits the same profile so the pair reads as call-and-response | identical: Focus Attack, bonus branch on `Resonance` presence |

Note the design gift already sitting in the data: Resonance is a **one-turn buff**, and the pair is
already a call-and-response. That is musically meaningful *without any timing judgement at all*.
Land the pair working on stock rules first (it is the last remaining co-op mechanic per
`_VERTICAL_SLICE_SCOPE.md`), then let Harmonix make it *sound* like a call and response. Do not
invert that order.

### 3.4 The rule that keeps this shippable

> Every skill must be fully playable, at full value, with the rhythm layer disabled.

`_VERTICAL_SLICE_SCOPE.md` already lists "Rhythm as required battle authority" under Explicitly
Deferred, and the flow priorities say "without making rhythm mandatory." Enforce it mechanically:
a `melodia.Rhythm.Disable 1` console var, and the acceptance test for every profile is *run the
skill twice — once with the layer off — and confirm identical stock damage, target, and turn
release*. That single test is what stops the quarantined-component failure from recurring.

---

## Part 4 — QOL lock-in

### 4.1 Already staged, needs finishing — P0

`UMelodiaGameUserSettings` persists master/music/SFX volume, reduced motion, high-contrast text,
minimal HUD, and UI scale; `WBP_MelodiaSettings` has the named controls; `SM_MelodiaUserPreferences`
is the SoundMix. **The bindings are not wired and it has never survived a restart.** Finish this in
the same pass as 1.4's build. Settings must never read or write the JRPG campaign slot.

Add to the same panel while it is open: the **audio/visual calibration offset** from 2.3, and
**text speed / auto-advance** for Quill.

### 4.2 The flow priorities already identified

From `_VERTICAL_SLICE_SCOPE.md`, restated as binary gates:

- [ ] Deterministic focus and input-mode transitions
- [ ] No stale dialogue, battle HUD, cursor, or movement input after a transition
- [ ] Stable pre-battle and post-result checkpoints; no mid-battle save
- [ ] Continue disabled with no canonical slot **and explains why**
- [ ] Short transitions, skip-safe dialogue, no duplicated confirmation steps
- [ ] Clear result/reward feedback before control returns

### 4.3 The loose ends RPGs forget

Grouped by what they cost. None of these require reopening any authority.

**Input & focus (cheapest, most felt)**
- Every menu opens with something already focused — gamepad users cannot start otherwise.
- Every panel has a Back/Cancel that works on `Esc`, `B`, and right-click, and never leaves the
  player in UI-only input mode. This is the #1 source of "I'm stuck" bug reports.
- Hold-to-confirm on destructive choices (overwrite save, abandon); tap-to-confirm everywhere else.
- Rebindable keys, or at minimum a legend. `MelodiaBattleKeyboardLegendWidget` already exists as a
  non-focusable native overlay — good; make sure it reflects actual bindings, not literals.
- Input device swap mid-session re-skins prompts (keyboard ⇄ gamepad) without a restart.

**Save/load (highest damage when wrong)**
- One canonical slot is fine, but **write to a temp file and atomically rename** — a crash during
  save otherwise destroys the only slot the player has.
- Save version stamp + a graceful "this save is from an older build" path. `BP_JRPGSaveGame` is
  canonical; the Melodia narrative record embeds in it versioned — keep that discipline.
- Autosave on map transition and after battle result, both already checkpoint boundaries.
- Never save mid-battle (already a gate). Also: never save mid-dialogue.
- Show map name + timestamp + playtime on the slot. Two of three already read from stock fields.

**Combat readability**
- Damage numbers that don't overlap and don't disappear behind the UI.
- Turn order visible before you commit, not after.
- Skill tooltips that state MP cost and effect in words a first-time player parses.
- Target-selection state is unambiguous (who am I about to hit).
- A visible "this buff is active and expires in N turns" for Resonance — an invisible one-turn buff
  is a mechanic the player will never learn.
- Log or toast for the terminal result before control returns.

**Transitions & interruption**
- Skippable everything: dialogue, victory fanfare, transitions. Skip must be *safe* — the state
  change happens whether or not the animation finished.
- Fade-out/fade-in on every level travel so the player never sees an unloaded frame.
- Loading never leaves a black screen with no indication the game is alive.

**Accessibility (already half-built — finish it)**
- Reduced motion, high-contrast text, UI scale, minimal HUD are all already in
  `UMelodiaGameUserSettings`. They need to actually *do* something in each widget.
- Never signal information by colour alone — the accuracy grades in particular.
- Subtitles for any voiced or significant SFX cue.
- Rhythm difficulty = window width, exposed as a setting, not a hidden constant.

**Failure & recovery**
- Defeat returns somewhere sensible, never to a hard crash or the main menu with lost progress.
- Missing/unknown script or checkpoint routes to an authored safe location without erasing valid
  state (already a foundation gate — keep it).
- A `MELODIA_FOUNDATION_STATE`-style diagnostic reachable from a debug key, not only Python.

**Content hygiene that pays off in month three**
- Stable string IDs for every skill/item/quest, never Blueprint paths. Renaming an asset must not
  break a save.
- One naming convention, enforced: `BP_`, `WBP_`, `DA_`, `AM_`, `SM_`, `T_`, `MI_`.
- A redirector fixup pass scheduled after every rename batch, not deferred.
- A "new skill" checklist doc so skill #4 takes twenty minutes instead of an afternoon.

---

## Sequence

Strictly ordered — each step de-risks the next.

| # | Step | Gate |
| --- | --- | --- |
| 1 | Local bare-mirror backup (1.1) | `git push mirror` succeeds; a test restore clones |
| 2 | Closed-editor build (1.4) | `MELODIA_FOUNDATION_STATE` in log; hair on `head_x` in PIE; full Melusina body visible in combat |
| 3 | Finish Petal Cadence ⇄ Skybound Refrain on stock rules | Petal Cadence → Resonance visible → Refrain bonus → one turn release; and Sir without Resonance = normal damage |
| 4 | Rewrite `CLAUDE.md`, archive superseded docs (1.3) | A fresh agent session reads only current truth |
| 5 | Content promotion out of `Experiments/` (1.2) | All references resolve; redirectors fixed up |
| 6 | Cook exit 25 (1.5) | The three-map route packages and launches |
| 7 | Harmonix modules + `UMelodiaMusicClockSubsystem` (2.2) | One MIDI plays; one UI element pulses on its real downbeat |
| 8 | Retire the three stale clocks (2.3) | Nothing in the project reads a hardcoded BPM |
| 9 | `DA_MelodiaRhythmProfile_PetalSever` (3.2) | Skill runs identically with the layer on and off |
| 10 | Settings binding + calibration + persistence (4.1) | Survives a full process restart |
| 11 | QOL sweep (4.2, 4.3) | Each item is a checkbox with a live test |

Steps 1–3 are this week. Steps 7–9 are the rhythm work proper and should not start before step 5,
or the profiles get authored into a folder that is about to move.

---

## Increment 1 closeout — musical-time delegation (2026-07-30)

```text
Task attempted:      Delegate all rhythm timing to Harmonix and Quartz (Decision 012).
Files/assets changed:
  Source/BS_GodFile/BS_GodFile.Build.cs                       (+Harmonix, HarmonixMidi, HarmonixMetasound)
  Source/BS_GodFile/MelodiaIntegration/MelodiaMusicClockSubsystem.h/.cpp   (new)
  Source/BS_GodFile/MelodiaIntegration/RhythmBeatTracker.h/.cpp            (accumulator -> forwarder)
  Source/BS_GodFile/MelodiaIntegration/MelodiaAudioReactivePresentationSubsystem.h/.cpp
                                                              (120 BPM wall clock removed)
  Source/BS_GodFile/MelodiaIntegration/MelodiaJRPGPresentationRhythmComponent.h/.cpp
                                                              (+RecordInputNow)
  Plugins/MelodiaCore/Source/MelodiaCore/MelodiaAudioComponent.h/.cpp      (+GetBattleClockBPM)
  _DECISION_LOG.md (012), _TASK_QUEUE.md
Authority preserved: Stock TurnBasedJRPG owns turns/damage/targets/results/save. Nothing added
                     here touches a damage path. Decisions 009 and 011 stand.
Validation run:      Static only. Harmonix API verified against the UE 5.8 engine source
                     (MusicClockComponent.h, MusicalTimebase.h, BeatMap.cpp). Grep confirms no
                     wall-clock beat accumulator remains outside _Quarantine.
Observed result:     Not runtime-verified. Editor was open (PID 21272); new reflected types
                     cannot be hot-reloaded.
Unproven or blocked: Everything runtime. Requires the closed-editor build below.
Single next action:  Close the editor, run the BS_GodFileEditor build, restart, confirm
                     UMelodiaMusicClockSubsystem resolves and melodia.Rhythm.Disable exists.
Do not touch:        Config/, stock BP_BattleUI, hair assets, environment art.
```

### Design notes worth keeping

- **Harmonix reports beat-in-bar 1-based; Quartz reports it 0-based.** The subsystem normalizes
  both to 0-based so no consumer has to know which source is live. This was a live off-by-one
  waiting to happen.
- **`check()` was deliberately avoided** in the source-resolution paths — it compiles out of
  shipping builds, so a null there would crash rather than degrade. Both paths fall through to
  `Source == None` instead.
- **`melodia.Rhythm.Disable 1`** is the enforcement mechanism for the "every skill plays fully
  without rhythm" rule. It is checked inside the subsystem, not at each call site, so it cannot be
  forgotten.
- **The Quartz path cannot supply `Bar` or `TotalBeats`** — it has no authored tempo map. Those
  stay 0 and consumers must branch on `Source`. Only Harmonix gives complete musical time.
- **MelodiaCore's `MelodiaRhythmExecutionComponent`** still owns a legacy accumulator, but it is
  confirmed unreferenced from `Source/BS_GodFile/`. It stays in the quarantined MelodiaCore lane;
  do not wire it to anything.

## Stop rule (unchanged, restated)

If a rhythm addition does not make the existing encounter more readable or more enjoyable, remove
it before adding scope. If it needs to own damage, a turn, or a result to be fun — it is the wrong
design, not a case for reopening Decision 009.
