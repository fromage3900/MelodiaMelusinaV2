import bpy, json, traceback, time, bmesh, math, mathutils
from mathutils import Vector

marker_path = r'C:\EnvironmentPortfolio\BS_GodFile\Saved\Audit\p2_detail_done.json'
log_path = r'C:\EnvironmentPortfolio\BS_GodFile\Saved\Audit\p2_detail_progress.log'
out = {'t0': time.time(), 'gates': {}}
open(log_path, 'w').close()
def log(msg):
    with open(log_path, 'a') as f:
        f.write('%.1f %s\n' % (time.time() - out['t0'], msg))

JOINTS = [
    ('neck', [-0.0026, -0.1537, 1.3682], [-0.0084, -0.0765, 0.997], 0.020),
    ('waist', [-0.001, -0.1967, 1.1772], [-0.0078, 0.3853, 0.9228], 0.030),
    ('shoulder_l', [0.1725, -0.1168, 1.2796], [0.3693, -0.074, -0.9264], 0.024),
    ('elbow_l', [0.278, -0.138, 1.0151], [0.3689, -0.0746, -0.9265], 0.019),
    ('wrist_l', [0.3836, -0.1593, 0.75], [0.4347, -0.1128, 0.8935], 0.015),
    ('hip_l', [0.0951, -0.2088, 0.8024], [-0.0168, 0.032, -0.9993], 0.026),
    ('knee_l', [0.0886, -0.1964, 0.414], [-0.0168, 0.0327, -0.9993], 0.020),
    ('ankle_l', [0.0821, -0.1837, 0.0247], [0.026, -0.4498, -0.8927], 0.016),
    ('shoulder_r', [-0.1763, -0.1168, 1.2767], [-0.3657, -0.0745, -0.9277], 0.024),
    ('elbow_r', [-0.2807, -0.1381, 1.0117], [-0.3654, -0.0751, -0.9278], 0.019),
    ('wrist_r', [-0.3853, -0.1596, 0.7462], [-0.999, 0.0265, -0.0373], 0.015),
    ('hip_r', [-0.0951, -0.2088, 0.8024], [0.0168, 0.032, -0.9993], 0.026),
    ('knee_r', [-0.0886, -0.1964, 0.414], [0.0168, 0.0327, -0.9993], 0.020),
    ('ankle_r', [-0.0821, -0.1837, 0.0247], [-0.026, -0.4498, -0.8927], 0.016),
]
GEAR_AT = {'shoulder_l', 'shoulder_r', 'hip_l', 'hip_r'}

