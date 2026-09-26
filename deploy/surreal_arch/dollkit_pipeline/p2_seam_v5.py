import bpy, bmesh, json, traceback, time
from mathutils import Vector, kdtree

marker_path = r'C:\EnvironmentPortfolio\BS_GodFile\Saved\Audit\p2_seam_v5_done.json'
log_path = r'C:\EnvironmentPortfolio\BS_GodFile\Saved\Audit\p2_seam_v5_progress.log'
out = {'t0': time.time(), 'gates': {}}
open(log_path, 'w').close()
def log(msg):
    with open(log_path, 'a') as f:
        f.write('%.1f %s\n' % (time.time() - out['t0'], msg))

SEG_STATIONS = {
    'head': [('neck', 0.020)],
    'chest': [('neck', 0.020), ('waist', 0.030), ('shoulder_l', 0.024), ('shoulder_r', 0.024)],
    'pelvis': [('waist', 0.030), ('hip_l', 0.026), ('hip_r', 0.026)],
    'upperarm_l': [('shoulder_l', 0.024), ('elbow_l', 0.019)],
    'forearm_l': [('elbow_l', 0.019), ('wrist_l', 0.015)],
    'hand_l': [('wrist_l', 0.015)],
    'thigh_l': [('hip_l', 0.026), ('knee_l', 0.020)],
    'shin_l': [('knee_l', 0.020), ('ankle_l', 0.016)],
    'foot_l': [('ankle_l', 0.016)],
    'upperarm_r': [('shoulder_r', 0.024), ('elbow_r', 0.019)],
    'forearm_r': [('elbow_r', 0.019), ('wrist_r', 0.015)],
    'hand_r': [('wrist_r', 0.015)],
    'thigh_r': [('hip_r', 0.026), ('knee_r', 0.020)],
    'shin_r': [('knee_r', 0.020), ('ankle_r', 0.016)],
    'foot_r': [('ankle_r', 0.016)],
}

TWIN_MM = 1.0  # faces closer than this to the other segment's shell are duplicates

