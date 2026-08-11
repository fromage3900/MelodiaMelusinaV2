import unreal
L=unreal.EditorLevelLibrary
w=L.get_game_world(); print('world',w)
if w:
 print('pc',unreal.GameplayStatics.get_player_controller(w,0)); gi=unreal.GameplayStatics.get_game_instance(w); print('gi',gi); print('sub',gi.get_subsystem(unreal.MelodiaBattleSession))
