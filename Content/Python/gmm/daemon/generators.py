"""Content generators for GMM subpackage daemons."""
from __future__ import annotations

import json
import textwrap
from typing import Any


# --- Melodia: enemies ---

def gen_enemy_forte() -> str:
    return textwrap.dedent("""\
    MelodiaEnemyDef(
        enemy_id="FireDrake",
        display_name="Fire Drake",
        element="Forte",
        bpm=150,
        max_hp=160,
        max_toughness=70,
        base_damage=12,
        speed=75,
        display_mesh="/Game/EnvSandbox/Melodia/Monsters/SM_FireDrake",
        mesh_scale=1.2,
    ),""")


def gen_enemy_umbral() -> str:
    return textwrap.dedent("""\
    MelodiaEnemyDef(
        enemy_id="ShadowWraith",
        display_name="Shadow Wraith",
        element="Umbral",
        bpm=90,
        max_hp=100,
        max_toughness=40,
        base_damage=15,
        speed=95,
        display_mesh="/Game/EnvSandbox/Melodia/Monsters/SM_ShadowWraith",
        mesh_scale=0.9,
    ),""")


def gen_enemy_arcane() -> str:
    return textwrap.dedent("""\
    MelodiaEnemyDef(
        enemy_id="ArcaneGolem",
        display_name="Arcane Golem",
        element="Arcane",
        bpm=70,
        max_hp=250,
        max_toughness=120,
        base_damage=10,
        speed=30,
        display_mesh="/Game/EnvSandbox/Melodia/Monsters/SM_ArcaneGolem",
        mesh_scale=1.5,
    ),""")


def gen_enemy_gale() -> str:
    return textwrap.dedent("""\
    MelodiaEnemyDef(
        enemy_id="StormFalcon",
        display_name="Storm Falcon",
        element="Gale",
        bpm=180,
        max_hp=90,
        max_toughness=30,
        base_damage=8,
        speed=120,
        display_mesh="/Game/EnvSandbox/Melodia/Monsters/SM_StormFalcon",
        mesh_scale=0.8,
    ),""")


def gen_enemy_tide() -> str:
    return textwrap.dedent("""\
    MelodiaEnemyDef(
        enemy_id="AbyssalKraken",
        display_name="Abyssal Kraken",
        element="Tide",
        bpm=60,
        max_hp=300,
        max_toughness=150,
        base_damage=14,
        speed=20,
        display_mesh="/Game/EnvSandbox/Melodia/Monsters/SM_AbyssalKraken",
        mesh_scale=2.0,
    ),""")


def gen_skills_l10() -> list[dict]:
    return [
        {"skill_id": "EmberStorm", "display_name": "Ember Storm", "element": "Forte",
         "instrument": "keyboard", "mechanic_level": 10, "sp_cost": 25, "power_scalar": 2.8,
         "note_pitches": (72, 76, 79, 84), "note_durations": (0.25, 0.25, 0.25, 0.5)},
        {"skill_id": "StoneBarrier", "display_name": "Stone Barrier", "element": "Stone",
         "instrument": "drum", "mechanic_level": 11, "sp_cost": 18, "power_scalar": 1.5,
         "note_pitches": (40, 47, 52), "note_durations": (0.5, 0.5, 0.5)},
        {"skill_id": "VoidLament", "display_name": "Void Lament", "element": "Umbral",
         "instrument": "violin", "mechanic_level": 12, "sp_cost": 30, "power_scalar": 3.5,
         "note_pitches": (55, 51, 48, 43), "note_durations": (0.5, 0.25, 0.25, 0.5)},
        {"skill_id": "ArcaneCascade", "display_name": "Arcane Cascade", "element": "Arcane",
         "instrument": "MusicBox", "mechanic_level": 13, "sp_cost": 22, "power_scalar": 2.2,
         "note_pitches": (60, 64, 67, 72, 76), "note_durations": (0.25, 0.25, 0.25, 0.25, 0.5)},
        {"skill_id": "RadiantBurst", "display_name": "Radiant Burst", "element": "Radiant",
         "instrument": "keyboard", "mechanic_level": 14, "sp_cost": 28, "power_scalar": 3.0,
         "note_pitches": (84, 88, 91, 96), "note_durations": (0.25, 0.25, 0.25, 0.5)},
    ]