try:
    junk = [o for o in bpy.data.objects if o.name.startswith('MEL_cupcutter') or o.name.startswith('ZZ_')]
    for o in junk:
        bpy.data.objects.remove(o, do_unlink=True)
    if junk:
        log('purged %d junk objects' % len(junk))

    snap = []
    for o in bpy.data.objects:
        for m in o.modifiers:
            snap.append((m, m.show_viewport, m.show_render))
            m.show_viewport = False
            m.show_render = False
    log('guarded %d modifiers' % len(snap))

    segs = {o.name.replace('MEL_seg_', ''): o for o in bpy.data.collections['MEL_DollKit_Segments'].objects}
    detail = bpy.data.collections['MEL_DollKit_Detail']

    def centroid(o):
        ws = [v.co for v in o.data.vertices]
        n = len(ws)
        return Vector((sum(v.x for v in ws)/n, sum(v.y for v in ws)/n, sum(v.z for v in ws)/n))

    PAIRS = []
    seen = set()
    for sname, lst in SEG_STATIONS.items():
        for label, br in lst:
            if label in seen:
                continue
            seen.add(label)
            others = [s for s, l in SEG_STATIONS.items() if any(x[0] == label for x in l) and s != sname]
            if others:
                PAIRS.append((label, sname, others[0], br))

    # station at closest-approach midpoint of the two shells (the throat)
    stations = {}
    for label, a_name, b_name, ball_r in PAIRS:
        A = segs[a_name]; B = segs[b_name]
        kd = kdtree.KDTree(len(A.data.vertices))
        for i, v in enumerate(A.data.vertices):
            kd.insert(v.co, i)
        kd.balance()
        best = None
        for v in B.data.vertices:
            co, j, d = kd.find(v.co)
            if best is None or d < best[0]:
                best = (d, v.co.copy(), A.data.vertices[j].co.copy())
        d, pb, pa = best
        st = (pa + pb) / 2
        axis = (centroid(B) - centroid(A)).normalized()
        stations[label] = {'pos': st, 'axis': axis, 'ball_r': ball_r,
                           'a': a_name, 'b': b_name, 'closest_mm': round(d * 1000, 3)}
    log('stations computed: %d' % len(stations))

    # hardware to stations
    for label, a_name, b_name, ball_r in PAIRS:
        st = stations[label]
        rot = st['axis'].to_track_quat('Z', 'Y').to_euler()
        ob = bpy.data.objects.get('MEL_dollkit_ball_' + label)
        if ob:
            ob.location = st['pos']
        ob = bpy.data.objects.get('MEL_dollkit_ring_' + label)
        if ob:
            ob.location = st['pos']
            ob.rotation_euler = rot
        ob = bpy.data.objects.get('MEL_dollkit_gear_' + label)
        if ob:
            ob.location = st['pos'] + st['axis'] * (ball_r * 0.7)
            ob.rotation_euler = rot
    log('hardware placed')

    # ---- twin-face deletion from the b-side of each pair ----
    # P1 duplicated the partition boundary into both segments at identical
    # coords (coincident VERTS). Face centroids sit ~2/3*edge away from a
    # corner, so test face CORNERS, not centers. Keep a-side copies, delete
    # b-side copies: one sheet remains, z-fighting dies, a-side plugs the
    # window from every exterior view. The seam scar sits at the joint
    # throat, hidden under the ball.
    eps = TWIN_MM / 1000.0
    del_stats = {}
    for label, a_name, b_name, ball_r in PAIRS:
        A = segs[a_name]; B = segs[b_name]
        kd = kdtree.KDTree(len(A.data.vertices))
        for i, v in enumerate(A.data.vertices):
            kd.insert(v.co, i)
        kd.balance()
        me = B.data
        bm = bmesh.new()
        bm.from_mesh(me)
        kill = []
        for f in bm.faces:
            hit = False
            for v in f.verts:
                co, j, d = kd.find(v.co)
                if d < eps:
                    hit = True
                    break
            if hit:
                kill.append(f)
        if kill:
            bmesh.ops.delete(bm, geom=kill, context='FACES')
            loose = [v for v in bm.verts if not v.link_faces]
            if loose:
                bmesh.ops.delete(bm, geom=loose, context='VERTS')
            bm.to_mesh(me)
            me.update()
        bm.free()
        del_stats[label] = len(kill)
    log('twin deletion done: %s' % json.dumps(del_stats))

    # ---- gates: zero z-fight pairs remain (both directions, corner test) ----
    remaining = {}
    for label, a_name, b_name, ball_r in PAIRS:
        A = segs[a_name]; B = segs[b_name]
        cnt = 0
        for O1, O2 in ((A, B), (B, A)):
            kd = kdtree.KDTree(len(O1.data.vertices))
            for i, v in enumerate(O1.data.vertices):
                kd.insert(v.co, i)
            kd.balance()
            for p in O2.data.polygons:
                hit = False
                for vi in p.vertices:
                    co, j, d = kd.find(O2.data.vertices[vi].co)
                    if d < eps:
                        hit = True
                        break
                if hit:
                    cnt += 1
        remaining[label] = cnt
    g = out['gates']
    g['twin_faces_remaining'] = remaining
    g['deleted_faces'] = del_stats
    g['closest_mm'] = {l: stations[l]['closest_mm'] for l in stations}
    g['pass'] = all(v == 0 for v in remaining.values())
    log('gates pass=%s remaining=%s' % (g['pass'], json.dumps(remaining)))

    # ---- renders ----
    scene = bpy.context.scene
    scene.render.engine = 'BLENDER_WORKBENCH'
    scene.display.shading.light = 'STUDIO'
    scene.display.shading.color_type = 'MATERIAL'
    scene.render.resolution_x = 1000
    scene.render.resolution_y = 1000
    scene.render.image_settings.file_format = 'PNG'
    show = set(segs.values()) | set(detail.objects)
    for o in bpy.data.objects:
        o.hide_render = (o not in show)
    cam_data = bpy.data.cameras.new('p2ncam')
    cam = bpy.data.objects.new('p2ncam', cam_data)
    scene.collection.objects.link(cam)
    scene.camera = cam
    def aim(target):
        dd = target - cam.location
        cam.rotation_euler = dd.to_track_quat('-Z', 'Y').to_euler()
    def closeup(name, target, dist):
        cam.location = (target.x + dist * 0.7, target.y - dist, target.z + dist * 0.5)
        cam_data.clip_end = dist * 20
        cam_data.clip_start = dist * 0.02
        aim(target)
        scene.render.filepath = r'C:\EnvironmentPortfolio\BS_GodFile\Saved\Audit\blender_stage_views_20260923\p2n_' + name + '.png'
        bpy.ops.render.render(write_still=True)
    for label in ('elbow_l', 'wrist_l', 'knee_l', 'shoulder_l', 'neck', 'waist', 'hip_l'):
        closeup(label, stations[label]['pos'], max(stations[label]['ball_r'] * 4, 0.08))
    allc = [centroid(o) for o in segs.values()]
    mid = Vector((0, 0, 0))
    for c in allc:
        mid += c
    mid /= len(allc)
    radius = max((c - mid).length for c in allc)
    cam.location = mid + Vector((1.0, -1.4, 0.55)) * radius * 1.9
    cam_data.clip_end = radius * 20
    cam_data.clip_start = radius * 0.02
    aim(mid)
    scene.render.filepath = r'C:\EnvironmentPortfolio\BS_GodFile\Saved\Audit\blender_stage_views_20260923\p2n_full.png'
    bpy.ops.render.render(write_still=True)
    bpy.data.objects.remove(cam, do_unlink=True)
    for o in bpy.data.objects:
        o.hide_render = False
    log('renders done')

    for m, vp, rd in snap:
        m.show_viewport = vp
        m.show_render = rd

    if g['pass']:
        bpy.ops.wm.save_mainfile()
        out['saved'] = True
        out['status'] = 'ok'
    else:
        out['status'] = 'gate_fail_no_save'
    out['elapsed_s'] = round(time.time() - out['t0'], 1)
except Exception:
    out['status'] = 'exception'
    out['trace'] = traceback.format_exc()[-2500:]
with open(marker_path, 'w') as f:
    json.dump(out, f, indent=1)
print('P2SEAMV5_DONE', out.get('status'))
