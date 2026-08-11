import unreal
w=unreal.EditorLevelLibrary.get_game_world(); print('w',w)
ss=unreal.MelodiaBattleSession.get(w); print('ss',ss)
print('spawn',hasattr(w,'spawn_actor'))
if ss:
 a=w.spawn_actor(unreal.MelodiaBattleArena,unreal.Vector(0,0,0),unreal.Rotator(0,0,0)); print('arena',a)
 e=unreal.MelodiaEncounterDefinition(); e.set_editor_property('battle_controller',a); e.set_editor_property('encounter_level',1); e.set_editor_property('encounter_display_name',unreal.Text('Smoke Encounter'))
 print('begin',ss.begin_encounter(e),'phase',ss.get_battle_phase())
 print('basic',ss.submit_basic_command(),'phase',ss.get_battle_phase())
 print('active',ss.is_encounter_active())
