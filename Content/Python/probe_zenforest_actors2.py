import unreal
print('load',unreal.EditorAssetLibrary.load_asset('/Game/ZenForestTest'))
unreal.EditorLevelLibrary.load_level('/Game/ZenForestTest')
a=unreal.EditorLevelLibrary.get_all_level_actors(); print('count',len(a))
for x in a[:30]: print(x.get_actor_label(),x.get_class().get_name())
