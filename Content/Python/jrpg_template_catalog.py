"""TurnBasedJRPGTemplate catalog — third-party asset map for Melodia bridge.

Content path: Content/_ThirdParty/TurnBasedJRPGTemplate/ (~330 uassets)
UE path:      /Game/_ThirdParty/TurnBasedJRPGTemplate/

Run audit (no editor):
  python Content/Python/audit_jrpg_template.py
"""
from __future__ import annotations

from dataclasses import dataclass

from paths import JRPG_TEMPLATE, MELODIA, THIRD_PARTY

# Melodia bridge targets (created by scaffold_melodia_jrpg_rhythm_bridge.py)
MELODIA_BRIDGE = f"{MELODIA}/Bridge/JRPG"
MELODIA_BATTLE = f"{MELODIA}/Blueprints/Battle"
MELODIA_DATA = f"/Game/Data/Melodia"
MELODIA_UI = f"{MELODIA}/UI"
MELODIA_LEVELS = f"{MELODIA}/Levels"

# Template roots
TPL = JRPG_TEMPLATE
TPL_BP = f"{TPL}/Blueprints"
TPL_BATTLE = f"{TPL_BP}/Battle"
TPL_UI = f"{TPL_BP}/UI"
TPL_SKILLS = f"{TPL_BP}/Skills"
TPL_ITEMS = f"{TPL_BP}/Items"
TPL_UNITS = f"{TPL_BP}/Units"
TPL_QUESTS = f"{TPL_BP}/Quests"
TPL_STRUCTS = f"{TPL_BP}/Structs"
TPL_ENUMS = f"{TPL_BP}/Enums"
TPL_CONTROLLERS = f"{TPL_BP}/Controllers"


@dataclass(frozen=True)
class TemplateAsset:
    name: str
    ue_path: str
    category: str
    melodia_role: str


# --- Battle (15) ---
BATTLE_ASSETS: tuple[TemplateAsset, ...] = (
    TemplateAsset("BP_BattleController", f"{TPL_BATTLE}/BP_BattleController", "battle", "Turn queue + AV — bridge to MelodiaBattleSession"),
    TemplateAsset("BP_BattleBase", f"{TPL_BATTLE}/BP_BattleBase", "battle", "Arena parent — host rhythm phase overlay"),
    TemplateAsset("BP_BattleUI", f"{TPL_UI}/BP_BattleUI", "ui", "Shell for WBP_Battle_Rhythm embed"),
    TemplateAsset("BP_TurnOrderUI", f"{TPL_UI}/BP_TurnOrderUI", "ui", "HSR turn bar — keep alongside rhythm HUD"),
    TemplateAsset("BP_TurnOrderList", f"{TPL_UI}/BP_TurnOrderList", "ui", "Unit portraits in turn order"),
    TemplateAsset("BP_ActionsUI", f"{TPL_UI}/BP_ActionsUI", "ui", "Command menu — Skill triggers rhythm phase"),
    TemplateAsset("BP_ActionButton", f"{TPL_UI}/BP_ActionButton", "ui", "Attack/Skill/Item/Flee buttons"),
    TemplateAsset("BP_PlayerUnitUI", f"{TPL_UI}/BP_PlayerUnitUI", "ui", "Party vitals — map to SP/ULT meters"),
    TemplateAsset("BP_EnemyUnitUI", f"{TPL_UI}/BP_EnemyUnitUI", "ui", "Enemy telegraph + toughness bar"),
    TemplateAsset("BP_HPBar", f"{TPL_UI}/BP_HPBar", "ui", "Reusable HP widget"),
    TemplateAsset("BP_MPBar", f"{TPL_UI}/BP_MPBar", "ui", "MP bar — parallel to Melodia SP"),
    TemplateAsset("BP_DamageText", f"{TPL_BATTLE}/BP_DamageText", "battle", "Floating damage — grade-colored pops"),
    TemplateAsset("BP_OneTimeBattle", f"{TPL_BATTLE}/BP_OneTimeBattle", "battle", "Encounter volume pattern"),
    TemplateAsset("BP_InteractionBattle", f"{TPL_BATTLE}/BP_InteractionBattle", "battle", "Interact-to-fight hook"),
    TemplateAsset("E_BattleResult", f"{TPL_BATTLE}/E_BattleResult", "enum", "Victory/Defeat/Fled — maps to MelodiaEncounterResult"),
)

# --- Data structures (template structs/enums) ---
STRUCT_ASSETS: tuple[TemplateAsset, ...] = (
    TemplateAsset("S_UnitStats", f"{TPL_STRUCTS}/S_UnitStats", "struct",
                  "maxHP, maxMP, minAttack, maxAttack, defense, speed, hit, magical stats, actionTime"),
    TemplateAsset("S_PlayerUnitData", f"{TPL_STRUCTS}/S_PlayerUnitData", "struct",
                  "Exp, currentHP, currentMP, equipment slots"),
    TemplateAsset("S_OffLevelBattleData", f"{TPL_STRUCTS}/S_OffLevelBattleData", "struct", "Overworld encounter payload"),
    TemplateAsset("S_QuestRewards", f"{TPL_STRUCTS}/S_QuestRewards", "struct", "XP/gold/item rewards"),
    TemplateAsset("E_EquipmentType", f"{TPL_ENUMS}/E_EquipmentType", "enum", "Weapon/Armor/Shield/Helm/Boots"),
    TemplateAsset("E_ActionType", f"{TPL_ENUMS}/E_ActionType", "enum", "Attack/Skill/Item/Flee/None/Interact"),
    TemplateAsset("E_UnitClass", f"{TPL_ENUMS}/E_UnitClass", "enum", "Class lanes for Melodist party"),
    TemplateAsset("E_TurnType", f"{TPL_ENUMS}/E_TurnType", "enum", "Player/Enemy turn discriminator"),
    TemplateAsset("E_GameState", f"{TPL_ENUMS}/E_GameState", "enum", "Explore/Battle/Menu state machine"),
    TemplateAsset("E_QuestStatus", f"{TPL_ENUMS}/E_QuestStatus", "enum", "Quest progression"),
)

