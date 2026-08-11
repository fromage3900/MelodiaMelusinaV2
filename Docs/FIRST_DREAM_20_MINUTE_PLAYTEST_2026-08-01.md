# First Dream 20-Minute Playtest

**Date:** 2026-08-01  
**Purpose:** Validate the grief hook and first complete Melodia narrative/gameplay loop while the surrounding environment is still being authored.  
**Canonical route:** `/Game/Melodia/Levels/Opening/L_MelusinaMorning` → merged Dreamstate content in `/Game/EnvSandbox/Environments/L_KaleidoNave` → stock JRPG encounter → exploration/save.

> **Route correction (2026-08-01):** The standalone `/Game/Melodia/Levels/Opening/L_Melodia_Dreamstate` leg named in the original timed script was merged into `L_KaleidoNave`. Treat references below to entering standalone Dreamstate and later arriving in KaleidoNave as two presentation beats within the merged KaleidoNave route, not two separate map loads. `ZenForestTest` remains protected and is not required by this test.

## Safety and authority rules

- Do **not** save `ZenForestTest` until its existing world-building edits are safe. This route does not require saving that map.
- Quill owns dialogue, choices, and story progression. A presentation widget must never advance the interpreter independently.
- The stock JRPG loop owns encounter input, outcome, rewards, and battle results.
- `AOrreryMainMenuGameMode` owns menu actions; `DA_OrreryRegistry` owns destination availability and travel semantics.
- Save/load is validated through the existing save authority, not by editor state or console mutation.
- The expected dream PPV stack is `MI_StorybookOutline_GameplayStandard` at `1.0` and `MI_MeluColorGrade_GameplayStandard` at `0.69` on `PPV_NikkiDream`.
- Capture PPV evidence only at the live viewport resolution until the buffer/view-rect issue is disproven.

## Before pressing Play (2 minutes outside the timed route)

1. Confirm the editor started after a successful closed-editor native build.
2. Open Output Log and clear it. Filter later for `Melodia`, `Quill`, `MELUSINA_LOOP`, `Error`, and `Warning`.
3. Confirm the intended GameMode for the starting map and that the correct local player/controller is active.
4. Confirm no prompt proposes saving `ZenForestTest`. Cancel if one appears.
5. Use a fresh save slot for the clean route. Keep a second slot for restart/idempotence checks.
6. Note input device and viewport resolution in the test record.

## Timed route

### 0:00–2:00 — Main menu and opening slideshow

1. Start from the native main-menu flow.
2. Navigate every visible action once with keyboard, then with gamepad if available.
3. Confirm focus is always visible, directional navigation is deterministic, and modal close restores the prior focus target.
4. Start New Game and view `/Game/Melodia/UI/WBP_MelodiaOpeningSlideshow`.
5. Advance one slide by clicking, one with Enter, and one with Space. Use Skip only on a second run.

**Expected**
- Cosmic Orrery presentation may animate rings, camera, materials, and Niagara, but confirm/travel still routes through the existing menu authority.
- Reduced-motion mode, if enabled, reduces ornamental motion without suppressing focus or input.
- Slideshow artwork fills 16:9; its lower third uses parchment noise, not the stretched SoftMG arch.
- Kicker, title, body, Advance, and Skip remain legible and inside the safe frame.
- Each input advances exactly once. No click plus key double-advance occurs.
- Keyboard/gamepad focus does not disappear behind artwork.

**Fail if**
- A destination unlock changes merely from highlighting it.
- `T_Melodia_SoftMG_Parchment` appears as a giant stretched arch in the lower third.
- A single action skips two slides, or the first input is ignored because focus is on a noninteractive root.
- Default Unreal fonts/buttons visibly replace the Melodia treatment.

### 2:00–5:00 — Melusina Morning and the grief hook

1. Enter `/Game/Melodia/Levels/Opening/L_MelusinaMorning` through normal opening flow.
2. Let the opening settle before interacting; note spawn location, facing, camera, and possession.
3. Trigger the Sir/Petal Priestess narrative path naturally.
4. Read without skipping on the first pass. Verify the emotional sequence: Melusina arrives too late/post-festival; the absent past duet is felt rather than explained away; Sir is alive and snack-seeking, preserving warmth against grief.
5. At the Petal Priestess tonal choice, inspect both options before choosing one.

**Expected**
- Interaction stencil appears only for the eligible NPC and clears after interaction, unpossession, and end play.
- Dialogue uses the project-owned Quill dialog adapter and retains Quill pacing.
- Speaker/body text updates for every line; no stale or blank labels.
- Enter, Space, click, and controller accept each work when used separately.
- Both Priestess choices are non-punitive and converge on exactly one authored intent: `melodia:stat:priestess_first_echo:melodia_harmony:1`.
- Quest `melodia_q_echo_01` is accepted once.
- UI reads `Harmony 1/5` after the choice; quest text remains clear.

