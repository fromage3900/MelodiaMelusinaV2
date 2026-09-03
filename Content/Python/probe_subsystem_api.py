import unreal
print([x for x in dir(unreal.GameplayStatics) if 'subsystem' in x.lower() or 'game_instance' in x.lower()])
print([x for x in dir(unreal) if 'Subsystem' in x and 'Game' in x])
