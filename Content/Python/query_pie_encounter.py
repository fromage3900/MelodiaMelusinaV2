import unreal
w=unreal.EditorLevelLibrary.get_game_world(); print('world',w)
for cls in [unreal.Pawn,unreal.MelodiaEncounterTrigger]:
 try:
  arr=unreal.GameplayStatics.get_all_actors_of_class(w,cls); print(cls.__name__,len(arr))
  for a in arr[:10]: print(a.get_name(),a.get_actor_location())
 except Exception as e: print('err',e)
ss=unreal.MelodiaBattleSession.get(w); print('session',ss,'phase',ss.get_battle_phase() if ss else None)
