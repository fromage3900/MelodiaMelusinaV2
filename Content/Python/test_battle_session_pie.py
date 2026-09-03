import unreal, time, json
L=unreal.EditorLevelLibrary
L.editor_play_simulate(); time.sleep(2)
world=L.get_game_world(); print('world',world)
print('classes',hasattr(unreal,'MelodiaBattleArena'),hasattr(unreal,'MelodiaBattleSession'))
if world:
 print('pc',unreal.GameplayStatics.get_player_controller(world,0))
 gi=unreal.GameplayStatics.get_game_instance(world); print('gi',gi)
 ss=gi.get_subsystem(unreal.MelodiaBattleSession); print('sub',ss)
 arena=world.spawn_actor(unreal.MelodiaBattleArena, unreal.Vector(0,0,0), unreal.Rotator(0,0,0)); print('arena',arena)
 enc=unreal.MelodiaEncounterDefinition(); enc.set_editor_property('battle_controller',arena); enc.set_editor_property('encounter_level',1); enc.set_editor_property('encounter_display_name','Smoke')
 print('begin',ss.begin_encounter(enc),'phase',ss.get_battle_phase())
 print('basic',ss.submit_basic_command(),'phase',ss.get_battle_phase())
 time.sleep(2)
 L.editor_end_play()
