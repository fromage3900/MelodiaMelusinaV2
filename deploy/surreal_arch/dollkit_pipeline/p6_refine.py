import bpy, json, traceback, time, math, os
from mathutils import Vector, kdtree

M = r'C:\EnvironmentPortfolio\BS_GodFile\Saved\Audit\p6_refine_done.json'
LOG = r'C:\EnvironmentPortfolio\BS_GodFile\Saved\Audit\p6_refine_progress.log'
RD = r'C:\EnvironmentPortfolio\BS_GodFile\Saved\Audit\blender_stage_views_20260923'
out = {'t0': time.time(), 'gates': {}}
open(LOG, 'w').close()
def log(s):
    open(LOG, 'a').write('%.1f %s\n' % (time.time() - out['t0'], s))

SEG_STATIONS = {
    'head': [('neck', 0.020)], 'chest': [('neck', 0.020), ('waist', 0.030), ('shoulder_l', 0.024), ('shoulder_r', 0.024)],
    'pelvis': [('waist', 0.030), ('hip_l', 0.026), ('hip_r', 0.026)],
    'upperarm_l': [('shoulder_l', 0.024), ('elbow_l', 0.019)], 'forearm_l': [('elbow_l', 0.019), ('wrist_l', 0.015)],
    'hand_l': [('wrist_l', 0.015)], 'thigh_l': [('hip_l', 0.026), ('knee_l', 0.020)],
    'shin_l': [('knee_l', 0.020), ('ankle_l', 0.016)], 'foot_l': [('ankle_l', 0.016)],
    'upperarm_r': [('shoulder_r', 0.024), ('elbow_r', 0.019)], 'forearm_r': [('elbow_r', 0.019), ('wrist_r', 0.015)],
    'hand_r': [('wrist_r', 0.015)], 'thigh_r': [('hip_r', 0.026), ('knee_r', 0.020)],
    'shin_r': [('knee_r', 0.020), ('ankle_r', 0.016)], 'foot_r': [('ankle_r', 0.016)],
}
NEW_R = {'waist': 0.038, 'neck': 0.026}  # torso balls sit proud like Ashlotte's corset joints
GEAR_LABELS = ('shoulder_l', 'shoulder_r', 'hip_l', 'hip_r')

def torus(major, minor, seg=24, side=8):
    vs, fs = [], []
    for i in range(seg):
        a = 2*math.pi*i/seg
        for j in range(side):
            b = 2*math.pi*j/side
            vs.append(((major+minor*math.cos(b))*math.cos(a), (major+minor*math.cos(b))*math.sin(a), minor*math.sin(b)))
    for i in range(seg):
        for j in range(side):
            fs.append((i*side+j, ((i+1)%seg)*side+j, ((i+1)%seg)*side+(j+1)%side, i*side+(j+1)%side))
    return vs, fs

def gear(root_r, tip_r, teeth, thick):
    vs, fs = [], []
    per = []
    for t in range(teeth):
        a0 = 2*math.pi*t/teeth
        for f, r in ((0.00, root_r), (0.18, root_r), (0.30, tip_r), (0.55, tip_r), (0.67, root_r)):
            a = a0 + f*2*math.pi/teeth
            per.append((r*math.cos(a), r*math.sin(a)))
    n = len(per)
    vs = [(x, y, thick/2) for x, y in per] + [(x, y, -thick/2) for x, y in per]
    fs.append(tuple(range(n)))
    fs.append(tuple(range(2*n-1, n-1, -1)))
    for i in range(n):
        fs.append((i, (i+1) % n, (i+1) % n+n, i+n))
    return vs, fs

def tube(r1, r2, length, seg=16):
    vs, fs = [], []
    for z, r in ((-length/2, r1), (length/2, r2)):
        for i in range(seg):
            a = 2*math.pi*i/seg
            vs.append((r*math.cos(a), r*math.sin(a), z))
    for i in range(seg):
        fs.append((i, (i+1) % seg, (i+1) % seg+seg, i+seg))
    return vs, fs

