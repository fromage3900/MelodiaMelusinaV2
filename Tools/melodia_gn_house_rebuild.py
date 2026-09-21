import bpy, sys, traceback, importlib
from mathutils import Vector

sys.path.insert(0, r'P:/MelodiaMelusinaV2-Laptop/deploy')
import surreal_arch.melodia_gn.paris_wall_detail as pwd

def sec(name, fn):
    try:
        print('---', name)
        fn()
    except Exception:
        traceback.print_exc(file=sys.stdout)

W = []

def rollout():
    for o in bpy.data.objects:
        if o.name.startswith('WALL_') and 'CURVED' not in o.name:
            st = 2 if 'W001' in o.name else 1
            n = pwd._set_mod(o, bpy.data.node_groups['GN_PARIS_WallDetail'], 'ParisDetail', style=st)
            W.append((o.name, n))
        elif o.name.startswith('SLAB_'):
            n = pwd._set_mod(o, bpy.data.node_groups['GN_PARIS_SlabTrim'], 'SlabTrim')
            W.append((o.name, n))

def corner_w(m, co):
    return m @ Vector(co)

def verify():
    bad = 0
    for o in bpy.data.objects:
        if not (o.name.startswith('WALL_') or o.name.startswith('SLAB_')):
            continue
        if 'CURVED' in o.name:
            continue
        vs = [corner_w(o.matrix_world, v.co) for v in o.data.vertices]
        blo = Vector((min(v.x for v in vs), min(v.y for v in vs), min(v.z for v in vs)))
        bhi = Vector((max(v.x for v in vs), max(v.y for v in vs), max(v.z for v in vs)))
        bpy.context.view_layer.update()
        ev = o.evaluated_get(bpy.context.evaluated_depsgraph_get())
        m = ev.to_mesh()
        evo = [v.co for v in m.vertices]
        n = len(evo)
        if n:
            elo = Vector((min(c.x for c in evo), min(c.y for c in evo), min(c.z for c in evo)))
            ehi = Vector((max(c.x for c in evo), max(c.y for c in evo), max(c.z for c in evo)))
        else:
            elo = ehi = Vector((0, 0, 0))
        ev.to_mesh_clear()
        dz = ehi.z - bhi.z
        dx = max(elo.x - blo.x, ehi.x - bhi.x)
        dy = max(elo.y - blo.y, ehi.y - bhi.y)
        limz = 1.35 if 'W001' in o.name else 0.45
        ok = dx <= 0.45 and dy <= 0.45 and dz <= limz and dz >= -0.45 and n > 0
        if not ok:
            bad += 1
        print('VV', o.name, 'n=%d dx=%.2f dy=%.2f dz=%+.2f' % (n, dx, dy, dz), 'OK' if ok else 'BAD')
    print('GATE', 'PASS' if bad == 0 else 'FAIL', bad)

def done():
    bpy.ops.wm.save_mainfile()
    print('saved')

sec('reload', lambda: importlib.reload(pwd))
sec('purge', lambda: [bpy.data.node_groups.remove(bpy.data.node_groups[g]) for g in ('GN_PARIS_WallDetail', 'GN_PARIS_SlabTrim') if g in bpy.data.node_groups] and None or print('purged'))
sec('rebuild', lambda: (print('wd:', pwd.build_wall_detail()), print('st:', pwd.build_slab_trim())))
sec('rollout', rollout)
sec('verify', verify)
sec('save', done)
