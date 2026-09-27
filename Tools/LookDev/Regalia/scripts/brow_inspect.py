import bpy, json, collections
out={}
for n in ("L_Eyebrow","R_Eyebrow","R_Eyelash","L_Eyelash"):
    o=bpy.data.objects.get(n)
    if not o: out[n]=None; continue
    d={"type":o.type,"parent":o.parent.name if o.parent else None,"parent_type":o.parent_type,"parent_bone":o.parent_bone,
       "mods":[(m.type,getattr(m,'object',None) and m.object.name) for m in o.modifiers],
       "nverts":len(o.data.vertices) if o.type=='MESH' else 0,"vgroups":len(o.vertex_groups),
       "loc":list(o.matrix_world.translation),"dims":list(o.dimensions),"colls":[c.name for c in o.users_collection],
       "constraints":[(c.type,getattr(c,'subtarget','')) for c in o.constraints]}
    if o.type=='MESH' and o.vertex_groups:
        w=collections.Counter()
        for v in o.data.vertices:
            for g in v.groups:
                if g.weight>0.01: w[o.vertex_groups[g.group].name]+=g.weight
        d["top_groups"]=w.most_common(8)
    out[n]=d
arm=[o for o in bpy.data.objects if o.type=='ARMATURE']
out["armatures"]=[a.name for a in arm]
for a in arm:
    out["brow_bones_"+a.name]=[b.name for b in a.data.bones if any(k in b.name.lower() for k in ("brow","forehead","head"))][:40]
print("JSON:"+json.dumps(out))
