import unreal
bp=unreal.load_object(None,'/Game/Melodia/Roguelike/Blueprints/BP_RoguelikeDungeonGenerator'); a=unreal.GameplayStatics.get_all_actors_of_class(unreal.EditorLevelLibrary.get_game_world(),bp.generated_class())[0]
print([x for x in dir(a) if any(k in x.lower() for k in ['generate','start','room','dungeon'])][:100])
