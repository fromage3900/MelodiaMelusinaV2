import unreal
w=unreal.EditorLevelLibrary.get_game_world(); ss=unreal.MelodiaBattleSession.get(w)
print('submit',ss.submit_basic_command(),'phase',ss.get_battle_phase())
ctrl=ss.get_battle_controller(); ex=ctrl.get_editor_property('RhythmExecution'); print('state',ex.get_editor_property('ExecutionState'),'notes',len(ex.get_editor_property('ActiveNotes')),'start',ex.get_editor_property('ExecutionStartBeat'))