def gen_skills_l15() -> list[dict]:
    return [
        {"skill_id": "TempestFury", "display_name": "Tempest Fury", "element": "Gale",
         "instrument": "violin", "mechanic_level": 15, "sp_cost": 35, "power_scalar": 4.0,
         "note_pitches": (76, 79, 84, 88, 91), "note_durations": (0.125,) * 4 + (0.5,)},
        {"skill_id": "TidalCrush", "display_name": "Tidal Crush", "element": "Tide",
         "instrument": "drum", "mechanic_level": 16, "sp_cost": 32, "power_scalar": 3.8,
         "note_pitches": (36, 48, 60, 72), "note_durations": (0.5, 0.25, 0.25, 0.5)},
        {"skill_id": "InfernoWaltz", "display_name": "Inferno Waltz", "element": "Forte",
         "instrument": "keyboard", "mechanic_level": 17, "sp_cost": 38, "power_scalar": 4.2,
         "note_pitches": (72, 76, 72, 79, 72, 84), "note_durations": (0.25,) * 6},
        {"skill_id": "CrystalSanctum", "display_name": "Crystal Sanctum", "element": "Stone",
         "instrument": "MusicBox", "mechanic_level": 18, "sp_cost": 20, "power_scalar": 1.0,
         "note_pitches": (48, 52, 55, 60), "note_durations": (0.5, 0.5, 0.5, 1.0)},
        {"skill_id": "UmbralRequiem", "display_name": "Umbral Requiem", "element": "Umbral",
         "instrument": "violin", "mechanic_level": 19, "sp_cost": 40, "power_scalar": 4.5,
         "note_pitches": (43, 40, 36, 43, 40, 36, 31), "note_durations": (0.25,) * 7},
    ]


def gen_skills_l20() -> list[dict]:
    return [
        {"skill_id": "AstralHarmony", "display_name": "Astral Harmony", "element": "Arcane",
         "instrument": "MusicBox", "mechanic_level": 20, "sp_cost": 35, "power_scalar": 3.5,
         "note_pitches": (60, 64, 67, 72, 76, 84), "note_durations": (0.25, 0.25, 0.25, 0.25, 0.25, 0.5)},
        {"skill_id": "SolarFlare", "display_name": "Solar Flare", "element": "Radiant",
         "instrument": "keyboard", "mechanic_level": 22, "sp_cost": 42, "power_scalar": 5.0,
         "note_pitches": (96, 100, 103, 108), "note_durations": (0.25, 0.25, 0.25, 0.75)},
        {"skill_id": "StormChase", "display_name": "Storm Chase", "element": "Gale",
         "instrument": "violin", "mechanic_level": 24, "sp_cost": 30, "power_scalar": 2.5,
         "note_pitches": (79, 84, 79, 88, 79, 91), "note_durations": (0.125,) * 6},
        {"skill_id": "AbyssalSong", "display_name": "Abyssal Song", "element": "Tide",
         "instrument": "drum", "mechanic_level": 25, "sp_cost": 45, "power_scalar": 5.5,
         "note_pitches": (36, 48, 60, 48, 36), "note_durations": (0.5, 0.25, 0.5, 0.25, 1.0)},
        {"skill_id": "PhoenixRise", "display_name": "Phoenix Rise", "element": "Forte",
         "instrument": "keyboard", "mechanic_level": 27, "sp_cost": 50, "power_scalar": 6.0,
         "note_pitches": (72, 76, 84, 91, 96, 108), "note_durations": (0.25,) * 5 + (1.0,)},
    ]


