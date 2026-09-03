# Melodia Battle UI Integration - 2026-07-11

## Intent

Make the existing `WBP_Battle_Rhythm` the presentation layer for the proven
native rhythm HUD. Keep `UMelodiaRhythmHUDWidget` authoritative for combat
state and note timing. The Blueprint should interpret those events visually;
it must not recalculate damage, SP, grades, or break state.

## Existing Assets

| Asset | Role | Decision |
| --- | --- | --- |
| `/Game/Melodia/UI/WBP_Battle_Rhythm` | Native HUD child | Use as the only runtime battle HUD class. |
| `/Game/Melodia/UI/WBP_GradePop` | Grade presentation atom | Use for Perfect, Great, Good, and Miss variants. |
| `/Game/Melodia/_PROJECT/Blueprints/Gameplay/BP_RhythmHUD` | Earlier authored HUD asset | Inspect for reusable styling only; do not spawn alongside the native HUD. |
| `/Game/Alphas_Sparkles/T_Spark_Twinkle8` | Sparkle texture | Candidate for Perfect and Break accents. |
| `NS_SakuraDreamSparkle`, `NS_MagicalHenshinBurst` | World VFX | Optional encounter/world accents, not UMG dependencies. |

## Runtime Wiring

After the current C++ pass builds successfully, perform these editor steps in
`BP_MelodiaGameMode`:

1. Set `HUDWidgetClass` to `WBP_Battle_Rhythm`.
2. Do not create a second `BP_RhythmHUD` at BeginPlay.
3. Confirm one widget is added to the viewport when `ZenForestTest` starts.
4. In PIE, verify the native fallback disappears only after the Blueprint child
   renders the equivalent event-driven UI.

## Widget Hierarchy

Use a single full-screen `Canvas Panel` and a small number of purpose-built
layers:

1. **Enemy state, top center:** name, HP, toughness/break bar, intent label.
2. **Rhythm layer, lower center:** four fixed-width lanes and the hit line.
3. **Player state, bottom left:** Melusina HP, SP pips, Ultimate/Crescendo.
4. **Command strip, bottom right:** Basic, selected Skill with cost, Ultimate,
   Flee. The selected Skill must agree with `ShowActionPrompt`.
5. **Result layer, center:** `WBP_GradePop`, damage text, `BREAK!`, victory.

Keep the gameplay view visible. Avoid opaque full-width panels, duplicated
bars, and persistent decorative frames that compete with the rhythm lanes.

## Blueprint Event Map

| Native event | Blueprint behavior |
| --- | --- |
| `SetHUDMode` | Fade battle-only layers in/out; exploration stays minimal. |
| `ShowActionPrompt` | Update command strip text, selected Skill name, and SP cost. |
| `SetNoteHighwayActive` | Show/hide lanes; drive only visual note widgets. |
| `SetJudgment` | Set `WBP_GradePop` variant. |
| `DoPulse` | Brief hit-line scale/brightness pulse. |
| `TriggerSparkleBurst` | Play the shared Perfect/Break accent. |
| `SetEnemyVitals`, `SetEnemyBreakGauge` | Animate top-center bars toward native values. |
| `SetPartyVitals`, `SetSkillPoints`, `SetUltimateGauge` | Animate player resources; do not predict values. |
| `SetBattlePhaseBanner` | Short phase card: Rhythm, Enemy Turn, Break, Victory, Defeat. |
| `PushFloatingCombatText` | Spawn pooled grade/damage/break text. |
| `TriggerDamageFlash` | Brief enemy-facing red flash, not a full-screen flash. |
| `ShowBattleStatus` | Reserved for concise one-line status changes. |

## Acceptance Pass

1. Run `python Content/Python/verify_melodia_ui_contract.py` before opening
   the editor; it must report `ok=true`.
2. Build `BS_GodFileEditor` and run `Melodia.CoreRules` with the current C++
   feedback patch.
3. In `ZenForestTest`, start one encounter and verify only one battle HUD.
4. Cycle Skill: name and cost update immediately.
5. Perform a Perfect: grade, pulse, and sparkle read as one event.
6. Cause Break: banner, bar state, and result text agree.
7. Win: the result layer clears and exploration input returns.

## Scope Boundary

This pass is desktop-first. It does not create `WBP_Battle_Mobile`, add touch
controls, or make mobile rendering claims. It also does not require bespoke
enemy UI art or a second combat framework.
