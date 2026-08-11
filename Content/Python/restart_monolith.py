import unreal
w=unreal.EditorLevelLibrary.get_editor_world()
print('world',w)
try:
 unreal.SystemLibrary.execute_console_command(w,'Monolith.Restart')
 print('restart sent')
except Exception as e: print('err',e)
