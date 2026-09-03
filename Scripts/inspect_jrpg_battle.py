import unreal

battle_class = unreal.load_class(None, "/Game/TurnBasedJRPGTemplate/Blueprints/Battle/BP_FixedEnemyBattleBase.BP_FixedEnemyBattleBase_C")
unreal.log("BATTLE_CLASS=" + str(battle_class))
if battle_class:
    cdo = unreal.get_default_object(battle_class)
    unreal.log("CDO=" + str(cdo))
    for prop in ["off_level_battle_data", "battle_data", "default_battle_data", "tags"]:
        try:
            unreal.log(prop + "=" + str(cdo.get_editor_property(prop)))
        except Exception as error:
            unreal.log_warning(prop + " ERROR=" + str(error))

world = unreal.EditorLoadingAndSavingUtils.load_map("/Game/TurnBasedJRPGTemplate/Maps/Gameplay")
unreal.log("WORLD=" + str(world))
for actor in unreal.EditorLevelLibrary.get_all_level_actors():
    if "Battle" in actor.get_class().get_name() or "Encounter" in actor.get_class().get_name():
        unreal.log("ACTOR=" + actor.get_name() + " CLASS=" + actor.get_class().get_name() + " TAGS=" + str(actor.tags))
