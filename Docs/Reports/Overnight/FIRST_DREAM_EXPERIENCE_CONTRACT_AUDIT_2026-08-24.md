# First Dream Persona / Infinity Nikki Experience Contract Audit — 2026-08-24

**Verdict:** the requested three-phase slice is now specified as a deterministic offline contract, not claimed as implemented. Current sources contain the narrative, progression, wardrobe vocabulary, capability seam, and stock encounter pieces, but the scarce preparation slot, resonant accessory binding, phrase-to-Glide transaction, combined four-outcome evening flow, and versioned day fragment remain design intent or live-evidence work.

Proof vocabulary is strict: `source_built`, `offline_proven`, `live_proven`, `design_intent`, and `LIVE_EVIDENCE_REQUIRED` are not interchangeable.

## Three-phase day

| Phase | Window | Player contract | Exit invariant | Proof |
|---|---:|---|---|---|
| MorningPreparation | 0:00–5:00 | Choose Sir or Priestess once, see the exact effect before confirmation, then leave with immediate feedback. | Preparation choice, modifier/cue, reaction key, and command ID are committed atomically before Expedition. | design_intent |
| Expedition | 5:00–22:00 | Preview/equip one accessory, follow one motif, complete one existing Piano phrase, unlock Glide, cross the route it reveals, then play one stock JRPG encounter with rhythm grading. | Exactly one typed battle outcome is committed and Quill resumes exactly once for victory, defeat, fled, or unavailable. | design_intent |
| EveningReturn | 22:00–30:00 | Receive a reaction that reflects both the morning relationship and typed battle outcome; understand one reward's single purpose; save and advance the phase. | Reaction, reward disposition, phase advance, checkpoint, and canonical save are replay-safe; failed reward/equip operations do not advance. | design_intent |

The phase order is `MorningPreparation → Expedition → EveningReturn`. One preparation slot is consumed per day. No calendar, weekday, NPC schedule, gacha, styling contest, second battle system, or second save system is introduced.

## Preparation choice contract

| Choice | Stable IDs | Distinct effect | Lifetime | Proof |
|---|---|---|---|---|
| Sir | NEED: stable Sir preparation choice ID; NEED: single-encounter rhythm-grace modifier ID; NEED: Sir evening reaction ID | One visible rhythm-grace modifier scoped to the next stock encounter; it may soften degree of success but never submit or replace a JRPG command. | Clear on the first terminal encounter outcome, including unavailable; repeat commit returns AlreadyApplied. | design_intent |
| Priestess | NEED: stable Priestess preparation choice ID; NEED: world-reading cue modifier ID; NEED: Priestess evening reaction ID | Commit the source-backed priestess_first_echo Harmony intent once and expose one readable world cue; the cue never grants Glide or completes the phrase. | The day slot is consumed once; the Harmony intent is idempotent per IntentId and the cue expires on EveningReturn. | source_built |

Current authored Priestess answers remain expressive because both converge to the same stat and quest notifications. The target Sir/Priestess selection is mechanically consequential only after the distinct effects and reaction checkpoints are authored.

## Fresh, Continue, and replay state contract

Fresh slot: `FreshSlot → MorningPreparation.AwaitingChoice → MorningPreparation.ChoiceCommitted → Expedition.WardrobePreview.GlideLocked → Expedition.AccessoryEquipped → Expedition.PhraseChallenge → Expedition.WorldResultCommitted → Expedition.GlideUnlocked → Expedition.VisibleRouteCrossed → Expedition.EncounterRequested → Expedition.BattleOutcome::<victory|defeat|fled|unavailable> → EveningReturn.QuillResumedOnce → EveningReturn.RelationshipOutcomeReaction → EveningReturn.RewardDisposition → EveningReturn.CheckpointCommitted → CanonicalJRPGSaveRequested → DayComplete`

Continue must restore:

- `MorningPreparation` — Restore day index and no/one committed preparation; never reopen the consumed alternative.
- `Expedition.before_phrase` — Restore choice, equipped accessory, locked Glide, motif checkpoint, and applied command IDs.
- `Expedition.after_phrase` — Restore world result and Glide; do not replay phrase completion or capability grant.
- `Expedition.encounter_pending` — Restart the encounter beat from its canonical checkpoint without replaying preparation, equip, phrase, or unlock.
- `EveningReturn.after_outcome` — Restore the exact typed outcome and choice-specific reaction checkpoint; do not invoke the battle callback again.
- `DayComplete` — Restore reward disposition and checkpoint, then advance to the next MorningPreparation without duplicate grants.

