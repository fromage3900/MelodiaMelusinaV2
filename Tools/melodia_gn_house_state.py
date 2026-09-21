import bpy

print('BLEND:', bpy.data.filepath)
for g in bpy.data.node_groups:
    if not g.name.startswith('GN_'):
        continue
    out = next((n for n in g.nodes if n.bl_idname == 'NodeGroupOutput'), None)
    wired = bool(out) and any(l.to_node == out for l in g.links)
    print('GROUP %r nodes=%d modifier=%s out_wired=%s' % (
        g.name, len(g.nodes), g.is_modifier, wired))
for w in ('WALL_W001', 'WALL_W002', 'WALL_W015', 'SLAB_S001'):
    o = bpy.data.objects.get(w)
    if o is None:
        print(w, 'MISSING')
        continue
    for m in o.modifiers:
        try:
            gname = m.node_group.name if m.node_group else 'None'
        except Exception as e:
            gname = 'ERR:' + str(e)
        try:
            mut = m.show_viewport
        except Exception:
            mut = '?'
        print('%s mod=%r group=%r muted=%s' % (w, m.name, gname, not mut))
print('DUMP DONE')
