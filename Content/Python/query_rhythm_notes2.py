import unreal
w=unreal.EditorLevelLibrary.get_game_world(); ss=unreal.MelodiaBattleSession.get(w); ex=ss.get_battle_controller().get_editor_property('RhythmExecution')
notes=ex.get_editor_property('ActiveNotes'); print('len',len(notes))
for i,n in enumerate(notes): print(i,n.get_editor_property('TargetBeat'),n.get_editor_property('LaneIndex'),n.get_editor_property('bResolved'))