Continue outcome restoration:

- `victory` — `CanonicalJRPGSaveLoaded → RestoreTypedOutcome.victory → RestoreEveningReaction.<choice+victory> → DoNotInvokeBattleCallbackAgain → DoNotDuplicateRewardOrIntent`
- `defeat` — `CanonicalJRPGSaveLoaded → RestoreTypedOutcome.defeat → RestoreEveningReaction.<choice+defeat> → DoNotInvokeBattleCallbackAgain → DoNotDuplicateRewardOrIntent`
- `fled` — `CanonicalJRPGSaveLoaded → RestoreTypedOutcome.fled → RestoreEveningReaction.<choice+fled> → DoNotInvokeBattleCallbackAgain → DoNotDuplicateRewardOrIntent`
- `unavailable` — `CanonicalJRPGSaveLoaded → RestoreTypedOutcome.unavailable → RestoreEveningReaction.<choice+unavailable> → DoNotInvokeBattleCallbackAgain → DoNotDuplicateRewardOrIntent`

Replay: `Reissue stable command ID → AppliedCommandIds contains ID → Return AlreadyApplied → Rebuild presentation read model only → Do not re-grant, re-equip, re-unlock, re-resume, or advance checkpoint`

Atomic rejection: `Equipment or reward authority rejects → Return Rejected → Do not add command ID → Do not advance narrative checkpoint or day phase → Show authored recovery and allow retry`

## Battle outcome contract

| Outcome | Current source | Target continuation | Reward | Proof / open evidence |
|---|---|---|---|---|
| victory | QSC has a distinct victory reaction; progression completes face_echo and grants reward.first_resonance_echo. | EveningReturn; resume Quill once; preserve morning choice; present victory consequence and reward once. | reward.first_resonance_echo | offline_proven; LIVE_EVIDENCE_REQUIRED: one outcome callback, one Quill resume, one reward grant. |
| defeat | QSC has a distinct defeat reaction; progression fails face_echo and records echo_unresolved without a reward. | EveningReturn; resume Quill once; no progression block; preserve defeat for the evening reaction. | NEED: owner decision: no reward or the slice's single outcome-neutral reward | offline_proven; LIVE_EVIDENCE_REQUIRED: one outcome callback and one Quill resume with no victory reward leak. |
| fled | QSC has a distinct fled reaction; progression shares the defeat failure intent and echo_unresolved consequence. | EveningReturn; resume Quill once; no progression block; retain fled as a distinct typed outcome. | NEED: owner decision: no reward or the slice's single outcome-neutral reward | source_built; LIVE_EVIDENCE_REQUIRED: fled remains distinguishable after save/reload. |
| unavailable | QSC contains fallback copy, but current progression has no unavailable terminal intent and the older model fails closed without resuming. | Commit a typed unavailable result once, resume Quill once into EveningReturn, grant no phantom victory state, and keep recovery authored. | NEED: owner decision: recovery presentation only or the slice's single outcome-neutral reward | design_intent; LIVE_EVIDENCE_REQUIRED: unavailable starts no battle, mutates no JRPG state, resumes Quill exactly once. |

Every outcome, including `unavailable`, enters EveningReturn and resumes Quill exactly once in the target contract. A rhythm miss changes degree of success, never access to the normal JRPG command or story progression.

## Exactly-once matrix

