"""Build the stock-to-Melodia UI migration ledger without loading maps or assets."""
from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
STOCK_ROOT = ROOT / "Content" / "TurnBasedJRPGTemplate" / "Blueprints" / "UI"
DUPLICATE_ROOT = ROOT / "Content" / "_ThirdParty" / "TurnBasedJRPGTemplate" / "Blueprints" / "UI"
OUTPUT = ROOT / "Saved" / "Audit" / "UI" / "stock_ui_migration_ledger.json"

MAPPING = {
    "BP_ActionButton": ("/Game/MelodiaIntegration/UI/BP_MelodiaActionButton", "wrap"),
    "BP_ActionsUI": ("/Game/MelodiaIntegration/UI/BP_MelodiaActionsUI", "wrap"),
    "BP_BattleUI": ("/Game/MelodiaIntegration/UI/BP_MelodiaBattleUI", "wrap"),
    "BP_TurnOrderList": ("/Game/MelodiaIntegration/UI/BP_MelodiaTurnOrderList", "wrap"),
    "BP_TurnOrderUI": ("/Game/MelodiaIntegration/UI/BP_MelodiaTurnOrderList", "wrap"),
    "BP_MainMenu": ("/Game/Melodia/UI/WBP_MainMenu", "replace"),
    "BP_MenuButton": ("/Game/Melodia/UI/WBP_MenuButton", "replace"),
    "BP_SaveUI": ("/Game/Melodia/UI/WBP_SaveLoad", "replace"),
    "BP_PauseMenu": ("/Game/Melodia/UI/WBP_ComicOrrery", "replace"),
    "BP_QuestDetails": ("/Game/Melodia/UI/WBP_QuestJournal", "replace"),
    "BP_SkillDetails": ("/Game/Melodia/UI/WBP_SkillCodex", "replace"),
    "BP_VictoryDialogue": ("/Game/Melodia/UI/WBP_Battle_Results", "replace"),
    "BP_DefeatDialogue": ("/Game/Melodia/UI/WBP_Battle_Results", "replace_lifecycle"),
    "BP_MobileUI": ("/Game/Melodia/UI/WBP_Battle_Mobile", "replace"),
}

BATTLE = {
    "BP_ActionButton", "BP_ActionsUI", "BP_ActionTimeBar", "BP_BattleUI", "BP_BossUI",
    "BP_DamageTextUI", "BP_EnemyUnitUI", "BP_HPBar", "BP_MPBar", "BP_PlayerUnitListUI",
    "BP_PlayerUnitUI", "BP_TargetIcon", "BP_TurnOrderList", "BP_TurnOrderUI",
    "BP_UnitBattleDetails", "BP_UnitClass", "BP_MobileUI",
}
SHOP = {
    "BP_BuyItemAmountDialogue", "BP_CraftDetails", "BP_CraftItemButton", "BP_CraftItemRecipe",
    "BP_EquipmentButton", "BP_EquipmentStatComparison", "BP_ItemButton",
    "BP_SellItemAmountDialogue", "BP_ShopBuyDialogue", "BP_ShopBuyItemButton",
    "BP_ShopSellDialogue", "BP_CraftBar",
}
MENU = {
    "BP_EquipmentComparisonUI", "BP_EquipmentDetails", "BP_ItemDetails", "BP_MainMenu",
    "BP_MenuButton", "BP_PartyUI", "BP_PauseMenu", "BP_QuestDetails", "BP_SaveButton",
    "BP_SaveUI", "BP_SkillDetails", "BP_UnitButton", "BP_UnitButtonList", "BP_UnitDetails",
    "BP_UnitDetailsSummary", "BP_UnitDetailsSummaryList", "BP_UnitPartyDetails",
    "BP_WearEquipmentUI",
}
LIFECYCLE = {"BP_DefeatDialogue", "BP_VictoryDialogue", "BP_FadeTransitionUI"}

