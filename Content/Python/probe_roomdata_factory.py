import unreal
for n in dir(unreal):
    if 'RoomData' in n or 'Factory' in n and 'Room' in n: unreal.log('[RoomFactory] '+n+'='+str(getattr(unreal,n)))
