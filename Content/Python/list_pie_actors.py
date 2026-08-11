import unreal
w=unreal.EditorLevelLibrary.get_game_world();
for a in unreal.EditorLevelLibrary.get_all_level_actors():
 print(a.get_actor_label(),a.get_class().get_name())