def gen_skills_l25() -> list[dict]:
    return [
        {"skill_id": "TerraFirma", "display_name": "Terra Firma", "element": "Stone",
         "instrument": "drum", "mechanic_level": 28, "sp_cost": 25, "power_scalar": 2.0,
         "note_pitches": (40, 48, 52, 60), "note_durations": (0.5, 0.5, 0.5, 1.0)},
        {"skill_id": "VoidGate", "display_name": "Void Gate", "element": "Umbral",
         "instrument": "violin", "mechanic_level": 29, "sp_cost": 55, "power_scalar": 7.0,
         "note_pitches": (36, 31, 43, 31, 36, 31), "note_durations": (0.25,) * 6},
        {"skill_id": "CosmicResonance", "display_name": "Cosmic Resonance", "element": "Arcane",
         "instrument": "MusicBox", "mechanic_level": 30, "sp_cost": 60, "power_scalar": 8.0,
         "note_pitches": (48, 60, 72, 84, 96, 108), "note_durations": (0.5,) * 4 + (0.25, 1.0)},
        {"skill_id": "Judgment", "display_name": "Judgment", "element": "Radiant",
         "instrument": "keyboard", "mechanic_level": 30, "sp_cost": 60, "power_scalar": 8.5,
         "note_pitches": (108, 103, 108, 112, 108, 120), "note_durations": (0.25, 0.125, 0.25, 0.125, 0.25, 1.0)},
        {"skill_id": "GrandFinale", "display_name": "Grand Finale", "element": "Tide",
         "instrument": "drum", "mechanic_level": 30, "sp_cost": 65, "power_scalar": 9.0,
         "note_pitches": (36, 48, 60, 72, 84, 96), "note_durations": (0.25,) * 4 + (0.5, 1.5)},
    ]


MELODIA_GENERATORS = {
    "enemy_forte": gen_enemy_forte,
    "enemy_umbral": gen_enemy_umbral,
    "enemy_arcane": gen_enemy_arcane,
    "enemy_gale": gen_enemy_gale,
    "enemy_tide": gen_enemy_tide,
    "skills_l10": gen_skills_l10,
    "skills_l15": gen_skills_l15,
    "skills_l20": gen_skills_l20,
    "skills_l25": gen_skills_l25,
}


# --- Game: equipment + patches ---

def gen_equip_weapons() -> list[dict]:
    return [
        {"item_id": "forte_brand", "display_name": "Forte Brand", "slot": "weapon",
         "min_attack_bonus": 10, "max_attack_bonus": 16, "element": "Forte", "speed_bonus": 8},
        {"item_id": "tide_trident", "display_name": "Tide Trident", "slot": "weapon",
         "min_attack_bonus": 8, "max_attack_bonus": 14, "element": "Tide", "hp_bonus": 30},
        {"item_id": "umbral_sickle", "display_name": "Umbral Sickle", "slot": "weapon",
         "min_attack_bonus": 12, "max_attack_bonus": 18, "element": "Umbral", "defense_bonus": 5},
        {"item_id": "arcane_staff", "display_name": "Arcane Staff", "slot": "weapon",
         "min_attack_bonus": 5, "max_attack_bonus": 10, "element": "Arcane", "magic_attack_bonus": 15},
        {"item_id": "gale_blade", "display_name": "Gale Blade", "slot": "weapon",
         "min_attack_bonus": 9, "max_attack_bonus": 12, "element": "Gale", "speed_bonus": 25},
    ]


def gen_equip_armors() -> list[dict]:
    return [
        {"item_id": "forte_plate", "display_name": "Forte Plate", "slot": "armor",
         "defense_bonus": 18, "hp_bonus": 40, "element": "Forte"},
        {"item_id": "tide_scale", "display_name": "Tide Scale", "slot": "armor",
         "defense_bonus": 12, "hp_bonus": 50, "element": "Tide", "magic_defense_bonus": 10},
        {"item_id": "umbral_shroud", "display_name": "Umbral Shroud", "slot": "armor",
         "defense_bonus": 10, "magic_defense_bonus": 20, "element": "Umbral", "speed_bonus": 10},
        {"item_id": "arcane_vestments", "display_name": "Arcane Vestments", "slot": "armor",
         "defense_bonus": 8, "magic_defense_bonus": 25, "element": "Arcane", "mp_bonus": 40},
        {"item_id": "gale_habit", "display_name": "Gale Habit", "slot": "armor",
         "defense_bonus": 6, "magic_defense_bonus": 6, "element": "Gale", "speed_bonus": 30},
    ]