| Analysis row | Phase | Command ID | Atomic effect | Repeat | Failure | Proof |
|---|---|---|---|---|---|---|
| preparation.sir | MorningPreparation | NEED: stable command ID for Sir preparation | choice + grace modifier + Sir evening key | AlreadyApplied | Rejected; consume=false; advance=false | design_intent |
| preparation.priestess | MorningPreparation | NEED: stable command ID for Priestess preparation | choice + Harmony/world cue + Priestess evening key | AlreadyApplied | Rejected; consume=false; advance=false | design_intent |
| dialogue.advance | MorningPreparation | NEED: stable dialogue-checkpoint command ID | one Quill checkpoint advance | AlreadyApplied | Rejected; consume=false; advance=false | design_intent |
| wardrobe.equip | Expedition | NEED: stable accessory equip command ID | Cos_Accessories_MelusinaV2 loadout only | AlreadyApplied | Rejected; consume=false; advance=false | design_intent |
| phrase.complete | Expedition | NEED: stable phrase-completion command ID | one typed world challenge result | AlreadyApplied | Rejected; consume=false; advance=false | design_intent |
| capability.unlock.glide | Expedition | NEED: stable Glide-unlock command ID | Glide unlock through wardrobe capability provider | AlreadyApplied | Rejected; consume=false; advance=false | design_intent |
| route.payoff | Expedition | NEED: stable blocked-route payoff command ID | one visible route state | AlreadyApplied | Rejected; consume=false; advance=false | design_intent |
| encounter.request | Expedition | NEED: stable encounter request command ID | one request to IMelodiaJRPGPort | AlreadyApplied | Rejected; consume=false; advance=false | design_intent |
| battle.outcome.victory | Expedition | NEED: stable victory outcome command ID | typed victory + source completion intent | AlreadyApplied | Rejected; consume=false; advance=false | design_intent |
| battle.outcome.defeat | Expedition | NEED: stable defeat outcome command ID | typed defeat + source failure intent | AlreadyApplied | Rejected; consume=false; advance=false | design_intent |
| battle.outcome.fled | Expedition | NEED: stable fled outcome command ID | typed fled retained separately from defeat | AlreadyApplied | Rejected; consume=false; advance=false | design_intent |
| battle.outcome.unavailable | Expedition | NEED: stable unavailable outcome command ID | typed unavailable without JRPG mutation | AlreadyApplied | Rejected; consume=false; advance=false | design_intent |
| quill.resume | EveningReturn | NEED: stable Quill-resume command ID | exactly one resume for any typed outcome | AlreadyApplied | Rejected; consume=false; advance=false | design_intent |
| evening.reaction | EveningReturn | NEED: stable relationship+outcome reaction command ID | one of eight authored reaction checkpoints | AlreadyApplied | Rejected; consume=false; advance=false | design_intent |
| reward.present | EveningReturn | intent.first_dream.reward.first_resonance_echo | one reward disposition with one stated purpose | AlreadyApplied | Rejected; consume=false; advance=false | offline_proven |
| phase.advance | EveningReturn | NEED: stable day-phase advance command ID | EveningReturn checkpoint then next day | AlreadyApplied | Rejected; consume=false; advance=false | design_intent |
| canonical.save | EveningReturn | NEED: stable canonical save request command ID | versioned Melodia fragment inside BP_JRPGSaveGame | AlreadyApplied | Rejected; consume=false; advance=false | design_intent |
| canonical.reload | Any | NEED: stable load request correlation ID | same phase/choice/loadout/unlock/outcome/checkpoint | AlreadyApplied | Rejected; consume=false; advance=false | design_intent |
| replay.applied_command | Any | NEED: stable replay probe command ID | AlreadyApplied and presentation-only refresh | AlreadyApplied | Rejected; consume=false; advance=false | offline_proven |

## 0–30 minute pacing

