# Presentation-Interface Integration — Proposal for Review

Prep pass per your brief: dance mocap on win, fall on death, sparkle, MPC audio reactivity + iridescence on Quartz BPM, UI tap/beat-hit animations, Figma motion + sheen. This is a **menu, not a commit** — tell me which lines to implement.

## Two bugs found while inventorying (worth fixing regardless of what else you pick)

**Bug A — the 6 presentation hooks are wired to nothing.** `MelodiaBattleSession.cpp` correctly calls `Execute_OnMelodiaCommandResolved/OnMelodiaVictory/OnMelodiaEnemyIntentStarted/OnMelodiaEnemyHit/OnMelodiaEnemyBroken/OnMelodiaEnemyDefeated` at the right moments — but zero classes (BP or C++) implement `IMelodiaCombatPresentationInterface`/`IMelodiaEnemyPresentationInterface`. Every call is a safe no-op. (Full detail: `Docs/BP_INTEGRATION_REVIEW_2026-07-18.md`.)

**Bug B — the audio-reactivity MPC writes to a mismatched collection.** `MelodiaRhythmReactivitySubsystem::AudioCollectionPath` targets `/Game/EnvSandbox/Materials/Functions/MPC_Portfolio_Audio`, which has only 2 scalar params (`BeatIntensity`, `RhythmPulse`). The C++ writes 12 different names (`BeatPulse`, `BassIntensity`, `MidIntensity`, `TrebleIntensity`, `ComboNormalized`, `CrescendoNormalized`, `CommandEnergy`, `BreakPulse`, `VictoryPulse`, `EnemyTension`, `BeatPhase`, `GlobalAudioReactivity`) — none of which exist on that collection, so every write is silently dropped. **Nothing currently reads live beat/combat state into any material, anywhere.** Separately, `/Game/Melodia/_PROJECT/04_Materials/MPC_Melodia_Palette` already exists with 17 well-named params including `GlobalSparkleIntensity`, `PaletteShift`, `GlobalEmissiveBoost`, `ProximityGlow` — much closer to what "iridescence on BPM" needs, and already the palette other materials presumably read from.

**Proposed fix for B** (mechanical, no creative call): either (a) add the 12 missing params to `MPC_Portfolio_Audio`, or (b) repoint `AudioCollectionPath` at `MPC_Melodia_Palette` and remap the `SetMPCScalar` calls to its existing names (`BeatPulse`→`BeatPulse` ✓ already matches, `VictoryPulse`→could map to `GlobalSparkleIntensity` pulse, etc.). **(b) is less churn and reuses the palette everything else presumably already samples — recommend it, but it's your call which MPC is canonical.**

## Asset inventory (confirmed to exist)

| Need | Asset found |
|---|---|
| Victory montage | `AM_Mocap_Victory` (already a montage, currently unused by anything) |
| Dance mocap raw takes | `A_Mocap_LittleDance`, `A_Mocap_LittleDance_001`, `A_Mocap_LittleDance_003`, `A_Mocap_Twirl_001` |
| Death/fall | `A_Die` (raw sequence, `/Game/Melodia/Characters/Melusina/Animations/`) — no montage wrapper exists yet |
| Hit reaction | `AM_GetHit` montage |
| Enemy side | `BP_MelodiaEnemyBase` + 3 subclasses have zero animation hookup checked yet — not inventoried this pass |
| Sparkle burst | `TriggerSparkleBurst()` already exists on `UMelodiaRhythmHUDWidget`, maps to `Motion/SparkleBurst` (Figma `72:2007`), texture art = `T_GradeHalo_{Perfect,Great,Good,Miss}.png` (already imported) |
| Figma motion contract | `Imports/UI/Specs/_MOTION_CHANNELS.md` — **already has a fully-specced gap list** (F-a/F-b/F-c/F-d) for StaffShimmer (sheen), NoteTrailIri (iridescence trail), BreakCrestReveal, and the `EMelodiaMotionTier` accessibility gate. This is pre-existing design work, not something to re-derive. |

## Proposed mapping — one line per ask, pick what you want

1. **Dance mocap on combat win** → `BP_Melusina` implements `IMelodiaCombatPresentationInterface::OnMelodiaVictory`, plays `AM_Mocap_Victory` if it already contains dance content, or compose a new montage from `A_Mocap_LittleDance`/`A_Mocap_Twirl_001` if `AM_Mocap_Victory` is a plain pose. *(Need your call: should I inspect `AM_Mocap_Victory`'s actual content first, or just build a fresh victory montage from the LittleDance/Twirl takes?)*
2. **Fall on death** → new `AM_Die` montage wrapping the existing `A_Die` sequence, played from `OnMelodiaEnemyDefeated`/a symmetric player-defeat hook (player-defeat interface call doesn't exist yet — would need a 7th interface event or reuse an existing one; flagging as a design decision).
3. **Enhanced sparkle** → extend `TriggerSparkleBurst()` call sites (already fires on Perfect/Break per the motion doc) — "enhanced" is subjective, need your direction on what changes (bigger burst? new particle? more triggers?).
4. **Audio-reactive materials + Nikki iridescence on Quartz BPM** → fix Bug B first (mechanical), then hook `PaletteShift`/`GlobalSparkleIntensity`/`BeatPulse` into whatever material(s) you want the iridescence sheen on — need you to point me at the target material(s), since "Nikki iridescence" isn't yet an authored material effect I found in the project.
5. **UI animations on tap/beat-hit** → this is **already fully speced** in `_MOTION_CHANNELS.md`'s F-a/F-b/F-c/F-d gaps (StaffShimmer sheen sweep, NoteTrailIri perfect-hit trail, BreakCrestReveal, motion-tier gate). Recommend implementing exactly that spec rather than inventing new UI motion — it already has Figma nodes, timing, and web-parity CSS selectors defined. F-c (`LastBreakRevealTime`) is explicitly called out in the doc as "the cheapest new cue to land."

## What I need from you to proceed

- Victory: reuse `AM_Mocap_Victory` as-is, or compose new from LittleDance/Twirl takes?
- Death/fall: new interface event for player-defeat, or reuse an existing one?
- Sparkle: what "enhanced" means concretely.
- MPC: repoint to `MPC_Melodia_Palette` (recommended) or patch `MPC_Portfolio_Audio`?
- Iridescence: which material(s) should sample it?
- UI tap/beat animations: confirm go-ahead on the existing F-a…F-d spec (my recommendation), or different direction?
