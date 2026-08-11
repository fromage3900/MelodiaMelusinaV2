import unreal
w=unreal.EditorLevelLibrary.get_game_world(); bp=unreal.load_object(None,'/Game/Melodia/Roguelike/Blueprints/BP_RoguelikeDungeonGenerator'); a=unreal.GameplayStatics.get_all_actors_of_class(w,bp.generated_class())[0]
for p in ['Rooms','rooms','RoomData','RoomDataList','room_data_list','DungeonConfig','DungeonLimits']:
 try: print(p,a.get_editor_property(p))
 except Exception as e: print(p,'ERR')
