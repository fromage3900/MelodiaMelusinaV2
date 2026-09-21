import bpy
from mathutils import Vector

WALLS = sorted([o.name for o in bpy.data.objects if o.name.startswith('WALL_')])
SLABS = sorted([o.name for o in bpy.data.objects if o.name.startswith('SLAB_')])

def bbox(o, mesh):
    m = o.matrix_world
    vs = [m @ v.co for v in mesh.vertices]
    if not vs:
        return None
    mn = Vector((min(v.x for v in vs), min(v.y for v in vs), min(v.z for v in vs)))
    mx = Vector((max(v.x for v in vs), max(v.y for v in vs), max(v.z for v in vs)))
    return mn, mx

def eval_of(o, muted):
    md = o.modifiers.get('ParisDetail') or o.modifiers.get('SlabTrim')
    old = md.show_viewport
    md.show_viewport = not muted
    bpy.context.view_layer.update()
    dg = bpy.context.evaluated_depsgraph_get()
    me = o.evaluated_get(dg).to_mesh()
    r = bbox(o, me)
    n = len(me.vertices)
    o.evaluated_get(dg).to_mesh_clear()
    md.show_viewport = old
    return r, n

def gate(o, style):
    md = o.modifiers.get('ParisDetail') or o.modifiers.get('SlabTrim')
    if md is None:
        return 'SKIP', 0, 0.0
    b, nb = eval_of(o, True)
    e, ne = eval_of(o, False)
    if not b or not e:
        return nm, 'EMPTY', 0
    dz = 1.35 if style == 2 else 0.45
    ok = True
    for i, tol in ((0, 0.45), (1, 0.45), (2, dz)):
        if e[0][i] < b[0][i] - tol or e[1][i] > b[1][i] + tol:
            ok = False
    return ok, ne, (e[1].z - b[1].z)

fails = []
for nm in WALLS + SLABS:
    o = bpy.data.objects.get(nm)
    if not o:
        continue
    st = 2 if nm == 'WALL_W001' else 1
    ok, n, dz = gate(o, st)
    print(nm, 'PASS' if ok else 'FAIL', 'n=%d' % n, 'dz=%+.2f' % dz)
    if not ok:
        fails.append(nm)
print('GATE:', 'ALL PASS' if not fails else 'FAILS: ' + ','.join(fails))