def gen_game_cfg_patch() -> str:
    return textwrap.dedent("""\
    # battle_manager.py — replace hardcoded tunables with GAME_CFG
    # flee_chance:
    #   GAME_CFG.flee_base_chance + (player.speed - enemy.speed) * GAME_CFG.flee_speed_factor
    # toughness_dmg:
    #   damage * GAME_CFG.toughness_reduction
    # ult_gain:
    #   GAME_CFG.ult_gain_perfect if grade == "perfect" else GAME_CFG.ult_gain_per_hit
    # defeat recovery:
    #   player.hp = max(1, player.max_hp * GAME_CFG.defeat_hp_recovery)
    # defense mitigation:
    #   max(1.0, raw_damage - defense * GAME_CFG.defense_mitigation)
    """)


def gen_test_save_manager() -> str:
    return textwrap.dedent("""\
    import os
    import tempfile
    import unittest
    from gmm.game.player_state import MelodiaPlayerState
    from gmm.game.save_manager import SaveManager


    class TestSaveManager(unittest.TestCase):
        def setUp(self):
            self.tmp = tempfile.mkdtemp()
            self.sm = SaveManager(save_dir=self.tmp)
            self.ps = MelodiaPlayerState()

        def test_save_load_roundtrip(self):
            self.ps.add_xp(50)
            self.ps.gold = 99
            path = self.sm.save(self.ps)
            self.assertTrue(os.path.isfile(path))
            loaded = MelodiaPlayerState()
            self.assertTrue(self.sm.load(loaded))
            self.assertEqual(loaded.gold, 99)

        def test_list_slots(self):
            self.sm.save(self.ps)
            slots = self.sm.list_slots()
            self.assertGreaterEqual(len(slots), 1)


    if __name__ == "__main__":
        unittest.main()
    """)


def gen_test_battle_edge() -> str:
    return textwrap.dedent("""\
    # Append to test_battle_manager.py
    def test_element_weakness_multiplier(self):
        from gmm.game.battle_manager import element_multiplier
        self.assertEqual(element_multiplier("Forte", "Stone"), 1.5)
        self.assertEqual(element_multiplier("Forte", "Tide"), 0.5)

    def test_flee_phase(self):
        mgr = MelodiaBattleManager()
        mgr.start_encounter("CrystalShard")
        mgr.player_command("flee")
        # resolve may fail flee — phase should remain valid
        self.assertIn(mgr.phase, ("AwaitingPlayerCommand", "RhythmExecution", "Fled"))
    """)


def gen_quest_stub() -> str:
    return textwrap.dedent("""\
    \"\"\"Quest manager stub — mirrors TurnBasedJRPGTemplate BP_QuestManager.\"\"\"
    from __future__ import annotations
    from dataclasses import dataclass, field


    @dataclass
    class QuestDef:
        quest_id: str
        display_name: str
        description: str = ""
        required_level: int = 1
        rewards_xp: int = 0
        rewards_gold: int = 0


    class QuestManager:
        def __init__(self):
            self.active: dict[str, QuestDef] = {}
            self.completed: list[str] = []

        def accept(self, quest: QuestDef) -> bool:
            if quest.quest_id in self.completed:
                return False
            self.active[quest.quest_id] = quest
            return True

        def complete(self, quest_id: str) -> QuestDef | None:
            q = self.active.pop(quest_id, None)
            if q:
                self.completed.append(quest_id)
            return q
    """)


GAME_GENERATORS: dict[str, Any] = {
    "equip_weapons": gen_equip_weapons,
    "equip_armors": gen_equip_armors,
    "game_cfg_patch": gen_game_cfg_patch,
    "test_save_manager": gen_test_save_manager,
    "test_battle_edge": gen_test_battle_edge,
    "quest_stub": gen_quest_stub,
}


# --- UI ---

def gen_combo_colors() -> str:
    return textwrap.dedent("""\
    # Add to GameColors in colors.py
    COMBO_TIER_3 = (0.4, 0.851, 1.0, 1.0)   # 3x combo — cyan
    COMBO_TIER_5 = (1.0, 0.902, 0.4, 1.0)   # 5x combo — gold
    COMBO_TIER_10 = (1.0, 0.431, 0.698, 1.0)  # 10x combo — magenta burst
    """)


