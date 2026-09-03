import unreal
for p in ['/Game/EnvSandbox/Greybox_Kit/SM_Greybox_Floor_4x4.SM_Greybox_Floor_4x4','/Game/EnvSandbox/Greybox_Kit/SM_Greybox_Rock_A.SM_Greybox_Rock_A']:
    m=unreal.load_asset(p)
    unreal.log('[DFBounds] %s bounds=%s' % (p, m.get_bounds() if m and hasattr(m,'get_bounds') else None))
