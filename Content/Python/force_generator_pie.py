import unreal
w=unreal.EditorLevelLibrary.get_game_world(); bp=unreal.load_object(None,'/Game/Melodia/Roguelike/Blueprints/BP_RoguelikeDungeonGenerator'); a=unreal.GameplayStatics.get_all_actors_of_class(w,bp.generated_class())[0]
print('create',a.create_dungeon()); print('generate',a.generate()); print('rooms',a.get_nb_room())
