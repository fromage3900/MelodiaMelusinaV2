import unreal
# Start a fresh PIE world is not needed; inspect the authored BP contract.
bp=unreal.load_object(None,'/Game/Melodia/Roguelike/Blueprints/BP_RoguelikeDungeonGenerator')
print('bp',bp)
print('graphs', [g.get_name() for g in bp.get_function_graphs()])
