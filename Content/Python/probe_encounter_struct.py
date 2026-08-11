import unreal
print([x for x in dir(unreal) if 'EncounterDefinition' in x])
s=unreal.MelodiaEncounterDefinition()
print(s,[x for x in dir(s) if not x.startswith('_')])
