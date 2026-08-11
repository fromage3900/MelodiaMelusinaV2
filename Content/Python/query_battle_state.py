import unreal
w=unreal.EditorLevelLibrary.get_game_world(); ss=unreal.MelodiaBattleSession.get(w); print('phase',ss.get_battle_phase(),'active',ss.is_encounter_active(),'hp',ss.get_editor_property('EnemyHP'),'result',ss.get_last_encounter_result())
