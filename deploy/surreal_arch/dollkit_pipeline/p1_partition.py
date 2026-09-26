import bpy, json, traceback, time, math, bmesh
from mathutils import Vector

marker_path = r'C:\EnvironmentPortfolio\BS_GodFile\Saved\Audit\p1_partition_done.json'
log_path = r'C:\EnvironmentPortfolio\BS_GodFile\Saved\Audit\p1_partition_progress.log'
out = {'t0': time.time(), 'gates': {}}
open(log_path, 'w').close()
def log(msg):
    with open(log_path, 'a') as f:
        f.write('%.1f %s\n' % (time.time() - out['t0'], msg))

try:
    dk = bpy.data.objects['Melusina_DollKit']
    me = dk.data
    names = [g.name for g in dk.vertex_groups]

    GROUPS = ['head', 'chest', 'pelvis',
              'upperarm_l', 'forearm_l', 'hand_l',
              'upperarm_r', 'forearm_r', 'hand_r',
              'thigh_l', 'shin_l', 'foot_l',
              'thigh_r', 'shin_r', 'foot_r']

    def classify_vg(n):
        nl = n.lower()
        side = 'l' if nl.endswith('.l') else ('r' if nl.endswith('.r') else None)
        if 'forearm' in nl:
            return 'forearm_' + side if side else None
        if 'thigh' in nl:
            return 'thigh_' + side if side else None
        if 'spine_03' in nl or 'spine_02' in nl or 'chest' in nl or 'breast' in nl:
            return 'chest'
        if 'spine_01' in nl or 'pelvis' in nl or 'hips' in nl:
            return 'pelvis'
        if 'neck' in nl or 'subneck' in nl:
            return 'head'
        if 'leg' in nl and 'pole' not in nl and 'proj' not in nl:
            return 'shin_' + side if side else None
        if 'foot' in nl or 'toes' in nl:
            return 'foot_' + side if side else None
        if 'hand' in nl:
            return 'hand_' + side if side else None
        if 'arm' in nl and 'pole' not in nl:
            return 'upperarm_' + side if side else None
        if 'shoulder' in nl:
            return 'chest'
        if 'root' in nl or 'spine' in nl:
            return 'pelvis'
        return None

    member_idx = {}
    for gi, n in enumerate(names):
        g = classify_vg(n)
        if g:
            member_idx[gi] = g
    out['vgroups_matched'] = len(member_idx)
    log('vgroups matched: %d' % len(member_idx))

    n = len(me.vertices)
    vert_group = [None] * n
    classified = []  # (index) for KD flood
    fallback = 0
    for i, v in enumerate(me.vertices):
        best_g = None
        best_w = 0.0
        for gr in v.groups:
            gi = gr.group
            if gi in member_idx and gr.weight > best_w:
                best_w = gr.weight
                best_g = member_idx[gi]
        if best_g is None or best_w < 1e-4:
            fallback += 1
        vert_group[i] = best_g
        if best_g is not None:
            classified.append(i)
    out['fallback_verts'] = fallback
    log('pass1 classified=%d fallback=%d' % (len(classified), fallback))

    # flood fallback verts: group of nearest classified vert (KD tree)
    if fallback:
        from mathutils import kdtree
        kd = kdtree.KDTree(len(classified))
        for j, vi in enumerate(classified):
            kd.insert(me.vertices[vi].co, j)
        kd.balance()
        flooded = 0
        for i, v in enumerate(me.vertices):
            if vert_group[i] is None:
                _co, j, _d = kd.find(v.co)
                vert_group[i] = vert_group[classified[j]]
                flooded += 1
        log('flooded %d verts' % flooded)

    # geometric arm-chain split: PCA along each arm, thirds by projection
    arm_splits = {}
    for s in ('l', 'r'):
        idxs = [i for i in range(n) if vert_group[i] == 'upperarm_' + s]
        if len(idxs) < 200:
            continue
        pts = [me.vertices[i].co.copy() for i in idxs]
        cen = Vector((0, 0, 0))
        for p in pts:
            cen += p
        cen /= len(pts)
        # covariance power iteration for principal axis
        cov = [[0.0] * 3 for _ in range(3)]
        for p in pts:
            d = p - cen
            for a in range(3):
                for b in range(3):
                    cov[a][b] += d[a] * d[b]
        axis = Vector((1, 0, 0))
        for _ in range(32):
            na = Vector((sum(cov[a][b] * axis[b] for b in range(3)) for a in range(3)))
            if na.length < 1e-12:
                break
            axis = na.normalized()
        # orient axis away from body center (PCA sign is arbitrary; without
        # this one side's upper/fore/hand split comes out mirrored)
        body_cen = Vector((0.0, -0.15, 1.0))
        if axis.dot(cen - body_cen) < 0:
            axis = -axis
        ts = [((p - cen).dot(axis)) for p in pts]
        tmin, tmax = min(ts), max(ts)
        rng = max(tmax - tmin, 1e-6)
        n_u = n_f = n_h = 0
        for k, i in enumerate(idxs):
            t = (ts[k] - tmin) / rng
            if t < 0.55:
                vert_group[i] = 'upperarm_' + s; n_u += 1
            elif t < 0.85:
                vert_group[i] = 'forearm_' + s; n_f += 1
            else:
                vert_group[i] = 'hand_' + s; n_h += 1
        arm_splits[s] = {'verts': len(idxs), 'upper': n_u, 'fore': n_f, 'hand': n_h}
    out['arm_splits'] = arm_splits
    log('arm splits: %s' % json.dumps(arm_splits))

    # face assignment: modal group; boundary faces go to every present group
    from collections import defaultdict
    group_faces = defaultdict(list)
    for p in me.polygons:
        gs = set(vert_group[vi] for vi in p.vertices)
        for g in gs:
            group_faces[g].append(p.vertices)

    coll = bpy.data.collections.get('MEL_DollKit_Segments')
    if coll:
        for o in list(coll.objects):
            bpy.data.objects.remove(o, do_unlink=True)
    else:
        coll = bpy.data.collections.new('MEL_DollKit_Segments')
        bpy.context.scene.collection.children.link(coll)

    segments = {}
    for gname, faces in group_faces.items():
        if len(faces) < 100:
            continue
        bm = bmesh.new()
        vmap = {}
        for vs in faces:
            new_vs = []
            for vi in vs:
                nv = vmap.get(vi)
                if nv is None:
                    nv = bm.verts.new(me.vertices[vi].co)
                    vmap[vi] = nv
                new_vs.append(nv)
            try:
                bm.faces.new(tuple(new_vs))
            except ValueError:
                pass
        bm.normal_update()
        m2 = bpy.data.meshes.new('MEL_seg_' + gname)
        bm.to_mesh(m2)
        bm.free()
        ob = bpy.data.objects.new('MEL_seg_' + gname, m2)
        coll.objects.link(ob)
        segments[gname] = ob
    out['segment_count'] = len(segments)

    g = out['gates']
    total = sum(sum(p.area for p in o.data.polygons) for o in segments.values())
    per = {k: {'verts': len(o.data.vertices),
               'area': round(sum(p.area for p in o.data.polygons), 3),
               'centroid': [round(v, 3) for v in (sum((o.matrix_world @ vv.co for vv in o.data.vertices), Vector()) / len(o.data.vertices))]}
           for k, o in segments.items()}
    g['per_segment'] = per
    g['total_area'] = round(total, 3)
    g['area_ratio'] = round(total / 2.143, 3)
    g['all_15_segments'] = len(segments) == 15
    g['area_ok'] = 1.0 <= g['area_ratio'] <= 1.15
    g['min_segment_area'] = round(min(v['area'] for v in per.values()), 3)
    g['pass'] = g['all_15_segments'] and g['area_ok'] and g['min_segment_area'] > 0.005
    log('gates pass=%s' % g['pass'])

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
print('PARTITION_DONE', out.get('status'))
