"""Author the typed Persona-lite content catalog against existing JRPG authorities."""
from __future__ import annotations

import unreal

CONTENT_PATH = "/Game/MelodiaIntegration/Config/DA_MelodiaPersonaContent"
INTEGRATION_PATH = "/Game/MelodiaIntegration/Config/DA_MelodiaIntegrationConfig"


def text(value: str):
    return unreal.Text(value)


def ability(identifier, name, description, stock, element, mp, level):
    value = unreal.MelodiaAbilityDefinition()
    value.set_editor_property("ability_id", identifier)
    value.set_editor_property("display_name", text(name))
    value.set_editor_property("description", text(description))
    value.set_editor_property("stock_skill_asset_id", stock)
    value.set_editor_property("element", element)
    value.set_editor_property("mp_cost", mp)
    value.set_editor_property("unlock_level", level)
    return value


def equipment(identifier, name, stock, slot, attack=0, defense=0, magic=0, speed=0):
    value = unreal.MelodiaEquipmentDefinition()
    value.set_editor_property("equipment_id", identifier)
    value.set_editor_property("display_name", text(name))
    value.set_editor_property("stock_item_asset_id", stock)
    value.set_editor_property("slot", slot)
    value.set_editor_property("attack_bonus", attack)
    value.set_editor_property("defense_bonus", defense)
    value.set_editor_property("magic_bonus", magic)
    value.set_editor_property("speed_bonus", speed)
    return value


def quest(identifier, giver, name, objective, prereq, flag, reward, required_stat="", required_value=0):
    value = unreal.MelodiaQuestDefinition()
    value.set_editor_property("quest_id", identifier)
    value.set_editor_property("giver_npc_id", giver)
    value.set_editor_property("display_name", text(name))
    value.set_editor_property("objective", text(objective))
    value.set_editor_property("prerequisite_quest_id", prereq)
    value.set_editor_property("required_social_stat_id", required_stat)
    value.set_editor_property("required_social_stat_value", required_value)
    value.set_editor_property("completion_flag_id", flag)
    value.set_editor_property("reward_id", reward)
    return value


def marker(identifier, tag, label, marker_type, quest_id=""):
    value = unreal.MelodiaMinimapMarkerDefinition()
    value.set_editor_property("marker_id", identifier)
    value.set_editor_property("actor_tag", tag)
    value.set_editor_property("label", text(label))
    value.set_editor_property("type", marker_type)
    value.set_editor_property("required_quest_id", quest_id)
    return value