**Fail if**
- The choice list is empty, valid options are disabled, or focus lands on a noninteractive row.
- Selecting one option emits the other option's `FStatement`.
- One click causes two Quill advances.
- Harmony remains 0, becomes 2, or changes again after reopening the same authored beat.
- Only one tonal choice grants Harmony, creating a softlock.

### 5:00–8:00 — Dreamstate traversal and presentation

1. Continue through normal flow into `/Game/Melodia/Levels/Opening/L_Melodia_Dreamstate`.
2. Walk, stop, turn the camera, jump/traverse where supported, and cross the opening transition boundary twice if it is reversible.
3. Observe foliage, silhouettes, hair, translucent effects, and UI against bright and dark backgrounds.
4. Trigger at least one background/narration change in Quill.

**Expected**
- Spawn context and possession are correct; no duplicate pawn appears.
- Movement input is restored after dialogue; cursor/input mode does not remain trapped.
- `PPV_NikkiDream` shows the foliage-safe outline without unstable edge shimmer and the active Melu grade at the intended strength.
- Background presentation appears even though the Quill plugin has an inverted viewport condition; the project adapter owns viewport insertion.
- Background changes emit one image change and do not obscure interaction UI.
- Existing hair presentation remains unchanged; this test is observation only.

**Fail if**
- Foliage becomes fully outlined noise, grade is doubled, or the scene differs radically after opening a menu.
- Dialogue closes but movement remains disabled.
- The background widget never appears, stacks duplicates, or steals focus from a choice.
- Traversal sends the player below the world or to an unintended map.

### 8:00–13:00 — Smoke encounter, JRPG UI, and Resonance

1. Enter `melodia_smoke_encounter` through the authored trigger.
2. Confirm the stock battle overlay is the instantiated authority; do not manually open stale `WBP_Battle_Rhythm`.
3. Exercise basic attack, skill, ultimate, back/cancel, and any available defend/flee commands using the displayed bindings.
4. Observe Melusina's body, hair, enemy readability, rhythm feedback, and camera framing during effects.
5. Complete the Resonance call-and-response beat without intentionally skipping prompts.
6. For the primary route, win the encounter.

**Expected**
- Exactly one battle session starts and one overlay is instantiated.
- Keyboard labels match actual controls; no null/default font appears in the legend.
- Disabled commands look disabled and cannot submit.
- UI sparkle/audio remains presentation-only and cannot submit a second command.
- Resonance prompts and response timing are readable over the PPV stack.
- The primary outcome is `victory`; reward flow includes `melodia_smoke_reward` and completion includes `melodia_smoke_complete`.
- Logs contain exactly one each of:
  - `MELUSINA_LOOP_BATTLE_COMPLETED`
  - `MELUSINA_LOOP_QUILL_RESTORE`
  - `MELUSINA_LOOP_QUILL_NEXT`

**Fail if**
- Battle input affects exploration simultaneously.
- Results appear twice, Quill resumes before results finish, or the encounter immediately retriggers.
- Any of the three loop markers is absent or occurs more than once.
- Presentation feedback changes health, rewards, save data, or travel state.

### 13:00–16:00 — Result, Quill resume, reward, and reunion

1. Dismiss the stock result screen once.
2. Allow Quill to restore and continue naturally.
3. Verify the reward/completion messaging and continue through the reunion ending.
4. Reopen the nearest eligible NPC interaction once if the route permits it.

**Expected**
- Results close once; control returns to Quill at the correct next statement.
- `melodia_smoke_reward` is granted once and `melodia_smoke_complete` is recorded once.
- Dialogue focus returns to the active Advance button; later selection focus goes to the first valid `ChoiceButton`.
- The emotional arc resolves as grief → call-and-response → reunion, without retconning the initial absence.
- Reopening dialogue does not replay stable intent rewards or duplicate quest acceptance.

**Fail if**
- Quill restarts the pre-battle paragraph, skips the post-battle paragraph, or waits forever.
- Rewards duplicate after reopening dialogue.
- Disabled choices become selectable by keyboard/controller.

### 16:00–18:00 — KaleidoNave arrival and world-building regression

1. Follow authored travel into `/Game/EnvSandbox/Environments/L_KaleidoNave`.
2. Record spawn marker, facing, camera, PPV transition, nearby collision, and interactable visibility.
3. Walk a short loop around the arrival area and return to the spawn marker.
4. Open and close the menu once; highlight an Orrery destination without confirming it.

**Expected**
- Arrival uses the intended spawn context and does not place the pawn at world origin.
- `marker_exit`/destination semantics remain registry-driven.
- No environment actor moves, disappears, or becomes dirty merely from PIE.
- Highlighting an Orrery destination may change presentation but cannot travel or mutate unlock/save state.
- Exiting the menu restores player input and prior focus cleanly.

