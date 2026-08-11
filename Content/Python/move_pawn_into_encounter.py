import unreal, time
w=unreal.EditorLevelLibrary.get_game_world(); pawn=unreal.GameplayStatics.get_player_pawn(w,0)
print('before',pawn.get_actor_location())
pawn.set_actor_location(unreal.Vector(500,0,100),False,False)
print('after',pawn.get_actor_location())
time.sleep(2)
ss=unreal.MelodiaBattleSession.get(w); print('phase',ss.get_battle_phase(),'active',ss.is_encounter_active(),'controller',ss.get_battle_controller())