try:
    segs = {o.name.replace('MEL_seg_', ''): o for o in bpy.data.collections['MEL_DollKit_Segments'].objects}
    coll = bpy.data.collections['MEL_DollKit_Detail']
    brass = bpy.data.materials.get('mj_brass') or bpy.data.materials.new('mj_brass')
    steel = bpy.data.materials.get('mj_steel') or bpy.data.materials.new('mj_steel')

    def centroid(o):
        ws = o.data.vertices
        n = len(ws)
        return Vector((sum(v.co.x for v in ws)/n, sum(v.co.y for v in ws)/n, sum(v.co.z for v in ws)/n))

    PAIRS = []
    seen = set()
    for sname, lst in SEG_STATIONS.items():
        for label, br in lst:
            if label in seen: continue
            seen.add(label)
            others = [s for s, l in SEG_STATIONS.items() if any(x[0] == label for x in l) and s != sname]
            if others: PAIRS.append((label, sname, others[0], br))

    stations = {}
    for label, an, bn, br in PAIRS:
        A, B = segs[an], segs[bn]
        kd = kdtree.KDTree(len(A.data.vertices))
        for i, v in enumerate(A.data.vertices): kd.insert(v.co, i)
        kd.balance()
        best = None
        for v in B.data.vertices:
            co, j, d = kd.find(v.co)
            if best is None or d < best[0]: best = (d, v.co.copy(), A.data.vertices[j].co.copy())
        stations[label] = {'C': (best[1]+best[2])/2,
                           'axis': (centroid(B)-centroid(A)).normalized(),
                           'a': an, 'b': bn, 'ball_r': NEW_R.get(label, br)}
    log('stations %d' % len(stations))

    # remove old rings + star gears
    old = [o for o in coll.objects if o.name.startswith('MEL_dollkit_ring_') or o.name.startswith('MEL_dollkit_gear_')]
    for o in old: coll.objects.unlink(o); bpy.data.objects.remove(o)
    log('cleared %d old hardware' % len(old))

    def make(name, vs, fs, mat):
        me = bpy.data.meshes.new(name+'M')
        me.from_pydata(vs, [], fs); me.update()
        ob = bpy.data.objects.new(name, me)
        coll.objects.link(ob)
        if mat: me.materials.append(mat)
        return ob

    ring_records = {}
    for label, an, bn, br in PAIRS:
        st = stations[label]
        C, ax, ball_r = st['C'], st['axis'], st['ball_r']
        rot = ax.to_track_quat('Z', 'Y').to_euler()
        # resize ball to new radius
        ball = bpy.data.objects.get('MEL_dollkit_ball_' + label)
        if ball: ball.scale = (ball_r/br, ball_r/br, ball_r/br)
        # stacked double ring: outer proud equator + inner seat ring (Ashlotte layering)
        for sub, maj, minor in (('outer', ball_r*1.06, ball_r*0.16), ('inner', ball_r*0.84, ball_r*0.09)):
            vs, fs = torus(maj, minor)
            ob = make('MEL_dk2_ring_%s_%s' % (label, sub), vs, fs, brass)
            ob.location = C; ob.rotation_euler = rot
            if sub == 'outer': ring_records[label] = {'ob': ob, 'maj': maj, 'C': C}
        # 12 rivets on outer ring
        rv, rf = [], []
        for i in range(12):
            a = 2*math.pi*i/12
            c = Vector((math.cos(a)*ball_r*1.06, math.sin(a)*ball_r*1.06, 0))
            r = ball_r*0.07
            base = len(rv)
            for dx, dy, dz in ((r,0,0),(-r,0,0),(0,r,0),(0,-r,0),(0,0,r),(0,0,-r)):
                rv.append(tuple(c+Vector((dx,dy,dz))))
            rf += [(base,base+2,base+4),(base+2,base+1,base+4),(base+1,base+3,base+4),(base+3,base,base+4),
                   (base+2,base,base+5),(base+1,base+2,base+5),(base+3,base+1,base+5),(base,base+3,base+5)]
        ob = make('MEL_dk2_rivets_' + label, rv, rf, brass)
        ob.location = C; ob.rotation_euler = rot
        # real cog gears on shoulders/hips, facing outward
        if label in GEAR_LABELS:
            vs, fs = gear(ball_r*0.95, ball_r*1.18, 14, ball_r*0.36)
            ob = make('MEL_dk2_gear_' + label, vs, fs, steel)
            ob.location = C + ax*(ball_r*0.55); ob.rotation_euler = rot
        # flared cuffs on both sides covering the twin-cut rim scars
        for side, sfx in ((-1, 'a'), (1, 'b')):
            vs, fs = tube(ball_r*1.12, ball_r*1.42, ball_r*1.1)
            ob = make('MEL_dk2_cuff_%s_%s' % (label, sfx), vs, fs, brass)
            ob.location = C + ax*side*(ball_r*0.75 + ball_r*0.55)
            ob.rotation_euler = (ax*side).to_track_quat('Z', 'Y').to_euler()
    log('hardware built')

    # wind-up key on the upper back (clockwork doll signature)
    chest_c = centroid(segs['chest'])
    back = Vector((0, 1, 0))
    key_vs, key_fs = [], []
    sv, sf = tube(0.011, 0.011, 0.05)
    key_vs += sv; key_fs += sf
    cv, cf = tube(0.007, 0.007, 0.11)
    cv = [(x, y, z+0.075) for x, y, z in cv]
    key_vs += cv; key_fs += [(a+len(sv), b+len(sv), c+len(sv), d+len(sv)) for a, b, c, d in cf]
    for sgn in (-1, 1):
        pv, pf = tube(0.028, 0.028, 0.012, seg=12)
        pv = [(x, y+sgn*0.062, z+0.115) for x, y, z in pv]
        key_vs += pv; key_fs += [(a+len(key_vs)-len(pv), b+len(key_vs)-len(pv), c+len(key_vs)-len(pv), d+len(key_vs)-len(pv)) for a, b, c, d in pf]
    key = make('MEL_dk2_windup_key', key_vs, key_fs, steel)
    key.location = chest_c + Vector((0, 0.075, 0.04))
    key.rotation_euler = (math.pi/2, 0, 0)
    log('windup key placed')

    # ---- gates ----
    g = out['gates']
    ok = True
    # G1: outer ring major radius correct and ring proud of both shells
    proud = {}
    for label, rec in ring_records.items():
        st = stations[label]
        kdS = {}
        for sname in (st['a'], st['b']):
            kd = kdtree.KDTree(len(segs[sname].data.vertices))
            for i, v in enumerate(segs[sname].data.vertices): kd.insert(v.co, i)
            kd.balance(); kdS[sname] = kd
        me = rec['ob'].data
        best = 1e9
        for v in me.vertices:
            w = rec['ob'].matrix_world @ v.co
            for kd in kdS.values():
                co, j, d = kd.find(w)
                best = min(best, d)
        proud[label] = round(best*1000, 2)
        if best < 0.0005: ok = False
    g['ring_proud_mm'] = proud
    g['G1_proud'] = ok
    # G2: gear teeth
    gv = 0
    for label in GEAR_LABELS:
        ob = bpy.data.objects.get('MEL_dk2_gear_' + label)
        if ob is None: ok = False; continue
        gv = len(ob.data.vertices)
    g['gear_verts'] = gv
    g['G2_gear'] = gv == 140  # 14 teeth x 5 profile pts x 2 faces
    # G3: cuffs clear the ball
    clr = 1e9
    for label, an, bn, br in PAIRS:
        st = stations[label]
        for sfx in ('a', 'b'):
            ob = bpy.data.objects.get('MEL_dk2_cuff_%s_%s' % (label, sfx))
            if ob is None: continue
            for v in ob.data.vertices:
                d = ((ob.matrix_world @ v.co) - st['C']).length
                clr = min(clr, d)
    g['cuff_min_to_ball_mm'] = round(clr*1000, 2)
    g['G3_cuff'] = clr > st['ball_r']*1.0
    g['pass'] = g['G1_proud'] and g['G2_gear'] and g['G3_cuff']

    # ---- renders ----
    scene = bpy.context.scene
    scene.render.engine = 'BLENDER_WORKBENCH'
    scene.display.shading.light = 'STUDIO'
    scene.display.shading.color_type = 'MATERIAL'
    scene.render.resolution_x = 1000
    scene.render.resolution_y = 1000
    scene.render.image_settings.file_format = 'PNG'
    show = set(segs.values()) | set(coll.objects)
    for o in bpy.data.objects: o.hide_render = (o not in show)
    cam_data = bpy.data.cameras.new('p6cam')
    cam = bpy.data.objects.new('p6cam', cam_data)
    scene.collection.objects.link(cam); scene.camera = cam
    def aim(t):
        cam.rotation_euler = (t - cam.location).to_track_quat('-Z', 'Y').to_euler()
    allc = [centroid(o) for o in segs.values()]
    mid = Vector((0, 0, 0))
    for c in allc: mid += c
    mid /= len(allc)
    rad = max((c - mid).length for c in allc)
    cam.location = mid + Vector((1.0, -1.4, 0.5)) * rad * 1.9
    cam_data.clip_end = rad*20; cam_data.clip_start = rad*0.02
    aim(mid)
    scene.render.filepath = RD + '\\p6_full.png'
    bpy.ops.render.render(write_still=True)
    for label, dist in (('waist', 0.16), ('shoulder_l', 0.12), ('wrist_l', 0.09)):
        st = stations[label]
        cam.location = (st['C'].x + dist*0.7, st['C'].y - dist, st['C'].z + dist*0.5)
        cam_data.clip_end = dist*20; cam_data.clip_start = dist*0.02
        aim(st['C'])
        scene.render.filepath = RD + '\\p6_%s.png' % label
        bpy.ops.render.render(write_still=True)
    bpy.data.objects.remove(cam, do_unlink=True)
    for o in bpy.data.objects: o.hide_render = False
    log('renders done')

    if g['pass']:
        bpy.ops.wm.save_mainfile()
        out['saved'] = True
        out['status'] = 'ok'
    else:
        out['status'] = 'gate_fail_no_save'
    out['elapsed_s'] = round(time.time() - out['t0'], 1)
except Exception:
    out['status'] = 'exception'
    out['trace'] = traceback.format_exc()[-2000:]
open(M, 'w').write(json.dumps(out, indent=1))
print('P6_DONE', out.get('status'))
