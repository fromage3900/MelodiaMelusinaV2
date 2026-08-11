import unreal
w=unreal.EditorLevelLibrary.get_game_world(); bp=unreal.load_object(None,'/Game/Melodia/Roguelike/Blueprints/BP_RoguelikeDungeonGenerator'); cls=bp.generated_class(); arr=unreal.GameplayStatics.get_all_actors_of_class(w,cls); print('gens',len(arr))
for a in arr: print(a.get_name(),[p for p in dir(a) if 'room' in p.lower() or 'advance' in p.lower() or 'seed' in p.lower()][:30])
