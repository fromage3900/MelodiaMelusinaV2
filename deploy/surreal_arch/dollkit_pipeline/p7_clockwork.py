import bpy, bmesh, json, traceback, time, math
from mathutils import Vector, kdtree

M = r'C:\EnvironmentPortfolio\BS_GodFile\Saved\Audit\p7_clockwork_done.json'
LOG = r'C:\EnvironmentPortfolio\BS_GodFile\Saved\Audit\p7_clockwork_progress.log'
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
GEAR_LABELS = {'shoulder_l', 'shoulder_r', 'hip_l', 'hip_r'}

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

try:
    segs = {o.name.replace('MEL_seg_', ''): o for o in bpy.data.collections['MEL_DollKit_Segments'].objects}
    detail = bpy.data.collections['MEL_DollKit_Detail']

    higgs = [g.name for g in bpy.data.node_groups if 'higgs' in g.name.lower()]
    out['higgsas_groups'] = higgs
    log('higgsas groups present: %s' % higgs)

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

    stations = []
    for label, an, bn, br in PAIRS:
        A, B = segs[an], segs[bn]
        kd = kdtree.KDTree(len(A.data.vertices))
        for i, v in enumerate(A.data.vertices): kd.insert(v.co, i)
        kd.balance()
        best = None
        for v in B.data.vertices:
            co, j, d = kd.find(v.co)
            if best is None or d < best[0]: best = (d, v.co.copy(), A.data.vertices[j].co.copy())
        C = (best[1]+best[2])/2
        axis = (centroid(B)-centroid(A)).normalized()
        # measured seating: how far each shell reaches past the throat, and
        # where the window-side (b) open rim actually is
        def depth(S):
            dmax = 0.0
            for v in S.data.vertices:
                p = v.co - C
                d = p.dot(axis)
                rad = (p - d*axis).length
                if rad < br*2.2 and abs(d) > dmax: dmax = abs(d)
            return dmax
        da, db = depth(A), depth(B)
        ball_r = min(max(db*1.05 + 0.0015, br), br*2.2)
        # b-side open-rim anchor via bmesh boundary verts near the station
        rim = None
        bm = bmesh.new(); bm.from_mesh(B.data)
        bverts = [v for v in bm.verts if any(len(e.link_faces) == 1 for e in v.link_edges)
                  and abs((v.co - C).dot(axis)) < 0.03]
        if bverts:
            rc = Vector((0, 0, 0))
            for v in bverts: rc += v.co
            rim = rc/len(bverts)
        bm.free()
        if rim is None:
            rim = C + axis*(db*0.55)
        stations.append({'label': label, 'C': C, 'axis': axis, 'br': br,
                         'ball_r': ball_r, 'off': min(db*0.45, ball_r*0.6),
                         'rim': rim, 'gear': 1.0 if label in GEAR_LABELS else 0.0})
    log('stations measured: %d' % len(stations))

    # ---- control mesh: editable parameter carrier (drag points = move joints) ----
    me = bpy.data.meshes.new('MEL_dollkit_stationsM')
    me.from_pydata([tuple(s['C']) for s in stations], [], [])
    me.update()
    ctrl = bpy.data.objects.get('MEL_dollkit_stations')
    if ctrl: bpy.data.objects.remove(ctrl, do_unlink=True)
    ctrl = bpy.data.objects.new('MEL_dollkit_stations', me)
    detail.objects.link(ctrl)
    def attr(name, dt, vals):
        a = me.attributes.get(name) or me.attributes.new(name, dt, 'POINT')
        if dt == 'FLOAT_VECTOR':
            for i, v in enumerate(vals): a.data[i].vector = v
        else:
            for i, x in enumerate(vals): a.data[i].value = x
    attr('axis', 'FLOAT_VECTOR', [tuple(s['axis']) for s in stations])
    attr('ball_r', 'FLOAT', [s['ball_r'] for s in stations])
    attr('ball_off', 'FLOAT', [s['off'] for s in stations])
    attr('rim', 'FLOAT_VECTOR', [tuple(s['rim']) for s in stations])
    attr('has_gear', 'FLOAT', [s['gear'] for s in stations])
    # global editable params (same value on every point; edit one or all)
    attr('ball_scale', 'FLOAT', [1.0]*len(stations))
    attr('ring_proud', 'FLOAT', [1.06]*len(stations))
    attr('cuff_len', 'FLOAT', [1.0]*len(stations))
    attr('gear_spin', 'FLOAT', [0.5]*len(stations))
    attr('rivet_n', 'FLOAT', [12.0]*len(stations))
    log('control mesh built')

    # hide P6 fallback meshes (kept in file)
    n_hidden = 0
    for o in detail.objects:
        if o.name.startswith('MEL_dk2_'):
            o.hide_render = True; o.hide_viewport = True; o.hide_set(True)
            n_hidden += 1
    log('P6 fallback hidden: %d' % n_hidden)

    # gear template
    gt = bpy.data.objects.get('MEL_dk2_gear_template')
    if gt is None:
        gvs, gfs = gear(0.95, 1.18, 14, 0.36)
        gme = bpy.data.meshes.new('gearTM'); gme.from_pydata(gvs, [], gfs); gme.update()
        gt = bpy.data.objects.new('MEL_dk2_gear_template', gme)
        detail.objects.link(gt)
    gt.hide_render = True; gt.hide_viewport = True; gt.hide_set(True)

    # ---- master GN tree (native nodes; Higgsas integration points logged) ----
    ng = bpy.data.node_groups.get('MEL_dollkit_clockwork')
    if ng: bpy.data.node_groups.remove(ng)
    ng = bpy.data.node_groups.new('MEL_dollkit_clockwork', 'GeometryNodeTree')
    ng.interface.new_socket(name='Geometry', in_out='INPUT', socket_type='NodeSocketGeometry')
    ng.interface.new_socket(name='Geometry', in_out='OUTPUT', socket_type='NodeSocketGeometry')
    pass  # use ng.nodes / ng.links directly
    def node(t, x, y):
        nd = ng.nodes.new(t); nd.location = (x, y); return nd
    def named(nm, x, y):
        nd = node('GeometryNodeInputNamedAttribute', x, y)
        nd.data_type = 'FLOAT_VECTOR' if nm in ('axis', 'rim') else 'FLOAT'
        nd.inputs['Name'].default_value = nm
        return nd
    gin = node('NodeGroupInput', -1200, 0)
    gout = node('NodeGroupOutput', 1400, 0)
    pts = gin.outputs['Geometry']
    na_axis = named('axis', -1200, -300)
    na_br = named('ball_r', -1200, -420)
    na_boff = named('ball_off', -1200, -540)
    na_rim = named('rim', -1200, -660)
    na_gear = named('has_gear', -1200, -780)
    na_bscale = named('ball_scale', -1200, -900)
    na_proud = named('ring_proud', -1200, -1020)
    na_clen = named('cuff_len', -1200, -1140)
    na_spin = named('gear_spin', -1200, -1260)
    na_rn = named('rivet_n', -1200, -1380)
    math_scale = node('ShaderNodeMath', -950, -900); math_scale.operation = 'MULTIPLY'
    ng.links.new(na_bscale.outputs['Attribute'], math_scale.inputs[0]); math_scale.inputs[1].default_value = 1.0
    ball_r_final = node('ShaderNodeMath', -700, -420); ball_r_final.operation = 'MULTIPLY'
    ng.links.new(na_br.outputs['Attribute'], ball_r_final.inputs[0]); ng.links.new(math_scale.outputs[0], ball_r_final.inputs[1])
    # ball center = C + axis*off
    axoff = node('ShaderNodeVectorMath', -950, -540); axoff.operation = 'SCALE'
    ng.links.new(na_axis.outputs['Attribute'], axoff.inputs[0]); ng.links.new(na_boff.outputs['Attribute'], axoff.inputs[3])
    setpos = node('GeometryNodeSetPosition', -600, -500)
    ng.links.new(pts, setpos.inputs['Geometry'])
    ng.links.new(axoff.outputs['Vector'], setpos.inputs['Offset'])
    pts = setpos.outputs['Geometry']
    bc = node('ShaderNodeVectorMath', -700, -300); bc.operation = 'ADD'
    ng.links.new(gin.outputs['Geometry'], bc.inputs[0])  # placeholder replaced below
    ng.nodes.remove(bc)
    pos_in = node('GeometryNodeInputPosition', -950, -240)
    bc = node('ShaderNodeVectorMath', -700, -240); bc.operation = 'ADD'
    ng.links.new(pos_in.outputs['Position'], bc.inputs[0]); ng.links.new(axoff.outputs['Vector'], bc.inputs[1])
    # BALL
    sph = node('GeometryNodeMeshUVSphere', -700, -60)
    sph.inputs['Radius'].default_value = 1.0
    sph.inputs['Segments'].default_value = 32
    sph.inputs['Rings'].default_value = 16
    inst_ball = node('GeometryNodeInstanceOnPoints', -400, -60)
    ng.links.new(pts, inst_ball.inputs['Points'])
    ng.links.new(sph.outputs['Mesh'], inst_ball.inputs['Instance'])
    ng.links.new(ball_r_final.outputs[0], inst_ball.inputs['Scale'])
    # OUTER RING (curve circle -> curve to mesh), counter-rotating slowly
    circ = node('GeometryNodeCurvePrimitiveCircle', -700, -700)
    ng.links.new(ball_r_final.outputs[0], circ.inputs['Radius'])
    ng.links.new(na_proud.outputs['Attribute'], circ.inputs['Radius'])  # proud factor folded below
    ng.nodes.remove(circ.inputs['Radius'].links[1].to_node.links[0] if False else circ)
    # (rebuild ring branch cleanly)
    ring_circ = node('GeometryNodeCurvePrimitiveCircle', -700, -700)
    mul_proud = node('ShaderNodeMath', -950, -1020); mul_proud.operation = 'MULTIPLY'
    ng.links.new(na_br.outputs['Attribute'], mul_proud.inputs[0]); ng.links.new(na_proud.outputs['Attribute'], mul_proud.inputs[1])
    ng.links.new(mul_proud.outputs[0], ring_circ.inputs['Radius'])
    ring_circ.inputs['Resolution'].default_value = 32
    prof = node('GeometryNodeCurvePrimitiveCircle', -700, -860)
    prof.inputs['Radius'].default_value = 0.16
    prof.inputs['Resolution'].default_value = 8
    c2m = node('GeometryNodeCurveToMesh', -400, -760)
    ng.links.new(ring_circ.outputs['Curve'], c2m.inputs['Curve'])
    ng.links.new(prof.outputs['Curve'], c2m.inputs['Profile Curve'])
    inst_ring = node('GeometryNodeInstanceOnPoints', -100, -700)
    ng.links.new(pts, inst_ring.inputs['Points'])
    ng.links.new(c2m.outputs['Mesh'], inst_ring.inputs['Instance'])
    align = node('FunctionNodeAlignEulerToVector', -400, -1000)
    ng.links.new(na_axis.outputs['Attribute'], align.inputs['Vector'])
    ng.links.new(align.outputs['Rotation'], inst_ring.inputs['Rotation'])
    # scale ring+profile by ball_r via instance scale
    ng.links.new(ball_r_final.outputs[0], inst_ring.inputs['Scale'])
    # RIVETS on resampled ring
    resample = node('GeometryNodeResampleCurve', -400, -1150)
    ng.links.new(ring_circ.outputs['Curve'], resample.inputs['Curve'])
    ng.links.new(na_rn.outputs['Attribute'], resample.inputs['Count'])
    ico = node('GeometryNodeMeshIcoSphere', -700, -1300)
    ico.inputs['Radius'].default_value = 0.12
    inst_rv = node('GeometryNodeInstanceOnPoints', -100, -1150)
    ng.links.new(resample.outputs['Curve'], inst_rv.inputs['Points'])
    ng.links.new(ico.outputs['Mesh'], inst_rv.inputs['Instance'])
    ng.links.new(ball_r_final.outputs[0], inst_rv.inputs['Scale'])
    ng.links.new(align.outputs['Rotation'], inst_rv.inputs['Rotation'])
    # GEAR: template object, spin via Scene Time
    oi = node('GeometryNodeObjectInfo', -700, -1500)
    oi.inputs['Object'].default_value = gt
    oi.transform_space = 'ORIGINAL'
    tm = node('GeometryNodeInputSceneTime', -950, -1600)
    mul_spin = node('ShaderNodeMath', -700, -1700); mul_spin.operation = 'MULTIPLY'
    ng.links.new(tm.outputs['Seconds'], mul_spin.inputs[0]); ng.links.new(na_spin.outputs['Attribute'], mul_spin.inputs[1])
    rot_e = node('FunctionNodeRotateEuler', -450, -1550)
    rot_e.rotation_type = 'AXIS_ANGLE'
    ng.links.new(align.outputs['Rotation'], rot_e.inputs['Rotation'])
    rot_e.inputs['Axis'].default_value = (0, 0, 1)
    ng.links.new(mul_spin.outputs[0], rot_e.inputs['Angle'])
    # filter gear points
    cmp_g = node('FunctionNodeCompare', -950, -1830)
    cmp_g.data_type = 'FLOAT'; cmp_g.operation = 'GREATER_THAN'
    ng.links.new(na_gear.outputs['Attribute'], cmp_g.inputs['A']); cmp_g.inputs['B'].default_value = 0.5
    del_g = node('GeometryNodeDeleteGeometry', -700, -1830)
    ng.links.new(pts, del_g.inputs['Geometry'])
    ng.links.new(cmp_g.outputs['Result'], del_g.inputs['Selection'])
    del_g.domain = 'POINT'
    inst_gear = node('GeometryNodeInstanceOnPoints', -100, -1500)
    ng.links.new(del_g.outputs['Geometry'], inst_gear.inputs['Points'])
    ng.links.new(oi.outputs['Geometry'], inst_gear.inputs['Instance'])
    ng.links.new(ball_r_final.outputs[0], inst_gear.inputs['Scale'])
    ng.links.new(rot_e.outputs['Rotation'], inst_gear.inputs['Rotation'])
    # CUFF on window side: cone from C+axis*off toward rim
    cuff_dir = node('ShaderNodeVectorMath', -700, -2000); cuff_dir.operation = 'SUBTRACT'
    ng.links.new(na_rim.outputs['Attribute'], cuff_dir.inputs[0]); ng.links.new(bc.outputs['Vector'], cuff_dir.inputs[1])
    cone = node('GeometryNodeMeshCone', -700, -2150)
    cone.inputs['Vertices'].default_value = 16
    cone.inputs['Radius Top'].default_value = 1.12
    cone.inputs['Radius Bottom'].default_value = 1.42
    ng.links.new(na_clen.outputs['Attribute'], cone.inputs['Depth'])
    inst_cuff = node('GeometryNodeInstanceOnPoints', -100, -2100)
    ng.links.new(pts, inst_cuff.inputs['Points'])
    ng.links.new(cone.outputs['Mesh'], inst_cuff.inputs['Instance'])
    ng.links.new(ball_r_final.outputs[0], inst_cuff.inputs['Scale'])
    ng.links.new(align.outputs['Rotation'], inst_cuff.inputs['Rotation'])
    # JOIN + realize (instances must be real mesh for bevel/export/gates)
    join = node('GeometryNodeJoinGeometry', 1100, -600)
    for src in (inst_ball, inst_ring, inst_rv, inst_gear, inst_cuff):
        ng.links.new(src.outputs['Instances'], join.inputs['Geometry'])
    realize = node('GeometryNodeRealizeInstances', 1200, -600)
    ng.links.new(join.outputs['Geometry'], realize.inputs['Geometry'])
    smooth = node('GeometryNodeSetShadeSmooth', 1300, -600)
    smooth.inputs['Shade Smooth'].default_value = True
    ng.links.new(realize.outputs['Geometry'], smooth.inputs['Geometry'])
    ng.links.new(smooth.outputs['Geometry'], gout.inputs['Geometry'])
    # materials
    brass = bpy.data.materials.get('mj_brass') or bpy.data.materials.new('mj_brass')
    steel = bpy.data.materials.get('mj_steel') or bpy.data.materials.new('mj_steel')
    porc = bpy.data.materials.get('mj_porcelain') or bpy.data.materials.new('mj_porcelain')
    log('GN tree built: %d nodes' % len(ng.nodes))

    # ---- hardware object: GN + live Bevel ----
    hw = bpy.data.objects.get('MEL_dollkit_clockwork')
    if hw: bpy.data.objects.remove(hw, do_unlink=True)
    hw = bpy.data.objects.new('MEL_dollkit_clockwork', me)  # shares attributed control mesh
    detail.objects.link(hw)
    mod = hw.modifiers.new('MEL_clockwork_GN', 'NODES')
    mod.node_group = ng
    bev = hw.modifiers.new('MEL_clockwork_bevel', 'BEVEL')
    bev.width = 0.0004; bev.segments = 2; bev.limit_method = 'ANGLE'
    log('hardware object live')
    # branch bisect: route each instance branch through Realize and count
    def eval_count():
        try:
            bpy.context.view_layer.update()
            dp = bpy.context.evaluated_depsgraph_get()
            evp = hw.evaluated_get(dp)
            t = evp.to_mesh()
            n = len(t.vertices)
            evp.to_mesh_clear()
            return n
        except Exception as e:
            log('BISECT EXC %r' % (e,))
            return -1
    try:
        join_link = realize.inputs['Geometry'].links[0]
        orig_from = join_link.from_socket
        ng.links.remove(join_link)
        probes = [('ball', inst_ball.outputs['Instances']),
                  ('ring', inst_ring.outputs['Instances']),
                  ('rivets', inst_rv.outputs['Instances']),
                  ('gear', inst_gear.outputs['Instances']),
                  ('cuff', inst_cuff.outputs['Instances']),
                  ('setpos', pts)]
        for nm, sock in probes:
            ll = ng.links.new(sock, realize.inputs['Geometry'])
            log('BISECT %s=%d' % (nm, eval_count()))
            ng.links.remove(ll)
        ng.links.new(orig_from, realize.inputs['Geometry'])
        log('BISECT full=%d' % eval_count())
    except Exception as e:
        log('BISECT2 EXC %r' % (e,))

    # ---- segments: live bevel for porcelain finish ----
    for ob in segs.values():
        if not any(m.type == 'BEVEL' for m in ob.modifiers):
            b = ob.modifiers.new('MEL_dollkit_skin_bevel', 'BEVEL')
            b.width = 0.0006; b.segments = 2; b.limit_method = 'ANGLE'
    bpy.context.view_layer.update()
    log('skin bevel live')

    # ---- gates ----
    g = out['gates']
    deps = bpy.context.evaluated_depsgraph_get()
    ev = hw.evaluated_get(deps)
    tmp = ev.to_mesh()
    nv = len(tmp.vertices); nf = len(tmp.polygons)
    ev.to_mesh_clear()
    g['eval_verts'] = nv; g['eval_faces'] = nf
    g['G1_nonempty'] = nv > 10000
    bpy.context.scene.frame_set(0); bpy.context.view_layer.update()
    h1 = hash(tuple(round(v, 4) for v in hw.evaluated_get(deps).to_mesh().vertices[5].co[:])) if False else None
    e1 = hw.evaluated_get(deps).to_mesh()
    snap1 = [tuple(v.co) for v in e1.vertices]
    e1_clear = ev.to_mesh_clear
    hw.evaluated_get(deps).to_mesh_clear()
    bpy.context.scene.frame_set(40); bpy.context.view_layer.update()
    e2 = hw.evaluated_get(deps).to_mesh()
    snap2 = [tuple(v.co) for v in e2.vertices]
    hw.evaluated_get(deps).to_mesh_clear()
    moved = sum(1 for a, b in zip(snap1, snap2) if a != b)
    g['gear_motion_changed_verts'] = moved
    g['G2_clockwork_motion'] = moved > 0
    g['pass'] = g['G1_nonempty'] and g['G2_clockwork_motion']
    log('gates pass=%s verts=%d moved=%d' % (g['pass'], nv, moved))

    # ---- renders ----
    scene = bpy.context.scene
    scene.frame_set(0)
    scene.render.engine = 'BLENDER_WORKBENCH'
    scene.display.shading.light = 'STUDIO'
    scene.display.shading.color_type = 'MATERIAL'
    scene.render.resolution_x = 1000
    scene.render.resolution_y = 1000
    scene.render.image_settings.file_format = 'PNG'
    show = set(segs.values()) | {o for o in detail.objects if not o.hide_get() and not o.name.startswith('MEL_dk2_gear_template')}
    for o in bpy.data.objects: o.hide_render = (o not in show)
    cam_data = bpy.data.cameras.new('p7cam')
    cam = bpy.data.objects.new('p7cam', cam_data)
    scene.collection.objects.link(cam); scene.camera = cam
    def aim(t): cam.rotation_euler = (t - cam.location).to_track_quat('-Z', 'Y').to_euler()
    allc = [centroid(o) for o in segs.values()]
    mid = Vector((0, 0, 0))
    for c in allc: mid += c
    mid /= len(allc)
    rad = max((c - mid).length for c in allc)
    cam.location = mid + Vector((1.0, -1.4, 0.5)) * rad * 1.9
    cam_data.clip_end = rad*20; cam_data.clip_start = rad*0.02
    aim(mid)
    scene.render.filepath = RD + '\\p7_full.png'
    bpy.ops.render.render(write_still=True)
    st_waist = [s for s in stations if s['label'] == 'waist'][0]
    cam.location = (st_waist['C'].x + 0.12, st_waist['C'].y - 0.15, st_waist['C'].z + 0.09)
    cam_data.clip_end = 3; cam_data.clip_start = 0.01
    aim(st_waist['C'])
    scene.render.filepath = RD + '\\p7_waist.png'
    bpy.ops.render.render(write_still=True)
    st_sh = [s for s in stations if s['label'] == 'shoulder_l'][0]
    cam.location = (st_sh['C'].x + 0.1, st_sh['C'].y - 0.12, st_sh['C'].z + 0.08)
    aim(st_sh['C'])
    scene.render.filepath = RD + '\\p7_shoulder.png'
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
    out['trace'] = traceback.format_exc()[-2500:]
open(M, 'w').write(json.dumps(out, indent=1))
print('P7_DONE', out.get('status'))