# --- MelodiaCore C++ bridge targets ---
MELODIA_CPP_BRIDGE: tuple[TemplateAsset, ...] = (
    TemplateAsset("MelodiaGameMode", "/Script/MelodiaCore.MelodiaGameMode", "cpp", "Loop phases: Exploration/Battle/Victory"),
    TemplateAsset("MelodiaBattleSession", "/Script/MelodiaCore.MelodiaBattleSession", "cpp", "Rhythm phase machine"),
    TemplateAsset("MelodiaRhythmHUDWidget", "/Script/MelodiaCore.MelodiaRhythmHUDWidget", "cpp", "NativePaint highway"),
    TemplateAsset("MelodiaRhythmExecutionComponent", "/Script/MelodiaCore.MelodiaRhythmExecutionComponent", "cpp", "Judgment + combo"),
    TemplateAsset("MelodiaEncounterTrigger", "/Script/MelodiaCore.MelodiaEncounterTrigger", "cpp", "Overlap → battle"),
)

# --- Bridge blueprints to scaffold ---
BRIDGE_SCAFFOLD: tuple[tuple[str, str, str], ...] = (
    ("BP_Melodia_JRPG_Bridge", f"{MELODIA_BRIDGE}/BP_Melodia_JRPG_Bridge", "Parent: BP_BattleController — rhythm phase delegate"),
    ("BP_Melodia_RhythmBattle", f"{MELODIA_BATTLE}/BP_Melodia_RhythmBattle", "Parent: BP_BattleBase — MelodiaGameMode ref"),
    ("BP_Melodia_QuestHook", f"{MELODIA}/Core/BP_QuestManager", "Quest manager stub — template quest BP child"),
    ("WBP_Melodia_BattleShell", f"{MELODIA_UI}/WBP_Melodia_BattleShell", "Hosts template BP_BattleUI + WBP_Battle_Rhythm"),
    ("WBP_Melodia_CommandMenu", f"{MELODIA_UI}/WBP_Melodia_CommandMenu", "P5-style commands → rhythm execution"),
    ("DT_MelodiaEnemies", f"{MELODIA_DATA}/DT_MelodiaEnemies", "Enemy stats from gmm/game/data_registry"),
    ("DT_MelodiaSkills", f"{MELODIA_DATA}/DT_MelodiaSkills", "Song skills with note charts"),
    ("DT_MelodiaPlayer", f"{MELODIA_DATA}/DT_MelodiaPlayer", "Player unit defaults"),
    ("L_Melodia_RhythmSlice", f"{MELODIA_LEVELS}/L_Melodia_RhythmSlice", "Vertical slice: encounter + rhythm + reward"),
)

# Assets explicitly NOT bridged in v1
EXCLUDED_BRIDGE = (
    {"name": "Full template inventory UI (58 widgets)", "reason": "Reskin subset only — BP_BattleUI shell + turn order"},
    {"name": "Template save game UI", "reason": "Melodia uses gmm/game/player_state JSON until C++ save wired"},
    {"name": "Crafting UI", "reason": "Post-MVP — Songcraft phase 5+"},
)


def all_template_assets() -> list[TemplateAsset]:
    return list(BATTLE_ASSETS) + list(STRUCT_ASSETS)


def as_catalog_dict() -> dict:
    def _row(a: TemplateAsset) -> dict:
        return {
            "name": a.name,
            "ue_path": a.ue_path,
            "category": a.category,
            "melodia_role": a.melodia_role,
        }

    return {
        "template_root": TPL,
        "third_party_root": THIRD_PARTY,
        "disk_root": "Content/_ThirdParty/TurnBasedJRPGTemplate",
        "asset_counts": {
            "animations": 25,
            "blueprints": 156,
            "materials": 31,
            "meshes": 3,
            "particles": 3,
            "sounds": 18,
            "textures": 94,
            "total_uassets": 330,
            "ui_widgets": 58,
        },
        "battle": [_row(a) for a in BATTLE_ASSETS],
        "data_model": [_row(a) for a in STRUCT_ASSETS],
        "melodia_cpp": [_row(a) for a in MELODIA_CPP_BRIDGE],
        "bridge_scaffold": [
            {"name": n, "ue_path": p, "notes": notes} for n, p, notes in BRIDGE_SCAFFOLD
        ],
        "excluded": list(EXCLUDED_BRIDGE),
        "python_runtime": [
            "gmm/game/data_registry.py",
            "gmm/game/player_state.py",
            "gmm/game/rhythm_clock.py",
            "gmm/game/battle_manager.py",
            "gmm/game/jrpg_bridge.py",
        ],
        "docs": [
            "Docs/DEEPSEEK_RHYTHM_GAMEPLAY_HANDOFF.md",
            "Docs/MELODIA_MELUSINA_GAME_UX.md",
            "Docs/MELODIA_JRPG_RHYTHM_SCAFFOLD.md",
            "Docs/WBP_BATTLE_RHYTHM_SETUP.md",
        ],
    }
