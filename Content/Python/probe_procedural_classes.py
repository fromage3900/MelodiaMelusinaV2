import unreal
for n in ['RoomData','DoorDef','BoxMinAndMax','RoguelikeRoomCustomData']:
    unreal.log('[ProcProbe] %s=%s' % (n, getattr(unreal,n,None)))
for p in ['/Script/ProceduralDungeon.RoomData','/Script/ProceduralDungeon.DoorDef','/Script/MelodiaCore.RoguelikeRoomCustomData']:
    try: unreal.log('[ProcProbe] load '+p+' -> '+str(unreal.load_class(None,p)))
    except Exception as e: unreal.log_warning('[ProcProbe] '+str(e))