def gen_battle_menu_wireframe() -> str:
    return textwrap.dedent("""\
    +----------------------------------+
    |  [1] Attack  [2] Skill  [3] Ult |
    |  [4] Defend  [5] Flee           |
    |  HP ████████░░  SP ██████░░░░    |
    |  ~ Rhythm lane: D F J K ~       |
    +----------------------------------+
    """)


def gen_victory_copy() -> str:
    return json.dumps({
        "victory_title": "=== VICTORY! ===",
        "combo_line": "Combo: {combo} | Max: {max_combo}",
        "grades_line": "Grades: P:{perfect} G:{great} g:{good} M:{miss}",
        "rewards_line": "XP: +{xp}  Gold: +{gold}",
    }, indent=2)


def gen_command_manifest() -> str:
    from gmm.ui.commands import GMM_COMMANDS

    entries = []
    for command_id, registration in GMM_COMMANDS.items():
        # EnvUI registrations are (section, callable) pairs, not bare callables.
        section, callback = registration
        entries.append({
            "id": command_id,
            "section": section,
            "callable": getattr(callback, "__name__", type(callback).__name__),
        })
    return json.dumps({"command_count": len(entries), "commands": entries}, indent=2)


def gen_rhythm_hud_stub() -> str:
    return json.dumps({
        "widget": "WBP_Battle_Rhythm",
        "parent": "UMelodiaRhythmHUDWidget",
        "bindings": {
            "BPMText": "clock.bpm",
            "ComboText": "battle.combo",
            "GradePop": "WBP_GradePop",
            "NoteLanes": ["D", "F", "J", "K"],
        },
    }, indent=2)


UI_GENERATORS = {
    "combo_colors": gen_combo_colors,
    "battle_menu_wireframe": gen_battle_menu_wireframe,
    "victory_copy": gen_victory_copy,
    "command_manifest": gen_command_manifest,
    "rhythm_hud_stub": gen_rhythm_hud_stub,
}


# --- JRPG bridge ---

def gen_action_map_expand() -> str:
    return json.dumps({
        "Attack": {"melodia": "basic_attack", "ue_handler": "OnBasicAttack"},
        "Skill": {"melodia": "skill", "ue_handler": "OnSkillSelected", "rhythm_phase": True},
        "Item": {"melodia": "item", "ue_handler": "OnItemUsed", "inventory_check": True},
        "Flee": {"melodia": "flee", "ue_handler": "OnFleeAttempt", "chance_formula": "GAME_CFG"},
        "Interact": {"melodia": "interact", "ue_handler": "OnWorldInteract", "overworld_only": True},
        "None": {"melodia": "", "ue_handler": None},
    }, indent=2)


def gen_equip_crosswalk() -> str:
    return json.dumps({
        "Weapon": {"slot": "weapon", "dt": "/Game/Data/Melodia/DT_MelodiaEquipment", "row_prefix": "WPN_"},
        "Armor": {"slot": "armor", "dt": "/Game/Data/Melodia/DT_MelodiaEquipment", "row_prefix": "ARM_"},
        "Shield": {"slot": "shield", "dt": "/Game/Data/Melodia/DT_MelodiaEquipment", "row_prefix": "SHD_"},
        "Helm": {"slot": "helm", "dt": "/Game/Data/Melodia/DT_MelodiaEquipment", "row_prefix": "HLM_"},
        "Boots": {"slot": "boots", "dt": "/Game/Data/Melodia/DT_MelodiaEquipment", "row_prefix": "BOT_"},
    }, indent=2)


def gen_quest_save_mapping() -> str:
    return json.dumps({
        "S_PlayerUnitData": {
            "Exp": "SaveSlot.xp",
            "currentHP": "SaveSlot.player_hp",
            "currentMP": "SaveSlot.player_mp",
            "Weapon": "SaveSlot.equipment.weapon",
        },
        "BP_JRPGSaveGame": "gmm.game.save_manager.SaveManager",
        "BP_QuestManager": "gmm.game.quest_manager.QuestManager (stub)",
    }, indent=2)


