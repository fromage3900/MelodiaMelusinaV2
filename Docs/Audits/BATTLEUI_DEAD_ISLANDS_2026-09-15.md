# BattleUI dead-island cut 2026-09-15

BEHAVIOR-FINDINGS (recorded before debris cut 2026-09-15): 1) Show Boss UI chain (PlayAnim ShowPlayerUnitListUIAnim/TargetImageAnim -> Show Boss UI) has no entry: boss bar likely never shows. 2) Set Player Unit UIList (battleController/playerUnits/currentBattle reads) has no entry: party list likely never refreshes. Chains removed as inert; see ROLLBACK_BP_BattleUI_2026-09-15.json for full wiring.

Removed nodes:
- K2Node_CallFunction_0 | K2Node_CallFunction | Set Player Unit UIList
- K2Node_CallFunction_1 | K2Node_CallFunction | Play Animation
- K2Node_CallFunction_18 | K2Node_CallFunction | Create Widget
- K2Node_CallFunction_2 | K2Node_CallFunction | Play Animation
- K2Node_CallFunction_21 | K2Node_CallFunction | Add to Viewport
- K2Node_CallFunction_25 | K2Node_CallFunction | Play Animation
- K2Node_CallFunction_28 | K2Node_CallFunction | Show Boss UI
- K2Node_CallFunction_3 | K2Node_CallFunction | Delay
- K2Node_CallFunction_39 | K2Node_CallFunction | Set Visibility
- K2Node_CallFunction_4 | K2Node_CallFunction | Remove from Parent
- K2Node_CallFunction_40 | K2Node_CallFunction | Create Widget
- K2Node_CallFunction_46 | K2Node_CallFunction | Add to Viewport
- K2Node_CallFunction_47 | K2Node_CallFunction | Set Visibility
- K2Node_CallFunction_56 | K2Node_CallFunction | Play Animation
- K2Node_CallFunction_58 | K2Node_CallFunction | Create Widget
- K2Node_CallFunction_59 | K2Node_CallFunction | Add to Viewport
- K2Node_CallFunction_60 | K2Node_CallFunction | Set Visibility
- K2Node_VariableGet_0 | K2Node_VariableGet | Get BP_PlayerUnitListUI
- K2Node_VariableGet_16 | K2Node_VariableGet | Get battleController
- K2Node_VariableGet_2 | K2Node_VariableGet | Get playerUnits
- K2Node_VariableGet_26 | K2Node_VariableGet | Get TargetImageAnim
- K2Node_VariableGet_3 | K2Node_VariableGet | Get ShowPlayerUnitListUIAnim
- K2Node_VariableGet_4 | K2Node_VariableGet | Get ShowPlayerUnitListUIAnim
- K2Node_VariableGet_46 | K2Node_VariableGet | Get ShowTurnOrderUI
- K2Node_VariableGet_7 | K2Node_VariableGet | Get currentBattle

## Panel audit 2026-09-15 (battle set)

- bp_sweep(Battle): 26 empty (default stubs, cosmetic, kept), 17 dead in BP_BattleUI (cut above, verified 158/157 compile-clean), 0 shadowed. DUPES: BP_MelodySlimeBattle + _Hub mirrored under /Game/_PROJECT/ vs /Game/Melodia/_PROJECT/; bp_live_path: 3 ORPHAN + 1 hub referenced-once-but-unreachable. No deletions (ORPHAN rule: TSoftObjectPtr/umap refs invisible) - owner call.
- ui_style_audit: raw #FFFFFF/#000000 across all panels (off-palette bar); Default 18pt on BossUI(1x)/UnitBattleDetails(7x); near-miss #050409 -> #000000 @a0.8 (2x BossUI + 8x UnitBattleDetails) NOT unified: batch_style targets whole classes, per-widget fix needs owner eyes. WBP_Battle_Rhythm already carries gold/ivory/slate tokens.
- Behavior findings (open): Show Boss UI + Set Player Unit UIList chains had no entries - boss bar and party-list refresh may never fire. Rewiring is new behavior, needs design + PIE, not done here.
