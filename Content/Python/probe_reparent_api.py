import unreal
print([x for x in dir(unreal.BlueprintEditorLibrary) if 'parent' in x.lower() or 'compile' in x.lower() or 'blueprint' in x.lower()])