| Window | Phase | Player verb | Choice | Feedback | Payoff | Failure recovery | Proof |
|---|---|---|---|---|---|---|---|
| 0:00–2:00 | MorningPreparation | Walk, inspect the empty perch, approach preparation choice | orientation and movement | NPC/perch highlight and concise goal | preparation choice becomes readable | Resume at morning checkpoint; no command consumed | source_built |
| 2:00–5:00 | MorningPreparation | Choose Sir or Priestess once | one scarce relationship choice | show exact modifier/cue, slot consumed, evening promise | meaningful day commitment | Rejected commit leaves both choices available; Applied commit survives reload | design_intent |
| 5:00–7:00 | Expedition | Preview and equip the resonant accessory | equip or back out | Cos_Accessories_MelusinaV2 visible; Glide shown locked with reason | outfit identity plus anticipated capability | Failed equip consumes nothing and cannot advance | design_intent |
| 7:00–9:00 | Expedition | Follow one audible/visible motif | route reading; Priestess cue changes readability, not access | motif feedback points toward Piano host | find the phrase challenge | Return to last expedition checkpoint | design_intent |
| 9:00–11:00 | Expedition | Play the selected Piano phrase | timing/input retry | grade plus explicit retry; success commits once | Glide unlock and world response | Miss never consumes command or blocks retry | design_intent |
| 11:00–14:00 | Expedition | Use Glide across the previously blocked route | take Glide route or inspect fallback | movement state and accessory remain visible | visible traversal payoff within six minutes of preview | Fall returns safely before the gate; unlock remains committed | design_intent |
| 14:00–22:00 | Expedition | Choose Attack/Skill/Item/Flee and time rhythm inputs | normal JRPG command choice with rhythm degree | grade modifies command feedback; miss still resolves command | typed victory/defeat/fled/unavailable | Any outcome resumes Quill once; unavailable starts no phantom battle | design_intent |
| 22:00–25:00 | EveningReturn | Read and advance the choice+outcome reaction | dialogue pacing only | distinct Sir/Priestess and outcome copy | relationship consequence | Restore exact reaction checkpoint; no battle callback replay | design_intent |
| 25:00–28:00 | EveningReturn | Inspect one reward and confirm return | accept presentation, not a second reward choice | one purpose stated; disposition visible | phase/checkpoint commit | Rejected reward does not consume command or advance | design_intent |
| 28:00–30:00 | EveningReturn | Save, return to menu, Continue, verify state | Continue or replay probe | same choice/outfit/unlock/outcome/dialogue checkpoint | restart proof and next-day handoff | AlreadyApplied on repeated commands; no duplicate intents/rewards | offline_proven |

## Persona lens

Persona's useful lens is opportunity cost plus relationship feedback, not a full calendar.

Scarcity: One preparation per day; atomic commit makes the alternative unavailable until the next day.

Expressive and consequential choices are scored separately. The feedback loop is: `choice → immediate effect card → expedition expression → outcome-specific evening reaction → canonical save`.

## Infinity Nikki lens

Infinity Nikki is used only as a lens for an explicit outfit-to-world verb, never as a parity or affiliation claim.

Target loop: `source-backed accessory → atomic equip → phrase result → Glide unlock → visibly blocked route → crossing payoff`

Current playable verdict: **False** — Manifest is source-ready, its accessory has no resonant form, and the current progression/golden run contain no wardrobe or Piano challenge beat.

## Drift report

| ID | Severity | Finding | Resolution | Proof |
|---|---|---|---|---|
| target_day_phase_absent | missing_contract | Current progression has six story beats but no day index, three-phase enum, or one-slot preparation economy. | Introduce the types-only contracts after owner approval; keep Narrative as command boundary. | source_built |
| preparation_choice_effect_drift | meaning_drift | Current Priestess response choices are expressive and there is no Sir-versus-Priestess scarce preparation command. | NEED: authored stable choice/modifier/reaction IDs. | source_built |
| wardrobe_resonance_gap | missing_pillar | Cos_Accessories_MelusinaV2 exists but resonant_form_id is null; current progression and golden run do not preview, equip, or query it. | Bind through the existing Wardrobe port/provider; do not add capability state to UI or narrative. | source_built |
| piano_world_result_gap | missing_pillar | No selected phrase/challenge/command ID is present in First Dream content and music_world_key remains an open live gate. | NEED: select the existing phrase and author stable challenge/command IDs. | source_built |
| unavailable_terminal_gap | outcome_drift | QSC has unavailable fallback copy, but progression accepts only victory, defeat, and fled; unavailable lacks a typed terminal intent and resume-once proof. | Add typed unavailable routing through the existing bridge; no JRPG mutation or phantom reward. | source_built |
| defeat_fled_collapse | outcome_drift | Defeat and fled have distinct QSC copy but share intent.first_dream.objective.face_echo.fail and the same saved failure flag. | Preserve the typed result in the versioned fragment so evening/reload can distinguish them. | source_built |
| reward_semantics_unresolved | owner_decision | The target evening promises one purposeful reward, while reward.first_resonance_echo is currently victory-only and other outcomes grant none. | OWNER_DECISION_REQUIRED: victory-only reward versus one outcome-neutral completion reward. | source_built |
| twenty_vs_thirty_minute_contract | scope_drift | The current playtest is a 0–20 minute route; the target day loop is a 20–30 minute three-phase slice. | Use the target pacing table for implementation; retain the older playtest as baseline evidence only. | source_built |
| proof_gates_open | proof_gap | wardrobe_equip_roundtrip, rhythm_grade_to_result, music_world_key, wardrobe_gameplay_hook, result matrix, and HUD single-writer proof remain open for this combined loop. | Only runtime evidence may close runtime gates. | LIVE_EVIDENCE_REQUIRED |

