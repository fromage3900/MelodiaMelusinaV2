import unreal

pairs = [
    ('/Game/EnvSandbox/Monoliths/SeaAbove/Prototype/Reef/Meshes/SM_Banner.SM_Banner',
     '/Game/EnvSandbox/Monoliths/SeaAbove/Prototype/Reef/Materials/MI_SeaAbove_Cloth_Banner.MI_SeaAbove_Cloth_Banner'),
    ('/Game/EnvSandbox/Monoliths/SeaAbove/Prototype/Reef/Meshes/SM_Shroud.SM_Shroud',
     '/Game/EnvSandbox/Monoliths/SeaAbove/Prototype/Reef/Materials/MI_SeaAbove_Cloth_Shroud.MI_SeaAbove_Cloth_Shroud'),
]

ok = 0
fails = []
for mpath, mp in pairs:
    try:
        m = unreal.load_asset(mpath)
        mat = unreal.load_asset(mp)
        if m is None:
            fails.append('%s: mesh not loadable' % mpath)
            continue
        if mat is None:
            fails.append('%s: MI not loadable' % mp)
            continue
        cls = m.get_class().get_name()
        unreal.log_warning('CLOTH mesh=%s class=%s mat=%s' % (mpath, cls, mat.get_name()))
        if cls == 'SkeletalMesh':
            m.set_material(0, mat)
            ok += 1
        else:
            fails.append('%s: unexpected class %s' % (mpath, cls))
    except Exception as e:
        fails.append('%s :: %s' % (mpath, e))

unreal.log_warning('CLOTH_BIND ok=%d fails=%d' % (ok, len(fails)))
for f in fails:
    unreal.log_warning('CLOTH_FAIL %s' % f)