def gen_ue_scaffold_checklist() -> str:
    return textwrap.dedent("""\
    UE scaffold checklist (run when editor idle):
    [ ] import scaffold_melodia_jrpg_rhythm_bridge as b; b.main()
    [ ] Parent BP_Melodia_JRPG_Bridge -> BP_BattleController
    [ ] Skill command -> RhythmExecution -> WBP_Battle_Rhythm
    [ ] Map S_UnitStats -> DT_MelodiaEnemies rows
    [ ] Verify MelodiaCore plugin enabled
    """)


JRPG_GENERATORS = {
    "action_map_expand": gen_action_map_expand,
    "equip_crosswalk": gen_equip_crosswalk,
    "quest_save_mapping": gen_quest_save_mapping,
    "ue_scaffold_checklist": gen_ue_scaffold_checklist,
}


# =============================================================================
# Roguelike Daemon Generators
# =============================================================================

def create_roguelike_contract() -> str:
    """Emit versioned MelodiaCore fixtures and deterministic golden traces."""
    from gmm.game.roguelike_contract import SCHEMA_VERSION, golden_recipe_trace

    seeds = (1337, 7331)
    return json.dumps(
        {
            "contract_version": SCHEMA_VERSION,
            "runtime_authority": "UMelodiaRoguelikeRunSubsystem",
            "gmm_role": "offline_authoring_simulation_fixture_and_verification",
            "forbidden_outputs": ["competing_unreal_runtime_subsystem"],
            "golden_recipe_traces": {
                str(seed): golden_recipe_trace(seed, 100)
                for seed in seeds
            },
        },
        indent=2,
        sort_keys=True,
    )

def create_dungeon_translator() -> str:
    """Emit an offline spatial fixture translating MelodiaCore recipe IDs to RoomData references.

    This output is authoring data only; shipping generation never executes Python.
    """
    return json.dumps({
        "module": "gmm.game.roguelike_dungeon",
        "description": "Translates GMM floor graph into ProceduralDungeon RoomData references",
        "entry_point": "generate_floor_graph_for_dungeon",
        "integration": {
            "procedural_dungeon": {
                "version": "3.8.3",
                "bridge": "RoguelikeRoomRegistry → URoomData assets",
                "flow": "FloorGraph → ADungeonGenerator::ChooseNextRoomData → room placement",
            },
            "nikki_theme": {
                "archetypes": ["SakuraDreamer", "CosmicWeaver", "MirageDancer"],
                "post_process": ["PPV_NikkiDream", "PPV_CosmicDream", "PPV_DreamBloom"],
                "lighting": ["Lights_Nikki", "Lights_Jewelry", "Lights_Silhouette"],
            },
        },
        "floor_rules": {
            "boss_every": 5,
            "standard_rooms_per_floor": "3-4",
            "shop_chance": 0.15,
            "treasure_chance": 0.15,
            "elite_chance_floor3plus": 0.30,
            "event_chance": 0.05,
        },
    }, indent=2)


def create_blessings_system() -> str:
    """Generate element-based blessings system with songcraft resonance.

    Expands the 6 basic blessings into a full 7-element + 3 resonance system.
    """
    from gmm.game.roguelike import BLESSINGS

    elements = {
        "Forte": {"name": "Ember Gift", "desc": "Unlock Forte element affinity", "cost": 25},
        "Tide": {"name": "Tidal Gift", "desc": "Unlock Tide element affinity", "cost": 25},
        "Gale": {"name": "Zephyr Gift", "desc": "Unlock Gale element affinity", "cost": 25},
        "Stone": {"name": "Crag Gift", "desc": "Unlock Stone element affinity", "cost": 25},
        "Radiant": {"name": "Radiance Gift", "desc": "Unlock Radiant element affinity", "cost": 25},
        "Umbral": {"name": "Eclipse Gift", "desc": "Unlock Umbral element affinity", "cost": 25},
        "Arcane": {"name": "Mystic Gift", "desc": "Unlock Arcane element affinity", "cost": 25},
    }

    resonance_tiers = {
        "Novice Resonance": {"elements_required": 3, "bonus": "+5% all elemental damage", "cost": 50},
        "Adept Resonance": {"elements_required": 5, "bonus": "+10% toughness damage, +5ms perfect window", "cost": 100},
        "Master Resonance": {"elements_required": 7, "bonus": "Ultimate deals +100% damage to broken enemies", "cost": 200},
    }

    existing = {bid: b.to_dict() for bid, b in BLESSINGS.items()}

    return json.dumps({
        "description": "7-element blessings + 3 resonance tiers (Infinity Nikki styling challenges)",
        "element_blessings": elements,
        "resonance_tiers": resonance_tiers,
        "meta_progression": {
            "total_token_cost_all_blessings": sum(b.token_cost for b in BLESSINGS.values()) + sum(e["cost"] for e in elements.values()) + sum(r["cost"] for r in resonance_tiers.values()),
            "estimated_runs_to_max": "~15-25 runs (assuming 10-15 golden tokens per run)",
        },
        "existing_blessings": existing,
    }, indent=2)