MIGRATION_STATUS_OVERRIDES = {
    "BP_ActionButton": {
        "status": "presentation_rethemed_in_place",
        "compile_status": "up_to_date_0_errors_0_warnings",
        "runtime_redirected": True,
        "editor_validated": True,
        "validation_evidence": "Melodia brush, skill-ring icon, typography, and text color confirmed by live dump_ui_spec readback.",
    },
    "BP_ActionsUI": {
        "status": "presentation_rethemed_in_place",
        "compile_status": "up_to_date_0_errors_0_warnings",
        "runtime_redirected": True,
        "editor_validated": True,
        "validation_evidence": "Four stock action-button slots match BP_MelodiaActionsUI and were confirmed by live dump_ui_spec readback.",
    },
    "BP_TurnOrderList": {
        "status": "presentation_rethemed_in_place",
        "compile_status": "up_to_date_0_errors_0_warnings",
        "runtime_redirected": True,
        "editor_validated": True,
        "validation_evidence": "Melodia parchment, heading typography/color, and hidden legacy trim confirmed by live dump_ui_spec readback.",
    },
    "BP_BattleUI": {
        "status": "presentation_rethemed_in_place",
        "compile_status": "up_to_date_0_errors_0_warnings",
        "runtime_redirected": True,
        "editor_validated": True,
        "validation_evidence": "Stock shell retained all 17 contract widgets and now includes the centered, collapsed BP_MelodiaRhythmPrompt child; live readback reports 18 widgets.",
    },
}


# Verified from live-editor T3D Blueprint exports. Keep these overrides in the
# generator so rebuilding the ledger cannot regress known runtime contracts.
RUNTIME_OVERRIDES = {
    "BP_ExploreUI": {
        "runtime_owner": "/Game/TurnBasedJRPGTemplate/Blueprints/Controllers/BP_JRPGPlayerController",
        "contract": (
            "Controller creates and retains exploreUI; the widget receives exploration crafting "
            "progress and quest-notification calls. Preserve those public presentation calls when "
            "redirecting them into the persistent Melodia HUD host."
        ),
        "owner_evidence": "BP_JRPGPlayerController EventGraph K2Node_CreateWidget_3 and exploreUI variable",
        "owner_verified": True,
    },
    "BP_PauseMenu": {
        "runtime_owner": "/Game/TurnBasedJRPGTemplate/Blueprints/Controllers/BP_JRPGPlayerController",
        "contract": (
            "Controller creates the pause widget for the menu flow, passes controller/battle context, "
            "and binds OnPauseMenuClosed. Orrery replacement must preserve close notification, input "
            "mode restoration, and battle/exploration context."
        ),
        "owner_evidence": "BP_JRPGPlayerController EventGraph K2Node_CreateWidget_4 and OnPauseMenuClosed delegate binding",
        "owner_verified": True,
    },
    "BP_DefeatDialogue": {
        "runtime_owner": "/Game/TurnBasedJRPGTemplate/Blueprints/Battle/BP_BattleController",
        "contract": (
            "Battle controller creates the defeat dialogue after stock defeat resolution and supplies "
            "mainMenuMapName and defeatTheme. Replace it with a presentation-only retry surface: allow "
            "up to three failed retries, expose Give Up earlier, then recover Melusina at the most recent "
            "sanctuary or validated nearby safe place. Never add corpse-run or resource-loss semantics."
        ),
        "owner_evidence": "BP_BattleController EventGraph CreateWidget class pin for BP_DefeatDialogue",
        "owner_verified": True,
    },
    "BP_ShopBuyDialogue": {
        "runtime_owner": "/Game/TurnBasedJRPGTemplate/Blueprints/Interactables/BP_ShopBase",
        "contract": (
            "Shop actor creates the buy dialogue, passes the player controller and usable item classes, "
            "adds it to the viewport, and binds OnShopUIClosed. Preserve stock item/price/transaction "
            "authority; replace only presentation and label the canonical balance as Resonance."
        ),
        "owner_evidence": "BP_ShopBase EventGraph K2Node_CreateWidget_0, AddToViewport, and OnShopUIClosed binding",
        "owner_verified": True,
    },
    "BP_BattleUI": {
        "runtime_owner": "/Game/TurnBasedJRPGTemplate/Blueprints/Battle/BP_BattleController",
        "contract": (
            "Battle controller creates the stock battle shell. Melodia must wrap its presentation and "
            "retain stock target selection, action availability, turn order, resource, and combat delegates."
        ),
        "owner_evidence": "Project node index: BP_BattleController Create BP Battle UI Widget",
        "owner_verified": True,
    },
    "BP_VictoryDialogue": {
        "runtime_owner": "/Game/TurnBasedJRPGTemplate/Blueprints/Battle/BP_BattleController",
        "contract": (
            "Battle controller creates victory presentation after stock reward/result resolution. The "
            "Melodia result screen must consume completed results without changing rewards or battle exit."
        ),
        "owner_evidence": "Project node index: BP_BattleController Create BP Victory Dialogue Widget",
        "owner_verified": True,
    },
    "BP_PartyUI": {
        "runtime_owner": "/Game/TurnBasedJRPGTemplate/Blueprints/UI/MainMenu/BP_PauseMenu",
        "contract": (
            "Pause menu creates the party surface. Move its presentation into the Orrery while retaining "
            "the stock party/equipment data and mutation calls and the parent menu close/back contract."
        ),
        "owner_evidence": "Project node index: BP_PauseMenu Create BP Party UI Widget",
        "owner_verified": True,
    },
    "BP_SaveUI": {
        "runtime_owner": "BP_SavePointBase | BP_MainMenu | BP_PauseMenu",
        "contract": (
            "Save UI has three verified entry owners: authored save points, main menu, and pause menu. "
            "The Melodia save/load surface must preserve all three entry contexts and canonical stock save calls."
        ),
        "owner_evidence": "Project node index: Create BP Save UI Widget in BP_SavePointBase, BP_MainMenu, and BP_PauseMenu",
        "owner_verified": True,
    },
}


