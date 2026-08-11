import unreal
for n in dir(unreal):
    if 'Roguelike' in n or 'Nikki' in n: unreal.log('[EnumProbe] '+n+'='+str(getattr(unreal,n)))
for c in (unreal.RoguelikeRoomType, unreal.NikkiNPCArchetype, unreal.NikkiLightingPreset):
    unreal.log('[EnumProbeMembers] '+c.__name__+' '+str([x for x in dir(c) if x.isupper()]))
