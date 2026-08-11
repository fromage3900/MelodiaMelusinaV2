import unreal
print([x for x in dir(unreal.AsyncEditorWaitForGameWorld) if not x.startswith('_')])
