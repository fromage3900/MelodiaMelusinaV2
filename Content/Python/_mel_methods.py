import unreal, json
MEL=unreal.MaterialEditingLibrary
# list methods with Function
print('METHODS', [m for m in dir(MEL) if 'unction' in m or 'function' in m or 'Expression' in m][:40])
