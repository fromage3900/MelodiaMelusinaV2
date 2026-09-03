# JRPG template BPs — replace / keep for gameplay (2026-08-11)

Inventory for First Dream. **Stock JRPG stays mechanical authority**; Melodia wraps presentation and bridge. Do not wholesale-replace battle authority BPs.

## Keep and wire (do not replace wholesale)

| Stock path | Why |
|---|---|
| `/Game/TurnBasedJRPGTemplate/Blueprints/UI/BP_BattleUI` | Real `OnKeyDown` Q/W/O/P → `RegisterLaneHit`; runtime gate evidence path |
| `/Game/TurnBasedJRPGTemplate/Blueprints/Battle/BP_BattleController` | Constructs BattleUI; skill/rhythm/complete battle authority |
| `/Game/TurnBasedJRPGTemplate/Blueprints/Battle/BP_BattleBase` | `playerUnits` / battle instance |
| `/Game/TurnBasedJRPGTemplate/Blueprints/Battle/BP_InteractionBattle` (+ OneTime) | Tagged encounter `StartBattle` / `OnBattleOver` |
| `/Game/TurnBasedJRPGTemplate/Blueprints/Controllers/BP_JRPGSaveGame` | Canonical slot + `melodiaNarrativeRecord` |
| `/Game/TurnBasedJRPGTemplate/Blueprints/Skills/*` | Stock skill execution; **never Python-load** (`D_DamageType` fatal) |

Tracked in this V2 checkout today: only `BP_BattleController` + `BP_BattleUI` under TurnBasedJRPGTemplate Blueprints (other stock BPs may still be LFS-sparse on cloud — pull `Content/TurnBasedJRPGTemplate/**` on workstation).

## Melodia-owned (already the slice face)

| Path | Role |
|---|---|
| `…/MelodiaIntegration/Blueprints/BP_MelodiaJRPGGameInstance` | GI / save bootstrap |
| `…/MelodiaIntegration/Blueprints/BP_MelodiaJRPGGameMode` | Slice GameMode |
| `…/MelodiaIntegration/Blueprints/BP_MelodiaJRPGPlayerController` | Exploration PC |
| `…/MelodiaIntegration/UI/BP_MelodiaBattleUI` | Overlay / `ShowRhythmGrade` |
| `…/MelodiaIntegration/UI/BP_MelodiaActionsUI` (+ ActionButton, TurnOrder) | Styled command UI — must stay type-compatible with stock casts |
| `…/MelodiaIntegration/Party/Skills/BP_SirSkyboundRefrain` + `BP_Resonance` | Co-op |
| `…/Experiments/MelodiaJRPG/Skills/BP_MelusinaPetalCadence` | Co-op |

## Priority if something “feels wrong” in play

1. **Stock `BP_BattleUI`** — input/highway (runtime gate)
2. **Stock `BP_BattleController`** — constructs UI + skills
3. **`BP_MelodiaBattleUI`** — Melodia overlay (avoid mirror copy)
4. **`BP_MelodiaJRPGGameMode` / PlayerController / GameInstance** — entry config
5. **`BP_MelodiaActionsUI`** — command menu compatibility
6. **SaveGame + InteractionBattle** — save / encounter seams
7. **Sir / Melusina skill BPs** — co-op mapping via `StockSkillRhythmIds`

## Dangerous doubles — do not use as replace sources

- `Content/MelodiaIntegration/Content_MelodiaIntegration/**` (33 tracked mirror; shadowed-event risk)
- `Content/_ThirdParty/TurnBasedJRPGTemplate/**` (not pristine; copy node clusters only)

See `Docs/Reports/DUPLICATE_TREE_INVENTORY_2026-08-11.md`.
