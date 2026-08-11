import unreal

unreal.EditorLoadingAndSavingUtils.load_map("/Game/ZenForestTest")
actors = unreal.EditorLevelLibrary.get_all_level_actors()
tag = unreal.Name("Encounter_CrystalShard")
for actor in actors:
    if tag in actor.tags:
        unreal.EditorLevelLibrary.destroy_actor(actor)

battle_class = unreal.load_class(None, "/Game/TurnBasedJRPGTemplate/Blueprints/Battle/BP_InteractionBattle.BP_InteractionBattle_C")
battle = unreal.EditorLevelLibrary.spawn_actor_from_class(battle_class, unreal.Vector(-20000.0, -20000.0, -10000.0))
if not battle:
    raise RuntimeError("Unable to spawn the stock interaction battle actor.")
battle.tags = [tag]
battle.set_actor_label("JRPG_CrystalShard_Battle")
unreal.EditorLevelLibrary.set_actor_selection_state(battle, False)
unreal.EditorLoadingAndSavingUtils.save_map(unreal.EditorLevelLibrary.get_editor_world(), "/Game/ZenForestTest")
unreal.log("AUTHORED_JRPG_BATTLE=" + battle.get_name() + " TAGS=" + str(battle.tags))