## Required heuristic flags

- `more_than_four_minutes_without_agency` — flagged `false`: Target has no >4 minute non-interactive span; the eight-minute battle is continuous command/timing agency.
- `apparently_meaningful_identical_effects` — flagged `true`: Current Priestess HarmonyAnswer and ListeningAnswer converge to the same priestess_first_echo stat intent and melodia_q_echo_01 quest notify. Treat them as expressive until the new Sir/Priestess preparation effects are authored distinctly.
- `payoff_delayed_over_six_minutes` — flagged `true`: Current source has no wardrobe-to-route payoff, so latency is unbounded. The target schedules accessory preview at minute 5 and visible route payoff at minute 11 (exactly six minutes).
- `absent_core_pillar` — flagged `true`: Current playtest/progression omit the playable wardrobe and music-as-key loops. The target contract includes both, but they remain DESIGN_INTENT until live gates close.

## Content ID resolution

| Kind | ID or NEED | Resolution | Evidence |
|---|---|---|---|
| encounter | melodia_smoke_encounter | resolved | MelodiaQuillSmoke.qsc |
| stat_intent | priestess_first_echo | resolved | MelodiaQuillPetalPriestess.qsc |
| stat | melodia_harmony | resolved | MelodiaQuillPetalPriestess.qsc |
| accessory | Cos_Accessories_MelusinaV2 | resolved | specs/wardrobe/wardrobe_catalog_manifest.v1.json |
| capability | Glide | resolved | specs/traversal/melodia_traversal_capability.v1.json |
| reward | reward.first_resonance_echo | resolved | specs/progression/melodia_first_dream_progression.v1.json |
| sir_choice | NEED: stable Sir preparation choice ID | NEED | No source ID found |
| priestess_choice | NEED: stable Priestess preparation choice ID | NEED | No source ID found |
| piano_phrase | NEED: selected existing Piano phrase stable ID | NEED | No First Dream binding found |
| world_challenge | NEED: First Dream world challenge stable ID | NEED | No First Dream binding found |
| resonant_form | NEED: resonant form ID for the accessory | NEED | Manifest value is null |
| evening_reactions | NEED: eight relationship+outcome reaction IDs | NEED | Current QSC reacts only to battle outcome |

## Owner decisions

- Reward semantics across defeat, fled, and unavailable.
- Exact Sir grace modifier policy and player-facing copy.
- Selection of the existing Piano phrase and blocked route.
- Eight evening reaction IDs/checkpoints.

## Live-only proof still required

- Does the accessory remain visible and equipped after process restart?
- Does phrase completion unlock Glide exactly once and open the visible route?
- Does a rhythm miss still submit the normal JRPG command and preserve progression?
- Do victory, defeat, fled, and unavailable each resume Quill exactly once?
- Does Continue restore choice, outfit, unlock, outcome, and dialogue checkpoint without duplication?
- Is MelodiaUIBridgeSubsystem the sole battle/rhythm presentation writer?

## Offline validation summary

```json
{
  "all_commands_failure_safe": true,
  "all_content_ids_resolved_or_need": true,
  "battle_outcome_count": 4,
  "exactly_once_row_count": 19,
  "fresh_continue_replay_present": true,
  "pacing_ends_at_thirty": true,
  "pacing_starts_at_zero": true,
  "phase_count": 3,
  "unique_analysis_ids": true
}
```

Generated deterministically from read-only text and JSON sources. No Unreal, binary assets, production source, canonical QSC, or progression spec was modified.