**Fail if**
- World-building actors are unexpectedly replaced or the map becomes dirty from runtime-only presentation.
- Closing the menu leaves a cursor/input lock.
- Selecting without confirming travels.

### 18:00–20:00 — Save, restart, load, and idempotence

1. Save through the normal save UI in KaleidoNave.
2. Exit PIE cleanly. Do not save `ZenForestTest` if prompted.
3. Start a new PIE session and load the slot through the normal menu.
4. Verify arrival map/context, Harmony, quest state, reward state, and completed encounter.
5. If reachable within time, revisit the Priestess interaction or reload the post-choice checkpoint.

**Expected**
- Load returns to the intended map/spawn context, not a default map or origin.
- Harmony remains exactly `1/5` from `priestess_first_echo`.
- `melodia_q_echo_01` remains accepted/completed as authored.
- Quest 2 eligibility requires quest 1 plus `melodia_harmony >= 1`; the gate is data-driven.
- The smoke encounter remains complete and its reward does not re-grant.
- Replaying/restoring the Priestess event does not increment Harmony because `social-stat:priestess_first_echo` is stable and idempotent.

**Fail if**
- Harmony resets, doubles, or the same intent can be farmed.
- Quest 2 ignores Harmony or is permanently locked despite both prerequisites.
- The encounter retriggers as fresh after a successful save/load.
- Process restart differs from same-session load.

## Outcome matrix (follow-up passes)

Run these as short branch tests after the clean victory route. Use separate slots where possible.

| Outcome | Trigger | Required result | Quill/save invariant |
|---|---|---|---|
| `victory` | Defeat encounter normally | Results, reward, completion, resume | One completion/restore/next marker; reward once |
| `defeat` | Allow party defeat | Defeat result and authored recovery | No victory reward; Quill resumes only through defined defeat path |
| `fled` | Use flee when available | Flee result and return | No victory reward/completion unless explicitly authored; encounter remains coherent |
| `unavailable` | Enter when JRPG authority cannot start | Clear unavailable handling | No phantom battle completion, reward, or Quill skip |

For every branch, count `MELUSINA_LOOP_BATTLE_COMPLETED`, `MELUSINA_LOOP_QUILL_RESTORE`, and `MELUSINA_LOOP_QUILL_NEXT`. Each marker must match the authored branch exactly; no branch may emit duplicates.

## Focused Persona/Quill matrix

| Check | Procedure | Expected |
|---|---|---|
| Choice fidelity | Select each Priestess option on separate fresh slots | Exact selected original `FStatement`; same converged stat intent |
| Disabled choice | Reach a gated option below requirements | Visible but disabled; cannot click or keyboard-submit |
| Focus | Open selection using keyboard and gamepad | First valid `ChoiceButton` receives focus |
| Text lifecycle | Reopen selection after viewport creation | Every entry label is populated; no blank first frame |
| Advance debounce | Press Enter and click nearly together | One `OnAdvance` broadcast |
| Selection debounce | Double-click or press accept rapidly | One `OnSelected` broadcast |
| Stat idempotence | Restore/replay `priestess_first_echo` | Harmony remains 1 |
| Quest gate | Query quest 2 before/after prerequisites | Locked before; eligible only with quest 1 and Harmony ≥1 |

## PPV and visual evidence checklist

Capture one live-resolution screenshot in each condition:

1. Morning dialogue over a bright background.
2. Dreamstate foliage at medium distance.
3. Dreamstate hair/body silhouette during movement.
4. Battle UI during a bright Resonance effect.
5. KaleidoNave arrival after travel.
6. Slideshow lower third showing parchment noise and Baroque ornament.

Record whether outline weight is `1.0`, grade weight is `0.69`, viewport resolution, motion tier, and whether the menu was opened before capture. Do not reassign or edit Codex-owned PPV/material assets during this test.

## Known failures that should not block this slice

Current automation baseline is 49 tests with 46 passing and three known failures:

- `Melodia.NPC.InteractionDefaults`
- Two `Melodia.Roguelike.Functional.*` failures, including `TwentyFiveGenerationSoak`

Treat any additional failure as a regression. `WBP_Battle_Rhythm` also contains known stale references (`ToggleOrreryMenu`, deleted `BP_Melusina` cast); do not repair or use it as authority during this route without separate ownership tracing.

## Test record template

- Build/date:
- Map started:
- Input device(s):
- Viewport resolution:
- Motion tier:
- Save slot:
- Route completed in:
- Harmony after Priestess / after load:
- Quest 1 state / Quest 2 eligibility:
- Encounter outcome:
- Loop marker counts (completed/restore/next):
- PPV outline/grade weights observed:
- Screenshots/log attached:
- New regressions:
- Environment changes intentionally preserved:
- Confirmed `ZenForestTest` not saved by this pass: Yes / No
