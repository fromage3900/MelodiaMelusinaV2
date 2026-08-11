import unreal
w=unreal.EditorLevelLibrary.get_game_world(); ss=unreal.MelodiaBattleSession.get(w); ex=ss.get_battle_controller().get_editor_property('RhythmExecution')
print('beat',ex.get_current_beat_position())
for n in ex.get_editor_property('ActiveNotes'): print(n.to_dict())
