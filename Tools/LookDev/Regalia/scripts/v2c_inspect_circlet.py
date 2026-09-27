import bpy
for cn in ("REG_circlet","REG_tiara"):
    c=bpy.data.collections.get(cn)
    if not c: continue
    for o in c.all_objects:
        mats=[(s.link, s.material.name if s.material else None) for s in o.material_slots]
        n=len(o.data.vertices) if o.type=="MESH" else -1
        mods=[m.type for m in o.modifiers]
        print("INSP",cn,o.name,o.type,n,mats,mods)
for m in bpy.data.materials:
    if m.use_nodes:
        b=[x for x in m.node_tree.nodes if x.type=="BSDF_PRINCIPLED"]
        col=tuple(round(v,2) for v in b[0].inputs["Base Color"].default_value) if b else None
        em=None
        if b:
            try: em=(tuple(round(v,2) for v in b[0].inputs["Emission Color"].default_value), b[0].inputs["Emission Strength"].default_value)
            except Exception: pass
        print("MAT",m.name,col,em,m.users)