def main():
    asset = unreal.EditorAssetLibrary.load_asset(CONTENT_PATH)
    if not asset:
        factory = unreal.DataAssetFactory()
        factory.set_editor_property("data_asset_class", unreal.MelodiaPersonaContent)
        asset = unreal.AssetToolsHelpers.get_asset_tools().create_asset(
            "DA_MelodiaPersonaContent", "/Game/MelodiaIntegration/Config", unreal.MelodiaPersonaContent, factory
        )
    if not asset:
        raise RuntimeError("Could not create Persona content asset")

    asset.set_editor_property("abilities", [
        ability("melodia_resonant_strike", "Resonant Strike", "A reliable opening cadence that rewards clean tempo.", "BP_FocusAttack", "Resonance", 4, 1),
        ability("melodia_starlight_refrain", "Starlight Refrain", "A focused arc of astral magic against one target.", "BP_Thunderbolt", "Astral", 8, 2),
        ability("melodia_petal_mend", "Petal Mend", "Restore an ally with a gentle Sakura refrain.", "BP_BasicHeal", "Sakura", 7, 2),
        ability("melodia_crescendo", "Crescendo", "A costly ensemble finisher for later first-dream encounters.", "BP_MeteorStorm", "Resonance", 18, 4),
    ])
    asset.set_editor_property("equipment", [
        equipment("melodia_tuning_fork", "Apprentice Tuning Fork", "BP_Rod", "Weapon", attack=3, magic=2),
        equipment("melodia_dreamweave_shawl", "Dreamweave Shawl", "BP_LeatherArmor", "Armor", defense=3, magic=1),
        equipment("melodia_star_charm", "Fallen-Star Charm", "BP_LeatherBoots", "Boots", magic=2, speed=1),
        equipment("melodia_solstice_drum", "Solstice Drum", "BP_Rod", "Weapon", attack=4, magic=3),
        equipment("melodia_dawn_veil", "First Dawn Veil", "BP_LeatherArmor", "Armor", defense=4, magic=2),
    ])
    asset.set_editor_property("reward_equipment", {
        "melodia_reward_tuning_fork": "melodia_tuning_fork",
        "melodia_reward_star_charm": "melodia_star_charm",
        "melodia_reward_dreamweave_shawl": "melodia_dreamweave_shawl",
        "melodia_reward_solstice_drum": "melodia_solstice_drum",
        "melodia_reward_dawn_veil": "melodia_dawn_veil",
    })
    asset.set_editor_property("quests", [
        quest("melodia_q_echo_01", "SD_02_PetalPriestess", "The Waking Echo", "Speak with the Petal Priestess and investigate the rhythm echo.", "", "melodia_q_echo_01_complete", "melodia_reward_tuning_fork"),
        quest("melodia_q_echo_02", "CW_01_StarWeaver", "A Constellation Out of Tune", "Win the grove encounter and report to the Star Weaver.", "melodia_q_echo_01", "melodia_q_echo_02_complete", "melodia_reward_star_charm", "melodia_harmony", 1),
        quest("melodia_q_echo_03", "MD_01_TwilightDancer", "Steps Toward Morning", "Reach the forest exit and learn the cadence home.", "melodia_q_echo_02", "melodia_q_echo_03_complete", "melodia_reward_dreamweave_shawl"),
    ])
    asset.set_editor_property("minimap_markers", [
        marker("marker_priestess", "SD_02_PetalPriestess", "Petal Priestess", unreal.MelodiaMinimapMarkerType.NPC),
        marker("marker_encounter", "melodia_smoke_encounter", "Rhythm Echo", unreal.MelodiaMinimapMarkerType.ENCOUNTER, "melodia_q_echo_02"),
        marker("marker_starweaver", "CW_01_StarWeaver", "Star Weaver", unreal.MelodiaMinimapMarkerType.NPC),
        marker("marker_exit", "MelodiaForestExit", "Path Forward", unreal.MelodiaMinimapMarkerType.EXIT, "melodia_q_echo_03"),
    ])
    unreal.EditorAssetLibrary.save_loaded_asset(asset)

    config = unreal.EditorAssetLibrary.load_asset(INTEGRATION_PATH)
    if not config:
        raise RuntimeError(f"Missing {INTEGRATION_PATH}")
    quest_ids = set(config.get_editor_property("quest_ids"))
    quest_ids.update(("melodia_q_echo_01", "melodia_q_echo_02", "melodia_q_echo_03"))
    flag_ids = set(config.get_editor_property("narrative_flag_ids"))
    flag_ids.update(("melodia_q_echo_01_complete", "melodia_q_echo_02_complete", "melodia_q_echo_03_complete"))
    reward_ids = set(config.get_editor_property("dialogue_reward_ids"))
    reward_ids.update(("melodia_reward_tuning_fork", "melodia_reward_star_charm", "melodia_reward_dreamweave_shawl"))
    reward_ids.update(("melodia_reward_solstice_drum", "melodia_reward_dawn_veil"))
    social_stat_ids = set(config.get_editor_property("social_stat_ids"))
    social_stat_ids.add("melodia_harmony")
    config.set_editor_property("quest_ids", list(quest_ids))
    config.set_editor_property("narrative_flag_ids", list(flag_ids))
    config.set_editor_property("dialogue_reward_ids", list(reward_ids))
    config.set_editor_property("social_stat_ids", list(social_stat_ids))
    unreal.EditorAssetLibrary.save_loaded_asset(config)

    counts = (
        len(asset.get_editor_property("abilities")),
        len(asset.get_editor_property("equipment")),
        len(asset.get_editor_property("quests")),
        len(asset.get_editor_property("minimap_markers")),
    )
    if counts != (4, 5, 3, 4):
        raise RuntimeError(f"Persona content count mismatch: {counts}")
    reward_map = {str(k).lower(): str(v).lower() for k, v in asset.get_editor_property("reward_equipment").items()}
    if reward_map.get("melodia_reward_solstice_drum") != "melodia_solstice_drum":
        raise RuntimeError(f"Solstice drum reward mapping not persisted: {reward_map}")
    if reward_map.get("melodia_reward_dawn_veil") != "melodia_dawn_veil":
        raise RuntimeError(f"Dawn veil reward mapping not persisted: {reward_map}")
    persisted_quests = {str(value).lower() for value in config.get_editor_property("quest_ids")}
    if not {"melodia_q_echo_01", "melodia_q_echo_02", "melodia_q_echo_03"}.issubset(persisted_quests):
        raise RuntimeError(f"Persona quest allowlist was not persisted: {sorted(persisted_quests)}")
    persisted_rewards = {str(value).lower() for value in config.get_editor_property("dialogue_reward_ids")}
    for rid in {"melodia_reward_solstice_drum", "melodia_reward_dawn_veil"}:
        if rid not in persisted_rewards:
            raise RuntimeError(f"Reward {rid} was not allowlisted: {sorted(persisted_rewards)}")
    persisted_stats = {str(value).lower() for value in config.get_editor_property("social_stat_ids")}
    if "melodia_harmony" not in persisted_stats:
        raise RuntimeError(f"Harmony allowlist was not persisted: {sorted(persisted_stats)}")
    authored_q2 = next(value for value in asset.get_editor_property("quests") if str(value.get_editor_property("quest_id")).lower() == "melodia_q_echo_02")
    if (str(authored_q2.get_editor_property("required_social_stat_id")).lower() != "melodia_harmony"
            or authored_q2.get_editor_property("required_social_stat_value") != 1):
        raise RuntimeError("Quest 2 Harmony gate was not persisted")
    print("MELODIA_PERSONA_FOUNDATION_AUTHORED abilities=4 equipment=5 quests=3 markers=4 harmony_gate=q2:1")


if __name__ == "__main__":
    main()