try:
    # crash guard: stage bevels on empty meshes AV during full eval
    snap = []
    for o in bpy.data.objects:
        for m in o.modifiers:
            snap.append((m, m.show_viewport, m.show_render))
            m.show_viewport = False
            m.show_render = False
    log('guarded %d modifiers' % len(snap))

    coll = bpy.data.collections.get('MEL_DollKit_Detail')
    if coll:
        for o in list(coll.objects):
            bpy.data.objects.remove(o, do_unlink=True)
    else:
        coll = bpy.data.collections.new('MEL_DollKit_Detail')
        bpy.context.scene.collection.children.link(coll)

    # ---- materials ----
    def make_mat(name, color, metallic, rough):
        m = bpy.data.materials.get(name) or bpy.data.materials.new(name)
        m.use_nodes = True
        bsdf = m.node_tree.nodes.get('Principled BSDF')
        bsdf.inputs['Base Color'].default_value = (*color, 1.0)
        bsdf.inputs['Metallic'].default_value = metallic
        bsdf.inputs['Roughness'].default_value = rough
        m.diffuse_color = (*color, 1.0)
        return m
    mj_porcelain = make_mat('mj_porcelain', (0.93, 0.90, 0.86), 0.0, 0.35)
    mj_brass = make_mat('mj_brass', (0.72, 0.52, 0.22), 0.9, 0.30)
    mj_steel = make_mat('mj_steel', (0.55, 0.58, 0.62), 0.95, 0.25)
    log('materials ok')

    # ---- reusable GN rivet ring (attribute-driven: each ring object's mesh
    #      carries ring_radius / rivet_count / rivet_r as POINT attrs) ----
    ng = bpy.data.node_groups.get('MEL_dollkit_rivet_ring')
    if ng:
        bpy.data.node_groups.remove(ng)
    ng = bpy.data.node_groups.new('MEL_dollkit_rivet_ring', 'GeometryNodeTree')
    ng.interface.new_socket(name='Geometry', in_out='INPUT', socket_type='NodeSocketGeometry')
    ng.interface.new_socket(name='Geometry', in_out='OUTPUT', socket_type='NodeSocketGeometry')
    n_out = ng.nodes.new('NodeGroupOutput'); n_out.location = (600, 0)
    n_gin = ng.nodes.new('NodeGroupInput'); n_gin.location = (-600, -350)
    def named_attr(name, dtype, loc):
        na = ng.nodes.new('GeometryNodeInputNamedAttribute')
        na.data_type = dtype
        na.inputs['Name'].default_value = name
        na.location = loc
        return na
    n_rad = named_attr('ring_radius', 'FLOAT', (-600, 200))
    n_cnt = named_attr('rivet_count', 'INT', (-600, 0))
    n_rrad = named_attr('rivet_r', 'FLOAT', (-600, -200))
    n_circ = ng.nodes.new('GeometryNodeCurvePrimitiveCircle'); n_circ.location = (-350, 200)
    n_circ.mode = 'RADIUS'
    ng.links.new(n_rad.outputs['Attribute'], n_circ.inputs['Radius'])
    n_pts = ng.nodes.new('GeometryNodeCurveToPoints'); n_pts.location = (-100, 100)
    n_pts.mode = 'COUNT'
    n_pts.inputs['Count'].default_value = 12
    ng.links.new(n_circ.outputs['Curve'], n_pts.inputs['Curve'])
    n_ico = ng.nodes.new('GeometryNodeMeshIcoSphere'); n_ico.location = (-100, -150)
    ng.links.new(n_rrad.outputs['Attribute'], n_ico.inputs['Radius'])
    n_inst = ng.nodes.new('GeometryNodeInstanceOnPoints'); n_inst.location = (150, 100)
    ng.links.new(n_pts.outputs['Points'], n_inst.inputs['Points'])
    ng.links.new(n_ico.outputs['Mesh'], n_inst.inputs['Instance'])
    n_real = ng.nodes.new('GeometryNodeRealizeInstances'); n_real.location = (400, 100)
    ng.links.new(n_inst.outputs['Instances'], n_real.inputs['Geometry'])
    ng.links.new(n_real.outputs['Geometry'], n_out.inputs['Geometry'])
    out['gn_nodes'] = len(ng.nodes)

    # ---- per-station objects ----
    for label, head, axis, ball_r in JOINTS:
        pos = Vector(head)
        ax = Vector(axis).normalized()
        rot = ax.to_track_quat('Z', 'Y').to_euler()

        # ball
        bm = bmesh.new()
        bmesh.ops.create_uvsphere(bm, u_segments=24, v_segments=16, radius=ball_r,
                                  matrix=mathutils.Matrix.Identity(4))
        m = bpy.data.meshes.new('MEL_dollkit_ball_' + label)
        bm.to_mesh(m); bm.free()
        ob = bpy.data.objects.new('MEL_dollkit_ball_' + label, m)
        coll.objects.link(ob)
        ob.location = pos
        ob.data.materials.append(mj_porcelain)
        for p in m.polygons:
            p.use_smooth = True

        # rivet ring (GN, attribute-driven)
        me2 = bpy.data.meshes.new('MEL_dollkit_ringmesh_' + label)
        me2.from_pydata([(0, 0, 0)], [], [])
        a1 = me2.attributes.new('ring_radius', 'FLOAT', 'POINT')
        a1.data[0].value = ball_r + 0.008
        a2 = me2.attributes.new('rivet_count', 'INT', 'POINT')
        a2.data[0].value = 12
        a3 = me2.attributes.new('rivet_r', 'FLOAT', 'POINT')
        a3.data[0].value = 0.0035
        ring = bpy.data.objects.new('MEL_dollkit_ring_' + label, me2)
        coll.objects.link(ring)
        ring.location = pos
        ring.rotation_euler = rot
        mod = ring.modifiers.new('rivets', 'NODES')
        mod.node_group = ng
        ring.data.materials.append(mj_brass)

        # gear cap at hero joints
        if label in GEAR_AT:
            teeth = 12
            ro = ball_r + 0.012
            ri = ro * 0.78
            thick = 0.006
            outline = []
            steps = teeth * 2
            for i in range(steps):
                a = 2 * math.pi * i / steps
                r = ro if i % 2 == 0 else ri
                outline.append((r * math.cos(a), r * math.sin(a)))
            vs = [(x, y, -thick / 2) for (x, y) in outline] + [(x, y, thick / 2) for (x, y) in outline]
            fs = []
            fs.append(tuple(range(steps - 1, -1, -1)))
            fs.append(tuple(range(steps, 2 * steps)))
            for i in range(steps):
                j = (i + 1) % steps
                fs.append((i, j, steps + j, steps + i))
            gm = bpy.data.meshes.new('MEL_dollkit_gear_' + label)
            gm.from_pydata(vs, [], fs)
            gm.update()
            gear = bpy.data.objects.new('MEL_dollkit_gear_' + label, gm)
            coll.objects.link(gear)
            gear.location = pos + ax * (ball_r * 0.7)
            gear.rotation_euler = rot
            gear.data.materials.append(mj_steel)
    bpy.context.view_layer.update()
    log('station objects built')
    bpy.context.scene.frame_set(1)

    # ---- gates ----
    g = out['gates']
    balls = [o for o in coll.objects if o.name.startswith('MEL_dollkit_ball_')]
    rings = [o for o in coll.objects if o.name.startswith('MEL_dollkit_ring_')]
    gears = [o for o in coll.objects if o.name.startswith('MEL_dollkit_gear_')]
    g['balls'] = len(balls)
    g['rings'] = len(rings)
    g['gears'] = len(gears)
    g['gn_nodes'] = len(ng.nodes)
    # GN ring must evaluate to real geometry
    eval_rv = 0
    dg = bpy.context.evaluated_depsgraph_get()
    for r in rings:
        ev = r.evaluated_get(dg)
        mev = ev.to_mesh()
        eval_rv += len(mev.vertices)
        ev.to_mesh_clear()
    g['ring_eval_verts'] = eval_rv
    g['pass'] = (len(balls) == 14 and len(rings) == 14 and len(gears) == 4
                 and g['gn_nodes'] >= 8 and eval_rv >= 1500)
    log('gates pass=%s ring_eval_verts=%d' % (g['pass'], eval_rv))

    # ---- renders (workbench, material colors) ----
    scene = bpy.context.scene
    scene.render.engine = 'BLENDER_WORKBENCH'
    scene.display.shading.light = 'STUDIO'
    scene.display.shading.color_type = 'MATERIAL'
    scene.render.resolution_x = 1000
    scene.render.resolution_y = 1000
    scene.render.image_settings.file_format = 'PNG'
    show = set(balls) | set(rings) | set(gears)
    seg_coll = bpy.data.collections.get('MEL_DollKit_Segments')
    if seg_coll:
        show |= set(seg_coll.objects)
    for o in bpy.data.objects:
        o.hide_render = (o not in show)
    cam_data = bpy.data.cameras.new('p2cam')
    cam = bpy.data.objects.new('p2cam', cam_data)
    scene.collection.objects.link(cam)
    scene.camera = cam
    def aim(target):
        d = target - cam.location
        cam.rotation_euler = d.to_track_quat('-Z', 'Y').to_euler()
    def closeup(name, target, dist):
        cam.location = (target.x + dist * 0.6, target.y - dist, target.z + dist * 0.45)
        cam_data.clip_end = dist * 10
        aim(Vector(target))
        scene.render.filepath = r'C:\EnvironmentPortfolio\BS_GodFile\Saved\Audit\blender_stage_views_20260923\p2_' + name + '.png'
        bpy.ops.render.render(write_still=True)
    jm = {j[0]: j for j in JOINTS}
    closeup('shoulder_l', Vector(jm['shoulder_l'][1]), 0.16)
    closeup('knee_l', Vector(jm['knee_l'][1]), 0.16)
    closeup('wrist_r', Vector(jm['wrist_r'][1]), 0.13)
    bpy.data.objects.remove(cam, do_unlink=True)
    for o in bpy.data.objects:
        o.hide_render = False
    log('renders done')

    # restore stage modifiers BEFORE saving
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
print('P2_DONE', out.get('status'))
