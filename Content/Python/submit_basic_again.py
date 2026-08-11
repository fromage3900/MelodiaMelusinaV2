import unreal
w=unreal.EditorLevelLibrary.get_game_world(); ss=unreal.MelodiaBattleSession.get(w); print('submit2',ss.submit_basic_command(),'phase',ss.get_battle_phase())
