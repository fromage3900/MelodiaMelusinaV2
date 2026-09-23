import bpy, json, traceback, time, math, os

marker_path = r'C:\EnvironmentPortfolio\BS_GodFile\Saved\Audit\p4_export_done.json'
log_path = r'C:\EnvironmentPortfolio\BS_GodFile\Saved\Audit\p4_export_progress.log'
GLB_PATH = r'C:\EnvironmentPortfolio\harp_bow_pipeline\Melusina_DollKit_20260923.glb'
out = {'t0': time.time(), 'gates': {}}
open(log_path, 'w').close()
def log(msg):
    with open(log_path, 'a') as f:
        f.write('%.1f %s\n' % (time.time() - out['t0'], msg))

try:
    segs = {o.name.replace('MEL_seg_', ''): o for o in bpy.data.collections['MEL_DollKit_Segments'].objects}
    detail = bpy.data.collections['MEL_DollKit_Detail']
    rig = bpy.data.objects.get('MEL_DollRig')

    # junk check
    junk = [o.name for o in bpy.data.objects if o.name.startswith('MEL_cupcutter') or o.name.startswith('ZZ_')]
    log('junk objects: %d' % len(junk))

    # copernicus probe (do not promise bakes if the API is not here)
    out['copernicus'] = {
        'has_bpy_copernicus': hasattr(bpy, 'copernicus'),
        'ops_with_copernicus': [op for op in dir(bpy.ops) if 'copernicus' in op.lower()][:20],
    }
    log('copernicus probe: %s' % out['copernicus']['has_bpy_copernicus'])

    # ---- Smart UV per segment ----
    snap = []
    for o in bpy.data.objects:
        for m in o.modifiers:
            snap.append((m, m.show_viewport, m.show_render))
            m.show_viewport = False
            m.show_render = False

    uv_stats = {}
    for sname, ob in segs.items():
        me = ob.data
        bpy.ops.object.select_all(action='DESELECT')
        ob.select_set(True)
        bpy.context.view_layer.objects.active = ob
        bpy.ops.object.mode_set(mode='EDIT')
        bpy.ops.mesh.select_all(action='SELECT')
        bpy.ops.uv.smart_project(angle_limit=math.radians(66), island_margin=0.02)
        bpy.ops.object.mode_set(mode='OBJECT')
        uvs = [uv for uv in me.uv_layers]
        tot = 0
        for uv in uvs:
            tot += len(uv.data)
        uv_stats[sname] = {'uv_layers': len(uvs), 'loops': tot,
                           'ok': len(uvs) >= 1 and tot == len(me.loops)}
    g_uv = all(v['ok'] for v in uv_stats.values())
    log('UV pass=%s' % g_uv)

    # ---- combined GLB export: segments + hardware + doll rig ----
    bpy.ops.object.select_all(action='DESELECT')
    for ob in segs.values():
        ob.select_set(True)
    for ob in detail.objects:
        ob.select_set(True)
    if rig:
        rig.select_set(True)
    bpy.ops.export_scene.gltf(
        filepath=GLB_PATH,
        export_format='GLB',
        use_selection=True,
        export_animations=False,
        export_skins=True,
        export_yup=True,
    )
    g_glb = os.path.exists(GLB_PATH) and os.path.getsize(GLB_PATH) > 1000000
    out['glb'] = {'path': GLB_PATH, 'size_mb': round(os.path.getsize(GLB_PATH) / 1e6, 1) if os.path.exists(GLB_PATH) else 0}
    log('GLB exported: %s' % out['glb'])

    for m, vp, rd in snap:
        m.show_viewport = vp
        m.show_render = rd
    for ob in segs.values():
        for m in ob.modifiers:
            if m.type == 'ARMATURE' and m.name.startswith('MEL_dollkit'):
                m.show_viewport = True
                m.show_render = True

    g = out['gates']
    g['uv'] = uv_stats
    g['uv_pass'] = g_uv
    g['glb_pass'] = bool(g_glb)
    g['junk_objects'] = junk
    g['pass'] = g_uv and g_glb and not junk
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
print('P4_DONE', out.get('status'))
