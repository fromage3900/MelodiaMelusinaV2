import unreal
unreal.EditorLevelLibrary.load_level('/Game/ZenForestTest')
for a in unreal.EditorLevelLibrary.get_all_level_actors():
 n=a.get_actor_label()
 c=a.get_class().get_name()
 if any(x in (n+c).lower() for x in ['encounter','battle','generator','melodia','enemy']):
  print(n,c,a.get_path_name())