def ue_path(path: Path, root: Path) -> str:
    return "/Game/" + path.relative_to(root / "Content").with_suffix("").as_posix()


def classify(name: str, relative_parent: str) -> str:
    if name in LIFECYCLE:
        return "lifecycle"
    if name in BATTLE:
        return "battle"
    if name in SHOP:
        return "shop_economy"
    if name in MENU or relative_parent == "MainMenu":
        return "orrery_menu"
    if name in {"BP_ExploreUI", "BP_InteractionUI", "BP_QuestNotification", "BP_QuestNotificationListUI"}:
        return "global_hud"
    if relative_parent == "Dialogues":
        return "dialogue_modal"
    return "shared"


def default_strategy(category: str) -> str:
    return {
        "battle": "wrap_stock_authority",
        "shop_economy": "replace_presentation_preserve_transaction_authority",
        "lifecycle": "replace_after_recovery_authority_exists",
        "global_hud": "replace_with_persistent_host",
        "orrery_menu": "replace_with_orrery_surface",
        "dialogue_modal": "replace_with_shared_melodia_modal",
        "shared": "replace_with_foundation_component",
    }[category]


def main() -> int:
    rows = []
    for path in sorted(STOCK_ROOT.rglob("*.uasset")):
        name = path.stem
        parent = path.parent.name if path.parent != STOCK_ROOT else ""
        category = classify(name, parent)
        replacement, explicit_strategy = MAPPING.get(name, (None, None))
        duplicate = DUPLICATE_ROOT / path.relative_to(STOCK_ROOT)
        runtime = RUNTIME_OVERRIDES.get(name, {})
        migration = MIGRATION_STATUS_OVERRIDES.get(name, {})
        rows.append({
            "stock_asset": ue_path(path, ROOT),
            "duplicate_asset": ue_path(duplicate, ROOT) if duplicate.is_file() else None,
            "name": name,
            "category": category,
            "runtime_owner": runtime.get("runtime_owner", "unverified"),
            "contract": runtime.get("contract", "inspect_in_editor"),
            "owner_evidence": runtime.get("owner_evidence"),
            "owner_verified": runtime.get("owner_verified", False),
            "melodia_replacement": replacement,
            "strategy": explicit_strategy or default_strategy(category),
            "status": migration.get("status", "candidate_exists" if replacement else "inventory_only"),
            "compile_status": migration.get("compile_status", "unverified"),
            "runtime_redirected": migration.get("runtime_redirected", False),
            "editor_validated": migration.get("editor_validated", False),
            "validation_evidence": migration.get("validation_evidence"),
            "validated": migration.get("validated", False),
            "quarantined": False,
        })

    report = {
        "generated_utc": datetime.now(timezone.utc).isoformat(),
        "policy": {
            "preserve_stock_combat_authority": True,
            "no_map_loading": True,
            "protected_content_accessed": False,
            "currency_name": "Resonance",
            "first_rhythm_skill": "Cadence Strike",
            "death_policy": (
                "Offer Retry after defeat for up to 3 failed attempts, with Give Up available earlier; "
                "after the third failed retry or Give Up, recover as Melusina at the most recent "
                "authored sanctuary or a validated nearby safe place. Do not use Dark Souls-style loss or corpse runs."
            ),
            "death_retry_limit": 3,
            "death_give_up_available": True,
            "global_hud": ["Orrery menu affordance", "Minimap", "Context prompts"],
        },
        "stock_root": "/Game/TurnBasedJRPGTemplate/Blueprints/UI",
        "duplicate_root": "/Game/_ThirdParty/TurnBasedJRPGTemplate/Blueprints/UI",
        "asset_count": len(rows),
        "duplicate_count": sum(row["duplicate_asset"] is not None for row in rows),
        "assets": rows,
    }
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({
        "output": str(OUTPUT),
        "asset_count": report["asset_count"],
        "duplicate_count": report["duplicate_count"],
    }, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
