import unreal
print([x for x in dir(unreal.GameplayStatics) if 'spawn' in x.lower()])