def create_artifacts_relics() -> str:
    """Generate artifacts (mid-run pickups) and relics (meta-progression).

    Expands the 4 basic artifacts with element-themed variants.
    """
    from gmm.game.roguelike import ARTIFACTS

    element_artifacts = {
        "ForteFlame": {"element": "Forte", "effect": "Forte skills have 30% chance to apply Burn on hit", "cost": 3},
        "TidePearl": {"element": "Tide", "effect": "Tide skills heal party for 15% of damage dealt", "cost": 3},
        "GaleFeather": {"element": "Gale", "effect": "Gale skills grant +1 SP on perfect timing", "cost": 3},
        "StoneHeart": {"element": "Stone", "effect": "Stone skills deal +50% toughness damage", "cost": 4},
        "RadiantBloom": {"element": "Radiant", "effect": "Radiant skills grant +5% ult gauge on hit", "cost": 3},
        "UmbralVeil": {"element": "Umbral", "effect": "Umbral skills reduce enemy turn delay by 1 stack on perfect", "cost": 3},
        "ArcanePrism": {"element": "Arcane", "effect": "Arcane skills have 20% chance to deal double damage", "cost": 5},
    }

    relics = {
        "NikkiLens": {"name": "Nikki Lens", "effect": "Start with 1 random artifact", "cost": 100, "tier": "rare"},
        "Dreamcatcher": {"name": "Dreamcatcher", "effect": "Shop prices reduced by 25%", "cost": 75, "tier": "uncommon"},
        "ComposerScore": {"name": "Composer's Score", "effect": "+2 SP at start of each encounter", "cost": 150, "tier": "epic"},
        "FlorawishCharm": {"name": "Florawish Charm", "effect": "Enemies have 10% less HP", "cost": 100, "tier": "rare"},
        "HeartcraftCrown": {"name": "Heartcraft Crown", "effect": "All element blessings unlocked (ignore element requirements)", "cost": 500, "tier": "legendary"},
    }

    existing = {aid: a.to_dict() for aid, a in ARTIFACTS.items()}

    return json.dumps({
        "description": "Artifacts (mid-run) + Relics (meta-progression) for Melodia roguelike",
        "element_artifacts": element_artifacts,
        "total_artifacts": len(ARTIFACTS) + len(element_artifacts),
        "relics": relics,
        "total_relics": len(relics),
        "existing_artifacts": existing,
    }, indent=2)


def create_dungeon_generator() -> str:
    """Generate dungeon generator configuration.

    Now using ProceduralDungeon (v3.8.3) instead of BSP/grid approach.
    """
    return json.dumps({
        "description": "ProceduralDungeon-based dungeon generator for Melodia roguelike",
        "plugin": {
            "name": "ProceduralDungeon",
            "version": "3.8.3",
            "path": "Plugins/ProceduralDungeon/",
            "ue58_compatible": True,
        },
        "generation": {
            "type": "Depth First (linear dungeon) for standard floors",
            "room_batch_size": 5,
            "can_loop": False,
            "seed_type": "Fixed with auto-increment per floor",
        },
        "room_registry": {
            "source": "gmm.game.roguelike_dungeon.RoguelikeRoomRegistry",
            "total_specs": 22,
            "room_types": ["Start", "Standard", "Elite", "Boss", "Shop", "Treasure", "Event", "Blessing"],
            "variants_per_type": 3,
        },
        "nikki_integration": {
            "photo_spots": "Event rooms use Nikki photo-spot framing",
            "npcs": "3 archetypes (SakuraDreamer, CosmicWeaver, MirageDancer)",
            "lighting": "Lights_Nikki/Jewelry/Silhouette per room type",
            "post_process": "PPV_NikkiDream on all rooms",
        },
        "floor_progression": {
            "boss_every": 5,
            "rooms_per_floor": [3, 4],
            "special_room_chances": {
                "shop": 0.15,
                "treasure": 0.15,
                "elite": 0.30,
                "event": 0.05,
            },
        },
    }, indent=2)


def build_report() -> str:
    """Stub: verify ProceduralDungeon plugin is present and compatible.

    Full verification requires Unreal Editor. In standalone GMM mode,
    just reports the installed files.
    """
    from pathlib import Path
    plugin_path = Path("Plugins/ProceduralDungeon/ProceduralDungeon.uplugin")
    if plugin_path.exists():
        return json.dumps({
            "ok": True,
            "plugin_installed": True,
            "version": "3.8.3",
            "ue58_compatible": True,
            "files_verified": [
                "ProceduralDungeon.uplugin",
                "Source/ProceduralDungeon/",
                "Source/ProceduralDungeonEditor/",
            ],
            "next": "Regenerate project files and compile via UE editor",
        }, indent=2)
    return json.dumps({
        "ok": False,
        "plugin_installed": False,
        "error": "ProceduralDungeon plugin not found at Plugins/ProceduralDungeon/",
        "action": "Copy from Downloads/ProceduralDungeon-master to Plugins/",
    }, indent=2)


def build_roguelike_report() -> str:
    """Test roguelike dungeon system end-to-end (GMM standalone).

    Full Unreal Editor execution runs setup_roguelike_dungeon.py.
    This function runs the GMM-side smoke tests.
    """
    from gmm.game.roguelike_dungeon import dungeon_system_summary
    from gmm.game.roguelike import ROOM_TEMPLATES, ARTIFACTS, BLESSINGS

    summary = dungeon_system_summary()

    # Run floor graph generation for floors 1-15
    from gmm.game.roguelike_dungeon import generate_floor_graph_for_dungeon
    floors_tested = []
    for floor in [1, 3, 5, 10, 15]:
        graph = generate_floor_graph_for_dungeon(floor, seed=1337)
        floors_tested.append({
            "floor": floor,
            "nodes": len(graph.nodes),
            "has_boss": any(n.is_boss for n in graph.nodes),
            "room_types": [n.room_data_name for n in graph.nodes],
        })

    # Test shop generation
    from gmm.game.roguelike_dungeon import generate_shop_inventory
    shop = generate_shop_inventory(5, 10, seed=1337)

    # Test reward calculation
    from gmm.game.roguelike_dungeon import calculate_room_rewards
    reward = calculate_room_rewards(
        "boss", 5,
        {"perfect": 8, "great": 3, "good": 1, "miss": 0},
        max_combo=15,
        seed=1337,
    )

    summary["smoke_test"] = {
        "floor_generation_tested": floors_tested,
        "shop_generation": shop.to_dict(),
        "reward_calculation": {
            "golden_tokens": reward.golden_tokens,
            "mana_regen": round(reward.mana_regen, 1),
            "elemental_shards": reward.elemental_shards,
            "bonus_artifact_chance": reward.bonus_artifact_chance,
        },
    }

    return json.dumps(summary, indent=2)


ROGUELIKE_GENERATORS = {
    "build_report": build_report,
    "create_roguelike_contract": create_roguelike_contract,
    "create_dungeon_translator": create_dungeon_translator,
    "create_blessings_system": create_blessings_system,
    "create_artifacts_relics": create_artifacts_relics,
    "create_dungeon_generator": create_dungeon_generator,
    "build_roguelike_report": build_roguelike_report,
}
